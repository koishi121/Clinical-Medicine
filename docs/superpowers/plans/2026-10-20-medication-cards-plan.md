# 用药速查安全精修与科室补齐 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把现有 14 篇用药卡改为有来源、可供带教核对的学习卡，优先消除高风险给药歧义，并补齐内科轮转缺页。

**Architecture:** Markdown 正文仍是唯一来源；来源核查台账逐条对应剂量、途径、频次等可操作数字。每批先核原始来源再改卡，主代理审阅风险，最后重建离线阅读器。

**Tech Stack:** Markdown、Python 3 标准库、unittest、Node.js 内置测试、Git、GitHub Pages。

**Spec:** `docs/superpowers/specs/2026-10-20-clinical-cards-drugs-history-design.md`

## Global Constraints

- 正库病种卡的治疗段仅修正与已核实药卡冲突或明显错误的内容，不全面重写。
- 学习卡不能替代本院规范、说明书或带教复核；不放入可识别患者资料。
- 具体剂量、途径、频次、疗程均须追溯至现行说明书或权威指南；未核实数字不保留为可复制医嘱。
- 儿童、妊娠、肾功能不全和本院处方权限差异不得从成人示例外推。
- EPUB、书中图片及长段原文不得入库；`资料/` 不得进入 HTML。
- Runner 当前无代理定义；只有确认定义可用才称为 Runner 执行，否则按用户授权用内置子代理处理独立低风险批次。

## Review Focus

1. 同名药不同制剂/浓度：卡片应分别给出适应证和给药途径，测试台账抽查急救药每条数字。
2. 特定适应证的剂量被写成通用剂量：人工逐页核对“适用与不适用场景”及来源版本。
3. 儿童、孕期、肾功能不全：抽查每页特殊人群警示，不得照搬成人数字。
4. 说明书与指南差异或已过期：来源台账必须有年份、链接、核查日期与适用地区/人群。
5. 旧卡与病种治疗段冲突：抽查跨页链接和冲突清单，修正后重新检索同一主张。

---

### Task 1: 高风险急救药卡

**Files:**
- Modify: `规培/内科/用药速查/急诊科/急诊抢救药_肾上腺素胺碘酮阿托品.md`
- Create: `docs/medication-source-log.tsv`
- Modify: `规培/内科/用药速查/README.md`

**Interfaces:** 台账列为 `path,claim,indication,formulation,source_title,source_year,url,checked_on,status`，后续任务沿用。

- [ ] **Step 1:** 核查成人心搏骤停、过敏性休克等不同情境的官方复苏指南及实际制剂说明书；逐项登记原文出处和适用范围。
- [ ] **Step 2:** 改写急救药卡，去掉未说明浓度的“不稀释”等直接操作语句；每一剂量注明场景、制剂浓度、途径、复核点。
- [ ] **Step 3:** 将 README 定位改为“带教核对用学习卡”；抽查心搏骤停、过敏性休克、症状性心动过缓三种场景不会互相套用剂量。
- [ ] **Step 4:** 检查改动、台账完整性并提交一个独立 commit。

### Task 2: 抗凝、心衰与心血管药

**Files:**
- Modify: `规培/内科/用药速查/心血管内科/*.md`（4 张）
- Modify: `docs/medication-source-log.tsv`

**Interfaces:** 沿用 Task 1 台账字段。

- [ ] **Step 1:** 以当前指南及说明书核对机械瓣/房颤抗栓、DOAC 肾功能和逆转、HFrEF 药物适应证；台账记录可操作数字。
- [ ] **Step 2:** 精修 4 张卡的适用场景、制剂/成人示例、禁忌、监测和复评，避免把一种 INR 目标或给药方案写成通用规则。
- [ ] **Step 3:** 逐项对照台账并检查目录链接，提交独立 commit。

### Task 3: 抗菌药和糖皮质激素

**Files:**
- Modify: `规培/内科/用药速查/药理类别/*.md`（2 张）
- Modify: `规培/内科/用药速查/感染科/*.md`（2 张）
- Modify: `docs/medication-source-log.tsv`

**Interfaces:** 沿用 Task 1 台账字段。

