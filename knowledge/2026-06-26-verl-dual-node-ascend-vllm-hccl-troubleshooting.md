---
type: knowledge
date: 2026-06-26
title: "VERL dual-node Ascend vLLM HCCL troubleshooting"
domain: npu-ascend
topics: [verl, ray, vllm-ascend, hccl, multi-node]
applies_to: ["VERL multi-node training on Ascend/NPU with Ray and vLLM rollout"]
confidence: verified
risk: medium
source_projects: []
source_incidents: []
last_verified: 2026-06-26
source_incidents: [incidents/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md]
sensitive: redacted
skill_candidate: false
---

# VERL dual-node Ascend vLLM HCCL troubleshooting

## Applicability

Use this knowledge when debugging multi-node VERL training on Ascend/NPU where Ray actors launch vLLM rollout workers and HCCL initialization fails or behaves differently from the driver shell.

## Trigger Signals

- HCCL `EJ0003` bind-port-already-bound during vLLM initialization.
- Stack contains vLLM EngineCore, Worker_TP, `tensor_model_parallel_all_gather`, or `hcclCommInitRootInfoConfig`.
- Ray cluster appears healthy but vLLM/HCCL worker processes fail.
- Environment variables exported in the training script do not affect remote actor behavior.

## Required Inputs

- Ray head address and active node list.
- Container names or execution environment for every node.
- Network interface and per-node IP used for Ray/vLLM/HCCL.
- Training script and rollout engine settings.
- Paths to custom reward modules or any external files loaded by Ray actors.

## Procedure

1. Clean Ray and stale training processes before every real run. After repeated failures, restart all training containers.
2. Confirm Ray has the expected two-node resource view.
3. Use Ray node affinity to print worker environment on each node. Verify `VLLM_HOST_IP` is node-local and HCCL variables are present.
4. Put HCCL variables on the `ray start` command for both head and worker nodes, not only in the driver training script.
5. Do not broadcast head `VLLM_HOST_IP` through `ray.init(runtime_env.env_vars)`.
6. For Ascend vLLM dual-node EngineCore EJ0003, try `VLLM_USE_V1=0` and source ATB env.
7. Ensure every path read by Ray actors exists on every node with matching content.

## Non-Applicable Cases

- Driver-only code paths where no Ray actors run remotely.
- Pure PyTorch distributed jobs that do not use vLLM rollout workers.
- HCCL failures caused by physical network/firewall/device faults; those need separate network and NPU diagnostics.

## Verification Method

- `ray status` shows all expected nodes and no pending/recent failures.
- Node-affinity Ray task prints expected `VLLM_HOST_IP`, `HCCL_HOST_SOCKET_PORT_RANGE`, and `HCCL_NPU_SOCKET_PORT_RANGE` on every node.
- Training log no longer contains `EJ0003` or `vllm/v1/engine` failure.
- Training reaches the progress loop or emits step metrics.

## Risk And Safety Notes

- Avoid `pkill -f` patterns that match the cleanup shell itself. Use bracket forms such as `[v]LLMHttpServer`.
- Do not assume Ray's `GPU` resource label means CUDA GPUs in Ascend/NPU setups; it may be a compatibility scheduling resource.
- Keep private IPs and dense logs out of durable knowledge records.

## Source Evidence

- Project archive: `projects/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md`.
- Incident: `incidents/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md`.

## Promotion Notes

This is reusable enough for a runbook. It may later become or update a VERL/NPU debugging skill if repeated across more projects.
