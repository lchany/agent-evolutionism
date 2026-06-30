---
type: knowledge
date: 2026-06-26
title: "多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录"
domain: verl-distributed-training
topics: [a3, qwen3-vl, verl, fsdp, ray, yuanrong, vllm-ascend, torch-npu]
applies_to: [multi-node-a3, qwen-vl-rl, verl-fsdp, ray-workers, yuanrong-transferqueue]
confidence: high
risk: medium
source_projects: []
source_incidents: []
last_verified: 2026-06-26
sensitive: reviewed
skill_candidate: false
---

# 多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录

## Applicability

Directly applicable to multi-machine A3/NPU Qwen-VL or VLM reinforcement learning setups using verl, Ray, FSDP, torch_npu, and optionally Yuanrong transfer queue/data system.

Core boundary: this is primarily a reusable **multi-machine setup/test flow**. Yuanrong is an optional layer. Removing the whole Yuanrong startup section turns the flow into the normal non-Yuanrong multi-machine setup/test procedure.

## Trigger Signals

- Multi-node A3/NPU verl training or RL setup.
- Ray sees the cluster but verl does not use all cards.
- Gloo, HCCL, or torch_npu networking/runtime issues appear only under Ray workers.
- VLM image token/features mismatch appears only in multi-machine FSDP/TP runs.
- Yuanrong transfer queue is being evaluated as an optional backend.
- Ray, datasets, or model caches fill system disks during multi-node training.
- vLLM multimodal rollout reports `mm_hash`, image token/feature mismatch, or rollout OOM.

## Required Inputs

- Node IPs and communication interface name.
- Per-node NPU device count and intended `ASCEND_RT_VISIBLE_DEVICES` range.
- Ray head address/port.
- Model and dataset paths consistent across nodes.
- Whether Yuanrong is enabled; if not, skip the Yuanrong startup and transfer_queue backend changes.
- Large data disk paths for Ray temp state and Python/HF/Torch caches.
- Exact TP/FSDP sizing and whether the model is VLM/multimodal.

## Procedure

1. Keep all nodes consistent: same image, Python packages, model path, dataset path, and preprocessing output path.
2. Start containers with enough shm for Yuanrong. In this verified run, shm needed to exceed `shared_memory_size_mb=131072`; the example used `--ipc=host` and `--shm-size 1024g`.
3. Start Ray only after exporting critical environment variables on every node: `GLOO_SOCKET_IFNAME=<comm-iface>`, `HCCL_IF_IP=<local-ip>`, and `ASCEND_RT_VISIBLE_DEVICES=0,1,...,15`.
4. Put Ray temp state on a large disk: `ray start ... --temp-dir=<large-data-disk>/ray_tmp`.
5. Redirect model/data caches before verl launch: `HF_HOME`, `HF_DATASETS_CACHE`, `TRANSFORMERS_CACHE`, and `TORCH_HOME`.
6. Ensure the verl launch process attaches to the intended Ray cluster: `export RAY_ADDRESS=<head-ip>:8888`.
7. For multi-machine VLM FSDP1 + TP, set `actor_rollout_ref.actor.fsdp_config.fsdp_size=8` to avoid splitting image tokens across shards.
8. If Yuanrong is enabled, start Yuanrong as an optional layer. Verified path: ETCD-backed `dscli start -w` on every node with each node's own `worker_address` and the head node `etcd_address`.
9. If Yuanrong is not enabled, remove the entire Yuanrong startup section and do not configure `transfer_queue` backend as `Yuanrong`.
10. For VLM `mm_hash`, disable vLLM multimodal processor cache with `+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0`.
11. For rollout OOM, use `checkpoint_engine.update_weights_bucket_megabytes=4096`, `free_cache_engine=True`, and `enforce_eager=True`.
12. For geometry3k reward scoring, ensure `mathruler` is installed on every node.

## Non-Applicable Cases

- Yuanrong-specific commands are not applicable to ordinary non-Yuanrong multi-machine tests.
- The Metastore startup path was not the verified successful path in this record; ETCD-backed Yuanrong was verified.

## Verification Method

User explicitly confirmed this record is a directly usable conclusion. Successful path used ETCD-backed Yuanrong for Yuanrong mode; ordinary non-Yuanrong mode is obtained by deleting the Yuanrong-specific startup section and Yuanrong transfer_queue backend changes. Treat the conclusion as verified for the stated two-node A3/Qwen3-VL-8B/verl/FSDP topology.

## Risk And Safety Notes

- Environment variables that must affect Ray workers need to be exported before `ray start`, not only before the verl launch command.
- Do not promote Yuanrong-specific steps into the base non-Yuanrong flow.
- `ACL stream synchronize failed, error code:507035` can be a downstream symptom of invalid `ASCEND_RT_VISIBLE_DEVICES`; inspect plog before treating it as a stream-only problem.
- Disk space errors from Ray or HuggingFace datasets are usually cache/temp placement issues, not necessarily dataset corruption.
- The external image token mismatch patch attempted in this run was not adopted because training metrics became abnormal; prefer fixing FSDP topology first for this verified topology.

## Source Evidence

- User-provided operational record dated 2026-06-09 for two A3/560T nodes and Qwen3-VL-8B-Instruct geometry3k RL training.
- plog evidence for the ACL 507035 case: `ASCEND_RT_VISIBLE_DEVICES:[] error, input data range[0-16)`.
- Runtime signatures preserved in the incident record: Ray GPU count mismatch, Gloo loopback fallback, VLM token/feature mismatch, Yuanrong `RPC unavailable`, vLLM `mm_hash`, and disk-cache failures.

## Promotion Notes

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: reusable-incident -> incidents/
- Distill classification: general-knowledge -> knowledge/
- Suggested domains: docker, npu-ascend, mindspeed, verl, python
