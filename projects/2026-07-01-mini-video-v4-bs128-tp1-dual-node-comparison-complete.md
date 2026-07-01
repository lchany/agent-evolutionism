---
type: project
date: 2026-07-01
title: "mini-video v4 bs128 tp1 dual-node comparison complete"
domain: verl
topics: ["verl", "ray", "ascend", "npu", "qwen3vl", "mini-video", "performance-comparison"]
status: verified
sensitive: reviewed
related_incidents: []
extracted_knowledge: []
---

# Mini-Video v4 双机 16 卡训练经验总结

## Goal

验证 Qwen3-VL-2B-Instruct 在 VERL PPO 流程中的 mini-video v4 视频帧压缩传输方案，比较 baseline 与优化版的单步耗时和 reward/score 偏差。

本次训练对象：

- 模型：`/mnt/sfs_turbo/models/Qwen3-VL-2B-Instruct`
- 数据集：`/mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl`
- Reward 文件：`/mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl/verlfiles/reward.py`
- Reward 函数：`compute_kitti_28f_7x4_reward`
- 代码根目录：容器内 `/vllm-workspace/verl`
- 容器：`qwen3vl2b_video_leicheng_much`
- 机器：`192.168.0.206` + `192.168.0.13`
- 卡：两机均使用后 8 卡，`8,9,10,11,12,13,14,15`
- 规模：`2 node * 8 card = 16 card`
- Batch size：`data.train_batch_size=128`
- 实际完成对比的 TP：`actor_rollout_ref.rollout.tensor_model_parallel_size=1`
- Step：`trainer.total_training_steps=10`

本次不是验证旧实现。baseline 和 optimized 都使用同一份 `/vllm-workspace/verl` 代码，唯一对比变量是 `VERL_MINI_VIDEO_TRANSPORT`。

## Scope

适用场景：

- Ascend/NPU 上做 VERL 双机或多机训练对比。
- 需要比较 baseline 与优化版性能，并保证训练字段完全一致。
- 需要排查 Ray、vLLM、HCCL、torch_npu 在双机后 8 卡上的启动问题。
- 需要验证数据传输优化是否带来 step time 收益。
- 需要从失败重试中区分环境故障、Ray 故障、NPU runtime 故障和代码效果。
- 需要在 `status.txt` 不可靠时，从日志和进程状态判断训练是否完成。

不直接适用：

- 不同模型、不同数据集、不同 reward 函数。
- `tp=2` 或更高 TP 的性能结论。
- 四机或更多节点跨网卡配置。
- 使用旧容器、旧代码目录或旧 mini-video 实现。
- 要求严格确定性逐样本 reward 对齐的实验。本次只比较 step 级 `score/reward mean` 偏差。

## Environment

必须使用：

- 容器：`qwen3vl2b_video_leicheng_much`
- 代码：`/vllm-workspace/verl`
- 数据盘：`/mnt/disk2t`
- 模型盘：`/mnt/sfs_turbo`

禁止误用：

- 不使用旧容器或其他同名相似容器作为证据。
- 不使用旧代码目录 `/mnt/disk2t/l30002999/verl_container_workspace/verl`。
- 不把方案 HTML 文档当成容器内文件查找；方案文档在宿主机 `/home/download_md_html/视频帧压缩方案优化版本-v4.html`。

Ray/HCCL 环境：

```bash
MASTER_ADDR=192.168.0.206
MASTER_PORT=29520
RAY_ADDRESS=192.168.0.206:6380
GLOO_SOCKET_IFNAME=enp23s0f3
HCCL_SOCKET_IFNAME=enp23s0f3
ASCEND_RT_VISIBLE_DEVICES=8,9,10,11,12,13,14,15
ASCEND_VISIBLE_DEVICES=8,9,10,11,12,13,14,15
NPU_VISIBLE_DEVICES=8,9,10,11,12,13,14,15
HCCL_HOST_SOCKET_PORT_RANGE=60000-63000
HCCL_NPU_SOCKET_PORT_RANGE=60000-63000
```

Ray 负责把 206 作为 head、13 作为 worker，供 VERL 的 `TaskRunner`、`WorkerDict`、`AgentLoopWorker`、vLLM HTTP server 等 actor 调度。`VLLM_HOST_IP` 必须使用当前节点自己的 IP：206 上为 `192.168.0.206`，13 上为 `192.168.0.13`。

## Key Files

训练脚本：

```text
/mnt/disk2t/l30002999/mini_video_v4_compare/scripts/container_train_qwen3vl2b_kitti_28f_7x4_v4_compare.sh
```

