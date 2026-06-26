---
type: project
date: 2026-06-26
title: "多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录"
domain: unknown
topics: []
status: verified
sensitive: reviewed
related_incidents: []
extracted_knowledge: []
---

# 多台A3 Qwen3-VL-8B verl+FSDP+元戎 强化学习调通记录

## Goal

## Scope

This record is a strictly verified, directly reusable multi-machine setup and test experience for A3 + Qwen3-VL-8B + verl + FSDP + Ray/NPU workflows.

Important boundary: the **Yuanrong startup section is an optional Yuanrong-specific layer**. If the entire "拉起元戎" section is removed, the remaining procedure is the ordinary non-Yuanrong multi-machine setup/test flow.

## Environment

- Hardware: two A3 nodes, 16 NPUs per node, 32 NPUs total.
- Software baseline: `quay.io/ascend/vllm-ascend:v0.18.0-a3`, MindSpeed `core_r0.15.3`, Megatron-LM `core_v0.15.3`, verl `main`.
- Model/data: Qwen3-VL-8B-Instruct and geometry3k.
- Yuanrong-specific configuration, when used: `openyuanrong-datasystem`, `dscli`, ETCD-backed worker startup, `shared_memory_size_mb=131072`.

## Timeline Summary

## Key Commands

## Key Files

## Problems Encountered

- Ray cluster showed all cards, but the verl Python process did not see the full cluster until `RAY_ADDRESS=<head-ip>:8888` was exported before launching verl.
- Gloo selected the wrong network interface when `GLOO_SOCKET_IFNAME` was not exported before Ray workers were started.
- `ACL stream synchronize failed, error code:507035` was caused by invalid `ASCEND_RT_VISIBLE_DEVICES=[]`; set `ASCEND_RT_VISIBLE_DEVICES=0,1,...,15` before `ray start` on every node.
- Multi-machine VLM image features/tokens mismatch was caused by TP=4 + FSDP1 full-mesh sharding splitting image tokens across shards; setting `actor_rollout_ref.actor.fsdp_config.fsdp_size=8` keeps image tokens inside one shard.
- Yuanrong Metastore path failed in this experiment with remote worker `RPC unavailable`; ETCD-backed Yuanrong startup was verified successful.

## Final Solution

Use the flow as two layers:

1. Base reusable multi-machine flow: container/env consistency, model/data path consistency, Ray cluster startup, `RAY_ADDRESS`, `GLOO_SOCKET_IFNAME`, `ASCEND_RT_VISIBLE_DEVICES`, verl config, FSDP sizing, VLM rollout/OOM fixes.
2. Optional Yuanrong layer: start Yuanrong workers with ETCD and configure verl `transfer_queue` backend as `Yuanrong` with `auto_init: False`.

## Verification

User confirmed this is strictly verified practical experience and can be directly reused.

## Residual Risks

- Yuanrong Metastore mode was not the verified successful path in this record; ETCD mode was the verified path.
- The non-Yuanrong flow should omit the Yuanrong worker startup section and Yuanrong transfer queue backend changes.

## Related Incidents

## Extracted Knowledge

## Sensitive Data Handling

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: reusable-incident -> incidents/
- Distill classification: general-knowledge -> knowledge/
- Suggested domains: docker, npu-ascend, mindspeed, verl, python
