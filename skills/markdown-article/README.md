# Markdown Article

在 Markdown 文章里写下修改要求，让 Codex 就地研究、核验和修订，尽量保留你的语气、结构和引用方式。

## 使用前

- 行内代码和代码块之外的所有 `**...**` 都是作者指令，完成后会被删除。原文若用粗体表示强调，请先改用其他形式。
- 文章会原地更新。请让 Codex 能访问并修改目标文件；需要查证时，还需有可用的检索工具或你提供的资料。
- 格式脚本使用 Python 标准库，建议 Python 3.11+；无需安装 PyYAML、Pandoc 或 Word。独立复核模式需要宿主支持子代理。

## 安装

从本仓库的 `skills/markdown-article/` 取得以下文件，保留目录结构，放入用户目录下的 `.agents/skills/markdown-article/`：

```text
markdown-article/
├── SKILL.md
├── README.md
├── agents/openai.yaml
└── scripts/
    ├── _markdown_blocks.py
    ├── align_markdown_tables.py
    └── normalize_heading_spacing.py
```

Windows 用户目录通常是 `C:\Users\你的用户名`，macOS/Linux 为 `~`。已有安装沿用原位置，避免重复安装。若 Codex 未发现新 skill，重启后再试。发现机制见 [OpenAI 官方说明](https://learn.chatgpt.com/docs/build-skills)。

## 第一次使用

在文章中加入一条指令，例如：

```markdown
# 我的文章

本节讨论远程办公的影响。

**请补充一段关于远程办公利弊的分析，并注明关键证据的来源。**
```

然后在 Codex 中发送（替换为你的真实路径）：

```text
请用 $markdown-article 处理 C:\文章\示例.md 中的作者指令。
```

完成后检查正文和来源：新增内容应融入文章，已完成的粗体指令应消失。下一轮直接添加新指令，继续处理同一文件即可。

## 按需增加复核

- 默认 L0：`**补充这段论述的一手来源。**`，主代理直接处理。
- L1：`**/review 核验这项计算及其适用条件。**`，增加一名独立复核者。
- L2：`**/roundtable 检验这一结论最有力的支持与反证。**`，红蓝两名复核者分别找反证和支持。

复核者只提供意见，最终由主代理判断并编辑。复核会增加耗时和模型用量；重要结论仍需要你阅读确认。

## 研究资料与格式整理

处理 `示例.md` 时，会在旁边创建 `示例.research/`：`materials/` 保存实际采用的资料，`notes.md` 保存简要证据与计算依据，`discussion.md` 记录 L2 讨论。后续修改会优先复用这些材料。

Codex 会用 [标题空行脚本](scripts/normalize_heading_spacing.py) 整理全文标题，用 [表格对齐脚本](scripts/align_markdown_tables.py) 整理本轮新增或修改的表格；通常无需手动运行。两者都依赖同目录的 [_markdown_blocks.py](scripts/_markdown_blocks.py)，分享时不要漏掉。表格对齐效果请在等宽字体下查看。

完整行为约定见 [SKILL.md](SKILL.md)。
