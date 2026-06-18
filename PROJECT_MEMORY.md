# Project Memory

## User Corrections

- [2026-06-18] Skills are agent-client adaptable, not Codex-only
  Previous wrong assumption: `The bundled skills and restore docs can be framed as Codex-only skills.`
  Correct value: `The skill content is reusable agent capability. Installation and activation must be adapted per agent client, such as Codex, Claude Code, or another client.`
  Future rule: Do not hard-code general skill packaging or docs to Codex unless the user explicitly asks for Codex-only installation.
  Source: user correction
  Status: active

- [2026-06-18] Restore target directory must not be hard-coded
  Previous wrong assumption: `The restore guide can prescribe /home/l30002999/experience-vault as the fixed local path.`
  Correct value: `Ask the user for the restore directory first. If the user does not provide one, restore under the current working directory as ./experience-vault.`
  Future rule: Recovery docs and scripts should use a workspace variable such as EXPERIENCE_VAULT_DIR instead of fixed user-specific paths.
  Source: user correction
  Status: active

## Invalidated Assumptions

- [2026-06-18] Do not assume `~/.codex/skills` is the only valid skill installation target.
  Invalidated by: user correction that skills are not necessarily for Codex.
  Replacement: Use generic `agent-skills/` in the repository and describe client-specific installation targets separately.
  Status: active

- [2026-06-18] Do not assume `/home/l30002999/experience-vault` is the universal restore path.
  Invalidated by: user correction that the target directory may vary by environment and should be user-provided.
  Replacement: Use the user-provided directory, or the current working directory when no directory is provided.
  Status: active
