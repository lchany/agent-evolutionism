---
type: runbook
date: 2026-06-25
title: "verl + TransferQueue + Yuanrong 手动拉起 SOP"
domain: verl-distributed-training
topics: [verl, transfer-queue, yuanrong, ppo, distributed-storage, ascend]
confidence: high
risk: medium
source_knowledge: []
source_incidents: []
sensitive: clean
skill_candidate: false
---

# verl + TransferQueue + Yuanrong 手动拉起 SOP

## When To Use

- verl PPO 训练需要启用 TransferQueue (TQ) 并使用 Yuanrong 作为分布式存储后端
- 单机或多机环境首次接入 Yuanrong 后端
- yuanrong 进程因端口被占 / 共享内存碎片 / datasystem 目录冲突导致启动失败需重新拉起
- 自动拉起模式暂不可用时的兜底方案

不适用:
- verl 默认 `SimpleStorage` 后端，无需 TQ
- Yuanrong 自动拉起模式 (本 SOP 不覆盖)

## Required Inputs

- verl 训练代码仓 (含 `vla.verl_train.trainer.main_ppo_sync`)
- python 环境可 `pip install`
- 容器内 `/dev/shm` 可扩容权限 (root 或具备 `mount -o remount` 能力)
- 多机场景需预先约定 `NODE_RANK` / `LOCAL_IP` / `MASTER_ADDR` (可通过 `torch.distributed` init 或 env vars 自取)
- 元数据组件二选一:
  - metastore (内置，零额外依赖)
  - etcd v3.5.12 (linux-arm64 包，目标为 ARM/NPU 服务器)

## Procedure

### Step 1. 修改 `ppo_trainer.yaml`

```yaml
transfer_queue:
  enable: True
  storage_backend: Yuanrong
  Yuanrong:
    auto_init: False
```

### Step 2. 切换主函数

TQ 启用后**必须**切换主函数 (原 `main_ppo` 不支持 TQ):

```bash
python3 -m vla.verl_train.trainer.main_ppo_sync
```

### Step 3. 安装 yuanrong

```bash
pip install openyuanrong-datasystem
which dscli  # 确认命令可用
```

### Step 4. 跑前清理 (关键，启动失败首先怀疑)

```bash
pkill -f datasystem
pkill -f yuanrong
pkill -f ray
rm -rf /dev/shm/*
```

注意 `pkill -f ray` 会杀掉机器上所有 ray 进程，复用同机其它 ray 任务须先评估。

### Step 5. 共享内存检查/扩容

```bash
df -h | grep shm                                    # 必须 > shared_memory_size_mb
mount -o remount,size=512G /dev/shm                  # 示例扩到 512G
```

示例 `shared_memory_size_mb=131072` (128GB)，扩容后留出余量。

### Step 6a. 单机拉起 — metastore 方式(推荐,零额外依赖)

```bash
dscli start -w \
  --worker_address "127.0.0.1:31501" \
  --start_metastore_service true \
  --metastore_address "127.0.0.1:2379" \
  --shared_memory_size_mb 131072
```

### Step 6b. 单机拉起 — etcd 方式

```bash
# 安装
ETCD_VER=v3.5.12
wget https://github.com/etcd-io/etcd/releases/download/v3.5.12/etcd-v3.5.12-linux-arm64.tar.gz
tar xzvf etcd-v3.5.12-linux-arm64.tar.gz
mv -f etcd-v3.5.12-linux-arm64/etcd /usr/local/bin/
mv -f etcd-v3.5.12-linux-arm64/etcdctl /usr/local/bin/
mv -f etcd-v3.5.12-linux-arm64/etcdutl /usr/local/bin/
rm -rf etcd-v3.5.12-linux-arm64*

# 启动 etcd
etcd --listen-client-urls http://127.0.0.1:2379 --advertise-client-urls http://127.0.0.1:2379

# 启动 yuanrong
dscli start -w \
  --worker_address "127.0.0.1:31501" \
  --etcd_address "127.0.0.1:2379" \
  --shared_memory_size_mb 131072
```

