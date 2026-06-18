---
type: project
date: 2026-06-17
title: "VeRL Ray worker deterministic seed_all issue"
domain: npu-ascend
topics: [verl, ray, deterministic, msprobe, torch-npu, fusion-attention, grpo, megatron]
status: draft
sensitive: reviewed
related_incidents: []
extracted_knowledge:
  - knowledge/2026-06-17-verl-ray-worker-deterministic-seed-all-issue.md
---

# VeRL Ray worker deterministic seed_all issue

## Goal

归档一次客户现场 VeRL + GRPO + Megatron 训练中“随机性固定不住”的定位闭环，明确 Ray worker 内未开启确定性计算是根因，并沉淀后续排查方法。

## Scope

Qwen2.5-72B 训练场景。现象包括 A3 与 A2 reward 表现差异明显、A3 训练中 reward 尖刺频繁出现，以及部分 A3 机器 grad_norm 频繁尖刺。

## Environment

已知涉及组件：

- VeRL 分布式强化学习训练框架
- Ray worker 执行训练前向和反向
- GRPO 算法
- Megatron 训练后端
- Ascend NPU A2/A3
- CANN 630 补丁版本
- tensordict 0.10.0
- `msprobe.pytorch.seed_all(mode=True)`
- `torch_npu.npu_fusion_attention`

## Timeline Summary

1. 先做版本对齐，确认当前版本存在 tensordict 和 CANN 已知问题。
2. 升级 `tensordict==0.10.0` 后，reward 尖刺消失，但开启确定性后多次实验仍无法固定结果。
3. 在主函数入口加入 `seed_all(mode=True)`，通过减层到 4 层复现不确定性。
4. 使用 msprobe dump 对比两次整网算子输入输出 MD5，发现前向完全固定，最后一层 Fusion Attention 反向首次出现不一致。
5. 抽取最后一层 FA 输入、输出和 backward grad tensor 做单算子确定性测试，FA 单算子多次运行完全一致。
6. 通过 plog 中 `FAGTiling` 的 TilingKey 确认单算子进入确定性模板。
7. 继续检查整网 FA TilingKey 和 ACL runtime 确定性开关日志，发现整网确定性计算没有生效。
8. 结合 Ray 环境隔离机制确认根因：只在 driver/main 入口调用 `seed_all`，没有覆盖实际执行训练前反向的 Ray worker。
9. 在 worker 内补充 `seed_all(mode=True)` 后，训练 20 step 的 grad 结果完全一致。

## Key Commands

- 查看 FA TilingKey：
  `grep -rn -i "FAGTiling" /root/ascend/log/debug/plog`
- 查看 ACL runtime 全局确定性开关：
  `grep -rn -i "AclrtSetSysParamOpt" /root/ascend/log/debug/plog`
- 查看 ACL runtime context 确定性开关：
  `grep -rn -i "AclrtCtxSetSysParamOpt" /root/ascend/log/debug/plog`

## Key Files

无本地文件路径。原始材料来自用户提供的 JD 文本。msprobe dump 参考路径：`debug/accuracy_tools/msprobe/docs/10.accuracy_compare_PyTorch.md`。

## Problems Encountered

- reward 或 grad_norm 尖刺最初可能由版本问题触发，不能直接等同于确定性问题。
- 单算子 FA 能固定，但整网 FA 不能固定，说明需要区分算子模板问题与框架侧确定性开关未传递问题。
- Ray driver 与 worker 之间存在环境变量及 PyTorch 全局变量隔离，只在主入口调用 `seed_all` 不足以覆盖训练实际执行进程。
- plog 默认每个进程只保留 10 个文件，长训练中日志可能被覆盖。

## Final Solution

在实际执行训练前向和反向的 Ray worker 初始化或执行入口中加入：

```python
from msprobe.pytorch import seed_all

seed_all(mode=True)
```

不要只在 driver/main 入口调用该函数。VeRL/Ray 场景下，确定性开关必须在 worker 内生效。

## Verification

- 升级 `tensordict==0.10.0` 后，reward 尖刺消失。
- 单算子 FA 多次运行输出和反向 grad 完全一致。
- 单算子 plog 中 `FAGTiling` TilingKey 进入确定性模板。
- 整网补齐 worker 内 `seed_all(mode=True)` 后，20 step 的 grad 结果完全一致。

## Residual Risks

- 该结论依赖当前 Ray/VeRL 执行模型；如果训练执行入口迁移，需要重新确认 `seed_all` 是否运行在真实 worker 进程。
- FA 确定性模板条件与 CANN/torch_npu 版本有关，后续版本需要重新用 TilingKey 和 ACL runtime plog 验证。
- `AclrtCtxSetSysParamOpt` 初始化阶段可能先打印 `value=0`，判读时需要剔除初始化记录。

## Related Incidents

- 可关联未来 Ray worker 未继承 driver 环境变量、确定性设置或 PyTorch 全局变量的事件。

## Extracted Knowledge

- `knowledge/2026-06-17-verl-ray-worker-deterministic-seed-all-issue.md`
- `runbooks/2026-06-17-verl-ray-worker-deterministic-seed-all-issue.md`

## Sensitive Data Handling

未归档客户图片、完整日志、原始 tensor dump、机器标识、账号或凭据。仅保留可复用的技术现象、判断命令、根因和验证结论。
## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: general-knowledge -> knowledge/
- Distill classification: runbook-candidate -> runbooks/
- Suggested domains: npu-ascend, mindspeed, verl
