"""shape subcommand.

Two modes:
  --init   : while status=shaping, stage templates/brief.md at the run root.
             (LLM body of /shape then fills brief.md.)
  default  : verify brief.md exists and is non-empty, transition shaping -> planning.

Note: the draft -> shaping transition itself lives in cmd_draft (default mode).
This subcommand only sees runs that have already been advanced into shaping by
/draft. That guarantees a question-asking step ran (and either captured
clarifications in answers.md or explicitly skipped) before the brief is authored.
"""
from __future__ import annotations

from lib import metadata, events, transitions, locks, stub_llm
from lib.cli._common import actor_from_env, fail, load_config


HELP = "Begin shaping (--init) or finalize the shape (default)."


def register(p) -> None:
    p.add_argument("run_id")
    p.add_argument("--init", action="store_true",
                   help="Stage templates/brief.md at the run root. No transition.")


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
        if meta["status"] != "shaping":
            return fail(f"--init requires status=shaping, got {meta['status']!r}", 2)
        # Stage brief.md from the template.
        src = cfg.root / "templates" / "brief.md"
        dest = rd / "brief.md"
        if not dest.exists():
            dest.write_text(src.read_text() if src.exists() else "# Brief\n")
        events.append(
            cfg, run_id, "ArtifactWritten",
            payload={"artifact_key": "brief", "path": str(dest), "summary": "template staged"},
            actor=actor,
        )
        # Reflect brief in metadata.
        def _m(d):
            d["artifacts"]["brief"] = "brief.md"
        metadata.update(cfg, run_id, _m)
        # Stub-LLM mode (TODO §1 E2E): if the env var is set, overwrite the
        # template with the fixture's canned brief.md.
        try:
            fix = stub_llm.fixture_dir_from_env()
        except stub_llm.StubLLMError as e:
            return fail(str(e), 2)
        if fix is not None:
            stub_llm.materialize(rd, "shaping", fix)
        print(f"{run_id}: shaping (--init); edit {dest}")
        return 0

    # Default: shaping -> planning.
    if meta["status"] != "shaping":
        return fail(f"default mode requires status=shaping, got {meta['status']!r}", 2)
    brief = rd / "brief.md"
    if not brief.exists() or not brief.read_text().strip():
        return fail(f"brief.md missing or empty at {brief}", 2)
    try:
        with locks.acquire(cfg, run_id):
            transitions.transition(
                cfg, run_id, "planning",
                evidence={"brief_path": str(brief)},
                actor=actor,
            )
    except transitions.TransitionError as e:
        return fail(str(e), 4)
    print(f"{run_id}: shaping -> planning")
    return 0
