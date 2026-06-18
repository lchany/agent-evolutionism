---
type: runbook
date: 2026-06-17
title: "VeRL Ray worker deterministic seed_all issue"
domain: npu-ascend
topics: [verl, ray, deterministic, msprobe, torch-npu, fusion-attention, plog]
confidence: mature
risk: medium
source_knowledge:
  - knowledge/2026-06-17-verl-ray-worker-deterministic-seed-all-issue.md
source_incidents: []
sensitive: reviewed
skill_candidate: false
---

# VeRL Ray worker deterministic seed_all issue

## When To Use

Use this runbook when VeRL/Ray training on Ascend NPU cannot be made deterministic after calling `msprobe.pytorch.seed_all(mode=True)`, or when reward/grad_norm differs across repeated runs and the actual training work may happen in Ray workers.

## Required Inputs

- Current versions of VeRL, Ray, CANN, torch_npu, msprobe, and tensordict.
- The exact location where `seed_all(mode=True)` is called.
- msprobe dump comparison for at least two runs.
- Tensor dumps for the first mismatching operator if single-op isolation is needed.
- Ascend plog Info logs from the actual training processes.

## Procedure

1. Align known-problem versions first.
   - For this case, upgrade `tensordict` to `0.10.0`.
   - Align CANN to the required 630 patch version.

2. Enable deterministic mode in the currently suspected entry point.

   ```python
   from msprobe.pytorch import seed_all

   seed_all(mode=True)
   ```

3. Reduce the model if needed, then collect msprobe dump data from two runs and compare operator input/output checksums.

4. Identify the first mismatch.
   - If forward is fully stable and the first mismatch is in backward, record the backward input and output tensors.
   - In this case, the first mismatch was the last-layer Fusion Attention backward output while its backward input was identical.

5. Build a single-op reproduction for the first mismatching operator.
   - Load the captured forward inputs and backward grad input.
   - Run the operator forward and backward multiple times.
   - Clear gradients after each backward.

   ```python
   query.grad.zero_()
   key.grad.zero_()
   value.grad.zero_()
   ```

6. If the single-op result is deterministic, verify whether the full network enabled deterministic mode in the actual process.

7. Enable verbose plog before rerunning the focused case.

   ```bash
   export ASCEND_GLOBAL_LOG_LEVEL=1
   export ASCEND_HOST_LOG_FILE_NUM=1000
   ```

8. Check FA TilingKey when Fusion Attention is involved.

   ```bash
   grep -rn -i "FAGTiling" /root/ascend/log/debug/plog
   ```

   For the observed FA deterministic path, the checks were `sameAB` and a TilingKey whose last 12 digits indicate deterministic mode. Example: `10000001101100002434`.

9. Check ACL runtime deterministic settings.

   ```bash
   grep -rn -i "AclrtSetSysParamOpt" /root/ascend/log/debug/plog
   grep -rn -i "AclrtCtxSetSysParamOpt" /root/ascend/log/debug/plog
   ```

   Treat `opt=0,value=1` as deterministic enabled. Treat `value=0` or missing records as not enabled, after ignoring initialization-only `value=0` records.

10. For Ray/VeRL, move or duplicate the deterministic setup into the worker path that actually executes training forward/backward.

    ```python
    from msprobe.pytorch import seed_all

    seed_all(mode=True)
    ```

## Validation

- The full-network plog shows deterministic mode enabled in worker processes.
- Fusion Attention TilingKey enters the deterministic template when FA is the target operator.
- Repeated training steps produce identical grad results. The reference case verified 20 identical steps.

## Failure Handling

- If reward spikes disappear after `tensordict==0.10.0` but determinism still fails, continue with deterministic-mode validation instead of stopping at version alignment.
- If single-op FA is non-deterministic, treat it as an operator/template issue and collect TilingKey, shape, layout, sparse mode, sequence length, and CANN/torch_npu versions.
- If single-op FA is deterministic but full-network FA is not, prioritize framework-side propagation of deterministic settings.
- If plog is missing early records, increase `ASCEND_HOST_LOG_FILE_NUM` and rerun the shortest reproducer.

## Non-Applicable Cases

- Training does not use Ray or another worker-isolated execution model.
- Determinism is already verified inside the process that executes forward/backward.
- The first mismatch is caused by nondeterministic data loading, sampling, checkpoint restore order, communication topology, or dropout settings outside the NPU operator path.

## Related Knowledge

- `knowledge/2026-06-17-verl-ray-worker-deterministic-seed-all-issue.md`

## Skill Promotion Notes

This can stay as a runbook unless multiple future cases require an automated skill for Ray/VeRL deterministic setup validation.
## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: general-knowledge -> knowledge/
- Distill classification: runbook-candidate -> runbooks/
- Suggested domains: npu-ascend, mindspeed, verl
