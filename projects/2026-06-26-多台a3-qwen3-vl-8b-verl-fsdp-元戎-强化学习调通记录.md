---
type: project
date: 2026-06-26
title: "多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录"
domain: verl-distributed-training
topics: [a3, qwen3-vl, verl, fsdp, ray, yuanrong, vllm-ascend, torch-npu]
status: verified
sensitive: reviewed
related_incidents: []
extracted_knowledge: []
---

# 多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录

## Goal

Archive a verified two-node A3/560T runbook and failure log for running Qwen3-VL-8B-Instruct reinforcement learning with verl, FSDP, Ray, vLLM-Ascend, and an optional Yuanrong TransferQueue backend.

## Scope

This record is a strictly verified, directly reusable multi-machine setup and test experience for A3 + Qwen3-VL-8B + verl + FSDP + Ray/NPU workflows.

Important boundary: the **Yuanrong startup section is an optional Yuanrong-specific layer**. If the entire "拉起元戎" section is removed, the remaining procedure is the ordinary non-Yuanrong multi-machine setup/test flow.

## Environment

- Hardware: two A3 nodes, 16 NPUs per node, 32 NPUs total.
- Software baseline: `quay.io/ascend/vllm-ascend:v0.18.0-a3`, MindSpeed `core_r0.15.3`, Megatron-LM `core_v0.15.3`, verl `main`.
- Model/data: Qwen3-VL-8B-Instruct and geometry3k.
- Yuanrong-specific configuration, when used: `openyuanrong-datasystem`, `dscli`, ETCD-backed worker startup, `shared_memory_size_mb=131072`.
- Container requirement: container `/dev/shm` must be larger than Yuanrong `shared_memory_size_mb`; the verified command used `--ipc=host` and `--shm-size 1024g`.
- Cross-node invariant: Python package set, model path, dataset path, and preprocessed parquet paths must be identical on all nodes.

## Timeline Summary

1. Created identical containers on both nodes from the vLLM-Ascend A3 image.
2. Installed MindSpeed, Megatron-LM, mbridge, verl, ETCD, Yuanrong, and missing runtime dependencies such as `mathruler`.
3. Downloaded Qwen3-VL-8B-Instruct and geometry3k, then preprocessed geometry3k to parquet.
4. Cleaned stale `datasystem`, `yuanrong`, Ray, and `/dev/shm/*` before each service bring-up attempt.
5. Brought up Yuanrong first through Metastore, observed cross-node RPC/KV failure, then switched to ETCD-backed startup successfully.
6. Started Ray with critical networking and NPU environment exported before `ray start` so Ray workers inherited them.
7. Enabled verl `transfer_queue` with `storage_backend: Yuanrong`, `auto_init: False`, and used `verl.trainer.main_ppo_sync`.
8. Iterated through Ray attachment, Gloo interface, ACL visible device, VLM token/feature mismatch, `mm_hash`, OOM, and disk-cache failures until the training path was usable.

## Key Commands

### Container

Use the A3 vLLM-Ascend image and expose Ascend devices, driver libraries, host network, host IPC, and a large shm area. For future container creation in this user's environment, also include the active global mounts `/mnt/disk2t` and `/mnt/sfs_turbo` unless explicitly overridden.

### Ray start invariants

Before `ray start` on every node:

```bash
export GLOO_SOCKET_IFNAME="<comm-iface>"
export HCCL_IF_IP="<local-ip>"
export ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
export HCCL_CONNECT_TIMEOUT=1500
export HCCL_HOST_SOCKET_PORT_RANGE=60000-60050
export HCCL_NPU_SOCKET_PORT_RANGE=61000-61050
```

Head node starts Ray with `--head --port=8888 --temp-dir=<large-data-disk>/ray_tmp`; worker nodes join `--address=<head-ip>:8888`.

### verl launch invariants

Before launching verl:

```bash
export RAY_ADDRESS=<head-ip>:8888
export HF_HOME=<large-data-disk>/hf_home
export HF_DATASETS_CACHE=$HF_HOME/datasets
export TRANSFORMERS_CACHE=$HF_HOME/models
export TORCH_HOME=<large-data-disk>/torch_home
```

Core verified flags:

```bash
python3 -m verl.trainer.main_ppo_sync \
  actor_rollout_ref.rollout.tensor_model_parallel_size=4 \
  actor_rollout_ref.actor.fsdp_config.fsdp_size=8 \
  +actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0 \
  actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=4096 \
  actor_rollout_ref.rollout.free_cache_engine=True \
  actor_rollout_ref.rollout.enforce_eager=True \
  trainer.n_gpus_per_node=16 \
  trainer.nnodes=2 \
  trainer.device=npu
```

## Key Files

