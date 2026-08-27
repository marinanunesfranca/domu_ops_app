"""
Task 2 (extended): turns raw call-outcome metrics into concrete, actionable
recommendations per client, instead of just displaying numbers.

This is intentionally a simple, transparent rules engine (not an LLM) because
these are operational thresholds Ops already knows and trusts — the value
here is automatically applying them consistently across 7 clients, not
generating new judgment. See Scope of Work for how these thresholds would be
made configurable per client in production instead of hardcoded.
"""

from __future__ import annotations

import statistics
from typing import Optional

# Thresholds — in production these should be configurable per client/region,
# not hardcoded, since "good" varies by client vertical (e.g. medical billing
# vs. auto loans naturally convert differently).
CONVERSION_RATE_THRESHOLD = 30.0   # paid / answered, in %
ANSWER_RATE_THRESHOLD = 55.0       # answered / calls_made, in %
FAILURE_RATE_THRESHOLD = 40.0      # failed / calls_made, in %
EARLY_HANGUP_SECONDS = 60          # calls ending before this are "early hangups"
EARLY_HANGUP_CLUSTER_RATIO = 0.5   # if >=50% of no-payment calls end this early, flag it


def _duration_stats(client_id: str, durations_by_client: dict) -> dict | None:
    durations = durations_by_client.get(client_id)
    if not durations:
        return None
    early = [d for d in durations if d <= EARLY_HANGUP_SECONDS]
    return {
        "count": len(durations),
        "median_seconds": statistics.median(durations),
        "early_hangup_count": len(early),
        "early_hangup_ratio": len(early) / len(durations),
    }


def evaluate_client(row: dict, durations_by_client: dict) -> list[dict]:
    """
    row: a dict with calls_made, answered, paid, failed, answer_rate, conversion_rate
    Returns a list of action items: {severity, finding, recommended_action}
    """
    actions = []

    # --- Conversion rate check --------------------------------------------
    if row["conversion_rate"] < CONVERSION_RATE_THRESHOLD:
        stats = _duration_stats(row["client_id"], durations_by_client)
        if stats and stats["early_hangup_ratio"] >= EARLY_HANGUP_CLUSTER_RATIO:
            actions.append({
                "severity": "High",
                "finding": (
                    f"Conversion rate is {row['conversion_rate']}% (below {CONVERSION_RATE_THRESHOLD}% target). "
                    f"{stats['early_hangup_count']} of {stats['count']} non-payment calls "
                    f"({stats['early_hangup_ratio']:.0%}) ended within {EARLY_HANGUP_SECONDS}s — "
                    f"a likely early-hangup pattern, not just low answer volume."
                ),
                "recommended_action": (
                    "Review the agent prompt around the point where payment is first raised — "
                    "customers appear to be disengaging early, possibly due to tone, pacing, or "
                    "how the ask is framed. Pull 3-5 of these short calls for manual listening before editing the prompt."
                ),
            })
        else:
            actions.append({
                "severity": "Medium",
                "finding": (
                    f"Conversion rate is {row['conversion_rate']}% (below {CONVERSION_RATE_THRESHOLD}% target), "
                    f"but call duration doesn't show an early-hangup pattern."
                ),
                "recommended_action": (
                    "Likely not a prompt-engagement issue. Check objection-handling quality "
                    "(QA Review tab) and whether the payment options offered match what customers are asking for."
                ),
            })

    # --- Answer rate check ---------------------------------------------------
    if row["answer_rate"] < ANSWER_RATE_THRESHOLD:
        actions.append({
            "severity": "Medium",
            "finding": f"Answer rate is {row['answer_rate']}% (below {ANSWER_RATE_THRESHOLD}% target).",
            "recommended_action": (
                "Check call-time scheduling against the client's region and permitted calling "
                "hours (Task 7) — low answer rate is often a timing issue, not a script issue."
            ),
        })

    # --- Failure rate check ----------------------------------------------
    failure_rate = round(row["failed"] / row["calls_made"] * 100, 1)
    if failure_rate > FAILURE_RATE_THRESHOLD:
        actions.append({
            "severity": "High",
            "finding": f"Failure rate is {failure_rate}% (above {FAILURE_RATE_THRESHOLD}% threshold).",
            "recommended_action": (
                "Investigate whether failures are technical (carrier/line issues) or data quality "
                "(bad numbers on file) before assuming it's an agent performance issue."
            ),
        })

    if not actions:
        actions.append({
            "severity": "OK",
            "finding": "All metrics within target range.",
            "recommended_action": "No action needed this cycle.",
        })

    return actions
