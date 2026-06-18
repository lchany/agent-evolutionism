# Distillation Guide

Experience Vault uses a two-step learning loop:

1. `review-turn` decides whether the latest work should be reviewed for archival.
2. `distill` decides where each reusable part belongs.

## Destinations

`projects/` stores project-specific context: goal, scope, environment, timeline, final result, verification, and residual risks.

`incidents/` stores reusable failures: trigger signal, error signature, root cause, resolution, verification, reuse notes, and non-applicable cases.

`knowledge/` stores portable lessons: applicability, trigger signals, required inputs, procedure, boundaries, verification method, and source evidence.

`runbooks/` stores repeatable procedures: when to use, required inputs, ordered steps, validation, and failure handling.

`skill-candidates/` stores class-level capabilities only after patterns have matured. Prefer updating an existing umbrella skill before creating a new one.

## Classification Rules

Keep project-specific details in `projects/`.

Classify user-provided facts by scope before archiving:

- Project-specific facts: paths, repositories, datasets, containers, machines, local environment, current task state, and one-off preferences. Store these in `PROJECT_MEMORY.md` or `projects/`.
- General reusable facts: cross-project principles, repeated procedures, best practices, and verified lessons. Store these in `knowledge/` or `runbooks/` only after verification.
- Mixed facts: split the project-local detail from the reusable principle before creating records.
- Unknown scope: keep the fact in the active task context until clarified.

Extract to `knowledge/` only when the lesson transfers across projects.

Extract to `incidents/` only when future searches can match the failure signature and the root cause plus fix were tested.

Promote to `runbooks/` only when the procedure can be repeated and verified.

Promote to `skill-candidates/` only when there are clear triggers, inputs, outputs, safety boundaries, and verified examples.

Discard raw logs, unverified guesses, temporary paths, and sensitive material.

Do not turn a fresh root-cause hypothesis into reusable knowledge immediately after a failure. First confirm the fix with an actual test, smoke test, rerun, or other concrete validation evidence. Without that evidence, keep the note as a project checkpoint or a pending hypothesis, not as `incidents/`, `knowledge/`, `runbooks/`, or `skill-candidates/`.

## Command

```bash
python scripts/experience_vault.py distill \
  --title "<archive title>" \
  --source "<summary text or source file path>" \
  --verified
```

Use `--verified` only when the summary includes tested confirmation. Add `--create-drafts` only after reviewing the classification result.
