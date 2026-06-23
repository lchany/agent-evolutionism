---
type: project
date: 2026-06-23
title: "206 frpc external mapping for hermes and codex mobile"
domain: unknown
topics: []
status: verified
sensitive: no
related_incidents: []
extracted_knowledge: []
---

# 206 frpc external mapping for hermes and codex mobile

## Goal

Expose the already-running `hermes-webui` and Codex `codex-mobile` services on `192.168.0.206` through the same FRP pattern used on the local machine, while keeping both applications bound only to local loopback inside `vpnns`.

## Scope

Project-specific configuration for `192.168.0.206` (`liteserver-8564-0.novalocal`) and FRP server `47.236.151.116`.

## Environment

- Target host: `192.168.0.206`
- FRP server: `47.236.151.116:7000`
- VPN namespace: `vpnns`
- Local services inside `vpnns`:
  - Hermes WebUI: `127.0.0.1:39999`
  - Codex Mobile: `127.0.0.1:18923`
- External FRP ports:
  - Hermes WebUI: `47.236.151.116:30002`
  - Codex Mobile: `47.236.151.116:20002`

## Timeline Summary

- User asked to make 206 externally accessible like the local machine via `frpc`.
- Local machine FRP pattern was inspected: local-only service listeners, `frpc` running inside `vpnns`, and remote TCP port mappings on `47.236.151.116`.
- Installed `frpc 0.69.0` on 206 by downloading from GitHub through `/usr/local/sbin/vpnns-run`.
- Created a 206-specific FRP config and systemd service.
- Started and enabled the service, then verified remote endpoints and listener safety.

## Key Commands

- `ssh 192.168.0.206 '/usr/local/sbin/vpnns-run curl -fL ... frp_0.69.0_linux_arm64.tar.gz'`
- `ssh 192.168.0.206 'systemctl enable frpc-206.service; systemctl restart frpc-206.service'`
- `curl http://47.236.151.116:30002/health`
- `curl http://47.236.151.116:20002/`
- `ssh 192.168.0.206 'ip netns exec vpnns ss -ltnp | grep -E ":(39999|18923)\b"'`

## Key Files

- `/opt/frp/frpc`
- `/opt/frp/frpc-206.toml`
- `/etc/systemd/system/frpc-206.service`
- Existing local comparison file: `/opt/frp/frpc-opencode.toml`

## Problems Encountered

No deployment failure after switching target-side downloads through `vpnns-run`. Sensitive FRP token was reused from the existing local configuration but was not printed or archived.

## Final Solution

`frpc-206.service` runs inside `vpnns`:

```text
ip netns exec vpnns /opt/frp/frpc -c /opt/frp/frpc-206.toml
```

Proxy mappings:

```text
hermes-webui-206: 127.0.0.1:39999 -> 47.236.151.116:30002
codex-mobile-206: 127.0.0.1:18923 -> 47.236.151.116:20002
```

## Verification

- `frpc-206.service` is enabled and active.
- FRP logs show both `hermes-webui-206` and `codex-mobile-206` started successfully.
- `frpc` process netns matches `/var/run/netns/vpnns`.
- `http://47.236.151.116:30002/health` returns HTTP 200.
- `http://47.236.151.116:20002/` returns HTTP 200.
- Application listeners remain `127.0.0.1:39999` and `127.0.0.1:18923` inside `vpnns`.
- No `0.0.0.0:39999` or `0.0.0.0:18923` listeners were found.

## Residual Risks

- External access depends on the remote FRP server and the reused FRP token remaining valid.
- Do not change the application bind addresses to `0.0.0.0`; external access should remain through FRP.

## Related Incidents

None.

## Extracted Knowledge

For this environment, target-side downloads from GitHub should be run through `vpnns-run` to avoid host-namespace connectivity timeouts.

## Sensitive Data Handling

The FRP auth token was read only to create the target config and was redacted from command output. No token, password, cookie, or auth file content is stored in this archive.
