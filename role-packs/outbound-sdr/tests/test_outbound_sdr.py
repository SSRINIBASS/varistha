"""Validation and conformance tests for Outbound SDR role pack."""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

# Add packages/spec/src to path for validator
spec_pkg = Path(__file__).resolve().parents[3] / "packages" / "spec" / "src"
if str(spec_pkg) not in sys.path:
    sys.path.insert(0, str(spec_pkg))

from validator import validate_spec  # noqa: E402  # pyright: ignore[reportMissingImports]

PACK_DIR = Path(__file__).resolve().parents[1]


def test_agent_spec_validates_against_canonical_schema() -> None:
    agent_yaml_path = PACK_DIR / "agent.yaml"
    assert agent_yaml_path.exists(), "agent.yaml must exist in role pack root"

    raw = yaml.safe_load(agent_yaml_path.read_text(encoding="utf-8"))
    agent = validate_spec(raw)

    assert agent.metadata.name == "outbound-sdr"
    assert agent.metadata.stage == "prototype"
    assert agent.spec.autonomy == "L1"
    assert agent.spec.budget is not None
    assert agent.spec.budget.max_usd_per_run == 0.30


def test_plugins_exist_in_plugin_ecosystem() -> None:
    agent_yaml_path = PACK_DIR / "agent.yaml"
    raw = yaml.safe_load(agent_yaml_path.read_text(encoding="utf-8"))
    plugins_declared = [p["name"] for p in raw["spec"]["plugins"]]

    repo_plugins = PACK_DIR.parents[1] / "plugins"
    for plugin_name in plugins_declared:
        plugin_dir = repo_plugins / plugin_name
        assert plugin_dir.exists(), (
            f"Declared plugin '{plugin_name}' missing from plugins/ directory"
        )
        assert (plugin_dir / "plugin.yaml").exists(), f"Plugin '{plugin_name}' missing plugin.yaml"


def test_prompts_and_instructions_file_exists_and_complete() -> None:
    agent_yaml_path = PACK_DIR / "agent.yaml"
    raw = yaml.safe_load(agent_yaml_path.read_text(encoding="utf-8"))
    instructions_rel = raw["spec"]["instructions"]

    prompt_path = PACK_DIR / instructions_rel
    assert prompt_path.exists(), f"Prompt file '{instructions_rel}' not found"

    content = prompt_path.read_text(encoding="utf-8")
    assert "Operating Principles" in content
    assert "Lavender 90+" in content
    assert "Multi-Channel 3-Touch" in content
    assert "Objection Pre-emption" in content
    assert "Structured Output Format" in content


def test_eval_suite_is_valid_and_structured() -> None:
    eval_suite_path = PACK_DIR / "evals" / "suite.yaml"
    assert eval_suite_path.exists(), "evals/suite.yaml must exist"

    data = yaml.safe_load(eval_suite_path.read_text(encoding="utf-8"))
    assert data["name"] == "outbound-sdr-benchmark"
    assert data["min_pass_rate"] >= 0.85
    assert len(data["cases"]) >= 5

    case_ids = [c["id"] for c in data["cases"]]
    assert "case-ai-founder-outreach" in case_ids
    assert "case-enterprise-vp-engineering" in case_ids
