---
type: project
date: 2026-06-25
title: "多机 A3 Qwen3-VL-8B verl FSDP Yuanrong 强化学习调通经验"
domain: npu-ascend
topics:
  - verl
  - qwen3-vl
  - fsdp
  - yuanrong
  - ray
  - vllm-ascend
  - mindspeed
  - multi-node-training
status: draft
sensitive: redacted
related_incidents: []
extracted_knowledge: []
---

# 多机 A3 Qwen3-VL-8B verl FSDP Yuanrong 强化学习调通经验

## Goal

沉淀用户提供的已调通记录：在两台 A3/560T 节点上，使用 `verl + FSDP + transfer_queue/Yuanrong + Ray + vLLM-Ascend` 跑通 `Qwen3-VL-8B-Instruct` 多机强化学习训练。

## Scope

适用于后续类似场景的项目级参考：

- 多台 Atlas A3/560T 节点。
- Qwen3-VL-8B-Instruct 多模态 RL。
- `verl` 多机训练。
- `FSDP1 + TP` 组合。
- Yuanrong 作为 `transfer_queue` 后端。
- Ray 集群调度多节点 NPU 资源。

本记录来自用户提供的已调通经验，具体 IP、账号、内部链接等敏感或环境专属信息已脱敏；未在本次对话中重新执行训练验证，因此暂保持 `draft`。

## Environment

用户记录中的关键环境：

- 容器镜像：`quay.io/ascend/vllm-ascend:v0.18.0-a3`。
- 容器要求：`--privileged`、`--network host`、`--ipc=host`、大 shm，例如 `--shm-size 1024g`。
- Yuanrong `shared_memory_size_mb`: `131072`，容器 shm 必须大于该值。
- MindSpeed：`core_r0.15.3`。
- Megatron-LM：`core_v0.15.3`。
- `mbridge`: `https://github.com/ISEEKYAN/mbridge.git`。
- `verl`: main 分支。
- `openyuanrong-datasystem`: pip 安装。
- etcd：用户记录使用 v3.5.31 linux-arm64 包。
- 模型：`Qwen/Qwen3-VL-8B-Instruct`。
- 数据集：`hiyouga/geometry3k`，使用 `verl/examples/data_preprocess/geo3k.py` 预处理。

所有节点必须保持一致：

- 容器镜像与启动挂载。
- `pip list`。
- 模型路径。
- 数据集路径。
- `verl`、`MindSpeed`、`Megatron-LM`、`mbridge` 版本。
- Ray worker 可继承的环境变量。

## Timeline Summary

1. 所有节点启动 vLLM-Ascend A3 容器，确保 shm 足够。
2. 所有节点安装 MindSpeed、Megatron-LM、mbridge、verl、etcd、openyuanrong-datasystem。
3. 所有节点下载一致路径的模型和数据集，并完成 Geo3K 预处理。
4. 启动前清理历史 `datasystem`、`yuanrong`、`ray` 进程以及 `/dev/shm` 残留。
5. Yuanrong 初期尝试 metastore 方式，遇到跨节点 RPC/KV 访问失败；改用 etcd 方式成功。
6. 启动 Ray 集群，并确保 Ray worker 继承 Gloo 网卡和 NPU 可见设备环境变量。
7. 修改 `ppo_trainer.yaml`，启用 Yuanrong transfer queue，关闭自动初始化。
8. 多机使用 `verl.trainer.main_ppo_sync` 启动。
9. 依次处理 Ray 资源识别、Gloo 网卡、依赖包、VLM token-feature 对齐、ACL runtime、mm_hash、OOM、磁盘空间等问题。

## Key Commands

### 容器 shm 检查

```bash
df -h | grep shm
```

### 启动前清理

```bash
pkill -f datasystem
pkill -f yuanrong
pkill -f ray
rm -rf /dev/shm/*
```

### Yuanrong 推荐 etcd 方式

主节点启动 etcd：

```bash
etcd --listen-client-urls http://<master_ip>:2379 \
  --advertise-client-urls http://<master_ip>:2379
```

主节点启动 worker：

