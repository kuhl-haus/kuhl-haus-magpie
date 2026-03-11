"""Tests for canary/env.py and metrics/env.py environment variable loading."""
import importlib


def test_canary_env_default_values():
    import kuhl_haus.magpie.canary.env as env
    importlib.reload(env)
    assert env.DEFAULT_CANARY_INVOCATION_INTERVAL == 300
    assert env.DEFAULT_CANARY_INVOCATION_COUNT == -1
    assert env.CONFIG_API is None
    assert env.CANARY_CONFIG_FILE_PATH == "./config/canary.json"
    assert env.RESOLVERS_CONFIG_FILE_PATH == "./config/resolvers.json"


def test_canary_env_overrides(monkeypatch):
    monkeypatch.setenv("DEFAULT_CANARY_INVOCATION_INTERVAL", "60")
    monkeypatch.setenv("DEFAULT_CANARY_INVOCATION_COUNT", "5")
    monkeypatch.setenv("CONFIG_API", "http://config.api")
    monkeypatch.setenv("CANARY_CONFIG_FILE_PATH", "/custom/canary.json")
    monkeypatch.setenv("RESOLVERS_CONFIG_FILE_PATH", "/custom/resolvers.json")

    import kuhl_haus.magpie.canary.env as env
    importlib.reload(env)

    assert env.DEFAULT_CANARY_INVOCATION_INTERVAL == 60
    assert env.DEFAULT_CANARY_INVOCATION_COUNT == 5
    assert env.CONFIG_API == "http://config.api"
    assert env.CANARY_CONFIG_FILE_PATH == "/custom/canary.json"
    assert env.RESOLVERS_CONFIG_FILE_PATH == "/custom/resolvers.json"


def test_metrics_env_default_values():
    import kuhl_haus.magpie.metrics.env as env
    importlib.reload(env)
    assert env.THREAD_POOL_SIZE == 20
    assert env.LOG_LEVEL == "INFO"
    assert env.APP_LOGS_PATH is None
    assert env.CARBON_CONFIG["server_ip"] is None
    assert env.CARBON_CONFIG["pickle_port"] == 2004
    assert env.NAMESPACE_ROOT == "default"
    assert env.METRIC_NAMESPACE == "dev"
    assert env.POD_NAME is None


def test_metrics_env_overrides(monkeypatch):
    monkeypatch.setenv("THREAD_POOL_SIZE", "10")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("APP_LOGS_PATH", "/var/log/app.log")
    monkeypatch.setenv("CARBON_SERVER_IP", "192.0.2.10")
    monkeypatch.setenv("CARBON_PICKLE_PORT", "2005")
    monkeypatch.setenv("NAMESPACE_ROOT", "prod")
    monkeypatch.setenv("METRIC_NAMESPACE", "myapp")
    monkeypatch.setenv("POD_NAME", "pod-abc123")

    import kuhl_haus.magpie.metrics.env as env
    importlib.reload(env)

    assert env.THREAD_POOL_SIZE == 10
    assert env.LOG_LEVEL == "DEBUG"
    assert env.APP_LOGS_PATH == "/var/log/app.log"
    assert env.CARBON_CONFIG["server_ip"] == "192.0.2.10"
    assert env.CARBON_CONFIG["pickle_port"] == "2005"
    assert env.NAMESPACE_ROOT == "prod"
    assert env.METRIC_NAMESPACE == "myapp"
    assert env.POD_NAME == "pod-abc123"
