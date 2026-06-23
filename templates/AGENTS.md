# User Operating Rules

## Experience Vault

Use `/home/l30002999/experience-vault` as the default project experience system.

Because multiple projects may share this vault, ensure the local checkout is current before every read or write. `event`, `search`, `recall`, `distill`, `new`, and `archive` pull by default; use `--no-pull` only after reviewing local state.

Prefer the lifecycle `event` command during normal agent work. It wraps search, incident recall, failure tracking, archive review, and distillation in the right order while keeping the output explicit and reviewable.

For non-trivial work, before planning or executing, recall prior experience:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event project-start --objective "<objective>" --query "<task keywords>"
```

For execution failures, repeated failed attempts, SSH/Docker/NPU/CANN/MindSpeed/VERL/profiling/training errors, or when changing strategy, stop and perform incident recall before continuing:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event command-failed --objective "<objective>" --failed-command "<command>" --exit-code "<exit code>" --error-text "<key error lines>"
```

Classify retrieved records as directly applicable, partially applicable, or not applicable before reusing them.

At meaningful project milestones, after resolving reusable incidents, after verification, or at project close, review whether to archive:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event milestone --title "<archive title>" --summary "<work summary>"
python /home/l30002999/experience-vault/scripts/experience_vault.py event project-close --title "<archive title>" --summary "<final summary>" --verified --create-drafts
```

Before creating archive drafts, classify the work summary with `distill` so project-specific facts, reusable incidents, general knowledge, runbooks, and skill candidates are separated.

Do not archive a fresh root-cause hypothesis as reusable experience immediately after an error. Only create incident, knowledge, runbook, or skill-candidate records after the fix was actually tested and confirmed. Unverified analysis belongs in the active task context or a project checkpoint marked as unverified.

When the user provides facts, classify scope before storing them. Project-specific facts such as local paths, repo state, machine details, datasets, containers, current task constraints, or one-off preferences belong in project memory or project archives. Only verified cross-project facts should become reusable knowledge or runbooks.

## Durable User Rules

Treat user statements that use phrases such as "以后/后续/永远/必须/不要/默认/所有", "remember this", "from now on", "always", "must", or "never" as candidate durable rules, not ordinary experience notes.

Route durable rules by scope before continuing:

- Global behavior constraints that should affect future agents belong in this user rule file or an installed skill.
- Project-specific constraints belong in that project's `PROJECT_MEMORY.md` under `User Corrections`, `Confirmed Project Facts`, or `Invalidated Assumptions`.
- Cross-project lessons may also be archived in Experience Vault as supporting `knowledge/` or `runbooks/`, but vault archival alone is not enough for hard constraints that must trigger reliably.

When a user gives a durable rule, record it in the highest-priority active layer first, then optionally create or update the lower-priority evidence record in Experience Vault. If the rule is sensitive, redact secrets before writing it anywhere.

Active global rule: when creating Docker containers for the user's Ascend/NPU, VERL, vLLM-Ascend, CANN, torch_npu, or related shared training workflows, include both shared mounts unless the user explicitly overrides the rule:

```bash
-v /mnt/disk2t:/mnt/disk2t \
-v /mnt/sfs_turbo:/mnt/sfs_turbo
```

After container creation, verify both paths are visible inside the container.

Never store passwords, API keys, tokens, private keys, raw auth files, or dense sensitive logs in Experience Vault.

## Project Memory

Use `$project-memory` for non-trivial project work, context compaction recovery, user corrections, and durable project-specific facts.

Maintain `<project>/PROJECT_MEMORY.md` for facts that belong to one project, such as dataset roots, output directories, container names, experiment configuration, machine constraints, current task state, user corrections, and invalidated assumptions.

At the start of project work, after context compaction, or when resuming a task, read `PROJECT_MEMORY.md` if it exists before relying on old summaries. Treat `User Corrections` and `Invalidated Assumptions` as higher priority than prior assistant conclusions.

When the user corrects an assistant conclusion, update `PROJECT_MEMORY.md` with both the correct value and the wrong assumption that must not be reused. Do not store raw logs or dense command output there; store durable conclusions and evidence pointers instead.

## Shell Output Context Policy

For log/query commands, minimize context impact:

- Prefer `tail`, `rg`, `sed -n`, `jq`, and targeted filters.
- Do not print full logs, full JSON, full directory trees, or full command output unless explicitly requested.
- For large outputs, redirect to `/tmp/*.out` and only show relevant excerpts.
- Use small tool output budgets for exploratory shell commands.
- Summarize inspected shell output into findings instead of preserving raw output.

## Python Code Review

After writing or modifying Python scripts, perform a code-review pass before finalizing the task.
Prioritize correctness bugs, edge cases, error handling, maintainability, and missing tests.
Report any findings with file and line references; if no issues are found, say so and note any test coverage gaps.
