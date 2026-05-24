"""Input-token bucket attribution.

We split a turn's reported ``input_tokens`` into buckets so a reader can see
where the cost is going (system prompt? tool defs? assistant history? tool
results?). The transcript line doesn't carry exact byte-counts for every
sub-region of the request, so we approximate by:

  1. Estimating tokens per text segment with a cheap heuristic (4 chars/token).
  2. Mapping each text segment to its bucket via content markers (the
     ``Contents of /Users/.../CLAUDE.md`` block, ``<command-name>`` tags, etc).
  3. Scaling the bucket totals so they sum to the turn's authoritative
     ``input_tokens`` count.

Unattributable bytes land in ``other`` — we'd rather under-attribute than
silently mis-attribute.

The output is always a dict with all bucket keys present (zero-valued if
absent). This keeps downstream summarization branchless.
"""
from __future__ import annotations

import re
from typing import Iterable


BUCKET_NAMES = (
    "system_prompt",
    "tool_defs",
    "claude_md_and_agents_md",
    "context_imports",
    "slash_command_body",
    "user_messages",
    "assistant_history",
    "tool_results",
    "other",
)

# Roughly 4 chars per token for English + code. Good enough for proportional
# splitting; the scaling step (see ``attribute()``) lifts the total back to the
# transcript's authoritative number.
_CHARS_PER_TOKEN = 4.0

_CLAUDE_MD_RE = re.compile(
    r"Contents of /Users/[^/]+/(?:\.claude/CLAUDE\.md|.*?CLAUDE\.md|.*?AGENTS\.md)",
    re.IGNORECASE,
)
_CONTEXT_IMPORT_RE = re.compile(r"@context/[^\s]+|@AGENTS\.md|@CLAUDE\.md")
_COMMAND_BLOCK_RE = re.compile(r"<command-name>.*?</command-args>", re.DOTALL)
_TOOL_USE_OPEN_RE = re.compile(r"<tool_use_error>|<tool_result>", re.IGNORECASE)


def _est_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, int(len(text) / _CHARS_PER_TOKEN))


def _classify_user_text(text: str) -> dict[str, int]:
    """Return per-bucket char counts for one user-role text body."""
    out = {k: 0 for k in BUCKET_NAMES}
    if not text:
        return out

    # Pull out CLAUDE/AGENTS blocks first.
    remaining = text
    md_total = 0
    for m in _CLAUDE_MD_RE.finditer(remaining):
        # We can't perfectly bound the block; charge until the next blank-line
        # separator from the match start.
        start = m.start()
        # Find the end by looking for a "Contents of " of a different file or
        # for "# currentDate" / "# claudeMd" boundary markers commonly seen.
        rest = remaining[start:]
        # Heuristic: next "Contents of " or end of string.
        nxt = re.search(r"\nContents of |\n# [a-z]", rest[1:])
        end = start + (nxt.start() + 1 if nxt else len(rest))
        chunk = remaining[start:end]
        md_total += len(chunk)
    out["claude_md_and_agents_md"] = md_total

    # Context imports: pull lines that match the @context pattern.
    ci_total = 0
    for m in _CONTEXT_IMPORT_RE.finditer(text):
        ci_total += len(m.group(0))
    out["context_imports"] = ci_total

    # Slash command body.
    cmd_total = 0
    for m in _COMMAND_BLOCK_RE.finditer(text):
        cmd_total += len(m.group(0))
    out["slash_command_body"] = cmd_total

    # Whatever's left in the user text — call it user_messages. We don't
    # subtract the other buckets here because the regex matches overlap; the
    # scaling step at the end reconciles.
    out["user_messages"] = max(
        0, len(text) - (md_total + ci_total + cmd_total)
    )
    return out


def attribute(turn) -> dict[str, int]:
    """Attribute one ``CorrelatedTurn``'s ``input_tokens`` into the buckets.

    Returns a dict keyed by ``BUCKET_NAMES``, summing to the turn's
    ``input_tokens`` (within ±1 token of rounding).
    """
    total_input = int(turn.usage.get("input_tokens", 0) or 0)
    if total_input <= 0:
        return {k: 0 for k in BUCKET_NAMES}

    # Per-bucket character counts derived from the available raw text.
    chars = {k: 0 for k in BUCKET_NAMES}

    # User-message bodies: classify each.
    for body in (turn.raw_user_messages or ()):
        sub = _classify_user_text(body)
        for k, v in sub.items():
            chars[k] += v

    # Tool-result bodies — these go into ``tool_results``.
    tr_chars = sum(len(b) for b in (turn.raw_tool_results or ()))
    chars["tool_results"] += tr_chars

    # System prompt / tool defs / assistant history are NOT in the transcript
    # record per-turn; they're carried implicitly by the cache. We approximate
    # by leaving them at 0 and letting them surface in ``other`` via the
    # scaling step. (When the cache misses, ``input_tokens`` is dominated by
    # them; when it hits, they're charged to ``cache_read_input_tokens`` which
    # we track separately at the turn level — not bucketed.)
    #
    # For attributability: when ``input_tokens`` is small (cache hit), most of
    # the visible text is the new user message + tool results; the bucketing
    # is meaningful. When ``input_tokens`` is large (cache miss / first turn),
    # most goes into ``other`` — that's the honest answer.

    measured_total = sum(chars[k] for k in BUCKET_NAMES)
    if measured_total <= 0:
        # No raw text at all → everything goes to other.
        return {**{k: 0 for k in BUCKET_NAMES}, "other": total_input}

    # Convert char counts to estimated tokens, then scale to match the
    # authoritative input_tokens count. The residual goes into ``other``.
    est = {k: int(chars[k] / _CHARS_PER_TOKEN) for k in BUCKET_NAMES}
    est_total = sum(est.values())
    if est_total >= total_input:
        # Estimates exceed the actual input (regex over-counted via overlap).
        # Scale down proportionally, no ``other`` residual.
        scale = total_input / est_total
        out = {k: int(round(est[k] * scale)) for k in BUCKET_NAMES}
        out["other"] = 0
        # Force-sum to total_input by adjusting the largest bucket.
        delta = total_input - sum(out.values())
        if delta != 0:
            largest = max(out, key=lambda k: out[k])
            out[largest] += delta
        return out

    # Estimates fit under the total: charge the rest to ``other``.
    other = total_input - est_total
    out = {k: est[k] for k in BUCKET_NAMES}
    out["other"] = max(0, other)
    return out


def merge(per_turn: Iterable[dict[str, int]]) -> dict[str, int]:
    """Sum a sequence of bucket dicts into one aggregate."""
    out = {k: 0 for k in BUCKET_NAMES}
    for d in per_turn:
        for k in BUCKET_NAMES:
            out[k] += int(d.get(k, 0) or 0)
    return out
