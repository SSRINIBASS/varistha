"""Tests validating that all example Agent Specs in examples/ conform to spec schema."""

from pathlib import Path

from validator import validate_spec_yaml


def get_repo_root() -> Path:
    """Find the repository root relative to this test file."""
    # packages/spec/tests/test_examples_validity.py -> 4 levels up
    return Path(__file__).resolve().parents[3]


def test_examples_exist_and_validate() -> None:
    """Iterate through all .yaml files in examples/ and assert zero validation errors."""
    root = get_repo_root()
    examples_dir = root / "examples"
    assert examples_dir.exists(), "Missing examples/ directory"

    yaml_files = list(examples_dir.glob("*.yaml")) + list(examples_dir.glob("*.yml"))
    assert len(yaml_files) >= 3, f"Expected at least 3 example yaml specs, found {len(yaml_files)}"

    for yaml_file in yaml_files:
        content = yaml_file.read_text(encoding="utf-8")
        spec = validate_spec_yaml(content)
        assert spec.apiVersion == "varistha/v1"
        assert spec.kind == "Agent"
        assert spec.metadata.name == yaml_file.stem
        assert "@" in spec.metadata.owner
        assert spec.spec.role is not None
        assert spec.spec.model.primary is not None
        assert spec.spec.autonomy in ("L0", "L1", "L2", "L3")
        assert len(spec.spec.plugins) > 0
        if spec.spec.budget:
            assert spec.spec.budget.max_usd_per_run > 0
            assert spec.spec.budget.max_usd_per_day > 0
