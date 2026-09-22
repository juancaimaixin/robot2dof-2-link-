"""Ensure an entirely unrecovered experiment still has a valid visualization."""

import importlib.util

import numpy as np
import yaml


def test_plot_all_unrecovered(tmp_path):
    from pathlib import Path

    from robot2dof.benchmark import create_disturbance_scenario

    # Minimal saved fixture; no simulation is needed to exercise this plot branch.
    time = 4.5 + np.arange(801) * 0.001
    scenario = create_disturbance_scenario()
    names = ("pid", "pid_gravity", "computed_torque")
    for name in names:
        np.savez_compressed(
            tmp_path / f"{name}_disturbance.npz",
            time_values=time,
            state_history=np.tile(scenario.initial_state, (time.size, 1)),
            reference_position_history=np.tile(
                scenario.initial_state[:2], (time.size, 1)
            ),
            end_effector_error_history_m=np.full(time.size, 0.02),
            external_torque_history=np.zeros((time.size, 2)),
        )
    config = {
        "disturbance": {"start_time_s": 4.5, "end_time_s": 4.7},
        "metrics": {"recovery_time": {"threshold_m": 0.01, "hold_duration_s": 0.5}},
    }
    (tmp_path / "pid_disturbance.yaml").write_text(
        yaml.safe_dump(config), encoding="utf-8"
    )
    (tmp_path / "disturbance_metrics.csv").write_text(
        "controller,recovered,recovery_time_s\n"
        + "".join(f"{name},False,\n" for name in names),
        encoding="utf-8",
    )
    path = (
        Path(__file__).resolve().parents[1]
        / "experiments/plot_disturbance_benchmark.py"
    )
    spec = importlib.util.spec_from_file_location("disturbance_plot_none", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.plot_disturbance_benchmark(tmp_path).stat().st_size > 1000
