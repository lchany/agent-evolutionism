# LLM Restore And Skill Install Guide

This document is for an AI agent restoring the Experience Vault project on a new Linux environment.

## Goal

Restore the GitHub-backed Experience Vault locally, install the bundled Codex skills, install user-level operating rules, and verify the project is ready for reuse.

## Source Of Truth

- GitHub repository: `git@github.com:lchany/agent-evolutionism.git`
- HTTPS fallback: `https://github.com/lchany/agent-evolutionism.git`
- Default local path: `/home/l30002999/experience-vault`

GitHub is the durable source of truth. Treat local checkouts on shared servers as disposable caches.

## Restore Project From GitHub

Use SSH when the machine has GitHub SSH access:

```bash
mkdir -p /home/l30002999
cd /home/l30002999
git clone git@github.com:lchany/agent-evolutionism.git experience-vault
cd experience-vault
git checkout main
git pull --ff-only
```

If SSH fails with `Permission denied (publickey)`, use HTTPS for read-only restore:

```bash
mkdir -p /home/l30002999
cd /home/l30002999
git clone https://github.com/lchany/agent-evolutionism.git experience-vault
cd experience-vault
git checkout main
git pull --ff-only
```

For future push support, configure a working GitHub SSH key and switch the remote back to SSH:

```bash
git remote set-url origin git@github.com:lchany/agent-evolutionism.git
```

## Install Bundled Codex Skills

Bundled custom skills live in:

```text
codex-skills/
├── experience-vault/
└── project-memory/
```

Install them into the current Codex home:

```bash
cd /home/l30002999/experience-vault
python scripts/install_codex_skills.py --force
```

By default the script installs to:

```text
$CODEX_HOME/skills
```

If `CODEX_HOME` is not set, it installs to:

```text
~/.codex/skills
```

To install into an explicit Codex home:

```bash
python scripts/install_codex_skills.py --codex-home /home/l30002999/.codex --force
```

To install only skills and skip user-level rules:

```bash
python scripts/install_codex_skills.py --skip-agents --force
```

Manual install fallback:

```bash
mkdir -p ~/.codex/skills
cp -R codex-skills/experience-vault ~/.codex/skills/
cp -R codex-skills/project-memory ~/.codex/skills/
```

## Install User-Level Rules

The installer copies:

```text
templates/AGENTS.md
```

to:

```text
~/.codex/AGENTS.md
```

For root-run Codex sessions, install to `/root/.codex/AGENTS.md`:

```bash
python scripts/install_codex_skills.py --codex-home /root/.codex --force
```

Manual fallback:

```bash
mkdir -p ~/.codex
cp templates/AGENTS.md ~/.codex/AGENTS.md
```

## Verify Installation

Run:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py doctor
python /home/l30002999/experience-vault/scripts/experience_vault.py validate
```

Expected result:

- Vault directory exists.
- Git repository and remote are configured.
- User-level `AGENTS.md` exists.
- Active `experience-vault` skill exists.
- Vault validation passes.

If `doctor` reports the working tree has changes, inspect before pushing:

```bash
git status --short
git diff --stat
```

## How The Restored AI Should Use The System

At the start of non-trivial work:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event project-start \
  --objective "<objective>" \
  --query "<task keywords>"
```

When a command fails:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event command-failed \
  --objective "<objective>" \
  --failed-command "<command>" \
  --exit-code "<exit code>" \
  --error-text "<key error lines>"
```

At a meaningful milestone:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event milestone \
  --title "<archive title>" \
  --summary "<work summary>"
```

At project close:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event project-close \
  --title "<archive title>" \
  --summary "<final result and reusable lessons>" \
  --create-drafts
```

Before writing any archive or skill update, pull the latest GitHub state. The helper commands do this by default. Use `--no-pull` only after reviewing local state.

## Push Changes Back To GitHub

After creating archives, docs, or skill updates:

```bash
cd /home/l30002999/experience-vault
python scripts/experience_vault.py validate
git status --short
git diff --stat
python scripts/experience_vault.py sync --message "<clear commit message>"
```

Never store passwords, API keys, tokens, private keys, raw auth files, or dense sensitive logs in this repository.
