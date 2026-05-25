"""Stop banner for agent-stopping transitions.

Prints a bordered ``STOP.`` banner to stdout when the CLI lands a run in a
state the agent does not drive: ``ready``, ``human_review``, ``done``, or
``abandoned``. The banner is the last thing the command writes so it lands
in the agent's most recent tool output. See ``docs/TODO.md`` §2.

Single public function:
    print_stop_banner(landing_state, run_id) -> None
"""
from __future__ import annotations

from typing import NamedTuple


BORDER = "=" * 60


class _BannerSpec(NamedTuple):
    header: str  # second-line annotation after "STOP. State: <state>"
    explanation: str
    next_moves: tuple[tuple[str, str], ...]  # (command, description) pairs
    terminal_line: str  # used in place of next_moves when next_moves is empty


_SPECS: dict[str, _BannerSpec] = {
    "ready": _BannerSpec(
        header="human-owned",
        explanation="The plan is staged and waiting for human approval.",
        next_moves=(
            ("start", "approve the plan and create the worktree"),
        ),
        terminal_line="",
    ),
    "human_review": _BannerSpec(
        header="human-owned",
        explanation="The run is staged for human review and decision.",
        next_moves=(
            ("complete", "accept and merge"),
            ("bounce", "send back to building"),
            ("abandon", "abandon the run"),
        ),
        terminal_line="",
    ),
    "done": _BannerSpec(
        header="terminal",
        explanation="The run is accepted and merged.",
        next_moves=(),
        terminal_line="Terminal state. No further action.",
    ),
    "abandoned": _BannerSpec(
        header="terminal",
        explanation="The run is abandoned.",
        next_moves=(),
        terminal_line="Terminal state. No further action.",
    ),
}


def print_stop_banner(landing_state: str, run_id: str) -> None:
    """Print the STOP banner for ``landing_state`` to stdout.

    Raises ``ValueError`` if ``landing_state`` is not one of the four
    agent-stopping states.
    """
    spec = _SPECS.get(landing_state)
    if spec is None:
        raise ValueError(
            f"unknown landing_state {landing_state!r}; expected one of "
            f"{sorted(_SPECS)!r}"
        )

    lines = [
        BORDER,
        f"STOP. State: {landing_state} ({spec.header}).",
        spec.explanation,
        "",
    ]
    if spec.next_moves:
        lines.append("Next moves (human-triggered):")
        for cmd, desc in spec.next_moves:
            lines.append(f"  agent-workbench {cmd} {run_id}  - {desc}")
    else:
        lines.append(spec.terminal_line)
    lines.append(BORDER)

    print("\n".join(lines))
