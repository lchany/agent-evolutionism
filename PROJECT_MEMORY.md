# Project Memory

## User Corrections

- [2026-06-29] Cross-project implementation reuse must be blocked by default
  Previous wrong assumption: `A high-scoring Experience Vault record from project B can be automatically learned and reused as an implementation plan for project A when keywords match.`
  Correct value: `Project-specific implementation plans, environment choices, and optimization tactics from one project must not be applied to another project by default. They are background evidence only unless the current project matches the recorded applicability boundary, required inputs, environment, topology, and non-applicable cases, or the lesson has been explicitly promoted to verified cross-project knowledge/runbook with clear boundaries.`
  Future rule: During project-start or incident recall, treat `projects/` records as context and provenance, not directly reusable plans. Reuse only verified `knowledge/` or `runbooks/` records whose applicability and non-applicable cases match the current project; otherwise ask for confirmation or proceed with project-local validation.
  Source: user correction
  Status: active

- [2026-06-26] A3 Qwen3-VL-8B verl/FSDP/Yuanrong record is a directly reusable conclusion
  Previous wrong assumption: `The archived record should be framed like a user-provided operational log that may still need rerun verification before reuse.`
  Correct value: `The user explicitly stated this record is a directly usable conclusion. Archive wording must treat it as an already debugged, reusable conclusion; only the archival agent did not rerun the training.`
  Future rule: For this A3 Qwen3-VL-8B verl/FSDP/Yuanrong record, do not downgrade confidence to a tentative note. Preserve it as a verified, directly reusable conclusion while still noting that the archive step itself did not execute a new run.
  Source: user correction
  Status: active

- [2026-06-18] Skills are agent-client adaptable, not Codex-only
  Previous wrong assumption: `The bundled skills and restore docs can be framed as Codex-only skills.`
  Correct value: `The skill content is reusable agent capability. Installation and activation must be adapted per agent client, such as Codex, Claude Code, or another client.`
  Future rule: Do not hard-code general skill packaging or docs to Codex unless the user explicitly asks for Codex-only installation.
  Source: user correction
  Status: active

- [2026-06-18] Do not archive unverified root-cause analysis as reusable experience
  Previous wrong assumption: `After an error is diagnosed, the system can immediately archive the finding as reusable incident/knowledge/runbook material.`
  Correct value: `A root cause must be tested and confirmed before it becomes reusable experience. Unverified analysis should stay in active context or a project checkpoint marked unverified.`
  Future rule: Require actual validation evidence before creating incident, knowledge, runbook, or skill-candidate records.
  Source: user correction
  Status: active

- [2026-06-18] Restore target directory must not be hard-coded
  Previous wrong assumption: `The restore guide can prescribe /home/l30002999/experience-vault as the fixed local path.`
  Correct value: `Ask the user for the restore directory first. If the user does not provide one, restore under the current working directory as ./experience-vault.`
  Future rule: Recovery docs and scripts should use a workspace variable such as EXPERIENCE_VAULT_DIR instead of fixed user-specific paths.
  Source: user correction
  Status: active

- [2026-06-18] User-provided facts must be classified by scope
  Previous wrong assumption: `A fact provided by the user can be stored directly as durable general experience.`
  Correct value: `User facts must first be classified as project-specific or generally reusable. Project-specific facts belong in PROJECT_MEMORY.md or project archives; only cross-project, verified facts belong in reusable knowledge/runbooks.`
  Future rule: Before archiving user facts, explicitly decide whether they are project-local, general reusable, mixed, or unknown.
  Source: user correction
  Status: active

- [2026-06-23] Hard future constraints must be promoted above vault search
  Previous wrong assumption: `A future-facing user rule can be stored as Experience Vault knowledge and reliably found later by keyword retrieval.`
  Correct value: `Rules phrased as future/always/must/never constraints need to be stored in active user rules, a dedicated skill, or project memory before optional vault archival.`
  Future rule: For durable user instructions, update the highest-priority active rule layer first; use Experience Vault knowledge as supporting evidence, not the only enforcement layer.
  Source: user correction
  Status: active

## Invalidated Assumptions

- [2026-06-29] Do not automatically apply project B optimization plans to project A.
  Invalidated by: user correction that cross-project leakage caused project A validation to deviate from expectations.
  Replacement: Project archives are recall context only; implementation reuse requires a matching applicability boundary or a verified promoted knowledge/runbook record.
  Status: active

- [2026-06-26] Do not frame the A3 Qwen3-VL-8B verl/FSDP/Yuanrong record as requiring fresh validation before reuse.
  Invalidated by: user correction that the record is a directly usable conclusion.
  Replacement: Treat the recorded flow and root causes as verified reusable experience for the stated topology; only revalidate when topology, versions, or parameters materially change.
  Status: active

- [2026-06-18] Do not assume `~/.codex/skills` is the only valid skill installation target.
  Invalidated by: user correction that skills are not necessarily for Codex.
  Replacement: Use generic `agent-skills/` in the repository and describe client-specific installation targets separately.
  Status: active

- [2026-06-18] Do not treat root-cause diagnosis as validated experience.
  Invalidated by: user correction that diagnosis alone is insufficient for archiving.
  Replacement: Gate reusable archive creation on explicit test or verification evidence.
  Status: active

- [2026-06-18] Do not assume `/home/l30002999/experience-vault` is the universal restore path.
  Invalidated by: user correction that the target directory may vary by environment and should be user-provided.
  Replacement: Use the user-provided directory, or the current working directory when no directory is provided.
  Status: active

- [2026-06-18] Do not treat all user-provided facts as general knowledge.
  Invalidated by: user correction that facts may be project-specific or general.
  Replacement: Route project-specific facts to project memory or project archives; route only verified cross-project facts to reusable knowledge.
  Status: active

- [2026-06-23] Do not rely on keyword recall for hard future rules.
  Invalidated by: user concern that rules such as future container mount requirements are unlikely to trigger reliably if stored only as knowledge.
  Replacement: Promote hard future rules into user rules, dedicated skills, or project memory, then archive evidence in Experience Vault if useful.
  Status: active