```bash
dscli start -w \
  --worker_address "<master_ip>:31501" \
  --etcd_address "<master_ip>:2379" \
  --shared_memory_size_mb 131072
```

从节点启动 worker：

```bash
dscli start -w \
  --worker_address "<worker_ip>:31501" \
  --etcd_address "<master_ip>:2379" \
  --shared_memory_size_mb 131072
```

### Ray 启动前关键环境变量

必须在 `ray start` 之前设置，使 Ray worker 继承：

```bash
export GLOO_SOCKET_IFNAME="<正式通信网卡>"
export ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
```

如果 Ray head 使用非默认端口，例如 8888，verl 启动前设置：

```bash
export RAY_ADDRESS=<master_ip>:8888
```

### Ray 本地临时目录迁移

```bash
mkdir -p /mnt/disk/ray_tmp
ray stop --force
ray start ... --temp-dir=/mnt/disk/ray_tmp
```

### 关键 verl 参数

```bash
actor_rollout_ref.actor.fsdp_config.fsdp_size=8
+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0
actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=4096
actor_rollout_ref.rollout.free_cache_engine=True
actor_rollout_ref.rollout.enforce_eager=True
```

## Key Files

- `/vllm-workspace/verl/verl/trainer/config/ppo_trainer.yaml`
- `worker_start.sh`
- `~/ascend/log/debug/plog`

`ppo_trainer.yaml` 中关键配置：

```yaml
transfer_queue:
  enabled: true
  storage_backend: "Yuanrong"
  auto_init: false
```

多机主函数使用：

```text
verl.trainer.main_ppo_sync
```

单机预验证时可改回：

```text
verl.trainer.main_ppo
```

## Problems Encountered

### 1. Ray local disk warning

现象：Ray 集群启动后出现本地磁盘不足告警。

处理：将 Ray temp-dir 指到大容量数据盘，例如 `/mnt/disk/ray_tmp`。

### 2. Ray status 可见 32 卡，但 verl 识别不到

根因：`ray status` 是集群视角；verl Python 进程没有连接到正确 Ray 集群。

修复：

```bash
export RAY_ADDRESS=<master_ip>:8888
```

### 3. Gloo 使用错误网卡

根因：`GLOO_SOCKET_IFNAME` 只对 Gloo 生效，但 verl/torch_npu 在 Ray worker 内启动；如果变量只在训练脚本中设置，Ray worker 继承不到。

修复：在所有节点 `ray start` 前设置：

```bash
export GLOO_SOCKET_IFNAME="<正式通信网卡>"
```

### 4. 缺少 `mathruler`

修复：所有节点安装：

```bash
pip install mathruler
```

### 5. 多机图像特征和 token 不匹配

现象：单机不出现，多机出现 image features 与 image tokens 不匹配。

有效修复：

```bash
actor_rollout_ref.actor.fsdp_config.fsdp_size=8
```

根因：TP=4、32GPU、FSDP1 下，如果不设置 `fsdp_size`，近似 full mesh：

- image token 分布在多个 shard。
- TP 又在 shard 内切 hidden state。
- padding/packing 后 image token 被切开。
- image features 与 tokens 对不齐。

设置 `fsdp_size=8` 后，image token 被锁在一个 shard 内，不再跨 shard。

### 6. ACL stream synchronize failed, error code 507035

现象：

```text
RuntimeError: ACL stream synchronize failed, error code:507035
```

根因：查看 `~/ascend/log/debug/plog` 后确认 `ASCEND_RT_VISIBLE_DEVICES=[]` 设置非法，导致 NPU runtime 初始化失败。

修复：所有节点在 `ray start` 前设置：

```bash
export ASCEND_RT_VISIBLE_DEVICES=0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
```

### 7. Yuanrong metastore 跨节点 RPC/KV 失败

现象：从节点访问主节点 KV 存储失败，RPC unavailable。

处理：改用 etcd 方式拉起 Yuanrong。

### 8. `mm_hash` 问题

修复：关闭 vLLM 多模态 processor cache：

```bash
+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0
```

### 9. 显存 OOM

