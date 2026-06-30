---
type: incident
date: 2026-06-26
title: "多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录"
domain: verl-distributed-training
topics: [a3, qwen3-vl, verl, fsdp, ray, gloo, yuanrong, vllm-ascend, torch-npu]
status: verified
confidence: high
sensitive: reviewed
source_projects: []
related_knowledge: []
---

# 多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录

## Trigger Signal

- Two-node A3 Qwen3-VL-8B verl RL training fails during Ray resource detection, Gloo/HCCL connectivity, torch_npu runtime initialization, VLM multimodal packing, Yuanrong TransferQueue, or vLLM multimodal rollout.

## Context

Strictly verified multi-machine A3 Qwen3-VL-8B verl/FSDP/Ray/NPU setup with optional Yuanrong transfer queue layer.

Boundary: Yuanrong is not required for the base multi-machine setup/test procedure. Removing the whole Yuanrong startup section yields the ordinary non-Yuanrong flow.

## Failed Command Or Operation

- Starting verl multi-node training with `python3 -m verl.trainer.main_ppo_sync` on a Ray cluster.
- Starting Yuanrong workers with Metastore mode across two nodes.
- Running vLLM multimodal rollout inside verl with Qwen3-VL-8B.

## Error Signature

- Ray has full cluster resources, but verl does not recognize all 32 NPUs.
- Gloo uses an invalid/default interface such as `lo`.
- `RuntimeError: ACL stream synchronize failed, error code:507035`.
- Multi-machine-only VLM image feature/token mismatch.
- Yuanrong Metastore remote worker fails with `RPC unavailable`.
- `mm_hash` errors or rollout OOM in VLM rollout.
- Ray local temp directory warning: `/tmp/ray/... is over 95% full`.
- `ModuleNotFoundError: No module named 'mathruler'` for `verl/utils/reward_score/geo3k.py`.
- HuggingFace datasets `OSError: Not enough disk space` during parquet loading/tokenization.

## Failed Attempts

- Setting `GLOO_SOCKET_IFNAME` only in the training script after Ray had already started did not affect Ray worker processes.
- Cherry-picking an external patch for Qwen3-VL image token mismatch could run but produced invalid training behavior in this run, so it was discarded.
- Yuanrong Metastore startup reached cross-node `RPC unavailable`; switching to ETCD was the verified path.

## Root Cause

- Ray worker processes only inherit environment prepared before `ray start`; late exports in the verl launch script are insufficient for Gloo/NPU runtime behavior.
- Without explicit `RAY_ADDRESS`, the verl Python process may not attach to the intended Ray head.
- TP=4 + FSDP1 full mesh can split image tokens across shards; TP then cuts hidden states inside shards, and padding/packing can make image features and tokens misalign.
- In this verified run, Yuanrong Metastore mode failed for remote worker KV access; ETCD mode was the working cluster metadata path.
- Ray and HuggingFace/datasets default cache/temp paths can silently land on small system disks; large model/data preprocessing then fails even though the main dataset/model paths are on a data disk.
- vLLM multimodal processor cache can require a cached item keyed by `mm_hash`; disabling the multimodal processor cache avoided the assertion in this workload.
- `ACL stream synchronize failed, error code:507035` was a secondary symptom; plog showed the primary cause was invalid `ASCEND_RT_VISIBLE_DEVICES=[]` causing NPU runtime initialization failure.

## Resolution

- Export before Ray startup on every node: `GLOO_SOCKET_IFNAME=<comm-iface>` and `ASCEND_RT_VISIBLE_DEVICES=0,1,...,15`.
- Export before verl launch: `RAY_ADDRESS=<head-ip>:8888`.
- For multi-machine VLM FSDP1, set `actor_rollout_ref.actor.fsdp_config.fsdp_size=8`.
- For Yuanrong mode, use ETCD-backed `dscli start -w ... --etcd_address <head-ip>:2379 --shared_memory_size_mb 131072`; treat Metastore as not verified for this scenario.
- For non-Yuanrong mode, remove the entire Yuanrong startup section and do not enable Yuanrong transfer queue backend.
- For `mm_hash`, set `+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0`.
- For rollout OOM, set `actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=4096`, `free_cache_engine=True`, and `enforce_eager=True`.
- Move Ray temp state to a large disk with `ray start --temp-dir=<large-data-disk>/ray_tmp`.
- Install `mathruler` on every node and keep `pip list` aligned across the cluster.
- Redirect `HF_HOME`, `HF_DATASETS_CACHE`, `TRANSFORMERS_CACHE`, and `TORCH_HOME` to a large data disk before launching verl.
- Prefer ETCD-backed Yuanrong for this scenario: start ETCD on head, then start each Yuanrong worker with its local `worker_address` and the head `etcd_address`.

## Verification

The user explicitly confirmed these are directly reusable conclusions from the debugged target two-node A3 environment. Treat the root causes and resolutions here as verified for the stated topology. No new training job was executed during archival, but the record itself is not tentative.

## Reuse Notes

Reuse this directly as a high-confidence incident bundle for multi-node A3 verl/FSDP/VLM/Ray/NPU setup. Split reuse into base multi-machine flow and optional Yuanrong layer.

Minimum preflight checklist before rerun:

1. Same image/package set/model path/dataset path on every node.
2. Container shm greater than Yuanrong `shared_memory_size_mb` when Yuanrong is enabled.
3. `GLOO_SOCKET_IFNAME`, `HCCL_IF_IP`, and `ASCEND_RT_VISIBLE_DEVICES` exported before `ray start`.
4. `RAY_ADDRESS=<head-ip>:8888` exported before verl launch.
5. `actor_rollout_ref.actor.fsdp_config.fsdp_size=8` retained for this topology.
6. Large-disk cache paths configured for Ray, HuggingFace datasets, Transformers, and Torch.

## Non-Applicable Cases

- Do not apply Yuanrong worker startup or `transfer_queue` backend changes when running ordinary non-Yuanrong multi-machine tests.
- Do not assume `fsdp_size=8` generalizes to other GPU/NPU counts, TP sizes, model families, or FSDP implementations without validation.

## Sensitive Data Handling

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: reusable-incident -> incidents/
- Distill classification: general-knowledge -> knowledge/
- Suggested domains: docker, npu-ascend, mindspeed, verl, python
