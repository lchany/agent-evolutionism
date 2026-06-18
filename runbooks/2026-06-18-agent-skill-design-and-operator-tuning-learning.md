---
type: runbook
date: 2026-06-18
title: "Agent Skill Design And Operator Tuning Learning"
domain: npu-ascend
topics: [agent-skills, skill-design, skill-evaluation, progressive-disclosure, operator-tuning]
confidence: tentative
risk: medium
source_knowledge:
  - knowledge/2026-06-18-agent-skill-design-and-operator-tuning-learning.md
source_incidents: []
verified_status: unvalidated-runbook-candidate
sensitive: reviewed
skill_candidate: false
---

# Agent Skill Design And Operator Tuning Learning

## When To Use

Use this tentative runbook when designing, refactoring, or evaluating an Agent Skill system, especially for Ascend/NPU operator tuning, profiling, vLLM-Ascend workflows, model adaptation, or deployment automation.

Do not treat this as a mature runbook yet. It is a structured procedure distilled from user-provided learning material and must be validated on a real skill before promotion.

## Required Inputs

- Target skill name or workflow name.
- 5-10 realistic positive prompts.
- 3-5 negative prompts that should not trigger the skill.
- Expected outputs and validation criteria.
- Known references, scripts, assets, domain docs, and repository links.
- Version constraints and source commits for domain-specific facts when relevant.

## Procedure

1. Define the user intent boundary.
   - Classify the request as high-level orchestration, mid-level skill, or low-level helper/tool.
   - Create a standalone skill only when the workflow is repeatable, has decision logic, and outputs have independent value.

2. Map decision loops.
   - Write the expected loop as `input -> decision -> output -> validation`.
   - Split skills when the decisions, outputs, or side effects differ.
   - Merge tiny helpers into scripts when management overhead exceeds reuse value.

3. Set the architecture layer.
   - Entry skills route and summarize.
   - Composer/orchestrator skills coordinate multiple atomic skills.
   - Atomic skills solve one narrow, verifiable problem.
   - Tool skills/scripts provide deterministic execution such as SSH, parsing, rendering, or validation.

4. Design progressive disclosure.
   - Put only metadata, triggers, workflow, key decisions, and reference index in SKILL.md.
   - Move detailed examples, domain facts, variants, and rules into references.
   - Move fragile repeated execution into scripts.
   - Avoid duplicating the same fact in SKILL.md and references.

5. Version and index shared knowledge.
   - Record applicable versions, source commits, last verification, watch files, and freshness.
   - Use topic-centered knowledge with core, deployment view, development view, and edge cases.
   - For NPU/Ascend work, keep hardware and CANN/torch_npu/vLLM differences explicit.

6. Define output contracts and side-effect boundaries.
   - State what files, reports, patches, commands, or metrics the skill produces.
   - State which directories, repositories, remote hosts, or containers it may modify.
   - Define failure handling and retry boundaries.

7. Create or update tests.
   - Include explicit, implicit, contextual, negative, ambiguity, conflict, version-boundary, and regression examples.
   - Prefer dry-run tests for expensive or risky workflows.
   - Avoid tests that require interactive input unless the evaluator supports it.

8. Evaluate behavior.
   - Check outcome: expected artifact or result exists.
   - Check process: expected skill/tool/phase sequence appears.
   - Check style: output format follows the contract.
   - Check efficiency: time, tokens, command count, and tool count are reasonable.
   - Where available, inspect structured traces such as `opencode run <prompt> --format json`.

9. Iterate from failures.
   - Convert real failures into regression tests.
   - Fix trigger descriptions when false positives or false negatives occur.
   - Move bloated SKILL.md material into references.
   - Promote stable repeated procedures to mature runbooks or skill candidates only after validation.

## Validation

Minimum validation before promoting this runbook:

- Apply it to at least one real skill creation or refactor.
- Validate the skill folder with the platform's validator, if available.
- Run a representative test set with both positive and negative prompts.
- Confirm that the skill can find needed references without preloading irrelevant detail.
- Confirm that failure handling and side-effect boundaries are explicit.

For Ascend/operator-tuning work, additionally inspect and cite the relevant procedures from:

- `https://gitcode.com/cann/skills`
- `https://gitcode.com/Ascend/agent-skills`
- `https://gitcode.com/Ascend/msagent`

## Failure Handling

- If triggers overlap with existing skills, sharpen the description and add negative examples.
- If SKILL.md approaches 500 lines or becomes hard to scan, split details into references.
- If deterministic steps are repeatedly rewritten, move them into scripts.
- If a test requires user interaction and times out, rewrite it as a complete prompt or dry-run test.
- If a skill changes code, environments, remote hosts, or containers without a side-effect contract, stop and define the boundary before continuing.

## Non-Applicable Cases

- One-off commands.
- Pure knowledge lookup with no process or decision logic.
- Early exploration where the workflow and success criteria are not yet stable.
- Tasks where existing tools or scripts are enough and a skill would only add maintenance overhead.

## Related Knowledge

- `knowledge/2026-06-18-agent-skill-design-and-operator-tuning-learning.md`

## Skill Promotion Notes

Potential future skill candidates:

- Agent Skill evaluator: once a local evaluator, trace format, and test dataset are available.
- Ascend operator tuning skill: after inspecting CANN/Ascend/msagent repositories and validating a repeatable tuning/profiling workflow.
- vLLM-Ascend skill refactor guide: after applying the decision-boundary framework to a real vLLM-Ascend skill tree.

## Distill Guidance

- Distill classification: project-specific -> projects/
- Distill classification: general-knowledge -> knowledge/
- Distill classification: runbook-candidate -> runbooks/
- Suggested domains: git-github, ssh, npu-ascend, profiling
