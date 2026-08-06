# GitHub 网页上传教程（v1.6.0）

这份教程适合第一次使用 GitHub、希望完全通过网页完成上传的用户。

## 一、删除实验仓库

实验仓库：`dnggxiao/serial-fiction-workflow_1`

1. 打开实验仓库页面。
2. 点击仓库顶部的 `Settings`。
3. 保持在 `General` 页面并滚动到最底部的 `Danger Zone`。
4. 点击 `Delete this repository`。
5. 阅读提示，按页面要求输入仓库全名：

```text
dnggxiao/serial-fiction-workflow_1
```

6. 完成身份确认并执行永久删除。

删除仓库会永久删除该仓库的代码、Issues、设置和提交历史。确认实验仓库中没有需要保留的内容后再操作。

## 二、解压正式源码包

解压：

```text
serial-fiction-workflow-v1.6.0-official.zip
```

解压后进入最里面的：

```text
serial-fiction-workflow/
```

打开后应直接看到：

```text
README.md
LICENSE
VERSION
.gitignore
.github/
.agents/
examples/
工作流/
模板/
```

上传的是这个目录里的全部内容，不要把外层目录再套一层。

## 三、创建正式私有仓库

1. 登录 GitHub。
2. 右上角点击 `+` → `New repository`。
3. Repository name 填：

```text
serial-fiction-workflow
```

4. Description 填：

```text
A controlled AI workflow for long-form serial fiction writing.
```

5. 选择 `Private`。
6. 不要勾选 README、`.gitignore` 或 License，因为源码包中已经包含。
7. 点击 `Create repository`。

## 四、第一次上传普通文件

在空仓库页面点击：

```text
uploading an existing file
```

或：

```text
Add file → Upload files
```

建议分两次上传，避免遗漏点号目录。

第一次上传以下普通文件和目录：

```text
README.md
LICENSE
NOTICE.md
THIRD_PARTY_NOTICES.md
VERSION
CHANGELOG.md
CONTRIBUTING.md
ROADMAP.md
UPLOAD_GUIDE_ZH.md
AGENTS.md
assets/
docs/
examples/
releases/
tests/
tools/
工作流/
工作区/
模板/
正文/
示例/
迁移/
其余根目录 Markdown 文件
```

提交说明填写：

```text
release: import v1.6.0 source
```

选择直接提交到 `main`，点击 `Commit changes`。

## 五、第二次单独上传隐藏目录

再次点击 `Add file → Upload files`，明确拖入：

```text
.github/
.agents/
.gitignore
```

提交说明填写：

```text
chore: add GitHub and Skill configuration
```

这样可以避免第一次拖拽时漏掉以点号开头的项目。

## 六、上传后必须检查

返回仓库首页，确认：

- README 在首页下方正常显示；
- 根目录存在 `.github`、`.agents` 和 `.gitignore`；
- `VERSION` 内容为 `1.6.0`；
- `.github/workflows/release-check.yml` 存在；
- `.agents/skills/writing-serial-fiction/SKILL.md` 存在；
- `examples/sample-novel/` 存在；
- 仓库中没有 `__pycache__` 或 `.pyc`；
- 仓库暂时仍为 Private。

## 七、等待自动检查

打开仓库顶部 `Actions`。首次提交后应看到 `Release checks` 工作流。

绿色对勾表示测试通过。若 GitHub 要求先启用 Actions，按页面提示启用来自本仓库的工作流。

## 八、设置仓库并公开

自动检查通过后，再按 `docs/REPOSITORY_SETTINGS_ZH.md` 添加 Topics、开启 Discussions、创建 v1.6.0 Release，最后将仓库改为 Public。
