---
type: project
date: 2026-06-30
title: "VERL dataset split ratio correction"
domain: unknown
topics: [verl, dataset, split-ratio, npu]
status: verified
sensitive: reviewed
related_incidents: ["incidents/2026-06-30-verl-dataset-split-ratio-correction.md"]
extracted_knowledge: []
---

# VERL dataset split ratio correction

## Goal

Create a VERL-compatible KITTI tracking dataset where one row is one sample with 28 physical images, arranged as 7 logical groups of 4 ordered frames, while using a standard train/test split.

## Scope

Project-local dataset generation under `/mnt/disk2t/l30002999/` using source data from `/mnt/disk2t/dataset/video-2D/kitti_tracking`.

## Environment

- Container used for validation: `verl_lazy_clean_baseline`
- Output directory: `/mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl/`
- Builder script: `/mnt/disk2t/l30002999/tmp/kitti_28frames_dataset/make_kitti_28f_7x4_verl.py`

## Timeline Summary

- Initial generation created valid VERL parquet rows but preserved raw KITTI `training`/`testing` counts, producing 72/118.
- User corrected that the split should follow a standard training/testing ratio.
- Builder was changed to merge source sample pools first, then split deterministically by 80/20.
- Final output regenerated and verified.

## Key Commands

- `python /mnt/disk2t/l30002999/tmp/kitti_28frames_dataset/make_kitti_28f_7x4_verl.py`
- Container validation loaded both parquet files, opened images, checked logical groups, checked shapes, and checked final ratio.

## Key Files

- `/mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl/train.parquet`
- `/mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl/test.parquet`
- `/mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl/summary.json`
- `/mnt/disk2t/l30002999/dataset/kitti_28f_7x4_verl/README.md`
- `/mnt/disk2t/l30002999/tmp/kitti_28frames_dataset/make_kitti_28f_7x4_verl.py`
- `/mnt/disk2t/l30002999/PROJECT_MEMORY.md`
- `/root/.config/opencode/AGENTS.md`

## Problems Encountered

The first final split was wrong because source directory names/counts were treated as final ML split semantics.

## Final Solution

The dataset builder now creates a complete sample pool from both KITTI source directories and applies a deterministic 80/20 split by default. The split strategy is documented in `summary.json` and `README.md`, and an active global rule plus project correction prevent repeating the mistake.

## Verification

Verified inside `verl_lazy_clean_baseline`:

- Train rows: 152
- Test rows: 38
- Train ratio: 0.8
- Each first-row sample in both splits has 28 images, 7 logical groups, 28 prompt image placeholders, and matching requested group shapes.

## Residual Risks

If a future task requires a benchmark-preserved split, the user must explicitly say so; otherwise the default should remain standard 80/20.

## Related Incidents

- `incidents/2026-06-30-verl-dataset-split-ratio-correction.md`

## Extracted Knowledge

Candidate lesson: generated VERL datasets should not inherit source directory split counts unless explicitly required; default to explicit or standard train/test ratio and verify counts.

## Sensitive Data Handling

No secrets, credentials, tokens, private keys, or raw sensitive logs are stored here.

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: reusable-incident -> incidents/
- Suggested domains: docker, verl
