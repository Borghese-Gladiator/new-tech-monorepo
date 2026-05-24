"""Claude Code transcript locator + correlator.

Claude Code writes one JSONL transcript per session to
``~/.claude/projects/<slug>/<session-id>.jsonl``. Each line is one record:

- ``type=user``: a user-role message. May contain ``<command-name>`` tags when
  the user fired a slash command.
- ``type=assistant``: an assistant-role message with ``message.usage.*`` token
  counts and ``message.model``.
- ``type=permission-mode`` / ``file-history-snapshot``: bookkeeping, no usage.

We correlate transcript turns to a workbench run by:
  1. Locating transcripts whose project slug matches the run's working dir,
     then narrowing to lines whose timestamp falls inside the run window
     ``[meta.created_at, meta.updated_at]``.
  2. Walking those lines in order, tracking which slash command is currently
     active (start = a user message containing ``<command-name>/shape``,
     ``/plan``, ``/validate``, ``/build``, ``/followups``; end = the next slash
     command or the run window boundary).
  3. Stamping each ``assistant`` turn inside that span with ``(stage, command)``.

Pure function over transcript bytes — feed it fixture paths to test.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib
import re
from dataclasses import dataclass
from typing import Iterable, Iterator


# Slash commands that gate a lifecycle stage. Order matters: longer prefixes
# first so ``/validate-init`` (hypothetical) wouldn't match ``/validate`` first.
COMMAND_TO_STAGE = {
    "/shape": "shaping",
    "/plan": "planning",
    "/build": "building",
    "/validate": "validating",
    "/followups": "followups",
    "/new-run": "draft",
    "/start": "ready",
    "/handoff": "human_review",
    "/complete": "done",
    "/bounce": "building",
    "/abandon": "abandoned",
}

# Marker used by Claude Code's user-message body for slash command turns.
_CMD_NAME_RE = re.compile(r"<command-name>\s*(/[A-Za-z0-9_\-]+)\s*</command-name>")


@dataclass(frozen=True)
class CorrelatedTurn:
    """One assistant turn attributed to a slash command + lifecycle stage.

    `stage` and `command` may be ``"other"`` when correlation fails (the turn
    fired between known slash commands or outside any).
    """

    turn_id: str
    ts: str  # ISO-8601 from the transcript record
    transcript_path: str
    session_id: str
    cwd: str | None
    stage: str
    command: str
    model: str
    usage: dict  # {input_tokens, output_tokens, cache_read_input_tokens, cache_creation_input_tokens}
    raw_user_messages: tuple[str, ...]  # text bodies of preceding user msgs in this command span
    raw_tool_results: tuple[str, ...]  # tool-result block bodies in the request that led to this turn


def slugify_project_path(path: str | pathlib.Path) -> str:
    """Mimic Claude Code's slug for ``~/.claude/projects/<slug>/``.

    Convention: replace every ``/`` with ``-``. Leading ``-`` is preserved
    (the directory in `~/.claude/projects/` keeps it). Underscores are
    replaced with ``-`` and dots with ``-`` to match observed slugs like
    ``-Users-timothy-shee-GitHub-LOCAL-worktrees-202605-agent-workbench-v2-agentic-development-task-system-v2--ai``.
    """
    s = str(path)
    s = s.replace("/", "-").replace("_", "-").replace(".", "-")
    return s


def transcripts_dir() -> pathlib.Path:
    return pathlib.Path.home() / ".claude" / "projects"


def find_transcripts(
    project_slug: str,
    *,
    base_dir: pathlib.Path | None = None,
) -> list[pathlib.Path]:
    """All JSONL files under ``~/.claude/projects/<slug>/``.

    Sorted by name (which is a UUID, but stable for tests). Empty list if
    the directory doesn't exist.
    """
    base = (base_dir or transcripts_dir()) / project_slug
    if not base.exists():
        return []
    return sorted(p for p in base.glob("*.jsonl") if p.is_file())


def _parse_ts(s: str | None) -> dt.datetime | None:
    if not s:
        return None
    try:
        # Claude Code uses "...Z"; Python <3.11 needs explicit replacement.
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return dt.datetime.fromisoformat(s)
    except ValueError:
        return None


def _iter_records(path: pathlib.Path) -> Iterator[dict]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def _extract_command(rec: dict) -> str | None:
    """Return the slash-command name (e.g. ``/build``) if this user record
    fired a slash command, else None."""
    if rec.get("type") != "user":
        return None
    msg = rec.get("message") or {}
    content = msg.get("content")
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        # Content blocks; join the text ones.
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block.get("text") or "")
            elif isinstance(block, str):
                parts.append(block)
        text = "\n".join(parts)
    m = _CMD_NAME_RE.search(text or "")
    if m:
        return m.group(1)
    return None


def _user_message_text(rec: dict) -> str | None:
    if rec.get("type") != "user":
        return None
    msg = rec.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text") or "")
                elif block.get("type") == "tool_result":
                    inner = block.get("content")
                    if isinstance(inner, str):
                        parts.append(inner)
                    elif isinstance(inner, list):
                        for ib in inner:
                            if isinstance(ib, dict) and ib.get("type") == "text":
                                parts.append(ib.get("text") or "")
        return "\n".join(parts)
    return None


def _tool_result_bodies(rec: dict) -> list[str]:
    if rec.get("type") != "user":
        return []
    msg = rec.get("message") or {}
    content = msg.get("content")
    out: list[str] = []
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                inner = block.get("content")
                if isinstance(inner, str):
                    out.append(inner)
                elif isinstance(inner, list):
                    for ib in inner:
                        if isinstance(ib, dict) and ib.get("type") == "text":
                            out.append(ib.get("text") or "")
    return out


def _assistant_usage(rec: dict) -> dict | None:
    if rec.get("type") != "assistant":
        return None
    msg = rec.get("message") or {}
    usage = msg.get("usage") or {}
    return {
        "input_tokens": int(usage.get("input_tokens", 0) or 0),
        "output_tokens": int(usage.get("output_tokens", 0) or 0),
        "cache_read_input_tokens": int(usage.get("cache_read_input_tokens", 0) or 0),
        "cache_creation_input_tokens": int(usage.get("cache_creation_input_tokens", 0) or 0),
    }


def _assistant_model(rec: dict) -> str:
    msg = rec.get("message") or {}
    return msg.get("model") or ""


def correlate(
    transcript_paths: Iterable[pathlib.Path],
    *,
    run_cwd: str,
    window_start: str | None = None,
    window_end: str | None = None,
) -> list[CorrelatedTurn]:
    """Walk transcripts and emit one CorrelatedTurn per assistant turn.

    ``run_cwd``: the run's working directory (``meta.target.repo.path`` or
    the worktree path). We only attribute turns whose record ``cwd`` matches
    (best-effort: a turn with a different cwd falls into ``stage='other'``).

    ``window_start``/``window_end``: ISO timestamps. Turns outside this window
    are skipped entirely. Either or both may be None (open-ended).
    """
    start = _parse_ts(window_start)
    end = _parse_ts(window_end)
    out: list[CorrelatedTurn] = []

    for path in transcript_paths:
        # Track per-transcript active command + buffered user/tool-result bodies.
        current_command: str | None = None
        current_stage: str = "other"
        # Pending bodies between commands; flushed onto each assistant turn
        # so the bucketer has the user-message context for that turn.
        pending_user_text: list[str] = []
        pending_tool_results: list[str] = []

        for rec in _iter_records(path):
            ts_raw = rec.get("timestamp")
            ts = _parse_ts(ts_raw)
            if ts is not None:
                if start is not None and ts < start:
                    continue
                if end is not None and ts > end:
                    # transcripts are time-ordered; stop early.
                    break

            # Watch for slash-command transitions.
            cmd = _extract_command(rec)
            if cmd is not None:
                current_command = cmd
                current_stage = COMMAND_TO_STAGE.get(cmd, "other")
                pending_user_text = []
                pending_tool_results = []
                # Don't continue — fall through so the user-message text is
                # captured for the next assistant turn (it contains the
                # slash-command body).
            user_text = _user_message_text(rec)
            if user_text is not None:
                pending_user_text.append(user_text)
            tool_results = _tool_result_bodies(rec)
            if tool_results:
                pending_tool_results.extend(tool_results)

            usage = _assistant_usage(rec)
            if usage is None:
                continue

            # Only attribute to a stage if the cwd matches the run's worktree
            # or repo path. Otherwise mark as ``other``.
            rec_cwd = rec.get("cwd")
            if rec_cwd and run_cwd and _cwd_matches(rec_cwd, run_cwd):
                stage = current_stage
                command = current_command or ""
            else:
                stage = "other"
                command = current_command or ""

            out.append(
                CorrelatedTurn(
                    turn_id=str(rec.get("uuid") or ""),
                    ts=ts_raw or "",
                    transcript_path=str(path),
                    session_id=str(rec.get("sessionId") or ""),
                    cwd=rec_cwd,
                    stage=stage,
                    command=command,
                    model=_assistant_model(rec),
                    usage=usage,
                    raw_user_messages=tuple(pending_user_text),
                    raw_tool_results=tuple(pending_tool_results),
                )
            )
            # After an assistant turn, clear the pending tool-results buffer —
            # they were "consumed" by this turn. The user-message buffer is
            # also cleared so the next turn sees only the next user text.
            pending_user_text = []
            pending_tool_results = []
    return out


def _cwd_matches(rec_cwd: str, run_cwd: str) -> bool:
    """A turn belongs to the run if its cwd equals the run cwd OR is a
    subdirectory of it (worktrees, nested scripts, etc.)."""
    try:
        r = pathlib.Path(rec_cwd).resolve()
        p = pathlib.Path(run_cwd).resolve()
    except OSError:
        return rec_cwd == run_cwd
    if r == p:
        return True
    try:
        r.relative_to(p)
        return True
    except ValueError:
        pass
    try:
        p.relative_to(r)
        return True
    except ValueError:
        return False
