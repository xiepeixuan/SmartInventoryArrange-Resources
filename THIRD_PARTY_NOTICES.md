# Third-party notices / 第三方材料说明

请结合 [LICENSE_SCOPE.md](LICENSE_SCOPE.md) 阅读。本项目 MIT 不重许可游戏素材或捆绑依赖。

## 渲染源码的依赖

`tools/layout_renderer_app.py` 使用 Python 标准库与 Pillow。`requirements.txt` 指定 `Pillow>=10,<13`；安装不同版本时须使用该实际版本的许可，不能把一份示例通知视为所有版本的完整清单。

## 当前 EXE：已观察到的组成

对当前 Git 跟踪的 `SmartLayoutRenderer.exe` 作只读 PyInstaller CArchive/PYZ 检查，未运行 EXE：

- 76 个外层归档条目；主程序为 `layout_renderer_app`，内部还有 `PYZ.pyz`。
- 内含 `python310.dll`，文件/产品版本均为 **3.10.7**。
- PYZ 中 `PIL._version` 的版本常量为 **12.3.0**。这不同于审查机器当前安装的 Pillow 11.3.0，因此没有拿本机许可证冒充打包版本。
- 存在 `_imaging`、`_imagingcms`、`_imagingft`、`_webp`、`_avif` 等原生扩展；还观察到 OpenSSL 1.1 命名 DLL、libffi 和 Windows CRT/API-set DLL。
- EXE 使用 PyInstaller 格式；此次没有确认其确切打包器版本，也不根据审查机已安装版本猜测。

这些是组件观察，不是完整版本/SBOM 或许可证审计结论。Pillow 的可选编解码器、字体/色彩库、Python 内置的第三方材料、OpenSSL、libffi 和 Microsoft 运行时等仍须按实际打包来源逐项核验；简单声明“全 EXE 为 MIT”不准确。

## 保留的上游许可原文与来源

- **Python 3.10.7**：PSF 及历史许可，保留 [该版本原始 LICENSE](third_party/licenses/Python-v3.10.7-LICENSE.txt)，[上游](https://github.com/python/cpython/blob/v3.10.7/LICENSE)。Python 中的其他第三方组件还可能有各自条款。
- **Pillow 12.3.0**：PIL/Pillow 的 MIT-CMU 许可与作者通知，保留 [该版本原始 LICENSE](third_party/licenses/Pillow-12.3.0-LICENSE.txt)，[上游](https://github.com/python-pillow/Pillow/blob/12.3.0/LICENSE)。这不是本项目标准 MIT，也不是所有编解码器的完整通告。
- **PyInstaller**：上游使用 GPL 与打包例外及部分 Apache 条款；见 [官方许可说明](https://pyinstaller.org/en/stable/license.html)。打包例外不取消应用依赖的许可义务；准确版本和 COPYINGS 需从实际构建链补齐。

此次仅增加已核实的通知和授权边界，未重打包 EXE，也未宣称 EXE 现有完整依赖通告已补齐。后续若重发完整二进制，应从实际构建环境收集对应版本的全部许可与必要通知。

## 游戏素材

`sprites/`、`catalog/`、`renders/` 与 `test_sets/` 的游戏素材/导出数据不由本项目授予 MIT 或 CC 许可。现有公开资源的再分发授权证据仍待游戏权利人确认；署名与开源工具许可不代替该授权。
