---
type: incident
date: 2026-06-29
title: "VERL NPU baseline HBM/Ray cleanup and subagent stall lessons"
domain: npu-ascend
topics: [verl, vllm-ascend, ray, hbm]
status: draft
confidence: verified
sensitive: false
source_projects: [2026-06-29-verl-npu-baseline-hbm-ray-cleanup-and-subagent-stall-lessons]
related_knowledge: [2026-06-29-verl-npu-baseline-hbm-ray-cleanup-and-subagent-stall-lessons]
---

# VERL NPU baseline HBM/Ray cleanup and subagent stall lessons

## Trigger Signal

vLLM-Ascend worker fails during VERL baseline startup with an NPU HBM availability error.

## Context

Multi-node VERL training on Ascend NPUs. A previous run or process left transient Ray/VERL/vLLM residue that reserved HBM without showing up as a current job in `npu-smi`.

## Failed Command Or Operation

vLLM-Ascend worker initialization during the `2node_8card` baseline run.

## Error Signature

```text
Free memory on device (24.17/61.27 GiB) on startup is less than desired gpu_memory_utilization (0.5, 30.63 GiB)
```

## Failed Attempts

- Re-running without cleanup reproduced the HBM shortfall.
- Checking current NPU occupation showed no external job, which initially made the cause unclear.

## Root Cause

Stale Ray/VERL/vLLM processes from earlier runs held NPU HBM reservations. The processes were transient enough that they did not appear as a persistent external job, but their HBM consumption exceeded the headroom required by vLLM-Ascend's `gpu_memory_utilization=0.5` setting.

## Resolution

1. Stop and clean up Ray/VERL/vLLM state on the head node and every worker node.
2. Verify no residual Ray or vLLM processes remain.
3. Restart the baseline run with unchanged parameters.

## Verification

- Rerun with `gen_tp=4`, `gpu_memory_utilization=0.5`, `train_batch_size=64` reached step 20 successfully.
- Success evidence: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/baseline/2node_8card/metrics-summary.yaml`
- Success evidence: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/baseline/2node_8card/exit_status.yaml`

## Reuse Notes

Apply this incident when VERL/vLLM-Ascend startup fails with an HBM utilization error and current NPU occupation appears clean. The fix is environmental cleanup, not a parameter change.

## Non-Applicable Cases

- If a different job legitimately occupies HBM, do not kill it; wait or reschedule.
- If the error persists after thorough cleanup, inspect for driver/runtime leaks or memory fragmentation rather than repeating cleanup.

## Sensitive Data Handling

No passwords, keys, tokens, or raw dense logs stored. Evidence is referenced by file path only.
