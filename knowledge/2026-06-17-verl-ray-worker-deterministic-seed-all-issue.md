---
type: knowledge
date: 2026-06-17
title: "VeRL Ray worker deterministic seed_all issue"
domain: npu-ascend
topics: [verl, ray, deterministic, msprobe, torch-npu, fusion-attention, plog]
applies_to: [verl, ray-worker-training, ascend-npu, torch-npu, msprobe]
confidence: verified
risk: medium
source_projects:
  - projects/2026-06-17-verl-ray-worker-deterministic-seed-all-issue.md
source_incidents: []
last_verified: 2026-06-17
sensitive: reviewed
skill_candidate: false
---

# VeRL Ray worker deterministic seed_all issue

## Applicability

适用于 VeRL、Ray 或类似 driver/worker 隔离架构下的 Ascend NPU 训练确定性问题，尤其是只在主函数入口调用 `seed_all(mode=True)` 后，整网训练结果仍无法固定的场景。

## Trigger Signals

- 相同代码和环境下，不同机器或多次训练 reward/grad_norm 表现差异明显。
- 开启确定性后，整网训练结果仍无法固定。
- msprobe dump 显示前向一致，某个反向算子首次不一致。
- 单算子复现可以固定，但整网同一算子仍不固定。
- plog 中 ACL runtime 确定性开关未出现 `value=1`，或整网 FA 未进入确定性 TilingKey。

## Required Inputs

- 两次训练或两次运行的 msprobe dump 对比结果。
- 首个不一致算子的输入、输出和反向梯度 tensor。
- Ascend plog Info 日志。
- 训练框架执行拓扑，特别是 driver/main 与 worker 的职责边界。

## Procedure

1. 先做版本对齐，排除已知组件问题。例如本案例中 `tensordict==0.10.0` 后 reward 尖刺消失，CANN 需对齐到 630 补丁版本。
2. 在整网中开启确定性后，用 msprobe dump 对比两次运行的算子输入输出，定位首次不一致算子。
3. 对首次不一致算子做单算子确定性复现。FA 场景可抽取 Q/K/V、attention mask、forward output、backward grad input，并在每次 backward 后清零 `query.grad`、`key.grad`、`value.grad`。
4. 如果单算子固定但整网不固定，检查整网是否真正开启确定性。
5. 通过 `FAGTiling` TilingKey 判断 FA 是否进入确定性模板。
6. 通过 `AclrtSetSysParamOpt` 和 `AclrtCtxSetSysParamOpt` 判断 ACL runtime 确定性开关是否在训练进程中生效。
7. 对 Ray/VeRL 场景，确认 `seed_all(mode=True)` 是否在实际执行前向/反向的 worker 内调用，而不是只在 driver/main 入口调用。

## Non-Applicable Cases

- 不使用 Ray 或 worker 隔离模型，且训练前反向确实在主进程执行。
- 不一致来自输入数据、dropout、数据并行采样、checkpoint 恢复或通信顺序等其他未固定因素。
- 算子单测和整网都未进入确定性模板，此时可能是算子模板覆盖或 shape 条件问题，而不是 Ray worker 传递问题。

## Verification Method

- plog 中 `AclrtSetSysParamOpt` 或有效的 `AclrtCtxSetSysParamOpt` 记录应出现 `opt=0,value=1`。
- FA 场景中，`FAGTiling` 应显示进入确定性模板；示例 TilingKey 为 `10000001101100002434`，判断要结合当前版本规则。
- 修复后重复训练若干 step，grad 结果应逐 step 一致。本案例验证为 20 step grad 完全一致。

## Risk And Safety Notes

- 开启 plog Info 前建议设置 `ASCEND_HOST_LOG_FILE_NUM=1000`，否则默认每进程 10 个文件容易覆盖关键日志。
- `AclrtCtxSetSysParamOpt` 初始化时可能打印默认 `value=0`，需要剔除初始化记录后判断。
- 不要归档原始 tensor dump、完整客户日志或机器敏感信息。

## Source Evidence

- 版本对齐后 reward 尖刺消失，但确定性仍无法固定。
- msprobe dump 定位到最后一层 FA 反向首次不一致。
- FA 单算子多次运行完全一致，且 TilingKey 进入确定性模板。
- 整网 plog 显示确定性计算未生效。
- 在 Ray worker 内补充 `seed_all(mode=True)` 后，20 step grad 完全一致。

## Promotion Notes

可作为 Ray/VeRL 训练确定性排查 runbook 的知识来源。若后续多次出现“driver 设置未传递到 worker”的同类问题，可提升为更通用的 Ray worker 环境隔离知识卡。
## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: general-knowledge -> knowledge/
- Distill classification: runbook-candidate -> runbooks/
- Suggested domains: npu-ascend, mindspeed, verl
