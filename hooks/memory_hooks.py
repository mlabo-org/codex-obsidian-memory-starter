#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    return Path(raw).expanduser().resolve()


REPO_ROOT = env_path(
    "CODEX_OBSIDIAN_MEMORY_REPO_ROOT",
    Path(__file__).resolve().parent.parent,
)
CODEX_HOME = env_path("CODEX_OBSIDIAN_MEMORY_CODEX_HOME", Path.home() / ".codex")
VAULT_ROOT = env_path("CODEX_OBSIDIAN_MEMORY_VAULT_ROOT", REPO_ROOT / "vault")
PROJECTS_FILE = env_path(
    "CODEX_OBSIDIAN_MEMORY_PROJECTS_FILE",
    REPO_ROOT / "config" / "projects.local.json",
)
EPISODES_DIR = VAULT_ROOT / "episodes"
ULTRA_SHORT_DIR = EPISODES_DIR / "ultra_short"
PROJECTS_DIR = VAULT_ROOT / "knowledge" / "projects"
RULES_DIR = VAULT_ROOT / "knowledge" / "rules"
LOG_DIR = CODEX_HOME / "hooks" / "logs"
STATE_DIR = CODEX_HOME / "hooks" / "state"
READ_LIMIT = int(os.environ.get("CODEX_OBSIDIAN_MEMORY_READ_LIMIT", "3"))
ULTRA_SHORT_READ_LIMIT = int(
    os.environ.get("CODEX_OBSIDIAN_MEMORY_ULTRA_SHORT_READ_LIMIT", "4")
)
ULTRA_SHORT_LOOKBACK_HOURS = int(
    os.environ.get("CODEX_OBSIDIAN_MEMORY_ULTRA_SHORT_LOOKBACK_HOURS", "12")
)
EPISODE_TTL_DAYS = int(os.environ.get("CODEX_OBSIDIAN_MEMORY_EPISODE_TTL_DAYS", "14"))
ULTRA_SHORT_TTL_DAYS = int(
    os.environ.get("CODEX_OBSIDIAN_MEMORY_ULTRA_SHORT_TTL_DAYS", "3")
)
AUTO_PRUNE_STATUSES = {"active"}
SUPPRESS_PATTERNS = (
    "read no external memory",
    "do not read external memory",
    "memory を読まない",
    "external memory を読まない",
)


@dataclass(frozen=True)
class MemoryProject:
    project_id: str
    project_note: Path
    workspace_hints: tuple[str, ...]
    keywords: tuple[str, ...]
    related_rules: tuple[Path, ...]


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    lowered = re.sub(r"[^a-z0-9]+", "-", lowered)
    lowered = lowered.strip("-")
    return lowered or "project"


def load_projects() -> tuple[MemoryProject, ...]:
    if not PROJECTS_FILE.exists():
        return ()

    try:
        payload = json.loads(PROJECTS_FILE.read_text())
    except json.JSONDecodeError:
        return ()

    projects: list[MemoryProject] = []
    for raw in payload.get("projects", []):
        project_id = slugify(str(raw.get("project_id", "")))
        if not project_id:
            continue
        note_relative = str(raw.get("project_note", "")).strip()
        if not note_relative:
            note_relative = f"knowledge/projects/{project_id}.md"
        related_rules = tuple(
            (VAULT_ROOT / str(item)).resolve()
            for item in raw.get("related_rules", [])
            if str(item).strip()
        )
        projects.append(
            MemoryProject(
                project_id=project_id,
                project_note=(VAULT_ROOT / note_relative).resolve(),
                workspace_hints=tuple(
                    str(item).strip()
                    for item in raw.get("workspace_hints", [])
                    if str(item).strip()
                ),
                keywords=tuple(
                    str(item).strip()
                    for item in raw.get("keywords", [])
                    if str(item).strip()
                ),
                related_rules=related_rules,
            )
        )
    return tuple(projects)


PROJECTS = load_projects()


