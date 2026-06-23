---
name: "project-memory"
description: "Preserve durable project-specific facts, hard user constraints, user corrections, invalidated assumptions, and current task state across context compaction or task resumption. Use when starting or resuming non-trivial project work, before/after context compaction, when the user provides project paths/configuration/preferences/rules, when the user says future/always/must/never, when the user corrects an assistant conclusion, or when shell/log exploration discovers a verified project fact."
---

# Project Memory

Use this skill to keep project-specific working memory outside the chat context. The goal is not to archive raw logs; it is to preserve the small set of facts and corrections needed to continue accurately after compaction.

## Memory Layers

Keep information in the right layer:

- Global rules: `AGENTS.md` or a skill. Store reusable behavior such as "read project memory after compaction."
- Project facts: `<project>/PROJECT_MEMORY.md`. Store paths, datasets, containers, experiment settings, user corrections, invalidated assumptions, and current state for one project.
- Long-term experience: `/home/l30002999/experience-vault`. Store cross-project incidents, runbooks, and reusable knowledge.

Do not promote project-local paths, private machine details, raw logs, or one-off experiment settings into global memory unless they become reusable knowledge.

## Read Workflow

At the start of non-trivial work, after compaction, or when resuming a task:

1. Locate the project root from the current working directory, repository root, or user-provided path.
2. Read `<project>/PROJECT_MEMORY.md` if it exists.
3. Treat `User Corrections` and `Invalidated Assumptions` as higher priority than previous assistant summaries.
4. Reconcile memory with the newest user message and current code/command evidence.
5. If memory is stale or contradicted, update it before relying on it.

Priority order:

```text
Newest user message
> PROJECT_MEMORY.md User Corrections
> PROJECT_MEMORY.md Confirmed Project Facts
> Current code and command evidence
> Experience Vault records
> Old context summaries
> model assumptions
```

## Write Workflow

Update `PROJECT_MEMORY.md` when any durable project-specific information appears:

- The user gives a path, dataset root, container name, machine constraint, preference, or experiment setting.
- The user corrects an assistant conclusion.
- Shell/log/code inspection verifies a fact needed later.
- A prior assumption is proven wrong.
- A phase ends and the current goal, verified state, or next step would otherwise be lost after compaction.

Write concise entries. Prefer evidence pointers over raw output. Do not store secrets, tokens, private keys, auth files, or dense sensitive logs.

## Durable Rule Promotion

When the user states a future-facing constraint, classify it before treating it as ordinary memory. Trigger phrases include "以后", "后续", "所有", "必须", "不要", "默认", "remember this", "from now on", "always", "must", and "never".

Promotion rules:

- Global hard rule: update the active user rules or create/update a dedicated skill so future tasks can trigger without keyword search.
- Project hard rule: update `<project>/PROJECT_MEMORY.md` immediately and include a short future rule.
- Evidence or rationale: optionally archive supporting context in Experience Vault, but do not rely on `knowledge/` alone for a rule that must always affect future behavior.
- Unknown scope: ask one narrow scope question or store it as project memory with `Status: needs-scope` instead of promoting it globally.

Use this pattern for project-local durable rules:

```md
## Confirmed Project Facts

- [YYYY-MM-DD] <rule title>
  Rule: <future-facing constraint>
  Scope: <project, machine, workflow, or global candidate>
  Source: user instruction
  Status: active
```

## Correction Rules

When the user corrects the assistant, record both the correct fact and the invalidated wrong conclusion.

Use this pattern:

```md
## User Corrections

- [YYYY-MM-DD] <short title>
  Previous wrong assumption: `<wrong value or conclusion>`
  Correct value: `<correct value or conclusion>`
  Future rule: <what future agents must not repeat>
  Source: user correction
  Status: active
```

Also add a matching entry under `Invalidated Assumptions` if the wrong conclusion is likely to reappear from older summaries, logs, scripts, or model assumptions.

## Project Memory File

If `PROJECT_MEMORY.md` does not exist, create it from `references/PROJECT_MEMORY.template.md`.

Keep the file compact:

- Record stable facts, not every observation.
- Put temporary notes under `Current Task State`.
- Move obsolete items to `Status: superseded` instead of deleting them when deletion would hide an important correction.
- Use exact paths, filenames, commands, and dates when they matter.

## Shell And Log Results

For shell-heavy workflows:

- Store only durable conclusions and evidence pointers.
- Prefer paths to saved outputs, command names, timestamps, and line references.
- Do not paste large command outputs into `PROJECT_MEMORY.md`.
- If a log was inspected once and has no future value, summarize the conclusion in one sentence or omit it.
