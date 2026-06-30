---
type: knowledge
date: 2026-06-29
title: "VERL NPU baseline HBM/Ray cleanup and subagent stall lessons"
domain: npu-ascend
topics: [verl, vllm-ascend, ray, subagent, hbm]
applies_to: [verl-multinode-training, vllm-ascend-startup, agent-orchestrated-training]
confidence: verified
risk: medium
source_projects: [2026-06-29-verl-npu-baseline-hbm-ray-cleanup-and-subagent-stall-lessons]
source_incidents: [2026-06-29-verl-npu-baseline-hbm-ray-cleanup-and-subagent-stall-lessons]
last_verified: 2026-06-29
sensitive: false
skill_candidate: false
---

# VERL NPU baseline HBM/Ray cleanup and subagent stall lessons

## Applicability

- Running VERL multi-node training with vLLM-Ascend on Ascend NPUs.
- Orchestrating long-running training subagents that must report durable status and metrics.

## Trigger Signals

1. vLLM-Ascend startup fails with `Free memory on device ... is less than desired gpu_memory_utilization` even though `npu-smi` shows no foreign job.
2. A training subagent appears stuck after the underlying run has already failed and durable artifacts exist.

## Required Inputs

- Access to head and all worker nodes for process cleanup.
- Durable per-topology artifact directory where the runner writes `exit_status.yaml` and `metrics-summary.yaml`.

## Procedure

### HBM cleanup before a VERL/vLLM-Ascend run

1. On the head node and every worker node, terminate residual Ray, VERL, and vLLM processes.
2. Clear Ray temporary state and any orphaned vLLM worker processes.
3. Verify freed HBM with `npu-smi info -t memory` or equivalent.
4. Start the new run with the intended parameters; do not lower `gpu_memory_utilization` as a workaround.

### Subagent post-failure behavior

1. The runner script must write `exit_status.yaml`, `metrics-summary.yaml`, and any other durable artifacts atomically before exiting.
2. The subagent must return immediately after durable artifacts are written.
3. Do not use `apply_patch` or similar multi-file repair tools in the subagent after a run failure. Artifact repair belongs in the runner script itself.

## Non-Applicable Cases

- If the HBM shortfall is caused by a legitimately running job, cleanup is wrong; reschedule instead.
- If the runner did not write durable artifacts, the subagent cannot safely return until fallback artifacts are created by the runner, not patched by the agent.

## Verification Method

- Confirm the rerun reaches the expected step count and writes success artifacts.
- Confirm subagent tasks exit promptly after failure artifacts are durable.

## Risk And Safety Notes

- Killing processes without checking ownership can disrupt other users on shared machines. Verify the residue belongs to the current session before cleanup.
- Stale HBM can reappear if cleanup is inconsistent across nodes; always clean head and every worker.

## Source Evidence

- Failure evidence: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/baseline/2node_8card/durable/training.log`
- Success evidence: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/baseline/2node_8card/metrics-summary.yaml`
- Success evidence: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/baseline/2node_8card/exit_status.yaml`

## Promotion Notes

Consider promoting to a runbook if this cleanup sequence is repeated across multiple projects.
