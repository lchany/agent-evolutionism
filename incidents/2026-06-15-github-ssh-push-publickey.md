---
type: incident
date: 2026-06-15
title: "GitHub push fails without HTTPS credentials or SSH public key"
domain: git
topics: [github, ssh, git-push, publickey, https-auth]
status: verified
confidence: verified
sensitive: scrubbed
source_projects:
  - 2026-06-15-experience-vault-bootstrap.md
related_knowledge:
  - 2026-06-15-github-backed-codex-experience-vault.md
---

# GitHub Push Fails Without HTTPS Credentials Or SSH Public Key

## Trigger Signal

Git push to GitHub fails in a non-interactive server environment.

Common errors:

```text
fatal: could not read Username for 'https://github.com': No such device or address
git@github.com: Permission denied (publickey).
```

## Context

This occurred while pushing the initial Experience Vault repository from a headless Linux server to GitHub.

The HTTPS remote was configured first:

```text
https://github.com/lchany/agent-evolutionism.git
```

The environment had no interactive GitHub username/token prompt and no GitHub CLI login.

## Failed Command Or Operation

HTTPS push failed:

```bash
git -C /home/l30002999/experience-vault push -u origin main
```

SSH authentication test initially failed:

```bash
ssh -T -o BatchMode=yes git@github.com
```

## Error Signature

```text
fatal: could not read Username for 'https://github.com': No such device or address
git@github.com: Permission denied (publickey).
```

## Failed Attempts

1. Tried HTTPS push without available GitHub token input.
2. Tested SSH before the server public key was added to GitHub.

## Root Cause

GitHub authentication was not configured for the non-interactive server environment.

HTTPS required a username/token prompt that the environment could not provide. SSH failed because the server public key had not yet been registered in GitHub account settings.

## Resolution

1. Display the server SSH public key.
2. Add the public key to GitHub under `Settings -> SSH and GPG keys`.
3. Verify SSH authentication:

```bash
ssh -T -o BatchMode=yes git@github.com
```

Expected successful authentication message:

```text
Hi <user>! You've successfully authenticated, but GitHub does not provide shell access.
```

4. Switch the repository remote from HTTPS to SSH:

```bash
git -C /home/l30002999/experience-vault remote set-url origin git@github.com:lchany/agent-evolutionism.git
```

5. Push:

```bash
git -C /home/l30002999/experience-vault push -u origin main
```

## Verification

Push succeeded:

```text
To github.com:lchany/agent-evolutionism.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

## Reuse Notes

When GitHub push fails on a headless server:

1. Check if HTTPS remote is being used.
2. Check for an available GitHub token environment variable or GitHub CLI authentication.
3. If no token is available, prefer SSH.
4. Test SSH authentication with `ssh -T -o BatchMode=yes git@github.com`.
5. If SSH fails with `Permission denied (publickey)`, add the server public key to GitHub.
6. Change remote to SSH and push again.

## Non-Applicable Cases

- Not applicable if the repository is intentionally read-only.
- Not applicable if the GitHub account does not have write permission to the repository.
- Not applicable if the network blocks SSH to GitHub; in that case use HTTPS with a token or an approved proxy.
- Do not write private keys or tokens into Experience Vault.

## Sensitive Data Handling

No private key or token was stored. Only public key based workflow and generic command outputs were documented.
