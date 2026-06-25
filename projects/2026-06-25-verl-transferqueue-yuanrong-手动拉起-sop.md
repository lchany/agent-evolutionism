---
type: project
date: 2026-06-25
title: "verl + TransferQueue + Yuanrong 手动拉起 SOP"
domain: verl-distributed-training
topics: [verl, transfer-queue, yuanrong, ppo, distributed-storage, ascend]
status: promoted
sensitive: clean
related_incidents: []
extracted_knowledge:
  - knowledge/2026-06-25-yuanrong-multi-node-isolate-worker-address.md
  - runbooks/2026-06-25-verl-tq-yuanrong-hand-bringup.md
---

# verl + TransferQueue + Yuanrong 手动拉起 SOP

## Goal

将 verl 的 PPO 训练 rollout 存储后端从默认 `SimpleStorage` 切换为 **Yuanrong 分布式存储**，并在单机/多机环境下稳定运行 PPO 训练。TransferQueue 机制负责把 rollout 样本通过 Yuanrong 进行跨进程/跨节点存储与传输。

## Scope

- 适用: verl PPO 训练需要启用 TransferQueue + Yuanrong 后端的场景
- 覆盖: 单机与多机两类拉起方式
- 不覆盖: Yuanrong 自动拉起模式（原声称"现在已经支持"但文档未给步骤）
- 技术栈: verl (PyTorch)，openyuanrong-datasystem (`dscli`)，metastore / etcd 二选一

## Environment

- 操作系统: Linux ARM (etcd 示例用 `linux-arm64` 包推断)
- 目标硬件: 与 Ascend NPU 服务器一致 (arm64)
- Python 环境: verl 训练容器
- 关键依赖:
  - `pip install openyuanrong-datasystem` (提供 `dscli` 命令)
  - 可选元数据组件: etcd v3.5.12 (linux-arm64)
- 物理资源约束:
  - `/dev/shm` 容量须 > `shared_memory_size_mb`，文档示例为 131072MB ≈ 128GB，扩容目标 `mount -o remount,size=512G /dev/shm`
  - 大页内存(可选): 65536 个 (当启用 `--enable_huge_tlb true` 时)

## Timeline Summary

- 2026-05-29: 文档《verl + TQ + yuanrong 拉起指导》最后修改日期 (作者 廖奕洋 00940110)
- 历史阶段: 之前自动拉起 yuanrong 失败 → 本 SOP 改用手动拉起
- 当前阶段: 手动 SOP 已稳定 (文档来源)，原文人道"现在已经支持 [自动模式]"
- 2026-06-25: 经验萃取沉淀到 Experience Vault (本次归档)

## Key Commands

### 1. 修改配置 `ppo_trainer.yaml`

```yaml
transfer_queue:
  enable: True
  storage_backend: Yuanrong
  Yuanrong:
    auto_init: False
```

### 2. 切换主函数 (TQ 启用必需)

```bash
python3 -m vla.verl_train.trainer.main_ppo_sync
# 原: python3 -m vla.verl_train.trainer.main_ppo (不支持 TQ)
```

### 3. 安装 yuanrong

```bash
pip install openyuanrong-datasystem
```

### 4. 单机拉起 yuanrong

**方式 A — metastore (推荐，零额外组件):**

```bash
dscli start -w \
  --worker_address "127.0.0.1:31501" \
  --start_metastore_service true \
  --metastore_address "127.0.0.1:2379" \
  --shared_memory_size_mb 131072
```

**方式 B — etcd (需额外安装 etcd v3.5.12):**

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

### 5. 多机拉起 yuanrong (metastore 为例)

> `${NODE_RANK}`、`${LOCAL_IP}`、`${MASTER_ADDR}` 需动态获取 (文档未给获取脚本)。

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

从节点:

```bash
dscli start \
  -d "./datasystem/node${NODE_RANK}" \
  -w \
    --worker_address "${LOCAL_IP}:31501" \
    --metastore_address "${MASTER_ADDR}:2379" \
    --shared_memory_size_mb 131072
```

### 6. 运行前清理 (启动失败时首先怀疑)

```bash
pkill -f datasystem
pkill -f yuanrong
pkill -f ray
rm -rf /dev/shm/*
```

### 7. 共享内存扩容 / 大页内存

```bash
# 共享内存
df -h | grep shm
mount -o remount,size=512G /dev/shm

# 大页内存 (仅在 --enable_huge_tlb true 时)
sysctl -w vm.nr_hugepages=65536
grep HugePages_Total /proc/meminfo
```

## Key Files

- `ppo_trainer.yaml` (verl 训练入口配置)
  - `transfer_queue.enable` / `transfer_queue.storage_backend` / `transfer_queue.Yuanrong.auto_init` 三个字段为本次切换关键
- `vla.verl_train.trainer.main_ppo_sync` — TQ 启用后必须使用的主函数
  - 原 `main_ppo` 不支持 TransferQueue
