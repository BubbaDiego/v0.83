import importlib.util
from pathlib import Path
import types
import sys


def load_module():
    base = Path(__file__).resolve().parents[1] / "gpt"
    pkg = types.ModuleType("gpt")
    sys.modules.setdefault("gpt", pkg)

    ctx_path = base / "context_loader.py"
    ctx_spec = importlib.util.spec_from_file_location("gpt.context_loader", ctx_path)
    ctx_mod = importlib.util.module_from_spec(ctx_spec)
    assert ctx_spec and ctx_spec.loader
    ctx_spec.loader.exec_module(ctx_mod)
    sys.modules["gpt.context_loader"] = ctx_mod
    setattr(pkg, "context_loader", ctx_mod)

    path = base / "oracle.py"
    spec = importlib.util.spec_from_file_location("gpt.oracle", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    sys.modules["gpt.oracle"] = module
    return module


def test_oracle_get_context(monkeypatch):
    mod = load_module()

    class DummyAlerts:
        def get_all_alerts(self):
            return ["a1", "a2"]

    class DummyPrices:
        def get_all_prices(self):
            return [1, 2, 3]

    class DummyLocker:
        def __init__(self):
            self.alerts = DummyAlerts()
            self.prices = DummyPrices()

        def get_last_update_times(self):
            return {"x": 1}

    def fake_ctx():
        return [{"role": "system", "content": "ctx"}]

    monkeypatch.setattr(mod, "get_context_messages", fake_ctx)
    oracle = mod.Oracle("portfolio", DummyLocker())
    msgs = oracle.get_context()
    assert msgs[0]["role"] == "system"
    assert msgs[-1]["content"] == oracle.instructions