- [ ] **Step 1:** 按感染综合征、病原证据、本地耐药和处方权限核对抗菌建议；核对激素换算及禁忌的来源。
- [ ] **Step 2:** 精修 4 张卡，明确抗菌药不能按病名机械选药，标注培养/药敏与降阶梯复评。
- [ ] **Step 3:** 抽查抗菌适应证和激素数字都能回到来源，提交独立 commit。

### Task 4: 消化、呼吸、内分泌现有药卡

**Files:**
- Modify: `规培/内科/用药速查/消化内科/*.md`（3 张）
- Modify: `规培/内科/用药速查/呼吸内科/*.md`（1 张）
- Modify: `规培/内科/用药速查/内分泌科/*.md`（1 张）
- Modify: `docs/medication-source-log.tsv`

**Interfaces:** 沿用 Task 1 台账字段。

- [ ] **Step 1:** 核查聚乙二醇不同产品配法、奥曲肽的真实适应证、PPI、吸入治疗、降糖药的现行来源。
- [ ] **Step 2:** 按统一栏目精修 5 张卡；对不能确认的数字标“待核”并删去可复制医嘱形式。
- [ ] **Step 3:** 抽查每页特殊人群和监测提示，提交独立 commit。

### Task 5: 补齐四个缺失科室

**Files:**
- Create: `规培/内科/用药速查/肾脏内科/容量电解质用药.md`
- Create: `规培/内科/用药速查/血液内科/贫血治疗用药.md`
- Create: `规培/内科/用药速查/神经内科/抗栓与抗癫痫用药.md`
- Create: `规培/内科/用药速查/风湿免疫科/NSAID激素与DMARD.md`
- Modify: `规培/内科/用药速查/README.md`
- Modify: `docs/medication-source-log.tsv`

**Interfaces:** 沿用 Task 1 台账字段；文件名和科室目录是 README 的链接目标。

- [ ] **Step 1:** 逐科确定轮转高频场景、资料来源及需要排除的危险人群，先列“适用/不适用”。
- [ ] **Step 2:** 写 4 张带教核对卡，数字只写已核实的成人示例，并登记台账。
- [ ] **Step 3:** 更新 README，逐一检查链接、来源和特殊人群；提交独立 commit。

### Task 6: 现有科室缺口与跨卡冲突

**Files:**
- Create: `docs/medication-gap-and-conflict-review.md`
- Modify: `规培/内科/用药速查/README.md`
- Modify: `考试/03_临床医学综合/<系统>/<卡片>.md`（仅核查后确认冲突的卡）
- Create: `规培/内科/用药速查/呼吸内科/哮喘急性发作与肺炎用药.md`、`规培/内科/用药速查/心血管内科/急性冠脉综合征用药.md`、`规培/内科/用药速查/消化内科/幽门螺杆菌根除与消化道出血用药.md`、`规培/内科/用药速查/内分泌科/糖尿病急症用药.md`、`规培/内科/用药速查/感染科/脓毒症初始抗感染用药.md`、`规培/内科/用药速查/急诊科/过敏反应与低血糖急救用药.md`（审计若发现与现有卡重复，可在审计文件解释并调整路径）

**Interfaces:** 新药卡仍采用 Task 1 的栏目与台账格式。

- [ ] **Step 1:** 对十个轮转科室建立“现有主题—缺口—是否新增”表，记录每个决定和目标文件路径。
- [ ] **Step 2:** 按表补心血管、消化、内分泌、感染、急诊、呼吸的关键主题；核实后修正病种卡明显冲突。
- [ ] **Step 3:** 按台账核对新页所有可操作数字；检查新增链接并提交独立 commit。

### Task 7: 发布前验收

**Files:**
- Modify: `索引.html`（由 `tools/make_reader.py` 生成）

**Interfaces:** 读取前面任务完成的 Markdown 和 README。

- [ ] **Step 1:** 运行 `python -m unittest discover -s tests -p test_make_reader.py` 和 `node --test tests/test_reader_app.js`，确认通过。
- [ ] **Step 2:** 运行 `python tools/make_reader.py`；检查新页每条目录链接能打开、HTML 不含本地资料/EPUB/患者信息。
- [ ] **Step 3:** 提交生成文件；推送并打开 GitHub Pages 核对新版入口。
