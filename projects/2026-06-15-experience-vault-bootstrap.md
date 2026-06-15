---
type: project
date: 2026-06-15
title: "Experience Vault bootstrap"
domain: codex
topics: [experience-vault, github, codex-skill, project-archive, incident-recall]
status: verified
sensitive: scrubbed
related_incidents:
  - 2026-06-15-github-ssh-push-publickey.md
extracted_knowledge:
  - 2026-06-15-github-backed-codex-experience-vault.md
---

# Experience Vault Bootstrap

## Goal

Create a durable learning loop for Codex that can preserve project experience, recall prior incidents during execution, archive completed work, extract reusable knowledge, and later promote mature patterns into Codex skills.

## Scope

Implemented the first release of a GitHub-backed Markdown vault and Codex skill:

- Local vault at `/home/l30002999/experience-vault`
- GitHub remote `git@github.com:lchany/agent-evolutionism.git`
- Codex skill at `/home/l30002999/.codex/skills/experience-vault`
- Skill backup under `skill-candidates/experience-vault/`
- OpenSpec proposal under `/home/l30002999/spec/changes/add-experience-vault`

Deferred:

- EvoSkill integration
- GEPA/DSPy optimization
- Mem0/Supermemory semantic retrieval

## Environment

- Linux server without GUI desktop
- Codex workspace: `/home/l30002999`
- GitHub SSH authentication
- Git branch: `main`

## Timeline Summary

1. Designed the Experience Vault workflow using Hermes Agent concepts as reference.
2. Created OpenSpec proposal, design, tasks, and requirement deltas.
3. Implemented the local Markdown vault structure and templates.
4. Created the `experience_vault.py` helper script.
5. Created the Codex `experience-vault` skill.
6. Initialized Git repository locally.
7. Added GitHub remote.
8. Resolved push authentication by adding the server SSH public key to GitHub.
9. Pushed the initial vault to GitHub.
10. Backed up the active Codex skill into the vault.

## Key Commands

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py validate
python /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py /home/l30002999/.codex/skills/experience-vault
git -C /home/l30002999/experience-vault remote set-url origin git@github.com:lchany/agent-evolutionism.git
git -C /home/l30002999/experience-vault push -u origin main
```

## Key Files

- `/home/l30002999/experience-vault/README.md`
- `/home/l30002999/experience-vault/scripts/experience_vault.py`
- `/home/l30002999/.codex/skills/experience-vault/SKILL.md`
- `/home/l30002999/experience-vault/skill-candidates/experience-vault/SKILL.md`
- `/home/l30002999/spec/changes/add-experience-vault/design.md`

## Problems Encountered

### HTTPS GitHub Push Failed

HTTPS push failed because the non-interactive environment could not prompt for GitHub username/token.

### SSH Push Failed Initially

SSH authentication failed with `Permission denied (publickey)` because the server public key had not been added to GitHub.

Resolution is recorded in:

- `incidents/2026-06-15-github-ssh-push-publickey.md`

## Final Solution

Use GitHub SSH remote and add the server's SSH public key to GitHub.

The durable repository is now:

```text
git@github.com:lchany/agent-evolutionism.git
```

## Verification

Validation passed:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py validate
```

Codex skill validation passed:

```bash
python /root/.codex/skills/.system/skill-creator/scripts/quick_validate.py /home/l30002999/.codex/skills/experience-vault
```

GitHub push succeeded:

```text
main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

## Residual Risks

- The vault is still small, so search quality has not been tested on a meaningful corpus.
- The current search is deterministic keyword search, not semantic search.
- GitHub authentication depends on the server SSH key remaining authorized.
- Active Codex skill installation is local; GitHub stores a backup candidate copy.

## Related Incidents

- `2026-06-15-github-ssh-push-publickey.md`

## Extracted Knowledge

- `2026-06-15-github-backed-codex-experience-vault.md`

## Sensitive Data Handling

Sensitive values were not written. GitHub authentication was documented as SSH key based. No passwords, tokens, private keys, or auth files were stored.

