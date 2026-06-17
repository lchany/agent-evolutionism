---
type: project
date: 2026-06-17
title: "PyTorch Training Precision Debugging Guide"
domain: unknown
topics: [pytorch, training-precision, msprobe, ascend-npu, nan, loss-alignment, determinism]
status: archived
sensitive: reviewed
related_incidents: []
extracted_knowledge:
  - runbooks/2026-06-17-pytorch-training-precision-debugging-guide.md
---

# PyTorch Training Precision Debugging Guide

## Goal

Archive a trusted internal guide for locating PyTorch training precision problems
on Ascend NPU, especially benchmarked migration cases where NPU training does not
align with GPU or another framework.

Source document:

- Title: PyTorch Training Precision Debugging Guide
- Version: 2025Q1-0327
- Created: 2025-03-25 16:11
- Last modified: 2025-12-23 15:18

## Scope

The guide covers training convergence and alignment issues such as:

- Loss not aligned with benchmark.
- Loss or Grad Norm overflow.
- NaN or Inf.
- Loss spikes.
- Downstream task quality regression.
- First-step or early-step loss divergence.
- Long-running training divergence after early alignment.

The primary scenario is migration with a benchmark, usually GPU-to-NPU or
framework-to-framework migration. Native NPU-only development is mentioned but is
not the main focus.

## Environment

Applicable stack:

- PyTorch training on Ascend NPU.
- PTA / torch_npu.
- CANN, driver, and related Ascend runtime packages.
- Common large-model frameworks such as ModelLink, Megatron, DeepSpeed, and
  MindSpeed+Megatron.
- msprobe / mindstudio-probe for dump, comparison, graph visualization, monitor,
  precheck, and config checking.

## Timeline Summary

The document recommends a strict order:

1. Judge whether the observed behavior violates the relevant training or operator
   precision standard.
2. Before blaming operators, compare hyperparameters, environment variables,
   third-party versions, data reading, model structure, and initialization.
3. Fix randomness and enable deterministic behavior before reproduction.
4. Reduce scale while preserving important parallel partition parameters when
   large clusters are involved.
5. Route by symptom: stable NaN/overflow, first-step loss difference, long-run
   divergence, unstable reproduction, memory stomp, determinism, hardware, framework,
   stage/model/version.
6. After bounding to an API, run single-operator verification and apply repair
   levers such as raising precision, moving to CPU, or replacing fused ops.

## Key Commands

Fix randomness and determinism:

```python
import numpy as np
import torch
import torch_npu

np.random.seed(1234)
torch.manual_seed(1234)
torch_npu.npu.manual_seed(1234)
torch.use_deterministic_algorithms(True)
```

```bash
export HCCL_DETERMINISTIC=TRUE
export INF_NAN_MODE_ENABLE=1
```

msprobe seed helper:

```python
from msprobe.pytorch import seed_all
seed_all(seed=1234, mode=True, rm_dropout=True)
```

Install msprobe:

```bash
pip install mindstudio-probe
```

or source install:

```bash
git clone https://gitcode.com/Ascend/mstt.git
export PYTHONPATH=$PYTHONPATH:$MSTT_HOME/debug/accuracy_tools/
```

Graph and overflow analysis:

```bash
msprobe -f pytorch graph -i ./compare.json -o ./output
msprobe -f pytorch graph -i ./compare.json -o ./output -oc
tensorboard --logdir output --bind_all --port <port>
```

Precision comparison:

```bash
msprobe -f pytorch compare -i ./compare.json -o ./output -s
```

API precheck:

```bash
msprobe -f pytorch run_ut -api_info ./dump_path/step{step}/rank{rank}/dump.json
msprobe -f pytorch api_precision_compare -npu /path/to/npu -gpu /path/to/gpu -o /path/to/output
```

## Key Files

The archived document is user-provided text in this conversation, not a local source
file. The runnable runbook extracted from it is:

- `runbooks/2026-06-17-pytorch-training-precision-debugging-guide.md`

Common msprobe config files referenced by the guide:

- `config.json` for precision dump.
- `compare.json` for graph or compare.
- `monitor_config.json` for training state monitoring.

## Problems Encountered

The guide emphasizes that many reported training precision issues are not operator
bugs. Frequent non-operator causes include:

- Training hyperparameters or environment variables differ from the benchmark.
- ModelLink, Megatron, DeepSpeed, PyTorch, or PTA versions differ.
- Dataset reading or preprocessing differs.
- Model structure differs.
- Weight initialization or loaded checkpoint differs.
- Randomness is not fixed.
- Dropout or shuffle remains enabled during reproduction.
- Communication or compute is nondeterministic.

## Final Solution

The extracted solution is a reusable debugging workflow:

- Start with standards and checklist.
- Fix reproducibility.
- Reduce scale if needed.
- Route by symptom.
- Use msprobe dump, graph, compare, monitor, precheck, config checking, and manual
  hooks to bound the first divergent location.
- Confirm suspicious APIs with single-operator verification.
- Repair by raising precision, moving the API to CPU, replacing fused ops with small
  ops, fixing framework parameters, fixing data/model/config mismatches, or escalating
  hardware/operator issues with evidence.

## Verification

Verification is not one command; it is a closed loop:

- Reproduce the original symptom under fixed randomness.
- Identify the first divergent step, module, API, tensor, or rank.
- Apply one change at a time.
- Re-run the same benchmark condition.
- Confirm that loss, Grad Norm, NaN/Inf occurrence, or downstream metric now meets
  the relevant training precision standard.
- For suspected API issues, compare NPU and GPU outputs against CPU on the same NPU
  input and verify whether the NPU-to-CPU distance is worse than GPU-to-CPU.

## Residual Risks

- The guide is broad; individual projects still need exact tolerance standards and
  benchmark definitions.
- Dumping can perturb timing and hide memory stomp issues.
- Deterministic settings can reduce performance and should not be assumed as final
  production configuration.
- CPU fallback and fp32 fallback are diagnosis or mitigation levers; they may not be
  acceptable final performance solutions.
- Hardware issues in large clusters require careful grouping and evidence collection
  before removing nodes from the pool.

## Related Incidents

None recorded from this document as a single incident. It includes multiple example
cases, but they are used as reusable signals in the runbook rather than archived as
separate incidents.

## Extracted Knowledge

- `runbooks/2026-06-17-pytorch-training-precision-debugging-guide.md`

## Sensitive Data Handling

The archived summary stores no credentials, private keys, tokens, customer names,
hostnames, IPs, raw logs, or private datasets. Author and department metadata from
the provided document was not repeated in full because it is not needed for reuse.
