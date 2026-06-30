---
type: project
date: 2026-06-27
title: "quad-node-verl-mini-video-transport-regressed"
domain: verl
topics: ["verl", "ascend", "npu", "multinode", "mini-video-transport", "kitti", "qwen3-vl"]
status: verified
sensitive: none
related_incidents: []
extracted_knowledge: []
---

# quad-node-verl-mini-video-transport-regressed

## Goal

Complete a 4-node VERL + Ascend/NPU baseline vs mini-video transport optimization workflow through the full subagent-union pipeline (environment → baseline → optimized → comparison → report), keeping environment/dataset/model consistent with the prior dual-node run.

## Scope

- 4 machines, 8 NPUs each (32 total)
- Container: `qwen3vl2b_video_quad_l30002999much`
- Model: `/mnt/disk/l00937466/model/Qwen3-VL-2B-Instruct`
- Dataset: `/mnt/disk2t/l30002999/dataset/kitti_2s4f_geo3k_style/train.parquet` / `test.parquet`
- Image root: `/mnt/disk2t/dataset/video-2D/kitti_tracking/`
- VERL root: `/mnt/disk2t/l30002999/verl_container_workspace/verl`
- Optimization toggle: `VERL_MINI_VIDEO_TRANSPORT=1`

## Environment

- Source image: `qwen3vl2b_video_baseline_l30002999much:latest`
- Target container name on all 4 machines: `qwen3vl2b_video_quad_l30002999much`
- Machines: local, `192.168.0.206`, `192.168.0.13`, `192.168.0.145`
- Ray cluster: 4 active nodes / 32 NPUs
- Fixed Ray helpers export `GLOO_SOCKET_IFNAME`, `HCCL_SOCKET_IFNAME`, `MASTER_ADDR`, `MASTER_PORT`, `VLLM_HOST_IP`

## Timeline Summary

1. Environment setup: distributed image and verified 4 containers.
2. Baseline attempt 1: failed `ppo_mini_batch_size=0` after normalization (fixed batch sizes to 32).
3. Baseline attempt 2: failed Gloo `connectFullMesh` loopback (fixed Ray helper env exports).
4. Baseline attempt 3: failed `FileNotFoundError` for KITTI images on machines 3/4 (rsynced image root).
5. First extra baseline retry: failed missing `kitti_tracking_2s4f` reward function (propagated reward registry/module).
6. Second extra baseline retry: **success**.
7. Optimized preparation: applied mini-video transport patch to `rl_dataset.py` and `vision_utils.py` on all 4 nodes.
8. Optimized run: **success**.
9. Comparison: **regressed** due to quality guardrail deviation.
10. Report and archive generated.

## Key Commands

- Baseline script: `/mnt/disk2t/l30002999/verl_four_node_runs/scripts/qwen3vl2b_kitti_2s4f_quad_node_baseline.sh`
- Optimized script: `/mnt/disk2t/l30002999/verl_four_node_runs/scripts/qwen3vl2b_kitti_2s4f_quad_node_optimized.sh`
- Ray head helper: `/mnt/disk2t/l30002999/verl_four_node_runs/tmp/baseline_runner/start_head.sh`
- Ray worker helper: `/mnt/disk2t/l30002999/verl_four_node_runs/tmp/baseline_runner/start_worker.sh`

## Key Files

- Final report: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/20260626-quad-node-baseline-env/report/final-report.md`
- Archive manifest: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/20260626-quad-node-baseline-env/report/archive-manifest.yaml`
- Baseline checkpoint: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/20260626-quad-node-baseline-env/baseline/checkpoint.md`
- Optimized checkpoint: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/20260626-quad-node-baseline-env/optimized/checkpoint.md`
- Comparison checkpoint: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/20260626-quad-node-baseline-env/comparison/checkpoint.md`
- Metric delta: `/mnt/disk2t/l30002999/verl_four_node_runs/runs/20260626-quad-node-baseline-env/comparison/metric-delta.yaml`

## Problems Encountered

- **batch normalization**: With 32 ranks, dual-node `batch=16` normalized `ppo_mini_batch_size` to 0. Fix: `train_batch_size=32`, `ppo_mini_batch_size=32`.
- **Gloo loopback**: Ray node processes lacked `GLOO_SOCKET_IFNAME`/`HCCL_SOCKET_IFNAME`/`MASTER_ADDR`/`MASTER_PORT`/`VLLM_HOST_IP`. Fix: export in Ray helper scripts before head/worker start.
- **dataset distribution**: `/mnt/disk2t` is node-local; KITTI image root missing on machines 3/4. Fix: rsync full image root and verify inside containers.
- **reward function propagation**: Remote workers lacked `kitti_tracking_2s4f` reward registration and `kitti_tracking.py`. Fix: copy `__init__.py` and module to machines 2-4.

## Final Solution

Workflow completed successfully with a **regressed** comparison verdict. The mini-video transport optimization produced sub-1% performance gains but increased validation accuracy deviation from baseline by 0.02099, so it was not adopted.

## Verification

- Baseline exit code: 0, reached step 20/20
- Optimized exit code: 0, reached step 20/20
- Baseline metrics:
  - throughput: 63.5119 tokens/s
  - step20 time: 34.1353 s/step
  - mean time: 34.7322 s/step
  - val acc: -0.9225
- Optimized metrics:
  - throughput: 63.7305 tokens/s
  - step20 time: 33.9942 s/step
  - mean time: 34.4633 s/step
  - val acc: -0.9435
- Comparison verdict: regressed

## Residual Risks

- Seed not explicitly set; reproducibility has randomness risk.
- `/mnt/disk2t` is node-local; future multi-node runs must explicitly verify data and source-patch consistency.
- Final verdict is regressed; optimization should not be adopted without further analysis.

## Related Incidents

- Dual-node counterpart: `20260625-dual-node-baseline-env` (also regressed).

## Extracted Knowledge

- None promoted; findings kept project-specific.

## Sensitive Data Handling

- No passwords, keys, or raw auth files stored in vault.
- SSH password used only ephemerally in subagent prompts; not persisted.

## Distill Guidance

- Distill classification: project-specific -> projects/
- Suggested domains: git-github, docker, npu-ascend, verl