def load_payload() -> dict[str, Any]:
    return json.load(sys.stdin)


def is_subagent_event(payload: dict[str, Any]) -> bool:
    return bool(payload.get("agent_id"))


def log_payload(payload: dict[str, Any], event_label: str) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = LOG_DIR / f"{timestamp}-{event_label}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def prepare_memory_environment() -> None:
    EPISODES_DIR.mkdir(parents=True, exist_ok=True)
    ULTRA_SHORT_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    RULES_DIR.mkdir(parents=True, exist_ok=True)
    cleanup_expired_notes(EPISODES_DIR, include_readme=False)
    cleanup_expired_notes(ULTRA_SHORT_DIR, include_readme=True)


def build_session_start_context(payload: dict[str, Any]) -> str | None:
    cwd = payload.get("cwd", "")
    project = match_projects("", cwd)
    recent = recent_project_episodes(project, limit=READ_LIMIT) if project else []
    ultra_short = recent_ultra_short_entries(limit=ULTRA_SHORT_READ_LIMIT)
    if not recent and not ultra_short:
        return None

    lines = [
        "External memory policy: episode-first. Read only a few recent episodes first; do not scan the whole vault; open durable rules or decisions only on demand.",
    ]
    if ultra_short:
        lines.append("Ultra-short captures:")
        lines.extend(f"- {item}" for item in ultra_short)
    if recent:
        lines.append("Recent episodes:")
        lines.extend(f"- {episode['title']}" for episode in recent)
    if project and project.project_note.exists():
        lines.append(f"Likely project note: {project.project_note.stem}")
    return "\n".join(lines)


def build_user_prompt_context(payload: dict[str, Any]) -> str | None:
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt or should_suppress_memory(prompt):
        return None

    project = match_projects(prompt, payload.get("cwd", ""))
    if not project:
        return None

    lines = [f"Potential relevant memory for `{project.project_id}`:"]
    if project.project_note.exists():
        lines.append(f"- Project: {brief_project_summary(project.project_note)}")

    recent = related_recent_episodes(project, prompt, limit=2)
    if recent:
        lines.append("- Related recent episodes:")
        lines.extend(f"  - {item['title']}" for item in recent)

    for rule_path in project.related_rules:
        if rule_path.exists():
            lines.append(f"- Rule: {brief_rule_summary(rule_path)}")

    return "\n".join(lines) if len(lines) > 1 else None


def maybe_capture_episode(payload: dict[str, Any]) -> None:
    if payload.get("stop_hook_active"):
        return

    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        return

    last_user_message = last_user_message_from_transcript(Path(transcript_path))
    last_assistant_message = str(payload.get("last_assistant_message", "")).strip()
    combined = " ".join(filter(None, (last_user_message, last_assistant_message)))
    if not combined:
        return

    project = match_projects(combined, payload.get("cwd", ""))
    if not project or memory_signal_score(combined, project) < 2:
        return

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    note_path = episode_note_path(project.project_id, str(payload.get("session_id", "")))
    state_path = STATE_DIR / f"{payload.get('session_id', 'unknown')}.json"
    fingerprint = hashlib.sha1(
        f"{last_user_message}\n---\n{last_assistant_message}".encode("utf-8")
    ).hexdigest()
    state = load_state(state_path)
    if fingerprint in state.get("seen_fingerprints", []):
        return

    if not note_path.exists():
        create_episode_note(note_path, project.project_id)

    append_episode_bullet(note_path, summarize_turn(last_user_message, last_assistant_message))
    state.setdefault("seen_fingerprints", []).append(fingerprint)
    state["note_path"] = str(note_path)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def maybe_capture_user_prompt(payload: dict[str, Any]) -> None:
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt or should_suppress_memory(prompt):
        return

    project = match_projects(prompt, payload.get("cwd", ""))
    if not project or memory_signal_score(prompt, project) < 2:
        return

    STATE_DIR.mkdir(parents=True, exist_ok=True)
    note_path = episode_note_path(project.project_id, str(payload.get("session_id", "")))
    state_path = STATE_DIR / f"{payload.get('session_id', 'unknown')}.json"
    fingerprint = hashlib.sha1(f"user-prompt::{prompt}".encode("utf-8")).hexdigest()
    state = load_state(state_path)
    if fingerprint in state.get("seen_fingerprints", []):
        return

    if not note_path.exists():
        create_episode_note(note_path, project.project_id)

    append_episode_bullet(note_path, summarize_user_prompt(prompt))
    state.setdefault("seen_fingerprints", []).append(fingerprint)
    state["note_path"] = str(note_path)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def capture_ultra_short_prompt(payload: dict[str, Any]) -> None:
    prompt = str(payload.get("prompt", "")).strip()
    if not prompt:
        return

    session_id = str(payload.get("session_id", "unknown"))
    fingerprint = hashlib.sha1(f"ultra-short::{prompt}".encode("utf-8")).hexdigest()
    state_path = STATE_DIR / f"{session_id}.json"
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    state = load_state(state_path)
    if fingerprint in state.get("seen_fingerprints", []):
        return

    note_path = ultra_short_note_path()
    if not note_path.exists():
        create_ultra_short_note(note_path)

    append_ultra_short_entry(
        note_path=note_path,
        timestamp=current_local_isoformat(),
        cwd=str(payload.get("cwd", "")).strip(),
        prompt=prompt,
        session_id=session_id,
    )
    state.setdefault("seen_fingerprints", []).append(fingerprint)
    state["ultra_short_note_path"] = str(note_path)
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n")


