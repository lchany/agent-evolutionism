---
type: knowledge
date: 2026-06-30
title: "Qwen3-VL SFT Frozen ViT Visual Token Cache"
domain: multimodal-training
topics: [ms-swift, qwen3-vl, sft, visual-cache, frozen-vit, deepstack, dataloader, safetensors, ascend-a3]
applies_to:
  - Multimodal SFT where the Vision Encoder or ViT is frozen during training
  - Qwen3-VL-style models whose LLM consumes both final image embeds and DeepStack visual features
  - Image-heavy datasets where identical image groups recur across epochs, experiments, or samples
  - Ascend A3 / NPU training where DataLoader worker prefetch can hide CPU cache IO and deserialization
confidence: high
risk: medium
source_projects: []
source_incidents: []
last_verified: 2026-06-30
sensitive: reviewed
skill_candidate: false
---

# Qwen3-VL SFT Frozen ViT Visual Token Cache

## Core Lesson

When ViT is frozen during multimodal SFT, repeatedly executing image read,
processor preprocessing, and ViT forward on every step is wasteful. For
Qwen3-VL, the effective cache boundary is not raw pixels and not only the final
ViT output. Cache the complete post-ViT / pre-LLM visual input structure:

- `image_embeds`
- `image_grid_thw`
- every `deepstack_image_embeds_*` tensor consumed by the LLM decoder

Then load the cached tensors inside DataLoader workers and let normal DataLoader
prefetch hide disk IO and safetensors deserialization behind the previous LLM
step. The speedup comes from removing frozen ViT forward from the training
critical path, not from the cache file format alone.

## Applicability

Use this pattern when all of these hold:

- The visual tower / ViT is frozen for the training run.
- The same image content is deterministic under the same processor and model
  config.
- The model consumes visual features deeply enough that preprocessing-only cache
  would leave major repeated work in the step path.
- Local or node-local storage can hold the visual cache.
- Offline prewarm cost is acceptable and excluded from training runtime.
- DataLoader workers can perform cache lookup, read, deserialization, and batch
  concatenation before the trainer needs the batch.

This was reported for ms-swift + Qwen3-VL on a single 8-card Ascend A3 node,
with `freeze_vit=true`, local disk cache, and SFT workloads spanning one-image
and 28-image samples.

## Non-Applicable Or Risky Cases

- ViT is trainable, LoRA-adapted, or otherwise changes during training.
- Processor config, resize policy, frame extraction, model config, or DeepStack
  layer selection can change without invalidating the cache.
- The dataset includes mutable image paths and cache identity is based only on
  filenames.
- Multi-image order may differ between prompt construction and cache lookup.
- The workload is dominated by LLM forward/backward, ZeRO offload, long-sequence
  communication, or storage contention; relative speedup may be small even if
  absolute time is saved.
- Cache reading is performed synchronously in the training rank, so IO latency
  lands directly on the critical path.

## Required Inputs Before Implementation

- Exact model family and config, especially Qwen3-VL DeepStack layer selection.
- Whether visual tower, visual merger/projector, and related adapters are frozen.
- Processor configuration and any image/video normalization, resize, crop, or
  frame extraction parameters.
- Prompt/template logic for `<image>` placeholders and image order.
- Dataset shape distribution: pure text, one image, multi-image, video, and
  interleaved multimodal samples.
- Storage path, capacity, bandwidth, and whether it is local NVMe or shared FS.
- DataLoader `num_workers` and `prefetch_factor` search range.
- Loss-alignment tolerance and benchmark window, such as first 100 training
  steps after warmup.

## Cache Identity

For image data, prefer content-derived identity over path-derived identity.
The source implementation used canonical PNG bytes:

```python
def compute_image_id(image) -> str:
    buf = io.BytesIO()
    image.convert('RGB').save(buf, format='PNG')
    return hashlib.sha256(buf.getvalue()).hexdigest()

def compute_image_group_id(image_ids: list[str]) -> str:
    raw = 'qwen3vl_image_group_v1|' + '|'.join(image_ids)
    return hashlib.sha256(raw.encode()).hexdigest()
```

Use a sample-level ordered `group_id`, not a single-image key, for Qwen3-VL
multi-image samples. The order of `image_embeds` and `image_grid_thw` must match
the prompt order of `<image>` tokens exactly.

## Cache Schema

Persist each image group as safetensors plus metadata/manifest. A minimal tensor
payload is:

```python
{
    'image_embeds': Tensor,
    'image_grid_thw': Tensor,
    'deepstack_image_embeds_0': Tensor,
    'deepstack_image_embeds_1': Tensor,
    # ... one tensor per configured DeepStack layer
}
```

Metadata should include at least:

