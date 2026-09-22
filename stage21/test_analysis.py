"""Key stage 21 paths, using synthetic data and the accepted saved runs."""

import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location(
    "stage21", Path(__file__).with_name("analyze.py")
)
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def synthetic():
    return {
        "time_values": np.array([0, 0.001, 0.002]),
        "state_history": np.tile([0, 0, 2, -1], (3, 1)),
        "reference_position_history": np.tile([3, 4], (3, 1)),
        "end_effector_position_history": np.zeros((3, 2)),
        "reference_end_effector_position_history": np.tile([0.003, 0.004], (3, 1)),
        "applied_torque_history": np.tile([2, 3], (3, 1)),
        "saturation_history": np.array([[True, False], [False, False], [True, True]]),
    }


def test_metrics_have_correct_units_and_terminal_semantics():
    values, distance = analysis.measure(synthetic())
    assert values["overall_joint_rmse_rad"] == pytest.approx(np.sqrt(12.5))
    assert values["end_effector_rmse_m"] == pytest.approx(0.005)
    assert values["control_effort_nm2_s"] == pytest.approx(0.026)
    assert values["absolute_mechanical_work_j"] == pytest.approx(0.002)
    assert values["saturation_fraction"] == 0.5
    assert np.allclose(distance, 0.005)


@pytest.mark.parametrize("failure", ["nan", "shape", "time"])
def test_bad_history_rejected(failure):
    h = synthetic()
    if failure == "nan":
        h["applied_torque_history"] = np.full((3, 2), np.nan)
    elif failure == "shape":
        h["state_history"] = np.zeros((2, 4))
    else:
        h["time_values"] = np.array([0, 0.001, 0.001])
    with pytest.raises(ValueError):
        analysis.measure(h)


@pytest.mark.parametrize("failure", ["missing", "duplicate", "unknown"])
def test_bad_grid_rejected(failure):
    rows = [{"controller": c} for c in analysis.CONTROLLERS]
    if failure == "missing":
        rows.pop()
    elif failure == "duplicate":
        rows.append(rows[0])
    else:
        rows[0] = {"controller": "unknown"}
    with pytest.raises(ValueError):
        analysis.validate_summary(rows, "nominal")


def test_saved_inputs_complete_and_normalized():
    rows, histories, inputs = analysis.load_inputs()
    assert len(rows) == len(histories) == 42
    assert len(inputs) == 88
    nominal = [r for r in rows if r["experiment"] == "nominal"]
    assert all(r["rmse_ratio_to_own_nominal"] == 1 for r in nominal)
    assert all(r["recovered"] is None for r in nominal)
    disturbance = [r for r in rows if r["experiment"] == "disturbance"]
    assert [r["recovery_time_s"] for r in disturbance] == pytest.approx(
        [1.555, 0.087, 0.263]
    )


def test_existing_output_not_modified(tmp_path, monkeypatch):
    marker = tmp_path / "keep.txt"
    marker.write_text("keep")
    monkeypatch.setattr(analysis, "load_inputs", lambda _: ([], {}, {}))
    with pytest.raises(FileExistsError):
        analysis.build(tmp_path)
    assert marker.read_text() == "keep"
