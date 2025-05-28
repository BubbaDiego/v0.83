import os
import types
import importlib
import sys

import pytest

flask = importlib.import_module("flask")
if not getattr(flask, "Flask", None):
    pytest.skip("Flask not available", allow_module_level=True)
from flask import Flask
from app.system_bp import system_bp


class DummySystem:
    def __init__(self):
        self.store = {}

    def get_active_theme_profile(self):
        return {}

    def get_var(self, key):
        return self.store.get(key)

    def set_var(self, key, value):
        self.store[key] = value


class DummyLocker:
    def __init__(self):
        self.system = DummySystem()


def make_client():
    app = Flask(__name__)
    app.config["TESTING"] = True
    app.register_blueprint(system_bp)
    app.data_locker = DummyLocker()
    return app.test_client()


def test_validate_api_success(monkeypatch):
    client = make_client()
    dl = client.application.data_locker
    dl.system.set_var("xcom_providers", {"api": {"account_sid": "sid", "auth_token": "token"}})

    resp_obj = types.SimpleNamespace(status_code=200, json=lambda: {}, text="")
    monkeypatch.setattr(importlib.import_module("requests"), "get", lambda *a, **k: resp_obj)

    resp = client.post("/system/xcom_config/validate_api")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_xcom_api_status_ok(monkeypatch):
    client = make_client()

    class DummyClient:
        def __init__(self, api_key=None):
            self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda *a, **k: None))

    monkeypatch.setitem(sys.modules, "openai", types.SimpleNamespace(OpenAI=DummyClient))

    cts = importlib.import_module("xcom.check_twilio_heartbeart_service")

    class DummyService:
        def __init__(self, *a, **k):
            pass

        def check(self, dry_run=True):
            return {"success": True}

    monkeypatch.setattr(cts, "CheckTwilioHeartbeartService", DummyService)
    monkeypatch.setenv("OPENAI_API_KEY", "test")

    resp = client.get("/system/xcom_api_status")
    assert resp.status_code == 200
    assert resp.get_json() == {"chatgpt": "ok", "api": "ok"}


def test_xcom_config_template_contains_status_button():
    client = make_client()
    resp = client.get("/system/xcom_config")
    assert resp.status_code == 200
    html = resp.data.decode()
    assert "checkAllApis" in html
    assert "apiStatusList" in html
