---
type: runbook
date: 2026-06-17
title: "PyTorch Training Precision Debugging Guide"
domain: unknown
topics: [pytorch, training-precision, msprobe, ascend-npu, nan, loss-alignment, determinism]
confidence: mature
risk: medium
source_knowledge:
  - projects/2026-06-17-pytorch-training-precision-debugging-guide.md
source_incidents: []
sensitive: reviewed
skill_candidate: false
---

# PyTorch Training Precision Debugging Guide

## When To Use

Use this runbook when PyTorch training on Ascend NPU has a precision or convergence
problem, especially in a benchmarked migration where NPU behavior must align with
GPU or another framework.

Typical symptoms:

- Loss does not align with benchmark.
- Loss, Grad Norm, activations, or gradients become Inf or NaN.
- Loss has spikes or later-stage divergence.
- First step or first few steps differ from benchmark by more than the accepted
  tolerance.
- Early training aligns, but long-running training diverges.
- Downstream task quality regresses although training loss appears close.
- Repeated runs are inconsistent after randomness should have been fixed.

## Required Inputs

- Benchmark definition: GPU, another NPU framework, previous version, or accepted
  golden run.
- Precision acceptance standard and tolerance for the scenario.
- Full NPU and benchmark launch commands.
- Training logs, environment variables, and hyperparameters from both sides.
- Framework and package versions: PyTorch, torch_npu/PTA, CANN, driver, ModelLink,
  Megatron, DeepSpeed, MindSpeed, and related libraries.
- Dataset path, sampling/shuffle configuration, preprocessing code, and first batch
  evidence.
- Model structure printout or code hash from both sides.
- Initialization method, random seed, and checkpoint path.
- Parallel strategy: DP, TP, PP, EP, CP, SP, ZeRO/offload, overlap settings, bucket
  sizes, and optimizer configuration.
- Symptom details: first bad step, rank, module, tensor, loss/Grad Norm trend, and
  whether stream sync or dumping changes the symptom.

## Procedure

### 1. Confirm It Is A Precision Problem

Do not start with operator debugging. First confirm that the observed behavior
violates the project training precision standard or operator precision standard.
Small numerical differences between CPU/GPU/NPU implementations can be acceptable
if final convergence and metrics meet the standard.

Classify the issue:

- Model precision issue: data, hyperparameters, model structure, framework usage,
  initialization, or evaluation mismatch.
- Numerical precision issue: finite precision, compute order, communication order,
  operator implementation, or fused expression differences.

### 2. Run The Pre-Operator Checklist

Compare NPU and benchmark for:

- Training hyperparameters and environment variables.
- Third-party versions and branches, including ModelLink, Megatron, DeepSpeed,
  PyTorch, and PTA/torch_npu.
- Data reading and preprocessing; print actual tokens or sample tensors from both
  sides.
- Model structure; print and diff both structures.
- Weight initialization; use the same checkpoint or same initialization seed.
- CANN, driver, and PTA versions; prefer current commercial releases.

Many precision issues are resolved at this stage.

### 3. Make Reproduction Deterministic

Fix all known randomness:

```python
import numpy as np
import torch
import torch_npu

np.random.seed(1234)
torch.manual_seed(1234)
torch_npu.npu.manual_seed(1234)
torch.use_deterministic_algorithms(True)
```

Disable randomness in the training path:

- Disable Dropout for reproduction.
- Set dataloader `shuffle=False`.
- Keep dataset order stable.

Enable communication determinism:

```bash
export HCCL_DETERMINISTIC=TRUE
```

Or use msprobe's helper:

```python
from msprobe.pytorch import seed_all
seed_all(seed=1234, mode=True, rm_dropout=True)
```

For Inf/NaN debugging, enable non-saturation mode:

```bash
export INF_NAN_MODE_ENABLE=1
```

### 4. Reduce Scale Without Changing The Bug

For large clusters, shrink the reproducer before deep debugging. Prefer preserving
parallel partition parameters that may affect the bug, such as TP, PP, CP, SP, and
EP. Reduce global batch size, micro-batch count, or model layer count first.

If the issue disappears after reduction, record exactly which dimension changed and
route to framework, communication, or hardware analysis instead of assuming the bug
is gone.

### 5. Route Stable Reproducers By Symptom

NaN or overflow:

