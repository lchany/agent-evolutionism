#!/usr/bin/env python3
"""Experience Vault helper CLI.

This script is intentionally dependency-free. It provides deterministic
Markdown search, template creation, validation, and Git status helpers.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
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

DISTILL_RECORD_TYPES = ["project", "incident", "knowledge", "runbook"]

DISTILL_RULES = {
    "project": {
        "label": "Project Archive",
        "classification": "project-specific",
        "destination": "projects/",
        "signals": [
            "project",
            "repo",
            "repository",
            "path",
            "environment",
            "milestone",
            "deliverable",
            "final solution",
            "scope",
            "项目",
            "仓库",
            "路径",
            "环境",
            "交付",
            "完成",
        ],
        "description": "Current-project goals, environment, timeline, decisions, verification, and residual risks.",
    },
    "incident": {
        "label": "Incident Candidate",
        "classification": "reusable-incident",
        "destination": "incidents/",
        "signals": [
            "error",
            "failure",
            "failed",
            "exception",
            "traceback",
            "permission denied",
            "publickey",
            "root cause",
            "resolution",
            "fix",
            "retry",
            "错误",
            "失败",
            "报错",
            "根因",
            "修复",
            "解决",
        ],
        "description": "Reusable failure with trigger, signature, root cause, resolution, verification, and non-applicable cases.",
    },
    "knowledge": {
        "label": "Knowledge Candidate",
        "classification": "general-knowledge",
        "destination": "knowledge/",
        "signals": [
            "reusable",
            "lesson",
            "knowledge",
            "best practice",
            "avoid",
            "should",
            "general",
            "portable",
            "across projects",
            "multiple projects",
            "next time",
            "复用",
            "经验",
            "知识",
            "通用",
            "原则",
            "下次",
            "避免",
        ],
        "description": "Cross-project lesson with applicability, trigger signals, required inputs, procedure, and boundaries.",
    },
    "runbook": {
        "label": "Runbook Candidate",
        "classification": "runbook-candidate",
        "destination": "runbooks/",
        "signals": [
            "runbook",
            "workflow",
            "procedure",
            "checklist",
            "step",
            "steps",
            "validate",
            "verification",
            "repeatable",
            "流程",
            "步骤",
            "检查",
            "验证",
            "可重复",
            "操作手册",
        ],
        "description": "Repeatable procedure with inputs, ordered steps, validation, and failure handling.",
    },
    "skill": {
        "label": "Skill Candidate",
        "classification": "skill-candidate",
        "destination": "skill-candidates/",
        "signals": [
            "skill",
            "trigger",
            "inputs",
            "outputs",
            "safety",
            "class-level",
            "multiple projects",
            "promote",
            "技能",
            "触发",
            "输入",
            "输出",
            "安全",
            "多次",
            "升级",
        ],
        "description": "Class-level task capability. Prefer updating an existing umbrella before creating a new skill candidate.",
    },
}

USER_AGENTS_PATH = Path("/root/.codex/AGENTS.md")
ACTIVE_SKILL_PATH = Path("/home/l30002999/.codex/skills/experience-vault/SKILL.md")
FAILURE_STATE_PATH = ROOT / "index" / "failure_attempts.json"
REVIEW_STATE_PATH = ROOT / "index" / "review_state.json"

DOMAIN_KEYWORDS = {
    "git-github": ["git", "github", "push", "pull", "remote", "branch", "publickey", "permission denied"],
    "ssh": ["ssh", "scp", "publickey", "known_hosts", "permission denied", "connection refused"],
    "docker": ["docker", "container", "image", "volume", "mount", "registry"],
    "npu-ascend": ["npu", "ascend", "cann", "torch_npu", "npu-smi", "hccl"],
    "mindspeed": ["mindspeed", "megatron", "llm", "pretrain", "finetune"],
    "verl": ["verl", "ppo", "grpo", "rollout", "reward", "ray"],
    "profiling": ["profiling", "profiler", "trace", "step_trace", "op_statistic", "slow rank"],
    "python": ["python", "pytest", "pip", "venv", "traceback", "modulenotfounderror"],
}

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

VERIFICATION_SIGNALS = [
    "verified",
    "validated",
    "tested",
    "test passed",
    "tests passed",
    "passed",
    "confirmed",
    "reproduced and fixed",
    "verification passed",
    "smoke test",
    "验证通过",
    "测试通过",
    "已验证",
    "已确认",
    "实际测试",
    "复现并修复",
]

UNVERIFIED_SIGNALS = [
    "not verified",
    "not tested",
    "unverified",
    "suspected",
    "hypothesis",
    "tentative",
    "未验证",
    "未测试",
    "待验证",
    "疑似",
    "猜测",
]

PROJECT_FACT_SIGNALS = [
    "this project",
    "current project",
    "this repo",
    "current repo",
    "local path",
    "dataset",
    "container",
    "machine",
    "server",
    "environment",
    "workspace",
    "当前项目",
    "本项目",
    "这个项目",
    "当前仓库",
    "本仓库",
    "路径",
    "目录",
    "数据集",
    "容器",
    "机器",
    "服务器",
    "环境",
    "工作区",
]

GENERAL_FACT_SIGNALS = [
    "general",
    "reusable",
    "portable",
    "across projects",
    "multiple projects",
    "all projects",
    "best practice",
    "principle",
    "next time",
    "always",
    "should",
    "通用",
    "复用",
    "跨项目",
    "多个项目",
    "所有项目",
    "最佳实践",
    "原则",
    "下次",
    "以后",
    "应该",
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


def shell_quote(text: object) -> str:
    return shlex.quote(str(text))


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


def redact_text(text: str) -> str:
    redacted = text
    replacements = [
        (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "<API_KEY>"),
        (re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"), "<TOKEN>"),
        (re.compile(r"Bearer\s+\S{20,}", re.IGNORECASE), "Bearer <TOKEN>"),
        (re.compile(r"\b(password|passwd)\s*[=:]\s*[^\s<>`]+", re.IGNORECASE), r"\1=<PASSWORD>"),
        (re.compile(r"\b(secret|token)\s*[=:]\s*[^\s<>`]+", re.IGNORECASE), r"\1=<TOKEN>"),
    ]
    for pattern, replacement in replacements:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def detect_domains(text: str) -> list[str]:
    lower = text.lower()
    domains: list[str] = []
    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(matches_signal(lower, keyword) for keyword in keywords):
            domains.append(domain)
    return domains


def matches_signal(lower_text: str, signal: str) -> bool:
    lower_signal = signal.lower()
    if " " in lower_signal or not lower_signal.isascii():
        return lower_signal in lower_text
    return re.search(rf"\b{re.escape(lower_signal)}\b", lower_text) is not None


def iter_markdown(dirs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for dirname in dirs:
        base = ROOT / dirname
        if not base.exists():
            continue
        paths.extend(sorted(base.rglob("*.md")))
    return paths


def classify(score: int, confidence: str, record_type: str = "unknown", source_dir: str = "") -> str:
    if record_type == "project" or source_dir == "projects":
        return "partially applicable" if score >= 5 else "not applicable"
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
    source_dir = relative.parts[0] if relative.parts else ""
    applicability = classify(hit.score, hit.confidence, hit.record_type, source_dir)
    print(f"- {hit.title} ({relative})")
    print(f"  type: {hit.record_type}; confidence: {hit.confidence}; score: {hit.score}")
    print(f"  matched: {', '.join(hit.matched_terms)}")
    print(f"  initial_applicability: {applicability}")
    if applicability == "directly applicable":
        print("  reuse_gate: verify applicability, required inputs, environment/topology, and non-applicable cases before adopting")
    if hit.record_type == "project" or source_dir == "projects":
        print("  reuse_guard: project archives are context/provenance, not direct implementation plans")


def command_search(args: argparse.Namespace) -> int:
    if getattr(args, "pull", True):
        latest = ensure_latest_for_read()
        if latest != 0:
            return latest
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
    if getattr(args, "pull", True):
        latest = ensure_latest_for_read()
        if latest != 0:
            return latest
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
        relative = hit.path.relative_to(ROOT)
        source_dir = relative.parts[0] if relative.parts else ""
        buckets[classify(hit.score, hit.confidence, hit.record_type, source_dir)].append(hit)

    for label in ["directly applicable", "partially applicable", "not applicable"]:
        print(f"{label.title()}:")
        if not buckets[label]:
            print("- None")
            continue
        for hit in buckets[label]:
            relative = hit.path.relative_to(ROOT)
            print(f"- {hit.title} ({relative})")
            print(f"  evidence: type={hit.record_type}, confidence={hit.confidence}, matched={', '.join(hit.matched_terms)}")
            source_dir = relative.parts[0] if relative.parts else ""
            if label == "directly applicable":
                print("  reuse_gate: verify applicability boundary, required inputs, environment/topology, and non-applicable cases before adopting")
            if hit.record_type == "project" or source_dir == "projects":
                print("  reuse_guard: project archive only; do not apply its implementation plan to another project without an explicit applicability match")

    print("\nApplicability checklist:")
    print("- Verify current trigger signals match the record.")
    print("- Confirm required inputs and environment compatibility.")
    print("- Check non-applicable cases before reusing steps.")
    print("- Treat project archives as context/provenance only; do not copy project-specific implementation choices across projects by keyword match.")
    print("- Treat partial matches as guidance, not a command script.")

    if buckets["directly applicable"]:
        print("\nNext action: use directly applicable record(s) only after confirming their applicability boundary matches the current project.")
    elif buckets["partially applicable"]:
        print("\nNext action: adapt only the reusable parts from partial matches.")
    else:
        print("\nNext action: do not reuse these records; proceed normally and archive new evidence if useful.")
    return 0


def build_fingerprint(args: argparse.Namespace) -> dict[str, object]:
    error_text = args.error_text or ""
    if args.error_file:
        error_text += "\n" + Path(args.error_file).read_text(encoding="utf-8", errors="ignore")
    raw = "\n".join(
        part
        for part in [
            args.objective or "",
            args.command or "",
            str(args.exit_code) if args.exit_code is not None else "",
            error_text,
            args.context or "",
        ]
        if part
    )
    redacted = redact_text(raw)
    domains = detect_domains(redacted)
    query_parts = domains + tokenize(redacted)[:30]
    seen: set[str] = set()
    query = " ".join(part for part in query_parts if not (part in seen or seen.add(part)))
    return {
        "objective": redact_text(args.objective or ""),
        "command": redact_text(args.command or ""),
        "exit_code": args.exit_code,
        "context": redact_text(args.context or ""),
        "error_excerpt": "\n".join(redact_text(error_text).splitlines()[:20]),
        "domains": domains,
        "recall_query": query,
    }


def command_fingerprint(args: argparse.Namespace) -> int:
    fp = build_fingerprint(args)
    print("# Incident Fingerprint")
    print()
    for key in ["objective", "command", "exit_code", "context"]:
        value = fp.get(key)
        if value not in {None, ""}:
            print(f"- {key}: {value}")
    print(f"- domains: {', '.join(fp['domains']) if fp['domains'] else 'unknown'}")
    if fp.get("error_excerpt"):
        print("\n## Error Excerpt")
        print("```text")
        print(fp["error_excerpt"])
        print("```")
    print("\n## Suggested Recall")
    print("```bash")
    print(f"python scripts/experience_vault.py recall --mode incident --query {shell_quote(fp['recall_query'])}")
    print("```")
    return 0


def command_domain_hints(args: argparse.Namespace) -> int:
    text = args.text or ""
    if args.file:
        text += "\n" + Path(args.file).read_text(encoding="utf-8", errors="ignore")
    domains = detect_domains(redact_text(text))
    if not domains:
        print("No domain hints detected.")
        return 0
    print("Detected domains:")
    for domain in domains:
        print(f"- {domain}: {', '.join(DOMAIN_KEYWORDS[domain])}")
    return 0


def load_failure_state() -> dict[str, dict[str, object]]:
    if not FAILURE_STATE_PATH.exists():
        return {}
    try:
        return json.loads(FAILURE_STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_failure_state(state: dict[str, dict[str, object]]) -> None:
    FAILURE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    FAILURE_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def command_fail_track(args: argparse.Namespace) -> int:
    key = args.key or slugify(" ".join(part for part in [args.objective or "", args.command or ""] if part))
    state = load_failure_state()
    if args.reset:
        if key in state:
            del state[key]
            save_failure_state(state)
        print(f"Reset failure counter: {key}")
        return 0

    entry = state.get(key, {"count": 0, "last_objective": "", "last_command": "", "last_error": ""})
    entry["count"] = int(entry.get("count", 0)) + 1
    entry["last_objective"] = redact_text(args.objective or str(entry.get("last_objective", "")))
    entry["last_command"] = redact_text(args.command or str(entry.get("last_command", "")))
    entry["last_error"] = redact_text(args.error_text or str(entry.get("last_error", "")))[:1000]
    state[key] = entry
    save_failure_state(state)

    count = int(entry["count"])
    print(f"Failure counter: {key} = {count}")
    if count >= args.threshold:
        query = " ".join(detect_domains(" ".join([str(entry["last_objective"]), str(entry["last_command"]), str(entry["last_error"])])))
        query = " ".join([query, str(entry["last_objective"]), str(entry["last_command"]), str(entry["last_error"])])
        query = " ".join(tokenize(query)[:30])
        print("\nThreshold reached. Stop exploratory retries and run incident recall:")
        print("```bash")
        print(f"python scripts/experience_vault.py recall --mode incident --query {shell_quote(query)}")
        print("```")
    return 0


def load_review_state() -> dict[str, object]:
    if not REVIEW_STATE_PATH.exists():
        return {"turn_count": 0}
    try:
        return json.loads(REVIEW_STATE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"turn_count": 0}


def save_review_state(state: dict[str, object]) -> None:
    REVIEW_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    REVIEW_STATE_PATH.write_text(json.dumps(state, indent=2, sort_keys=True), encoding="utf-8")


def contains_any(text: str, words: list[str]) -> bool:
    lower = text.lower()
    return any(word in lower for word in words)


def command_review_turn(args: argparse.Namespace) -> int:
    state = load_review_state()
    if args.reset:
        save_review_state({"turn_count": 0})
        print("Review state reset.")
        return 0

    turn_count = int(state.get("turn_count", 0)) + 1
    state["turn_count"] = turn_count
    save_review_state(state)

    text_parts = [
        args.user_message or "",
        args.assistant_summary or "",
        args.error_text or "",
        args.context or "",
    ]
    combined = redact_text("\n".join(part for part in text_parts if part))
    domains = detect_domains(combined)

    reasons: list[str] = []
    recommendations: list[str] = []

    if turn_count >= args.interval:
        reasons.append(f"turn interval reached ({turn_count}/{args.interval})")
        recommendations.append("consider project checkpoint archive if meaningful progress occurred")
        state["turn_count"] = 0
        save_review_state(state)

    if args.failed or args.error_text:
        reasons.append("failure or error observed")
        recommendations.append("create or update an incident record if the failure was diagnosed or reusable")

    if args.incident_recall:
        reasons.append("incident recall was used")
        recommendations.append("archive the incident outcome if it changed the plan or resolved a blocker")

    if contains_any(combined, ["完成", "解决", "验证通过", "done", "fixed", "resolved", "passed", "milestone"]):
        reasons.append("completion or verification signal detected")
        recommendations.append("create a project checkpoint or knowledge card")

    if contains_any(combined, ["复用", "经验", "下次", "runbook", "knowledge", "lesson", "reusable"]):
        reasons.append("reusable-knowledge signal detected")
        recommendations.append("create or update a knowledge card")

    if domains:
        recommendations.append(f"tag candidate records with domains: {', '.join(domains)}")

    print("# Turn Review")
    print(f"- turn_count: {turn_count}")
    print(f"- domains: {', '.join(domains) if domains else 'unknown'}")

    if not reasons:
        print("- decision: no archive needed")
        print("- reason: no failure, milestone, interval, or reusable-knowledge signal")
        return 0

    print("- decision: archive review recommended")
    print("\n## Reasons")
    for reason in reasons:
        print(f"- {reason}")

    print("\n## Recommendations")
    for recommendation in recommendations:
        print(f"- {recommendation}")

    title = args.title or "Turn Review Followup"
    print("\n## Draft Commands")
    print(f"python scripts/experience_vault.py distill --title {shell_quote(title)} --source '<paste summary or file path>'")
    if args.failed or args.error_text or args.incident_recall:
        print(f"python scripts/experience_vault.py archive --title {shell_quote(title)} --type incident")
    if any("knowledge" in r for r in recommendations):
        print(f"python scripts/experience_vault.py archive --title {shell_quote(title)} --type knowledge")
    if any("project" in r or "checkpoint" in r for r in recommendations):
        print(f"python scripts/experience_vault.py archive --title {shell_quote(title)} --type project")
    return 0


def read_distill_source(args: argparse.Namespace) -> str:
    parts: list[str] = []
    if args.file:
        parts.append(Path(args.file).read_text(encoding="utf-8", errors="ignore"))
    if args.source:
        source = args.source
        if "\n" not in source and len(source) < 240:
            candidate = Path(source)
            if candidate.exists() and candidate.is_file():
                parts.append(candidate.read_text(encoding="utf-8", errors="ignore"))
            else:
                parts.append(source)
        else:
            parts.append(source)
    text = "\n".join(part for part in parts if part)
    return redact_text(text)


def score_distill_categories(text: str) -> dict[str, int]:
    lower = text.lower()
    scores: dict[str, int] = {}
    for record_type, rule in DISTILL_RULES.items():
        score = 0
        for signal in rule["signals"]:
            if matches_signal(lower, signal):
                score += 2 if " " in signal else 1
        scores[record_type] = score

    if text.strip():
        # Preserve project archiving as the default durable source of truth.
        scores["project"] = max(scores["project"], 1)
    if scores["incident"] >= 2 and scores["knowledge"] >= 2:
        scores["knowledge"] += 1
    if scores["runbook"] >= 3 and scores["knowledge"] >= 2:
        scores["runbook"] += 1
    if scores["skill"] >= 2 and (scores["runbook"] >= 2 or scores["knowledge"] >= 3):
        scores["skill"] += 1
    return scores


def has_verification_evidence(text: str, verified: bool = False) -> bool:
    if verified:
        return True
    lower = text.lower()
    if any(matches_signal(lower, signal) for signal in UNVERIFIED_SIGNALS):
        return False
    return any(matches_signal(lower, signal) for signal in VERIFICATION_SIGNALS)


def classify_fact_scope(text: str) -> str:
    lower = text.lower()
    project_hits = sum(1 for signal in PROJECT_FACT_SIGNALS if matches_signal(lower, signal))
    general_hits = sum(1 for signal in GENERAL_FACT_SIGNALS if matches_signal(lower, signal))
    if project_hits and general_hits:
        return "mixed"
    if project_hits:
        return "project-specific"
    if general_hits:
        return "general-reusable"
    return "unknown"


def distill_decisions(scores: dict[str, int], verified: bool, fact_scope: str = "unknown") -> dict[str, str]:
    decisions: dict[str, str] = {}
    project_only = fact_scope == "project-specific"
    for record_type, score in scores.items():
        if record_type == "project":
            decisions[record_type] = "recommended" if score >= 1 else "skip"
        elif record_type == "incident":
            decisions[record_type] = "recommended" if score >= 3 and verified else "skip"
        elif record_type == "runbook":
            decisions[record_type] = "recommended" if score >= 3 and verified and not project_only else "skip"
        elif record_type == "skill":
            decisions[record_type] = "consider" if score >= 3 and verified and not project_only else "skip"
        else:
            decisions[record_type] = "recommended" if score >= 2 and verified and not project_only else "skip"
    return decisions


def extract_distill_evidence(text: str, signals: list[str], limit: int = 5) -> list[str]:
    evidence: list[str] = []
    for line in text.splitlines():
        clean = line.strip().strip("-* ")
        if len(clean) < 4:
            continue
        lower = clean.lower()
        if any(matches_signal(lower, signal) for signal in signals):
            evidence.append(clean[:220])
        if len(evidence) >= limit:
            break
    return evidence


def create_archive_drafts(
    record_types: list[str],
    title: str,
    slug: str | None,
    force: bool,
    distill_note: str = "",
) -> list[Path]:
    created: list[Path] = []
    for record_type in record_types:
        template_path, output_dir = TEMPLATE_BY_TYPE[record_type]
        template = (ROOT / template_path).read_text(encoding="utf-8")
        output_slug = slug or slugify(title)
        output = ROOT / output_dir / f"{date.today().isoformat()}-{output_slug}.md"
        if output.exists() and not force:
            raise FileExistsError(str(output))
        content = render_template(template, title)
        if distill_note:
            content = content.rstrip() + "\n\n## Distill Guidance\n\n" + distill_note.rstrip() + "\n"
        output.write_text(content, encoding="utf-8")
        created.append(output)
    return created


def command_distill(args: argparse.Namespace) -> int:
    if getattr(args, "pull", True):
        latest = ensure_latest_for_write() if args.create_drafts else ensure_latest_for_read()
        if latest != 0:
            return latest
    text = read_distill_source(args)
    if not tokenize(text):
        print("No distillable source provided.", file=sys.stderr)
        return 2
    if has_secret(text):
        print("Source contains potential secrets after redaction. Refusing to distill.", file=sys.stderr)
        return 1

    domains = detect_domains(text)
    scores = score_distill_categories(text)
    verified = has_verification_evidence(text, getattr(args, "verified", False))
    fact_scope = classify_fact_scope(text)
    decisions = distill_decisions(scores, verified, fact_scope)
    selected = [
        record_type
        for record_type in DISTILL_RECORD_TYPES
        if decisions[record_type] == "recommended"
    ]

    print("# Distill Review")
    print(f"- title: {args.title}")
    print(f"- domains: {', '.join(domains) if domains else 'unknown'}")
    print(f"- source_terms: {len(tokenize(text))}")
    print(f"- fact_scope: {fact_scope}")
    print(f"- verification_gate: {'passed' if verified else 'not passed'}")
    if not verified:
        print("- verification_rule: reusable incidents, knowledge, runbooks, and skill candidates require confirmed test/validation evidence")
    if fact_scope == "project-specific":
        print("- scope_rule: project-local facts stay in projects/ or PROJECT_MEMORY.md unless explicitly generalized")
    if fact_scope == "mixed":
        print("- scope_rule: split mixed facts: keep local details in project memory/projects and reusable principles in knowledge/runbooks")
    print("\n## Classification")

    for record_type in ["project", "incident", "knowledge", "runbook", "skill"]:
        rule = DISTILL_RULES[record_type]
        decision = decisions[record_type]
        print(f"- {rule['label']}: {decision}")
        print(f"  classification: {rule['classification']}")
        print(f"  destination: {rule['destination']}")
        print(f"  score: {scores[record_type]}")
        print(f"  use_for: {rule['description']}")
        evidence = extract_distill_evidence(text, rule["signals"], limit=3)
        if evidence:
            print(f"  evidence: {' | '.join(evidence)}")

    print("\n## Hermes-Style Rules Applied")
    print("- Keep project-specific context in projects/ instead of polluting generic knowledge.")
    print("- Classify user-provided facts by scope before archiving; project-local facts are not reusable knowledge by default.")
    print("- Promote portable lessons to knowledge/ only when they can transfer across projects.")
    print("- Promote procedures to runbooks/ only when the sequence is repeatable and verified.")
    print("- Do not promote root-cause hypotheses into reusable experience until the fix was actually tested.")
    print("- Treat skill-candidates/ as class-level capabilities, not one-off project summaries.")
    print("- Record environment failures as fixes or setup steps, not permanent tool limitations.")

    print("\n## Suggested Commands")
    if selected:
        types = " ".join(f"--type {record_type}" for record_type in selected)
        verified_flag = " --verified" if any(record_type != "project" for record_type in selected) else ""
        print(f"python scripts/experience_vault.py archive --title {shell_quote(args.title)} {types}{verified_flag}")
    if decisions["skill"] == "consider":
        skill_slug = slugify(args.title)
        print(f"mkdir -p skill-candidates/{shell_quote(skill_slug)}")
        print(f"cp templates/skill-candidate-SKILL.md skill-candidates/{shell_quote(skill_slug)}/SKILL.md")
    if not selected and decisions["skill"] != "consider":
        print("# No durable archive recommended; keep this in session history only.")

    if args.create_drafts:
        if not selected:
            print("\nNo archive drafts created because no record type was recommended.")
            return 0
        guidance_lines = [
            f"- Distill classification: {DISTILL_RULES[record_type]['classification']} -> {DISTILL_RULES[record_type]['destination']}"
            for record_type in selected
        ]
        if domains:
            guidance_lines.append(f"- Suggested domains: {', '.join(domains)}")
        try:
            created = create_archive_drafts(
                selected,
                args.title,
                args.slug,
                args.force,
                "\n".join(guidance_lines),
            )
        except FileExistsError as exc:
            print(f"Refusing to overwrite existing file: {exc}", file=sys.stderr)
            return 2
        print("\n## Created Drafts")
        for path in created:
            print(f"- {path.relative_to(ROOT)}")
        print("\nNext steps:")
        print("- Fill in the draft sections with verified facts.")
        print("- Run: python scripts/experience_vault.py validate")
        print("- Run: python scripts/experience_vault.py sync --message \"Archive <topic>\"")
    return 0


def render_template(template: str, title: str) -> str:
    skill_name = slugify(title)
    return (
        template.replace("{{date}}", date.today().isoformat())
        .replace("{{title}}", title)
        .replace("{{skill_name}}", skill_name)
        .replace("{{description}}", f"Candidate agent skill for {title}.")
    )


def command_new(args: argparse.Namespace) -> int:
    if getattr(args, "pull", True):
        latest = ensure_latest_for_write()
        if latest != 0:
            return latest
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
    if getattr(args, "pull", True):
        latest = ensure_latest_for_write()
        if latest != 0:
            return latest
    reusable_types = [record_type for record_type in args.type if record_type != "project"]
    if reusable_types and not args.verified:
        print(
            "Refusing to create reusable archive drafts without --verified. "
            "Root cause analysis must be tested before incident/knowledge/runbook archival.",
            file=sys.stderr,
        )
        return 2
    try:
        created = create_archive_drafts(args.type, args.title, args.slug, args.force)
    except FileExistsError as exc:
        print(f"Refusing to overwrite existing file: {exc}", file=sys.stderr)
        return 2

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


def git_status_short() -> subprocess.CompletedProcess[str]:
    return run_capture(["git", "status", "--short"])


def command_git_status(args: argparse.Namespace) -> int:
    if not (ROOT / ".git").exists():
        print("Git repository is not initialized.")
        print("Run: git init")
        print("Then add a private GitHub remote before durable use.")
        return 0
    result = git_status_short()
    print(result.stdout.strip() or "Working tree clean.")
    return result.returncode


def has_remote() -> bool:
    result = subprocess.run(["git", "remote"], cwd=ROOT, text=True, capture_output=True)
    return bool(result.stdout.strip())


def ensure_latest_for_read() -> int:
    if not (ROOT / ".git").exists() or not has_remote():
        return 0
    pull = subprocess.run(["git", "pull", "--ff-only"], cwd=ROOT, text=True)
    return pull.returncode


def ensure_latest_for_write() -> int:
    if not (ROOT / ".git").exists() or not has_remote():
        return 0
    status = git_status_short()
    if status.returncode != 0:
        return status.returncode
    if status.stdout.strip():
        print(
            "Refusing to pull before writing because the vault has local changes. "
            "Run git-review/sync first, or retry with --no-pull after reviewing.",
            file=sys.stderr,
        )
        return 1
    pull = subprocess.run(["git", "pull", "--ff-only"], cwd=ROOT, text=True)
    return pull.returncode


def ensure_no_remote_changes_before_sync() -> int:
    if not (ROOT / ".git").exists() or not has_remote():
        return 0
    fetch = subprocess.run(["git", "fetch"], cwd=ROOT, text=True)
    if fetch.returncode != 0:
        return fetch.returncode
    upstream = run_capture(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"])
    if upstream.returncode != 0:
        return 0
    count = run_capture(["git", "rev-list", "--count", f"HEAD..{upstream.stdout.strip()}"])
    if count.returncode != 0:
        return count.returncode
    if int(count.stdout.strip() or "0") > 0:
        print(
            "Remote has new commits. Pull/rebase and review before syncing local archive changes.",
            file=sys.stderr,
        )
        return 1
    return 0


def command_ensure_latest(args: argparse.Namespace) -> int:
    if args.write:
        return ensure_latest_for_write()
    return ensure_latest_for_read()


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
        status = git_status_short()
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
    return ensure_latest_for_read()


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
    if args.pull:
        status_before_pull = git_status_short()
        if status_before_pull.returncode != 0:
            return status_before_pull.returncode
        if status_before_pull.stdout.strip():
            remote_check = ensure_no_remote_changes_before_sync()
            if remote_check != 0:
                return remote_check
        else:
            pull = ensure_latest_for_read()
            if pull != 0:
                return pull

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


def event_source_text(args: argparse.Namespace) -> str:
    parts = [
        args.objective or "",
        args.query or "",
        args.summary or "",
        args.error_text or "",
        args.context or "",
    ]
    return redact_text("\n".join(part for part in parts if part))


def event_query(args: argparse.Namespace) -> str:
    explicit = " ".join(part for part in [args.query, args.objective, args.summary, args.context] if part)
    domains = detect_domains(redact_text(explicit))
    query_parts = domains + tokenize(explicit)[:30]
    seen: set[str] = set()
    query = " ".join(part for part in query_parts if not (part in seen or seen.add(part)))
    return query


def print_event_header(name: str, args: argparse.Namespace) -> None:
    print(f"# Experience Vault Event: {name}")
    if args.title:
        print(f"- title: {args.title}")
    if args.objective:
        print(f"- objective: {redact_text(args.objective)}")


def command_event(args: argparse.Namespace) -> int:
    if args.pull:
        latest = ensure_latest_for_write() if args.create_drafts else ensure_latest_for_read()
        if latest != 0:
            return latest

    print_event_header(args.event_type, args)

    if args.event_type == "project-start":
        query = event_query(args)
        if not query:
            print("No project-start query terms provided.", file=sys.stderr)
            return 2
        print("\n## Recall")
        return command_recall(argparse.Namespace(query=query, mode="project-start", limit=args.limit, pull=False))

    if args.event_type == "command-failed":
        fp_args = argparse.Namespace(
            objective=args.objective,
            command=args.failed_command,
            exit_code=args.exit_code,
            error_text=args.error_text,
            error_file=args.error_file,
            context=args.context,
        )
        fp = build_fingerprint(fp_args)
        error_excerpt = str(fp.get("error_excerpt") or "")
        print("\n## Fingerprint")
        command_fingerprint(fp_args)

        print("\n## Failure Tracking")
        fail_code = command_fail_track(
            argparse.Namespace(
                key=args.key,
                objective=args.objective,
                command=args.failed_command,
                error_text=error_excerpt,
                threshold=args.threshold,
                reset=False,
            )
        )
        if fail_code != 0:
            return fail_code

        query = str(fp.get("recall_query") or "")
        if query:
            print("\n## Incident Recall")
            return command_recall(argparse.Namespace(query=query, mode="incident", limit=args.limit, pull=False))
        print("\nNo incident recall query could be built.")
        return 0

    if args.event_type in {"milestone", "project-close"}:
        title = args.title or ("Project Close" if args.event_type == "project-close" else "Project Milestone")
        failed = bool(args.error_text or args.error_file)
        print("\n## Archive Review")
        review_code = command_review_turn(
            argparse.Namespace(
                user_message=args.user_message,
                assistant_summary=args.summary,
                error_text=args.error_text,
                context=args.context,
                title=title,
                interval=args.interval,
                failed=failed,
                incident_recall=args.incident_recall,
                reset=False,
            )
        )
        if review_code != 0:
            return review_code

        source = event_source_text(args)
        if tokenize(source) or args.file:
            print("\n## Distill")
            return command_distill(
                argparse.Namespace(
                    title=title,
                    source=source,
                    file=args.file,
                    slug=args.slug,
                    create_drafts=args.create_drafts,
                    force=args.force,
                    verified=args.verified,
                    pull=False,
                )
            )

        print("\nNo distillable summary provided. Add --summary or --file to classify archive destinations.")
        return 0

    print(f"Unsupported event type: {args.event_type}", file=sys.stderr)
    return 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    search = sub.add_parser("search", help="Search experience records")
    search.add_argument("--query", required=True)
    search.add_argument("--mode", choices=sorted(SEARCH_ORDER), default="project-start")
    search.add_argument("--limit", type=int, default=5)
    search.add_argument("--no-pull", dest="pull", action="store_false")
    search.set_defaults(func=command_search, pull=True)

    recall = sub.add_parser("recall", help="Search and group records by applicability")
    recall.add_argument("--query", required=True)
    recall.add_argument("--mode", choices=sorted(SEARCH_ORDER), default="project-start")
    recall.add_argument("--limit", type=int, default=5)
    recall.add_argument("--no-pull", dest="pull", action="store_false")
    recall.set_defaults(func=command_recall, pull=True)

    fingerprint = sub.add_parser("fingerprint", help="Build an incident fingerprint and recall query")
    fingerprint.add_argument("--objective")
    fingerprint.add_argument("--command")
    fingerprint.add_argument("--exit-code", type=int)
    fingerprint.add_argument("--error-text")
    fingerprint.add_argument("--error-file")
    fingerprint.add_argument("--context")
    fingerprint.set_defaults(func=command_fingerprint)

    domain_hints = sub.add_parser("domain-hints", help="Detect Experience Vault domain keywords")
    domain_hints.add_argument("--text")
    domain_hints.add_argument("--file")
    domain_hints.set_defaults(func=command_domain_hints)

    fail_track = sub.add_parser("fail-track", help="Track repeated failures and recommend recall")
    fail_track.add_argument("--key")
    fail_track.add_argument("--objective")
    fail_track.add_argument("--command")
    fail_track.add_argument("--error-text")
    fail_track.add_argument("--threshold", type=int, default=2)
    fail_track.add_argument("--reset", action="store_true")
    fail_track.set_defaults(func=command_fail_track)

    review_turn = sub.add_parser("review-turn", help="Review whether the latest turn should be archived")
    review_turn.add_argument("--user-message")
    review_turn.add_argument("--assistant-summary")
    review_turn.add_argument("--error-text")
    review_turn.add_argument("--context")
    review_turn.add_argument("--title")
    review_turn.add_argument("--interval", type=int, default=5)
    review_turn.add_argument("--failed", action="store_true")
    review_turn.add_argument("--incident-recall", action="store_true")
    review_turn.add_argument("--reset", action="store_true")
    review_turn.set_defaults(func=command_review_turn)

    distill = sub.add_parser("distill", help="Classify a project summary into archive destinations")
    distill.add_argument("--title", required=True)
    distill.add_argument("--source", help="Source text or a path to a source file")
    distill.add_argument("--file", help="Path to a source file")
    distill.add_argument("--slug")
    distill.add_argument("--create-drafts", action="store_true", help="Create recommended archive drafts")
    distill.add_argument("--verified", action="store_true", help="Allow reusable archive recommendations after confirmed testing")
    distill.add_argument("--force", action="store_true")
    distill.add_argument("--no-pull", dest="pull", action="store_false")
    distill.set_defaults(func=command_distill, pull=True)

    new = sub.add_parser("new", help="Create a record from a template")
    new.add_argument("--type", choices=sorted(TEMPLATE_BY_TYPE), required=True)
    new.add_argument("--title", required=True)
    new.add_argument("--slug")
    new.add_argument("--force", action="store_true")
    new.add_argument("--no-pull", dest="pull", action="store_false")
    new.set_defaults(func=command_new, pull=True)

    archive = sub.add_parser("archive", help="Create one or more archive drafts")
    archive.add_argument("--title", required=True)
    archive.add_argument("--type", choices=sorted(TEMPLATE_BY_TYPE), action="append", required=True)
    archive.add_argument("--slug")
    archive.add_argument("--verified", action="store_true", help="Required for incident, knowledge, or runbook drafts")
    archive.add_argument("--force", action="store_true")
    archive.add_argument("--no-pull", dest="pull", action="store_false")
    archive.set_defaults(func=command_archive, pull=True)

    validate = sub.add_parser("validate", help="Validate repository structure and hygiene")
    validate.set_defaults(func=command_validate)

    doctor = sub.add_parser("doctor", help="Check Experience Vault health")
    doctor.set_defaults(func=command_doctor)

    git_status = sub.add_parser("git-status", help="Show Git status")
    git_status.set_defaults(func=command_git_status)

    git_pull = sub.add_parser("git-pull", help="Pull from configured Git remote")
    git_pull.set_defaults(func=command_git_pull)

    ensure_latest = sub.add_parser("ensure-latest", help="Pull latest vault state before reading or writing")
    ensure_latest.add_argument("--write", action="store_true", help="Require a clean working tree before pulling")
    ensure_latest.set_defaults(func=command_ensure_latest)

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

    event = sub.add_parser("event", help="Run a lifecycle event workflow")
    event.add_argument(
        "event_type",
        choices=["project-start", "command-failed", "milestone", "project-close"],
        help="Lifecycle event to process",
    )
    event.add_argument("--title")
    event.add_argument("--objective")
    event.add_argument("--query")
    event.add_argument("--summary")
    event.add_argument("--user-message")
    event.add_argument("--context")
    event.add_argument("--file", help="Additional source file for milestone or project-close distillation")
    event.add_argument("--failed-command")
    event.add_argument("--exit-code", type=int)
    event.add_argument("--error-text")
    event.add_argument("--error-file")
    event.add_argument("--key", help="Failure tracking key")
    event.add_argument("--threshold", type=int, default=2)
    event.add_argument("--interval", type=int, default=5)
    event.add_argument("--limit", type=int, default=5)
    event.add_argument("--incident-recall", action="store_true")
    event.add_argument("--verified", action="store_true", help="Mark milestone/project-close summary as tested and confirmed")
    event.add_argument("--create-drafts", action="store_true", help="Create recommended archive drafts after distillation")
    event.add_argument("--slug")
    event.add_argument("--force", action="store_true")
    event.add_argument("--no-pull", dest="pull", action="store_false")
    event.set_defaults(func=command_event, pull=True)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
