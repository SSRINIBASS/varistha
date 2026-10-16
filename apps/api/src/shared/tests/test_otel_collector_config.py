"""Tests validating OpenTelemetry Collector configuration and Compose profile schemas."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[5]
DEPLOY_DIR = REPO_ROOT / "deploy"


def test_otel_collector_config_yaml_validity() -> None:
    """Ensure deploy/otel-collector-config.yaml is valid YAML with mandatory OTel pipelines."""
    config_file = DEPLOY_DIR / "otel-collector-config.yaml"
    assert config_file.exists(), f"Missing config file: {config_file}"

    with config_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert isinstance(data, dict)
    assert "receivers" in data
    assert "processors" in data
    assert "exporters" in data
    assert "service" in data

    # Verify receivers
    otlp_rcv = data["receivers"].get("otlp", {})
    protocols = otlp_rcv.get("protocols", {})
    assert "grpc" in protocols
    assert "http" in protocols
    assert ":4317" in protocols["grpc"].get("endpoint", "")
    assert ":4318" in protocols["http"].get("endpoint", "")

    # Verify processors
    assert "batch" in data["processors"]
    assert "memory_limiter" in data["processors"]

    # Verify fan-out exporters
    exporters = data["exporters"]
    assert "otlphttp/varistha" in exporters
    assert "debug" in exporters
    varistha_endpoint = exporters["otlphttp/varistha"].get("endpoint", "")
    assert "/v1/traces" in varistha_endpoint

    # Verify pipelines
    traces_pipeline = data["service"].get("pipelines", {}).get("traces", {})
    assert "otlp" in traces_pipeline.get("receivers", [])
    assert "batch" in traces_pipeline.get("processors", [])
    assert "otlphttp/varistha" in traces_pipeline.get("exporters", [])


def test_docker_compose_otel_profile_declaration() -> None:
    """Ensure docker-compose.yml defines otel-collector strictly behind the 'otel' profile."""
    compose_file = DEPLOY_DIR / "docker-compose.yml"
    assert compose_file.exists()

    with compose_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    assert "otel-collector" in services

    collector = services["otel-collector"]
    assert "otel" in collector.get("profiles", [])
    assert "otel/opentelemetry-collector-contrib" in collector.get("image", "")

    # Verify core services have no profiles (they run on default docker compose up)
    for core_service in ["postgres", "api", "worker", "ui"]:
        assert core_service in services
        assert "profiles" not in services[core_service]


def test_docker_compose_otel_overlay_file() -> None:
    """Ensure deploy/docker-compose.otel.yml is a valid override compose file."""
    overlay_file = DEPLOY_DIR / "docker-compose.otel.yml"
    assert overlay_file.exists()

    with overlay_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    services = data.get("services", {})
    assert "otel-collector" in services
    assert "4317:4317" in services["otel-collector"].get("ports", [])
    assert "4318:4318" in services["otel-collector"].get("ports", [])


def test_env_example_contains_otel_fanout_vars() -> None:
    """Ensure .env.example contains all documented OTel fan-out environment variables."""
    env_file = DEPLOY_DIR / ".env.example"
    assert env_file.exists()

    content = env_file.read_text(encoding="utf-8")
    assert "OTEL_EXPORTER_OTLP_ENDPOINT" in content
    assert "LANGFUSE_HOST" in content
    assert "TEMPO_OTLP_ENDPOINT" in content
