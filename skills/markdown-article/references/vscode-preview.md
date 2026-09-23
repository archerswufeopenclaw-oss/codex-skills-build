# VS Code 作者说明：源码高亮与预览红字

源码编辑区与 Markdown 预览使用不同配置，可按需要选用，也可同时启用。两者都保留同一份 `/explain` 标记，不改动文章文字。

## 源码编辑区：浅红背景

1. 在 VS Code 扩展面板安装 [Highlight](https://marketplace.visualstudio.com/items?itemName=fabiospampinato.vscode-highlight)，核对扩展 ID 为 `fabiospampinato.vscode-highlight`。
2. 打开随包的 [`vscode-author-notes.settings.json`](../assets/vscode-author-notes.settings.json)，在命令面板运行 `Preferences: Open User Settings (JSON)`，合并其中的 `highlight.regexes` 设置。若已有该设置，只把文件中的规则追加到现有对象，保留其他规则；不要覆盖整个用户设置文件或创建重复的同名属性。
3. 将下方作者说明示例复制到测试 `.md` 文件，不要复制外层代码围栏。在源码编辑区确认整块出现浅红背景，右侧滚动条出现红色标记；原来的文字语法颜色保持不变。

这份设置不含本机路径，可直接分享；只安装 `markdown-docx` 的用户也可单独下载并合并，无需安装整个 `markdown-article`。只想在某个项目启用时，将同一规则合并到该项目的 `.vscode/settings.json`，也要保留其中的其他设置。

规则仅作用于语言模式为 Markdown 的文件，从固定首行开始覆盖连续的 `>` 行，包括只含 `>` 的空行；遇到不带 `>` 的空行即结束。编辑器的自动折行不影响识别。规则不解析 Markdown，代码围栏内的相同字面示例也可能被高亮。若无效果，检查扩展是否启用、文件语言模式及规则是否成功合并。扩展的配置方式见 [官方说明](https://github.com/fabiospampinato/vscode-highlight)。

## 内置预览：红色文字

CSS 只影响预览，不能给源码编辑区上色；这一选项不需要 Highlight 扩展。

1. 在 VS Code 中打开包含文章的项目文件夹，将随包的 [`assets/author-notes.css`](../assets/author-notes.css) 复制到工作区根目录的 `.vscode/author-notes.css`。只安装 `markdown-docx` 的用户可单独下载此 CSS，无需安装整个 `markdown-article`。
2. 在命令面板运行 `Preferences: Open Workspace Settings (JSON)`，将下面的相对路径追加到该项目 `.vscode/settings.json` 的 `markdown.styles` 数组：

   ```json
   {
     "markdown.styles": [".vscode/author-notes.css"]
   }
   ```

   工作区设置会覆盖用户级同名数组；需要同时使用的其他有效样式也要保留在工作区数组中。文章必须位于当前打开的工作区内；若只是打开单个文件，先打开它所在的文件夹。
3. 将下面的作者说明示例复制到测试 `.md` 文件，不要复制外层代码围栏。重新打开内置 Markdown 预览（Windows：`Ctrl+Shift+V`），确认作者说明整块变红。深色主题采用较亮的红色，浅色主题采用深红色。

不要直接引用工作区外的 skill 安装目录：VS Code 的本地资源范围可能阻止加载，并提示 `Could not load 'markdown.styles'`；改成 `file://` 也不能解除这一限制。若沿用旧的绝对路径配置，请改用上述工作区内副本和相对路径，无需降低预览安全级别。

## 标记与效果

`/explain` 生成的 Markdown 保持引用块结构。完整固定首行供源码规则识别，`span` 标记也供 CSS 和 DOCX 转换器识别；无需手动设置文字颜色：

```markdown
> <span class="author-note">🔴 作者说明（供作者阅读，可整段删除）</span>
>
> 本小节解释……。确认后可删除整个引用块。
```

说明的每行都保留 `>`，段间空行写成 `>`；说明结束后使用不带 `>` 的空行。CSS 只匹配首段带 `author-note` 标记的引用块，正文、链接和行内代码均显示为红色。普通引用保持原样。删除说明时，删除整块连续的引用内容及首行标记。

该 CSS 同时把独立段落中的 `doc-meta` 标记设为左对齐、零首行缩进，不改变颜色。段内需要换行时，在行末使用反斜杠：

```markdown
<span class="doc-meta">内部决策讨论稿\
政策核查截至今日</span>
```

Codex 预览及其他阅读器不保证应用上述配置，仍可通过红点和“可整段删除”提示辨认。DOCX 的红字由 `markdown-docx` 根据同一标记生成：宋体（西文 Times New Roman）、11 pt、左对齐，不添加背景色，也不依赖扩展或 CSS。若预览没有效果，先核对路径及工作区的 `markdown.styles`，再更新 VS Code；第三方预览扩展可能使用不同的样式配置。

参见 [VS Code 官方自定义 Markdown CSS 说明](https://code.visualstudio.com/docs/languages/markdown#_using-your-own-css)。
