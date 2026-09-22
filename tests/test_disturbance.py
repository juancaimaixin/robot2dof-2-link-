"""Boundary, recovery and output contracts for the disturbance experiment."""

import csv
import importlib.util
import json
from dataclasses import fields, replace
from pathlib import Path

import numpy as np
import pytest
import yaml

from robot2dof.benchmark import (
    FROZEN_CONFIGURATION_SHA256,
    DisturbanceRun,
    create_disturbance_scenario,
)
from robot2dof.controllers import ComputedTorqueGains, PIDGains
from robot2dof.disturbances import create_disturbance_torque_for_step
from robot2dof.metrics import compute_recovery_time
from robot2dof.parameters import RobotParams
from robot2dof.results_io import (
    build_disturbance_configuration,
    compute_configuration_sha256,
    save_disturbance_history,
    save_disturbance_manifest,
    save_disturbance_summary,
)
from robot2dof.simulation import ComputedTorqueSimulationResult, PIDSimulationResult

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "start,active", [(4.499, False), (4.5, True), (4.699, True), (4.7, False)]
)
def test_pulse_keeps_interval_gate_but_updates_stage_geometry(start, active):
    params = RobotParams()
    torque = create_disturbance_torque_for_step(start, 0.001, params)
    for time, q in (
        (start, np.array([0.3, -0.4])),
        (start + 0.001, np.array([0.5, 0.2])),
    ):
        expected = (
            np.array(
                [
                    -10 * (params.l1 * np.sin(q[0]) + params.l2 * np.sin(q.sum())),
                    -10 * params.l2 * np.sin(q.sum()),
                ]
            )
            if active
            else np.zeros(2)
        )
        np.testing.assert_allclose(torque(time, q), expected, rtol=0, atol=1e-14)


@pytest.mark.parametrize("start", [4.4995, 4.6995])
def test_pulse_rejects_straddling_intervals(start):
    with pytest.raises(ValueError, match="pulse boundary"):
        create_disturbance_torque_for_step(start, 0.001, RobotParams())


def test_recovery_reports_start_not_confirmation_and_resets_on_violation():
    time = 4.7 + np.arange(1001) * 0.001
    errors = np.full(time.size, 0.01)
    assert compute_recovery_time(time[:501], errors[:501]) == 0
    assert compute_recovery_time(time[:500], errors[:500]) is None
    errors[300] = 0.02
    assert compute_recovery_time(time, errors) == pytest.approx(0.301)
    errors[:] = 0.02
    assert compute_recovery_time(time, errors) is None


@pytest.fixture
def runs():
    time = 4.5 + np.arange(801) * 0.001
    q = np.array([0.3, -0.4])
    scenario = replace(
        create_disturbance_scenario(),
        waypoint_times=np.array([time[0], time[-1]]),
        waypoint_positions=np.tile(q, (2, 1)),
        initial_state=np.r_[q, 0.0, 0.0],
    )
    result = []
    for name in ("pid", "pid_gravity", "computed_torque"):
        ctc = name == "computed_torque"
        history_type = ComputedTorqueSimulationResult if ctc else PIDSimulationResult
        arrays = {
            field.name: np.zeros((time.size, 2)) for field in fields(history_type)
        }
        arrays.update(
            time_values=time.copy(),
            state_history=np.tile(scenario.initial_state, (time.size, 1)),
            reference_position_history=np.tile(q, (time.size, 1)),
            saturation_history=np.zeros((time.size, 2), dtype=bool),
        )
        gains = (
            ComputedTorqueGains(np.ones(2), np.ones(2))
            if ctc
            else PIDGains(np.ones(2), np.ones(2), np.ones(2))
        )
        result.append(
            DisturbanceRun(
                name,
                FROZEN_CONFIGURATION_SHA256,
                gains,
                scenario,
                history_type(**arrays),
            )
        )
    return result


def test_configuration_and_npz_round_trip_without_overwrite(runs, tmp_path):
    run = runs[0]
    configuration = build_disturbance_configuration(run)
    assert yaml.safe_load(yaml.safe_dump(configuration)) == configuration
    digest = compute_configuration_sha256(configuration)
    destination = save_disturbance_history(
        run, tmp_path / configuration["output"]["history"]
    )
    with np.load(destination, allow_pickle=False) as archive:
        for field in fields(run.simulation):
            np.testing.assert_array_equal(
                archive[field.name], getattr(run.simulation, field.name)
            )
        assert archive["configuration_sha256"].item() == digest
        assert np.count_nonzero(archive["external_force_history_n"][:, 0]) == 200
        np.testing.assert_array_equal(
            archive["external_force_history_n"][-1], [0.0, 0.0]
        )
        assert not np.array_equal(
            archive["external_torque_history"], archive["applied_torque_history"]
        )
    before = destination.read_bytes()
    with pytest.raises(FileExistsError):
        save_disturbance_history(run, destination)
    assert destination.read_bytes() == before
    snapshot = build_disturbance_configuration(run)
    snapshot["trajectory"]["waypoint_positions"][0][0] = 999
    assert run.scenario.waypoint_positions[0, 0] == 0.3


def test_invalid_histories_do_not_create_output(runs, tmp_path):
    run = replace(
        runs[0],
        simulation=replace(runs[0].simulation, state_history=np.full((801, 4), np.nan)),
    )
    folder = tmp_path / "invalid"
    with pytest.raises(ValueError):
        save_disturbance_history(run, folder / "history.npz")
    assert not folder.exists()
    with pytest.raises(ValueError, match="npz"):
        save_disturbance_history(runs[0], folder / "history.csv")
    assert not folder.exists()


def test_summary_unconfirmed_recovery_is_empty_and_duplicate_rejected(runs, tmp_path):
    run = runs[0]
    runs[0] = replace(
        run,
        simulation=replace(
            run.simulation, reference_position_history=np.zeros((801, 2))
        ),
    )
    destination = save_disturbance_summary(runs[::-1], tmp_path / "summary.csv")
    with destination.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    assert [row["controller"] for row in rows] == [run.controller for run in runs]
    assert rows[0]["recovered"] == "False" and rows[0]["recovery_time_s"] == ""
    assert rows[1]["recovered"] == "True" and float(rows[1]["recovery_time_s"]) == 0
    with pytest.raises(ValueError, match="one run"):
        save_disturbance_summary([runs[0]] * 3, tmp_path / "bad.csv")
    assert not (tmp_path / "bad.csv").exists()


def test_manifest_hash_links_and_plot_rejects_inconsistent_recovery(runs, tmp_path):
    for run in runs:
        config = build_disturbance_configuration(run)
        save_disturbance_history(run, tmp_path / config["output"]["history"])
        yaml_path, metadata_path = save_disturbance_manifest(run, tmp_path, ROOT)
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        assert metadata["configuration_sha256"] == compute_configuration_sha256(
            yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        )
        assert "src/robot2dof/disturbances.py" in metadata["source_sha256"]
    csv_path = save_disturbance_summary(runs, tmp_path / "disturbance_metrics.csv")
    spec = importlib.util.spec_from_file_location(
        "plot_disturbance", ROOT / "experiments/plot_disturbance_benchmark.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Reject before creating a figure, so corrupt input cannot yield a misleading plot.
    csv_path.write_text(
        csv_path.read_text(encoding="utf-8").replace("True,0.0", "False,0.0", 1),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="disagree"):
        module.plot_disturbance_benchmark(tmp_path)
    assert not (tmp_path / "disturbance_comparison.png").exists()