修复参数：

```bash
actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=4096
actor_rollout_ref.rollout.free_cache_engine=True
actor_rollout_ref.rollout.enforce_eager=True
```

其中 `update_weights_bucket_megabytes=4096` 是关键。

### 10. 磁盘容量不足

处理：

- Ray temp-dir 指到大盘。
- 训练中间数据放到指定大盘目录。
- 从节点 Docker root 空间不足时迁移 Docker 根目录。

## Final Solution

稳定跑通的核心组合：

1. 所有节点环境、包、模型、数据路径一致。
2. 容器 shm 大于 Yuanrong `shared_memory_size_mb`。
3. Yuanrong 多机使用 etcd，不使用本次失败过的 metastore 路径。
4. Ray 启动前设置并继承：
   - `GLOO_SOCKET_IFNAME`
   - `ASCEND_RT_VISIBLE_DEVICES`
5. verl 启动前显式设置 `RAY_ADDRESS`。
6. `ppo_trainer.yaml` 中启用 Yuanrong transfer queue，`auto_init: false`。
7. 多机使用 `verl.trainer.main_ppo_sync`。
8. Qwen3-VL 多机 TP+FSDP 下设置：
   - `actor_rollout_ref.actor.fsdp_config.fsdp_size=8`
9. 多模态 cache 问题设置：
   - `+actor_rollout_ref.rollout.engine_kwargs.vllm.mm_processor_cache_gb=0`
10. OOM 缓解设置：
   - `actor_rollout_ref.rollout.checkpoint_engine.update_weights_bucket_megabytes=4096`
   - `actor_rollout_ref.rollout.free_cache_engine=True`
   - `actor_rollout_ref.rollout.enforce_eager=True`

## Verification

用户提供的记录说明该配置已调通；本次归档未重新执行训练、Ray、Yuanrong 或 NPU 验证命令。因此：

- 用户侧经验：已验证调通。
- 本次归档动作：已创建 draft 并通过 vault validate。
- 本条记录状态保持 `draft`，避免把未在本会话复验的经验直接升级为通用 runbook/knowledge。

## Residual Risks

- 具体 IP、网卡名、路径、容器名、数据盘路径均需按实际环境替换。
- `verl` main 分支变化较快，后续接口或参数路径可能变化。
- `fsdp_size=8` 是该拓扑与 TP/FSDP 组合下的有效值，其他卡数、TP、FSDP mesh 需要重新评估。
- Yuanrong、Ray、vLLM-Ascend 版本变化可能影响参数或行为。
- etcd 安装记录中 tar 包版本与 cd 目录名曾出现不一致，实际操作需核对解压目录。

## Related Incidents

后续可拆分为独立 incident：

- Ray status 可见资源但 verl 未连接 Ray cluster。
- Ray worker 未继承 `GLOO_SOCKET_IFNAME` 导致 Gloo 错误网卡。
- `ASCEND_RT_VISIBLE_DEVICES=[]` 导致 ACL runtime 初始化失败。
- Qwen3-VL 多机 FSDP/TP 下 image token 与 image feature 不匹配。
- Yuanrong metastore 跨节点 RPC unavailable。
- vLLM 多模态 `mm_hash` cache 问题。
- rollout 权重更新导致 OOM。

## Extracted Knowledge

可后续提升为 knowledge/runbook 的可迁移经验：

1. 多机 Ray + NPU 训练中，Ray worker 继承环境比训练脚本内 export 更关键。
2. `ray status` 正常不代表 Python/verl 进程连接到了同一个 Ray cluster。
3. VLM 多机训练中，FSDP/TP mesh 会影响 image token 与 feature 对齐。
4. ACL stream 错误需要查 plog，Python 异常不一定暴露真正根因。
5. Yuanrong 多机 transfer queue 优先选择 etcd 管理跨节点 worker。

## Sensitive Data Handling

- 原始主从节点 IP 使用 `<master_ip>`、`<worker_ip>` 占位。
- 内部链接未写入。
- 用户工号、姓名未写入正文。
- 未保存原始密集日志。