最终有效日志：

```text
/mnt/disk2t/l30002999/mini_video_v4_compare/runs/20260701-133316-bs128-tp1-step10-v4-final/baseline/train.log
/mnt/disk2t/l30002999/mini_video_v4_compare/runs/20260701-133316-bs128-tp1-step10-v4-final/optimized_retry3/train.log
```

失败尝试日志：

```text
/mnt/disk2t/l30002999/mini_video_v4_compare/runs/20260701-133316-bs128-tp1-step10-v4-final/optimized/train.log
/mnt/disk2t/l30002999/mini_video_v4_compare/runs/20260701-133316-bs128-tp1-step10-v4-final/optimized_retry1/train.log
/mnt/disk2t/l30002999/mini_video_v4_compare/runs/20260701-133316-bs128-tp1-step10-v4-final/optimized_retry2/train.log
```

本次对齐后的主要代码文件：

- `verl/utils/mini_video_transport.py`
- `verl/utils/dataset/rl_dataset.py`
- `verl/experimental/agent_loop/single_turn_agent_loop.py`
- `verl/experimental/agent_loop/agent_loop.py`
- `verl/trainer/main_ppo.py`
- `verl/utils/reward_score/__init__.py`
- `verl/utils/reward_score/kitti_tracking.py`

## Baseline/Optimized Alignment

脚本只允许两个模式：

```bash
MODE="${1:?baseline|optimized}"
RUN_DIR="${2:?run dir}"
TP="${3:-2}"
```

实际完成跑显式传了 `TP=1`，日志确认：

```bash
actor_rollout_ref.rollout.tensor_model_parallel_size=1
```

唯一的 baseline/optimized 差异：

```bash
if [[ "${MODE}" == "optimized" ]]; then
  export VERL_MINI_VIDEO_TRANSPORT=1
else
  export VERL_MINI_VIDEO_TRANSPORT=0
fi
```

共同字段：

```bash
data.train_batch_size=128
actor_rollout_ref.actor.ppo_mini_batch_size=128
trainer.n_gpus_per_node=8
trainer.nnodes=2
trainer.total_training_steps=10
trainer.total_epochs=10
trainer.device=npu
reward.custom_reward_function.path=/mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl/verlfiles/reward.py
reward.custom_reward_function.name=compute_kitti_28f_7x4_reward
```

`trainer.total_epochs=10` 是共同修复：数据轮次不足时，仅设置 `trainer.total_training_steps=10` 不能保证实际 10 step。该修改不是优化变量。

固定 HCCL 端口范围也是共同环境修复，不是优化变量。

## Environment Isolation And Recovery Procedure

本次最有复用价值的经验不是短测数值，而是如何保证双机 Ray/NPU 训练环境不被旧进程、旧 Ray session、错误容器、错误代码目录和 NPU runtime 残留污染。

核心原则：

- 训练前只认一个容器标准：两台机器都使用 `qwen3vl2b_video_leicheng_much`。
- 训练前只认一个代码标准：容器内 `/vllm-workspace/verl`。
- Ray 集群必须每轮重建，不复用未知状态的旧 Ray session。
- 206 和 13 必须同时清理，不能只处理 head 节点。
- 清理后必须做 NPU smoke test，再启动 Ray，再启动训练。
- 不修改宿主机系统配置来“试错”；容器重启、Ray 重启、进程清理优先。
- 每次训练必须写独立 run 目录、`train.log`、`pid.txt`、`status.txt`，让失败重试可追溯。

启动前检查：

```bash
docker ps --format '{{.Names}} {{.Status}}' | grep qwen3vl2b_video_leicheng_much
docker exec qwen3vl2b_video_leicheng_much test -d /vllm-workspace/verl
docker exec qwen3vl2b_video_leicheng_much test -d /mnt/disk2t
docker exec qwen3vl2b_video_leicheng_much test -d /mnt/sfs_turbo
test -d /mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl
test -f /mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl/verlfiles/reward.py
test -d /mnt/sfs_turbo/models/Qwen3-VL-2B-Instruct
```

NPU smoke test：

```bash
npu-smi info -l
ASCEND_RT_VISIBLE_DEVICES=8,9,10,11,12,13,14,15 python3 - <<'PY'
import torch
import torch_npu
print(torch.npu.device_count())
torch.npu.set_device(0)
print("ok")
PY
```

清理残留：

