---
type: project
date: 2026-06-30
title: "qwen3vl2b_video_leicheng_much container creation archive"
domain: docker,npu-ascend,verl,qwen3vl
topics: [docker, ascend-npu, qwen3vl, container-creation]
status: verified
sensitive: no
related_incidents: []
extracted_knowledge: []
---

# qwen3vl2b_video_leicheng_much container creation archive

## Goal

Archive the exact baseline image and reusable `docker run` reference command used to create the local Ascend/NPU container `qwen3vl2b_video_leicheng_much`.

## Scope

This is a project-specific container creation record for the local machine and current Qwen3VL2B/VERL workflow. It preserves the image tag, container name, required Ascend device/driver mounts, shared storage mounts, and verification commands.

Do not treat this project archive as a generic runbook for unrelated projects without revalidating image availability, host device paths, and mount requirements.

## Environment

- Host working context: `/home/l30002999`.
- Baseline image: `qwen3vl2b_video_quad_l30002999much:latest`.
- Baseline image ID: `sha256:8a9df3d8981f3fe3006b7791c9ee2446889976acd3555cb149bef6cb7ab08670`.
- Baseline image created: `2026-06-26T16:25:36.605174262Z`.
- Created container: `qwen3vl2b_video_leicheng_much`.
- Container ID: `bfe9f5963a5c246473a64ef0ff887dcd725568b622797b94798c32830fd02312`.
- Container created: `2026-06-30T10:32:52.88184287Z`.
- Required shared mounts verified: `/mnt/disk2t:/mnt/disk2t`, `/mnt/sfs_turbo:/mnt/sfs_turbo`.

## Timeline Summary

1. Confirmed the image `qwen3vl2b_video_quad_l30002999much:latest` exists locally.
2. Confirmed target container name `qwen3vl2b_video_leicheng_much` was not already occupied.
3. Confirmed host-side Ascend device files and shared mount directories existed.
4. Created the container using Ascend runtime, host network, host IPC, and required device/driver/shared-storage mounts.
5. Verified the container is running and `npu-smi info -l` reports 8 NPU IDs inside the container.
6. Wrote the reusable command archive to `/home/l30002999/markdown/qwen3vl2b_video_leicheng_much_container_archive.md` and linked it from `/home/l30002999/PROJECT_MEMORY.md`.

## Key Commands

Reference creation command:

```bash
docker run -itd \
  --name qwen3vl2b_video_leicheng_much \
  --runtime ascend \
  --privileged \
  -u root \
  --network host \
  --ipc=host \
  --cgroupns host \
  --security-opt label=disable \
  --device=/dev/davinci_manager \
  --device=/dev/devmm_svm \
  --device=/dev/hisi_hdc \
  -v /usr/local/dcmi:/usr/local/dcmi \
  -v /usr/local/bin/npu-smi:/usr/local/bin/npu-smi \
  -v /usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/common \
  -v /usr/local/Ascend/driver/lib64/driver:/usr/local/Ascend/driver/lib64/driver \
  -v /etc/ascend_install.info:/etc/ascend_install.info \
  -v /usr/local/Ascend/driver/version.info:/usr/local/Ascend/driver/version.info \
  -v /mnt/sfs_turbo:/mnt/sfs_turbo \
  -v /mnt/disk2t:/mnt/disk2t \
  qwen3vl2b_video_quad_l30002999much:latest \
  bash
```

Verification command:

```bash
docker exec qwen3vl2b_video_leicheng_much bash -lc '
set -e
test -d /mnt/disk2t
test -d /mnt/sfs_turbo
/usr/local/bin/npu-smi info -l
'
```

## Key Files

- User-facing command archive: `/home/l30002999/markdown/qwen3vl2b_video_leicheng_much_container_archive.md`.
- Project memory pointer: `/home/l30002999/PROJECT_MEMORY.md`.

## Problems Encountered

None. Image lookup, container-name preflight, host-device preflight, container creation, and verification all succeeded.

## Final Solution

The local container `qwen3vl2b_video_leicheng_much` was created from image `qwen3vl2b_video_quad_l30002999much:latest` with Ascend runtime, required Ascend devices/driver mounts, and both shared storage mounts. The exact command is preserved in the Markdown archive and in this project archive.

## Verification

- `docker ps` reported `qwen3vl2b_video_leicheng_much qwen3vl2b_video_quad_l30002999much:latest Up ...`.
- `docker inspect` reported `running=true` and the expected bind mounts.
- `docker exec ... /usr/local/bin/npu-smi info -l` completed and reported `Total Count : 8` with NPU IDs 0 through 7.
- `test -d /mnt/disk2t` and `test -d /mnt/sfs_turbo` passed inside the container.

## Residual Risks

- The image tag is local. If this needs to be recreated on another host, first verify the image exists there or transfer/load it explicitly.
- The command assumes the host has the same Ascend device files and driver paths.
- `/mnt/sfs_turbo` is shared storage; avoid deleting or overwriting shared files without explicit user confirmation.

## Related Incidents

None.

## Extracted Knowledge

Project-local fact only: this specific Qwen3VL2B container should be recreated from `qwen3vl2b_video_quad_l30002999much:latest` with `/mnt/disk2t` and `/mnt/sfs_turbo` mounted. The cross-project rule requiring these two mounts already exists in the active Ascend Docker rules.

## Sensitive Data Handling

No passwords, API keys, tokens, private keys, auth files, or dense sensitive logs were recorded.
