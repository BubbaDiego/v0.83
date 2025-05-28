import importlib
import importlib.util
import sys
import types
from pathlib import Path
import json

import pytest


def test_strategy_manager_builtin_loading():
    sm_mod = importlib.import_module("oracle_core.strategy_manager")
    manager = sm_mod.StrategyManager()
    assert "safe" in manager.list_strategies()
    assert "profit_management" in manager.list_strategies()


def test_strategy_manager_alias(monkeypatch):
    sm_mod = importlib.import_module("oracle_core.strategy_manager")
    manager = sm_mod.StrategyManager()
    # 'aggressive' should resolve to the built-in 'degen' strategy
    strat = manager.get("aggressive")
    assert strat.name == "degen"


def setup_core(monkeypatch):
    base = Path(__file__).resolve().parents[1]

    class DummyClient:
        def __init__(self, *a, **k):
            pass

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyClient))
    monkeypatch.setenv("OPENAI_API_KEY", "test")
    monkeypatch.setitem(sys.modules, "dotenv", types.SimpleNamespace(load_dotenv=lambda *a, **k: False))
    sys.modules.pop("gpt", None)
    import importlib
    importlib.invalidate_caches()

    class DummyAlerts:
        def get_all_alerts(self):
            return []

    class DummyPrices:
        def get_all_prices(self):
            return []

    class DummyPortfolio:
        def get_latest_snapshot(self):
            return {}

    class DummySystem:
        def get_last_update_times(self):
            return {}

    class DummyLocker:
        def __init__(self, *a, **k):
            self.alerts = DummyAlerts()
            self.prices = DummyPrices()
            self.portfolio = DummyPortfolio()
            self.system = DummySystem()

        def get_last_update_times(self):
            return {}

        def get_portfolio_history(self):
            return []

    monkeypatch.setitem(sys.modules, "data.data_locker", types.SimpleNamespace(DataLocker=DummyLocker))

    import oracle_core
    monkeypatch.setattr(oracle_core.OracleCore, "query_gpt", lambda self, msgs: msgs)

    gc_path = base / "gpt" / "gpt_core.py"
    pkg = types.ModuleType("gpt")
    pkg.__path__ = [str(base / "gpt")]
    sys.modules.setdefault("gpt", pkg)
    spec = importlib.util.spec_from_file_location("gpt.gpt_core", gc_path)
    gpt_core = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(gpt_core)
    return gpt_core.GPTCore


def test_gptcore_ask_oracle_applies_strategy(monkeypatch):
    GPTCore = setup_core(monkeypatch)
    core = GPTCore()
    messages = core.ask_oracle("portfolio", "safe")
    ctx = json.loads(messages[1]["content"])
    assert ctx.get("strategy_modifiers", {}).get("risk_level") == "low"
    assert messages[-1]["content"] == "Answer briefly and focus on risk mitigation."


@pytest.fixture
def client(monkeypatch):
    flask = importlib.import_module("flask")
    if not getattr(flask, "Flask", None):
        pytest.skip("Flask not available", allow_module_level=True)
    GPTCore = setup_core(monkeypatch)
    bp_mod = importlib.import_module("gpt.gpt_bp")
    from flask import Flask
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(bp_mod.gpt_bp)
    with app.test_client() as client:
        yield client


def test_oracle_endpoint_with_strategy(client):
    resp = client.get("/gpt/oracle/portfolio?strategy=safe")
    assert resp.status_code == 200
    data = resp.get_json()
    ctx = json.loads(data["reply"][1]["content"])
    assert ctx.get("strategy_modifiers", {}).get("risk_level") == "low"
    assert data["reply"][-1]["content"] == "Answer briefly and focus on risk mitigation."
