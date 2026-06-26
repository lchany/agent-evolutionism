---
type: knowledge
date: 2026-06-26
title: "多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录"
domain: unknown
topics: []
applies_to: []
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

## Required Inputs

- Node IPs and communication interface name.
- Per-node NPU device count and intended `ASCEND_RT_VISIBLE_DEVICES` range.
- Ray head address/port.
- Model and dataset paths consistent across nodes.
- Whether Yuanrong is enabled; if not, skip the Yuanrong startup and transfer_queue backend changes.

## Procedure

1. Keep all nodes consistent: same image, Python packages, model path, dataset path, and preprocessing output path.
2. Start Ray only after exporting critical environment variables on every node: `GLOO_SOCKET_IFNAME=<comm-iface>` and `ASCEND_RT_VISIBLE_DEVICES=0,1,...,15`.
3. Ensure the verl launch process attaches to the intended Ray cluster: `export RAY_ADDRESS=<head-ip>:8888`.
4. For multi-machine VLM FSDP1 + TP, set `actor_rollout_ref.actor.fsdp_config.fsdp_size=8` to avoid splitting image tokens across shards.
5. If Yuanrong is enabled, start Yuanrong as an optional layer. Verified path: ETCD-backed `dscli start -w` on every node with each node's own `worker_address` and the head node `etcd_address`.
6. If Yuanrong is not enabled, remove the entire Yuanrong startup section and do not configure `transfer_queue` backend as `Yuanrong`.
7. For VLM `mm_hash`, disable vLLM multimodal processor cache with `+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0`.
8. For rollout OOM, use `checkpoint_engine.update_weights_bucket_megabytes=4096`, `free_cache_engine=True`, and `enforce_eager=True`.

## Non-Applicable Cases

- Yuanrong-specific commands are not applicable to ordinary non-Yuanrong multi-machine tests.
- The Metastore startup path was not the verified successful path in this record; ETCD-backed Yuanrong was verified.

## Verification Method

User confirmed the record is strictly verified and directly reusable. Successful path used ETCD-backed Yuanrong for Yuanrong mode; ordinary non-Yuanrong mode is obtained by deleting the Yuanrong-specific startup section and Yuanrong transfer_queue backend changes.

## Risk And Safety Notes

- Environment variables that must affect Ray workers need to be exported before `ray start`, not only before the verl launch command.
- Do not promote Yuanrong-specific steps into the base non-Yuanrong flow.

## Source Evidence

## Promotion Notes

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: reusable-incident -> incidents/
- Distill classification: general-knowledge -> knowledge/
- Suggested domains: docker, npu-ascend, mindspeed, verl, python
