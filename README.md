<p align="center">
  <img src="assets/banner.svg" alt="serial-fiction-workflow banner" width="900">
</p>

# serial-fiction-workflow

> **Version 1.6.0** · A controlled AI workflow for long-form serial fiction writing.

让 AI 协助写长篇小说，同时让作者继续掌控剧情、人物、世界观和章节状态。

本项目不是“一键生成整本书”的工具。它把长篇创作拆成可确认、可检查、可回滚的步骤：

```text
作者提供事实与方向
        ↓
章节规划与场景执行卡
        ↓
作者确认
        ↓
AI 生成正文
        ↓
独立轻检
        ↓
通过后更新连续状态
```

## 为什么需要这套工作流

普通对话式写作容易出现：

- 忘记前文已经发生的事实；
- 擅自修改人物决定或世界规则；
- 把大纲、状态表和解释性语言直接写进正文；
- 一次修改同时污染正文和长期状态；
- 在章节末尾机械盘点所有未解决事项。

本项目通过文件化记忆、正文最小输入、人工确认门和独立检查阶段降低这些问题。

## 核心能力

- 长篇连续性与已发生事实管理；
- 章节级规划和 2～4 个可执行场景；
- 正文最小包与规划资料隔离；
- 场景执行卡驱动的正文生成；
- 独立只读诊断与章节轻检；
- 轻检通过前禁止更新正式正文和连续状态；
- 支持 Codex 项目工作区与独立 Skill；
- 可选番茄中文网文参考，但默认不加载、非官方认证。

## 快速开始

### 方案 A：使用完整 Codex 工作流

1. 从 Releases 下载 `codex-novel-workflow-portable-v1.6.0.zip`。
2. 解压到一个新目录。
3. 用 Codex 打开解压后的项目根目录。
4. 按 `README_迁移.md` 或 `新项目启动提示词.md` 初始化小说资料。
5. 使用命令准备章节、确认执行卡、生成正文和运行轻检。

### 方案 B：只安装独立 Skill

1. 从 Releases 下载 `skill.zip`。
2. 在支持 Skills 的 ChatGPT/Codex 环境中安装该 ZIP。
3. 显式调用一种模式：

```text
$writing-serial-fiction mode=chapter-planning
$writing-serial-fiction mode=prose-writing
$writing-serial-fiction mode=readonly-diagnosis
```

一次调用只执行一种模式。独立 Skill 不会自动打开你的历史章节或项目文件，所需事实必须由调用方提供。

正文模型只接收两个输入：正文最小包和场景执行卡；生成后执行一轮静默删重，再交给独立轻检。

## 三种 Skill 模式

| 模式 | 用途 | 主要输入 |
| --- | --- | --- |
| `chapter-planning` | 把章节事实转成可执行场景 | 固定事件、人物目标、结尾落点、禁区 |
| `prose-writing` | 根据执行卡生成自然正文 | 正文最小包＋场景执行卡 |
| `readonly-diagnosis` | 只读分析现有章节体验 | 章节正文＋必要背景 |

## Demo

查看 [`examples/sample-novel/`](examples/sample-novel/) 中的原创示例《雾港回声》。它展示：

- 世界观和人物资料；
- 连续状态；
- 第一卷大纲；
- 第 001 章场景执行卡；
- 正文初稿；
- 轻检报告。

## 仓库结构

```text
serial-fiction-workflow/
├── .agents/skills/writing-serial-fiction/  # 内嵌 Skill
├── .github/                                # Issue、PR、CI 配置
├── examples/sample-novel/                  # 原创演示项目
├── tests/                                  # 工作流和 Skill 守卫测试
├── tools/                                  # 清单与发布校验工具
├── 工作流/                                 # 准备、正文、轻检、修正
├── 模板/                                   # 资料包、执行卡和报告模板
├── 01_剧情主线.md
├── 02_连续状态表.md
├── 03_大纲.md
├── 04_章节细纲.md
└── 05_写作规则卡.md
```

## GitHub 上传与发布

第一次接触 GitHub，请先阅读：

- [`UPLOAD_GUIDE_ZH.md`](UPLOAD_GUIDE_ZH.md)：删除实验仓库、网页上传和检查步骤；
- [`docs/REPOSITORY_SETTINGS_ZH.md`](docs/REPOSITORY_SETTINGS_ZH.md)：Topics、Discussions、公开设置和 Release 发布。

## 从旧 Skill 名称迁移

v1.4.0 起，调用令牌已从 `$writing-fanqie-serial-fiction` 改为：

```text
$writing-serial-fiction
```

详细映射见 [`迁移/05_v1.4.0_技能命名迁移.md`](迁移/05_v1.4.0_技能命名迁移.md)。

## 测试

在项目根目录执行：

```bash
python -m pip install pytest
python -m pytest -q
```

GitHub Actions 会在每次 Push 和 Pull Request 时自动执行同一套测试。

完整项目中的工作流 03、04 分别负责独立轻检和条件修正；它们不属于独立 Skill 的三种模式。

## 贡献

欢迎贡献文档、测试、通用写作模板、检查规则和兼容性改进。提交前请阅读 [`CONTRIBUTING.md`](CONTRIBUTING.md)。

## 许可证与内容权利

项目原创代码、提示词、模板和文档使用 [MIT License](LICENSE)。

小说正文、剧情设定、连续状态、文风样本和其他用户内容，**不会因为放入本项目目录而自动采用 MIT License**。详细边界见 [`NOTICE.md`](NOTICE.md) 和 [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)。

本项目与番茄小说网及其他第三方平台无官方隶属、认证、赞助或效果背书关系。
