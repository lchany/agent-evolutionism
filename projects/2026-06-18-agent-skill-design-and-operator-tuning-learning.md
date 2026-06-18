---
type: project
date: 2026-06-18
title: "Agent Skill Design And Operator Tuning Learning"
domain: npu-ascend
topics: [agent-skills, skill-design, context-engineering, operator-tuning, profiling, skill-evaluation]
status: archived
sensitive: reviewed
related_incidents: []
extracted_knowledge:
  - knowledge/2026-06-18-agent-skill-design-and-operator-tuning-learning.md
---

# Agent Skill Design And Operator Tuning Learning

## Goal

Archive and summarize user-provided learning material about Agent Skill design, Ascend/NPU operator tuning skill sources, vLLM-Ascend skill system design, and skill evaluation methodology.

## Scope

In scope:

- Preserve a concise local learning source file.
- Extract reusable cross-project principles into Experience Vault knowledge.
- Create a tentative runbook for future skill design and evaluation.
- Record links to operator tuning skill repositories for later inspection.

Out of scope:

- Verify the external GitCode/Huawei JX resources.
- Install or modify active Codex/OpenCode skills.
- Promote any new official skill without future validation.

## Environment

- Workspace root: `/home/l30002999`
- Experience Vault: `/home/l30002999/experience-vault`
- Local source summary: `/home/l30002999/markdown-archive/20260618_agent_skill_design_learning_source.md`
- Date: 2026-06-18

## Timeline Summary

- User provided a large collection of Agent Skill design notes, OpenCode Skill construction guidance, vLLM-Ascend skill practice notes, model-lighting skill evaluation notes, and operator tuning related repositories.
- Project memory and Experience Vault instructions were loaded.
- Experience Vault `event project-start` was run to recall prior NPU/Ascend records.
- Prior records were classified as mostly background context, not directly reusable procedures for this learning archive.
- A concise learning source file was created under `markdown-archive/`.
- Experience Vault `review-turn` recommended a knowledge archive.
- Experience Vault `distill --create-drafts` created project, knowledge, and runbook drafts.

## Key Commands

```bash
python /home/l30002999/experience-vault/scripts/experience_vault.py event project-start \
  --objective "归档学习用户提供的 Agent Skill 设计、算子调优 Skill 信源和系统化评估经验" \
  --query "Agent Skill 设计 决策边界 渐进式披露 算子调优 Ascend CANN skills skill evaluator"

python /home/l30002999/experience-vault/scripts/experience_vault.py review-turn \
  --user-message "归档学习" \
  --assistant-summary "<summary>" \
  --title "Agent Skill Design And Operator Tuning Learning"

python /home/l30002999/experience-vault/scripts/experience_vault.py distill \
  --title "Agent Skill Design And Operator Tuning Learning" \
  --file /home/l30002999/markdown-archive/20260618_agent_skill_design_learning_source.md \
  --create-drafts
```

## Key Files

- `/home/l30002999/markdown-archive/20260618_agent_skill_design_learning_source.md`
- `/home/l30002999/experience-vault/projects/2026-06-18-agent-skill-design-and-operator-tuning-learning.md`
- `/home/l30002999/experience-vault/knowledge/2026-06-18-agent-skill-design-and-operator-tuning-learning.md`
- `/home/l30002999/experience-vault/runbooks/2026-06-18-agent-skill-design-and-operator-tuning-learning.md`

## Problems Encountered

- The source material is high-value but mostly user-provided design guidance rather than locally executed evidence.
- Some links point to external/internal resources that were not fetched or verified during this archive.
- Therefore reusable lessons should remain `tentative` until validated in real skill creation, operator tuning, or evaluation tasks.

## Final Solution

Created a compact learning archive and split it by scope:

- Project record: this file, documenting the archive activity.
- Knowledge card: reusable principles for Agent Skill boundaries, progressive disclosure, knowledge layering, testing, and NPU skill systems.
- Runbook draft: a tentative procedure for designing or evaluating a skill system using the learned framework.

## Verification

Verified:

- Experience Vault project-start recall ran successfully and pulled latest vault state.
- Experience Vault distill created the three draft records.
- Sensitive data review found no passwords, tokens, private keys, raw auth files, or dense sensitive logs in the summarized archive.

Not verified:

- External links and internal Huawei JX articles were not fetched.
- The CANN/Ascend/msagent repositories were not inspected.
- The runbook was not tested by building or evaluating a new skill.

## Residual Risks

- Some article claims may be outdated or context-specific.
- The runbook should not be treated as mature until it is validated on at least one real skill.
- The operator tuning repository links should be checked before using them as implementation references.

## Related Incidents

None.

## Extracted Knowledge

- `knowledge/2026-06-18-agent-skill-design-and-operator-tuning-learning.md`
- `runbooks/2026-06-18-agent-skill-design-and-operator-tuning-learning.md`

## Sensitive Data Handling

The archive contains public or user-provided learning summaries and repository/article links. No secrets, credentials, raw authentication files, or dense sensitive logs were stored.

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: general-knowledge -> knowledge/
- Distill classification: runbook-candidate -> runbooks/
- Suggested domains: git-github, ssh, npu-ascend, profiling
