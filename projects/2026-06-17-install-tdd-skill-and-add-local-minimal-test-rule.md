---
type: project
date: 2026-06-17
title: "Install TDD skill and add local minimal test rule"
domain: agent-skills
topics: [tdd, testing, agents-md, local-validation]
status: verified
sensitive: no
related_incidents: []
extracted_knowledge: []
---

# Install TDD skill and add local minimal test rule

## Goal

Install a TDD-oriented agent skill and persist a project-level operating rule that favors reproducing end-to-end failures with the smallest local automated test before changing production code.

## Scope

- Installed the `mattpocock/skills@tdd` skill for the current agent user.
- Created `/home/l30002999/AGENTS.md` because no file existed there.
- Preserved the user's Experience Vault and Python code-review rules in the new `AGENTS.md`.
- Added a `Local Minimal Test First` section to guide future coding work.

## Environment

- Workspace: `/home/l30002999`
- Shell user: `root`
- Skill install destination verified at `/root/.agents/skills/tdd`
- Project rules file created at `/home/l30002999/AGENTS.md`

## Timeline Summary

1. Searched installable skills for TDD and selected `mattpocock/skills@tdd` based on relevance and quality signals.
2. Ran `npx skills add mattpocock/skills@tdd -g -y`.
3. Confirmed the installer copied the skill under `/root/.agents/skills/tdd`.
4. Found that `/home/l30002999/AGENTS.md` did not exist.
5. Created `/home/l30002999/AGENTS.md` with the user's operating rules and a new local-minimal-test-first rule.
6. Verified the new AGENTS file and the installed TDD skill files.

## Key Commands

- `npx skills add mattpocock/skills@tdd -g -y`
- `sed -n '1,260p' /home/l30002999/AGENTS.md`
- `sed -n '1,180p' /root/.agents/skills/tdd/SKILL.md`
- `ls -la /root/.agents/skills/tdd /home/l30002999/AGENTS.md`

## Key Files

- `/home/l30002999/AGENTS.md`
- `/root/.agents/skills/tdd/SKILL.md`
- `/root/.agents/skills/tdd/tests.md`
- `/root/.agents/skills/tdd/mocking.md`
- `/root/.agents/skills/tdd/interface-design.md`
- `/root/.agents/skills/tdd/deep-modules.md`
- `/root/.agents/skills/tdd/refactoring.md`

## Problems Encountered

- `/home/l30002999/AGENTS.md` did not exist, so a new file was created.
- The skill installer reported: `PromptScript does not support global skill installation`. The same install still copied the TDD skill for the active agent user.
- Initial lookup under `/home/l30002999/.agents/skills/tdd` failed because the current shell user is `root`; the actual install path was `/root/.agents/skills/tdd`.
- Experience Vault archive initially refused to write because unrelated untracked vault drafts already existed. After reviewing `git status --short`, archive creation continued with `--no-pull`.

## Final Solution

The TDD skill is installed for the active agent user, and `/home/l30002999/AGENTS.md` now contains a `Local Minimal Test First` rule:

- Prefer reproducing bugs or behavior changes with the smallest local automated test before production changes.
- Reduce E2E-discovered failures into unit, integration, component, or minimal local tests when possible.
- Verify the smaller test fails for the expected reason, implement the fix, make it pass, then run the broader E2E test as confirmation.
- Prefer observable behavior through public interfaces over mocks, private implementation details, or internal structure.

## Verification

- Verified `/home/l30002999/AGENTS.md` exists and contains the new rule.
- Verified `/root/.agents/skills/tdd/SKILL.md` exists and describes Red-Green-Refactor, behavior-oriented tests, and public-interface testing.
- Verified the installed skill directory contains the expected supporting files.

## Residual Risks

- The installed skill is under `/root/.agents/skills/tdd` because the active shell user is `root`. If a future agent session runs as `l30002999`, it may need the same skill installed under that user's home.
- The installer reported PromptScript global installation is unsupported, so PromptScript-specific surfaces may not see the skill.
- Existing unrelated Experience Vault drafts were left untouched.

## Related Incidents

- None.

## Extracted Knowledge

- None promoted. This was project-specific setup.

## Sensitive Data Handling

- No passwords, API keys, tokens, private keys, raw auth files, or dense logs were stored.
