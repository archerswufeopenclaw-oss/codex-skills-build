# Codex Skills Build

本仓库维护五个可独立安装的 skill 入口。可安装的 skill 文件不包含私有数据服务、凭据或真实研究资料；仓库另保留明确标记的历史重建资料。

| Skill | 源目录 | 用途与依赖 |
| --- | --- | --- |
| markdown-article | [skills/markdown-article](skills/markdown-article/README.md) | 按作者的 `**...**` 指令研究、修订文章；格式脚本仅依赖 Python 标准库 |
| markdown-docx | [skills/markdown-docx](skills/markdown-docx/README.md) | Markdown 转 DOCX；需要 Windows、Pandoc、Microsoft Word 和 Windows PowerShell |
| valuation-scan-public-router | `valuation-scan/router` | 证券识别和市场路由；启动器需要 Python 3.11+ 及已配置的私有执行器 |
| valuation-scan-us | `valuation-scan/us` | 已核实美股标的的估值压力卡片契约 |
| valuation-scan-cn-a-ah | `valuation-scan/cn-a-ah` | 非金融 A 股及 A/H 公司的估值压力契约；A/H 必须展示两套价格 |

`technical-entry-scan` 已退役，不再作为仓库发布入口；历史实现保留在 Git 历史中。

## 安装

从仓库根目录操作，将每个 skill 放入目标宿主实际使用的 skills 目录，并以表中 Skill 名称命名。新安装可使用用户目录下的 `.agents/skills`；维护已有安装时沿用其实际位置。发现机制见 [OpenAI 文档](https://learn.chatgpt.com/docs/build-skills)。

Markdown 两个 skill 使用下面的明确文件清单，避免把本地文章、测试产物或缓存一起复制。已有同名文件会更新；其他文件不会删除。

```powershell
$skillRoot = Join-Path $env:USERPROFILE '.agents/skills'
$packages = @(
    @{ Name = 'markdown-article'; Source = 'skills/markdown-article'; Files = @(
        'SKILL.md', 'README.md', 'agents/openai.yaml', 'scripts/_markdown_blocks.py',
        'scripts/align_markdown_tables.py', 'scripts/normalize_heading_spacing.py'
    ) },
    @{ Name = 'markdown-docx'; Source = 'skills/markdown-docx'; Files = @(
        'SKILL.md', 'README.md', 'agents/openai.yaml', 'assets/reference-public.docx',
        'scripts/convert.py', 'scripts/autofit_tables.ps1', 'scripts/inline_code_style.lua'
    ) }
)
foreach ($package in $packages) {
    foreach ($relative in $package.Files) {
        $target = Join-Path (Join-Path $skillRoot $package.Name) $relative
        New-Item -ItemType Directory -Force -Path (Split-Path $target) | Out-Null
        Copy-Item -LiteralPath (Join-Path $package.Source $relative) -Destination $target -Force
    }
}
```

三个估值 skill 的安装及执行器配置见 [valuation-scan/README.md](valuation-scan/README.md)。只安装公共 skill 不代表已经获得数据服务。

## 本地验证

使用 Python 3.11+ 创建独立环境；若 `python` 不在 PATH 中，将第一条命令替换为已安装解释器的完整路径。仓库操作使用 PowerShell 7。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -X utf8 -B -m unittest discover -s tests -v
```

`requirements-dev.txt` 中的 PyYAML 仅用于技能元数据校验，业务脚本没有新增第三方 Python 依赖。用该环境运行宿主 Skill Creator 提供的 `scripts/quick_validate.py <skill目录>`，逐一检查上表五个入口。

DOCX 测试包含真实 Pandoc 转换与模拟 Word 阶段，不启动 Word/COM，不能代替 Word 排版验收。转换器目前将所有 Pandoc 警告视为失败，避免缺图等内容损失进入成品。

估值 schema 随 router 放在 `references/` 中；原 `valuation-scan/schemas/` 路径保留相同副本供已有使用方读取。修改 schema 时同步两处，并运行测试验证一致性。