def recent_episodes(limit: int) -> list[dict[str, str]]:
    files = [
        path
        for path in EPISODES_DIR.glob("*.md")
        if path.name.lower() != "readme.md" and path.is_file() and not note_is_expired(path)
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return [{"path": str(path), "title": first_heading(path) or path.stem} for path in files[:limit]]


def recent_ultra_short_entries(limit: int) -> list[str]:
    entries: list[tuple[datetime, str]] = []
    if not ULTRA_SHORT_DIR.exists():
        return []

    files = [
        path
        for path in ULTRA_SHORT_DIR.glob("*.md")
        if path.is_file() and not note_is_expired(path)
    ]
    files.sort(key=lambda path: path.stat().st_mtime, reverse=True)

    for path in files:
        for raw_line in reversed(safe_read_text(path).splitlines()):
            if not raw_line.startswith("- "):
                continue
            parsed = parse_ultra_short_entry(raw_line[2:])
            if not parsed:
                continue
            timestamp, text = parsed
            age = datetime.now(timezone.utc) - timestamp.astimezone(timezone.utc)
            if age > timedelta(hours=ULTRA_SHORT_LOOKBACK_HOURS):
                continue
            entries.append((timestamp, text))
            if len(entries) >= limit:
                break
        if len(entries) >= limit:
            break

    entries.sort(key=lambda item: item[0], reverse=True)
    return [text for _, text in entries[:limit]]


def related_recent_episodes(
    project: MemoryProject, prompt: str, limit: int
) -> list[dict[str, str]]:
    lowered = prompt.lower()
    related: list[dict[str, str]] = []
    for episode in recent_episodes(limit=8):
        path = Path(episode["path"])
        content = safe_read_text(path).lower()
        score = 0
        for keyword in project.keywords:
            if keyword.lower() in lowered and keyword.lower() in content:
                score += 1
        if score:
            related.append(episode)
        if len(related) >= limit:
            break
    return related


def recent_project_episodes(
    project: MemoryProject, limit: int, search_limit: int = 12
) -> list[dict[str, str]]:
    related: list[dict[str, str]] = []
    project_marker = f"project: {project.project_id}".lower()
    project_id = project.project_id.lower()

    for episode in recent_episodes(limit=search_limit):
        path = Path(episode["path"])
        content = safe_read_text(path).lower()
        if project_marker not in content and project_id not in path.stem.lower():
            continue
        related.append(episode)
        if len(related) >= limit:
            break

    return related


def first_heading(path: Path) -> str | None:
    for line in safe_read_text(path).splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip()
    return None


def brief_project_summary(path: Path) -> str:
    title = first_heading(path) or path.stem
    bullets = first_bullets(path, limit=2)
    return f"{title}; " + "; ".join(bullets) if bullets else title


def brief_rule_summary(path: Path) -> str:
    title = first_heading(path) or path.stem
    bullets = first_bullets(path, limit=2)
    if bullets:
        return f"{title}; " + "; ".join(bullets)
    body = first_paragraph(path)
    return f"{title}; {body}" if body else title


def first_bullets(path: Path, limit: int) -> list[str]:
    bullets: list[str] = []
    for line in safe_read_text(path).splitlines():
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped[2:])
            if len(bullets) >= limit:
                break
    return bullets


