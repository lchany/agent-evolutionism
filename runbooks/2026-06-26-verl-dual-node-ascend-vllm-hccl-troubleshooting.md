---
type: runbook
date: 2026-06-26
title: "VERL dual-node Ascend vLLM HCCL troubleshooting"
domain: npu-ascend
topics: [verl, ray, vllm-ascend, hccl, troubleshooting]
confidence: verified
risk: medium
source_knowledge: [knowledge/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md]
source_incidents: [incidents/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md]
sensitive: redacted
skill_candidate: false
---

# VERL dual-node Ascend vLLM HCCL troubleshooting

## When To Use

Use when a VERL multi-node Ascend/NPU training run using Ray and vLLM fails during rollout/vLLM/HCCL initialization, especially with `EJ0003` or vLLM EngineCore errors.

## Required Inputs

- Container or host execution commands for every node.
- Ray head IP/port and worker IPs.
- Network interface name used by Ray/Gloo/HCCL.
- Training script path and custom reward/module paths.
- Expected NPU device selection per node.

## Procedure

1. Stop active training and clean Ray on every node:

```bash
ray stop --force || true
pkill -f "[p]ython3 -m verl.trainer.main_ppo" || true
pkill -f "[v]LLMHttpServer" || true
pkill -f "[E]ngineCore" || true
pkill -f "[W]orker_TP" || true
```

2. If prior attempts left GCS/session/zombie state, restart all training containers.

3. Start Ray with per-node vLLM/HCCL envs. On the head:

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
VLLM_HOST_IP=<head-ip> \
GLOO_SOCKET_IFNAME=<ifname> \
HCCL_SOCKET_IFNAME=<ifname> \
HCCL_WHITELIST_DISABLE=1 \
HCCL_TIMEOUT=7200 \
HCCL_CONNECT_TIMEOUT=7200 \
HCCL_EXEC_TIMEOUT=7200 \
HCCL_HOST_SOCKET_PORT_RANGE=auto \
HCCL_NPU_SOCKET_PORT_RANGE=auto \
HCCL_OP_EXPANSION_MODE=AIV \
ray start --head --node-ip-address=<head-ip> --port=<port> --num-gpus=<npu-count>
```

4. Start each worker with the same HCCL env and its own `VLLM_HOST_IP=<worker-ip>`.

5. Verify Ray worker environment with a node-affinity Ray task before launching training.

6. In the VERL training script, source CANN and ATB envs and disable vLLM V1 when EngineCore EJ0003 appears:

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
export VLLM_USE_V1=0
```

7. Sync custom reward scripts and other Ray actor-imported files to identical paths on every node.

8. Launch the training in the background with durable log/PID/status artifacts.

## Validation

- `ray status` shows all expected nodes active and the expected CPU/GPU/NPU resource counts.
- Ray worker environment includes node-local `VLLM_HOST_IP` and HCCL variables on every node.
- Log does not contain `EJ0003`, `hcclCommInitRootInfoConfig`, or `vllm/v1/engine` failure.
- Log reaches `Training Progress` or step metrics.

## Failure Handling

- If Ray GCS reports session mismatch, stop Ray, remove Ray temp dirs, and restart containers before retrying.
- If cleanup hangs, inspect `pkill -f` patterns for self-matching.
- If reward actors fail with `FileNotFoundError`, sync custom module files to all nodes.
- If EJ0003 persists after worker env is verified, inspect network/firewall/HCCL port state and vLLM version compatibility.

## Non-Applicable Cases

- Single-node VERL jobs without remote Ray actors.
- Multi-node jobs that do not use vLLM rollout.
- Failures after training steps start, such as optimizer OOM or reward quality issues.

## Related Knowledge

- `knowledge/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md`

## Skill Promotion Notes

Candidate for inclusion in a VERL/NPU debug skill after another independent confirmation.
