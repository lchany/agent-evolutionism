---
type: runbook
date: 2026-06-26
title: "A3 Qwen3-VL-8B verl FSDP Yuanrong 多机强化学习 Runbook"
domain: verl-distributed-training
topics: [a3, qwen3-vl, verl, fsdp, ray, yuanrong, vllm-ascend, torch-npu]
confidence: verified
risk: medium
source_knowledge:
  - knowledge/2026-06-26-多台a3-qwen3-vl-8b-verl-fsdp-元戎-强化学习调通记录.md
source_incidents:
  - incidents/2026-06-26-多台a3-qwen3-vl-8b-verl-fsdp-元戎-强化学习调通记录.md
sensitive: reviewed
skill_candidate: false
---

# A3 Qwen3-VL-8B verl FSDP Yuanrong 多机强化学习 Runbook

## When To Use

- Two-node or similar A3 NPU cluster running Qwen3-VL-8B-Instruct RL with verl, Ray, FSDP, vLLM-Ascend, and torch_npu.
- Need to enable verl TransferQueue with Yuanrong as the storage backend.
- Need to debug Ray resource visibility, Gloo interface selection, VLM token/feature mismatch, `mm_hash`, rollout OOM, or disk-cache exhaustion in this stack.

This runbook is a directly reusable conclusion for the stated two-node A3/Qwen3-VL-8B/verl/FSDP/Yuanrong topology. Revalidate only when topology, versions, TP/FSDP layout, or model family materially changes.

Do not use Yuanrong-specific steps when running ordinary non-Yuanrong verl multi-node tests. In that case, keep the Ray/NPU/verL parts and remove Yuanrong startup plus `transfer_queue.backend.storage_backend=Yuanrong`.

## Required Inputs

- `<head-ip>`, `<worker-ip>`, and `<comm-iface>` for the training network.
- A large shared or per-node data disk for model, dataset, Ray temp state, and Python/HF/Torch caches.
- Identical container image and package set on every node.
- Qwen3-VL-8B-Instruct model path and geometry3k parquet paths that are identical on every node.
- Optional Yuanrong backend decision. If enabled, container shm must be larger than `shared_memory_size_mb`.

## Procedure

### 1. Container and package baseline

Use `quay.io/ascend/vllm-ascend:v0.18.0-a3` or the verified equivalent image. Start containers with host network, host IPC or sufficiently large shm, Ascend device mappings, driver/toolkit mounts, and project data mounts.

In this user's environment, future Ascend/NPU containers should include both shared mounts unless explicitly overridden:

```bash
-v /mnt/disk2t:/mnt/disk2t \
-v /mnt/sfs_turbo:/mnt/sfs_turbo
```

Install consistently on every node:

```bash
pip install -e MindSpeed
pip install -e Megatron-LM
pip install -e mbridge
pip install -r requirements-npu.txt
pip install -v -e verl
pip install openyuanrong-datasystem
pip install mathruler
```

Keep `pip list` aligned across nodes.

### 2. Model and dataset

Download model and dataset to paths that exist identically on every node. Preprocess geometry3k with verl's `examples/data_preprocess/geo3k.py` and ensure `train.parquet` / `test.parquet` paths are identical across the cluster.

### 3. Clean stale services before each bring-up

```bash
pkill -f datasystem
pkill -f yuanrong
pkill -f ray
rm -rf /dev/shm/*
```

Use this only when it is safe to stop all Ray/Yuanrong jobs on the machine.

### 4. Start Yuanrong if TransferQueue uses Yuanrong

Verified path: ETCD-backed Yuanrong.

Head node:

```bash
etcd --listen-client-urls http://<head-ip>:2379 \
  --advertise-client-urls http://<head-ip>:2379

dscli start -w \
  --worker_address "<head-ip>:31501" \
  --etcd_address "<head-ip>:2379" \
  --shared_memory_size_mb 131072
```

Worker node:

```bash
dscli start -w \
  --worker_address "<worker-ip>:31501" \
  --etcd_address "<head-ip>:2379" \
  --shared_memory_size_mb 131072
```

Metastore mode produced cross-node `RPC unavailable` in the verified run; treat it as not verified for this topology.

### 5. Start Ray with inherited env

Export these before `ray start` on every node so Ray workers inherit them:

```bash
export GLOO_SOCKET_IFNAME="<comm-iface>"
export HCCL_IF_IP="<local-ip>"
export ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
export HCCL_CONNECT_TIMEOUT=1500
export HCCL_HOST_SOCKET_PORT_RANGE=60000-60050
export HCCL_NPU_SOCKET_PORT_RANGE=61000-61050
```

Head node:

```bash
ray start --head --port=8888 \
  --min-worker-port=20122 \
  --max-worker-port=20999 \
  --temp-dir=<large-data-disk>/ray_tmp
```

Worker node:

```bash
ray start --address=<head-ip>:8888 \
  --min-worker-port=20122 \
  --max-worker-port=20999
```

Validate with `ray status` and confirm 32 NPUs for a 2 x 16 topology.

### 6. Configure verl

In `verl/trainer/config/ppo_trainer.yaml`, enable TransferQueue only when Yuanrong is desired:

```yaml
transfer_queue:
  enable: True
  metrics:
    enabled: false
    port: 0
  backend:
    storage_backend: Yuanrong
    Yuanrong:
      auto_input: False
      auto_init: False
```

