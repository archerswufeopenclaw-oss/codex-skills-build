# 在 VS Code 中显示作者说明红字

建议使用 `/explain` 的作者配置此 CSS：内置 Markdown 预览会把整块作者说明显示为红字，普通引用保持原样。不安装额外扩展，也不改变 Markdown 正文内容。

## 配置一次

1. 找到安装目录中的 [`assets/author-notes.css`](../assets/author-notes.css)。只安装 `markdown-docx` 的用户可单独下载此 CSS，保存到固定目录，无需安装整个 `markdown-article`。请指向长期保留的副本，不要指向临时分享包或下载目录。
2. 在 VS Code 命令面板运行 `Preferences: Open User Settings (JSON)`，将 CSS 的绝对路径追加到 `markdown.styles`。保留已有条目，路径使用 `/`；把下面的用户名和安装路径替换为自己的：

   ```json
   {
     "markdown.styles": [
       "C:/Users/你的用户名/.agents/skills/markdown-article/assets/author-notes.css"
     ]
   }
   ```

   示例沿用安装 README 的 `.agents/skills` 路径；已有 `.codex/skills` 安装或单独保存 CSS 的用户，使用自己的实际路径。

   若只对一个项目启用，可将 CSS 复制到项目的 `.vscode/author-notes.css`，在该项目的 `.vscode/settings.json` 中追加：

   ```json
   {
     "markdown.styles": [".vscode/author-notes.css"]
   }
   ```

   工作区设置会覆盖用户级同名数组；需要同时使用的其他样式也要保留在工作区数组中。
3. 将下面的作者说明示例复制到测试 `.md` 文件，不要复制外层代码围栏。重新打开内置 Markdown 预览（Windows：`Ctrl+Shift+V`），确认作者说明整块变红。深色主题采用较亮的红色，浅色主题采用深红色。

## 标记与效果

`/explain` 生成的 Markdown 保持引用块结构。首行 `span` 的 class 只用于让 CSS 和 DOCX 转换器识别作者说明；无需手动设置文字颜色：

```markdown
> <span class="author-note">🔴 作者说明（供作者阅读，可整段删除）</span>
>
> 本小节解释……。确认后可删除整个引用块。
```

CSS 只匹配首段带 `author-note` 标记的引用块，正文、链接和行内代码均显示为红色。不要用普通引用的 `>` 代替此标记；普通引用不会被染红。删除说明时，删除整块连续的引用内容及首行标记。

该 CSS 同时把独立段落中的 `doc-meta` 标记设为左对齐、零首行缩进，不改变颜色。段内需要换行时，在行末使用反斜杠：

```markdown
<span class="doc-meta">内部决策讨论稿\
政策核查截至今日</span>
```

CSS 仅影响 VS Code 的内置 Markdown 预览；源码视图、Codex 预览及其他阅读器不保证红字，仍可通过红点和“可整段删除”提示辨认。DOCX 的红字由 `markdown-docx` 自行生成，不依赖此 CSS。若没有效果，先核对路径及工作区的 `markdown.styles`，再更新 VS Code；第三方预览扩展可能使用不同的样式配置。

参见 [VS Code 官方自定义 Markdown CSS 说明](https://code.visualstudio.com/docs/languages/markdown#_using-your-own-css)。
