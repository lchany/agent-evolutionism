# LLM 项目恢复与 Skills 安装指南

本文档给接手环境的 AI 阅读，用于在新的 Linux 服务器上恢复 Experience Vault 项目，并安装配套的 Codex skills。

## 目标

完成以下事情：

1. 从 GitHub 拉取 Experience Vault 到本地。
2. 安装仓库内打包好的 Codex skills。
3. 安装用户级 `AGENTS.md` 规则。
4. 验证项目、skills、GitHub 同步能力可用。
5. 明确后续 AI 应该如何使用这套经验系统。

## 唯一可信来源

- GitHub SSH 仓库：`git@github.com:lchany/agent-evolutionism.git`
- HTTPS 只读备用地址：`https://github.com/lchany/agent-evolutionism.git`
- 默认本地路径：`/home/l30002999/experience-vault`

GitHub 是长期可信来源。本地目录只当作缓存，尤其是在多人共用服务器上，不要假设本地内容一定最新。

## 从 GitHub 恢复项目

优先使用 SSH 克隆，因为后续需要推送归档和 skill 更新：

```bash
mkdir -p /home/l30002999
cd /home/l30002999
git clone git@github.com:lchany/agent-evolutionism.git experience-vault
cd experience-vault
git checkout main
git pull --ff-only
```

如果 SSH 报错 `Permission denied (publickey)`，说明当前机器没有可用的 GitHub SSH key。此时可以先用 HTTPS 做只读恢复：

```bash
mkdir -p /home/l30002999
cd /home/l30002999
git clone https://github.com/lchany/agent-evolutionism.git experience-vault
cd experience-vault
git checkout main
git pull --ff-only
```

如果之后需要推送到 GitHub，先配置可用的 SSH key，然后把 remote 切回 SSH：

```bash
git remote set-url origin git@github.com:lchany/agent-evolutionism.git
```

## 安装仓库内置 Codex Skills

仓库内已经打包了当前自定义 skills：

```text
codex-skills/
├── experience-vault/
└── project-memory/
```

推荐用安装脚本安装：

```bash
cd /home/l30002999/experience-vault
python scripts/install_codex_skills.py --force
```

默认安装位置是：

```text
$CODEX_HOME/skills
```

如果没有设置 `CODEX_HOME`，脚本会安装到：

```text
~/.codex/skills
```

如果需要指定 Codex home，例如安装到 `/home/l30002999/.codex`：

```bash
python scripts/install_codex_skills.py --codex-home /home/l30002999/.codex --force
```

如果 Codex 以 root 用户运行，需要安装到 `/root/.codex`：

```bash
python scripts/install_codex_skills.py --codex-home /root/.codex --force
```

如果只想安装 skills，不想覆盖用户级规则：

```bash
python scripts/install_codex_skills.py --skip-agents --force
```

手动安装方式：

```bash
mkdir -p ~/.codex/skills
cp -R codex-skills/experience-vault ~/.codex/skills/
cp -R codex-skills/project-memory ~/.codex/skills/
```

## 安装用户级 AGENTS.md

安装脚本会把：

```text
templates/AGENTS.md
```

复制到：

```text
~/.codex/AGENTS.md
```

如果需要手动安装：

```bash
mkdir -p ~/.codex
cp templates/AGENTS.md ~/.codex/AGENTS.md
```

如果 Codex 运行在 root 用户下，手动安装路径应为：

```bash
mkdir -p /root/.codex
cp templates/AGENTS.md /root/.codex/AGENTS.md
```

## 验证恢复结果

执行：

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py doctor
python /home/l30002999/experience-vault/scripts/experience_vault.py validate
```

正常情况下应看到：

- vault 目录存在。
- Git 仓库存在。
- Git remote 已配置。
- 用户级 `AGENTS.md` 存在。
- active `experience-vault` skill 存在。
- vault 结构和内容校验通过。

如果 `doctor` 显示 working tree 有变更，先检查再推送：

```bash
git status --short
git diff --stat
```

## 恢复后的 AI 应如何使用

开始任何非简单任务前，先检索历史经验：

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event project-start \
  --objective "<当前目标>" \
  --query "<任务关键词>"
```

命令失败时，先做失败指纹、失败计数和事故召回：

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event command-failed \
  --objective "<当前目标>" \
  --failed-command "<失败命令>" \
  --exit-code "<退出码>" \
  --error-text "<关键错误行>"
```

阶段性完成后，评审是否需要归档：

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event milestone \
  --title "<归档标题>" \
  --summary "<工作摘要>"
```

项目结束时，提炼并创建推荐归档草稿：

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event project-close \
  --title "<归档标题>" \
  --summary "<最终结果和可复用经验>" \
  --create-drafts
```

## 推送变更回 GitHub

新增归档、文档或 skill 更新后，按以下顺序操作：

```bash
cd /home/l30002999/experience-vault
python scripts/experience_vault.py validate
git status --short
git diff --stat
python scripts/experience_vault.py sync --message "<清晰的提交信息>"
```

`search`、`recall`、`distill`、`new`、`archive` 和 `event` 默认会先拉取 GitHub 最新状态。只有在确认本地状态安全后，才使用 `--no-pull`。

## 安全规则

不要把以下内容写入仓库：

- 密码
- API key
- token
- 私钥
- 原始认证文件
- 大段敏感日志
- 原始 tensor dump
- 客户机器标识或账号信息

如果必须记录问题现象，只保留可复用结论、关键错误特征、验证方法和脱敏后的证据指针。