def first_paragraph(path: Path) -> str:
    lines: list[str] = []
    for line in safe_read_text(path).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("- "):
            if lines:
                break
            continue
        lines.append(stripped)
        if len(" ".join(lines)) > 180:
            break
    return " ".join(lines)


def should_suppress_memory(prompt: str) -> bool:
    lowered = prompt.lower()
    return any(pattern in lowered for pattern in SUPPRESS_PATTERNS)


def match_projects(text: str, cwd: str) -> MemoryProject | None:
    lowered = text.lower()
    best: tuple[int, MemoryProject] | None = None
    for project in PROJECTS:
        score = 0
        if any(hint in cwd for hint in project.workspace_hints):
            score += 1
        for keyword in project.keywords:
            if keyword.lower() in lowered:
                score += 1
        if score and (best is None or score > best[0]):
            best = (score, project)
    return best[1] if best else None


def memory_signal_score(text: str, project: MemoryProject) -> int:
    lowered = text.lower()
    score = 0
    for keyword in project.keywords:
        if keyword.lower() in lowered:
            score += 1
    for keyword in ("must", "should", "rule", "rules", "policy", "memory", "episode", "hook", "記録", "運用"):
        if keyword.lower() in lowered:
            score += 1
    return score


def last_user_message_from_transcript(path: Path) -> str:
    if not path.exists():
        return ""
    last_message = ""
    for raw_line in path.read_text().splitlines():
        try:
            entry = json.loads(raw_line)
        except json.JSONDecodeError:
            continue
        payload = entry.get("payload", {})
        if entry.get("type") == "event_msg" and payload.get("type") == "user_message":
            last_message = str(payload.get("message", "")).strip()
    return last_message


def episode_note_path(project_id: str, session_id: str) -> Path:
    today = date.today().isoformat()
    short_session = session_id[:8] if session_id else "session"
    return EPISODES_DIR / f"{today}-{project_id}-hook-session-{short_session}.md"


def ultra_short_note_path() -> Path:
    return ULTRA_SHORT_DIR / f"{date.today().isoformat()}-ultra-short.md"


def create_episode_note(path: Path, project_id: str) -> None:
    expires_at = (date.today() + timedelta(days=EPISODE_TTL_DAYS)).isoformat()
    title = project_id.replace("-", " ").title()
    content = (
        "---\n"
        f"created_at: {date.today().isoformat()}\n"
        f"expires_at: {expires_at}\n"
        f"project: {project_id}\n"
        "tags:\n"
        "  - hook\n"
        "  - codex\n"
        "  - memory\n"
        "status: active\n"
        "promotion_hint: Promote only if the captured pattern recurs and remains useful across sessions.\n"
        "---\n\n"
        f"# {title}\n\n"
        "## Context\n\n"
        "Short operational observations captured automatically by Codex hooks during the session.\n\n"
        "## Episode\n\n"
        "## Potential Reuse\n\n"
        "Promote only when the note remains useful beyond this session.\n"
    )
    path.write_text(content)


