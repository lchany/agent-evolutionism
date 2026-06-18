---
type: knowledge
date: 2026-06-18
title: "Agent Skill Design And Operator Tuning Learning"
domain: npu-ascend
topics: [agent-skills, context-engineering, progressive-disclosure, decision-boundaries, vllm-ascend, operator-tuning, skill-evaluation]
applies_to: [codex-skills, opencode-skills, ascend-npu-workflows, vllm-ascend-skills]
confidence: tentative
risk: medium
source_projects:
  - projects/2026-06-18-agent-skill-design-and-operator-tuning-learning.md
source_incidents: []
last_verified: 2026-06-18
verified_status: user-provided-learning-not-executed
sensitive: reviewed
skill_candidate: false
---

# Agent Skill Design And Operator Tuning Learning

## Applicability

Use this knowledge when creating, refactoring, or evaluating Agent Skills, especially for Ascend/NPU, vLLM-Ascend, profiling, operator tuning, deployment, or model adaptation workflows.

It is most useful when a task involves a reusable process, a non-trivial decision loop, structured domain knowledge, scripts, references, and regression-style skill evaluation.

## Trigger Signals

- User asks to create, update, audit, or evaluate a skill.
- User mentions skill boundary, decision boundary, progressive disclosure, context budget, context engineering, or skill evaluation.
- User asks for Ascend/NPU operator tuning, profiling, CANN skills, vLLM-Ascend skills, model-lighting, or model adaptation skill design.
- A skill system shows overlapping triggers, duplicated orchestration layers, growing SKILL.md files, duplicated knowledge, or inconsistent execution paths.

## Required Inputs

- The target skill or proposed workflow.
- Example prompts that should and should not trigger the skill.
- Expected outputs and validation criteria.
- Known domain references, scripts, or repository links.
- Version constraints for domain knowledge when relevant, such as vLLM, vLLM-Ascend, CANN, torch_npu, hardware generation, or source commits.

## Procedure

Core design rules distilled from the user-provided material:

1. Cut skills by decision boundary, not by broad feature labels.
2. Require each skill to have an input-decision-output-validation loop.
3. Keep SKILL.md as routing, workflow, and resource index; move details into references.
4. Use scripts for deterministic, fragile, or frequently repeated steps.
5. Treat shared knowledge as versioned, topic-centered, and multi-view.
6. Keep model, hardware, and feature differences explicit through profiles and rules.
7. Add tests that cover triggers, negative controls, knowledge consistency, output structure, rule blocking, and key scenarios.
8. Evaluate skill quality with separate outcome, process, style, and efficiency dimensions.
9. Use real failures and user corrections as future regression cases.

For NPU/operator-tuning skills, inspect relevant external skill sources before creating local procedures:

- `https://gitcode.com/cann/skills`
- `https://gitcode.com/Ascend/agent-skills`
- `https://gitcode.com/Ascend/msagent`

## Non-Applicable Cases

- The task is a one-off command or simple factual answer.
- No repeatable process, decision logic, or output contract exists.
- The requested work is exploratory research without enough examples to define a stable skill.
- The only need is pure information retrieval; use memory/RAG/docs rather than a skill.

## Verification Method

Current verification status: tentative. The knowledge was distilled from user-provided material and has not yet been validated by building or evaluating a new skill in this workspace.

Future validation should include:

- Create or refactor one real skill using these boundaries.
- Keep SKILL.md under the intended budget and move variant details to references.
- Run skill validation tooling, if available.
- Test at least 10-20 prompts covering explicit, implicit, contextual, negative, ambiguity, and conflict cases.
- Inspect execution traces where available, for example JSONL traces from `opencode run <prompt> --format json`.

## Risk And Safety Notes

- Do not promote this knowledge to mature confidence until the workflow is exercised on a real task.
- Do not copy private/internal article text into public artifacts.
- Do not store credentials, private login details, raw auth files, or dense logs in skill references or the vault.
- Avoid broad skills that can modify too much state without clear side-effect boundaries.

## Source Evidence

- Local distilled source: `/home/l30002999/markdown-archive/20260618_agent_skill_design_learning_source.md`
- User-provided source themes:
  - Agent Skill design framework based on decision boundaries and context engineering.
  - vLLM-Ascend skill system design and shared knowledge practice.
  - OpenCode skill construction guide and model-lighting skill example.
  - Ascend/NPU automatic adaptation skill architecture.
  - Skill evaluator methodology with static and dynamic checks.
  - Operator tuning related repositories: CANN skills, Ascend agent-skills, msagent.

## Promotion Notes

Potential future promotions:

- Promote to a mature runbook after a real skill is created or refactored using this process and passes validation.
- Create a skill candidate for "agent-skill-evaluator" only after there is a working local evaluator or representative test dataset.
- Create an operator-tuning skill candidate only after inspecting the GitCode repositories and extracting verified Ascend/CANN procedures.

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: general-knowledge -> knowledge/
- Distill classification: runbook-candidate -> runbooks/
- Suggested domains: git-github, ssh, npu-ascend, profiling
