---
type: project
date: 2026-06-17
title: "VERL vLLM multimodal profiling logs"
domain: verl
topics: [vllm, profiling, multimodal, path_refs]
status: verified
sensitive: reviewed
related_incidents: []
extracted_knowledge: []
---

# VERL vLLM multimodal profiling logs

## Goal

Add enough opt-in profiling logs to diagnose baseline raw-image versus optimized path_refs end-to-end VERL/vLLM multimodal performance differences without changing default training behavior.

## Scope

The change was limited to the dedicated workspace `/mnt/disk2t/l30002999/verl_container_workspace` and synchronized across `192.168.0.206`, `192.168.0.59`, and `192.168.0.145`.

## Environment

- Project workspace: `/mnt/disk2t/l30002999/verl_container_workspace`
- Containers checked:
  - `192.168.0.206`: `verl_lazy_dual_baseline_206`
  - `192.168.0.59`: `verl_lazy_quad_baseline_59`
  - `192.168.0.145`: `verl_lazy_quad_baseline_145`

## Timeline Summary

- Added `VLLM_MM_PROFILE` gated logs to vLLM server input processing, Qwen2-VL image parsing, and vLLM worker multimodal extraction/materialization.
- Added `VLLM_MM_PROFILE` propagation through the existing VERL launch script Ray `runtime_env.env_vars`.
- Updated project `AGENTS.md` with the modification record.
- Synchronized files to all three target hosts and verified matching hashes.

## Key Commands

- `python3 -m py_compile vllm/vllm/v1/worker/gpu_model_runner.py vllm/vllm/v1/engine/input_processor.py vllm/vllm/model_executor/models/qwen2_vl.py`
- `bash -n scripts/run_verl_full_train_28img_ab_dedicated.sh`
- `sha256sum` on modified files across `192.168.0.206`, `192.168.0.59`, and `192.168.0.145`

## Key Files

- `vllm/vllm/v1/engine/input_processor.py`
- `vllm/vllm/model_executor/models/qwen2_vl.py`
- `vllm/vllm/v1/worker/gpu_model_runner.py`
- `scripts/run_verl_full_train_28img_ab_dedicated.sh`
- `AGENTS.md`

## Problems Encountered

- The Experience Vault `archive` command does not accept `--source`; a failed attempt was fingerprinted.
- Vault had pre-existing untracked archive files, so `archive --no-pull` was used only after reviewing local vault state with `git-review`.

## Final Solution

`VLLM_MM_PROFILE=1` now enables diagnostic logs for:

- server-side `InputProcessor.process_inputs`: prompt length, multimodal feature count, lazy feature count, preprocessing, validation/split, sampling-param handling, multimodal feature construction, and total time;
- Qwen2-VL image parser: lazy-ref serialization/tensor build and raw/dict/lazy parse timing;
- worker-side `GPUModelRunner._extract_mm_kwargs`: request/feature count, lazy materialized count, collect time, group/batch time, lazy decode/load/open/convert, processor lookup, `parse_mm_data`, HF processor lookup, `processor.apply`, validation, and total materialization time.

The switch defaults to off. The worker code passes the already-read profiling flag into inner materialization/loading helpers to avoid repeated environment-variable reads when profiling is disabled.

## Verification

- Local syntax checks passed for the three modified vLLM Python files.
- Local `bash -n` passed for the modified launcher.
- Container-level `py_compile` and `bash -n` passed on all three target hosts.
- Hashes matched across the three target hosts for all modified files.

## Residual Risks

- No training job was launched as part of this logging-only step.
- The next A/B diagnosis run must explicitly set `VLLM_MM_PROFILE=1` and keep baseline and optimized training fields aligned.
- Profiling logs add overhead and should not be used for final clean performance numbers unless both baseline and optimized runs use the same profiling setting.

## Related Incidents

- None for the code change itself.

## Extracted Knowledge

- Keep profiling switches default-off and propagate them through Ray runtime environment when vLLM workers run under VERL.
- For this project, record every code/script modification in project `AGENTS.md` before closing the task.

## Sensitive Data Handling

No credentials, full logs, raw dataset samples, or private keys were recorded.
