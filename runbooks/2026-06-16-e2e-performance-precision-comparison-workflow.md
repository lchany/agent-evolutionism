---
type: runbook
date: 2026-06-16
title: "End-to-end performance and precision comparison workflow"
domain: unknown
topics: [e2e-test, performance, precision, verl, distributed-training, docker, ray, npu]
confidence: mature
risk: medium
source_knowledge: [knowledge/2026-06-15-github-backed-codex-experience-vault.md]
source_incidents: [incidents/2026-06-16-verl-jpeg-q90-reward-drift-root-cause.md]
sensitive: reviewed
skill_candidate: false
---

# End-to-end performance and precision comparison workflow

## When To Use

Use this runbook when comparing a baseline and an optimized implementation in
an end-to-end distributed training/inference workflow, especially when both
performance and precision/reward correctness matter.

Typical examples:

- VERL/Ray/vLLM distributed RL training on Ascend NPU
- image/video/data transport optimizations
- communication or preprocessing optimizations
- any change where a faster result is invalid if it changes reward/accuracy

Do not treat this as specific to JPEG. The main lesson is the testing discipline:
make runs comparable, preserve evidence, isolate variables, and clean temporary
state.

## Required Inputs

- Test objective: what changed, what is baseline, what is optimized.
- Acceptance gates:
  - performance metric and expected direction, such as throughput up or step time down
  - precision metric and tolerance, such as `abs(optimized - baseline) <= 0.03`
- Exact machines, IPs, containers, images, and shared/local mount semantics.
- Existing image archives or container records under `/mnt/disk2t/l30002999`,
  if any, before creating or copying new containers.
- For VERL tasks, whether the user wants to load the archived baseline image
  from `/mnt/disk2t/l30002999/container-migration/verl_baseline_migrated_from59_20260612.tar`
  and create a fresh container.
- Dataset paths and whether they are shared across machines.
- Full launch scripts or exact command lines for baseline and optimized runs.
- Cleanup policy for temporary scripts, ports, Ray clusters, monitor processes, and logs.
- Where final artifacts should be archived.

## Procedure

### 1. Record The Test Matrix Before Running

Create a small run directory and record:

- machine list, role of each machine, and private IPs
- container ID, container name, image, and code hash if code differs
- whether a previous Docker image archive, container export, or container
  metadata record already exists under `/mnt/disk2t/l30002999`
- mounted paths, explicitly marking true shared storage versus same-name local disks
- dataset train/validation paths
- model/checkpoint paths
- launch script path
- temporary ports and processes that must be cleaned
- expected output/log directories

Important lesson from the 13+59 tests: `/mnt/sfs_turbo` was a real shared NFS
mount, while `/mnt/disk2t` was only a same-name local disk on each machine.
Do not assume a path is shared because the string is identical.

Before preparing containers for VERL E2E tests, search local storage for
previously stored images or container records:

```bash
find /mnt/disk2t/l30002999 -type f \
  \( -iname '*.tar' -o -iname '*.tar.gz' -o -iname '*.tgz' -o -iname '*.tar.zst' \
     -o -iname '*.zst' -o -iname '*.img' -o -iname '*.sif' -o -iname '*.sqsh' \
     -o -iname '*.docker' \) \
  -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' 2>/dev/null | sort -r | head -100

find /mnt/disk2t/l30002999 -maxdepth 5 -type f \
  \( -iname '*image*' -o -iname '*docker*' -o -iname '*container*' \
     -o -iname '*镜像*' -o -iname '*容器*' \) \
  -printf '%TY-%Tm-%Td %TH:%TM %s %p\n' 2>/dev/null | sort -r | head -100
```

If only `docker inspect` or env records exist, treat them as provenance, not as
loadable images. Use them to identify the expected image tag and mounts, then
verify with `docker images` or rebuild/copy the actual image if needed.

Known local VERL baseline image archive:

```text
/mnt/disk2t/l30002999/container-migration/verl_baseline_migrated_from59_20260612.tar
```

Metadata:

