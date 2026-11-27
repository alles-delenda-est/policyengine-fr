"""Tests for `policyengine_fr.studio` microsimulation API & HTTP server."""

from __future__ import annotations

import io
import json
import threading
import urllib.error
import urllib.request

import pytest

from policyengine_fr.studio import (
    MAX_REQUEST_BYTES,
    application,
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

        # Invalid JSON returns sanitized 400 error without internal exception leak
        bad_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/simulate",
            data=b"{not-valid-json",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc_bad:
            urllib.request.urlopen(bad_req, timeout=5)
        assert exc_bad.value.code == 400
        assert json.loads(exc_bad.value.read())["error"] == "Invalid simulation request"

        # Oversized body (> 64 KiB) is rejected with 413
        big_req = urllib.request.Request(
            f"http://127.0.0.1:{port}/api/simulate",
            data=b"{" + b" " * 70_000 + b"}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with pytest.raises(urllib.error.HTTPError) as exc_big:
            urllib.request.urlopen(big_req, timeout=5)
        assert exc_big.value.code == 413
    finally:
        server.shutdown()
        server.server_close()


def _call_wsgi(
    method: str,
    path: str,
    body: bytes = b"",
    headers: dict[str, str] | None = None,
    include_content_length: bool = True,
) -> tuple[str, dict[str, str], bytes]:
    environ: dict[str, object] = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "wsgi.input": io.BytesIO(body),
    }
    if include_content_length and body:
        environ["CONTENT_LENGTH"] = str(len(body))
    for k, v in (headers or {}).items():
        lk = k.lower()
        if lk == "origin":
            environ["HTTP_ORIGIN"] = v
        elif lk == "host":
            environ["HTTP_HOST"] = v
        elif lk == "content-length":
            environ["CONTENT_LENGTH"] = v

    captured: dict[str, object] = {}

    def start_response(status_str: str, resp_headers: list[tuple[str, str]]) -> None:
        captured["status"] = status_str
        captured["headers"] = {k.lower(): v for k, v in resp_headers}

    chunks = application(environ, start_response)
    return str(captured["status"]), dict(captured["headers"]), b"".join(chunks)


def test_studio_wsgi_application_endpoints_and_headers():
    status, hdrs, body = _call_wsgi("GET", "/api/health")
    assert status.startswith("200")
    assert json.loads(body)["status"] == "ok"
    assert hdrs["x-content-type-options"] == "nosniff"
    assert hdrs["x-frame-options"] == "DENY"

    h_status, h_hdrs, h_body = _call_wsgi("HEAD", "/api/health")
    assert h_status.startswith("200")
    assert h_body == b""
    assert int(h_hdrs["content-length"]) == len(body)

    nf_status, _, _ = _call_wsgi("GET", "/api/unknown")
    assert nf_status.startswith("404")

    sim_payload = json.dumps(
        {
            "year": "2024",
            "household": {
                "couple": False,
                "adults": [{"age": 32, "salaire_brut": 30_000}],
            },
            "include_curve": False,
        }
    ).encode("utf-8")
    ok_status, ok_hdrs, ok_body = _call_wsgi("POST", "/api/simulate", body=sim_payload)
    assert ok_status.startswith("200")
    assert ok_hdrs["x-content-type-options"] == "nosniff"
    assert "revenu_disponible" in json.loads(ok_body)["baseline"]

    big_status, _, _ = _call_wsgi(
        "POST",
        "/api/simulate",
        body=b"{" + b" " * (MAX_REQUEST_BYTES + 10) + b"}",
        include_content_length=False,
    )
    assert big_status.startswith("413")


def test_studio_static_ui_dist_and_cache_headers(tmp_path, monkeypatch):
    dist_dir = tmp_path / "dist"
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text(
        "<!doctype html><div id='root'></div>", encoding="utf-8"
    )
    (assets_dir / "app-abc123.js").write_text("console.log('ok');", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("TOP_SECRET", encoding="utf-8")

    monkeypatch.setenv("STUDIO_UI_DIST", str(dist_dir))

    status_root, hdrs_root, body_root = _call_wsgi("GET", "/")
    assert status_root.startswith("200")
    assert hdrs_root["cache-control"] == "no-cache"
    assert b"<div id='root'></div>" in body_root

    status_js, hdrs_js, body_js = _call_wsgi("GET", "/assets/app-abc123.js")
    assert status_js.startswith("200")
    assert hdrs_js["cache-control"] == "public, max-age=31536000, immutable"
    assert b"console.log('ok');" in body_js

    status_spa, _, body_spa = _call_wsgi("GET", "/share/demo")
    assert status_spa.startswith("200")
    assert b"<div id='root'></div>" in body_spa

    status_trav, _, body_trav = _call_wsgi("GET", "/../secret.txt")
    assert status_trav.startswith("200")
    assert b"TOP_SECRET" not in body_trav
    assert b"<div id='root'></div>" in body_trav


def test_studio_cors_same_origin_and_allowed_origins(monkeypatch):
    monkeypatch.delenv("STUDIO_ALLOWED_ORIGINS", raising=False)

    _, hdrs_local, _ = _call_wsgi(
        "OPTIONS", "/api/simulate", headers={"Origin": "http://localhost:5173"}
    )
    assert hdrs_local.get("access-control-allow-origin") == "http://localhost:5173"

    _, hdrs_same, _ = _call_wsgi(
        "OPTIONS",
        "/api/simulate",
        headers={
            "Origin": "https://demo-tunnel.trycloudflare.com",
            "Host": "demo-tunnel.trycloudflare.com",
        },
    )
    assert (
        hdrs_same.get("access-control-allow-origin")
        == "https://demo-tunnel.trycloudflare.com"
    )

    _, hdrs_other, _ = _call_wsgi(
        "OPTIONS",
        "/api/simulate",
        headers={"Origin": "https://evil.example", "Host": "studio.example"},
    )
    assert "access-control-allow-origin" not in hdrs_other

    monkeypatch.setenv("STUDIO_ALLOWED_ORIGINS", "https://trusted.example")
    _, hdrs_cfg, _ = _call_wsgi(
        "OPTIONS",
        "/api/simulate",
        headers={"Origin": "https://trusted.example", "Host": "studio.example"},
    )
    assert hdrs_cfg.get("access-control-allow-origin") == "https://trusted.example"
