#!/usr/bin/env python3
"""TEMPORARY: run the independent statute review via Gemini instead of Claude.

Rerouted while the `ANTHROPIC_API_KEY` secret is unavailable (see
`docs/reviewer-agent-gate.md`). To restore the Claude reviewer, revert this file
and the `claude-review.yml` step back to the `anthropics/claude-code-action`.

Advisory by design: it posts a PR comment and NEVER fails the build. Any error
(missing key, unknown model, API failure) exits 0 with a warning, so the check
stays green — matching the gate's "never a red X before it's configured" intent.

Env (from the workflow):
  GEMINI_API_KEY   the Google AI Studio / Generative Language API key (secret)
  GEMINI_MODEL     model id, default "gemini-3.6-flash" (override via repo var)
  GH_TOKEN         GITHUB_TOKEN, for `gh pr comment`
  PR_NUMBER, BASE_SHA, HEAD_SHA
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

MODEL = os.environ.get("GEMINI_MODEL", "gemini-3.6-flash")
KEY = os.environ.get("GEMINI_API_KEY", "")
PR = os.environ.get("PR_NUMBER", "")
BASE = os.environ.get("BASE_SHA", "")
HEAD = os.environ.get("HEAD_SHA", "")

REVIEW_PATHS = [
    "policyengine_fr/variables",
    "policyengine_fr/parameters",
    "policyengine_fr/tests",
]
MAX_DIFF_CHARS = 200_000

PROMPT_HEADER = """You are an INDEPENDENT reviewer of a French tax-benefit
microsimulation pull request (policyengine-fr, built on policyengine-core). You
did NOT write this code. Be adversarial: assume the author may have misread the
law. Review ONLY the changed variables, parameters, and tests below against
French statute (CGI / CSS / CASF / arrêtés).

Report findings tied to specific articles / URLs:
1. Statute fidelity — does each formula match the cited article? Is the
   `reference:` real, current and on-point (not a vaguely-related page)?
2. Independent reference values — are the test expected values traceable to an
   INDEPENDENT source (openfisca-france parameters at
   github.com/openfisca/openfisca-france, or the official DGFiP/CAF simulator),
   not merely re-derived from this same code? Hand-check at least one value.
3. Silent scope-narrowing — every simplification (e.g. a means-test on
   current-year income instead of base ressources N-2, a benefit without its
   phase-out) MUST be explicit in the variable docstring AND
   modelled_policies.yaml. Flag undocumented ones.
4. Entity & period — correct entity (individu / foyer_fiscal / famille /
   menage) and definition_period (YEAR vs MONTH); correct cross-entity
   aggregation (no double counting).
5. Edge cases — zero income, exactly-at-threshold, single / couple / parent
   isolé, many children, age boundaries (14 / 18 / 20): are they tested?
6. Vectorisation & safety — numpy-safe (max_/min_/where), no divide-by-zero, no NaN.

End with a clear verdict line: `VERDICT: APPROVE` or `VERDICT: REQUEST CHANGES`,
followed by the prioritised findings.

--- CHANGED FILES (unified diff) ---
"""


def warn_and_exit(msg: str) -> None:
    print(f"::warning::{msg}")
    sys.exit(0)


def main() -> None:
    if not KEY:
        warn_and_exit("GEMINI_API_KEY not set; skipping advisory statute review.")

    diff = subprocess.run(
        ["git", "diff", f"{BASE}...{HEAD}", "--", *REVIEW_PATHS],
        capture_output=True,
        text=True,
    ).stdout
    if not diff.strip():
        print("No variable/parameter/test changes to review.")
        return
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n…(diff truncated for length)…"

    payload = {"contents": [{"parts": [{"text": PROMPT_HEADER + diff}]}]}
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{MODEL}:generateContent?key={KEY}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.load(resp)
        review = data["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:500]
        warn_and_exit(f"Gemini API HTTP {e.code} ({MODEL}): {detail}")
    except (urllib.error.URLError, KeyError, IndexError, ValueError) as e:
        warn_and_exit(f"Gemini review call failed ({type(e).__name__}: {e}).")

    comment = (
        f"## 🔎 Statute review — Gemini (`{MODEL}`) · temporary reroute\n\n"
        f"{review}\n\n"
        "---\n"
        "_Advisory review, routed through Gemini while the Claude reviewer key is "
        "unavailable. Not blocking; findings are for the maintainer to weigh._"
    )
    result = subprocess.run(
        ["gh", "pr", "comment", PR, "--body", comment],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        warn_and_exit(f"Could not post PR comment: {result.stderr.strip()}")
    print("Posted Gemini statute review.")


if __name__ == "__main__":
    main()
