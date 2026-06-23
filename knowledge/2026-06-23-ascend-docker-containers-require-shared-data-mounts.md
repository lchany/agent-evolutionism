---
type: knowledge
date: 2026-06-23
title: "Ascend Docker containers require shared data mounts"
domain: ascend-npu-docker
topics: [ascend, npu, docker, verl, shared-storage]
applies_to:
  - "User's Ascend/NPU Docker workflows on shared training servers"
  - "verl/NPU opencode multi-agent environment setup"
confidence: verified
risk: medium
source_projects:
  - "/home/l30002999/source_code/sub-agent-union-work"
source_incidents: []
last_verified: 2026-06-23
sensitive: false
skill_candidate: false
---

# Ascend Docker containers require shared data mounts

## Applicability

Use this rule when creating Docker containers for the user's Ascend/NPU training, verl, vLLM-Ascend, or related opencode multi-agent workflows on the shared server environment.

## Trigger Signals

- Creating a Docker container for Ascend/NPU training or inference experiments.
- Creating a container for verl end-to-end, baseline, optimized, profiling, or debug runs.
- Using images with CANN, torch_npu, vLLM-Ascend, or verl.
- User asks to prepare a test container on the shared NPU machine.

## Required Inputs

- Container image name.
- Container name.
- Any extra user-requested mounts or runtime options.
- Confirmation before changing shared machine state when the action may affect other users.

## Procedure

Always include both shared mounts unless the user explicitly overrides the rule:

```bash
-v /mnt/disk2t:/mnt/disk2t \
-v /mnt/sfs_turbo:/mnt/sfs_turbo
```

For Ascend/NPU containers, also prefer matching the known working baseline pattern when applicable:

```bash
--runtime ascend --privileged --network host --ipc host --cgroupns host --security-opt label=disable
```

## Non-Applicable Cases

- Non-Docker workflows.
- Local-only throwaway containers where the user explicitly says not to mount shared storage.
- Environments where `/mnt/disk2t` or `/mnt/sfs_turbo` do not exist; in that case, re-check mount layout before container creation.

## Verification Method

After container creation/start, verify that the container can see both paths:

```bash
docker exec <container> test -d /mnt/disk2t
docker exec <container> test -d /mnt/sfs_turbo
```

For NPU workflows, also verify NPU visibility with `npu-smi info` inside or via the host-compatible container runtime.

## Risk And Safety Notes

- `/mnt/sfs_turbo` is shared storage and may be space constrained; check capacity before large output or dataset writes.
- Avoid deleting or overwriting shared files without explicit user confirmation.
- Do not store credentials, tokens, private keys, or raw sensitive logs in the vault.

## Source Evidence

- User correction on 2026-06-23 during `sub-agent-union-work` setup: all future containers must mount `/mnt/disk2t` and `/mnt/sfs_turbo`.
- Host inspection during the same workflow found `/mnt/sfs_turbo` as NFS/SFS Turbo shared storage and `/mnt/disk2t` as the local large Docker/storage disk.
- Test container requested: `verl-subagent-test-leicheng` from image `verl-0.7.1_vllm-0.18.0_cann-8.5.1_baseline:migrated_from_59_20260612`.

## Promotion Notes

This is global user experience for Ascend/NPU container workflows. It may later become part of a reusable container-creation runbook or agent skill rule if repeated across projects.