### Step 7. 多机拉起 — metastore 主从模式

> `${NODE_RANK}` / `${LOCAL_IP}` / `${MASTER_ADDR}` 需动态获取
> 共享存储场景下主从节点 `worker_address` **必须放不同位置**避免 datasystem 冲突

主节点:

```bash
dscli start \
  -d "./datasystem/node${NODE_RANK}" \
  -w \
    --worker_address "${LOCAL_IP}:31501" \
    --start_metastore_service true \
    --metastore_address "${MASTER_ADDR}:2379" \
    --shared_memory_size_mb 131072
```

从节点(只接 metastore 地址):

```bash
dscli start \
  -d "./datasystem/node${NODE_RANK}" \
  -w \
    --worker_address "${LOCAL_IP}:31501" \
    --metastore_address "${MASTER_ADDR}:2379" \
    --shared_memory_size_mb 131072
```

### Step 8 (可选). 大页内存优化

仅在启用 `--enable_huge_tlb true` 时需要:

```bash
sysctl -w vm.nr_hugepages=65536
grep HugePages_Total /proc/meminfo    # 校验已分配
```

### Step 9. 触发 verl PPO 训练

```bash
python3 -m vla.verl_train.trainer.main_ppo_sync
```

## Validation

1. `pip install openyuanrong-datasystem` 之后 `which dscli` 有输出
2. `dscli start -w ...` 之后 `ps -ef | grep dscli` 进程存活
3. 触发 verl PPO 训练，TransferQueue metric 出现非零吞吐，确认 yuanrong 真正在用
4. 多机: 各从节点 `dscli` 进程相互独立、`worker_address` 不冲突、`-d` 指定目录独立
5. 大页模式: `grep HugePages_Total /proc/meminfo` 显示 65536 已分配
6. 共享内存: `df -h | grep shm` 显示容量 ≥ `shared_memory_size_mb`

## Failure Handling

| 症状 | 可能原因 | 处置 |
|---|---|---|
| `dscli` 报端口占用 | 上次 yuanrong/datasystem 未退 | Step 4 清理后重启 |
| 启动挂起 / 无报错退出 | `/dev/shm` 碎片 | `rm -rf /dev/shm/*` + 重新拉起 |
| 多机从节点 datasystem 启动报冲突 | 主从 `worker_address` 同位置 | 拆到不同目录 (用 `-d` 隔离) |
| OOM / 共享内存不足 | `/dev/shm` < `shared_memory_size_mb` | Step 5 `mount -o remount,size=512G` |
| `--enable_huge_tlb` 启动失败 | 大页未预分配 | Step 8 `sysctl -w vm.nr_hugepages=65536` |
| 主函数报 TQ 不兼容 | 仍在用 `main_ppo` | 切换为 `main_ppo_sync` (Step 2) |

## Non-Applicable Cases

- verl 默认 `SimpleStorage` 后端，TQ 不需要
- 非 ARM/x86 目标平台的 etcd 二进制 (需要换平台包)
- Yuanrong 自动拉起模式 (文档称已支持但本 SOP 未覆盖步骤)
- 非 verl 训练框架、未集成 TransferQueue 的场景

## Related Knowledge

- knowledge/2026-06-25-yuanrong-multi-node-isolate-worker-address.md — 共享存储场景下主从 worker_address 须分区避坑
- projects/2026-06-25-verl-transferqueue-yuanrong-手动拉起-sop.md — 原始项目归档与残留风险

## Skill Promotion Notes

- 触发面广、步骤稳定，可考虑后续提炼为 OpenCode skill 候选 (`yuanrong-bringup`)
- 触发关键词: `verl 启用 TQ`, `yuanrong 拉起`, `transfer_queue`, `dscli 启动失败`
- 待跑过 3+ 次稳定复现后评估升级路径