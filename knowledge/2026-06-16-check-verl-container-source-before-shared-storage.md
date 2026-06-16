---
type: knowledge
date: 2026-06-16
title: "Check VERL container source before shared storage"
domain: verl
topics: [container-source, shared-storage, training-workflow, workspace-isolation]
applies_to: [verl, vllm, qwen3vl, npu-container, lazy-image-transport]
confidence: verified
risk: medium
source_projects: [add-verl-lazy-image-transport]
source_incidents: []
last_verified: 2026-06-16
sensitive: false
skill_candidate: false
---

# Check VERL container source before shared storage

## Applicability

Use this rule for future VERL training, testing, debugging, or implementation
work in NPU containers.

## Trigger Signals

- The user asks to run or modify VERL training.
- The task mentions VERL, vLLM, Ray, Qwen3VL, path_refs, LazyImageRef, reward
  precision, throughput, or end-to-end training.
- A container such as `verl_lazy_dual_baseline_13` or another VERL runtime
  container is involved.

## Required Inputs

- Target container name or host.
- User-provided code path only if they explicitly want a non-container source.

## Procedure

1. Enter or inspect the target container first.
2. Check where `verl` and `vllm` are imported from:

   ```bash
   python3 - <<'PY'
   import importlib.util
   for name in ["verl", "vllm"]:
       spec = importlib.util.find_spec(name)
       print(name, None if spec is None else spec.origin)
       if spec and spec.submodule_search_locations:
           print(list(spec.submodule_search_locations))
   PY
   python3 -m pip show verl vllm
   ```

3. Prefer the container's editable source tree for framework inspection and
   patch planning, for example `/vllm-workspace/verl` and `/vllm-workspace/vllm`.
4. Do not search shared storage for framework source by default.
5. Use shared storage only for reading models, reading datasets, and storing
   intermediate artifacts or logs unless the user explicitly specifies otherwise.
6. If modifications are required, keep the implementation in a user-owned
   workspace such as `/mnt/disk2t/l30002999/` and make the container runtime
   point to that copy deliberately.

## Non-Applicable Cases

- The user explicitly names a shared-storage source tree and asks to inspect it.
- The task is only copying logs, model files, or datasets.
- The container is unavailable and the user approves using a host-side source
  copy as a fallback.

## Verification Method

- Confirm `pip show verl` and `pip show vllm` report editable project locations.
- Confirm `importlib.util.find_spec("verl")` and `find_spec("vllm")` match the
  expected container paths before relying on source code.
- Do not infer the runtime source from a shared directory path alone.

## Risk And Safety Notes

- Shared storage may contain unrelated source copies that are not the active
  runtime used by training.
- Editing shared source can affect other users or invalidate running tests.
- Container editable paths are the authoritative source for what the current
  training process imports unless launch-time `PYTHONPATH` overrides are proven.

## Source Evidence

On 2026-06-16, container `verl_lazy_dual_baseline_13` was inspected without
accessing shared storage. It reported:

- `verl` imported from `/vllm-workspace/verl/verl/__init__.py`
- `vllm` imported from `/vllm-workspace/vllm/vllm/__init__.py`
- `pip show verl`: version `0.7.1`, editable project location `/vllm-workspace/verl`
- `pip show vllm`: version `0.18.0+empty`, editable project location `/vllm-workspace/vllm`

## Promotion Notes

Promote this into a VERL/NPU training runbook if future sessions continue to
mix container runtime source and shared-storage project copies.
