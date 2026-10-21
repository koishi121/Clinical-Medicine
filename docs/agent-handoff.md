# Superpowers / Runner 代理交接入口

当 Codex 额度不足或需要第二模型复核时，可以通过 Runner 调用本仓库的只读代理定义 `.agents/clinical-review-opencode.md`。它用于分批审阅草稿，不自动检测额度，也不自动切换模型。每次运行由操作者明确指定任务范围；临床内容是否采纳，由主代理核对原始来源和带教意见后决定。

本机 OpenCode 模型目录在 2026-10-21 列出 `opencode-go/deepseek-v4.1-flash`；这是本仓库默认值。目录中另有 `opencodego/deepseek-v4-flash`，但没有 `opencodego/deepseek-v4.1-flash`，因此采用实际可识别的前一个 ID。模型提供方以后若改名，先用 `opencode models` 确认，再更新代理定义。API key 只配置在本机 OpenCode 的授权/环境中，不写入仓库、交接提示或 VS Code 配置。

## 交接资料

1. 先读 `README.md` 与 `docs/clinical-card-coverage.tsv`，确认 275 张卡目前是 `drafted / linked`，不是医学审核完成。
2. 按 `docs/superpowers/specs/2026-10-20-clinical-cards-drugs-history-design.md` 和对应 plans/progress 恢复已批准的范围；每次只交给代理一个可核对的系统或小批次。
3. 代理输出文件位置、行号、当前说法、疑点和原始指南链接；主代理复核原文、修稿、重建 HTML、运行审计并提交。
4. 临床资料不带患者身份信息，不把草稿当作本院医嘱或处方。`source_checked` 只在完整核读且记录证据后更新。

## 从 VS Code 终端接入

在 VS Code 打开此 Git 工作区后，找到已安装 Runner 插件中的 `skills/sub-agents/scripts/run_subagent.py`，先列出本仓库代理定义：

Windows 上先在当前 PowerShell 终端加入 npm 命令目录，并让 JSON 中文输出使用 UTF-8：

```powershell
$env:PATH = "$env:APPDATA\npm;$env:PATH"
$env:PYTHONIOENCODING = "utf-8"
```

```powershell
python <RUNNER_SCRIPT> --list --cwd <CLINICAL_REPO>
```

再针对一个明确的卡片批次调用：

```powershell
python <RUNNER_SCRIPT> --agent clinical-review-opencode --cwd <CLINICAL_REPO> --prompt "只读审阅指定卡片：列出有来源支持的高风险问题，不修改文件。"
```

`<RUNNER_SCRIPT>` 是本机插件安装路径，`<CLINICAL_REPO>` 是当前仓库或工作区的绝对路径。VS Code 后续可把同一命令放进用户级任务或项目 `.vscode/tasks.json`；这两个参数保持显式，避免把某台电脑的路径提交到公开仓库。若 Runner 无法启动，先检查 OpenCode CLI、授权及模型 ID；不要把 key 粘贴给代理或写进任务文件。

代理运行结果只是审阅意见。若它没有读取原始指南、输出缺少路径/行号，或因额度/凭据失败，保留未核状态并由主代理继续处理。

2026-10-21 已验证 Runner 能发现此代理，并让 OpenCode 2.0.32 收到一个完整的只读测试提示；这只验证接入，不算医学来源核验。本机 Runner 0.14.1 的 Windows npm 启动器需要直接调用 OpenCode 自带的 `opencode.exe` 才能保留多行提示，已对本机插件缓存作兼容修复。插件更新可能覆盖该本机修复；若更新后代理只看到 `[System Context]` 或报告找不到 `opencode`，先检查启动器，再恢复兼容修复。
