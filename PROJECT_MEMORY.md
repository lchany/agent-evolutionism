# Project Memory

## User Corrections

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
