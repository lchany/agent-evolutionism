---
type: knowledge
date: 2026-06-25
title: "Yuanrong 多机共享存储下 worker_address 须分区避免 datasystem 冲突"
domain: distributed-storage
topics: [yuanrong, datasystem, multi-node, shared-storage, worker-address]
applies_to: [verl-transfer-queue, yuanrong-distributed-storage, ascend-npu-training]
confidence: high
risk: medium
source_projects: [projects/2026-06-25-verl-transferqueue-yuanrong-手动拉起-sop.md]
source_incidents: []
last_verified: 2026-06-25
sensitive: clean
skill_candidate: false
---

# Yuanrong 多机共享存储下 worker_address 须分区避免 datasystem 冲突

## Applicability

- 使用 Yuanrong (`openyuanrong-datasystem`) 作为分布式存储后端的多机部署
- 多节点共享同一物理存储 / PV / 共享卷的场景
- 任何通过 `dscli start -w --worker_address ...` 启动多个 worker 的方案

## Trigger Signals

- 多机部署 yuanrong，主从节点启动后从节点报 datasystem 目录初始化失败
- `dscli` 错误信息包含 `datasystem` 冲突 / 路径已存在 / 初始化冲突等关键词
- 主从节点共享同一卷但 `worker_address` 配在相同相对路径下
- 多节点复用同一共享挂载点 (`-d` 写同一目录)

## Required Inputs

- 多机共享存储挂载 (PV / NFS / 共享卷)
- `NODE_RANK` 区分各节点身份
- `LOCAL_IP` / `MASTER_ADDR` 用于 yuanrong 通信
- 每个 yuanrong worker 独立的目录位 (推荐 `./datasystem/node${NODE_RANK}/`)

## Procedure

1. 每节点用独立的 `-d` 路径隔离工作目录,如 `-d "./datasystem/node${NODE_RANK}"`
2. 主从节点的 `worker_address` 写**不同**位置 (用 LOCAL_IP + 同一端口即可,Yuanrong 自身区分靠 `-d` 与 IP)
3. 主节点带 `--start_metastore_service true --metastore_address <MASTER_ADDR>:2379`
4. 从节点只接 `--metastore_address <MASTER_ADDR>:2379`(不带 start_metastore_service)
5. 验证每节点 `./datasystem/node${NODE_RANK}/` 目录独立存在且互不串写

## Non-Applicable Cases

- 单机部署(仅一个 worker,无主从概念,不存在目录冲突)
- 多机但每节点独占独立本地盘(非共享存储,无冲突风险)
- 使用其它分布式存储后端 (非 Yuanrong) 的多机部署

## Verification Method

1. `ls -la ./datasystem/` 应看到 `node0/ node1/ ...` 多个独立目录而非单一共享目录
2. 各节点 `dscli` 进程的 cwd 与 `-d` 参数指向各自独立目录
3. 任一节点写入数据后,**仅该节点目录**有新文件,其它节点目录不出现同文件
4. 多机训练启动后无 datasystem 冲突错误日志

## Risk And Safety Notes

- 即便 `worker_address` 拆开,__作品内部共享内存 `/dev/shm` 不分区仍可能造成 IPC 残留干扰;启动前 `rm -rf /dev/shm/*` 清理
- 共享 PV 场景下,目录误放会导致后续写入错乱/碰撞,无自动禁钞机制,完全依赖人工对齐
- 多节点并发写同一卷可能产生额外 IO 压力,需评估共享卷带宽

## Source Evidence

来自《verl + TransferQueue + Yuanrong 手动拉起 SOP》文档第 5 节多机拉起原文:
> 主节点和从节点的 worker_address 需放置不同位置,防止 datasystem 冲突

源 project 归档: `projects/2026-06-25-verl-transferqueue-yuanrong-手动拉起-sop.md`
源 runbook: `runbooks/2026-06-25-verl-tq-yuanrong-hand-bringup.md` Step 7

## Promotion Notes

- 该条已从项目归档提炼为通用 knowledge(2026-06-25 验证)
- 触发关键词覆盖明确,后续如出现 `"datasystem 冲突"`, `"yuanrong 多机目录"`, `"worker_address 冲突"` 等场景可直接检索命中
- 未来若出现反例(如 Yuanrong 新版自动隔离主从目录),须更新 Non-Applicable Cases 并下调 confidence