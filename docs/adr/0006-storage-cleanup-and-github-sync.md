# ADR 0006 — 本地存储治理与 GitHub 远程同步

## 状态
已采纳（2026-09-13/14）

## 背景
- 工作区本地占用一度达 **326.7 MB**,大头为:旧笔记 HTML(228.7 MB,20 个分区 base64 内嵌图)、模拟试卷 PDF(69.8 MB)、教材 txt(8.9 MB)。
- 旧笔记 HTML 是"唯一正本"(MHT 源已删),但体积大;模拟试卷 PDF 为二进制大文件,OCR 文本已入库。
- 需要手机查看(用户有 GitHub App),需把仓库推送到 GitHub 私有仓库。

## 决策
1. **本地瘦身**:
   - 删除模拟试卷 PDF(69.8 MB,已被 .gitignore 忽略,OCR 文本 `_txt\` 已入库)。
   - 删除旧笔记 HTML(228.7 MB,git 历史有备份)。
   - 删除旧笔记文件夹(README/index/拆图方案),清理 26 个 md 的 39 行失效引用,重跑 `索引.html`。
   - 本地占用 326.7 MB → **28.2 MB**。
2. **git 历史重写(彻底删除旧笔记)**:
   - 用 `git filter-branch --index-filter` 重写全部历史,删除 `资料/旧笔记` 路径;`--prune-empty` 移除纯旧笔记提交。
   - `git reflog expire --expire=now --all` + `git gc --prune=now --aggressive` 清理垃圾对象。
   - .git 体积 426.6 MB → **239.8 MB**;提交数 96 → 92。
   - ⚠️ 旧笔记 HTML 从此**彻底不存在**(本地+git 历史均无),如需恢复只能靠外部备份。
3. **GitHub 远程同步**:
   - 远程仓库 `https://github.com/koishi121/Clinical-Medicine.git`(私有),`master` 分支跟踪 `origin/master`。
   - 凭据用 Windows 凭据管理器(koishi121),HTTPS 推送自动认证。
   - 手机查看:GitHub App 看 md 渲染 + 浏览器打开 `索引.html` 离线阅读器。

## 权衡
- **filter-branch 重写历史**:破坏性操作,重写后所有 commit hash 变化;因无远程协作(单人仓库),可接受。执行前已完整备份 .git(426.6 MB)到仓库外,确认成功后删除。
- **删除旧笔记**:牺牲"唯一正本"换取 228 MB 空间;git 历史重写后连备份也没了——这是用户明确要求("把 git 历史的旧笔记也删掉")。
- **模拟试卷 PDF 超 50MB**:GitHub 允许最大 100MB,推送成功仅警告;若需进一步瘦身可用 Git LFS 或从历史移除。

## 影响
- 本地工作区 28.2 MB,轻量;git 历史 92 提交,无旧笔记。
- 远程 `Clinical-Medicine` 与本地 `master` 同步;日常 `git push` 即更新手机端。
- 旧笔记内容不可恢复(除非外部备份),正库卡/检验速查/用药速查为当前学习主资产。