1. Dump forward/backward inputs and outputs around the overflow step.
2. If adding dump or stream synchronization makes the issue disappear, suspect memory
   stomp.
3. If it still reproduces, use graph overflow analysis to locate the first abnormal
   tensor.
4. If abnormal tensor is a weight, suspect the previous backward gradient.
5. If abnormal tensor is an input, suspect an uncaptured special operator or earlier
   path.
6. If abnormal tensor is an output, focus on that operator.
7. For Megatron/MindSpeed-style models, temporarily disable overlap parameters and
   Flash Attention branches to test high-risk fused paths.

First-step loss difference:

1. Dump the first differing step.
2. Compare NPU and benchmark dumps.
3. Locate the first API/module where input is close but output diverges.
4. If no suspicious API appears, run msprobe API precheck.

Long-running loss divergence:

1. If the first divergent step is known, dump that step and compare.
2. If not known, use training monitor to track activation, weight gradient, optimizer
   state, and communication statistics.
3. Check optimizer behavior: Adam versus SGD, fused Adam versus small ops, optimizer
   disabled, or learning rate set to zero.
4. Check matmul stagger strategy and framework overlap settings.

### 6. Route Unstable Reproducers

Memory stomp:

- Strong signal: stream sync or precision dump makes NaN/overflow disappear.
- Try async dump.
- Inspect tensor-difference patterns for regular overwrite features.
- Use profiling plus MindStudio Insight to inspect compute parallelism.
- Add pointer address printing around suspicious tensors.
- Use operator competition or stress tools when available.

Operator determinism:

1. Run two repeated deterministic trainings.
2. Dump in md5 summary mode.
3. Find the first operator where inputs match but outputs differ.
4. For special random operators such as `torch.randn`, generate on CPU and transfer
   to device.
5. For unsupported deterministic operators, use CPU fallback or an alternative small-op
   implementation while escalating to operator owners.

Hardware:

- For large clusters, split nodes into groups and run identical model stress jobs.
- If one operator is suspicious but single-op reproduction fails, run grouped
  single-operator stress.
- Use `ascend-dmi` AICore stress for repeated hardware pressure tests.
- Treat hardware conclusions as evidence-based; do not remove nodes without logs.

Framework:

- Megatron: disable overlap parameters; simplify TP/PP/SP/CP/EP strategies.
- DeepSpeed: disable overlap parameters; inspect `bucket_size`; switch among
  ZeRO-1/2/3 and offload strategies.

Training stage, model stage, and version:

- Set learning rate to zero or disable optimizer to separate forward/backward from
  optimizer update.
- Replace optimizer to isolate optimizer-specific issues.
- Reduce layers, bisect modules, disable attention or other major blocks, move device,
  or freeze gradients by bisection.
- Use version bisection for suspected regression introductions.

### 7. Bound To API And Verify The Operator

After a suspicious API is identified:

1. Use the precision dump tool to collect concrete NPU tensor values for the API.
2. Generate a single-operator validation script from the captured API.
3. Run the same NPU input through the single-op script on NPU and GPU.
4. Compare each result with CPU using Euclidean distance.
5. If NPU-to-CPU distance is larger than GPU-to-CPU distance beyond standard, treat
   the API as suspicious.

### 8. Apply The Three Repair Levers

Use these to test whether the suspicious API affects full training:

- Raise precision, such as fp16/bf16 to fp32.
- Move the API to CPU.
- Replace a fused operator with equivalent small operators.

Keep the final fix separate from diagnostic mitigations. CPU fallback may prove root
cause but still be unacceptable for production performance.

### 9. Use msprobe Tools

Install:

```bash
pip install mindstudio-probe
```

or:

```bash
git clone https://gitcode.com/Ascend/mstt.git
export PYTHONPATH=$PYTHONPATH:$MSTT_HOME/debug/accuracy_tools/
```

Precision dump minimal pattern:

```python
from msprobe.pytorch import PrecisionDebugger, seed_all

seed_all(mode=True)
debugger = PrecisionDebugger(config_path="./config.json", model=model)

for step in range(total_steps):
    debugger.start()
    output = model(data)
    loss.backward()
    debugger.stop()
    debugger.step()
```

Graph and overflow analysis:

