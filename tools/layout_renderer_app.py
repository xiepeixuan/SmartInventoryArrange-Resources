#!/usr/bin/env python3
import argparse
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import re
import sys
from PIL import Image, ImageDraw

HEADER = '========== Smart Arrange Result =========='
END = '========== Result End =========='
ITEM_RE = re.compile(r'^\[(\d+)\] Name: (.*?) \| ItemId: (.*?) \| Coordinate: \((-?\d+),(-?\d+)\) \| Size: (\d+)x(\d+) \| Type: (.*?) \| Orientation: (\d+)(?: \| Status: (.*))?$')


def message(text, title='Smart Layout Renderer', flags=0x40):
    ctypes.windll.user32.MessageBoxW(None, str(text), title, flags)


def choose_log_file():
    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [
            ('lStructSize', wintypes.DWORD), ('hwndOwner', wintypes.HWND),
            ('hInstance', wintypes.HINSTANCE), ('lpstrFilter', wintypes.LPCWSTR),
            ('lpstrCustomFilter', wintypes.LPWSTR), ('nMaxCustFilter', wintypes.DWORD),
            ('nFilterIndex', wintypes.DWORD), ('lpstrFile', wintypes.LPWSTR),
            ('nMaxFile', wintypes.DWORD), ('lpstrFileTitle', wintypes.LPWSTR),
            ('nMaxFileTitle', wintypes.DWORD), ('lpstrInitialDir', wintypes.LPCWSTR),
            ('lpstrTitle', wintypes.LPCWSTR), ('Flags', wintypes.DWORD),
            ('nFileOffset', wintypes.WORD), ('nFileExtension', wintypes.WORD),
            ('lpstrDefExt', wintypes.LPCWSTR), ('lCustData', wintypes.LPARAM),
            ('lpfnHook', ctypes.c_void_p), ('lpTemplateName', wintypes.LPCWSTR),
            ('pvReserved', ctypes.c_void_p), ('dwReserved', wintypes.DWORD),
            ('FlagsEx', wintypes.DWORD),
        ]
    buf = ctypes.create_unicode_buffer(32768)
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.lpstrFilter = '排序日志 (*.txt;*.log)\0*.txt;*.log\0所有文件 (*.*)\0*.*\0\0'
    ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
    ofn.nMaxFile = len(buf)
    ofn.lpstrTitle = '选择包含 Smart Arrange Result 的 TXT 或 LOG'
    ofn.Flags = 0x00001000 | 0x00000800 | 0x00000008
    return Path(buf.value) if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)) else None


def parse_latest(text):
    starts = [m.start() for m in re.finditer(re.escape(HEADER), text)]
    if not starts:
        raise ValueError('文件中没有找到 Smart Arrange Result 区块。')
    block = text[starts[-1]:]
    end = block.find(END)
    if end >= 0:
        block = block[:end]
    width = height = None
    outcome = 'unknown'
    items = []
    for raw in block.splitlines():
        line = raw.strip()
        if line.startswith('Outcome:'):
            outcome = line.split(':', 1)[1].strip()
        elif line.startswith('ContainerSize:'):
            width, height = map(int, line.split(':', 1)[1].strip().lower().split('x'))
        else:
            m = ITEM_RE.match(line)
            if m:
                items.append({'index': int(m[1]), 'name': m[2], 'itemId': m[3],
                    'x': int(m[4]), 'y': int(m[5]), 'width': int(m[6]),
                    'height': int(m[7]), 'type': m[8], 'orientation': int(m[9]),
                    'status': m[10]})
    if width is None or height is None:
        raise ValueError('结果区块缺少 ContainerSize。')
    if not items:
        raise ValueError('结果区块没有可解析的物品行。')
    return {'width': width, 'height': height, 'outcome': outcome, 'items': items}


def rotate(image, orientation):
    orientation %= 4
    if orientation == 1:
        return image.transpose(Image.Transpose.ROTATE_90)
    if orientation == 2:
        return image.transpose(Image.Transpose.ROTATE_180)
    if orientation == 3:
        return image.transpose(Image.Transpose.ROTATE_270)
    return image


def render(log_path, output_path, resources, scale=2):
    layout = parse_latest(log_path.read_text(encoding='utf-8', errors='replace'))
    catalog_path = resources / 'catalog' / 'items-renderer.json'
    if not catalog_path.exists():
        raise FileNotFoundError(f'物品目录不存在：{catalog_path}')
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    catalog_items = {x['itemId']: x for x in catalog['items']}
    cell = 16 * scale
    canvas = Image.new('RGBA', (layout['width'] * cell + 2, layout['height'] * cell + 2), (28, 21, 31, 255))
    draw = ImageDraw.Draw(canvas)
    for x in range(layout['width'] + 1):
        draw.line((1 + x * cell, 1, 1 + x * cell, 1 + layout['height'] * cell), fill=(58, 40, 57, 255), width=max(1, scale))
    for y in range(layout['height'] + 1):
        draw.line((1, 1 + y * cell, 1 + layout['width'] * cell, 1 + y * cell), fill=(58, 40, 57, 255), width=max(1, scale))
    missing = []
    for item in sorted(layout['items'], key=lambda x: x['index']):
        meta = catalog_items.get(item['itemId'])
        sprite_file = meta.get('spriteFile') if meta else None
        sprite_path = resources / sprite_file if sprite_file else None
        if sprite_path is None or not sprite_path.exists():
            missing.append(item['itemId'])
            continue
        image = rotate(Image.open(sprite_path).convert('RGBA'), item['orientation'])
        target = (item['width'] * cell, item['height'] * cell)
        if image.size != target:
            image = image.resize(target, Image.Resampling.NEAREST)
        canvas.alpha_composite(image, (1 + item['x'] * cell, 1 + item['y'] * cell))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path)
    report = {
        'sourceLog': str(log_path.resolve()), 'output': str(output_path.resolve()),
        'containerSize': f"{layout['width']}x{layout['height']}",
        'outcome': layout['outcome'], 'itemCount': len(layout['items']),
        'missingSprites': sorted(set(missing)), 'cellPixels': cell,
    }
    output_path.with_suffix('.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', nargs='?')
    parser.add_argument('-o', '--output')
    parser.add_argument('--resources')
    parser.add_argument('--scale', type=int, default=2)
    parser.add_argument('--no-open', action='store_true')
    parser.add_argument('--quiet', action='store_true')
    args = parser.parse_args()
    selected_by_dialog = not args.input
    log_path = Path(args.input) if args.input else choose_log_file()
    if log_path is None:
        return 0
    if not log_path.exists():
        raise FileNotFoundError(f'输入文件不存在：{log_path}')
    app_dir = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    resources = Path(args.resources) if args.resources else app_dir
    output = Path(args.output) if args.output else log_path.with_name(log_path.stem + '.layout.png')
    report = render(log_path, output, resources, args.scale)
    if not args.quiet:
        message(f"布局图已生成。\n\n容器：{report['containerSize']}\n物品：{report['itemCount']}\n缺失图片：{len(report['missingSprites'])}\n\n{output}")
    if not args.no_open:
        os.startfile(output)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception as exc:
        message(f'生成失败：\n\n{exc}', flags=0x10)
        raise SystemExit(1)

