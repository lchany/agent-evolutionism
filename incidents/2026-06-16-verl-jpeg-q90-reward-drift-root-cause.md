---
type: incident
date: 2026-06-16
title: "VERL JPEG q90 reward drift root cause"
domain: unknown
topics: [verl, jpeg, precision, reward, ascension-npu, distributed-training]
status: validated
confidence: verified
sensitive: reviewed
source_projects: [/mnt/disk2t/l30002999/RGB2JPEG_13_59]
related_knowledge: []
---

# VERL JPEG q90 reward drift root cause

## Trigger Signal

In VERL multimodal GRPO testing on a 13+59 two-node Ascend setup, `reward/mean`
and `critic/rewards/mean` differed by more than the accepted 0.03 threshold
between `raw_rgb` image transport and `jpeg_bytes` q90 transport.

## Context

The experiment compared:

- original dataset with `actor_rollout_ref.rollout.custom.image_transport.mode=raw_rgb`
- original dataset with `image_transport.mode=jpeg_bytes` and `jpeg_quality=90`
- JPEGized dataset, where images were encoded/decoded through JPEG q90 and saved
  back to PNG, then transported with `raw_rgb`

The third case isolates visual pixel perturbation from the transport code path.
All runs used aligned seed/shuffle/truncation/balance settings.

## Failed Command Or Operation

Not a command failure. The failed invariant was precision alignment:
`abs(reward/mean optimized - reward/mean baseline) <= 0.03`.

## Error Signature

Initial validation before training update:

- original `raw_rgb`: `val reward@1 = 0.0`
- `jpeg_bytes` q90: `val reward@1 = 0.056249999`
- JPEGized dataset with `raw_rgb`: `val reward@1 = 0.056249999`

15-step training also exceeded the threshold on multiple steps:

- raw vs JPEG transport: 7/15 steps over 0.03, max diff 0.084374998
- raw vs JPEGized raw: 7/15 steps over 0.03, max diff 0.084375009

## Failed Attempts

Deterministic seeds and aligned training parameters reduced confounders but did
not make 15-step sampled training trajectories bitwise identical. Training-step
metrics should therefore be treated as amplification evidence, not exact
trajectory equivalence evidence.

## Root Cause

JPEG q90 transport is lossy and changes the visual input seen by vLLM.
The running transport implementation converts PIL images to RGB, saves JPEG
bytes at q90, and decodes the JPEG bytes back to RGB on the receiver. The
JPEGized dataset was pixel-identical to this transport round trip while being
measurably different from the original raw images.

Pixel check over train+test rows:

- 64/64 JPEGized images exactly matched the transport q90 encode/decode result
- average changed channel fraction: 0.240798
- average changed pixel fraction: 0.415557
- average mean absolute channel diff: 0.716499
- max absolute channel diff: 98
- average compression ratio: 32.151418

## Resolution

Do not use lossy JPEG q90 as a precision-equivalent optimization for this VLM
training path. For precision-aligned performance optimization, test a lossless
transport path such as PNG bytes or another lossless image-byte representation
against `raw_rgb`.

## Verification

Primary report:

`/mnt/disk2t/l30002999/RGB2JPEG_13_59/precision_debug/deterministic_seed_20260615_2038/jpegized_raw_transport_retry_20260615_233039/jpegized_raw_vs_raw_jpeg_compare.md`

Pixel equivalence file:

`/mnt/disk2t/l30002999/RGB2JPEG_13_59/precision_debug/deterministic_seed_20260615_2038/jpegized_raw_transport_retry_20260615_233039/pixel_transport_equivalence.json`

Archived report:

`/home/l30002999/markdown-archive/20260615_verl_jpegized_raw_validation.md`

## Reuse Notes

When debugging precision drift in VERL multimodal transport:

1. First align sample set, shuffle, validation shuffle, truncation, seed, TP/DP/PP,
   `rollout.n`, model path, and batch sizes.
2. Compare initial validation before any optimizer update; it is cleaner than
   sampled training-step reward.
3. Build an isolating dataset that applies only the suspected image transform,
   then run it through the baseline transport.
4. Verify pixel equivalence between the isolating dataset and the transport
   encode/decode output.
5. Use msprobe/NPU math tools only after input bytes/pixels are proven identical.

## Non-Applicable Cases

This record does not prove all JPEG qualities fail. It proves q90 is not
precision-equivalent for the tested Geometry3K/Qwen3-VL setup and acceptance
threshold. Higher quality JPEG still requires the same validation.

## Sensitive Data Handling

No passwords, keys, tokens, raw logs, or auth files are stored here. This record
contains only summary metrics and local artifact paths.
