---
name: writing-serial-fiction
description: "Use when a Chinese serial-fiction workflow explicitly requests chapter planning from supplied facts, prose writing from a supplied prose-minimal packet and scene card, or readonly diagnosis of reader experience. Preserve fixed plot and continuity while making craft invisible through concrete causal scenes, compressed repeated proof, distinct pressured dialogue, natural narration, visible payoff, and precise endings."
---

# 中文连载小说写作引擎

一次调用只执行一种模式。要求调用方显式提供：

`$writing-serial-fiction mode=<模式>`

允许的模式：

- `chapter-planning`
- `prose-writing`
- `readonly-diagnosis`

## 先处理输入

按以下优先级返回错误，且不要附带半成品：

1. 同时提供多个受支持模式：`INPUT_ERROR: multiple_modes`
2. 未提供模式或模式无效：`INPUT_ERROR: mode`
3. 必填字段缺失：`INPUT_ERROR: missing=<字段1>,<字段2>`
4. 输入中的硬事实无法同时成立：`BLOCKED: <最短冲突说明>`

`BLOCKED:` 只用于事实冲突，不代替字段缺失。

## 共同边界

- 只使用调用方已经提供的材料；不要自行打开文件、历史章节、长期资料或网站。
- 固定事件、结果、人物决定、结尾落点和禁区优先于任何写作手法。
- 不新增重要人物、支线、核心设定或长期伏笔。
- 不负责命令路由、文件保存、阶段变化、轻检、修正、转正或状态更新。
- 不承诺流量、读完率或固定效果，不把方法写成机械数量公式。
- 写作方法只在幕后起作用；规划卡与正文不得写成课程讲解、审计报告、合同条款或规则宣言。

## 按模式加载

### `chapter-planning`

读取 `references/technique-selector.md` 和
`references/chapter-planning.md`。默认不读取任何平台 profile。

### `prose-writing`

正文写作只接受“正文最小包＋场景执行卡”这两个输入。
读取 `references/prose-writing.md` 和
`references/natural-prose-patterns.md`。不要同时执行诊断或规划。

### `readonly-diagnosis`

读取 `references/readonly-diagnosis.md` 和
`references/natural-prose-patterns.md`。这是独立只读评估，不进入章节生产、
轻检或修正流程。

## 可选平台参考

`references/fanqie-cn-profile.md` 是可选平台参考，默认不读取。只有调用方明确要求
番茄中文网文写作参考、相关方法出处或来源解释时才读取；不得把其中的方法当作
通用强制公式，也不得声称本 Skill 获得番茄官方认证或效果背书。需要说明来源时，
明确区分 `[官方主题]` 与 `[Skill归纳]`。