def create_ultra_short_note(path: Path) -> None:
    expires_at = (date.today() + timedelta(days=ULTRA_SHORT_TTL_DAYS)).isoformat()
    content = (
        "---\n"
        f"created_at: {date.today().isoformat()}\n"
        f"expires_at: {expires_at}\n"
        "project: ultra-short-memory-buffer\n"
        "tags:\n"
        "  - ultra-short\n"
        "  - memory\n"
        "  - hook\n"
        "status: active\n"
        "promotion_hint: Immediate undecided captures only. Promote, keep, or discard later based on actual reuse.\n"
        "---\n\n"
        "## Context\n\n"
        "Immediate user-prompt captures stored before keep-or-discard judgment.\n\n"
        "## Captures\n\n"
    )
    path.write_text(content)


def append_episode_bullet(path: Path, bullet: str) -> None:
    text = path.read_text()
    marker = "## Potential Reuse"
    if marker not in text:
        text += "\n## Potential Reuse\n"
    before, after = text.split(marker, 1)
    if f"- {bullet}\n" in before:
        return
    if not before.endswith("\n"):
        before += "\n"
    before += f"- {bullet}\n\n"
    path.write_text(before + marker + after)


def append_ultra_short_entry(
    note_path: Path, timestamp: str, cwd: str, prompt: str, session_id: str
) -> None:
    text = note_path.read_text()
    entry = (
        f"- {timestamp} | session={session_id[:8]} | cwd={compact_excerpt(cwd, 48)} | "
        f'prompt="{compact_excerpt(prompt, 220)}"\n'
    )
    if entry in text:
        return
    if not text.endswith("\n"):
        text += "\n"
    text += entry
    note_path.write_text(text)


def summarize_turn(user_message: str, assistant_message: str) -> str:
    user_excerpt = compact_excerpt(user_message, 120)
    assistant_excerpt = compact_excerpt(assistant_message, 120)
    return f'User "{user_excerpt}" / Assistant "{assistant_excerpt}"'


def summarize_user_prompt(user_message: str) -> str:
    excerpt = compact_excerpt(user_message, 140)
    return f'User raised a memory-relevant prompt: "{excerpt}"'


def compact_excerpt(text: str, limit: int) -> str:
    one_line = re.sub(r"\s+", " ", text).strip()
    if len(one_line) <= limit:
        return one_line
    return one_line[: limit - 3] + "..."


def parse_ultra_short_entry(text: str) -> tuple[datetime, str] | None:
    parts = [part.strip() for part in text.split("|")]
    if len(parts) < 4:
        return None
    timestamp_raw = parts[0]
    prompt_part = parts[3]
    if not prompt_part.startswith('prompt="') or not prompt_part.endswith('"'):
        return None
    try:
        timestamp = datetime.fromisoformat(timestamp_raw)
    except ValueError:
        return None
    prompt_text = prompt_part[len('prompt="') : -1]
    return timestamp, f"{timestamp.strftime('%H:%M')} {prompt_text}"


def current_local_isoformat() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def cleanup_expired_notes(directory: Path, include_readme: bool) -> None:
    if not directory.exists():
        return

    for path in directory.glob("*.md"):
        if not path.is_file():
            continue
        if not include_readme and path.name.lower() == "readme.md":
            continue
        if not note_is_expired(path):
            continue
        if note_status(path) not in AUTO_PRUNE_STATUSES:
            continue
        try:
            path.unlink()
        except FileNotFoundError:
            continue


def note_is_expired(path: Path) -> bool:
    expires_at = note_metadata(path).get("expires_at", "")
    if not expires_at:
        return False
    try:
        expiry = date.fromisoformat(expires_at)
    except ValueError:
        return False
    return date.today() > expiry


def note_status(path: Path) -> str:
    return note_metadata(path).get("status", "").strip().lower()


def note_metadata(path: Path) -> dict[str, str]:
    lines = safe_read_text(path).splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    metadata: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError:
        return {}


def safe_read_text(path: Path) -> str:
    try:
        return path.read_text()
    except FileNotFoundError:
        return ""
