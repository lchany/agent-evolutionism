---
type: incident
date: 2026-06-26
title: "VERL dual-node Ascend vLLM HCCL troubleshooting"
domain: npu-ascend
topics: [verl, ray, vllm-ascend, hccl, docker, multi-node]
status: verified
confidence: verified
sensitive: redacted
source_projects: [projects/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md]
related_knowledge: [knowledge/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md]
---

# VERL dual-node Ascend vLLM HCCL troubleshooting

## Trigger Signal

VERL dual-node Ascend/NPU training reaches vLLM EngineCore or rollout initialization and fails with HCCL port binding errors, often after Ray restarts or multi-node vLLM setup changes.

## Context

- Two-node VERL baseline on Ascend/NPU, 8 visible NPUs per node, total 16 NPU.
- Ray cluster head and worker were in Docker containers with host networking.
- vLLM rollout used tensor parallel workers and Ray actors.
- Node IPs and private paths are redacted or represented as placeholders.

## Failed Command Or Operation

Background launch of the dual-node VERL baseline training script after starting a two-node Ray cluster.

## Error Signature

Primary signature:

```text
hcclCommInitRootInfoConfig(...), error code is 7
Communication_Error_Bind_IP_Port(EJ0003): Failed to bind the IP port. Reason: The IP address and port have been bound already.
```

Related signatures encountered during recovery:

```text
ray status timed out waiting for GCS
Session name ... does not match persisted value ... Perhaps there was an error connecting to Redis.
FileNotFoundError: Custom module file not found: dummy_reward.py
```

## Failed Attempts

1. Reusing an existing Ray cluster without full cleanup: left stale Ray/vLLM process state and repeated HCCL bind failures.
2. Passing head-node `VLLM_HOST_IP` through `ray.init(runtime_env.env_vars)`: remote vLLM workers inherited the wrong IP.
3. Putting HCCL variables only in the training script: driver saw them, but Ray workers did not.
4. Using `pkill -f` patterns that matched their own shell command line: remote cleanup could hang or terminate unexpectedly.

## Root Cause

The final verified cause was a combination of environment propagation and vLLM engine selection:

- `VLLM_HOST_IP` must be node-local in multi-node vLLM. It must not be broadcast from the head driver runtime_env to all Ray workers.
- vLLM/HCCL worker processes inherit the environment from the Ray node process. HCCL settings must be present when `ray start` is executed on each node, not only when the driver training script starts.
- In this Ascend dual-node setup, vLLM V1 EngineCore repeatedly hit HCCL EJ0003 during initialization. Disabling V1 (`VLLM_USE_V1=0`) and sourcing ATB environment switched to the stable path.
- A later non-HCCL failure occurred because the custom reward file existed only on the head node; Ray reward actors on the worker node could not import it.

## Resolution

Applied fixes:

1. Remove `VLLM_HOST_IP` from VERL `ray.init(runtime_env.env_vars)` propagation; keep only safe cluster-wide variables such as `GLOO_SOCKET_IFNAME`.
2. Before each real training run: stop Ray, kill stale VERL/vLLM/Ray workers, and restart Ray. After repeated failures, restart both containers before Ray restart.
3. Start Ray head/worker with node-local `VLLM_HOST_IP` and HCCL environment:

```bash
VLLM_HOST_IP=<node-ip> \
GLOO_SOCKET_IFNAME=<ifname> \
HCCL_SOCKET_IFNAME=<ifname> \
HCCL_WHITELIST_DISABLE=1 \
HCCL_TIMEOUT=7200 \
HCCL_CONNECT_TIMEOUT=7200 \
HCCL_EXEC_TIMEOUT=7200 \
HCCL_HOST_SOCKET_PORT_RANGE=auto \
HCCL_NPU_SOCKET_PORT_RANGE=auto \
HCCL_OP_EXPANSION_MODE=AIV \
ray start ...
```

4. In the training script, source both CANN and ATB envs and disable vLLM V1:

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
export VLLM_USE_V1=0
```

5. Sync custom reward scripts and other Ray actor-imported files to the same path on all nodes.

6. Use self-safe `pkill -f` patterns, for example `[v]LLMHttpServer`, to avoid killing the current cleanup shell.

## Verification

- Ray status after clean restart showed 2 active nodes, 64 CPU, 16 GPU resources, and 16 NPU resources.
- Ray node-affinity tasks confirmed each node had its own `VLLM_HOST_IP` and inherited HCCL variables after moving them to `ray start`.
- Final training log showed `VLLM_USE_V1=0`, no `vllm/v1/engine` stack, no EJ0003, no missing reward file, and entered the training progress loop (`Training Progress: 0/20`).

## Reuse Notes

For future VERL multi-node Ascend/NPU failures, check Ray worker environment directly with a node-affinity Ray task before assuming driver-shell exports are visible to vLLM workers.

## Non-Applicable Cases

- Single-node training that does not use Ray remote workers across nodes.
- Non-vLLM rollout engines where HCCL is not initialized inside vLLM EngineCore or Worker_TP.
- Cases where all Ray actor-imported files are packaged in runtime_env or installed as Python modules rather than read from shared paths.

## Sensitive Data Handling

Private node IPs are represented as placeholders. No credentials, tokens, raw auth files, or dense logs are stored here.
