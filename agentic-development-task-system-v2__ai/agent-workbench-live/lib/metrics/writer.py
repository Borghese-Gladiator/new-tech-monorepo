"""Per-run metrics.jsonl writer.

``record_run_metrics(cfg, run_id)`` is the single public entry point. It
locates the run's transcripts, correlates turns to slash commands, attributes
input tokens to buckets, computes per-turn USD cost via the price table, and
writes a fresh ``metrics.jsonl`` to the run directory.

Idempotent: re-running on the same run overwrites the file (we re-derive from
the transcript every time — the transcript is the source of truth).

Row kinds:
  - ``turn``: one per assistant turn correlated to the run.
  - ``build_outcome``: one per validate decision (read from events.jsonl).
  - ``line_count``: one for ``generated``, one for ``accepted`` if a merge sha
    is recorded in metadata.

The writer never raises into the lifecycle: if a transcript is missing, it
writes an empty metrics.jsonl with a header row noting the cause.
"""
from __future__ import annotations

import datetime as dt
import json
import pathlib

from lib import metadata as metadata_mod
from lib.metrics import buckets as buckets_mod
from lib.metrics import lines as lines_mod
from lib.metrics import prices as prices_mod
from lib.metrics import transcript as transcript_mod


SCHEMA_VERSION = 1
METRICS_FILE = "metrics.jsonl"
SUMMARY_FILE = "metrics-summary.json"


def _now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def _project_slug_for_run(meta: dict) -> str:
    """Pick the project slug for the run.

    Prefer the worktree path (where /build runs); fall back to the repo path
    (where /shape /plan run).
    """
    wt = (meta.get("target") or {}).get("worktree") or {}
    wt_path = wt.get("path")
    if wt_path:
        return transcript_mod.slugify_project_path(wt_path)
    repo = (meta.get("target") or {}).get("repo") or {}
    return transcript_mod.slugify_project_path(repo.get("path") or "")


def _run_cwd_candidates(meta: dict) -> list[str]:
    out: list[str] = []
    wt = (meta.get("target") or {}).get("worktree") or {}
    if wt.get("path"):
        out.append(wt["path"])
    repo = (meta.get("target") or {}).get("repo") or {}
    if repo.get("path") and repo["path"] not in out:
        out.append(repo["path"])
    return out


def _prices_path(cfg) -> pathlib.Path:
    return cfg.root / "metrics" / "prices.yaml"


def _read_events(events_path: pathlib.Path) -> list[dict]:
    out: list[dict] = []
    if not events_path.exists():
        return out
    with events_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _build_outcomes_from_events(events: list[dict]) -> list[dict]:
    """Return one row per ReviewCompleted event."""
    outcomes: list[dict] = []
    attempt = 0
    for ev in events:
        t = ev.get("type")
        if t == "TransitionApplied" and ev.get("from") == "building" and ev.get("to") == "validating":
            attempt += 1
        elif t == "ReviewCompleted":
            decision = (ev.get("payload") or {}).get("review_decision") or "unknown"
            outcomes.append({
                "schema_version": SCHEMA_VERSION,
                "kind": "build_outcome",
                "at": ev.get("at") or "",
                "attempt": attempt or 1,
                "validate_result": decision,
            })
    return outcomes


