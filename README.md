# Experience Vault

Experience Vault is a GitHub-backed Markdown knowledge base for Codex project work.

It preserves:

- Full project archives in `projects/`
- Mid-task troubleshooting records in `incidents/`
- Reusable lessons in `knowledge/`
- Mature procedures in `runbooks/`
- Candidate Codex skills in `skill-candidates/`
- Evaluation datasets in `evals/`

## Operating Model

GitHub is the durable source of truth. A server checkout is only a disposable cache.

Standard flow:

1. Pull before recall or writing.
2. Search relevant prior experience.
3. Work on the current task.
4. Archive meaningful results.
5. Validate generated records.
6. Review diff.
7. Commit and push after approval.

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

Search raw matches:

```bash
python scripts/experience_vault.py search --query "mindspeed profiling slow rank" --mode incident
```

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
