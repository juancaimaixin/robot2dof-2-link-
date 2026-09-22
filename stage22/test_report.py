"""Report assembly must remain tied to accepted data and fail visibly."""

import importlib.util
import json
import re
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location(
    "stage22", Path(__file__).with_name("build_report.py")
)
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


def test_missing_template_field_rejected():
    with pytest.raises(ValueError, match="Missing report fields"):
        report.substitute("Value @@absent@@", {})


def test_source_tampering_rejected(tmp_path):
    (tmp_path / "summary.csv").write_text("altered data")
    manifest = {"outputs_sha256": {"summary.csv": "0" * 64}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Stage 21 output changed"):
        report.validate_data(tmp_path)


def test_full_assembly_and_data_binding(tmp_path):
    output = report.build(tmp_path / "report", render=False)
    qmd = (output / "report.qmd").read_text(encoding="utf-8")
    assert "@@" not in qmd
    assert len(list((output / "figures").glob("*.png"))) == 8
    assert (output / "summary.csv").read_bytes() == (
        report.DATA / "summary.csv"
    ).read_bytes()
    identifiers = set(re.findall(r"\{#(fig-[\w-]+)", qmd))
    references = set(re.findall(r"@(fig-[\w-]+)", qmd))
    assert len(identifiers) == 8
    assert references <= identifiers
    rows, manifest = report.validate_data(report.DATA)
    values = report.make_values(rows, manifest)
    assert values["run_count"] == 42
    assert values["nominal_rmse"] == "1.115037 / 0.152634 / 0.004992"
    assert values["recovery"] == "1.555 / 0.087 / 0.263"
    # Change a source value in memory: both the narrative and table must change.
    changed = [dict(r) for r in rows]
    changed[0]["overall_joint_rmse_deg"] = "9.125"
    updated = report.make_values(changed, manifest)
    assert updated["nominal_rmse"].startswith("9.125000")
    assert "9.125000" in updated["nominal_table"]
    assert values["nominal_rmse"] in qmd


def test_existing_directory_preserved(tmp_path):
    marker = tmp_path / "keep.txt"
    marker.write_text("keep")
    with pytest.raises(FileExistsError):
        report.build(tmp_path, render=False)
    assert marker.read_text() == "keep"