- sha256: `570dd32691a9dc1be04f6b1cbda5e7bb4a9b0985c3b67fb952e4ebafe4bec886`
- repo tag: `verl-0.7.1_vllm-0.18.0_cann-8.5.1_baseline:migrated_from_59_20260612`

At the start of a new VERL task or before starting training, ask the user
whether to load this archive and create a new container. Do not automatically
load the archive, replace containers, or copy it to another machine without
explicit confirmation.

When loading the archive, treat the `.tar` as immutable source material: do not
delete, move, overwrite, rename, chmod/chown, recompress, or otherwise modify it.

### 2. Make Baseline And Optimized Parameters Comparable

Before starting a run, diff the final command lines, not just the shell scripts.
At minimum verify:

- dataset and validation files
- model path and checkpoint/resume mode
- batch size, rollout count, max prompt/response length
- shuffle and validation shuffle
- truncation and overlong filtering
- random seeds and worker-side deterministic seed propagation
- TP/DP/PP sizes and number of nodes/NPUs
- Ray/runtime environment variables
- logging, save, validation frequency, and total steps

If parameters must change to make a run start, record that the result is no
longer a like-for-like comparison.

### 3. Preflight The Machines

Before launching:

- check whether `/mnt/disk2t/l30002999` already has relevant Docker image
  archives, container exports, or inspect records from previous VERL tests
- if the task is new, ask whether to create a fresh container from
  `/mnt/disk2t/l30002999/container-migration/verl_baseline_migrated_from59_20260612.tar`
  instead of reusing an existing container
- preserve that source image archive unchanged after any `docker load` or
  container creation operation
- check NPU processes and memory
- check CPU/memory pressure
- check whether other users have jobs
- check Ray state and stop only Ray/processes started by this test
- check that required containers are running on all machines
- check SSH key access in the intended direction
- check that scripts/data exist on every non-shared path

Never kill a process that was not started by this test unless the user explicitly
approves it.

### 4. Launch Only In Background For Long Runs

Training and long benchmarks must run detached, such as via `setsid`, `nohup`,
or a wrapper that survives connection interruption. Log stdout/stderr to a
timestamped directory.

The wrapper should:

- write `run_meta.log` with machine/container/script/parameter information
- write preflight output before starting
- start monitors with their PID files or control logs
- start Ray and record Ray status
- append `TRAIN_END` and `EXIT_CODE`
- run cleanup in a trap/finalizer

### 5. Monitor With Evidence, Not Memory

Keep periodic status checks in files:

- training step, validation step, latest metric line
- throughput, time per step, token count, MFU if present
- reward/mean or task-specific precision metric
- NPU utilization and memory
- CPU/memory usage
- monitor start/stop logs

Do not summarize from memory. Every claim in the final report should point to a
log file, JSON, markdown report, or command output.

### 6. Precision Comparison Comes Before Performance Acceptance

A faster optimized run is invalid if precision is outside tolerance. Compare
the exact user-approved metric. In the VERL case this was `reward/mean` /
`critic/rewards/mean`, not simply whether optimized became higher or lower.

Use absolute deviation from baseline:

```text
abs(optimized_metric - baseline_metric) <= tolerance
```

For stochastic training, initial validation before optimizer updates is often
cleaner than late training steps. Training-step trajectories may diverge due to
sampling and update dynamics; do not overclaim bitwise equivalence from sampled
rollout metrics.

### 7. If Precision Fails, Isolate One Variable

Do not immediately tune parameters. First prove where the difference enters.
Recommended isolation ladder:

1. Confirm baseline/optimized command-line parameter equality.
2. Confirm sample set and validation set equality.
3. Confirm shuffle and ordering semantics.
4. Confirm input bytes/pixels/tensors are equal or intentionally changed.
5. Build an isolating dataset or synthetic input that applies only the suspected transform.
6. Run the isolating case through the baseline path.
7. Compare initial validation and per-sample outputs/scores.
8. Only after input equality is proven should NPU math tools such as msprobe be the next focus.

JPEG q90 example:

- original raw input + `raw_rgb`: initial validation reward `0.0`
- original input + JPEG q90 transport: initial validation reward `0.05625`
- JPEGized input + `raw_rgb`: initial validation reward `0.05625`

