---
type: knowledge
date: 2026-06-16
title: "Use dedicated workspace for VERL lazy transport changes"
domain: verl
topics: [workspace-isolation, shared-directory-safety, lazy-image-transport]
applies_to: [verl, vllm, qwen3vl, path_refs, lazy-image-transport]
confidence: verified
risk: medium
source_projects: [add-verl-lazy-image-transport]
source_incidents: []
last_verified: 2026-06-16
sensitive: false
skill_candidate: false
---

# Use dedicated workspace for VERL lazy transport changes

## Applicability

Use this rule for the VERL/Qwen3VL lazy image transport work, especially when
editing scripts, launchers, dataset converters, or patched VERL/vLLM code.

## Trigger Signals

- The requested change involves `/mnt/sfs_turbo/f30040252/code/qwen3vl-lazy-mm`
  or another shared project directory.
- The work requires creating scripts, changing test launchers, converting
  datasets, or patching VERL/vLLM behavior.
- The user asks to test baseline vs optimized VERL runs, path_refs, LazyImageRef,
  worker-side validation, throughput, or reward precision.

## Required Inputs

- Dedicated writable workspace: `/mnt/disk2t/l30002999/`.
- Source path to copy from when a working copy is needed.
- Clear user approval before changing any shared or third-party path.

## Procedure

1. Treat shared directories as read-only unless the user explicitly approves a
   specific edit.
2. Do not create new scripts in shared directories.
3. Do not modify existing scripts that may belong to other users.
4. Create or update project-specific scripts only under `/mnt/disk2t/l30002999/`.
5. If code changes are required, first create a dedicated working copy under
   `/mnt/disk2t/l30002999/` and edit that copy.
6. Before running tests, make launch scripts point to the dedicated working copy
   and output paths under `/mnt/disk2t/l30002999/`.
7. If an accidental shared-directory edit happens, stop, restore only the files
   modified by the agent, and verify syntax/content before continuing.

## Non-Applicable Cases

- Purely read-only inspection of shared code or logs.
- User explicitly approves a named edit in a shared path for the current task.
- Copying logs or datasets out of shared storage without modifying source files.

## Verification Method

- Check target paths before any edit.
- Use `rg`, `stat`, `bash -n`, and `python -m py_compile` as appropriate.
- Confirm no newly created scripts or modified files are left in shared
  directories after accidental edits are restored.

## Risk And Safety Notes

- Shared paths such as `/mnt/sfs_turbo/f30040252/code/qwen3vl-lazy-mm` may be
  used by other users or running tests. Modifying them can invalidate results or
  break someone else's environment.
- Dataset copies and generated test artifacts can remain under
  `/mnt/disk2t/l30002999/`; source shared code should not be changed without
  explicit approval.

## Source Evidence

- During the VERL lazy image transport work on 2026-06-16, code was briefly
  edited in the shared qwen3vl-lazy-mm directory. The user clarified that all
  future changes must be made only under `/mnt/disk2t/l30002999/`.
- The edited shared files were restored and syntax-checked before continuing.

## Promotion Notes

Promote this into a project runbook if more VERL lazy-transport tasks continue
across multiple sessions.
