#!/usr/bin/env python3
"""Experience Vault helper CLI.

This script is intentionally dependency-free. It provides deterministic
Markdown search, template creation, validation, and Git status helpers.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_DIRS = [
    "projects",
    "incidents",
    "knowledge",
    "runbooks",
    "skill-candidates",
    "evals",
    "index",
    "templates",
]

SEARCH_ORDER = {
    "project-start": ["runbooks", "knowledge", "incidents", "projects"],
    "incident": ["incidents", "knowledge", "runbooks", "projects"],
    "promotion": ["knowledge", "runbooks", "incidents", "projects", "evals"],
}

TEMPLATE_BY_TYPE = {
    "project": ("templates/project.md", "projects"),
    "incident": ("templates/incident.md", "incidents"),
    "knowledge": ("templates/knowledge.md", "knowledge"),
    "runbook": ("templates/runbook.md", "runbooks"),
}

USER_AGENTS_PATH = Path("/root/.codex/AGENTS.md")
ACTIVE_SKILL_PATH = Path("/home/l30002999/.codex/skills/experience-vault/SKILL.md")

SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9_]{20,}"),
    re.compile(r"ghu_[A-Za-z0-9_]{20,}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"Bearer\s+\S{20,}", re.IGNORECASE),
    re.compile(r"-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----", re.IGNORECASE),
    re.compile(r"\b(password|passwd|secret|token)\s*[=:]\s*[^\s<>`]+", re.IGNORECASE),
    re.compile(r"\b(OPENAI_API_KEY|ANTHROPIC_API_KEY|OPENROUTER_API_KEY|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY)\b"),
]


@dataclass
class SearchHit:
    path: Path
    score: int
    title: str
    record_type: str
    confidence: str
    matched_terms: list[str]


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", text)
    text = text.strip("-")
    return text or "untitled"


def tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"[^A-Za-z0-9\u4e00-\u9fff]+", text.lower()) if len(t) >= 2]


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    fields: dict[str, str] = {}
    for line in parts[1].splitlines():
        if ":" not in line or line.startswith(" "):
            continue
        key, value = line.split(":", 1)
        fields[key.strip()] = value.strip().strip("'\"")
    return fields


def has_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def iter_markdown(dirs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for dirname in dirs:
        base = ROOT / dirname
        if not base.exists():
            continue
        paths.extend(sorted(base.rglob("*.md")))
    return paths


def classify(score: int, confidence: str) -> str:
    if score >= 8 and confidence in {"verified", "mature"}:
        return "directly applicable"
    if score >= 5:
        return "partially applicable"
    return "not applicable"


def search_records(query: str, mode: str, limit: int) -> list[SearchHit]:
    terms = tokenize(query)
    if not terms:
        return []

    dirs = SEARCH_ORDER[mode]
    hits: list[SearchHit] = []
    for path in iter_markdown(dirs):
        text = path.read_text(encoding="utf-8", errors="ignore")
        frontmatter = parse_frontmatter(text)
        haystack = f"{path.name}\n{text}".lower()
        matched = [term for term in terms if term in haystack]
        if not matched:
            continue
        score = len(matched) * 2
        if any(term in path.name.lower() for term in matched):
            score += 3
        topics = frontmatter.get("topics", "").lower()
        if any(term in topics for term in matched):
            score += 2
        title = frontmatter.get("title") or path.stem
        hits.append(
            SearchHit(
                path=path,
                score=score,
                title=title,
                record_type=frontmatter.get("type", "unknown"),
                confidence=frontmatter.get("confidence", "unknown"),
                matched_terms=matched,
            )
        )

    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]


def print_search_hit(hit: SearchHit) -> None:
    relative = hit.path.relative_to(ROOT)
    applicability = classify(hit.score, hit.confidence)
    print(f"- {hit.title} ({relative})")
    print(f"  type: {hit.record_type}; confidence: {hit.confidence}; score: {hit.score}")
    print(f"  matched: {', '.join(hit.matched_terms)}")
    print(f"  initial_applicability: {applicability}")


def command_search(args: argparse.Namespace) -> int:
    if not tokenize(args.query):
        print("No searchable terms provided.", file=sys.stderr)
        return 2
    hits = search_records(args.query, args.mode, args.limit)
    if not hits:
        print("No relevant Experience Vault records found.")
        return 0

    for hit in hits:
        print_search_hit(hit)
    return 0


def command_recall(args: argparse.Namespace) -> int:
    if not tokenize(args.query):
        print("No searchable terms provided.", file=sys.stderr)
        return 2
    hits = search_records(args.query, args.mode, args.limit)
    if not hits:
        print("No relevant Experience Vault records found.")
        print("\nNext action: proceed normally, then archive any reusable lesson if the task produces one.")
        return 0

    buckets = {
        "directly applicable": [],
        "partially applicable": [],
        "not applicable": [],
    }
    for hit in hits:
        buckets[classify(hit.score, hit.confidence)].append(hit)

    for label in ["directly applicable", "partially applicable", "not applicable"]:
        print(f"{label.title()}:")
        if not buckets[label]:
            print("- None")
            continue
        for hit in buckets[label]:
            relative = hit.path.relative_to(ROOT)
            print(f"- {hit.title} ({relative})")
            print(f"  evidence: type={hit.record_type}, confidence={hit.confidence}, matched={', '.join(hit.matched_terms)}")

    print("\nApplicability checklist:")
    print("- Verify current trigger signals match the record.")
    print("- Confirm required inputs and environment compatibility.")
    print("- Check non-applicable cases before reusing steps.")
    print("- Treat partial matches as guidance, not a command script.")

    if buckets["directly applicable"]:
        print("\nNext action: use the directly applicable record(s) as the first plan input.")
    elif buckets["partially applicable"]:
        print("\nNext action: adapt only the reusable parts from partial matches.")
    else:
        print("\nNext action: do not reuse these records; proceed normally and archive new evidence if useful.")
    return 0


def render_template(template: str, title: str) -> str:
    skill_name = slugify(title)
    return (
        template.replace("{{date}}", date.today().isoformat())
        .replace("{{title}}", title)
        .replace("{{skill_name}}", skill_name)
        .replace("{{description}}", f"Candidate Codex skill for {title}.")
    )


def command_new(args: argparse.Namespace) -> int:
    template_path, output_dir = TEMPLATE_BY_TYPE[args.type]
    template = (ROOT / template_path).read_text(encoding="utf-8")
    slug = args.slug or slugify(args.title)
    output = ROOT / output_dir / f"{date.today().isoformat()}-{slug}.md"
    if output.exists() and not args.force:
        print(f"Refusing to overwrite existing file: {output}", file=sys.stderr)
        return 2
    output.write_text(render_template(template, args.title), encoding="utf-8")
    print(output.relative_to(ROOT))
    return 0


def command_archive(args: argparse.Namespace) -> int:
    created: list[Path] = []
    for record_type in args.type:
        template_path, output_dir = TEMPLATE_BY_TYPE[record_type]
        template = (ROOT / template_path).read_text(encoding="utf-8")
        slug = args.slug or slugify(args.title)
        output = ROOT / output_dir / f"{date.today().isoformat()}-{slug}.md"
        if output.exists() and not args.force:
            print(f"Refusing to overwrite existing file: {output}", file=sys.stderr)
            return 2
        output.write_text(render_template(template, args.title), encoding="utf-8")
        created.append(output)

    print("Created archive draft(s):")
    for path in created:
        print(f"- {path.relative_to(ROOT)}")
    print("\nNext steps:")
    print("- Fill in the draft sections with verified facts.")
    print("- Run: python scripts/experience_vault.py validate")
    print("- Run: python scripts/experience_vault.py sync --message \"Archive <topic>\"")
    return 0


def validate_structure() -> list[str]:
    errors: list[str] = []
    for dirname in REQUIRED_DIRS:
        if not (ROOT / dirname).is_dir():
            errors.append(f"Missing directory: {dirname}")
    return errors


def validate_markdown() -> list[str]:
    errors: list[str] = []
    for path in iter_markdown(["projects", "incidents", "knowledge", "runbooks"]):
        text = path.read_text(encoding="utf-8", errors="ignore")
        frontmatter = parse_frontmatter(text)
        if not frontmatter:
            errors.append(f"Missing frontmatter: {path.relative_to(ROOT)}")
            continue
        for required in ["type", "date", "title"]:
            if required not in frontmatter:
                errors.append(f"Missing {required}: {path.relative_to(ROOT)}")
        if has_secret(text):
            errors.append(f"Potential secret found: {path.relative_to(ROOT)}")
    return errors


def command_validate(args: argparse.Namespace) -> int:
    errors = validate_structure() + validate_markdown()
    if errors:
        print("Experience Vault validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Experience Vault validation passed.")
    return 0


def run_capture(cmd: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)


def command_git_status(args: argparse.Namespace) -> int:
    if not (ROOT / ".git").exists():
        print("Git repository is not initialized.")
        print("Run: git init")
        print("Then add a private GitHub remote before durable use.")
        return 0
    result = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True)
    print(result.stdout.strip() or "Working tree clean.")
    return result.returncode


def has_remote() -> bool:
    result = subprocess.run(["git", "remote"], cwd=ROOT, text=True, capture_output=True)
    return bool(result.stdout.strip())


def command_doctor(args: argparse.Namespace) -> int:
    checks: list[tuple[str, bool, str]] = []
    checks.append(("vault directory", ROOT.is_dir(), str(ROOT)))
    checks.append(("git repository", (ROOT / ".git").is_dir(), str(ROOT / ".git")))
    checks.append(("git remote", has_remote(), "configured" if has_remote() else "missing"))
    checks.append(("user-level AGENTS.md", USER_AGENTS_PATH.exists(), str(USER_AGENTS_PATH)))
    checks.append(("active experience-vault skill", ACTIVE_SKILL_PATH.exists(), str(ACTIVE_SKILL_PATH)))

    validation_errors = validate_structure() + validate_markdown()
    checks.append(("vault validation", not validation_errors, "; ".join(validation_errors) if validation_errors else "passed"))

    if (ROOT / ".git").is_dir():
        status = run_capture(["git", "status", "--short"])
        clean = status.returncode == 0 and not status.stdout.strip()
        checks.append(("git working tree", clean, "clean" if clean else "has changes"))

    failed = False
    for name, ok, detail in checks:
        marker = "OK" if ok else "FAIL"
        print(f"[{marker}] {name}: {detail}")
        failed = failed or not ok
    return 1 if failed else 0


def command_git_pull(args: argparse.Namespace) -> int:
    if not (ROOT / ".git").exists():
        print("Git repository is not initialized.")
        return 1
    if not has_remote():
        print("No Git remote configured. Add a private GitHub remote before pull/push.")
        return 0
    result = subprocess.run(["git", "pull", "--ff-only"], cwd=ROOT, text=True)
    return result.returncode


def command_git_review(args: argparse.Namespace) -> int:
    if not (ROOT / ".git").exists():
        print("Git repository is not initialized.")
        return 1
    status = subprocess.run(["git", "status", "--short"], cwd=ROOT, text=True, capture_output=True)
    print("Changed files:")
    print(status.stdout.strip() or "Working tree clean.")
    diff = subprocess.run(["git", "diff", "--stat"], cwd=ROOT, text=True, capture_output=True)
    if diff.stdout.strip():
        print("\nDiff stat:")
        print(diff.stdout.strip())
    return status.returncode or diff.returncode


def command_sync(args: argparse.Namespace) -> int:
    if not (ROOT / ".git").exists():
        print("Git repository is not initialized.", file=sys.stderr)
        return 1
    if args.pull and has_remote():
        pull = subprocess.run(["git", "pull", "--ff-only"], cwd=ROOT, text=True)
        if pull.returncode != 0:
            return pull.returncode

    errors = validate_structure() + validate_markdown()
    if errors:
        print("Refusing to sync because validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    review = command_git_review(argparse.Namespace())
    status = run_capture(["git", "status", "--short"])
    if status.returncode != 0:
        return status.returncode
    if not status.stdout.strip():
        print("No changes to sync.")
        return review

    if args.dry_run:
        print("Dry run: not committing or pushing.")
        return review

    subprocess.run(["git", "add", "."], cwd=ROOT, check=True)
    commit = subprocess.run(["git", "commit", "-m", args.message], cwd=ROOT, text=True)
    if commit.returncode != 0:
        return commit.returncode
    if args.push:
        if not has_remote():
            print("Committed locally, but no remote is configured.")
            return 0
        push = subprocess.run(["git", "push"], cwd=ROOT, text=True)
        return push.returncode
    print("Committed locally. Push skipped by --no-push.")
    return 0


def command_redact_check(args: argparse.Namespace) -> int:
    text = Path(args.path).read_text(encoding="utf-8", errors="ignore")
    if has_secret(text):
        print(f"Potential secret found in {args.path}")
        return 1
    print(f"No obvious secret patterns found in {args.path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="Search experience records")
    search.add_argument("--query", required=True)
    search.add_argument("--mode", choices=sorted(SEARCH_ORDER), default="project-start")
    search.add_argument("--limit", type=int, default=5)
    search.set_defaults(func=command_search)

    recall = sub.add_parser("recall", help="Search and group records by applicability")
    recall.add_argument("--query", required=True)
    recall.add_argument("--mode", choices=sorted(SEARCH_ORDER), default="project-start")
    recall.add_argument("--limit", type=int, default=5)
    recall.set_defaults(func=command_recall)

    new = sub.add_parser("new", help="Create a record from a template")
    new.add_argument("--type", choices=sorted(TEMPLATE_BY_TYPE), required=True)
    new.add_argument("--title", required=True)
    new.add_argument("--slug")
    new.add_argument("--force", action="store_true")
    new.set_defaults(func=command_new)

    archive = sub.add_parser("archive", help="Create one or more archive drafts")
    archive.add_argument("--title", required=True)
    archive.add_argument("--type", choices=sorted(TEMPLATE_BY_TYPE), action="append", required=True)
    archive.add_argument("--slug")
    archive.add_argument("--force", action="store_true")
    archive.set_defaults(func=command_archive)

    validate = sub.add_parser("validate", help="Validate repository structure and hygiene")
    validate.set_defaults(func=command_validate)

    doctor = sub.add_parser("doctor", help="Check Experience Vault health")
    doctor.set_defaults(func=command_doctor)

    git_status = sub.add_parser("git-status", help="Show Git status")
    git_status.set_defaults(func=command_git_status)

    git_pull = sub.add_parser("git-pull", help="Pull from configured Git remote")
    git_pull.set_defaults(func=command_git_pull)

    git_review = sub.add_parser("git-review", help="Show changed files and diff stat")
    git_review.set_defaults(func=command_git_review)

    sync = sub.add_parser("sync", help="Validate, review, commit, and optionally push")
    sync.add_argument("--message", required=True, help="Commit message")
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--no-pull", dest="pull", action="store_false")
    sync.add_argument("--no-push", dest="push", action="store_false")
    sync.set_defaults(func=command_sync, pull=True, push=True)

    redact = sub.add_parser("redact-check", help="Scan a file for obvious secret patterns")
    redact.add_argument("path")
    redact.set_defaults(func=command_redact_check)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