Use `verl.trainer.main_ppo_sync` for the Yuanrong/TQ path.

### 7. Launch training

Before launch:

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
source /usr/local/Ascend/nnal/atb/set_env.sh
export RAY_ADDRESS=<head-ip>:8888
export HF_HOME=<large-data-disk>/hf_home
export HF_DATASETS_CACHE=$HF_HOME/datasets
export TRANSFORMERS_CACHE=$HF_HOME/models
export TORCH_HOME=<large-data-disk>/torch_home
export HCCL_CONNECT_TIMEOUT=7200
export HCCL_EXEC_TIMEOUT=7200
export HCCL_HOST_SOCKET_PORT_RANGE=auto
export HCCL_NPU_SOCKET_PORT_RANGE=auto
export HCCL_OP_EXPANSION_MODE=AIV
```

Keep these verified arguments for the two-node Qwen3-VL-8B topology:

```bash
python3 -m verl.trainer.main_ppo_sync \
  data.train_batch_size=128 \
  data.max_prompt_length=1024 \
  data.max_response_length=3072 \
  data.image_key=images \
  actor_rollout_ref.model.enable_gradient_checkpointing=True \
  actor_rollout_ref.model.use_remove_padding=True \
  actor_rollout_ref.rollout.max_num_batched_tokens=4096 \
  actor_rollout_ref.rollout.tensor_model_parallel_size=4 \
  actor_rollout_ref.actor.fsdp_config.fsdp_size=8 \
  +actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0 \
  +actor_rollout_ref.rollout.engine_kwargs.vllm.mm_encoder_tp_mode=data \
  actor_rollout_ref.rollout.enable_chunked_prefill=False \
  actor_rollout_ref.rollout.enforce_eager=True \
  actor_rollout_ref.rollout.free_cache_engine=True \
  actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=4096 \
  trainer.n_gpus_per_node=16 \
  trainer.nnodes=2 \
  trainer.device=npu
```

## Validation

1. `df -h | grep shm` inside the container shows shm larger than Yuanrong `shared_memory_size_mb`.
2. `dscli start -w ...` returns `[OK]` on all nodes when Yuanrong is enabled.
3. `ray status` shows the expected total NPU/GPU resources.
4. verl process uses the intended cluster after `RAY_ADDRESS=<head-ip>:8888` is exported.
5. No Gloo loopback fallback appears; if it does, restart Ray after exporting `GLOO_SOCKET_IFNAME`.
6. No plog `ASCEND_RT_VISIBLE_DEVICES:[]` error appears; if it does, restart Ray after exporting the visible device list.
7. Training passes the previous failure points: Ray resource check, Gloo connection, Qwen3-VL image token/features match, vLLM `mm_hash`, and rollout weight update.

## Failure Handling

| Symptom | Root Cause | Resolution |
|---|---|---|
| `Total available GPUs 16.0 is less than total desired GPUs 32` | verl Python process not attached to the Ray head | `export RAY_ADDRESS=<head-ip>:8888` before launch |
| Gloo connects to `127.0.0.1` / loopback | Ray workers did not inherit `GLOO_SOCKET_IFNAME` | Export `GLOO_SOCKET_IFNAME` before `ray start`, then restart Ray |
| `ACL stream synchronize failed, error code:507035` | Invalid `ASCEND_RT_VISIBLE_DEVICES=[]` caused NPU runtime init failure | Export `ASCEND_RT_VISIBLE_DEVICES=0,...,15` before `ray start`; confirm plog |
| `Image features and image tokens do not match` | TP=4 + FSDP1 full mesh split image tokens across shards | Set `actor_rollout_ref.actor.fsdp_config.fsdp_size=8` |
| Yuanrong `RPC unavailable` in Metastore mode | Cross-node Metastore/KV path failed in this run | Use ETCD-backed Yuanrong startup |
| vLLM `mm_hash` cached item assertion | Multimodal processor cache mismatch | Set `+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0` |
| Rollout/checkpoint OOM | Weight update/cache pressure | Set update bucket `4096`, `free_cache_engine=True`, `enforce_eager=True` |
| Ray `/tmp/ray` disk over 95% full | Ray temp state on small system disk | Use `ray start --temp-dir=<large-data-disk>/ray_tmp` |
| `ModuleNotFoundError: mathruler` | Reward dependency missing | `pip install mathruler` on every node |
| `datasets.load_dataset` not enough disk | HF/datasets cache on small disk | Set `HF_HOME`, `HF_DATASETS_CACHE`, `TRANSFORMERS_CACHE`, `TORCH_HOME` to large disk |

## Non-Applicable Cases

- Non-Yuanrong training: remove Yuanrong startup and TransferQueue backend changes.
- Different node count, card count, TP, model size, FSDP2 strategy, or non-VLM model: re-evaluate `fsdp_size` and VLM-specific flags.
- Yuanrong Metastore mode: this runbook records it as failed for the verified topology; do not treat it as the known-good path.

## Related Records

- projects/2026-06-26-多台a3-qwen3-vl-8b-verl-fsdp-元戎-强化学习调通记录.md
- incidents/2026-06-26-多台a3-qwen3-vl-8b-verl-fsdp-元戎-强化学习调通记录.md
- knowledge/2026-06-26-多台a3-qwen3-vl-8b-verl-fsdp-元戎-强化学习调通记录.md
- runbooks/2026-06-25-verl-tq-yuanrong-hand-bringup.md
