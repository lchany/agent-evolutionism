# Auto Archive Timing

This vault does not run a background daemon. Codex uses explicit helper commands plus user-level `AGENTS.md` rules to make recall and archive timing semi-automatic during normal work.

The design is inspired by Hermes-style turn review:

1. Track failure and turn signals while work is in progress.
2. Stop repeated blind retries.
3. Recall prior incidents when the failure fingerprint crosses a threshold.
4. Recommend archive review when a milestone, reusable lesson, or resolved incident appears.
5. Create reusable archive drafts only after the root cause and fix were actually tested.

## Lifecycle Events

Prefer the unified event command during normal agent work. It mirrors the NanoHermes idea of routing loop events into background review tasks, but keeps execution explicit and reviewable.

Project start:

```bash
python scripts/experience_vault.py event project-start \
  --objective "<current objective>" \
  --query "<task keywords>"
```

Command failure:

```bash
python scripts/experience_vault.py event command-failed \
  --objective "<current objective>" \
  --failed-command "<failed command>" \
  --exit-code "<exit code>" \
  --error-text "<key error lines>"
```

Meaningful milestone:

```bash
python scripts/experience_vault.py event milestone \
  --title "<archive title>" \
  --summary "<what changed, what was learned, verification status>"
```

Project close:

```bash
python scripts/experience_vault.py event project-close \
  --title "<archive title>" \
  --summary "<final result, reusable lessons, incidents, verification>" \
  --verified \
  --create-drafts
```

Use the lower-level commands below when you need to inspect or override one step of the event workflow.

## In-Progress Recall

Use `fingerprint` when a failure has enough context to describe:

```bash
python scripts/experience_vault.py fingerprint \
  --objective "<current objective>" \
  --command "<failed command>" \
  --exit-code "<exit code>" \
  --error-text "<key error lines>"
```

Use `fail-track` after related failures. The default threshold is `2`, which means the second similar failure recommends incident recall:

```bash
python scripts/experience_vault.py fail-track \
  --objective "<current objective>" \
  --command "<failed command>" \
  --error-text "<key error lines>"
```

When the threshold is reached, stop exploratory retries and run the suggested `recall --mode incident` command.

## Archive Review

Use `review-turn` after meaningful turns, especially after failures, fixes, verification, or user corrections:

```bash
python scripts/experience_vault.py review-turn \
  --user-message "<latest user message>" \
  --assistant-summary "<what changed or was learned>" \
  --title "<archive title>"
```

`review-turn` recommends archive drafts when it sees any of these signals:

- Turn interval reached, default `5` turns.
- A failure or error was observed.
- Incident recall was used.
- Completion or verification words appear.
- Reusable-knowledge words appear.
- Domain hints are detected, such as GitHub, SSH, Docker, NPU/Ascend, MindSpeed, VERL, profiling, or Python.

## Archive Decision

Use `review-turn` to decide whether archiving is worth considering. Use `distill` to decide where the knowledge belongs:

```bash
python scripts/experience_vault.py distill \
  --title "<archive title>" \
  --source "<project summary, incident outcome, or reusable lesson>"
```

Create an `incident` when the work diagnosed or resolved a reusable failure and the fix was tested.

Create `knowledge` when the lesson applies beyond one task and has verification evidence.

Create a `project` checkpoint when a milestone completed or a workflow changed materially.

Create a `runbook` when the lesson is already a repeatable procedure with validation.

Consider `skill-candidates/` only for class-level capabilities with triggers, inputs, outputs, safety boundaries, and verified examples. Do not promote one-off project details directly into skills.

If a failure has only been analyzed but not tested, keep it out of reusable archives. Continue testing, or record a project checkpoint that clearly marks the conclusion as unverified.

Do not archive raw secrets, private keys, tokens, passwords, auth files, or dense sensitive logs.
