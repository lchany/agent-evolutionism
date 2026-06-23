---
type: project
date: 2026-06-23
title: "206 hermes and codex mobile vpn localhost deployment"
domain: unknown
topics: []
status: verified
sensitive: no
related_incidents: []
extracted_knowledge: []
---

# 206 hermes and codex mobile vpn localhost deployment

## Goal

Deploy `hermes-agent`, `hermes-webui`, and Codex `codex-mobile` on `192.168.0.206` using VPN namespace startup while keeping service listeners local-only.

## Scope

Project-specific deployment on `192.168.0.206` (`liteserver-8564-0.novalocal`). Do not generalize credentials, ports, or paths beyond this machine without rechecking.

## Environment

- Host: `192.168.0.206` / `liteserver-8564-0.novalocal`
- VPN namespace: `vpnns`
- VPN service: `vpnns-openvpn.service`
- Hermes agent: `/usr/local/lib/hermes-agent`
- Hermes WebUI: `/opt/hermes-webui`
- Codex Mobile: `/opt/codex-mobile`
- Service ports: `127.0.0.1:39999` and `127.0.0.1:18923` inside `vpnns`

## Timeline Summary

- User requested deployment on 206 using the same local logic and explicitly required monitoring/listening only on `127.0.0.1`, never `0.0.0.0`.
- Local service patterns were inspected: `hermes-webui.service`, `codex-mobile.service`, `/home/opencode/hermes-webui.sh`, and env files.
- Initial large-directory copy was corrected by the user: prefer target-side downloads/installs instead of sending large application directories from the local machine.
- Target-side direct GitHub fetch from the host namespace timed out.
- Target-side `vpnns-run curl` and `vpnns-run git ls-remote/fetch` to GitHub succeeded.
- `codex-mobile` was installed and built on 206 with `vpnns-run pnpm install --frozen-lockfile` and `vpnns-run pnpm run build`.
- Systemd services were enabled and started.

## Key Commands

- `ssh 192.168.0.206 'ip netns list; systemctl status vpnns-openvpn.service'`
- `ssh 192.168.0.206 '/usr/local/sbin/vpnns-run git -C /opt/hermes-webui fetch --prune origin'`
- `ssh 192.168.0.206 'cd /opt/codex-mobile; /usr/local/sbin/vpnns-run pnpm install --frozen-lockfile; /usr/local/sbin/vpnns-run pnpm run build'`
- `ssh 192.168.0.206 'systemctl enable hermes-webui.service codex-mobile.service; systemctl restart hermes-webui.service codex-mobile.service'`
- `ssh 192.168.0.206 'ip netns exec vpnns ss -ltnp | grep -E ":(39999|18923)\b"'`
- `ssh 192.168.0.206 '/usr/local/sbin/vpnns-run curl http://127.0.0.1:39999/health'`
- `ssh 192.168.0.206 '/usr/local/sbin/vpnns-run curl http://127.0.0.1:18923/'`

## Key Files

- `/etc/systemd/system/hermes-webui.service`
- `/etc/systemd/system/codex-mobile.service`
- `/home/opencode/hermes-webui.sh`
- `/etc/hermes-webui.env`
- `/etc/codex-mobile/codex-mobile.env`
- `/usr/local/sbin/vpnns-run`

## Problems Encountered

- Remote `git fetch` from the host namespace timed out against GitHub port 443.
- `codex-mobile` needs a local deployment patch so it can bind to a configured host instead of hard-coded `0.0.0.0`; the deployed service passes `--host 127.0.0.1`.
- Corepack added a `packageManager` field to `/opt/codex-mobile/package.json` during target-side `pnpm` activation.

## Final Solution

Both services run under `vpnns` and bind only loopback:

- Hermes WebUI: `hermes-webui.service` calls `/home/opencode/hermes-webui.sh internal-start`, which validates VPN reachability and execs through `/usr/local/sbin/vpnns-run`.
- Codex Mobile: `codex-mobile.service` runs `/usr/sbin/ip netns exec vpnns ... /usr/local/bin/node /opt/codex-mobile/dist-cli/index.js --host 127.0.0.1 --port 18923 --no-tunnel --no-open --no-login`.

## Verification

- `hermes-webui.service`, `codex-mobile.service`, and `vpnns-openvpn.service` are enabled and active.
- Process network namespace inodes for Hermes WebUI and Codex Mobile match `/var/run/netns/vpnns` and differ from `/proc/1/ns/net`.
- Host namespace has no listeners on ports `39999` or `18923`.
- `vpnns` has only `127.0.0.1:39999` and `127.0.0.1:18923` listeners for these services.
- No `0.0.0.0:39999` or `0.0.0.0:18923` listeners exist in host or `vpnns`.
- No NAT or FORWARD iptables rules expose ports `39999` or `18923`.
- `vpnns-run curl http://127.0.0.1:39999/health` returned HTTP 200.
- `vpnns-run curl http://127.0.0.1:18923/` returned HTTP 200.
- `vpnns-run codex exec --skip-git-repo-check 'Reply with exactly: ok'` returned `ok`.

## Residual Risks

- Some app directories contain local deployment changes and untracked files; do not blindly reset them without checking the localhost binding patch.
- Access should be via SSH local port forwarding, not by changing service bind addresses or adding public NAT rules.

## Related Incidents

None promoted.

## Extracted Knowledge

For 206, GitHub access for deployment should run through `vpnns-run`; host namespace GitHub fetch may time out.

## Sensitive Data Handling

Env files containing service passwords were not printed in full; outputs were redacted. No tokens, passwords, cookies, or auth JSON contents were archived.
## Distill Guidance

- Distill classification: project-specific -> projects/
- Suggested domains: git-github
