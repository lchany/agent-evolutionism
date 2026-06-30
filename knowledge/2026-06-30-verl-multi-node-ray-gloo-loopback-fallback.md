---
type: knowledge
date: 2026-06-30
title: "VERL multi-node Ray Gloo loopback fallback diagnosis and prevention"
domain: verl-distributed-training
topics: [verl, ray, gloo, loopback, socket, ifname, multi-node, ascend, npu]
confidence: verified
risk: low
source_project: /mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253
source_incidents:
  - /mnt/disk2t/l30002999/verl_four_node_runs/runs/scaling-20260628-190253/debug/2node_8card_optimized/root-cause.md
sensitive: reviewed
skill_candidate: true
---

# VERL multi-node Ray Gloo loopback fallback diagnosis and prevention

## Symptom

Multi-node VERL training fails during `WorkerDict.__init__` before step 1. The log contains Gloo warnings such as:

```text
Gloo could not resolve hostname to a local address; falling back to loopback.
```

followed by `Gloo connectFullMesh` attempts using `127.0.0.1` local/remote endpoints, and then Ray actor creation failure inside `torch.distributed.init_process_group`.

## Root cause

`GLOO_SOCKET_IFNAME` (and sometimes `HCCL_SOCKET_IFNAME`, `MASTER_ADDR`, `VLLM_HOST_IP`) is set in the training driver shell, but Ray worker actors do not inherit driver-shell exports. They inherit the environment of the already-running Ray daemon (`raylet`/`gcs_server`). If the daemon was started without these variables, Gloo has no routable interface binding and falls back to `127.0.0.1`, making cross-node full-mesh impossible.

## Why it happens in VERL specifically

- VERL uses Ray actors (`WorkerDict`, `ActorRollout`, `RefPolicy`, etc.) that call `torch.distributed.init_process_group` internally.
- The training script often `export`s network variables and then connects to an existing Ray cluster with `ray.init(address=...)`.
- `runtime_env.env_vars` shown in the driver log does not include `GLOO_SOCKET_IFNAME`/`HCCL_SOCKET_IFNAME`/`MASTER_ADDR`/`VLLM_HOST_IP`, so the actors see none of them.

## Diagnostic checklist

1. Locate the first network-specific failure in the training log. It is usually before model loading.
2. Check whether Gloo endpoints are loopback (`127.0.0.1`).
3. Compare the Ray start procedure between a successful baseline run and the failing run:
   - Did the baseline export `GLOO_SOCKET_IFNAME` **before** `ray start` on every node?
   - Does the failing run only export it inside the training script?
4. Capture `ray_preflight.log` and `ray_verify.json` to confirm node count and environment inheritance.

## Fix / prevention

Export all network variables **before** starting Ray on every node, not only in the training script:

```bash
export GLOO_SOCKET_IFNAME=<comm-iface>
export HCCL_SOCKET_IFNAME=<comm-iface>
export MASTER_ADDR=<head-ip>
export MASTER_PORT=29520
export VLLM_HOST_IP=<local-node-ip>   # different on head and worker
export HCCL_HOST_SOCKET_PORT_RANGE=60000-63000
export HCCL_NPU_SOCKET_PORT_RANGE=60000-63000
# optional but recommended
export HCCL_WHITELIST_DISABLE=1
export HCCL_TIMEOUT=7200
export HCCL_CONNECT_TIMEOUT=7200
export HCCL_EXEC_TIMEOUT=7200
```

Then start Ray with explicit node IPs:

```bash
# head
ray start --head --node-ip-address=<head-ip> --port=6380 --resources='{"NPU": 4}'

# worker
ray start --address=<head-ip>:6380 --node-ip-address=<worker-ip> --resources='{"NPU": 4}'
```

Verify before training:

```python
import ray, json
ray.init(address='<head-ip>:6380')
resources = ray.cluster_resources()
nodes = [n for n in ray.nodes() if n.get('Alive')]
assert len(nodes) == expected_nodes
assert resources.get('NPU', 0) == expected_npu
```

## What does NOT work

- Setting `GLOO_SOCKET_IFNAME` only in the training driver shell after `ray.init`.
- Passing it via `runtime_env.env_vars` unless explicitly configured and verified.
- Relying on Ray's default interface selection in containerized or multi-homed environments.

## Verification

After the fix, the training log should show:

- No Gloo loopback fallback warning.
- Successful Gloo full-mesh peer connectivity before model initialization.
- `WorkerDict.__init__` completing without actor death.

## Related records

- `runbooks/2026-06-26-verl-dual-node-ascend-vllm-hccl-troubleshooting.md`
- `runbooks/2026-06-26-a3-qwen3-vl-8b-verl-fsdp-yuanrong-multinode.md`
