---
type: knowledge
date: 2026-06-17
title: "Safe remote command formatting for SSH Docker Ray VERL workflows"
domain: unknown
topics: [ssh, docker, ray, verl, npu, remote-command, shell-quoting]
applies_to:
  - SSH commands that execute Docker commands on remote training nodes
  - Docker container commands for VERL, Ray, vLLM, and NPU training workflows
  - Remote cleanup, launch, monitoring, and dataset validation commands
confidence: verified
risk: medium
source_projects:
  - projects/2026-06-17-verl-remote-command-formatting-pitfalls-and-safe-execution-rules.md
source_incidents: []
last_verified: 2026-06-17
敏感信息: none
skill_candidate: false
---

# Safe remote command formatting for SSH Docker Ray VERL workflows

## Applicability

Use this when running commands across multiple layers such as:

- local shell -> `ssh root@host` -> `docker exec container bash -lc "..."`
- remote VERL/Ray/vLLM startup, cleanup, or monitoring
- NPU process cleanup after aborted distributed training
- parquet/dataset validation inside the target training container

The guidance is global. It is not limited to one VERL project, but it was verified during a VERL dual-node NPU training workflow on 2026-06-17.

## Trigger Signals

- A remote command exits with `143` while running cleanup.
- `pkill -f ...` appears in a command that also contains the same pattern in the shell command line.
- A heredoc such as `python3 - <<'PY'` is nested inside SSH and Docker quotes.
- A command works locally but prints no output or behaves differently inside `ssh`/`docker exec`.
- `sed` or `awk` fails only in the remote composed command.
- `scp` succeeds but the expected remote script is unchanged.
- Host Python lacks packages such as `pandas`, while the target training container has them.
- `ray status` hangs while the cluster is stopped or half-stopped.

## Required Inputs

- Target host and container name.
- Exact target path for copied scripts or generated files.
- Whether the operation is read-only, cleanup, or training launch.
- Expected process names or NPU process IDs when cleanup is required.
- The target runtime environment for data/framework checks, usually the training container rather than the host.

## Procedure

Prefer simple, verifiable remote commands over deeply nested shell programs.

For process cleanup:

- Run `ray stop --force` first.
- Avoid bare `pkill -f ray::` or similar patterns that can match the current shell.
- If `pkill` is necessary, use a non-self-matching regex:

```bash
pkill -f '[r]ay::' || true
pkill -f '[v]erl.trainer.main_ppo' || true
pkill -f '[W]orkerDict' || true
pkill -f '[T]askRunner' || true
pkill -f '[v]LLMHttpServer' || true
pkill -f '[v]llm' || true
```

- If NPU memory remains occupied, use `npu-smi info` to get concrete PIDs and kill those PIDs directly:

```bash
kill -TERM <pid...> 2>/dev/null || true
sleep 3
kill -KILL <pid...> 2>/dev/null || true
```

For SSH plus Docker commands:

- Keep the command short when possible.
- Avoid nesting heredocs inside `ssh "docker exec ... bash -lc '... <<PY ... PY'"`.
- For complex Python checks, use one of these patterns:

```bash
docker exec <container> python3 -c '<short_python_program>'
```

or put the script in a real file under the user-owned workspace, then run:

```bash
docker exec <container> python3 /mnt/disk2t/<user>/path/check.py
```

For text parsing:

- Avoid complex `sed`/`awk` filters in multi-layer remote commands.
- Prefer simple `tail`, `grep`, or Python parsing inside the target container.
- If only a status check is needed, `pgrep -af '<pattern>' || true` is usually safer than chained `ps | awk`.

For `scp`:

- Always copy to the full target file path, not only the target directory, when replacing scripts:

```bash
scp local_script.sh root@host:/mnt/disk2t/<user>/project/scripts/local_script.sh
```

- Immediately verify the actual target file:

```bash
ssh root@host 'grep -n "EXPECTED_SETTING" /mnt/disk2t/<user>/project/scripts/local_script.sh'
```

For environment-specific checks:

- If training runs inside a container, inspect framework code and read parquet files inside that container.
- Do not infer dataset validity from the host if the container has different mounts.
- Host Python missing `pandas` or `pyarrow` is not a dataset problem; run the validation in the target container.

For Ray state:

- Do not rely on `ray status` during cleanup or after an aborted run; it can hang when GCS is gone or half-stopped.
- Verify cleanup using process checks and NPU process tables:

```bash
docker exec <container> pgrep -af 'verl.trainer.main_ppo|WorkerDict|TaskRunner|ray::|vLLMHttpServer|vllm|gcs_server|raylet' || true
npu-smi info | tail -35
```

For training launches:

- Use `DRY_RUN=1` before a real launch to confirm expanded paths and parameters.
- Start training in the background only when required by the workflow.
- Monitor with low-frequency tail checks, not full-log reads.

## Non-Applicable Cases

- Local-only commands without SSH or Docker layering.
- Interactive shell sessions where the operator manually controls quoting and process cleanup.
- Systems without `pkill`, `npu-smi`, Docker, or Ray; adapt the same principle with local equivalents.

## Verification Method

After applying these rules, verify all of the following when relevant:

- The remote command exits with `0` or an expected non-fatal code.
- The intended remote file changed, verified at the exact target path.
- `DRY_RUN=1` prints the intended dataset/model/log paths.
- `pgrep` no longer shows VERL/Ray/vLLM processes after cleanup.
- `npu-smi info` shows no training or `VLLMWorker` process on the target NPUs.
- For dataset checks, validation ran inside the same container that will run training.

## Risk And Safety Notes

- `pkill -f` can terminate the command that is currently performing cleanup. Prefer non-self-matching regexes or concrete PIDs.
- Direct PID kills are safer after `npu-smi` identifies residual NPU workers, but they must only target processes from the current training job or explicitly disposable environment.
- Do not store passwords, tokens, raw auth files, or dense sensitive logs in the vault.
- Keep shared directories read-only unless the user explicitly permits writing there.

## Source Evidence

During a VERL dual-node retest on 2026-06-17:

- `pkill -f ray::` inside a cleanup command caused exit `143`, likely by matching the current cleanup shell.
- A nested SSH/Docker/Python heredoc returned empty output even though a simpler command worked.
- A `sed` process-table filter failed due to quoting/expression handling in the remote composed command.
- A script was accidentally copied to the project root instead of the intended `scripts/` path until a full target path and remote `grep` verification were used.
- Host Python lacked parquet dependencies while the target VERL container could read the dataset correctly.
- `ray status` hung after the cluster was partially stopped; process and `npu-smi` checks gave a reliable cleanup signal.

## Promotion Notes

Consider promoting this to a runbook or adding it to an existing SSH/Docker/VERL skill if similar failures recur in multiple projects.
