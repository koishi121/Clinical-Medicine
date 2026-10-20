# 药物迭代时间线与阅读入口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 从用户提供的《药物简史》正文提炼易懂、可核查的药物迭代时间线，并让手机与离线读者从用药速查目录找到它。

**Architecture:** EPUB 只在本地只读提取，时间线 Markdown 是唯一入库正文。每个节点同时列书内章节与独立史料，最后更新目录、重建 `索引.html` 并核查 Pages。

**Tech Stack:** EPUB（只读）、Markdown、Python 3 标准库、unittest、Node.js 内置测试、Git、GitHub Pages。

**Spec:** `docs/superpowers/specs/2026-10-20-clinical-cards-drugs-history-design.md`

## Global Constraints

- 输入 EPUB 位于 `E:\microsoft edge\药物简史 (德吕恩·布奇) (z-library.sk, 1lib.sk, z-lib.sk).epub`，只读，不提交 EPUB、书中图片或长段原文。
- 历史时间线不是当前治疗推荐；争议年份独立核查，保留“观察/分离/临床应用/规模生产”等不同事件的区别。
- 约 10 个节点，每行写“年代—药物/方法—解决什么—局限—推动下一步”，标书内章节及独立来源。
- Markdown 是正文唯一来源，`索引.html` 由 `tools/make_reader.py` 生成；`资料/` 不收录至 Git/HTML。

## Review Focus

1. 同一药的发现、分离、临床应用被压成一年：对照书章与独立史料，将事件分开或标年代段。
2. 书中旧医学主张被误当现行治疗：逐条查时间线没有现代处方指令。
3. 年份争议或来源不明：每节点至少一条书章定位与一条可打开的独立来源。
4. EPUB 文本/图片被意外复制：检查 Git 变更和生成 HTML，仅保留短句原创概述。
5. 手机入口找不到时间线：从 README、用药目录和 Pages 手动点击验证。

---

### Task 1: 提取节点与双重核查

**Files:**
- Create: `规培/内科/用药速查/药物迭代时间线.md`

**Interfaces:** 输出文档有“阅读说明”“时间线”“来源索引”三个栏目；时间线表列为 `年代|药物/方法|解决的问题|局限|推动的下一步|书内章节与核查来源`。

- [ ] **Step 1:** 只读检查 EPUB 的目录和正文，选择约 10 个确实出现在书中的节点，记录章节，不复制长段原文。
- [ ] **Step 2:** 用诺贝尔奖、原始研究或监管机构等可靠来源核查年份和事件性质；发现不一致时在表中解释。
- [ ] **Step 3:** 用简短中文原创表述写时间线，包含奎宁、阿司匹林、选择性化疗、磺胺、青霉素、链霉素/试验和药物警戒等从书中核实的主线。
- [ ] **Step 4:** 手工审读每行能回答“为什么从上一代走到下一代”，检查无处方建议、无大段原文，提交独立 commit。

### Task 2: 用药目录、离线阅读器与手机入口

**Files:**
- Modify: `规培/内科/用药速查/README.md`
- Modify: `索引.html`（生成文件）
- Test: `tests/test_make_reader.py`（仅在已有收录测试未覆盖新页时增补）

**Interfaces:** 目录链接固定为 `药物迭代时间线.md`；由阅读器递归收录该 Markdown。

- [ ] **Step 1:** 在用药速查 README 的醒目位置加时间线链接与“历史学习、非处方依据”一句说明。
- [ ] **Step 2:** 如新页收录/内部链接没有现成测试，先补测试并见到失败，再修阅读器；已有测试覆盖则直接运行。
- [ ] **Step 3:** 运行 `python -m unittest discover -s tests -p test_make_reader.py`、`node --test tests/test_reader_app.js`；生成 `python tools/make_reader.py` 并确认新页可检索、链接可跳。
- [ ] **Step 4:** 检查 Git 变更无 EPUB/图片/本地资料，提交、推送，手机宽度实测 Pages 的入口与阅读效果。