- `/vllm-workspace/verl/verl/trainer/config/ppo_trainer.yaml` — enable TransferQueue, set backend to `Yuanrong`, and set Yuanrong `auto_init: False`.
- Ray worker startup script — exports Gloo/HCCL/NPU visibility before `ray start`.
- verl launch script — uses `main_ppo_sync`, sets `RAY_ADDRESS`, model/data/cache paths, FSDP/TP sizing, VLM rollout flags, and OOM mitigation flags.

## Problems Encountered

- Ray cluster showed all cards, but the verl Python process did not see the full cluster until `RAY_ADDRESS=<head-ip>:8888` was exported before launching verl.
- Gloo selected the wrong network interface when `GLOO_SOCKET_IFNAME` was not exported before Ray workers were started.
- `ACL stream synchronize failed, error code:507035` was caused by invalid `ASCEND_RT_VISIBLE_DEVICES=[]`; set `ASCEND_RT_VISIBLE_DEVICES=0,1,...,15` before `ray start` on every node.
- Multi-machine VLM image features/tokens mismatch was caused by TP=4 + FSDP1 full-mesh sharding splitting image tokens across shards; setting `actor_rollout_ref.actor.fsdp_config.fsdp_size=8` keeps image tokens inside one shard.
- Yuanrong Metastore path failed in this experiment with remote worker `RPC unavailable`; ETCD-backed Yuanrong startup was verified successful.
- `/tmp/ray` local disk exhaustion was resolved by moving Ray temp state to a large data disk with `ray start --temp-dir=<large-data-disk>/ray_tmp`.
- `ModuleNotFoundError: No module named 'mathruler'` was resolved by installing `mathruler` consistently on every node.
- HuggingFace datasets cache disk exhaustion was resolved by clearing stale cache and redirecting `HF_HOME`, `HF_DATASETS_CACHE`, `TRANSFORMERS_CACHE`, and `TORCH_HOME` to a large data disk.
- vLLM multimodal `mm_hash` cache assertion was resolved by setting `+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0`.
- Rollout/checkpoint OOM was resolved by setting `actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=4096`, `free_cache_engine=True`, and `enforce_eager=True`.

## Final Solution

Use the flow as two layers:

1. Base reusable multi-machine flow: container/env consistency, model/data path consistency, Ray cluster startup, `RAY_ADDRESS`, `GLOO_SOCKET_IFNAME`, `ASCEND_RT_VISIBLE_DEVICES`, verl config, FSDP sizing, VLM rollout/OOM fixes.
2. Optional Yuanrong layer: start Yuanrong workers with ETCD and configure verl `transfer_queue` backend as `Yuanrong` with `auto_init: False`.

## Verification

The user explicitly confirmed this is a directly usable conclusion from a debugged two-node A3 run, not a tentative note. The flow, parameters, and root causes in this record should be reused directly for the stated topology. The archival step itself did not start a new training job; that does not downgrade the recorded conclusion.

## Residual Risks

- Yuanrong Metastore mode was not the verified successful path in this record; ETCD mode was the verified path.
- The non-Yuanrong flow should omit the Yuanrong worker startup section and Yuanrong transfer queue backend changes.
- `fsdp_size=8` is a verified conclusion for this topology/TP/FSDP combination; other node counts, TP sizes, FSDP variants, or Qwen-VL model sizes need fresh validation.
- Image, verl, vLLM-Ascend, torch_npu, Yuanrong, and Ray version changes can alter behavior; keep package lists consistent across nodes and record exact versions for future reruns.

## Related Incidents

- `RAY_ADDRESS` missing causes verl to see only local GPUs even when `ray status` shows full cluster.
- Ray workers inherit networking/NPU runtime environment only from the environment present at `ray start` time.
- TP + FSDP mesh can split VLM image tokens and cause image feature/token mismatch.
- Yuanrong Metastore cross-node RPC/KV can fail; ETCD-backed Yuanrong is the verified path here.

## Extracted Knowledge

- Separate the base multi-machine verl/Ray/NPU flow from the optional Yuanrong layer.
- Export worker-affecting env vars before starting Ray, not only before launching the Python training script.
- For this Qwen3-VL-8B 2-node A3 run, keep model/data/cache paths consistent and on large disks across all nodes.
- Treat disk cache placement as part of the training configuration, not an afterthought.

## Sensitive Data Handling

Author identity, exact user directory names, and node IPs are not expanded here. Use placeholders such as `<head-ip>`, `<worker-ip>`, `<comm-iface>`, and `<large-data-disk>` in reusable instructions.

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: reusable-incident -> incidents/
- Distill classification: general-knowledge -> knowledge/
- Suggested domains: docker, npu-ascend, mindspeed, verl, python
