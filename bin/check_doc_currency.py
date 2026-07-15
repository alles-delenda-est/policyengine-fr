#!/usr/bin/env python3
"""Fail the build when the front-door docs drift from the code.

Two recurring drift failure modes are guarded here (see docs/specs/STRATEGY.md,
S5 — "Automate doc currency"):

1. **Test counts.** CLAUDE.md advertises a headline count like
   "(77 YAML tests + 37 pytest)". These rot silently every time a test is added.
   This check parses that claim and compares it to the *collected* counts
   (YAML cases counted directly; pytest via ``--collect-only``).

2. **Simplifications parity.** ``modelled_policies.yaml`` carries the
   machine-readable ``simplifications:`` list (the reviewer-gate's source of
   truth) and ``docs/coverage.md`` carries the human-readable numbered list of
   the same caveats. When one gains an entry and the other does not, the
   documented scope no longer matches the declared scope. This check asserts the
   two counts are equal.

Run: ``python bin/check_doc_currency.py`` (or ``make check-docs``).
Exit code 0 = in sync, 1 = drift (with a message naming the mismatch).

Deliberately conservative: it checks *counts and the advertised numbers*, not
prose, so it never fails on wording. If it ever becomes a nuisance, that means
the claim it guards was itself the thing going stale.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
TESTS_YAML_DIR = ROOT / "policyengine_fr" / "tests"
PYTEST_DIR = ROOT / "tests"
CLAUDE_MD = ROOT / "CLAUDE.md"
POLICIES_YAML = ROOT / "policyengine_fr" / "modelled_policies.yaml"
COVERAGE_MD = ROOT / "docs" / "coverage.md"


def count_yaml_cases() -> int:
    """Each ``output:`` key in a test YAML is one policyengine-core test case."""
    total = 0
    for path in TESTS_YAML_DIR.rglob("*.yaml"):
        for line in path.read_text(encoding="utf-8").splitlines():
            # A test case declares its expectation with an ``output:`` mapping.
            if re.match(r"\s*output:\s*$", line):
                total += 1
    return total


def count_pytest_tests() -> int:
    """Collected pytest count (honours parametrisation), via --collect-only."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(PYTEST_DIR), "--collect-only", "-q"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    m = re.search(r"(\d+) tests? collected", proc.stdout)
    if not m:
        raise SystemExit(
            "check_doc_currency: could not parse pytest collection output:\n"
            + proc.stdout
            + proc.stderr
        )
    return int(m.group(1))


def stated_counts() -> tuple[int, int]:
    """Parse '(<y> YAML tests + <p> pytest)' out of CLAUDE.md."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    m = re.search(r"\((\d+)\s*YAML tests\s*\+\s*(\d+)\s*pytest\)", text)
    if not m:
        raise SystemExit(
            "check_doc_currency: could not find the '(NN YAML tests + MM pytest)' "
            "claim in CLAUDE.md — did its wording change?"
        )
    return int(m.group(1)), int(m.group(2))


def count_simplifications() -> int:
    data = yaml.safe_load(POLICIES_YAML.read_text(encoding="utf-8"))
    return len(data["core"]["simplifications"])


def count_coverage_caveats() -> int:
    """Numbered items in the '⚠️ Partial coverage' section of coverage.md."""
    text = COVERAGE_MD.read_text(encoding="utf-8")
    lines = text.splitlines()
    in_section = False
    count = 0
    for line in lines:
        if line.startswith("## ") and "Partial coverage" in line:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if in_section and re.match(r"^\d+\.\s", line):
            count += 1
    return count


def main() -> int:
    failures: list[str] = []

    stated_yaml, stated_pytest = stated_counts()
    actual_yaml = count_yaml_cases()
    actual_pytest = count_pytest_tests()

    if actual_yaml != stated_yaml:
        failures.append(
            f"YAML test count: CLAUDE.md says {stated_yaml}, collected {actual_yaml}."
        )
    if actual_pytest != stated_pytest:
        failures.append(
            f"pytest count: CLAUDE.md says {stated_pytest}, collected {actual_pytest}."
        )

    n_simpl = count_simplifications()
    n_caveats = count_coverage_caveats()
    if n_simpl != n_caveats:
        failures.append(
            f"Simplifications parity: modelled_policies.yaml lists {n_simpl} "
            f"simplification(s) but docs/coverage.md numbers {n_caveats} caveat(s). "
            "Add the missing entry to whichever is behind."
        )

    if failures:
        print("Doc-currency drift detected:\n")
        for f in failures:
            print(f"  - {f}")
        print(
            "\nUpdate the stale doc (CLAUDE.md count and/or docs/coverage.md) so it "
            "matches the code, then re-run `make check-docs`."
        )
        return 1

    print(
        f"Docs in sync: {actual_yaml} YAML tests + {actual_pytest} pytest; "
        f"{n_simpl} simplifications == {n_caveats} coverage caveats."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
