"""plan subcommand.

Two modes:
  --init   : while status=planning, stage templates for plan/preflight/assumptions/decisions.
  default  : verify all four artifacts exist and are non-empty, then transition
             planning -> ready. Emits AssumptionRecorded / DecisionRecorded events
             for each top-level heading in assumptions.md / decisions.md.
"""
from __future__ import annotations

import re

from lib import metadata, events, transitions, locks
from lib.cli._common import actor_from_env, fail, load_config


HELP = "Stage planning templates (--init) or finalize the plan (default)."


PLAN_TEMPLATES = ("plan.md", "preflight.md", "assumptions.md", "decisions.md")


def register(p) -> None:
    p.add_argument("run_id")
    p.add_argument("--init", action="store_true",
                   help="Stage templates/{plan,preflight,assumptions,decisions}.md.")


def _stage_templates(cfg, rd) -> None:
    for name in PLAN_TEMPLATES:
        dest = rd / name
        if not dest.exists():
            src = cfg.root / "templates" / name
            dest.write_text(src.read_text() if src.exists() else f"# {name}\n")


def _parse_ids(md_text: str, prefix: str) -> list[str]:
    """Pull `## PREFIX-NNN` style headings (e.g. ASM-001, DR-001)."""
    pattern = re.compile(rf"^##\s+({prefix}-\d+)\b", re.MULTILINE)
    return pattern.findall(md_text)


def _extract_assumption_blocks(md_text: str) -> list[dict]:
    """Return [{assumption_id, text, reason, impact}, ...]."""
    parts = re.split(r"^##\s+(ASM-\d+)\s*$", md_text, flags=re.MULTILINE)
    out: list[dict] = []
    # parts: [preamble, id1, body1, id2, body2, ...]
    for i in range(1, len(parts), 2):
        asm_id = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        out.append({
            "assumption_id": asm_id,
            "text": _field(body, "Text"),
            "reason": _field(body, "Reason"),
            "impact": _field(body, "Impact"),
        })
    return out


def _extract_decision_blocks(md_text: str) -> list[dict]:
    parts = re.split(r"^##\s+(DR-\d+)\s*$", md_text, flags=re.MULTILINE)
    out: list[dict] = []
    for i in range(1, len(parts), 2):
        dr_id = parts[i]
        body = parts[i + 1] if i + 1 < len(parts) else ""
        out.append({
            "decision_id": dr_id,
            "decision": _field(body, "Decision"),
            "rationale": _field(body, "Rationale"),
            "alternatives_considered": _field(body, "Alternatives considered"),
            "why_not_alternatives": _field(body, "Why not the alternatives"),
        })
    return out


def _field(body: str, label: str) -> str:
    m = re.search(rf"-\s*\*\*{re.escape(label)}\*\*:\s*(.*)", body)
    if not m:
        return ""
    return m.group(1).strip()


def run(args) -> int:
    cfg = load_config(args)
    actor = actor_from_env("agent")
    run_id = args.run_id

    try:
        meta = metadata.load(cfg, run_id)
    except metadata.MetadataError as e:
        return fail(str(e), 2)

    rd = metadata.run_dir(cfg, run_id)

    if args.init:
        if meta["status"] != "planning":
            return fail(f"--init requires status=planning, got {meta['status']!r}", 2)
        _stage_templates(cfg, rd)
        def _m(d):
            d["artifacts"]["plan"] = "plan.md"
            d["artifacts"]["preflight"] = "preflight.md"
            d["artifacts"]["assumptions"] = "assumptions.md"
            d["artifacts"]["decisions"] = "decisions.md"
        metadata.update(cfg, run_id, _m)
        for name in PLAN_TEMPLATES:
            events.append(
                cfg, run_id, "ArtifactWritten",
                payload={"artifact_key": name.replace(".md",""), "path": str(rd / name), "summary": "template staged"},
                actor=actor,
            )
        print(f"{run_id}: staged {', '.join(PLAN_TEMPLATES)}")
        return 0

    # Default: planning -> ready.
    if meta["status"] != "planning":
        return fail(f"default mode requires status=planning, got {meta['status']!r}", 2)

    # Verify all four artifacts exist and have non-template content.
    for name in PLAN_TEMPLATES:
        p = rd / name
        if not p.exists() or not p.read_text().strip():
            return fail(f"{name} missing or empty at {p}", 2)

    # Emit AssumptionRecorded / DecisionRecorded for any ID found.
    asm_text = (rd / "assumptions.md").read_text()
    for asm in _extract_assumption_blocks(asm_text):
        if not asm["text"]:
            continue
        events.append(
            cfg, run_id, "AssumptionRecorded",
            payload={
                "assumption_id": asm["assumption_id"],
                "text": asm["text"],
                "reason": asm["reason"] or "(not recorded)",
                "impact": asm["impact"] or "(not recorded)",
                "source_artifact": "assumptions.md",
            },
            actor=actor,
        )
    dr_text = (rd / "decisions.md").read_text()
    for dr in _extract_decision_blocks(dr_text):
        if not dr["decision"]:
            continue
        events.append(
            cfg, run_id, "DecisionRecorded",
            payload={
                "decision_id": dr["decision_id"],
                "decision": dr["decision"],
                "rationale": dr["rationale"] or "(not recorded)",
                "alternatives_considered": dr["alternatives_considered"],
                "why_not_alternatives": dr["why_not_alternatives"],
                "source_artifact": "decisions.md",
            },
            actor=actor,
        )

    # Emit PreflightCompleted.
    events.append(
        cfg, run_id, "PreflightCompleted",
        payload={
            "preflight_path": str(rd / "preflight.md"),
            "repo_path": meta["target"]["repo"]["path"],
            "repo_name": meta["target"]["repo"]["name"],
            "base_ref": meta["target"]["repo"]["base_ref"],
            "branch_name": meta["target"]["worktree"]["branch_name"],
            "worktree_name": meta["target"]["worktree"]["name"],
        },
        actor=actor,
    )

    # Apply the transition.
    try:
        with locks.acquire(cfg, run_id):
            transitions.transition(
                cfg, run_id, "ready",
                evidence={
                    "plan_path": str(rd / "plan.md"),
                    "assumptions_path": str(rd / "assumptions.md"),
                    "decisions_path": str(rd / "decisions.md"),
                    "preflight_path": str(rd / "preflight.md"),
                    "repo_path": meta["target"]["repo"]["path"],
                    "repo_name": meta["target"]["repo"]["name"],
                    "worktree_name": meta["target"]["worktree"]["name"],
                    "branch_name": meta["target"]["worktree"]["branch_name"],
                    "base_ref": meta["target"]["repo"]["base_ref"],
                },
                actor=actor,
            )
    except transitions.TransitionError as e:
        return fail(str(e), 4)

    print(f"{run_id}: planning -> ready")
    return 0
