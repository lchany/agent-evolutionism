# User Operating Rules

## Experience Vault

Use `/home/l30002999/experience-vault` as the default project experience system.

For non-trivial work, before planning or executing, search prior experience:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py search --mode project-start --query "<task keywords>"
```

For execution failures, repeated failed attempts, SSH/Docker/NPU/CANN/MindSpeed/VERL/profiling/training errors, or when changing strategy, stop and perform incident recall before continuing:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py search --mode incident --query "<error command framework keywords>"
```

Classify retrieved records as directly applicable, partially applicable, or not applicable before reusing them.

At meaningful project milestones or project close, archive reusable experience into the vault and push after validation and review.

Never store passwords, API keys, tokens, private keys, raw auth files, or dense sensitive logs in Experience Vault.

## Python Code Review

After writing or modifying Python scripts, perform a code-review pass before finalizing the task.
Prioritize correctness bugs, edge cases, error handling, maintainability, and missing tests.
Report any findings with file and line references; if no issues are found, say so and note any test coverage gaps.
