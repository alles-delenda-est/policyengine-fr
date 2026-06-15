"""Golden-master regression tests.

A frozen grid of (income x family structure) -> all headline outputs, captured
in fixtures/golden_master.json. Any later change that moves a value fails here
and must be justified.

IMPORTANT: golden values are computed BY THE MODEL, so they lock *current
behaviour* and catch silent regressions/drift — they do NOT prove correctness
against French law. Correctness is the job of the independent oracle
(docs/cowork-validation-brief.md). When a change is intentional, regenerate with:

    REGEN_GOLDEN=1 python -m pytest tests/test_golden_master.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from helpers import build_household, totals

FIXTURE = Path(__file__).parent / "fixtures" / "golden_master.json"

# (id, adult_incomes, child_ages, parent_isole)
CASES = [
    ("single_0", [0], [], False),
    ("single_20k", [20_000], [], False),
    ("single_30k", [30_000], [], False),
    ("single_50k", [50_000], [], False),
    ("single_120k", [120_000], [], False),
    ("single_parent_25k_1child", [25_000], [8], True),
    ("single_parent_18k_2children", [18_000], [4, 9], True),
    ("couple_60k_0child", [60_000, 0], [], False),
    ("couple_60k_2children", [60_000, 0], [10, 16], False),
    ("couple_90k_3children", [50_000, 40_000], [3, 8, 15], False),
    ("couple_200k_3children", [120_000, 80_000], [5, 9, 15], False),
    ("couple_40k_4children", [40_000, 0], [2, 6, 11, 15], False),
    ("dualearner_75k_2children", [45_000, 30_000], [7, 14], False),
]


def _compute() -> dict:
    out = {}
    for cid, incomes, ages, isole in CASES:
        sim = build_household(incomes, ages, parent_isole=isole)
        out[cid] = totals(sim)
    return out


def test_golden_master():
    computed = _compute()
    if os.environ.get("REGEN_GOLDEN") or not FIXTURE.exists():
        FIXTURE.write_text(json.dumps(computed, indent=2, ensure_ascii=False) + "\n")
        pytest.skip(f"Regenerated golden master at {FIXTURE}")
    expected = json.loads(FIXTURE.read_text())
    diffs = []
    for cid, vals in computed.items():
        for var, value in vals.items():
            ref = expected.get(cid, {}).get(var)
            if ref is None or abs(value - ref) > 0.01:
                diffs.append(f"{cid}.{var}: got {value}, expected {ref}")
    assert not diffs, (
        "Golden-master drift (regenerate with REGEN_GOLDEN=1 if intended):\n"
        + "\n".join(diffs)
    )