- `./datasystem/node${NODE_RANK}/` — 多机时每节点隔离的 yuanrong 工作目录 (通过 `-d` 指定)

## Problems Encountered

1. **自动拉起 yuanrong 失败 (历史问题)** — 文档未给出根因与诊断步骤，仅给出"现在已经支持"的结论，本 SOP 改走手动路径作为可重复方案。
2. **Yuanrong 启动卡死/端口被占** — 多因上次任务未清理 `datasystem` / `yuanrong` 进程或 `/dev/shm/*` 碎片残留 → 强制 `pkill -f` + `rm -rf /dev/shm/*` 解决。
3. **共享存储目录冲突 (多机共享 PV)** — 主从节点 `worker_address` 写同一位置 → `datasystem` 启动报错 → 文档明确要求"主从必须放不同位置"。
4. **共享内存不足** — 默认容器 `/dev/shm` 远小于示例 128GB → `mount -o remount,size=512G` 动态扩容。
5. **缺少环境变量获取脚本** — 多机配置的 `NODE_RANK` / `LOCAL_IP` / `MASTER_ADDR` 文档未给统一取值方法 → 残留空白点。

## Final Solution

文档形成"配置改 → 主函数换 → 安装包 → 单机 metastore 或多机主从 → 启动前清理 + /dev/shm 扩容"五段式 SOP：
- 配置三关键字段 `enable/storage_backend.auto_init` 改写
- 主函数从 `main_ppo` 切换到 `main_ppo_sync`
- 单机优先 metastore (零依赖)；多机使用主从 metastore
- 启动前 `pkill -f datasystem/yuanrong/ray` + `rm -rf /dev/shm/*`
- `/dev/shm` 按需扩容到 512G

## Verification

**2026-06-25 用户确认五段式流程与多机目录避坑为明确结论**，已升级:

- Runbook draft (`runbooks/...`，已带 `confidence: high` `last_verified: 2026-06-25`)
- Knowledge draft (`knowledge/...`，已带 `confidence: high` `last_verified: 2026-06-25`)

下次实施仍建议在每台节点复跑以下逐项校验以再巩固:

1. 在容器内执行 `df -h | grep shm` 确认 `/dev/shm` 已 > `shared_memory_size_mb`
2. `pip install openyuanrong-datasystem` 后 `which dscli` 确认命令存在
3. `dscli start -w ...` 后 `ps -ef | grep dscli` 确认进程存活
4. 触发 verl PPO 训练，检查 TransferQueue metric 出现非零吞吐，确认 yuanrong 真正在用
5. 多机场景下各从节点 `dscli` 进程相互独立、`worker_address` 不冲突、`-d` 目录独立
6. 大页模式启用后检查 `grep HugePages_Total /proc/meminfo` 命中

## Residual Risks

- **未亲自验证**: 本 project 归档来自二手文档，未实测 end-to-end；不可直接作为 Runbook
- **自动拉起模式缺口**: 文档称"现在已经支持"但未给步骤；若未来要恢复自动模式须重新调研
- **环境变量取值空白**: `NODE_RANK` / `LOCAL_IP` / `MASTER_ADDR` 没有统一获取脚本，需自行补全 (可借助 `torch.distributed` 初始化或环境变量约定)
- **`pkill -f ray` 副作用**: 会杀掉机器上所有 ray 进程；复用同机的其它 ray 任务前需评估
- **共享存储目录冲突不可自动检测**: 多机共享 PV 模式下，目录错放导致后续写入错乱 / 碰撞，无禁钞机制
- **多核 IPC socket 数未说明**: 共享内存 131072MB 是单条容量阈值，未指明多实例并发时的总上限
- **etcd 持久化与 HA 配置未涉及**: 文档只给 listen 单 IP，集群化后改造成本未评估
- **平台假设**: etcd 用 `linux-arm64` 包推断目标环境为 ARM；若改用 x86 平台安装命令需调整

## Related Incidents

无（本归档来自他人文档审计，未发生本人执行期间的命令级失败）。

## Extracted Knowledge

2026-06-25 由用户确认为明确经验，已升级为通用可复用归档(`--verified`):

- **Runbook**: `runbooks/2026-06-25-verl-tq-yuanrong-hand-bringup.md` — 六步式手动拉起流程 (配置改 → 主函数换 → 安装 → 单机 metastore / 多机主从 → 启动前清理 → `/dev/shm` 扩容 / 大页)
- **Knowledge**: `knowledge/2026-06-25-yuanrong-multi-node-isolate-worker-address.md` — 共享存储场景下主从节点 `worker_address` 必须放不同位置避免 `datasystem` 冲突

待后续补充:

- **Incident Candidate**: 自动拉起 yuanrong 失败 (历史问题) — 但缺根因与复现细节,暂未升级为 reusable incident;待自动模式调研后补

## Sensitive Data Handling

无敏感信息。命令行仅涉及本机回环地址 (127.0.0.1) 与示例变量 (`${LOCAL_IP}` / `${MASTER_ADDR}` 占位符)，未含密码、token、API key 或私有路径。