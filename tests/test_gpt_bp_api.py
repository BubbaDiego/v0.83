import pytest
import importlib
import importlib.util
import sys
import types
from pathlib import Path

flask = importlib.import_module("flask")
if not getattr(flask, "Flask", None):
    pytest.skip("Flask not available", allow_module_level=True)
from flask import Flask


def load_blueprint():
    base = Path(__file__).resolve().parents[1] / "gpt"
    pkg = types.ModuleType("gpt")
    pkg.__path__ = [str(base)]
    sys.modules.setdefault("gpt", pkg)

    core_mod = types.ModuleType("gpt.gpt_core")

    class DummyCore:
        def __init__(self, *a, **k):
            pass

        def analyze(self, instructions: str = "") -> str:
            return "analysis"

        def ask_gpt_about_portfolio(self) -> str:
            return "portfolio"

        def ask_oracle(self, topic: str, instructions: str = "") -> str:
            if topic != "portfolio":
                raise ValueError("Unknown topic")
            return "portfolio result"

    core_mod.GPTCore = DummyCore
    sys.modules["gpt.gpt_core"] = core_mod

    path = base / "gpt_bp.py"
    spec = importlib.util.spec_from_file_location("gpt.gpt_bp", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.gpt_bp


@pytest.fixture
def client():
    gpt_bp = load_blueprint()
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(gpt_bp)
    with app.test_client() as client:
        yield client


def test_oracle_portfolio_reply(client):
    resp = client.get("/gpt/oracle/portfolio")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "reply" in data


def test_oracle_invalid_topic(client):
    resp = client.get("/gpt/oracle/unknown")
    assert resp.status_code == 400
    data = resp.get_json()
    assert "error" in data