- cache schema version
- processor fingerprint
- model/config fingerprint
- DeepStack layer list
- image count and ordered image IDs
- token/feature counts derived from `image_grid_thw`
- dtype and shape for each saved tensor

Strict mode should fail on cache miss or schema mismatch instead of silently
falling back, unless the run is explicitly configured for mixed cached and
uncached samples.

## Implementation Pattern

### 1. Offline Prewarm

1. Read original images.
2. Run the exact same processor as training.
3. Execute frozen ViT and visual merger/projector once.
4. Save `image_embeds`, `image_grid_thw`, and all DeepStack visual features.
5. Use multi-card or multi-process prewarm with per-rank shard directories to
   avoid write conflicts, for example:

```text
cache_root.shards/shard_0
cache_root.shards/shard_1
...
cache_root.shards/shard_7
```

6. Merge shards into the final cache root and validate manifest completeness.

Offline prewarm is not counted in training throughput, but it should be measured
separately for end-to-end pipeline planning.

### 2. Template / Dataset Stage

- Compute image IDs and ordered group ID while processing each sample.
- Use group metadata to obtain `image_grid_thw` early when needed to expand
  `<image>` tokens correctly.
- Do not emit `pixel_values` when a strict valid cache hit exists.
- Load cached tensors in DataLoader workers, not inside the trainer forward path.

The returned dataset fields should resemble:

```python
{
    'cached_image_embeds': entry['image_embeds'],
    'cached_image_grid_thw': entry['image_grid_thw'],
    'cached_deepstack_image_embeds': entry.get('deepstack_image_embeds'),
}
```

Keep tensors on CPU. Let the ordinary pin-memory and device-copy path handle
movement to NPU/GPU unless profiling proves a special path is needed.

### 3. Collator Stage

- Concatenate `cached_image_embeds` across samples on dimension 0.
- Concatenate `cached_image_grid_thw` across samples on dimension 0.
- For DeepStack, concatenate per layer, preserving layer order:

```python
deepstack_concat = []
for layer_idx in range(len(cached_deepstack[0])):
    deepstack_concat.append(torch.cat([d[layer_idx] for d in cached_deepstack], dim=0))
```

### 4. Model Forward Stage

- If `cached_image_embeds` and `cached_image_grid_thw` are present, skip ViT.
- Move cached tensors to `inputs_embeds.device` and `inputs_embeds.dtype`.
- Validate image token count equals cached feature count before scatter.
- Scatter `image_embeds` into `<image>` token positions and pass DeepStack
  tensors into the decoder exactly as the pixel path would.

Critical guard:

```python
n_image_tokens = int((input_ids == self.config.image_token_id).sum().item())
n_image_features = int(image_embeds.shape[0])
if n_image_tokens != n_image_features:
    raise ValueError(
        f'Image features and image tokens do not match: '
        f'tokens={n_image_tokens}, features={n_image_features}'
    )
```

## DataLoader Prefetch Guidance

Do not assume more workers and larger prefetch are always better. Tune cache and
baseline together. Larger worker pools can increase random IO, CPU scheduling
pressure, and prefetch queue memory. In the source experiment, good candidates
were:

- `dataloader_num_workers`: 8 or 16
- `dataloader_prefetch_factor`: 1 or 4

The preferred implementation is standard DataLoader worker prefetch. A custom
training-rank prefetch queue was tested conceptually but had similar performance
and higher complexity because it introduced additional thread-count and queue
length knobs.

## Verification Method

Verify correctness first:

- Compare loss between pixel path and cached path with the same model, dataset,
  seed, batch size, and training configuration.
- Require strict alignment of prompt image token count, `image_grid_thw`, and
  cached feature count.
- Test single-image and multi-image samples; multi-image order is the critical
  failure mode.
- Include cache miss, schema mismatch, and strict-mode failure tests.

Then verify performance:

- Benchmark the same step window, such as the first 100 training steps.
- Search DataLoader worker/prefetch settings for both baseline and cached path.
- Profile active steps and separate:
  - DataLoader wait time
  - time before memory peak / pre-LLM visual path
  - LLM forward/backward time after memory peak
  - total step time

Expected profiling pattern: cached path removes the pre-LLM ViT segment, while
LLM forward/backward after the memory peak remains nearly unchanged. DataLoader
wait should stay very small if cache IO is hidden by workers.

## Source Evidence

The source article reported these measured results on ms-swift + Qwen3-VL with
single-node 8-card Ascend A3 and local visual cache.

### Best-parameter results over first 100 steps