```bash
ps -ef | grep -E 'ray|vllm|verl.trainer.main_ppo|TaskRunner|WorkerDict|AgentLoopWorker' | grep -v grep
ray stop --force || true
pkill -f 'verl.trainer.main_ppo' || true
pkill -f 'vllm' || true
pkill -f 'ray::' || true
```

关键判断：

- 如果有旧 `raylet`、`gcs_server`、`dashboard`、`TaskRunner`、`WorkerDict`、`AgentLoopWorker`、`vLLMHttpServer`、`EngineCore`、`verl.trainer.main_ppo`，都可能占卡、占 HCCL 端口或保留错误 actor 状态。
- 如果 `ray status` 还能看到旧节点或旧资源，说明 Ray 环境没有清干净。
- 如果 `npu-smi` 或 `torch_npu` smoke test 失败，不要直接重跑训练。
- 如果 13 曾重启、掉线或容器退出，必须重新清 Ray、重新拉起容器、重新加入 Ray 集群。

恢复顺序：

1. 停掉两机容器内 Ray：`ray stop --force`。
2. 查杀两机容器内训练/vLLM/Ray 残留进程。
3. 如出现 NPU runtime 初始化错误，重启两机 `qwen3vl2b_video_leicheng_much` 容器。
4. 验证 `/mnt/disk2t`、`/mnt/sfs_turbo`、`/vllm-workspace/verl` 仍在容器内可见。
5. 在两机分别做 `torch_npu` 后 8 卡 smoke test。
6. 206 作为 Ray head 启动，13 作为 Ray worker 加入。
7. 确认 `VLLM_HOST_IP` 使用各自节点 IP，确认 HCCL/GLOO 网卡一致。
8. 再启动 baseline 或 optimized 训练。

`SetDevice 507033` / `aclInit 507008` 的处理经验：

- 这类错误通常说明 NPU runtime 或上一轮 Ray/vLLM actor 状态不干净。
- 本次有效恢复方式是重启两机容器、重做 NPU smoke test、重启 Ray。
- 不要通过修改宿主机系统配置解决这类一次性 runtime 污染，除非已经确认是宿主机设备或驱动缺失。

13 节点掉线后的处理经验：

- 13 被 Ray 标记为 dead 后，即使机器恢复，也不能直接继续用原 Ray 集群。
- 先确认 13 容器状态，再清理两机 Ray 和训练残留。
- 重新启动 Ray 集群后再重跑；掉线前的部分 step 只作为故障证据，不作为性能结论。

状态文件滞后的处理经验：

- `status.txt` 只能作为辅助信号。
- 若 `status.txt` 显示 `RUNNING`，但进程已退出且 `train.log` 有完整 `Training Progress: 100%`，以日志和进程为准。
- 若日志末尾有清理阶段 warning/Traceback，要先判断它发生在训练 step 完成前还是完成后。

训练启动：

```bash
RUN_ROOT=/mnt/disk2t/l30002999/mini_video_v4_compare/runs/20260701-133316-bs128-tp1-step10-v4-final
mkdir -p "$RUN_ROOT"/baseline "$RUN_ROOT"/optimized_retry3

nohup bash /mnt/disk2t/l30002999/mini_video_v4_compare/scripts/container_train_qwen3vl2b_kitti_28f_7x4_v4_compare.sh \
  baseline "$RUN_ROOT/baseline" 1 \
  > "$RUN_ROOT/baseline/train.log" 2>&1 &
echo $! > "$RUN_ROOT/baseline/pid.txt"

nohup bash /mnt/disk2t/l30002999/mini_video_v4_compare/scripts/container_train_qwen3vl2b_kitti_28f_7x4_v4_compare.sh \
  optimized "$RUN_ROOT/optimized_retry3" 1 \
  > "$RUN_ROOT/optimized_retry3/train.log" 2>&1 &
echo $! > "$RUN_ROOT/optimized_retry3/pid.txt"
```

监控：

```bash
grep -E 'training/global_step|timing_s/step|critic/score/mean|critic/rewards/mean|Training Progress|Traceback|RuntimeError|HCCL|SetDevice|aclInit|marked dead' \
  "$RUN_ROOT/optimized_retry3/train.log" | tail -n 200
```

完成判断不要只看 `status.txt`。本次 `optimized_retry3/status.txt` 保持 `RUNNING`，但进程已退出且日志包含 `Training Progress: 100%|...| 10/10` 和 `Final validation metrics: None`，因此以日志 step 和进程状态为准。

## Problems Encountered

