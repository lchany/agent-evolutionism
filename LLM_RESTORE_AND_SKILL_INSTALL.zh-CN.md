# LLM 项目恢复与 Skills 安装指南

本文档给接手环境的 AI 阅读，用于在新的 Linux 服务器上恢复 Experience Vault 项目，并安装或适配配套的 agent skills。

## 目标

完成以下事情：

1. 从 GitHub 拉取 Experience Vault 到本地。
2. 安装仓库内打包好的 agent skills。
3. 按目标 agent 客户端安装或转换用户级规则。
4. 验证项目、skills、GitHub 同步能力可用。
5. 明确后续 AI 应该如何使用这套经验系统。

## 唯一可信来源

- GitHub SSH 仓库：`git@github.com:lchany/agent-evolutionism.git`
- HTTPS 只读备用地址：`https://github.com/lchany/agent-evolutionism.git`
- 本地恢复路径：先询问用户。用户没有指定时，在当前目录下恢复为 `./experience-vault`。

GitHub 是长期可信来源。本地目录只当作缓存，尤其是在多人共用服务器上，不要假设本地内容一定最新。

## 从 GitHub 恢复项目

优先使用 SSH 克隆，因为后续需要推送归档和 skill 更新：

```bash
WORKSPACE_DIR="${WORKSPACE_DIR:-$(pwd)}"
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"
git clone git@github.com:lchany/agent-evolutionism.git experience-vault
export EXPERIENCE_VAULT_DIR="$WORKSPACE_DIR/experience-vault"
cd "$EXPERIENCE_VAULT_DIR"
git checkout main
git pull --ff-only
```

如果 SSH 报错 `Permission denied (publickey)`，说明当前机器没有可用的 GitHub SSH key。此时可以先用 HTTPS 做只读恢复：

```bash
WORKSPACE_DIR="${WORKSPACE_DIR:-$(pwd)}"
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"
git clone https://github.com/lchany/agent-evolutionism.git experience-vault
export EXPERIENCE_VAULT_DIR="$WORKSPACE_DIR/experience-vault"
cd "$EXPERIENCE_VAULT_DIR"
git checkout main
git pull --ff-only
```

如果之后需要推送到 GitHub，先配置可用的 SSH key，然后把 remote 切回 SSH：

```bash
git remote set-url origin git@github.com:lchany/agent-evolutionism.git
```

## 安装仓库内置 Agent Skills

仓库内已经打包了当前自定义 skills：

```text
agent-skills/
├── ascend-docker-rules/
├── experience-vault/
└── project-memory/
```

推荐用安装脚本安装：

这些 skills 是通用的 `SKILL.md` 能力包，不是 Codex 专属。不同 agent 客户端的安装位置、元数据格式、用户规则文件名可能不同，恢复时应按目标客户端适配。

客户端适配原则：

- Codex 或兼容 Codex skills 目录的客户端：把每个 skill 目录复制到 `<agent-home>/skills/`，并在支持时使用 `AGENTS.md` 作为用户级规则。
- Claude Code 或使用用户/项目指令文件的客户端：复用 `SKILL.md` 的触发条件、流程和安全规则，但放到该客户端支持的 skill 或指令位置；如果不支持 skill 目录，就把相关 workflow 转成客户端的说明文件。
- 其他 agent 客户端：保留 skill 的触发描述、执行步骤、安全边界、references/scripts，只调整安装路径和客户端要求的元数据格式。

安装到显式 agent home：

```bash
cd "$EXPERIENCE_VAULT_DIR"
python scripts/install_agent_skills.py --agent-home <agent-home> --force
```

默认安装位置是：

```text
$AGENT_HOME/skills
```

如果没有设置 `AGENT_HOME`，脚本会回退使用：

```text
$CODEX_HOME/skills
```

如果两个环境变量都没有设置，脚本会安装到：

```text
~/.codex/skills
```

`--codex-home` 仍然保留为兼容旧命令的别名：

```bash
python scripts/install_agent_skills.py --codex-home <codex-home> --force
```

如果目标客户端以 root 用户运行，且使用 `/root/.codex` 作为 agent home：

```bash
python scripts/install_agent_skills.py --agent-home /root/.codex --force
```

如果只想安装 skills，不想覆盖用户级规则：

```bash
python scripts/install_agent_skills.py --skip-agents --force
```

手动安装方式：

```bash
mkdir -p <client-skill-dir>
cp -R agent-skills/ascend-docker-rules <client-skill-dir>/
cp -R agent-skills/experience-vault <client-skill-dir>/
cp -R agent-skills/project-memory <client-skill-dir>/
```

## 安装用户级 AGENTS.md

安装脚本会把默认用户规则：

```text
templates/AGENTS.md
```

复制到：

```text
~/.codex/AGENTS.md
```

这个路径适用于 Codex 兼容客户端。其他客户端不要硬套 `AGENTS.md` 文件名，应把 `templates/AGENTS.md` 的内容转换到该客户端支持的用户级或项目级指令文件中。

`templates/AGENTS.md` 是可迁移的用户级硬规则来源。恢复到新客户端时，必须保留其中的 `Durable User Rules` 段落，尤其是那些不能只依赖 Experience Vault 检索的长期规则。当前包括：创建用户的 Ascend/NPU、VERL、vLLM-Ascend、CANN、torch_npu 或相关共享训练容器时，默认必须挂载 `/mnt/disk2t` 和 `/mnt/sfs_turbo`，并在容器创建后验证两个路径可见，除非用户显式覆盖该规则。

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
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" doctor
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" validate
```

正常情况下应看到：

- vault 目录存在。
- Git 仓库存在。
- Git remote 已配置。
- 对 Codex 兼容安装，用户级 `AGENTS.md` 存在。
- `experience-vault` skill 已存在于目标客户端的 skill 或指令位置。
- `project-memory` 和 `ascend-docker-rules` skills 已存在于目标客户端的 skill 或指令位置。
- 用户级规则中保留了 `Durable User Rules` 段落。
- vault 结构和内容校验通过。

如果 `doctor` 显示 working tree 有变更，先检查再推送：

```bash
git status --short
git diff --stat
```

## 恢复后的 AI 应如何使用

开始任何非简单任务前，先检索历史经验：

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" event project-start \
  --objective "<当前目标>" \
  --query "<任务关键词>"
```

当用户给出长期规则、硬约束或未来行为要求时，例如包含“以后、后续、所有、必须、不要、默认、always、must、never”等信号，不要只把它归档为 `knowledge/`。先把规则写入目标客户端的用户级规则、专门 skill，或相关项目的 `PROJECT_MEMORY.md`，再按需要创建 Experience Vault 记录作为证据。

命令失败时，先做失败指纹、失败计数和事故召回：

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" event command-failed \
  --objective "<当前目标>" \
  --failed-command "<失败命令>" \
  --exit-code "<退出码>" \
  --error-text "<关键错误行>"
```

阶段性完成后，评审是否需要归档：

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" event milestone \
  --title "<归档标题>" \
  --summary "<工作摘要>"
```

项目结束时，提炼并创建推荐归档草稿：

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" event project-close \
  --title "<归档标题>" \
  --summary "<最终结果和可复用经验>" \
  --verified \
  --create-drafts
```

只有在根因、修复方案或可复用经验已经实际测试确认后，才使用 `--verified`。如果还只是推测或未验证结论，不要创建可复用归档草稿。

## 推送变更回 GitHub

新增归档、文档或 skill 更新后，按以下顺序操作：

```bash
cd "$EXPERIENCE_VAULT_DIR"
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
