# Markdown to DOCX

把本地 Markdown 文章转换为带中文样式的 Word 文档，并自动调整表格宽度。保留原文措辞，不改写源文件。

## 使用前

- 需要 Windows、本机桌面版 Microsoft Word、Python（建议 3.11+）、Pandoc，以及可运行的 Windows PowerShell（`powershell.exe`）。网页版 Word 和仅安装 PowerShell 7 均不能替代这些依赖。
- Python 脚本只使用标准库，无需安装额外 Python 包。Pandoc 需在 PATH 中，或安装于 `%LOCALAPPDATA%\Pandoc\pandoc.exe`。
- Word 应能正常打开文档，并具备模板使用的中文字体（包括楷体）。图片等相对路径以源 Markdown 所在目录为准。

## 安装

从本仓库的 `skills/markdown-docx/` 取得以下文件，保留目录结构，放入用户目录下的 `.agents/skills/markdown-docx/`：

```text
markdown-docx/
├── SKILL.md
├── README.md
├── agents/openai.yaml
├── assets/reference-public.docx
└── scripts/
    ├── convert.py
    ├── autofit_tables.ps1
    └── inline_code_style.lua
```

三个脚本和公开模板都必须保留。已有安装沿用原位置，避免重复安装；若 Codex 未发现新 skill，重启后再试。发现机制见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。

## 第一次使用

准备好一份 `.md` 或 `.markdown` 文件，在 Codex 中发送（替换为真实路径）：

```text
请用 $markdown-docx 将 C:\文章\示例.md 转成 Word，并检查生成文档的排版。
```

默认在源文件旁生成 `示例.docx`。每次处理一个明确指定的文件；若同名 DOCX 已存在，默认停止。需要替换时，在请求中明确写“覆盖已有 DOCX”。

完成后用 Word 查看中文、标题、列表、图片、链接和表格，确认没有缺失、乱码、重叠或超出页宽。自然分页、表格跨页或末页较短不一定是排版错误。

## 输出特点

- 使用随包提供的中文文章模板；表格先按内容调整，再适应页面宽度。
- 中文软换行不会额外插入空格；英文词间空格、显式换行和代码缩进仍保留。
- 单反引号包裹的行内代码使用楷体、加粗、小四（12 pt）；标为 `text` 的围栏代码块使用楷体、常规、10 pt，保留换行和缩进。
- Pandoc 转换和 Word 表格调整都成功后才生成最终文件。图片缺失等 Pandoc 告警会终止转换；失败时不会发布新成品，也不会替换已有 DOCX。

## 可选：直接运行脚本

在安装后的 `markdown-docx` 目录中运行：

```powershell
python -X utf8 -B scripts/convert.py "C:\文章\示例.md"
```

用 `--output "C:\输出\示例.docx"` 指定其他输出位置；仅在确定要替换已有文件时加 `--overwrite`。

若提示找不到 Pandoc 或 Word 调整失败，先检查对应程序是否安装且能正常运行；若提示缺少图片，修正文章中的资源路径后重试。转换器不会自动修复 Markdown，也不会批量转换整个目录。

完整行为约定见 [SKILL.md](SKILL.md)。
