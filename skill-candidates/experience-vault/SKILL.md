---
name: experience-vault
description: Use this skill to preserve and reuse project experience through a GitHub-backed Markdown vault. Trigger when starting a non-trivial project, debugging, deployment, NPU/Ascend/CANN/MindSpeed/VERL/profiling/training work, SSH or Docker troubleshooting, execution failures, repeated failed attempts, user requests to recall prior experience, project archival, knowledge extraction, runbook promotion, Codex skill candidate creation, or future EvoSkill/GEPA optimization planning.
---

# Experience Vault

Use Experience Vault as the durable learning loop for Codex work. The vault stores project archives, incidents, reusable knowledge, runbooks, skill candidates, and eval data in Markdown.

Default vault path:

```bash
/home/l30002999/experience-vault
```

GitHub is the intended durable source of truth. Treat the local checkout as a disposable cache on shared servers.

## Core Rule

Before acting on a non-trivial task, or after a meaningful failure during execution, search Experience Vault for relevant prior experience. Do not blindly apply retrieved steps; classify applicability first.

## Workflows

### 1. Project Start Recall

Use when the user starts a non-trivial task.

Steps:

1. If the vault is a Git repo with a remote, run `git pull` unless the user asked not to sync.
2. Build a problem fingerprint from the request:
   - Objective
   - Domain and framework
   - Commands, paths, files, logs, and constraints if available
3. Search in this order:
   - `runbooks/`
   - `knowledge/`
   - `incidents/`
   - `projects/`
4. Classify each useful hit:
   - `directly applicable`
   - `partially applicable`
   - `not applicable`
5. Summarize what should be reused and what must not be reused.
6. Continue planning or implementation.

Command:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py search \
  --mode project-start \
  --query "<task keywords>"
```

### 2. In-Progress Incident Recall

Use when work is already underway and a problem appears.

Trigger on:

- Command failure
- Build/test/training/deployment/profiling failure
- SSH, Docker, NPU, CANN, MindSpeed, VERL, or environment failure
- Two related attempts failing in the same direction
- User correction
- User asks whether this happened before
- Codex is about to switch strategy

Steps:

1. Stop exploratory retries.
2. Build an incident fingerprint:
   - Failed command
   - Exit code if available
   - Key error lines
   - Current objective
   - Current path
   - Framework/tool names
   - Attempts already made
3. Redact sensitive values before writing or searching persistent records.
4. Search in this order:
   - `incidents/`
   - `knowledge/`
   - `runbooks/`
   - `projects/`
5. Explain applicability and next action before continuing.

Command:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py search \
  --mode incident \
  --query "<error command framework keywords>"
```

If a concrete command failed, first build a sanitized fingerprint and use its suggested query:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py fingerprint \
  --objective "<current objective>" \
  --command "<failed command>" \
  --exit-code "<exit code>" \
  --error-text "<key error lines>"
```

For repeated related failures, track attempts. When the threshold is reached, stop exploratory retries and run the suggested incident recall:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py fail-track \
  --objective "<current objective>" \
  --command "<failed command>" \
  --error-text "<key error lines>"
```

### 3. Project Close Archive

Use when the user asks to archive, summarize, learn from, or close a project. Also use after meaningful milestones, verified fixes, incident recall outcomes, or reusable lessons.

Steps:

1. Pull latest vault if a remote is configured.
2. Run `review-turn` if the archive need is not already explicit.
3. Run `distill` on the work summary to classify project-specific context, incidents, knowledge, runbooks, and skill candidates.
4. Create only the recommended archive drafts.
5. Validate the vault.
6. Show generated files and Git diff/status.
7. Commit and push only after user approval.

Commands:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py review-turn \
  --user-message "<latest user message>" \
  --assistant-summary "<work summary>" \
  --title "<archive title>"

python /home/l30002999/experience-vault/scripts/experience_vault.py distill \
  --title "<archive title>" \
  --source "<work summary, incident outcome, or source file path>"

python /home/l30002999/experience-vault/scripts/experience_vault.py new \
  --type project \
  --title "<project title>"

python /home/l30002999/experience-vault/scripts/experience_vault.py new \
  --type incident \
  --title "<incident title>"

python /home/l30002999/experience-vault/scripts/experience_vault.py new \
  --type knowledge \
  --title "<knowledge title>"
```

### 4. Promotion And Evolution Planning

Use when a repeated pattern should become a runbook, skill candidate, or evolved skill.

Promotion chain:

```text
projects -> incidents -> knowledge -> runbooks -> skill-candidates -> official skills -> evolved skills
```

Rules:

- Promote to `knowledge/` when a lesson is reusable.
- Promote to `runbooks/` when the procedure is repeatable and has clear boundaries.
- Promote to `skill-candidates/` only after triggers, inputs, outputs, safety rules, and validation are clear.
- Keep project-specific details in `projects/`; do not promote one-off project facts into generic knowledge or skills.
- Use EvoSkill only for candidate generation from mature runbooks and representative examples.
- Use GEPA/DSPy only for optimizing stable official `SKILL.md` files with eval datasets.
- Never install or replace active Codex skills without explicit user approval.

## Applicability Assessment

For each retrieved record, answer:

1. Does the current task match the record's applicability?
2. Are the trigger signals present?
3. Are required inputs available?
4. Are non-applicable cases present?
5. Is the environment compatible?
6. Is the record current enough?
7. Is the confidence level sufficient?

Report:

```text
Directly applicable:
- ...

Partially applicable:
- ...

Not applicable:
- ...
```

## Safety

Do not write these into the vault:

- Passwords
- API keys
- Tokens
- Private keys
- Raw auth files
- Full sensitive logs

Use placeholders:

```text
<PASSWORD>
<API_KEY>
<TOKEN>
<PRIVATE_KEY>
<REMOTE_HOST>
```

Before committing:

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py validate
python /home/l30002999/experience-vault/scripts/experience_vault.py git-status
```

## Shared Server Policy

On shared servers, the local checkout is not durable. If the vault is missing, clone it from GitHub or ask the user for the remote URL. If GitHub sync fails, leave files locally and report the retry path.

## Future Integrations

- EvoSkill: synthesize candidate Codex skills from mature runbooks and representative incidents.
- GEPA/DSPy: optimize stable official skills using `evals/<skill-name>/`.
- Mem0/Supermemory: add semantic retrieval only after Markdown search becomes insufficient.