| Model | Data | BS | Parallelism | Baseline best runtime | Visual cache best runtime | Speedup | Mean loss error |
| --- | --- | ---: | --- | ---: | ---: | ---: | ---: |
| Qwen3-VL-2B | 1 image | 1 | zero1 | 66.64s (w8/pf1) | 59.15s (w8/pf1) | 11.24% | -0.00012 |
| Qwen3-VL-8B | 1 image | 1 | zero1 | 115.6s (w8/pf1) | 106.4s (w8/pf1) | 7.96% | 0.00014 |
| Qwen3-VL-30B-A3B | 1 image | 1 | zero3 | 238.9925s (w16/pf4) | 220.0601s (w16/pf4) | 7.92% | -0.000002 |
| Qwen3-VL-2B | 1-image subset | 4 | zero1 | 73.1342s (w16/pf4) | 62.96s (w8/pf1) | 13.91% | -0.00018 |
| Qwen3-VL-2B | 1-image subset | 8 | zero1 | 93.3806s (w16/pf4) | 72.29s (w8/pf1) | 22.59% | 0.00019 |
| Qwen3-VL-2B | 28 images | 1 | zero1 | 346.90s (w16/pf4) | 146.10s (w16/pf4) | 57.88% | -0.00016 |
| Qwen3-VL-8B | 28 images | 1 | zero2 | 690.5s (w16/pf4) | 481.0s (w16/pf4) | 30.34% | -0.00035 |
| Qwen3-VL-30B-A3B | 28 images | 1 | zero3 offload | 2592.9005s (w16/pf1) | 2448.0162s (w8/pf1) | 5.59% | 0.00109 |

### Same-parameter examples, w=8, pf=1, BS=1

| Model | Data | Parallelism | Baseline runtime | Visual cache runtime | Speedup | Mean loss error |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Qwen3-VL-2B | 1 image | zero1 | 66.64s | 59.15s | 11.24% | -0.00012 |
| Qwen3-VL-2B | 28 images | zero1 | 357.8s | 147.0s | 58.92% | 0.00081 |
| Qwen3-VL-8B | 1 image | zero1 | 115.6s | 106.4s | 7.96% | 0.00012 |
| Qwen3-VL-8B | 28 images | zero2 | 705.6s | 485.4s | 31.21% | 0.00132 |
| Qwen3-VL-30B-A3B | 1 image | zero3 offload | 2372.9856s | 2311.9678s | 2.57% | 0.00019 |
| Qwen3-VL-30B-A3B | 28 images | zero3 offload | 2863.2829s | 2448.0162s | 14.50% | 0.00209 |

### Profiling evidence

For Qwen3-VL-2B, 28 images, BS=1, w8/pf1, active steps 12-14:

- Baseline active step average: about 1834 ms.
- Visual cache active step average: about 1426 ms.
- Step reduction: about 408 ms.
- Baseline memory peak occurred about 750 ms after step start.
- Visual cache memory peak occurred about 334 ms after step start.
- Difference before memory peak: about 398 ms, matching the step reduction.
- After memory peak to step end: baseline about 1102 ms, visual cache about
  1092 ms, effectively unchanged.
- DataLoader wait: baseline about 1.16 ms, visual cache about 1.40 ms.

Conclusion from profiling: the speedup comes from removing ViT forward from the
critical path. Cache loading and tensor assembly were hidden by DataLoader worker
prefetch and did not become a trainer-side bottleneck.

## Practical Conclusions

- Cache post-ViT visual features, not just pixels, when ViT is frozen.
- For Qwen3-VL, cache all DeepStack features together with final image embeds.
- Use ordered image-group cache keys for multi-image samples.
- Keep cache IO and deserialization inside DataLoader workers, not the training
  rank's synchronous path.
- Tune DataLoader settings jointly with cache; larger worker/prefetch values can
  hurt under IO or CPU scheduling pressure.
- Expect larger relative gains when image count is high or ViT is the bottleneck.
- Expect smaller relative gains when ZeRO offload, LLM compute, long sequence
  communication, or memory pressure dominates, but absolute savings may remain
  useful.

## Extension Ideas

- Extend schema from image groups to video frame groups. Include frame extraction
  policy, frame order, temporal position encoding, and processor config in the
  fingerprint.
- Add finer-grained shard indexing, batched safetensors reads, local NVMe plus
  shared-storage two-level cache, resumable prewarm, and cache integrity checks.
- Generalize at framework level as "offline materialize frozen subgraph + async
  prefetch reuse", where users declare frozen modules and cacheable inputs.
- Apply to RL frameworks such as verl when the visual tower remains frozen during
  rollout and update stages.

## Relationship To Existing Vault Knowledge

This complements `knowledge/2026-06-17-qwen35-multimodal-api-server-downshift-latency-optimization.md`.
That record covers multimodal inference API-server downshift: move heavy image
work from API server to workers and reduce large-object IPC. This record covers
SFT training: remove frozen ViT computation entirely from each training step by
offline materialization and DataLoader-prefetched cache reuse. The shared
principle is to keep expensive visual processing out of the latency-critical
consumer path while preserving image-token alignment and cache identity.
