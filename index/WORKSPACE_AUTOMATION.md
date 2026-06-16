# User-Level Automation

The active Codex user uses `/root/.codex/AGENTS.md` to make Experience Vault recall a default behavior across workspaces.

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

After cloning the vault, copy the user-level rule for the Codex runtime user:

```bash
mkdir -p /root/.codex
cp /home/l30002999/experience-vault/templates/AGENTS.md /root/.codex/AGENTS.md
```

Then adjust paths if the vault checkout is not `/home/l30002999/experience-vault`.

## Limitation

This is semi-automatic. Codex can follow the user-level rule when user instructions are loaded, but it is not a background daemon and cannot intercept shell failures outside a Codex turn.
