---
type: knowledge
date: 2026-06-15
title: "GitHub-backed Codex Experience Vault"
domain: codex
topics: [experience-vault, github, markdown, codex-skill, shared-server]
applies_to: [Codex, shared Linux server, GitHub private repository, Markdown knowledge base]
confidence: verified
risk: medium
source_projects:
  - 2026-06-15-experience-vault-bootstrap.md
source_incidents:
  - 2026-06-15-github-ssh-push-publickey.md
last_verified: 2026-06-15
sensitive: scrubbed
skill_candidate: true
---

# GitHub-backed Codex Experience Vault

## Applicability

Use this pattern when Codex runs on a shared or disposable Linux server and project experience must survive across sessions, machines, or environment resets.

This pattern is especially useful when the user wants Codex to:

- Recall prior project experience before starting work.
- Search prior incidents during troubleshooting.
- Archive completed projects.
- Extract reusable knowledge cards.
- Promote mature workflows into Codex skills.

## Trigger Signals

- The server has no durable local storage guarantee.
- The user wants experience reuse across future projects.
- The user wants GitHub as the authoritative storage.
- The user wants Obsidian or Markdown-compatible viewing later.
- The task involves repeated operational patterns such as SSH, Docker, NPU, CANN, MindSpeed, VERL, profiling, or deployment work.

## Required Inputs

- Private GitHub repository URL.
- Local checkout path.
- Git authentication method.
- Markdown templates.
- Redaction policy for sensitive data.

## Procedure

1. Create or select a private GitHub repository.
2. Create a local vault checkout on the server.
3. Initialize standard folders:
   - `projects/`
   - `incidents/`
   - `knowledge/`
   - `runbooks/`
   - `skill-candidates/`
   - `evals/`
   - `index/`
   - `templates/`
4. Add templates for project, incident, knowledge, runbook, skill candidate, and eval examples.
5. Add a helper script for deterministic search, record creation, validation, and Git review.
6. Add a Codex skill that defines when to search, when to archive, and how to classify applicability.
7. Initialize Git and bind the remote.
8. Validate and push.
9. During future projects, pull before recall and push after reviewed archival changes.

## Non-Applicable Cases

- Do not use this as a secret store.
- Do not store raw sensitive logs.
- Do not treat first-time tentative knowledge as a mature runbook.
- Do not automatically install generated skills without review.
- Do not add Mem0/Supermemory until Markdown search becomes insufficient.

## Verification Method

Verify:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py validate
git -C /home/l30002999/experience-vault status --short
git -C /home/l30002999/experience-vault remote -v
```

For Codex skill validation:

```bash
python /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py /home/l30002999/.codex/skills/experience-vault
```

## Risk And Safety Notes

- GitHub repository should be private.
- Always redact passwords, tokens, keys, and dense sensitive logs.
- Review `git diff` before pushing.
- Treat local checkout as cache, not source of truth.
- Human approval is required before replacing active Codex skills.

## Source Evidence

Validated by the initial Experience Vault bootstrap on 2026-06-15.

## Promotion Notes

This pattern is already represented by the local Codex `experience-vault` skill and backed up under `skill-candidates/experience-vault/`.

