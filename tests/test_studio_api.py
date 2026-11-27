"""Tests for `policyengine_fr.studio` microsimulation API & HTTP server."""

from __future__ import annotations

import json
import threading
import urllib.request

import pytest

from policyengine_fr.studio import (
    create_server,
    get_metadata,
    simulate_household,
)


def test_studio_metadata_exposes_policies_variables_and_lvt():
    meta = get_metadata()
    assert meta["years"] == ["2024", "2025"]
    assert len(meta["policies"]["simplifications"]) == 16
    assert "revenu_disponible" in meta["variables"]
    assert "prime_activite" in meta["variables"]
    assert len(meta["lvt"]["variants"]) == 5


def test_studio_simulate_smic_worker_and_curve():
    res = simulate_household(
        {
            "year": "2024",
            "household": {
                "couple": False,
                "adults": [{"age": 30, "salaire_brut": 21_203, "cadre": False}],
                "children": [],
            },
        }
    )
    assert res["reform_active"] is False
    base = res["baseline"]
    assert base["reduction_generale"] == pytest.approx(6_772.24, abs=1.0)
    assert base["prime_activite"] > 1_800.0
    assert base["revenu_disponible"] > base["salaire_net"]
    assert len(res["curve"]["points"]) == 61
    assert res["curve"]["points"][0]["rsa"] == pytest.approx(6_639.28, abs=1.0)


def test_studio_combined_lvt_and_dp6_reform_over_http():
    server = create_server("127.0.0.1", 0)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{port}/api/health", timeout=5
        ) as resp:
            assert json.loads(resp.read())["status"] == "ok"

        payload = {
            "year": "2025",
            "household": {
                "couple": False,
                "adults": [{"age": 68, "pension_retraite": 48_000}],
                "children": [],
                "patrimoine": {
                    "taxe_fonciere_locale": 2_000,
                    "valeur_terrain_imposable": 100_000,
                },
            },
            "reforms": {
                "lvt_scenario": "S1",
                "ir_freeze_2024": True,
                "dp6_underindex_pct": 2.0,
                "dp6_threshold_annual": 24_000,
            },
            "include_curve": False,
        }
        req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/simulate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            out = json.loads(resp.read())

        assert out["reform_active"] is True
        assert out["baseline"]["taxe_fonciere"] == pytest.approx(2_060.0)
        assert out["reform"]["taxe_fonciere"] == 0.0
        assert out["reform"]["taxe_valeur_sol"] == pytest.approx(1_100.0)
        assert out["dp6_clawback_share"] is not None
    finally:
        server.shutdown()
        server.server_close()
