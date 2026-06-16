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

Extract to `knowledge/` only when the lesson transfers across projects.

Extract to `incidents/` when future searches can match the failure signature.

Promote to `runbooks/` only when the procedure can be repeated and verified.

Promote to `skill-candidates/` only when there are clear triggers, inputs, outputs, and safety boundaries.

Discard raw logs, unverified guesses, temporary paths, and sensitive material.

## Command

```bash
python scripts/experience_vault.py distill \
  --title "<archive title>" \
  --source "<summary text or source file path>"
```

Add `--create-drafts` only after reviewing the classification result.
