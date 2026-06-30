---
type: project
date: 2026-06-29
title: "VERL NPU baseline HBM/Ray cleanup and subagent stall lessons"
domain: npu-ascend
topics: [verl, vllm-ascend, ray, hbm, subagent, mini-video]
status: draft
sensitive: false
related_incidents: [2026-06-29-verl-npu-baseline-hbm-ray-cleanup-and-subagent-stall-lessons]
extracted_knowledge: [2026-06-29-verl-npu-baseline-hbm-ray-cleanup-and-subagent-stall-lessons]
---

# VERL NPU baseline HBM/Ray cleanup and subagent stall lessons

## Goal

Archive verified failure causes and fixes from the four-node VERL NPU scaling baseline runs under `/mnt/disk2t/l30002999/verl_four_node_runs`.

## Scope

- 2node_8card baseline startup failure caused by stale Ray/VERL/vLLM residue consuming NPU HBM.
- baseline-runner subagent stall after training failure due to misuse of `apply_patch` for post-run artifact repair.
- Optimized mini-video data pipeline alignment to the latest PyAV/FFV1 bgr0 BytesIO scheme.

## Environment

- Ascend NPU cluster used for VERL multi-node RL training.
- vLLM-Ascend worker startup enforces a desired HBM utilization threshold.
- Ray/VERL/vLLM processes can leave transient NPU HBM reservations across runs if not fully cleaned up.

## Timeline Summary

1. Baseline run `2node_8card` failed at vLLM startup with an HBM availability error.
2. NPU occupation checks showed no persistent external job; residue was transient.
3. Exact Ray/VERL/vLLM cleanup on head and worker nodes freed the HBM.
4. Rerun with identical parameters reached step 20 successfully.
5. A separate baseline-runner subagent hung after a training failure while trying to repair root-level artifacts via `apply_patch`.

## Key Commands

- Ray/VERL/vLLM cleanup script executed on head and all workers before rerun.
- Rerun parameters: `gen_tp=4`, `gpu_memory_utilization=0.5`, `train_batch_size=64`.

## Key Files

- Failure evidence: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/baseline/2node_8card/durable/training.log`
- Success evidence: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/baseline/2node_8card/metrics-summary.yaml`
- Success evidence: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/baseline/2node_8card/exit_status.yaml`

## Problems Encountered

1. **vLLM-Ascend NPU HBM startup check failure**
   - Error signature: `Free memory on device (24.17/61.27 GiB) on startup is less than desired gpu_memory_utilization (0.5, 30.63 GiB)`.
   - Root cause: stale Ray/VERL/vLLM residue consumed NPU HBM at startup.

2. **baseline-runner subagent stall after failure**
   - The subagent attempted `apply_patch` to repair root-level artifacts after training had already failed.
   - Durable per-topology artifacts had already recorded the failure, so the patch attempt was unnecessary and hung until manual cancel.

## Final Solution

- Execute exact Ray/VERL/vLLM cleanup on head and all worker nodes before starting a new run.
- Runner scripts must write durable status and metric artifacts atomically themselves; subagents must return immediately after those artifacts are written and must not use `apply_patch` for post-run multi-file artifact repair.
- Align optimized mini-video code to: PyAV FFV1 AVI bgr0 via BytesIO, no load/decode worker env vars, no deepcopy/url/path fallback in `rl_dataset.py`, surface `bit_exact=True`.

## Verification

- 2node_8card rerun with `gen_tp=4`, `gpu_memory_utilization=0.5`, `train_batch_size=64` reached step 20 successfully.
- Success recorded in `metrics-summary.yaml` and `exit_status.yaml`.

## Residual Risks

- Transient Ray/VERL/vLLM residue can reappear if cleanup is skipped or incomplete on any node.
- Subagents that attempt post-run patching can stall the entire workflow even after durable failure records exist.

## Related Incidents

- `incidents/2026-06-29-verl-npu-baseline-hbm-ray-cleanup-and-subagent-stall-lessons.md`

## Extracted Knowledge

- `knowledge/2026-06-29-verl-npu-baseline-hbm-ray-cleanup-and-subagent-stall-lessons.md`

## Sensitive Data Handling

No passwords, keys, tokens, or raw dense logs stored. Evidence is referenced by file path only.
