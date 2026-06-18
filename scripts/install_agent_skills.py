#!/usr/bin/env python3
"""Install bundled agent skills from this repository."""

from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILLS_SOURCE = ROOT / "agent-skills"
AGENTS_TEMPLATE = ROOT / "templates" / "AGENTS.md"


def default_agent_home() -> Path:
    return Path(os.environ.get("AGENT_HOME", os.environ.get("CODEX_HOME", Path.home() / ".codex"))).expanduser()


def copy_tree(source: Path, destination: Path, force: bool) -> None:
    if destination.exists():
        if not force:
            raise FileExistsError(f"{destination} already exists; rerun with --force to replace it")
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def install_skills(target: Path, force: bool) -> list[Path]:
    if not SKILLS_SOURCE.is_dir():
        raise FileNotFoundError(f"Missing bundled skills directory: {SKILLS_SOURCE}")

    target.mkdir(parents=True, exist_ok=True)
    installed: list[Path] = []
    for skill_dir in sorted(path for path in SKILLS_SOURCE.iterdir() if path.is_dir()):
        if not (skill_dir / "SKILL.md").is_file():
            continue
        destination = target / skill_dir.name
        copy_tree(skill_dir, destination, force)
        installed.append(destination)
    return installed


def install_agents(path: Path, force: bool) -> Path:
    if not AGENTS_TEMPLATE.is_file():
        raise FileNotFoundError(f"Missing AGENTS template: {AGENTS_TEMPLATE}")
    if path.exists() and not force:
        raise FileExistsError(f"{path} already exists; rerun with --force to replace it")
    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(AGENTS_TEMPLATE, path)
    return path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent-home", type=Path, default=default_agent_home())
    parser.add_argument("--codex-home", type=Path, help="Backward-compatible alias for --agent-home")
    parser.add_argument("--force", action="store_true", help="Replace existing installed skills or AGENTS.md")
    parser.add_argument("--skip-agents", action="store_true", help="Do not install the user-level AGENTS.md template")
    parser.add_argument("--agents-path", type=Path, help="Override AGENTS.md install path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    agent_home = (args.codex_home or args.agent_home).expanduser()
    skills_target = agent_home / "skills"
    installed = install_skills(skills_target, args.force)

    print("Installed agent skills:")
    for path in installed:
        print(f"- {path}")

    if args.skip_agents:
        print("Skipped AGENTS.md install.")
        return 0

    agents_path = (args.agents_path or (agent_home / "AGENTS.md")).expanduser()
    installed_agents = install_agents(agents_path, args.force)
    print(f"Installed user rules: {installed_agents}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
