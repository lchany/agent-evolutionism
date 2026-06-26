---
type: incident
date: 2026-06-26
title: "多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录"
domain: unknown
topics: []
status: verified
confidence: high
sensitive: reviewed
source_projects: []
related_knowledge: []
---

# 多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录

## Trigger Signal

## Context

Strictly verified multi-machine A3 Qwen3-VL-8B verl/FSDP/Ray/NPU setup with optional Yuanrong transfer queue layer.

Boundary: Yuanrong is not required for the base multi-machine setup/test procedure. Removing the whole Yuanrong startup section yields the ordinary non-Yuanrong flow.

## Failed Command Or Operation

## Error Signature

- Ray has full cluster resources, but verl does not recognize all 32 NPUs.
- Gloo uses an invalid/default interface such as `lo`.
- `RuntimeError: ACL stream synchronize failed, error code:507035`.
- Multi-machine-only VLM image feature/token mismatch.
- Yuanrong Metastore remote worker fails with `RPC unavailable`.
- `mm_hash` errors or rollout OOM in VLM rollout.

## Failed Attempts

## Root Cause

- Ray worker processes only inherit environment prepared before `ray start`; late exports in the verl launch script are insufficient for Gloo/NPU runtime behavior.
- Without explicit `RAY_ADDRESS`, the verl Python process may not attach to the intended Ray head.
- TP=4 + FSDP1 full mesh can split image tokens across shards; TP then cuts hidden states inside shards, and padding/packing can make image features and tokens misalign.
- In this verified run, Yuanrong Metastore mode failed for remote worker KV access; ETCD mode was the working cluster metadata path.

## Resolution

- Export before Ray startup on every node: `GLOO_SOCKET_IFNAME=<comm-iface>` and `ASCEND_RT_VISIBLE_DEVICES=0,1,...,15`.
- Export before verl launch: `RAY_ADDRESS=<head-ip>:8888`.
- For multi-machine VLM FSDP1, set `actor_rollout_ref.actor.fsdp_config.fsdp_size=8`.
- For Yuanrong mode, use ETCD-backed `dscli start -w ... --etcd_address <head-ip>:2379 --shared_memory_size_mb 131072`; treat Metastore as not verified for this scenario.
- For non-Yuanrong mode, remove the entire Yuanrong startup section and do not enable Yuanrong transfer queue backend.
- For `mm_hash`, set `+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0`.
- For rollout OOM, set `actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=4096`, `free_cache_engine=True`, and `enforce_eager=True`.

## Verification

User confirmed the record is strictly verified, explicitly learnable, and directly reusable.

## Reuse Notes

Reuse this as a high-confidence incident bundle for multi-node A3 verl/FSDP/VLM/Ray/NPU setup. Split reuse into base multi-machine flow and optional Yuanrong layer.

## Non-Applicable Cases

- Do not apply Yuanrong worker startup or `transfer_queue` backend changes when running ordinary non-Yuanrong multi-machine tests.

## Sensitive Data Handling

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: reusable-incident -> incidents/
- Distill classification: general-knowledge -> knowledge/
- Suggested domains: docker, npu-ascend, mindspeed, verl, python
