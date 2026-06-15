# Workspace Automation

The active workspace uses `/home/l30002999/AGENTS.md` to make Experience Vault recall a default Codex behavior.

## Default Recall

For non-trivial work, Codex should search:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py search --mode project-start --query "<task keywords>"
```

## Incident Recall

For command failures, repeated failed attempts, SSH/Docker/NPU/CANN/MindSpeed/VERL/profiling/training errors, user correction, or strategy changes, Codex should search:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py search --mode incident --query "<error command framework keywords>"
```

## Restore On A New Machine

After cloning the vault, copy the workspace rule if this checkout should control the workspace:

```bash
cp /home/l30002999/experience-vault/templates/AGENTS.md /home/l30002999/AGENTS.md
```

Then adjust paths if the vault checkout is not `/home/l30002999/experience-vault`.

## Limitation

This is semi-automatic. Codex can follow the workspace rule when the workspace instructions are loaded, but it is not a background daemon and cannot intercept shell failures outside a Codex turn.
