# 临床病种闪卡检查与鉴别诊断 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 给 14 个系统的 275 张正库闪卡逐张补齐适用的首诊检查、确诊/参考标准、关键鉴别与可追溯来源。

**Architecture:** 不另复制病种内容；以逐卡覆盖台账锁定文件类型与状态。先完成风湿和消化，随后逐系统核查；规则脚本只验结构、链接、状态和遗漏，医学正确性仍逐卡查原始来源并由主代理验收。

**Tech Stack:** Markdown、Python 3 标准库、unittest、Node.js 内置测试、Git、GitHub Pages。

**Spec:** `docs/superpowers/specs/2026-10-20-clinical-cards-drugs-history-design.md`

## Global Constraints

- 正库 `考试/03_临床医学综合/` 是病种内容唯一正本；保留原题链接、打卡和状态。
- 具体疾病与合并卡写 `首诊辅助检查`、`确诊依据（或参考标准）`、`关键鉴别诊断`、`核查来源`；检查分实验室与影像/内镜/心电/其他。
- 无单一金标准时明确写“无单一金标准”，不能把筛查、支持证据或分类标准误称确诊金标准。
- 技能/操作/保健/总论卡改用初评、危险信号、必要检查、分流或操作核对、关键鉴别的适配结构，并在台账标记例外。
- 指南、诊断标准或说明书须记录标题、年份、链接、核查日期；模拟题与 AI 初稿不作医学证据。
- 未经教材及带教复核的卡保留“AI 初稿待教材校对”，不标注已完成临床审核；不加入患者资料。

## Review Focus

1. 组合病种共享一个“金标准”：抽查亚型分节，不同诊断路径分别写明。
2. 临床诊断/排除诊断被硬套单项检验：抽查“无单一金标准”及标准适用范围。
3. 首诊检查被写成人皆必做：抽查常规、条件触发、检查目的三栏表达。
4. 技能/总论卡被套疾病模板：台账类型与栏目规则必须一致。
5. 新增检查与旧治疗段冲突或来源失效：逐卡来源核查，冲突进入用药计划的审计表。

---

### Task 1: 锁定 275 张卡与覆盖规则

**Files:**
- Create: `docs/clinical-card-coverage.tsv`
- Create: `tools/audit_clinical_cards.py`
- Create: `tests/test_audit_clinical_cards.py`

**Interfaces:** TSV 列为 `path,system,card_type,work_status,source_status,reviewed_on,notes`；`card_type` 为 `disease|combined|non_disease`，`work_status` 为 `pending|drafted|source_checked|needs_review`。脚本提供 `audit(root: pathlib.Path) -> list[str]`，返回问题列表，命令行有问题时非零退出。

- [ ] **Step 1:** 写测试：临时目录中新增卡却无台账行应报漏卡；重复路径应报错；`non_disease` 用适配栏目应通过；`source_checked` 缺来源链接/日期应报错。
- [ ] **Step 2:** 运行 `python -m unittest tests.test_audit_clinical_cards -v`，确认测试先失败。
- [ ] **Step 3:** 实现 `audit(root: Path) -> list[str]` 与命令行；只扫描 14 个系统下非 README 的 Markdown，排除 `检验速查`；对现有 275 张逐张建台账。
- [ ] **Step 4:** 再运行该测试和 `python tools/audit_clinical_cards.py`，确认通过且台账路径集合与磁盘相等；提交独立 commit。

### Task 2: 风湿免疫性疾病 15 张

**Files:** Modify: `考试/03_临床医学综合/风湿免疫性疾病/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

**Interfaces:** 使用 Task 1 的类型、状态和审计命令。

- [ ] **Step 1:** 逐卡核查原始诊断标准/指南；特别区分分类标准、临床诊断与晶体/病理等参考证据。
- [ ] **Step 2:** 按类型补齐栏目与鉴别线索；每卡记来源和核查日期，更新 15 行状态。
- [ ] **Step 3:** 运行审计，人工抽查全部 15 张对照来源及用药冲突；提交独立 commit。

### Task 3: 消化系统 29 张

**Files:** Modify: `考试/03_临床医学综合/消化系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

**Interfaces:** 使用 Task 1 审计命令。