```bash
pip3 install tb-graph-ascend
msprobe -f pytorch graph -i ./compare.json -o ./output
msprobe -f pytorch graph -i ./compare.json -o ./output -oc
tensorboard --logdir output --bind_all --port <port>
```

Precision comparison:

```bash
msprobe -f pytorch compare -i ./compare.json -o ./output -s
```

Training monitor pattern:

```python
from msprobe.pytorch import TrainerMon, seed_all

seed_all(mode=True)
monitor = TrainerMon(
    config_file_path="./monitor_config.json",
    process_group=mpu.get_pipeline_model_parallel_group(),
    params_have_main_grad=True,
)
monitor.set_monitor(model[0], grad_acc_steps=..., optimizer=optimizer, ...)
```

API precheck:

```bash
msprobe -f pytorch run_ut -api_info ./dump_path/step{step}/rank{rank}/dump.json
msprobe -f pytorch api_precision_compare -npu /path/to/npu/result -gpu /path/to/gpu/result -o /path/to/output
```

Config checking instrumentation:

```python
from msprobe.pytorch.config_checking.checkers.random_checker import apply_patches
apply_patches()

from msprobe.pytorch.config_checking.config_checker import ConfigChecker
ConfigChecker(model, shell_path, output_zip_path)
```

Config comparison:

```bash
msprobe -f pytorch config_checking -c bench_zip_path cmp_zip_path -o output_path
```

## Validation

The debugging result is valid only when:

- The first divergence is bounded to a concrete category: config/data/model,
  framework, API/operator, communication, determinism, memory stomp, hardware, or
  version regression.
- A single change removes or explains the symptom under the same reproduction setup.
- The corrected run meets the relevant precision standard.
- For operator claims, single-op validation compares NPU/GPU against CPU on the same
  captured input.
- For memory stomp claims, evidence includes disappearing symptoms under sync/dump,
  async dump or pointer evidence, or profiling evidence.
- For hardware claims, grouped stress evidence identifies the bad node/card pattern.

## Failure Handling

If dump changes the symptom:

- Stop treating the dump run as faithful reproduction.
- Switch to async dump, stream-sync experiments, pointer logging, and profiling.

If first-step comparison finds no suspicious operator:

- Recheck checklist items.
- Run API precheck.
- Confirm benchmark and NPU inputs are byte/tensor equivalent.

If repeated deterministic runs still differ:

- Use md5 summary mode.
- Find first input-same/output-different API.
- Check random operators and unsupported deterministic operators.

If large-cluster behavior cannot be reproduced at small scale:

- Preserve partition parameters where possible.
- Run grouped stress tests by node/card.
- Collect hardware and communication evidence before changing model code.

If a fused op is suspicious:

- Disable the fused branch or replace with small ops.
- Confirm whether parameters such as attention masks follow the fused operator's
  specification.

## Non-Applicable Cases

- The task is pure inference accuracy without a training loop.
- No benchmark, tolerance, or acceptance standard exists yet; define those first.
- The only issue is performance with aligned metrics; use performance profiling
  workflows instead.
- The reproduction cannot be made deterministic enough to compare, and the user is
  asking for final root cause rather than a staged investigation.

## Related Knowledge

- `projects/2026-06-17-pytorch-training-precision-debugging-guide.md`
- `runbooks/2026-06-16-e2e-performance-precision-comparison-workflow.md`

Example signals preserved from the source guide:

- Config mismatch can look like precision drift, such as FSDP on one side and DDP on
  the benchmark side.
- Data preprocessing mismatch can cause loss misalignment even with correct kernels.
- Model structure mismatch can hide in small residual or layernorm placement changes.
- Flash Attention misuse, such as incorrect `attention_mask`, can cause overflow.
- GELU mismatch can show as small input difference but large output difference.
- Embedding gradient clipping can fix bf16 long-run divergence when Grad Norm spikes
  concentrate near embeddings.
- FSDP multi-stream layernorm paths can trigger memory stomp if record semantics are
  missing.
- Unsupported deterministic operators may need small-op or CPU replacement.
- Large clusters may need grouped hardware stress to isolate bad nodes.

## Skill Promotion Notes

Distillation marked this as a possible skill candidate because it is a class-level
debugging workflow. Keep it as a runbook until at least one local investigation uses
it end to end and records concrete commands, configs, and outcome quality.
