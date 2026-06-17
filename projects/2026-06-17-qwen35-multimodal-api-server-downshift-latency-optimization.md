---
type: project
date: 2026-06-17
title: "Qwen3.5 Multimodal API Server Downshift Latency Optimization"
domain: unknown
topics: [vllm, multimodal, qwen3.5, api-server, worker, latency, ascend-a3, npu]
status: archived
sensitive: reviewed
related_incidents: []
extracted_knowledge:
  - knowledge/2026-06-17-qwen35-multimodal-api-server-downshift-latency-optimization.md
---

# Qwen3.5 Multimodal API Server Downshift Latency Optimization

## Goal

Summarize and preserve a trusted internal optimization article:
"2.5x improvement: Qwen3.5 multimodal inference ultra-low-latency A3 optimization practice",
published 2026-04-15.

The reusable goal is to remember how API Server-side multimodal processing became
the dominant TTFT bottleneck, and how moving image-heavy work to TP workers reduced
API Server e2e latency from 196 ms to 44 ms.

## Scope

In scope:

- Qwen3.5-122B-A10B multimodal serving on a vLLM-based stack.
- A3 PD-separated inference architecture with P/D both tuned under TP8EP8.
- Single request with about 10k text tokens plus 40 images at 288x512, roughly
  16k total input length.
- API Server multimodal handling, worker-side image processing, mm_hash stability,
  image-size lazy loading, path handling, tokenizer scheduling, and ViT-side
  micro-optimizations.

Out of scope:

- General Qwen3.5 accuracy evaluation.
- Full LLM kernel optimization, except where baseline TTFT decomposition mentions it.
- Multi-request API Server horizontal scaling; the bottleneck here is single-request
  intra-request multimodal processing.

## Environment

- Model: Qwen3.5-122B-A10B MoE multimodal model.
- Model structure: Vision Encoder plus LLM; LLM has 48 layers, with 36 linear
  attention layers and 12 Flash Attention layers arranged as three linear-attention
  layers followed by one full-attention layer.
- MoE: 256 experts, 8 active experts per forward pass, plus 1 shared expert.
- Vision stack: Qwen3-VL-style 27-layer ViT.
- Serving framework basis: vLLM 0.18 multi-process architecture.
- Architecture: Ascend A3 PD separation, P/D both TP8EP8.
- Baseline software called out by article: CANN 8.5.1 and torch_npu 2.9.
- Customer scenario: H800 4-card mixed deployment context; Ascend A3 was used for
  the optimization path.
- Input: 10240 text tokens plus 40 images at 288x512, about 5760 image tokens,
  total about 16k tokens.

## Timeline Summary

- Baseline: single-concurrency average TTFT was 1.031 s.
- Initial TTFT breakdown:
  - API Server: 196 ms.
  - TP Worker multimodal read before ViT: 7.7 ms.
  - TP Worker deserialization before ViT: 2 ms.
  - TP Worker `_prepare_input()` before ViT: 10.3 ms.
  - ViT model inference: 45 ms.
  - LLM model inference: 770 ms, later optimized to about 450 ms.
- API Server bottleneck analysis showed linear growth from 20 images to 40 images,
  indicating poor CPU multi-core utilization for single-request multimodal work.
- Implementation was split into four rollback-friendly phases:
  - Phase0: instrumentation only, preserving the original multimodal path.
  - Phase1: cheaper local image hash based on local path plus file mtime.
  - Phase2: pass local image paths to engine core / worker and validate worker-side
    ViT-DP image slicing.
  - Phase3: fully downshift image reading and image preprocessing to workers.

## Key Commands

Runtime phase controls from the article:

```bash
VLLM_ASCEND_API_OPT_PHASE=0  # baseline path plus unified profiling
VLLM_ASCEND_API_OPT_PHASE=1  # cheaper local image hash
VLLM_ASCEND_API_OPT_PHASE=2  # local path passthrough; worker-side image slicing
VLLM_ASCEND_API_OPT_PHASE=3  # worker-side image read, preprocess, and ViT input rebuild
```

## Key Files

Article-mentioned code touchpoints:

- `vllm/model_executor/models/qwen3_vl.py#L518`: AddLayerNorm fusion.
- `vllm_ascend/ops/mm_encoder_attention.py#L155`: replacement for pad before ViT FA.

No local source file was modified while archiving this article.

## Problems Encountered

Main API Server-side costs for the 40-image case:

| Component | Cost | Diagnosis |
| --- | ---: | --- |
| `shm copy2buff` | 54 ms | Largest API Server bottleneck; large object serialization/copy path. |
| `pre_process` | 32 ms | Heavy HF image processor and image data preparation path. |
| tokenizer | 36 ms | Blocking encode can stall request processing. |
| `post_process` | 15 ms | Tensor dtype cast work on API Server path. |
| `get_mm_hash` | 8 ms | Content-based or heavier hash path too costly for local images. |
| `cached_qwen2_tokenizer` | 11 ms | Secondary tokenizer-related cost. |