- [ ] **Step 1:** 逐卡核查指南，区分首诊实验室、影像、胃肠镜及其适用时机；出血、梗阻、肝胆胰病种先写危险信号。
- [ ] **Step 2:** 补齐 29 张对应栏目，明确确诊依据或“无单一金标准”，列 2–4 个有判别线索的鉴别。
- [ ] **Step 3:** 更新台账、运行审计、人工抽查全部 29 张来源与药卡冲突，提交独立 commit。

### Task 4: 呼吸系统 20 张

**Files:** Modify: `考试/03_临床医学综合/呼吸系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查诊断标准、检查适用情境及危险信号来源。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 20 行台账。
- [ ] **Step 3:** 运行审计并逐卡来源复核，提交独立 commit。

### Task 5: 心血管系统 19 张

**Files:** Modify: `考试/03_临床医学综合/心血管系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查心电、心肌标志物及影像检查的首诊时机与参考标准。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 19 行台账。
- [ ] **Step 3:** 运行审计、逐卡核对急症分流和药卡冲突，提交独立 commit。

### Task 6: 泌尿系统 20 张

**Files:** Modify: `考试/03_临床医学综合/泌尿系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查尿检、肾功能、影像和病理适应证。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 20 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 7: 血液系统 16 张

**Files:** Modify: `考试/03_临床医学综合/血液系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查血常规、涂片、溶血/凝血和骨髓检查的适应证。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 16 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 8: 内分泌系统 19 张

**Files:** Modify: `考试/03_临床医学综合/内分泌系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查功能试验、激素测定与影像的顺序和干扰因素。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 19 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 9: 神经精神系统 27 张

**Files:** Modify: `考试/03_临床医学综合/神经精神系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查影像、脑脊液、脑电及临床诊断标准的适用条件。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 27 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 10: 传染病 16 张

**Files:** Modify: `考试/03_临床医学综合/传染病/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查病原检测、标本时机与公共卫生处置来源。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 16 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 11: 儿科 24 张

**Files:** Modify: `考试/03_临床医学综合/儿科/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查年龄相关参考范围、检查风险和必要的分流标准。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 24 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 12: 女性生殖系统 25 张

**Files:** Modify: `考试/03_临床医学综合/女性生殖系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查妊娠相关危险信号、实验室/超声与诊断依据。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 25 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 13: 运动系统 18 张

**Files:** Modify: `考试/03_临床医学综合/运动系统/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 区分疾病、骨折/损伤总论和操作类卡，核查影像与急症分流来源。
- [ ] **Step 2:** 按卡型补栏目/鉴别/来源并更新 18 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 14: 其他 19 张

**Files:** Modify: `考试/03_临床医学综合/其他/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 对外科总论、急诊和技能卡逐张判型，核查必要检查与分流来源。
- [ ] **Step 2:** 按卡型补对应栏目并更新 19 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 15: 性传播疾病 8 张

**Files:** Modify: `考试/03_临床医学综合/性传播疾病/*.md`（不含 README）；Modify: `docs/clinical-card-coverage.tsv`。

- [ ] **Step 1:** 核查病原检测、窗口期、鉴别和随访来源。
- [ ] **Step 2:** 逐张补栏目/鉴别/来源并更新 8 行台账。
- [ ] **Step 3:** 运行审计、逐卡来源复核，提交独立 commit。

### Task 16: 全库一致性、阅读器与上线

**Files:**
- Modify: `README.md`（只更新真实完成状态）
- Modify: `索引.html`（生成文件）
- Modify: `docs/clinical-card-coverage.tsv`（最终状态）

**Interfaces:** 使用 Task 1 的覆盖审计结果作为完成判据。

- [ ] **Step 1:** 确认台账 275 个唯一文件路径，14 系统数量之和为 275；所有非疾病例外可解释；逐张来源日期/链接及旧打卡、题链保留。
- [ ] **Step 2:** 运行 `python -m unittest discover -s tests`、`node --test tests/test_reader_app.js` 和 `python tools/audit_clinical_cards.py`，确认通过。
- [ ] **Step 3:** 运行 `python tools/make_reader.py`，检查 275 张可检索、来源链接正常、本地资料未入 HTML。
- [ ] **Step 4:** 提交生成文件，推送并检查 GitHub Pages 页面；未核对卡保持待核状态。
