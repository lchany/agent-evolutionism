---
type: project
date: 2026-06-17
title: "VERL remote command formatting pitfalls and safe execution rules"
domain: verl
topics: [ssh, docker, ray, command-formatting, npu-cleanup]
status: draft
敏感信息: none
related_incidents: []
extracted_knowledge:
  - knowledge/2026-06-17-safe-remote-command-formatting-for-ssh-docker-ray-verl-workflows.md
---

# VERL remote command formatting pitfalls and safe execution rules

## Goal

Record the project-specific context that led to the global command-formatting knowledge entry.

## Scope

This project note only indexes the VERL dual-node testing context. The reusable guidance has been promoted to:

`knowledge/2026-06-17-safe-remote-command-formatting-for-ssh-docker-ray-verl-workflows.md`

## Environment

- VERL dual-node NPU workflow.
- Remote hosts used during the incident: `.206` and `.59`.
- Training containers executed VERL/Ray/vLLM commands.
- User-owned workspace: `/mnt/disk2t/l30002999`.

## Timeline Summary

- While retesting VERL with corrected datasets, several remote command composition issues occurred.
- The recurring issues were generalized into a global knowledge entry instead of remaining project-only.

## Key Commands

- `ssh root@host ...`
- `docker exec <container> ...`
- `ray stop --force`
- `pkill -f ...`
- `npu-smi info`
- `scp local root@host:/exact/target/path`

## Key Files

- `knowledge/2026-06-17-safe-remote-command-formatting-for-ssh-docker-ray-verl-workflows.md`

## Problems Encountered

- `pkill -f` could match and terminate the current cleanup shell, producing exit `143`.
- Nested SSH/Docker/here-doc commands were fragile.
- Complex `sed`/`awk` expressions failed in remote composed commands.
- `scp` initially copied a script to the wrong directory level.
- Host Python lacked dependencies that existed inside the training container.
- `ray status` could hang after partial cluster shutdown.

## Final Solution

Promote the command-formatting lessons into a global knowledge record with safe patterns and verification steps.

## Verification

The knowledge record was written and will be validated through the vault validation command before commit/push.

## Residual Risks

- The rule should be promoted to a runbook or skill update if similar incidents recur.
- The vault currently has an unrelated local modification in `templates/AGENTS.md`; it must be reviewed before committing.

## Related Incidents

None linked yet.

## Extracted Knowledge

- `knowledge/2026-06-17-safe-remote-command-formatting-for-ssh-docker-ray-verl-workflows.md`

## Sensitive Data Handling

No passwords, tokens, private keys, or dense logs were included.
