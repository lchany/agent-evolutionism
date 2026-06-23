---
type: project
date: 2026-06-23
title: "vpnns-run nested invocation fix"
domain: unknown
topics: []
status: verified
sensitive: no
related_incidents: []
extracted_knowledge: []
---

# vpnns-run nested invocation fix

## Goal

Restore the `vpnns-run codex` entrypoint on machine 13 while preserving normal use from the host network namespace.

## Scope

Local machine/network namespace wrapper behavior. This is a project checkpoint, not a cross-project runbook.

## Environment

- Host: `liteserver-8564-1.novalocal`
- Target namespace: `vpnns`
- Wrapper: `/usr/local/sbin/vpnns-run`
- Setup script: `/usr/local/sbin/vpnns-setup`
- Codex CLI: `codex-cli 0.139.0`

## Timeline Summary

- User reported that machine 13 no longer seemed able to use `vpnns-run codex`.
- Minimal reproduction showed `vpnns-run true` and `vpnns-run codex --version` failed before launching Codex with `RTNETLINK answers: File exists`.
- Inspection showed the current Codex process was already inside `vpnns`: `/proc/self/ns/net` and `/var/run/netns/vpnns` had the same device/inode.
- The wrapper always reran `vpnns-setup`, so nested invocation tried to recreate veth state and collided with an existing interface.
- Updated `vpnns-run` to directly execute the requested command when already inside `vpnns`.

## Key Commands

- `timeout 8 vpnns-run true`
- `timeout 8 vpnns-run codex --version`
- `stat -Lc '%d:%i' /proc/1/ns/net /proc/self/ns/net /var/run/netns/vpnns`
- `timeout 10 nsenter -t 1 -n vpnns-run true`
- `timeout 10 nsenter -t 1 -n vpnns-run codex --version`
- `timeout 12 vpnns-run curl -sS --connect-timeout 5 https://api.openai.com/v1/models -o /tmp/vpnns-openai-test.out -w 'http_code=%{http_code}\n'`

## Key Files

- `/usr/local/sbin/vpnns-run`
- `/usr/local/sbin/vpnns-setup`
- `/home/l30002999/PROJECT_MEMORY.md`

## Problems Encountered

- `vpnns-run` failed before invoking the requested command:

```text
RTNETLINK answers: File exists
```

- Initial detection using `readlink /var/run/netns/vpnns` was wrong because `/var/run/netns/vpnns` is a bind mount, not a symlink with a comparable `net:[...]` string.

## Final Solution

`/usr/local/sbin/vpnns-run` now compares the device/inode of `/proc/self/ns/net` and `/var/run/netns/vpnns` using `stat -Lc '%d:%i'`. If they match, the wrapper executes the requested command directly. Otherwise, it runs `/usr/local/sbin/vpnns-setup` and then `ip netns exec vpnns`.

## Verification

- `sh -n /usr/local/sbin/vpnns-run` exited 0.
- `vpnns-run true` exited 0 from the current `vpnns` environment.
- `vpnns-run codex --version` returned `codex-cli 0.139.0` from the current `vpnns` environment.
- `nsenter -t 1 -n vpnns-run true` exited 0 from the host/root namespace.
- `nsenter -t 1 -n vpnns-run codex --version` returned `codex-cli 0.139.0` from the host/root namespace.
- Unauthenticated `vpnns-run curl https://api.openai.com/v1/models` returned HTTP 401 with curl exit 0, confirming network reachability without storing or using credentials.

## Residual Risks

- This only fixes nested invocation of the wrapper. A future failure in interactive Codex startup, credentials, or upstream API behavior would be a separate issue.
- The underlying `vpnns-setup` script still assumes a specific veth naming scheme and is not fully self-healing for arbitrary corrupted namespace state.

## Related Incidents

None.

## Extracted Knowledge

Do not compare `/var/run/netns/<name>` with `/proc/self/ns/net` using `readlink`; compare resolved file identity with `stat -L` because named network namespaces are bind mounts.

## Sensitive Data Handling

No secrets, tokens, private keys, auth files, or dense logs were stored. The connectivity check intentionally used an unauthenticated request and recorded only the HTTP status.
## Distill Guidance

- Distill classification: project-specific -> projects/
