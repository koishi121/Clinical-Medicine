# Superpowers / Codex / VS Code / Runner 代理交接入口

本仓库使用统一审阅约定 [`clinical-review-contract.md`](clinical-review-contract.md)，Codex CLI、OpenCode、VS Code 任务和 Runner 都遵循它。通用入口是 `tools/review_clinical.ps1`；Codex CLI 与 VS Code 直接调用同一个脚本，Runner 保留独立的兼容代理定义。每次运行由操作者明确选择后端、模型和文件范围；它不自动检测额度或切换模型，临床内容是否采纳由主代理核对原始来源和带教意见后决定。

本机 OpenCode 模型目录在 2026-10-21 列出 `opencode-go/deepseek-v4.1-flash`；这是本仓库默认值。目录中另有 `opencodego/deepseek-v4-flash`，但没有 `opencodego/deepseek-v4.1-flash`，因此采用实际可识别的前一个 ID。模型提供方以后若改名，先用 `opencode models` 确认，再更新代理定义。API key 只配置在本机 OpenCode 的授权/环境中，不写入仓库、交接提示或 VS Code 配置。

## 交接资料

1. 先读 `README.md` 与 `docs/clinical-card-coverage.tsv`，确认 275 张卡目前是 `drafted / linked`，不是医学审核完成。
2. 按 `docs/superpowers/specs/2026-10-20-clinical-cards-drugs-history-design.md` 和对应 plans/progress 恢复已批准的范围；每次只交给代理一个可核对的系统或小批次。
3. 代理输出文件位置、行号、当前说法、疑点和原始指南链接；主代理复核原文、修稿、重建 HTML、运行审计并提交。
4. 临床资料不带患者身份信息，不把草稿当作本院医嘱或处方。`source_checked` 只在完整核读且记录证据后更新。

## 从 VS Code 接入

打开 VS Code 的“终端 → 运行任务”，选择 `Clinical Medicine: review cards`，然后选择后端、模型、文件路径和本次任务。任务调用 `tools/review_clinical.ps1`，与 Codex CLI 终端使用同一个入口。

也可以在 VS Code 终端手动调用：

```powershell
& .\tools\review_clinical.ps1 -Backend codex -Paths "考试/03_临床医学综合/消化系统/胃食管反流病.md" -Prompt "只读审阅这张卡，列出最重要的医学证据疑点和来源。"
```

切换为 OpenCode 并指定模型：

```powershell
& .\tools\review_clinical.ps1 -Backend opencode -Model "opencode-go/deepseek-v4.1-flash" -Paths "考试/03_临床医学综合/消化系统/胃食管反流病.md" -Prompt "只读审阅这张卡，列出最重要的医学证据疑点和来源。"
```

## 从 Codex CLI 接入

```powershell
& .\tools\review_clinical.ps1 -Backend codex -Paths "考试/03_临床医学综合/消化系统/胃食管反流病.md" -Prompt "只读审阅这张卡，列出最重要的医学证据疑点和来源。"
```

可用 `-Model "模型 ID"` 覆盖当前 CLI 默认模型。Codex 使用本机 Codex CLI 登录，OpenCode 默认为 `opencode-go/deepseek-v4.1-flash`。两者的密钥都由本机 CLI 管理，不传给脚本，不写进任务文件或仓库。

## 从 Runner 接入

先运行 Runner 的 `--list --cwd <CLINICAL_REPO>` 查看可用定义，再用 `--agent clinical-review-opencode` 或 `--agent clinical-review-codex`。两个 Runner 定义都遵循共享审阅约定；Codex CLI profile 使用本机默认模型，OpenCode profile 使用 DeepSeek v4.1 Flash。

代理运行结果只是审阅意见。若它没有读取原始指南、输出缺少路径/行号，或因额度/凭据失败，保留未核状态并由主代理继续处理。

2026-10-21 曾验证 Runner 能发现 OpenCode 代理。Runner 0.14.1 的 Windows npm 启动器需要直接调用 OpenCode 自带的 `opencode.exe` 才能保留多行提示；本机缓存已有兼容修复，插件更新可能覆盖它。通用 PowerShell 入口直接调用 CLI，绕过此 Runner 启动器问题。
