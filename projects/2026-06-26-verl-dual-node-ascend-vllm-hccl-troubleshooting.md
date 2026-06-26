---
type: project
date: 2026-06-26
title: "VERL dual-node Ascend vLLM HCCL troubleshooting"
domain: npu-ascend
topics: [verl, ray, vllm-ascend, hccl, docker, multi-node]
status: verified
sensitive: redacted
related_incidents: [incidents/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md]
extracted_knowledge: [knowledge/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md, runbooks/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md]
---

# VERL dual-node Ascend vLLM HCCL troubleshooting

## Goal

Bring up a two-node VERL baseline on Ascend/NPU using Ray and vLLM rollout, diagnose repeated HCCL `EJ0003` failures, and reach the training loop.

## Scope

- Two nodes, 8 visible NPUs per node.
- Existing containers on both nodes.
- Baseline script and helper Ray start script under the user workspace.
- Private IPs are redacted as placeholders.

## Environment

- Containers: `qwen3vl2b_video_baseline_l30002999much` on head and worker.
- Ray cluster target: 2 active nodes, 64 CPU, 16 GPU scheduling resources, 16 NPU resources.
- Key scripts:
  - `/mnt/disk2t/l30002999/scripts/qwen3vl2b_kitti_2s4f_dual_node_baseline.sh`
  - `/mnt/disk2t/l30002999/scripts/start_ray_dual_node_manual.sh`
- Evidence log that reached training loop: `/mnt/disk2t/l30002999/logs/dual_node_baseline/run_20260626_114136.log`.

## Timeline Summary

1. Initial dual-node attempts failed in vLLM EngineCore with HCCL `EJ0003`.
2. Ray lifecycle issues and a complex launcher caused additional failures before training started.
3. Containers were restarted and Ray was started cleanly.
4. `VLLM_HOST_IP` runtime_env propagation was removed.
5. HCCL envs were moved from driver-only training script exports to `ray start` on every node.
6. ATB env sourcing and `VLLM_USE_V1=0` were added based on a known working user reference.
7. Missing remote custom reward file was synced.
8. Final run reached the training progress loop without the previous HCCL and reward-file failures.

## Key Commands

Representative commands, with private IPs redacted:

```bash
docker restart qwen3vl2b_video_baseline_l30002999much
ssh root@<worker-ip> 'docker restart qwen3vl2b_video_baseline_l30002999much'
bash /mnt/disk2t/l30002999/scripts/start_ray_dual_node_manual.sh
bash /mnt/disk2t/l30002999/scripts/qwen3vl2b_kitti_2s4f_dual_node_baseline.sh
```

## Key Files

- Baseline script: `/mnt/disk2t/l30002999/scripts/qwen3vl2b_kitti_2s4f_dual_node_baseline.sh`
- Manual Ray starter: `/mnt/disk2t/l30002999/scripts/start_ray_dual_node_manual.sh`
- Reward script synced across nodes: `/mnt/disk2t/l30002999/scripts/dummy_reward.py`
- Source archive summary: `/home/l30002999/markdown/2026-06-26-verl-dual-node-hccl-troubleshooting-summary.md`

## Problems Encountered

- Ray GCS/session residue after failed starts.
- `pkill -f` matching cleanup command lines.
- Cluster-wide `VLLM_HOST_IP` override from head node.
- HCCL env variables absent from Ray worker environment.
- vLLM V1 EngineCore HCCL EJ0003 on dual-node Ascend.
- Missing remote custom reward file.

## Final Solution

Use a clean container/Ray lifecycle, start Ray with per-node `VLLM_HOST_IP` and inherited HCCL envs, source CANN and ATB env in training, disable vLLM V1, and ensure all Ray actor-loaded files exist on both nodes.

## Verification

- `ray status` showed 2 active nodes and expected resources.
- Ray worker env was verified per node.
- Final run log reached `Training Progress: 0/20` without the previous HCCL EJ0003 and reward FileNotFound failures.

## Residual Risks

- The archive records reaching the training loop, not completion of all 20 steps or baseline/optimized comparison.
- Exact vLLM V1 compatibility may depend on vLLM/vLLM-Ascend/CANN versions.

## Related Incidents

- `incidents/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md`

## Extracted Knowledge

- `knowledge/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md`
- `runbooks/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md`

## Sensitive Data Handling

Private IPs are redacted or represented as placeholders. No secrets or dense logs are included.
