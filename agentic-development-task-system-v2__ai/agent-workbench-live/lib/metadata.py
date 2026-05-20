"""Run metadata read/write.

Source of truth for a run's state. Only this module writes
runs/<run_id>/metadata.yaml. The transition engine calls into it; other modules
read via load() but never call save() directly.

We DO NOT enforce every field in schemas/run-metadata.yaml on every save. The
template there is illustrative; what matters for V1 is:

- required_top_level_fields are present
- status is one of the enum values
- nothing else trips the writer
"""
from __future__ import annotations

import datetime as dt
import pathlib
from typing import Any

from lib import yaml_io
from lib.config import Config


class MetadataError(Exception):
    pass


STATUSES = {
    "draft",
    "shaping",
    "planning",
    "ready",
    "building",
    "validating",
    "human_review",
    "done",
    "abandoned",
}

REQUIRED_TOP_LEVEL = (
    "schema_version",
    "run_id",
    "status",
    "created_at",
    "updated_at",
    "target",
    "scope",
    "artifacts",
    "validation",
    "completion",
)


def now_iso() -> str:
    """ISO-8601 timestamp with seconds resolution, local time + offset."""
    return dt.datetime.now().astimezone().replace(microsecond=0).isoformat()


def run_dir(cfg: Config, run_id: str) -> pathlib.Path:
    return cfg.runs_path / run_id


def metadata_path(cfg: Config, run_id: str) -> pathlib.Path:
    return run_dir(cfg, run_id) / "metadata.yaml"


def _validate(data: dict) -> None:
    if not isinstance(data, dict):
        raise MetadataError("metadata must be a mapping")
    missing = [k for k in REQUIRED_TOP_LEVEL if k not in data]
    if missing:
        raise MetadataError(f"missing required keys: {missing}")
    status = data["status"]
    if status not in STATUSES:
        raise MetadataError(f"invalid status: {status!r}")


def load(cfg: Config, run_id: str) -> dict:
    p = metadata_path(cfg, run_id)
    if not p.exists():
        raise MetadataError(f"no metadata for run {run_id!r}: {p}")
    with open(p) as f:
        data = yaml_io.loads(f.read())
    if not isinstance(data, dict):
        raise MetadataError(f"{p}: top-level must be a mapping")
    _validate(data)
    return data


def save(cfg: Config, run_id: str, data: dict) -> None:
    _validate(data)
    data["updated_at"] = now_iso()
    p = metadata_path(cfg, run_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + ".tmp")
    with open(tmp, "w") as f:
        f.write(yaml_io.dumps(data))
    tmp.replace(p)


def create(
    cfg: Config,
    run_id: str,
    *,
    repo_mode: str,
    repo_path: str,
    repo_name: str,
    base_ref: str,
    worktree_name: str,
    branch_name: str,
    raw_idea_path: str,
    scope_kind: str = "implementation",
    scope_summary: str = "",
) -> dict:
    """Create the run directory and initial metadata.yaml. Returns the saved metadata."""
    rd = run_dir(cfg, run_id)
    if rd.exists():
        raise MetadataError(f"run {run_id!r} already exists at {rd}")
    rd.mkdir(parents=True)
    now = now_iso()
    data: dict[str, Any] = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "draft",
        "created_at": now,
        "updated_at": now,
        "target": {
            "repo": {
                "mode": repo_mode,
                "path": repo_path,
                "name": repo_name,
                "base_ref": base_ref,
                "fingerprint": None,
                "created_by_run": run_id if repo_mode == "new" else None,
            },
            "worktree": {
                "name": worktree_name,
                "path": None,
                "branch_name": branch_name,
                "created": False,
                "base_ref": base_ref,
                "initial_commit_sha": None,
            },
        },
        "scope": {
            "kind": scope_kind,
            "summary": scope_summary,
        },
        "artifacts": {
            "raw_idea": raw_idea_path,
            "answers": None,
            "brief": None,
            "plan": None,
            "preflight": None,
            "assumptions": None,
            "decisions": None,
            "implementation_summary": None,
            "diff_summary": None,
            "review_report": None,
            "qa_report": None,
            "audit": None,
            "handoff": None,
        },
        "validation": {
            "required": True,
            "review_completed": False,
            "qa_completed": False,
            "qa_recorded": False,
            "tests_passed": None,
            "known_issues_count": 0,
        },
        "completion": {
            "accepted_by": None,
            "completion_ref": None,
            "completed_at": None,
            "abandoned_reason": None,
        },
        # Build-loop telemetry surfaced for the reviewer (TODO §1e). Optional
        # at load time so flat-layout runs created before this field existed
        # still load; required to be filled by validate --init before
        # building -> validating.
        "build": {
            "iterations": None,
            "exit_reason": None,
            "max_iterations": _resolve_max_build_iterations(cfg),
        },
    }
    save(cfg, run_id, data)
    return data


def _resolve_max_build_iterations(cfg: Config) -> int:
    raw = cfg.raw.get("defaults", {}) or {}
    return int(raw.get("max_build_iterations", 5))


def set_status(cfg: Config, run_id: str, new_status: str) -> dict:
    """Used only by lib/transitions. Other code MUST NOT call this."""
    if new_status not in STATUSES:
        raise MetadataError(f"invalid status: {new_status!r}")
    data = load(cfg, run_id)
    data["status"] = new_status
    save(cfg, run_id, data)
    return data


def update(cfg: Config, run_id: str, mutator) -> dict:
    """Apply a callable to the metadata dict in place and save. Convenience helper."""
    data = load(cfg, run_id)
    mutator(data)
    save(cfg, run_id, data)
    return data


def list_runs(cfg: Config) -> list[str]:
    if not cfg.runs_path.exists():
        return []
    return sorted(p.name for p in cfg.runs_path.iterdir() if (p / "metadata.yaml").exists())