The API Server work scaled approximately linearly from 20 images to 40 images,
which showed that thread-pool usage did not actually exploit CPU multi-core
capacity enough for this workload.

Rejected or limited alternatives:

- Multiple API Servers: helps distribute separate requests, but does not parallelize
  one request's 40-image internal work.
- Coroutine or child-process parallelism: may help partially, but does not remove
  shared-memory copy and Python overhead; benefits are limited.

## Final Solution

Core architecture decision: keep API Server responsible for request semantics and
small scheduling metadata, and move image-heavy work to the TP workers that actually
consume the processed tensors.

API Server keeps:

- Stable multimodal identifier / `mm_hash`.
- Image width and height.
- `grid_thw` and placeholder planning.
- APC identifier plus offset/length metadata.
- Scheduler-required encoder token length information.
- OpenAI API request validation and prompt planning semantics.

TP workers take over:

- Local image reading.
- Decode and PIL/RGB conversion equivalent work.
- HF image processor heavy path.
- `pixel_values` creation.
- ViT-DP image slicing.
- ViT pre-input reconstruction for each rank.
- ViT inference.

Specific supporting optimizations:

- Derive stable local-image `mm_hash` from `real_image_path + mtime_ns`; this keeps
  APC and encoder_cache usable without maintaining an API Server-side multimodal
  processor cache pool.
- Use manual PNG/JPEG header parsing for image dimensions instead of full PIL load.
  Reported timing:
  - PNG: manual parse 0.0087 s, PIL lazy load 0.0318 s, imagesize 0.0394 s,
    full PIL load 1.3199 s.
  - JPEG: manual parse 0.0117 s, imagesize 0.0482 s, PIL lazy load 0.0485 s,
    full PIL load 0.3289 s.
- Use `os.path.abspath()` rather than `Path.resolve()` when canonical symlink
  resolution is not required, because `Path.resolve()` performs `realpath()` work
  across path components.
- Pass a lightweight `LocalImageRef` object with `__slots__`, carrying only path,
  width, and height.
- Wrap blocking tokenizer encode in an executor:

```python
res = await loop.run_in_executor(_TOKEN_EXECUTOR, tk_func)
```

ViT micro-optimizations:

- Fuse AddLayerNorm: about 16 us per use, about 0.4 ms whole-network gain.
- Move `cumsum` before the vision block so it is calculated once and does not
  repeatedly force `.cpu()` synchronization in each attention layer; about 2.8 ms gain.
- Replace pad before ViT FA; reduced to about 70 us and saved about 1 ms whole-network.
- Cache `fast_pos_embed_interpolate` by repeated image size; in the 40-image scenario,
  identical sizes avoid repeated recomputation and save about 1 ms.

## Verification

Before/after API Server e2e result:

| Component | Before | After | Reduction |
| --- | ---: | ---: | ---: |
| API Server e2e | 196 ms | 44 ms | 77.55% |
| `fetch_image` | 20 ms | 6 ms | 70.00% |
| tokenizer | 36 ms | 22 ms | 38.89% |
| `get_mm_hash` | 8 ms | 1 ms | 87.50% |
| preprocess | 32 ms | 0 ms | 100.00% |
| `cached_qwen2_tokenizer` | 11 ms | 1 ms | 90.91% |
| `shm copy2buff` | 54 ms | 0 ms | 100.00% |
| post process | 15 ms | 0 ms | 100.00% |
| other | 35 ms | 14 ms | 60.00% |

Worker-side image read and process added 30.7 ms.

Net latency gain:

```text
196 ms - 44 ms - 30.7 ms = 121.3 ms
```

Article-reported conclusion: API Server-side performance improved by about 2.5x.
ViT-side micro-optimizations contributed about 4-5 ms, much smaller than the
120+ ms API Server downshift gain.

## Residual Risks

- `real_image_path + mtime_ns` is appropriate for local immutable or mtime-tracked
  files. It is risky for object stores, URLs, mutable files with unreliable mtimes,
  symlink-sensitive paths, or content-addressing requirements.
- `os.path.abspath()` must not replace `Path.resolve()` when symlink canonicalization,
  filesystem existence checks, or security boundary checks depend on real paths.
- Worker-side preprocessing must preserve APC, encoder_cache, placeholder, and
  scheduler semantics exactly; otherwise cache hits, image-token accounting, or rank
  slicing can silently break.
- Manual PNG/JPEG dimension parsing needs complete format coverage and fallback
  behavior for unsupported or malformed images.
- Thread-pooling tokenizer encode improves event-loop responsiveness, but executor
  sizing and backpressure still need load testing under production concurrency.

## Related Incidents

None. This is an optimization archive, not a failure incident.

## Extracted Knowledge

- `knowledge/2026-06-17-qwen35-multimodal-api-server-downshift-latency-optimization.md`

## Sensitive Data Handling

The article content provided by the user was treated as directly trusted internal
experience. No secrets, credentials, raw logs, customer identifiers, hostnames, IPs,
tokens, or private keys were written into this archive.