This isolated lossy pixel perturbation as the precision root cause.

### 8. Performance Microbenchmarks Must Match The Question

When measuring compression/transport optimizations, separate:

- encode/compress time
- payload size
- transfer time
- remote decode/decompress time
- end-to-end total time

Avoid benchmark artifacts. In the 13->59 TCP benchmark, the first run without
`TCP_NODELAY` showed about 45 ms delayed-ACK latency and was invalid for
scheme comparison. Fix the benchmark protocol before drawing conclusions.

Include lossy schemes only as reference if precision has already rejected them.

### 9. Cleanup Is Part Of The Test

Before launching, list temporary resources:

- scripts copied to remote `/tmp`
- server/client benchmark processes
- ports
- Ray head/worker processes
- monitor processes
- temporary datasets

After completion or failure:

- stop only processes created by the wrapper
- remove temporary scripts copied to remote containers
- stop monitors
- stop or leave Ray according to the run contract, but record the decision
- verify with `pgrep` and NPU process checks
- preserve logs and final artifacts

### 10. Write A Final Decision Report

The final report should contain:

- objective and test matrix
- machine/container/image/mount summary
- exact baseline and optimized command/log paths
- parameter equality table
- precision table and pass/fail against tolerance
- performance table and pass/fail against objective
- resource utilization summary
- failures and retries
- cleanup proof
- final decision: adopt, reject, or keep as conditional fallback

Avoid vague conclusions. Say exactly why a方案 is rejected or accepted.

## Validation

The runbook is complete for a test only when these are true:

- baseline and optimized logs are preserved
- final command lines are inspectable
- parameter differences are intentional and documented
- precision metric is compared against the agreed tolerance
- performance metric is compared over matching scope
- all temporary processes/scripts/ports are cleaned or explicitly retained
- final report and archive paths exist
- reusable lessons are stored in Experience Vault or local markdown archive

For this JPEG/RGB transport work, reusable evidence was archived at:

- `/home/l30002999/markdown-archive/20260615_verl_jpegized_raw_validation.md`
- `/home/l30002999/markdown-archive/20260616_lossless_transport_benchmark_13_59.md`
- `/home/l30002999/markdown-archive/20260616_lossless_transport_benchmark_13_59_scale4.md`

## Failure Handling

On any execution failure:

1. Stop repeated blind retries.
2. Preserve the failed log and mark it as failed.
3. Search Experience Vault incident records.
4. Identify whether failure is:
   - environment/resource issue
   - parameter mismatch
   - code bug
   - benchmark design bug
   - external user workload interference
5. Fix the cause or explicitly exclude the run from evidence.
6. Do not delete failed logs unless the user explicitly requested cleanup of
   failed intermediates and the result is no longer needed.

Examples from the JPEG transport work:

- Remote path mismatch: `/mnt/disk2t` looked identical but was not shared; copy
  scripts/data to the remote host or use true shared storage.
- Foreground launch risk: long training must be backgrounded.
- Delayed ACK artifact: benchmark result was invalid until `TCP_NODELAY` was set.
- Training trajectory divergence: use initial validation and isolating inputs
  for stronger precision evidence.

## Non-Applicable Cases

This runbook does not replace domain-specific correctness tests. For example,
if a model should be numerically bitwise identical, task reward comparison alone
is not sufficient. Add tensor/logit/byte-level checks.

This runbook also does not authorize killing unknown processes on shared
machines.

## Related Knowledge

- `incidents/2026-06-16-verl-jpeg-q90-reward-drift-root-cause.md`
- `/home/l30002999/markdown-archive/20260615_verl_dual_node_temp_process_cleanup_lessons.md`
- `/home/l30002999/markdown-archive/20260615_verl_jpegized_raw_validation.md`

## Skill Promotion Notes

This should become a Codex skill if we repeat three or more similar E2E
baseline-vs-optimized comparisons. Candidate triggers:

- "做双机/多机性能精度对比"
- "baseline 和 optimized 对比"
- "reward/mean 对齐"
- "训练日志保留并清理临时进程"

The skill should automate checklist creation, run directory layout, parameter
diff extraction, cleanup verification, and final report generation.
