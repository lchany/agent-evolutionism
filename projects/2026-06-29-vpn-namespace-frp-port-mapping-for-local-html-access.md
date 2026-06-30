---
type: project
date: 2026-06-29
title: "VPN namespace FRP port mapping for local HTML access"
domain: unknown
topics: [vpnns, openvpn, frp, frpc, port-mapping, html]
status: verified
sensitive: redacted
related_incidents: []
extracted_knowledge: []
---

# VPN namespace FRP port mapping for local HTML access

## Goal

Document the local machine's VPN namespace plus FRP reverse-proxy layout, and add a stable remote port for viewing local HTML files.

## Scope

- Applies to this local machine's `vpnns` network namespace workflow.
- Applies to `/opt/frp/frpc-opencode.toml` and `frpc-opencode.service`.
- Remote FRP server address is recorded as `<FRP_SERVER_IP>`; do not store credentials, tokens, or passwords here.

## Environment

- `vpnns-openvpn.service` starts OpenVPN inside network namespace `vpnns`.
- `frpc-opencode.service` starts `/opt/frp/frpc -c /opt/frp/frpc-opencode.toml` inside the same `vpnns` namespace via `ip netns exec vpnns`.
- `frpc` connects to `<FRP_SERVER_IP>:7000`.
- `frpc` proxy targets with `localIP = "127.0.0.1"` refer to localhost inside `vpnns`, not the host/root namespace.

## Mapping Table And Port Meanings

| Remote endpoint | Local endpoint inside `vpnns` | Port meaning | Expected surface |
|---|---|---|---|
| `<FRP_SERVER_IP>:7000` | FRP control connection from `frpc` | FRP server control/listener port, not a browser app port | `frpc` login/control |
| `<FRP_SERVER_IP>:40001` | `127.0.0.1:3000` | OpenCode Web/API remote access | HTTP 401 when unauthenticated |
| `<FRP_SERVER_IP>:30001` | `127.0.0.1:39999` | Hermes WebUI remote access | HTTP redirect/login |
| `<FRP_SERVER_IP>:20001` | `127.0.0.1:18923` | Codex Mobile Web UI remote access | HTTP 200 |
| `<FRP_SERVER_IP>:50001` | `127.0.0.1:18080` | Fixed remote port for local HTML viewing | Static HTML from `python3 -m http.server` |

HTML viewing rule:

```bash
cd /path/to/html-dir
ip netns exec vpnns python3 -m http.server 18080 --bind 127.0.0.1
```

Then open:

```text
http://<FRP_SERVER_IP>:50001/<file>.html
```

## Timeline Summary

- Verified existing FRP mappings on remote ports `40001`, `30001`, and `20001`.
- Added `local-html-59` mapping: remote `50001` -> `vpnns 127.0.0.1:18080`.
- Restarted `frpc-opencode.service`; logs showed `local-html-59 start proxy success`.
- Verified remote `50001` returns probe HTML when the HTTP server runs inside `vpnns`.

## Key Commands

Inspect network and services:

```bash
ip -br addr
ip route
ss -lntup
systemctl status vpnns-openvpn.service frpc-opencode.service --no-pager
```

Verify FRP registration:

```bash
systemctl restart frpc-opencode.service
journalctl -u frpc-opencode.service --since '2 minutes ago' --no-pager | rg 'local-html-59|start proxy success|proxy added|login to server|error|fail'
```

Run a managed probe inside `vpnns`:

```bash
systemd-run --unit=frpc-html-probe --collect \
  --working-directory=/path/to/html-dir \
  /usr/sbin/ip netns exec vpnns /usr/bin/python3 -m http.server 18080 --bind 127.0.0.1

curl http://<FRP_SERVER_IP>:50001/
systemctl stop frpc-html-probe.service
```

## Key Files

- `/opt/frp/frpc-opencode.toml`: FRP client proxy definitions.
- `/etc/systemd/system/frpc-opencode.service`: runs `frpc` inside `vpnns`.
- `/etc/systemd/system/vpnns-openvpn.service`: starts OpenVPN inside `vpnns`.
- `/usr/local/sbin/vpnns-setup`: creates/configures the namespace and veth route.
- `/usr/local/sbin/vpnns-bypass-routes`: manages explicit bypass routes inside `vpnns`.

## Problems Encountered

- Starting `python3 -m http.server` from shell backgrounding caused the tool session to time out. Use systemd transient services for managed verification when possible.
- Starting the HTTP server through plain `systemd-run` put it in the host/root network namespace, so `frpc` could not reach `127.0.0.1:18080` from inside `vpnns`.
- Root cause of the failed first systemd probe: `localIP = "127.0.0.1"` in `frpc` is namespace-local. The target service must run inside the same namespace as `frpc`.

## Final Solution

Added this proxy to `/opt/frp/frpc-opencode.toml`:

```toml
[[proxies]]
name = "local-html-59"
type = "tcp"
localIP = "127.0.0.1"
localPort = 18080
remotePort = 50001
```

The stable HTML viewing path is:

```text
browser/curl -> <FRP_SERVER_IP>:50001 -> frps -> frpc inside vpnns -> vpnns 127.0.0.1:18080 -> local HTML server
```

## Verification

- `frpc-opencode.service` restarted successfully and stayed active.
- `journalctl -u frpc-opencode.service` showed `proxy added: [... local-html-59 ...]` and `[local-html-59] start proxy success`.
- A transient service running `/usr/sbin/ip netns exec vpnns /usr/bin/python3 -m http.server 18080 --bind 127.0.0.1` served a probe `index.html`.
- `curl http://<FRP_SERVER_IP>:50001/` returned the probe HTML body.

## Residual Risks

- Remote `50001` is only useful while a local HTML server is running inside `vpnns` on `127.0.0.1:18080`.
- Do not use local port `8080` for this workflow; the user explicitly rejected it. If a host/root-namespace service binds `127.0.0.1:18080`, `frpc` still cannot reach it; run the server with `ip netns exec vpnns`.
- If remote `50001` later fails, check both `frps` listener state and `frpc-opencode.service` logs before changing app services.

## Related Incidents

- Transient verification pitfall: shell-backgrounded `http.server` can keep the tool session open; use systemd transient units for reproducible start/stop.

## Extracted Knowledge

- In namespace-isolated FRP deployments, `localIP = "127.0.0.1"` points to the FRP client's network namespace. Co-locate the target listener with `frpc`, or use an address reachable from that namespace.
- Keep a port table with remote endpoint, local namespace endpoint, meaning, and expected HTTP behavior; this avoids confusing FRP control ports with application ports.

## Sensitive Data Handling

- Passwords, auth tokens, raw OpenVPN credentials, and the real FRP auth token are intentionally omitted.
- Server address is represented as `<FRP_SERVER_IP>` in this archive.

## Distill Guidance

- Distill classification: project-specific -> projects/
- Suggested domains: git-github
