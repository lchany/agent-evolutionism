---
type: project
date: 2026-06-16
title: "VERL dual-node lazy path_refs performance precision comparison"
domain: verl
topics: [verl, vllm, qwen3vl, lazy-image-transport, dual-node, performance, precision]
status: verified
sensitive: reviewed
related_incidents: [incidents/2026-06-16-verl-jpeg-q90-reward-drift-root-cause.md]
extracted_knowledge:
  - knowledge/2026-06-16-use-dedicated-workspace-for-verl-lazy-transport-changes.md
  - knowledge/2026-06-16-check-verl-container-source-before-shared-storage.md
---

# VERL dual-node lazy path_refs performance precision comparison

## Goal

Audit the VERL/vLLM lazy path reference implementation, then run a complete
two-node end-to-end VERL comparison between the baseline raw image path and the
optimized worker-side path reference path. Preserve complete logs and produce a
performance plus precision report.

## Scope

- Baseline mode: `raw_rgb`.
- Optimized mode: `path_refs` using worker-side `LazyImageRef` materialization.
- Dataset: Geometry3K 28-image copy under `/mnt/disk2t/l30002999/dataset/`.
- Test length: 15 training steps.
- Main performance metrics: `timing_s/step` and `timing_s/gen`.
- Precision metric: `critic/rewards/mean`, compared by absolute difference.
- Supporting metric only: `perf/throughput`, because token denominator differs
  between raw visual tokens and path reference prompts.

## Environment

- Head node: `192.168.0.206`, container `verl_lazy_dual_baseline_206`.
- Worker node: `192.168.0.13`, container `verl_lazy_dual_baseline_13`.
- Ray address: `192.168.0.206:6389`.
- Image: `verl-0.7.1_vllm-0.18.0_cann-8.5.1_baseline:migrated_from_59_20260612`.
- Dedicated workspace:
  `/mnt/disk2t/l30002999/verl_container_workspace`.
- Full local report artifacts:
  `/mnt/disk2t/l30002999/verl_lazy_transport_runs/dual_node_report_artifacts_20260616_190247`.

## Timeline Summary

- Verified Ray had two active nodes and 32 idle NPUs before launching optimized
  training.
- Audited dedicated workspace code and confirmed checksums matched between local
  host and the 206 container workspace.
- Confirmed baseline 15-step run had completed with `EXIT_CODE=0`.
- Launched optimized run in the background with
  `VLLM_MM_LAZY_VALIDATE_GRID=0`.
- Optimized run completed 15 steps with `EXIT_CODE=0`.
- Copied complete baseline and optimized run directories back to the local
  report artifact directory.
- Uploaded a compressed package of training logs and report artifacts to the
  user-provided external host path, without recording credentials in the vault.

## Key Commands

```bash
/mnt/disk2t/l30002999/verl_container_workspace/scripts/launch_verl_train_background.sh \
  optimized optimized_path_refs_28img_2node_steps15_prompt6144_20260616_185252 \
  TOTAL_STEPS=15 VLLM_MM_LAZY_VALIDATE_GRID=0
```

The baseline and optimized launch commands are preserved in each run's
`command.sh`.

## Key Files

- Baseline local training log:
  `/mnt/disk2t/l30002999/verl_lazy_transport_runs/dual_node_report_artifacts_20260616_190247/baseline_raw_rgb_28img_2node_steps15_prompt6144_20260616_183418/train.log`
- Optimized local training log:
  `/mnt/disk2t/l30002999/verl_lazy_transport_runs/dual_node_report_artifacts_20260616_190247/optimized_path_refs_28img_2node_steps15_prompt6144_20260616_185252/train.log`
- Markdown report:
  `/mnt/disk2t/l30002999/verl_lazy_transport_runs/dual_node_report_artifacts_20260616_190247/dual_node_comparison_report.md`
- Metrics JSON:
  `/mnt/disk2t/l30002999/verl_lazy_transport_runs/dual_node_report_artifacts_20260616_190247/dual_node_metrics_summary.json`
- Step CSV:
  `/mnt/disk2t/l30002999/verl_lazy_transport_runs/dual_node_report_artifacts_20260616_190247/dual_node_step_metrics.csv`

## Problems Encountered

- A monitoring command failed because nested shell quoting broke a `grep -E`
  expression. It did not affect training. The subsequent monitoring command used
  `bash -s` to avoid nested quoting.
- Both successful runs emitted shutdown-time `multiprocessing.resource_tracker`
  `/psm_*` warnings. The optimized log also showed a vLLM EngineCore shutdown
  message after the final step. These were treated as non-fatal because both
  runs completed all 15 steps and wrote `EXIT_CODE=0`.

## Final Solution

The implementation and test harness matched the intended design:

- Lazy path references are built in VERL and decoded to vLLM lazy image refs.
- vLLM worker-side image materialization reads local `/mnt` image files.
- Worker-side grid/token validation is implemented behind
  `VLLM_MM_LAZY_VALIDATE_GRID`; performance testing used `0`.
- Baseline and optimized wrappers are separate scripts.
- Training fields were aligned except for expected data, transport, env, and
  output-directory differences.

## Verification

Both runs completed 15 steps with `EXIT_CODE=0`.

Main averages over steps 2-15:

| Metric | Baseline | Optimized | Result |
| --- | ---: | ---: | --- |
| `timing_s/step` | 23.417699 | 14.287020 | 38.99% lower |
| `timing_s/gen` | 9.036719 | 6.665983 | 26.23% lower |
| `critic/rewards/mean` | 0.000000 | 0.000000 | abs diff 0.000000 |

Step 15:

| Metric | Baseline | Optimized |
| --- | ---: | ---: |
| `timing_s/step` | 22.315574 | 13.662911 |
| `timing_s/gen` | 9.074467 | 6.665370 |
| `critic/rewards/mean` | 0.000000 | 0.000000 |

The precision gate passed for both `<= 0.03` and `<= 0.05`.

## Residual Risks

- `perf/throughput` is not comparable as a main metric because path reference
  prompts have far fewer counted tokens than raw image prompts.
- The shutdown-time `/psm_*` warnings should be watched in longer runs, even
  though they were non-fatal here.
- Reward equality over a 15-step sampled training run is useful evidence for
  this comparison, but future broader validation should include more samples or
  initial validation if available.

## Related Incidents

- `incidents/2026-06-16-verl-jpeg-q90-reward-drift-root-cause.md`

## Extracted Knowledge

- `knowledge/2026-06-16-use-dedicated-workspace-for-verl-lazy-transport-changes.md`
- `knowledge/2026-06-16-check-verl-container-source-before-shared-storage.md`

## Sensitive Data Handling

No passwords, API keys, private keys, raw credentials, or full training logs are
stored in this vault record. The external upload target is described only as a
user-provided destination; credentials are intentionally omitted.
