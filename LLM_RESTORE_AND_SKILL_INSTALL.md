# LLM Restore And Skill Install Guide

This document is for an AI agent restoring the Experience Vault project on a new Linux environment.

## Goal

Restore the GitHub-backed Experience Vault locally, install the bundled agent skills, install user-level operating rules for the target client, and verify the project is ready for reuse.

## Source Of Truth

- GitHub repository: `git@github.com:lchany/agent-evolutionism.git`
- HTTPS fallback: `https://github.com/lchany/agent-evolutionism.git`
- Local path: ask the user first. If the user does not provide a directory, restore under the current working directory as `./experience-vault`.

GitHub is the durable source of truth. Treat local checkouts on shared servers as disposable caches.

## Restore Project From GitHub

Use SSH when the machine has GitHub SSH access:

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

If SSH fails with `Permission denied (publickey)`, use HTTPS for read-only restore:

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

For future push support, configure a working GitHub SSH key and switch the remote back to SSH:

```bash
git remote set-url origin git@github.com:lchany/agent-evolutionism.git
```

## Install Bundled Agent Skills

Bundled custom skills live in:

```text
agent-skills/
├── ascend-docker-rules/
├── experience-vault/
└── project-memory/
```

These are portable `SKILL.md` packages. Do not assume they are Codex-only. Install or adapt them according to the target agent client's skill mechanism.

Client mapping:

- Codex or Codex-compatible clients: copy each skill directory under `<agent-home>/skills/`, and use `AGENTS.md` as user-level rules when supported.
- Claude Code or clients that use project/user instruction files: reuse the same `SKILL.md` content, but place it in the client's supported skill or instruction location. If the client does not support skill folders, convert the relevant `SKILL.md` workflow into that client's instruction file.
- Other agent clients: preserve each skill's trigger description, workflow steps, safety rules, and bundled references/scripts; only change the installation path and metadata format required by that client.

Install into an explicit agent home:

```bash
cd "$EXPERIENCE_VAULT_DIR"
python scripts/install_agent_skills.py --agent-home <agent-home> --force
```

By default the script installs to:

```text
$AGENT_HOME/skills
```

If `AGENT_HOME` is not set, it falls back to:

```text
$CODEX_HOME/skills
```

If neither variable is set, it installs to:

```text
~/.codex/skills
```

The `--codex-home` option still works as a backward-compatible alias:

```bash
python scripts/install_agent_skills.py --codex-home <codex-home> --force
```

To install only skills and skip user-level rules:

```bash
python scripts/install_agent_skills.py --skip-agents --force
```

Manual install fallback:

```bash
mkdir -p <client-skill-dir>
cp -R agent-skills/ascend-docker-rules <client-skill-dir>/
cp -R agent-skills/experience-vault <client-skill-dir>/
cp -R agent-skills/project-memory <client-skill-dir>/
```

## Install User-Level Rules

The installer copies the repository's default user rules:

```text
templates/AGENTS.md
```

to:

```text
~/.codex/AGENTS.md
```

This path is appropriate for Codex-compatible clients. For other clients, adapt the content of `templates/AGENTS.md` into the client's supported user or project instruction file instead of assuming the filename is valid.

`templates/AGENTS.md` is the portable source for user-level hard rules. When restoring to a new client, preserve the `Durable User Rules` section, especially rules that must not depend only on Experience Vault keyword retrieval. The current active rule is: when creating Docker containers for the user's Ascend/NPU, VERL, vLLM-Ascend, CANN, torch_npu, or related shared training workflows, include `/mnt/disk2t` and `/mnt/sfs_turbo` mounts by default and verify both paths inside the container unless the user explicitly overrides the rule.

For root-run Codex-compatible sessions, install to `/root/.codex/AGENTS.md`:

```bash
python scripts/install_agent_skills.py --agent-home /root/.codex --force
```

Manual fallback:

```bash
mkdir -p ~/.codex
cp templates/AGENTS.md ~/.codex/AGENTS.md
```

## Verify Installation

Run:

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" doctor
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" validate
```

Expected result:

- Vault directory exists.
- Git repository and remote are configured.
- For Codex-compatible installs, user-level `AGENTS.md` exists.
- The `experience-vault` skill exists in the target client's skill or instruction location.
- The `project-memory` and `ascend-docker-rules` skills exist in the target client's skill or instruction location.
- The user-level rules preserve the `Durable User Rules` section.
- Vault validation passes.

If `doctor` reports the working tree has changes, inspect before pushing:

```bash
git status --short
git diff --stat
```

## How The Restored AI Should Use The System

At the start of non-trivial work:

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" event project-start \
  --objective "<objective>" \
  --query "<task keywords>"
```

When a command fails:

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" event command-failed \
  --objective "<objective>" \
  --failed-command "<command>" \
  --exit-code "<exit code>" \
  --error-text "<key error lines>"
```

When the user provides a long-lived rule, hard constraint, or future behavior requirement, such as statements containing "always", "must", "never", "from now on", "以后", "后续", "所有", "必须", "不要", or "默认", do not store it only as `knowledge/`. First promote it into the target client's user-level rules, a dedicated skill, or the relevant project's `PROJECT_MEMORY.md`; then optionally archive supporting evidence in Experience Vault.

At a meaningful milestone:

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" event milestone \
  --title "<archive title>" \
  --summary "<work summary>"
```

At project close:

```bash
python "$EXPERIENCE_VAULT_DIR/scripts/experience_vault.py" event project-close \
  --title "<archive title>" \
  --summary "<final result and reusable lessons>" \
  --verified \
  --create-drafts
```

Use `--verified` only after the root cause, fix, or reusable lesson was actually tested. If the work is still a hypothesis, do not create reusable archive drafts.

Before writing any archive or skill update, pull the latest GitHub state. The helper commands do this by default. Use `--no-pull` only after reviewing local state.

## Push Changes Back To GitHub

After creating archives, docs, or skill updates:

```bash
cd "$EXPERIENCE_VAULT_DIR"
python scripts/experience_vault.py validate
git status --short
git diff --stat
python scripts/experience_vault.py sync --message "<clear commit message>"
```

Never store passwords, API keys, tokens, private keys, raw auth files, or dense sensitive logs in this repository.
