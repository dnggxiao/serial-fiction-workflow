# GitHub 仓库设置与首次 Release 教程

仓库源码上传并且 Actions 通过后，再完成下面的公开设置。

## 1. About 与 Topics

在仓库首页右侧 `About` 区域点击齿轮。

Description：

```text
A controlled AI workflow for long-form serial fiction writing.
```

Topics 建议逐项添加：

```text
ai-writing
ai-agent
novel-writing
creative-writing
long-form-fiction
writing-workflow
codex
claude-code
chinese-novel
prompt-engineering
```

保存修改。

## 2. 开启 Discussions

进入：

```text
Settings → General → Features
```

勾选：

```text
Issues
Discussions
```

Issues 用于可执行的 Bug 和功能请求；Discussions 用于使用交流、写作工作流分享和一般问答。

## 3. Template repository

确认仓库中只有空白模板和原创 Demo，没有私人小说后，可以在：

```text
Settings → General
```

勾选 `Template repository`。其他用户便可以从模板创建自己的独立小说项目。

## 4. 创建 v1.6.0 Release

打开仓库首页右侧的 `Releases`，点击 `Draft a new release`。

填写：

```text
Tag: v1.6.0
Target: main
Release title: serial-fiction-workflow v1.6.0
```

将 `releases/v1.6.0_RELEASE.md` 的正文复制到 Release 描述中。

上传以下附件：

```text
skill.zip
writing-serial-fiction-v1.6.0.zip
codex-novel-workflow-portable-v1.6.0.zip
serial-fiction-workflow-v1.6.0-official.zip
SHA256SUMS-v1.6.0.txt
```

先保存为 Draft，检查文件名和版本一致，再点击 `Publish release`。

## 5. 改为 Public

完成以下检查后再公开：

- Actions 为绿色；
- README、LICENSE、NOTICE 正常；
- 没有私人正文、账号、密钥或未授权资料；
- Release 附件均为 v1.6.0；
- `.agents` 和 `.github` 存在；
- 没有缓存或编译文件。

然后进入：

```text
Settings → General → Danger Zone → Change repository visibility
```

选择 `Make public`，按页面要求确认。

## 6. 推荐的首次公开顺序

```text
私有上传
→ 检查目录
→ 等待 Actions 通过
→ 添加 Topics 和 Discussions
→ 创建 v1.6.0 Release
→ 改为 Public
→ 发布中文介绍帖
```
