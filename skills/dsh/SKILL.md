---
name: dsh
description: 使用本机 DeepSeek Harness 官方命令行执行用户指定的问答、分析、代码或文件任务。用户说“使用 dsh”“让 DSH 执行”“用 DeepSeek Harness”或“使用 DeepSeek CLI”时使用。
---

# DSH / DeepSeek Harness

把用户指定的任务交给本机官方 `dsh headless` 执行，再由 Codex 检查结果。不要只给调用说明，也不要把指定给 DSH 的工作静默改由其他模型完成。

## 本机入口

- Windows 使用 PowerShell 7（`pwsh.exe`）。
- 官方命令为 `dsh`，随 DeepSeek Harness Desktop 安装，桌面窗口关闭后仍可调用。
- 优先从 PATH 定位 `dsh`；若 PATH 未刷新，检查当前用户的 Desktop 安装位置。下面的示例从 `$env:LOCALAPPDATA` 定位默认 Windows 安装，不写死用户名。
- 沿用当前 headless profile 的 provider 和 model；用户另有指定时先核实实际支持的配置。首次使用需要先完成官方 DSH 的安装、模型配置和认证。
- 使用现有 `DEEPSEEK_API_KEY` 或 DSH 凭据存储，不打印密钥、认证配置或整份环境变量。
- 仅使用官方 DSH；不要把 API 直连或其他同名 CLI 当成 DSH。

`dsh --version`、`dsh headless --help` 用于检查入口。入口缺失时检查实际桌面版安装位置；不要把 API 直连或其他 CLI 当成 DSH 的成功调用。

## 推理档位

- 默认使用 `max`，优先完成质量，不因节省 token 主动降档。
- 用户明确指定的档位优先。未指定档位但明确要求速度优先或快速初稿时，Codex 可为本次任务选择 `high`。
- `low` 或 `off` 用于用户明确指定，或已有验证依据的大批量简单任务吞吐优化；不确定时保持 `max`。
- 按一次交接任务选择档位，无需逐个调度 DSH 内部的工具步骤。
- 临时调整仅影响本次任务：使用独立的 `--patch` 文件覆盖 `agent-default-model` 的配置，保留其 `provider`、`model`，调整 `reasoningEffort`。不要改写共享的 home/profile 默认配置，也不要通过“改全局后再恢复”调档，以免影响其他会话。

## 交接与权限

在任务对应的工作目录运行，交代目标、相关文件、允许修改的范围和验收条件。DSH 有自己的会话，不会自动获得当前 Codex 对话；只传完成任务所需的上下文。

- 问答、分析、审查使用 `--permission-mode read-only`。
- 用户已授权编辑时使用 `--permission-mode workspace-write`，限定在对应工作区；DSH 会直接编辑文件。
- 用户要求“仅生成候选”“不改原文件”时，在隔离副本或合适的独立工作树执行，再审查候选。候选目录与验收机制需要另行准备。
- 不默认增加 `--add-dir` 或开启完整访问。需要更大权限、外部发送、发布等操作时，遵守当前任务的授权边界；DSH 调用不扩大授权。

任务通过 UTF-8 标准输入传递，避免中文编码和 `.cmd` 参数转义问题。示例在已选定的工作目录运行：

```powershell
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$dshCommand = Get-Command dsh -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
$dsh = if ($dshCommand) {
    $dshCommand.Source
} else {
    Join-Path $env:LOCALAPPDATA 'Programs\DeepSeek Harness\resources\runtime\cli\bin\dsh.cmd'
}
if (-not (Test-Path -LiteralPath $dsh -PathType Leaf)) {
    throw '未找到官方 DSH CLI；请核实实际安装位置。'
}
$task = @'
这里填写完整任务、文件范围、限制和所需结果。
'@
$task | & $dsh headless --permission-mode read-only -
$dshExitCode = $LASTEXITCODE
```

需要编辑时替换权限参数，不把任务文本拼成 shell 命令。长任务可将完整提示写入 UTF-8 文件，再用 `Get-Content -LiteralPath <任务文件> -Raw -Encoding utf8` 管道传入。

## 结果与续接

需要进度记录时加 `--json`，将 stdout、stderr 保存到本次任务的工作目录。JSONL 包含 `session`、`status`、`tool_call`、`tool_result`、`final` 等事件；检查最终事件与退出码，仅汇总所需状态、工具结果和最终答案，不把 `thinking` 事件全文输出到聊天。

持续跟踪尚未结束的进程。长时间没有最终答案不等于请求已失败；结合进度、错误及约定时限判断。网络或认证失败不盲目重发。需要接续同一任务时，用已记录的 `sessionId` 加 `--session-id`；不要恢复无关会话。

如果 DSH 修改了文件，检查实际差异并运行与任务相称的验证。报告 DSH 完成了什么、Codex 验证了什么，以及仍未完成的部分。命令存在或退出码为零，都不能替代实际输出和文件验收。

官方命令说明：https://github.com/deepseek-ai/deepseek-harness/blob/master/apps/cli/README.md
