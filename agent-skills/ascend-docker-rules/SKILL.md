---
name: ascend-docker-rules
description: Enforce the user's Ascend/NPU Docker container rules. Use when creating, running, or reviewing Docker containers for Ascend, NPU, VERL, vLLM-Ascend, CANN, torch_npu, profiling, training, inference, or shared training server workflows; also use when writing docker run commands, compose files, container launch scripts, or container setup docs for those workflows.
---

# Ascend Docker Rules

Use this skill whenever the task involves Docker containers for the user's Ascend/NPU training, inference, profiling, VERL, vLLM-Ascend, CANN, or torch_npu workflows on shared servers.

## Mandatory Shared Mounts

Unless the user explicitly overrides this rule, every matching container must include both mounts:

```bash
-v /mnt/disk2t:/mnt/disk2t \
-v /mnt/sfs_turbo:/mnt/sfs_turbo
```

Do not treat this as an optional best practice. It is an active user rule.

## Preferred Ascend Runtime Baseline

For Ascend/NPU containers, prefer the known working baseline when applicable:

```bash
--runtime ascend --privileged --network host --ipc host --cgroupns host --security-opt label=disable
```

Adjust only when the target environment or user request requires a different runtime pattern.

## Verification

After creating or starting the container, verify both mounts are visible:

```bash
docker exec <container> test -d /mnt/disk2t
docker exec <container> test -d /mnt/sfs_turbo
```

For NPU workflows, also verify device/runtime visibility with the environment-appropriate check, such as `npu-smi info`.

## Safety

- `/mnt/sfs_turbo` is shared storage; do not delete or overwrite shared files without explicit user confirmation.
- Check capacity before writing large datasets, checkpoints, or logs to shared storage.
- Do not store credentials, tokens, private keys, or raw sensitive logs in the vault or container setup docs.