1. 文档与容器角色混淆  
   方案文档在宿主机 `/home/download_md_html/视频帧压缩方案优化版本-v4.html`，容器只用于训练执行。

2. 代码目录用错风险  
   当前代码必须是 `/vllm-workspace/verl`，不是 `/mnt/disk2t/l30002999/verl_container_workspace/verl`。

3. 本地环境无 NPU 设备  
   本地机器无 `/dev/davinci*` 等设备节点，改用 `192.168.0.206` 和 `192.168.0.13`。

4. Docker 挂载 `/etc/ascend_install.info` 类型问题  
   宿主机文件/目录类型不匹配会导致挂载异常。不要随意改宿主机系统配置，参考 206 正确形态或使用正确机器。

5. TP=2 HCCL 端口绑定问题  
   TP=2 出现 HCCL `Communication_Error_Bind_IP_Port` / `hcclCommInitRootInfoConfig error code 7`。按用户允许范围切到 `tp=1`，并统一固定 HCCL 端口范围。

6. 只跑 2 step  
   `trainer.total_epochs=2` 不足以让 `trainer.total_training_steps=10` 实际生效。共同改为 `trainer.total_epochs=10`。

7. 13 节点中途掉线  
   优化版第一次跑到 step 5 后，13 被 Ray 标记为 dead，机器短时不可达，容器退出。恢复后清理 Ray/训练残留并重新加入集群。该失败日志不作为最终性能结论。

8. `SetDevice 507033` / `aclInit 507008`  
   13 恢复后出现 NPU runtime 初始化错误。通过重启 206 和 13 的 `qwen3vl2b_video_leicheng_much` 容器、重做 smoke test、重启 Ray 后恢复。

9. 结束后的 `resource_tracker` Traceback  
   `optimized_retry3` 完成 10 step 后出现 Python `multiprocessing.resource_tracker` 的 `KeyError`。该 Traceback 出现在 `Training Progress: 100%` 与 `Final validation metrics: None` 之后，不影响已提取的 10 step 指标。

## Verification

最终有效对比应从当次 `train.log` 重新解析，不把某次短测的具体性能或 reward/score 数值归档为经验结论。原因是 10 step 短测结果受环境状态、Ray/vLLM 调度、节点状态和随机生成影响，每次测试不一定相同。

归档只保留验证方法：

- baseline 与 optimized 都必须有完整 10 个 `training/global_step`。
- 从日志提取 `timing_s/step`，分别计算全 10 step 平均值和去掉第 1 步 warmup 后的平均值。
- 从日志提取 `critic/score/mean` 和 `critic/rewards/mean`，按相同步号比较平均绝对偏差和最大绝对偏差。
- 若 `status.txt` 与日志矛盾，以 `Training Progress: 100%`、实际 step 指标和进程退出状态为准。
- 结束后的 `multiprocessing.resource_tracker` 清理告警如果出现在 10 step 完成之后，不影响已提取指标。

## Reusable Lessons

1. 最大经验是环境防干扰：双机都要清 Ray、vLLM、训练进程和旧 actor 状态，不能只处理 head 节点。
2. 遇到 NPU runtime 初始化错误时，先判断是否是残留状态污染；本次有效恢复是重启两机容器、重做 smoke test、重启 Ray。
3. worker 节点中途掉线后，不要续用原 Ray 集群；恢复后必须重新清理并重建集群。
4. 对比实验先锁变量。此次唯一变量是 `VERL_MINI_VIDEO_TRANSPORT`。
5. 不要只看脚本默认值，要看训练日志实际 Hydra 参数。本脚本默认 `TP=2`，但有效完成跑是 `TP=1`。
6. `total_training_steps=10` 不一定保证实际 10 step，数据轮次不足时还要同步调整 `total_epochs`。
7. 完成判断以日志里的 `Training Progress: 100%`、实际 step 指标和进程退出为准，`status.txt` 可能滞后。
8. 文档、代码、容器、数据路径必须先对齐；路径错了，后面所有性能结论都没有意义。
9. 不归档某次短测具体数值作为经验结论；结果每次从当前日志重新解析。

## Residual Risks

- 结论只覆盖 `tp=1`，不覆盖 `tp=2`。
- 结论只覆盖当前数据集、reward、模型和 206+13 双机环境。
- 本次为 10 step 对比，适合短测性能和偏差判断，不等价于长训稳定性结论。

## Sensitive Data Handling

未记录密码、token、私钥或认证文件。路径、机器 IP、容器名属于当前项目环境事实，保留在项目归档中。