def record_run_metrics(cfg, run_id: str) -> pathlib.Path:
    """Walk the transcript, write ``runs/<run_id>/metrics.jsonl``.

    Returns the path to the written file. Never raises into the caller:
    transcript-not-found / price-table-malformed produce a metrics.jsonl
    whose first row is a ``notice`` describing the gap.
    """
    rd = metadata_mod.run_dir(cfg, run_id)
    metrics_path = rd / METRICS_FILE
    summary_path = rd / SUMMARY_FILE

    try:
        meta = metadata_mod.load(cfg, run_id)
    except Exception as e:
        _write_notice(metrics_path, f"metadata load failed: {e}")
        return metrics_path

    # Load prices.
    try:
        price_table = prices_mod.load(_prices_path(cfg))
    except prices_mod.PricesError:
        # Don't crash — write metrics with cost=0 and a notice row.
        price_table = {}

    rows: list[dict] = []
    rows.append({
        "schema_version": SCHEMA_VERSION,
        "kind": "header",
        "at": _now_iso(),
        "run_id": run_id,
        "status": meta.get("status"),
        "scope_kind": (meta.get("scope") or {}).get("kind"),
        "prices_loaded": bool(price_table),
    })

    # Locate transcripts.
    slug = _project_slug_for_run(meta)
    transcripts = transcript_mod.find_transcripts(slug) if slug else []
    if not transcripts:
        rows.append({
            "schema_version": SCHEMA_VERSION,
            "kind": "notice",
            "at": _now_iso(),
            "message": f"no transcripts found for project slug {slug!r}",
        })

    # Correlate turns.
    turn_rows: list[dict] = []
    for cwd_candidate in _run_cwd_candidates(meta):
        turns = transcript_mod.correlate(
            transcripts,
            run_cwd=cwd_candidate,
            window_start=meta.get("created_at"),
            window_end=None,
        )
        if turns:
            for turn in turns:
                bucket = buckets_mod.attribute(turn)
                cost = prices_mod.cost_usd(turn.usage, turn.model, price_table) if price_table else 0.0
                turn_rows.append({
                    "schema_version": SCHEMA_VERSION,
                    "kind": "turn",
                    "at": turn.ts,
                    "stage": turn.stage,
                    "command": turn.command,
                    "model": turn.model,
                    "usage": {
                        "input": turn.usage.get("input_tokens", 0),
                        "output": turn.usage.get("output_tokens", 0),
                        "cache_read": turn.usage.get("cache_read_input_tokens", 0),
                        "cache_creation": turn.usage.get("cache_creation_input_tokens", 0),
                    },
                    "bucket_attribution": bucket,
                    "cost_usd": round(cost, 6),
                    "transcript_ref": {
                        "path": turn.transcript_path,
                        "turn_id": turn.turn_id,
                        "session_id": turn.session_id,
                    },
                })
            break  # First cwd that yields any turns wins.

    rows.extend(turn_rows)

    # Build outcomes from events.jsonl.
    events_path = rd / "events.jsonl"
    events = _read_events(events_path)
    rows.extend(_build_outcomes_from_events(events))

    # Line counts.
    wt = (meta.get("target") or {}).get("worktree") or {}
    repo = (meta.get("target") or {}).get("repo") or {}
    base_ref = repo.get("base_ref") or "HEAD"
    gen = lines_mod.count_generated(
        worktree_path=wt.get("path"),
        base_ref=base_ref,
        events_path=events_path,
    )
    rows.append({
        "schema_version": SCHEMA_VERSION,
        "kind": "line_count",
        "at": _now_iso(),
        "phase": "generated",
        "lines": gen,
    })

    completion_ref = (meta.get("completion") or {}).get("completion_ref")
    acc, merge_sha = lines_mod.count_accepted(
        worktree_path=wt.get("path"),
        base_ref=base_ref,
        completion_ref=completion_ref,
    )
    row = {
        "schema_version": SCHEMA_VERSION,
        "kind": "line_count",
        "at": _now_iso(),
        "phase": "accepted",
        "lines": acc,
    }
    if merge_sha:
        row["merge_commit"] = merge_sha
    rows.append(row)

    # Write atomically: write to .tmp then rename.
    tmp = metrics_path.with_suffix(".jsonl.tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, sort_keys=True))
            f.write("\n")
    tmp.replace(metrics_path)

    # Stale-ify the summary cache so the next reader recomputes.
    if summary_path.exists():
        try:
            summary_path.unlink()
        except OSError:
            pass

    return metrics_path


def _write_notice(metrics_path: pathlib.Path, message: str) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps({
            "schema_version": SCHEMA_VERSION,
            "kind": "notice",
            "at": _now_iso(),
            "message": message,
        }, sort_keys=True) + "\n"
    )
