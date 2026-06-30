# Experience Vault

Experience Vault is a GitHub-backed Markdown knowledge base for agent project work.

It preserves:

- Full project archives in `projects/`
- Mid-task troubleshooting records in `incidents/`
- Reusable lessons in `knowledge/`
- Mature procedures in `runbooks/`
- Candidate agent skills in `skill-candidates/`
- Evaluation datasets in `evals/`

## Operating Model

GitHub is the durable source of truth. A server checkout is only a disposable cache.

Standard flow:

1. Pull before recall or writing.
2. Search relevant prior experience.
   - Treat `projects/` records as source context only. Do not apply another project's implementation plan, environment choices, or optimization tactics to the current project by keyword match.
   - Reuse across projects requires a verified `knowledge/` or `runbooks/` record with matching applicability and non-applicable cases, or explicit user confirmation.
3. Work on the current task.
4. Archive meaningful results.
5. Validate generated records.
6. Review diff.
7. Commit and push after approval.

## Restore And Skills

For a new AI agent or new Linux server, start with:

```text
LLM_RESTORE_AND_SKILL_INSTALL.md
LLM_RESTORE_AND_SKILL_INSTALL.zh-CN.md
```

Bundled custom agent skills are stored in:

```text
agent-skills/
```

Current bundled skills:

```text
agent-skills/
├── ascend-docker-rules/
├── experience-vault/
└── project-memory/
```

Install them with:

```bash
python scripts/install_agent_skills.py --agent-home <agent-home> --force
```

The bundled skills use `SKILL.md` packages. Treat them as portable agent capability descriptions, then map them to the target client's expected skill/rules location.

Portable hard rules live in `templates/AGENTS.md` and, when trigger reliability matters, in dedicated skills such as `agent-skills/ascend-docker-rules/`. Do not rely on `knowledge/` records alone for rules that must affect future behavior after migration.

## Safety Rules

Do not store:

- Passwords
- API keys
- Private keys
- Tokens
- Raw auth files
- Full sensitive logs

Use placeholders such as `<PASSWORD>`, `<API_KEY>`, `<TOKEN>`, `<PRIVATE_KEY>`, and `<REMOTE_HOST>`.

## Core Commands

Health check:

```bash
python scripts/experience_vault.py doctor
```

Ensure this checkout is up to date before shared use:

```bash
python scripts/experience_vault.py ensure-latest
```

Lifecycle event entrypoints:

```bash
python scripts/experience_vault.py event project-start \
  --objective "implement lifecycle recall for the vault" \
  --query "Experience Vault NanoHermes lifecycle event scheduler"

python scripts/experience_vault.py event command-failed \
  --objective "push vault changes" \
  --failed-command "git push" \
  --exit-code 128 \
  --error-text "Permission denied (publickey)."

python scripts/experience_vault.py event milestone \
  --title "Vault lifecycle event workflow" \
  --summary "Implemented a reusable lifecycle event entrypoint and verified it."

python scripts/experience_vault.py event project-close \
  --title "Vault lifecycle event workflow" \
  --summary "Finished the workflow. The lesson is reusable across projects." \
  --verified \
  --create-drafts
```

The `event` command is the preferred Hermes/NanoHermes-style wrapper for normal agent work. It keeps the workflow explicit while reducing missed recall or archive-review steps.

Search raw matches:

```bash
python scripts/experience_vault.py search --query "mindspeed profiling slow rank" --mode incident
```

`search`, `recall`, `distill`, `new`, and `archive` pull the latest remote state by default. Use `--no-pull` only after reviewing local state.

Recall with applicability grouping:

```bash
python scripts/experience_vault.py recall --query "github ssh permission denied publickey push" --mode incident
```

Build an incident fingerprint and recall query from a failure:

```bash
python scripts/experience_vault.py fingerprint \
  --objective "push vault changes" \
  --command "git push" \
  --exit-code 128 \
  --error-text "Permission denied (publickey)."
```

Detect domain tags from a task, error, or summary:

```bash
python scripts/experience_vault.py domain-hints --text "VERL rollout reward drift NPU profiling"
```

Track repeated failures and trigger incident recall after the threshold:

```bash
python scripts/experience_vault.py fail-track \
  --objective "push vault changes" \
  --command "git push" \
  --error-text "Permission denied (publickey)."
```

Review whether the latest turn should be archived:

```bash
python scripts/experience_vault.py review-turn \
  --user-message "fix GitHub SSH push" \
  --assistant-summary "resolved and verified" \
  --incident-recall \
  --title "GitHub SSH push followup"
```

Classify a summary into archive destinations:

```bash
python scripts/experience_vault.py distill \
  --title "GitHub SSH push followup" \
  --source "Fixed GitHub SSH push failure. Root cause was missing SSH public key. Verified by successful git push. This is reusable for future GitHub push incidents." \
  --verified
```

Create recommended archive drafts from the distill result:

```bash
python scripts/experience_vault.py distill \
  --title "GitHub SSH push followup" \
  --file /tmp/work-summary.md \
  --verified \
  --create-drafts
```

Create a record from a template:

```bash
python scripts/experience_vault.py new --type knowledge --title "MindSpeed slow rank profiling"
```

Create archive drafts:

```bash
python scripts/experience_vault.py archive \
  --title "MindSpeed profiling debug" \
  --type project \
  --type incident \
  --type knowledge
```

Validate structure and secret hygiene:

```bash
python scripts/experience_vault.py validate
```

Show Git synchronization status:

```bash
python scripts/experience_vault.py git-status
```

Validate, review, commit, and push:

```bash
python scripts/experience_vault.py sync --message "Archive MindSpeed profiling debug"
```

## GitHub Setup

After creating a private GitHub repository, bind this checkout:

```bash
git remote add origin git@github.com:<owner>/experience-vault.git
git branch -M main
git push -u origin main
```

Only push after reviewing generated files and secret scan results.
