"""doctor subcommand. Validate the workbench root."""
from __future__ import annotations

import json
import pathlib

from lib import yaml_io, config as config_mod
from lib.cli._common import fail, load_config


HELP = "Validate the workbench root, schemas, and config."


def register(p) -> None:
    pass


def _check_file(p: pathlib.Path) -> bool:
    if not p.exists():
        print(f"  MISSING  {p}")
        return False
    print(f"  ok       {p}")
    return True


def run(args) -> int:
    root = pathlib.Path(args.root).resolve()
    print(f"workbench root: {root}")
    ok = True

    print("layout:")
    for sub in ("bin/agent-workbench", "lib", "schemas", "templates", "agent-workbench.yaml"):
        if not _check_file(root / sub):
            ok = False
    print()

    print("schemas:")
    for name in ("events.jsonl", "run-metadata.yaml", "transitions.yaml"):
        p = root / "schemas" / name
        if not p.exists():
            print(f"  MISSING  {p}")
            ok = False
            continue
        try:
            if name.endswith(".jsonl"):
                for n, line in enumerate(p.read_text().splitlines(), start=1):
                    line = line.strip()
                    if not line:
                        continue
                    json.loads(line)
            else:
                yaml_io.loads(p.read_text())
            print(f"  ok       {p}")
        except Exception as e:
            print(f"  INVALID  {p}: {e}")
            ok = False
    print()

    print("config:")
    try:
        cfg = config_mod.load(root)
        print(f"  ok       agent-workbench.yaml (cli={cfg.cli_name})")
    except Exception as e:
        print(f"  INVALID  agent-workbench.yaml: {e}")
        ok = False

    print()
    if ok:
        print("doctor: PASS")
        return 0
    print("doctor: FAIL")
    return 1
