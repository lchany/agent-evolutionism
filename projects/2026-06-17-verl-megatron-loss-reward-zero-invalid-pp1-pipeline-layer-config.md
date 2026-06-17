---
type: project
date: 2026-06-17
title: "VERL Megatron loss and reward zero from invalid PP1 pipeline layer config"
domain: unknown
topics: [verl, megatron, dapo, sglang, mindspeed, checkpoint, pipeline-parallel, loss-zero, reward-zero]
status: archived
sensitive: reviewed
related_incidents: []
extracted_knowledge: []
---

# VERL Megatron loss and reward zero from invalid PP1 pipeline layer config

## Goal

Archive a trusted BOSS case where a VERL + Megatron + DAPO + SGLang adaptation
showed training `loss` and `reward` as 0, and the closed-loop root cause was an
invalid Megatron pipeline-stage layer configuration under `pp=1`.

Source note:

- Title: BOSS loss and reward are 0
- Created: 2026-02-26 15:14
- Last modified: 2026-02-26 15:18
- Status: closed loop

## Scope

In scope:

- Customer self-developed `nanbeige3b` dense model.
- VERL + Megatron + DAPO + SGLang adaptation.
- Checkpoint shard validation before saving weights.
- TP4, PP1, single-machine 16-card setup.
- Misconfiguration of `num_layers_in_first_pipeline_stage` and
  `num_layers_in_last_pipeline_stage`.

Out of scope:

- MoE-specific grouped linear offset fixes from another case.
- General reward function correctness.
- General environment upgrade or package compatibility.

## Environment

Recorded environment:

- Python: 3.10.18
- CANN: 8.3.rc1
- VERL: 0.7.0
- SGLang: 0.5.7
- Megatron: 0.12.1
- MindSpeed: 2.3.0

Parallel setup:

- Tensor parallel: TP4
- Pipeline parallel: PP1
- Hardware shape: single machine, 16 cards
- Model layers: 32

## Timeline Summary

1. Symptom reported: model training `loss` and `reward` were both 0.
2. Save-weight checkpoint shard validation reported an error under TP4/PP1.
3. Training and inference were normal, suggesting the model shards were not
   fundamentally unusable.
4. Megatron save-checkpoint validation was inspected; before saving checkpoint it
   computes and validates shard information, but the code path did not obtain valid
   mapping information.
5. A similar external case involved MoE optimizer state validation and was fixed by
   adding shard offsets in MindSpeed grouped linear, but applying that idea did not
   fix this dense-model case.
6. Comparison showed Qwen3-8B saved weights normally.
7. Control experiments ruled out environment/version and narrowed the issue to model
   configuration.
8. The offending settings were found:

```bash
+actor_rollout_ref.actor.megatron.override_transformer_config.num_layers_in_first_pipeline_stage=11
+actor_rollout_ref.actor.megatron.override_transformer_config.num_layers_in_last_pipeline_stage=11
```

9. Because PP=1 and the model has 32 layers, all layers should belong to the single
   pipeline stage. Setting first and last pipeline stages to 11 was invalid.

## Key Commands

Problematic configuration:

```bash
+actor_rollout_ref.actor.megatron.override_transformer_config.num_layers_in_first_pipeline_stage=11
+actor_rollout_ref.actor.megatron.override_transformer_config.num_layers_in_last_pipeline_stage=11
```

Resolution: remove both settings for the PP1 run.

## Key Files

Reference from the similar but non-applicable MoE case:

```text
MindSpeed/mindspeed/te/pytorch/module/grouped_linear.py
```

That file was relevant to another optimizer-state shard validation issue that needed
offset handling, but it was not the fix for this dense-model PP1 configuration case.

## Problems Encountered

Primary symptom:

- Training `loss` and `reward` were 0.

Observed correlated issue:

- Saving weights failed during Megatron checkpoint shard validation.

Initial analysis:

- Training and inference were normal, so the shard content itself was not obviously
  broken.
- Megatron checkpoint save validation failed while computing or checking shard
  information, indicating invalid or missing mapping metadata.

Potential causes considered:

- Environment, VERL, or third-party library version mismatch.
- Model structure difference.
- Model configuration difference.

Control-variable results:

- Qwen3-8B in the customer environment ran and saved normally, which made a pure
  environment/version issue unlikely.
- Qwen3-8B with the same problematic configuration also reproduced the save-weight
  error, which confirmed the configuration as the likely root cause.
- Aligning checkpoint-related configuration exposed the invalid first/last pipeline
  stage layer settings.

## Final Solution

Delete these invalid overrides:

```bash
+actor_rollout_ref.actor.megatron.override_transformer_config.num_layers_in_first_pipeline_stage=11
+actor_rollout_ref.actor.megatron.override_transformer_config.num_layers_in_last_pipeline_stage=11
```

Reason:

- The model has 32 layers.
- The run uses PP1.
- With a single pipeline stage, all 32 layers should be assigned to that one stage.
- Explicitly setting first and last pipeline stages to 11 creates an inconsistent
  layer-stage mapping and breaks Megatron checkpoint shard validation.

## Verification

The original BOSS note marks the issue as closed loop after deleting the invalid
configuration.

Recommended verification when reusing this case:

- Confirm `pipeline_model_parallel_size == 1`.
- Confirm total model layer count, here 32.
- Confirm there are no `num_layers_in_first_pipeline_stage` or
  `num_layers_in_last_pipeline_stage` overrides inconsistent with PP1.
- Re-run save checkpoint and verify shard validation passes.
- Confirm training metrics no longer show `loss=0` and `reward=0` due to this
  checkpoint/config path.

## Residual Risks

- The `loss/reward=0` symptom can have many unrelated causes. Reuse this case only
  when checkpoint shard validation or pipeline-stage layer config is present in the
  evidence.
- For PP > 1, first/last pipeline stage layer overrides may be valid; do not delete
  them blindly without checking the intended layer distribution.
- The MoE grouped-linear offset fix from the similar case is not generally applicable
  to dense-model PP1 layer-count misconfiguration.
- Environment versions are old relative to current stacks; preserve the root-cause
  pattern rather than copying version-specific assumptions.

## Related Incidents

None archived separately. This record itself is the closed-loop case.

## Extracted Knowledge

Reusable lesson:

- In Megatron/VERL runs with `pp=1`, avoid setting
  `override_transformer_config.num_layers_in_first_pipeline_stage` and
  `num_layers_in_last_pipeline_stage` to partial layer counts. All layers belong to
  the single pipeline stage, and inconsistent first/last-stage overrides can break
  checkpoint shard validation.

## Sensitive Data Handling

The source BOSS note was summarized without storing customer identifiers, private
paths, hostnames, IP addresses, raw logs, credentials, tokens, or private keys.
