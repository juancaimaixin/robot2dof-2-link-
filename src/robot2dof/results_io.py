import csv
import hashlib
import json
import platform
import subprocess
from collections.abc import Sequence
from dataclasses import asdict, fields
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

import numpy as np
import yaml

from .benchmark import (
    DisturbanceRun,
    ModelUncertaintyRun,
    NominalRun,
    PayloadRun,
    summarize_disturbance_run,
    summarize_model_uncertainty_run,
    summarize_nominal_run,
    summarize_payload_run,
)
from .disturbances import create_disturbance_torque_for_step
from .kinematics import end_effector_force_to_joint_torque, forward_kinematics


def save_nominal_history(
    run: NominalRun,
    path: str | Path,
) -> Path:
    """Save a nominal run's complete history without overwriting files."""

    destination = Path(path).resolve()
    if destination.suffix.lower() != ".npz":
        raise ValueError("The output path must end with .npz.")

    history = run.simulation

    arrays = {
        field.name: np.asarray(getattr(history, field.name))
        for field in fields(history)
    }

    arrays["end_effector_position_history"] = np.array(
        [
            forward_kinematics(q, run.scenario.params)
            for q in history.state_history[:, :2]
        ],
        dtype=float,
    )

    arrays["reference_end_effector_position_history"] = np.array(
        [
            forward_kinematics(q, run.scenario.params)
            for q in history.reference_position_history
        ],
        dtype=float,
    )

    arrays["external_torque_history"] = np.broadcast_to(
        run.scenario.external_tau,
        (history.time_values.size, 2),
    ).copy()

    for name, values in arrays.items():
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Cannot save non-finite history: {name}")

    arrays["controller"] = np.array(run.controller)
    arrays["tuning_configuration_sha256"] = np.array(run.configuration_sha256)
    arrays["configuration_sha256"] = np.array(
        compute_configuration_sha256(build_nominal_configuration(run))
    )

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("xb") as output:
        np.savez_compressed(output, **arrays)

    return destination


def save_payload_history(
    run: PayloadRun,
    path: str | Path,
) -> Path:
    """Save a payload run's complete history without overwriting files."""

    destination = Path(path).resolve()
    if destination.suffix.lower() != ".npz":
        raise ValueError("The output path must end with .npz.")

    payload_mass = float(run.scenario.params.payload_mass)
    if not np.isfinite(payload_mass) or payload_mass < 0.0:
        raise ValueError("Payload mass must be finite and non-negative.")

    history = run.simulation

    arrays = {
        field.name: np.asarray(getattr(history, field.name))
        for field in fields(history)
    }

    arrays["end_effector_position_history"] = np.array(
        [
            forward_kinematics(q, run.scenario.params)
            for q in history.state_history[:, :2]
        ],
        dtype=float,
    )

    arrays["reference_end_effector_position_history"] = np.array(
        [
            forward_kinematics(q, run.scenario.params)
            for q in history.reference_position_history
        ],
        dtype=float,
    )

    arrays["external_torque_history"] = np.broadcast_to(
        run.scenario.external_tau,
        (history.time_values.size, 2),
    ).copy()

    arrays["payload_mass_kg"] = np.array(payload_mass, dtype=float)

    for name, values in arrays.items():
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Cannot save non-finite history: {name}")

    arrays["controller"] = np.array(run.controller)
    arrays["tuning_configuration_sha256"] = np.array(run.configuration_sha256)
    arrays["configuration_sha256"] = np.array(
        compute_configuration_sha256(build_payload_configuration(run))
    )

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("xb") as output:
        np.savez_compressed(output, **arrays)

    return destination


def save_model_uncertainty_history(
    run: ModelUncertaintyRun,
    path: str | Path,
) -> Path:
    """Save model uncertainty history without overwriting files."""

    destination = Path(path).resolve()
    if destination.suffix.lower() != ".npz":
        raise ValueError("The output path must end with .npz.")

    relative_error = float(run.scenario.relative_error)
    if not np.isfinite(relative_error) or relative_error <= -1.0:
        raise ValueError("Relative error must be finite and greater than -1.")

    history = run.simulation

    arrays = {
        field.name: np.asarray(getattr(history, field.name))
        for field in fields(history)
    }

    arrays["end_effector_position_history"] = np.array(
        [
            forward_kinematics(q, run.scenario.params)
            for q in history.state_history[:, :2]
        ],
        dtype=float,
    )

    arrays["reference_end_effector_position_history"] = np.array(
        [
            forward_kinematics(q, run.scenario.params)
            for q in history.reference_position_history
        ],
        dtype=float,
    )

    arrays["external_torque_history"] = np.broadcast_to(
        run.scenario.external_tau,
        (history.time_values.size, 2),
    ).copy()

    arrays["relative_error"] = np.array(relative_error, dtype=float)

    for name, values in arrays.items():
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Cannot save non-finite history: {name}")

    arrays["controller"] = np.array(run.controller)
    arrays["tuning_configuration_sha256"] = np.array(run.configuration_sha256)
    arrays["configuration_sha256"] = np.array(
        compute_configuration_sha256(build_model_uncertainty_configuration(run))
    )

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("xb") as output:
        np.savez_compressed(output, **arrays)

    return destination


def build_nominal_configuration(run: NominalRun) -> dict[str, object]:
    """Capture the inputs and conventions used by one nominal run."""

    scenario = run.scenario
    gains = {
        field.name: np.asarray(getattr(run.gains, field.name), dtype=float).tolist()
        for field in fields(run.gains)
    }

    return {
        "schema_version": 1,
        "experiment": "nominal",
        "actual_model": asdict(scenario.params),
        "controller_model": (
            None if run.controller == "pid" else asdict(scenario.controller_params)
        ),
        "trajectory": {
            "type": "quintic_stop_to_stop",
            "position_unit": "rad",
            "time_unit": "s",
            "waypoint_times": scenario.waypoint_times.tolist(),
            "waypoint_positions": scenario.waypoint_positions.tolist(),
        },
        "controller": {
            "name": run.controller,
            "gains": gains,
            "tuning_configuration_sha256": run.configuration_sha256,
        },
        "simulation": {
            "integrator": "fixed_step_rk4",
            "control_hold": "zero_order_hold",
            "step_s": float(scenario.step),
            "state_order": ["q1", "q2", "q1_dot", "q2_dot"],
            "initial_state": scenario.initial_state.tolist(),
            "initial_integral_error": (
                None
                if run.controller == "computed_torque"
                else scenario.initial_integral_error.tolist()
            ),
        },
        "actuator": {
            "type": "symmetric_joint_torque_limit",
            "limit_nm": float(scenario.torque_limit),
        },
        "disturbance": {
            "type": "constant_joint_torque",
            "torque_nm": scenario.external_tau.tolist(),
        },
        "seed": None,
        "metrics": {
            "joint_rmse": "unweighted_all_samples_including_terminal",
            "overall_joint_rmse": "root_mean_square_over_samples_and_joints",
            "end_effector_error": "euclidean_distance_using_actual_geometry",
            "control_effort": "applied_torque_squared_held_interval_integral",
            "saturation_fraction": "any_joint_saturated_interval_duration",
            "absolute_mechanical_work": "left_rectangle_absolute_total_power",
        },
        "output": {
            "history": f"{run.controller}.npz",
            "configuration": f"{run.controller}.yaml",
            "metadata": f"{run.controller}.json",
            "summary": "nominal_metrics.csv",
        },
    }


def build_payload_configuration(run: PayloadRun) -> dict[str, object]:
    """Capture the inputs and conventions used by one payload run."""

    scenario = run.scenario

    payload_mass = float(scenario.params.payload_mass)
    if not np.isfinite(payload_mass) or payload_mass < 0.0:
        raise ValueError("Payload mass must be finite and non-negative.")

    gains = {
        field.name: np.asarray(getattr(run.gains, field.name), dtype=float).tolist()
        for field in fields(run.gains)
    }

    stem = f"{run.controller}_payload_{payload_mass}kg"

    return {
        "schema_version": 1,
        "experiment": "payload",
        "actual_model": asdict(scenario.params),
        "controller_model": (
            None if run.controller == "pid" else asdict(scenario.controller_params)
        ),
        "trajectory": {
            "type": "quintic_stop_to_stop",
            "position_unit": "rad",
            "time_unit": "s",
            "waypoint_times": scenario.waypoint_times.tolist(),
            "waypoint_positions": scenario.waypoint_positions.tolist(),
        },
        "controller": {
            "name": run.controller,
            "gains": gains,
            "tuning_configuration_sha256": run.configuration_sha256,
        },
        "simulation": {
            "integrator": "fixed_step_rk4",
            "control_hold": "zero_order_hold",
            "step_s": float(scenario.step),
            "state_order": ["q1", "q2", "q1_dot", "q2_dot"],
            "initial_state": scenario.initial_state.tolist(),
            "initial_integral_error": (
                None
                if run.controller == "computed_torque"
                else scenario.initial_integral_error.tolist()
            ),
        },
        "actuator": {
            "type": "symmetric_joint_torque_limit",
            "limit_nm": float(scenario.torque_limit),
        },
        "disturbance": {
            "type": "constant_joint_torque",
            "torque_nm": scenario.external_tau.tolist(),
        },
        "seed": None,
        "metrics": {
            "joint_rmse": "unweighted_all_samples_including_terminal",
            "overall_joint_rmse": "root_mean_square_over_samples_and_joints",
            "end_effector_error": "euclidean_distance_using_actual_geometry",
            "control_effort": "applied_torque_squared_held_interval_integral",
            "saturation_fraction": "any_joint_saturated_interval_duration",
            "absolute_mechanical_work": "left_rectangle_absolute_total_power",
        },
        "output": {
            "history": f"{stem}.npz",
            "configuration": f"{stem}.yaml",
            "metadata": f"{stem}.json",
            "summary": "payload_metrics.csv",
        },
    }


def build_model_uncertainty_configuration(
    run: ModelUncertaintyRun,
) -> dict[str, object]:
    """Capture inputs and conventions for one model uncertainty run."""

    scenario = run.scenario
    relative_error = float(scenario.relative_error)
    if not np.isfinite(relative_error) or relative_error <= -1.0:
        raise ValueError("Relative error must be finite and greater than -1.")

    gains = {
        field.name: np.asarray(getattr(run.gains, field.name), dtype=float).tolist()
        for field in fields(run.gains)
    }

    stem = f"{run.controller}_model_error_{relative_error}"

    return {
        "schema_version": 1,
        "experiment": "model_uncertainty",
        "model_uncertainty": {
            "relative_error": relative_error,
            "scaled_parameters": ["m2", "I2"],
        },
        "actual_model": asdict(scenario.params),
        "controller_model": (
            None if run.controller == "pid" else asdict(scenario.controller_params)
        ),
        "trajectory": {
            "type": "quintic_stop_to_stop",
            "position_unit": "rad",
            "time_unit": "s",
            "waypoint_times": scenario.waypoint_times.tolist(),
            "waypoint_positions": scenario.waypoint_positions.tolist(),
        },
        "controller": {
            "name": run.controller,
            "gains": gains,
            "tuning_configuration_sha256": run.configuration_sha256,
        },
        "simulation": {
            "integrator": "fixed_step_rk4",
            "control_hold": "zero_order_hold",
            "step_s": float(scenario.step),
            "state_order": ["q1", "q2", "q1_dot", "q2_dot"],
            "initial_state": scenario.initial_state.tolist(),
            "initial_integral_error": (
                None
                if run.controller == "computed_torque"
                else scenario.initial_integral_error.tolist()
            ),
        },
        "actuator": {
            "type": "symmetric_joint_torque_limit",
            "limit_nm": float(scenario.torque_limit),
        },
        "disturbance": {
            "type": "constant_joint_torque",
            "torque_nm": scenario.external_tau.tolist(),
        },
        "seed": None,
        "metrics": {
            "joint_rmse": "unweighted_all_samples_including_terminal",
            "overall_joint_rmse": "root_mean_square_over_samples_and_joints",
            "end_effector_error": "euclidean_distance_using_actual_geometry",
            "control_effort": "applied_torque_squared_held_interval_integral",
            "saturation_fraction": "any_joint_saturated_interval_duration",
            "absolute_mechanical_work": "left_rectangle_absolute_total_power",
        },
        "output": {
            "history": f"{stem}.npz",
            "configuration": f"{stem}.yaml",
            "metadata": f"{stem}.json",
            "summary": "model_uncertainty_metrics.csv",
        },
    }


def build_disturbance_configuration(
    run: DisturbanceRun,
) -> dict[str, object]:
    """Capture inputs and conventions for the fixed disturbance experiment."""

    scenario = run.scenario

    if scenario.external_tau_factory is not create_disturbance_torque_for_step:
        raise ValueError("Expected the fixed disturbance torque factory.")

    gains = {
        field.name: np.asarray(getattr(run.gains, field.name), dtype=float).tolist()
        for field in fields(run.gains)
    }

    stem = f"{run.controller}_disturbance"

    return {
        "schema_version": 1,
        "experiment": "disturbance",
        "actual_model": asdict(scenario.params),
        "controller_model": (
            None if run.controller == "pid" else asdict(scenario.controller_params)
        ),
        "trajectory": {
            "type": "quintic_stop_to_stop",
            "position_unit": "rad",
            "time_unit": "s",
            "waypoint_times": scenario.waypoint_times.tolist(),
            "waypoint_positions": scenario.waypoint_positions.tolist(),
        },
        "controller": {
            "name": run.controller,
            "gains": gains,
            "tuning_configuration_sha256": run.configuration_sha256,
        },
        "simulation": {
            "integrator": "fixed_step_rk4",
            "control_hold": "zero_order_hold",
            "step_s": float(scenario.step),
            "state_order": ["q1", "q2", "q1_dot", "q2_dot"],
            "initial_state": scenario.initial_state.tolist(),
            "initial_integral_error": (
                None
                if run.controller == "computed_torque"
                else scenario.initial_integral_error.tolist()
            ),
        },
        "actuator": {
            "type": "symmetric_joint_torque_limit",
            "limit_nm": float(scenario.torque_limit),
        },
        "disturbance": {
            "type": "end_effector_rectangular_pulse",
            "force_frame": "base",
            "force_n": [10.0, 0.0],
            "start_time_s": 4.5,
            "end_time_s": 4.7,
            "active_interval": "[start, end)",
            "force_hold": "constant_within_each_integration_interval",
            "joint_torque_mapping": "actual_jacobian_transpose_at_each_rk4_stage",
            "boundary_policy": "reject_intervals_crossing_pulse_boundaries",
            "boundary_tolerance_s": 1e-12,
            "saved_force_history": "interval_value_at_left_sample_terminal_instantaneous",
            "saved_torque_history": "J(q_sample).T_F_not_constant_over_interval",
        },
        "seed": None,
        "metrics": {
            "joint_rmse": "unweighted_all_samples_including_terminal",
            "overall_joint_rmse": "root_mean_square_over_samples_and_joints",
            "end_effector_error": "euclidean_distance_using_actual_geometry",
            "maximum_end_effector_error": "maximum_over_all_samples",
            "control_effort": "applied_torque_squared_held_interval_integral",
            "saturation_fraction": "any_joint_saturated_interval_duration",
            "absolute_mechanical_work": "left_rectangle_absolute_total_power",
            "recovery_time": {
                "disturbance_end_time_s": 4.7,
                "threshold_m": 0.01,
                "threshold_comparison": "<=",
                "hold_duration_s": 0.5,
                "criterion": "consecutive_samples_within_threshold",
                "reported_value": "earliest_window_start_minus_disturbance_end",
                "time_tolerance_s": 1e-12,
                "unconfirmed_value": None,
            },
        },
        "output": {
            "history": f"{stem}.npz",
            "configuration": f"{stem}.yaml",
            "metadata": f"{stem}.json",
            "summary": "disturbance_metrics.csv",
            "summary_json": "disturbance_metrics.json",
        },
    }


def compute_configuration_sha256(
    configuration: dict[str, object],
) -> str:
    """Hash a canonical JSON representation of the configuration."""

    canonical = json.dumps(
        configuration,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def save_nominal_manifest(
    run: NominalRun,
    output_dir: str | Path,
    project_root: str | Path,
) -> tuple[Path, Path]:
    """Save configuration and metadata for an existing history file."""

    directory = Path(output_dir).resolve()
    root = Path(project_root).resolve()

    configuration = build_nominal_configuration(run)
    configuration_hash = compute_configuration_sha256(configuration)
    filenames = configuration["output"]

    history_path = directory / filenames["history"]
    configuration_path = directory / filenames["configuration"]
    metadata_path = directory / filenames["metadata"]

    for destination in (configuration_path, metadata_path):
        if destination.exists():
            raise FileExistsError(f"Output already exists: {destination}")

    with np.load(history_path, allow_pickle=False) as history:
        if history["controller"].item() != run.controller:
            raise ValueError("History belongs to another controller.")
        if history["configuration_sha256"].item() != configuration_hash:
            raise ValueError("History configuration hash does not match.")

    def git_output(*arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout.rstrip("\r\n")

    commit = git_output("rev-parse", "HEAD")
    git_status = git_output("status", "--short")

    metadata = {
        "schema_version": 1,
        "controller": run.controller,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration_file": configuration_path.name,
        "configuration_sha256": configuration_hash,
        "tuning_configuration_sha256": run.configuration_sha256,
        "history_file": history_path.name,
        "history_sha256": hashlib.sha256(history_path.read_bytes()).hexdigest(),
        "seed": configuration["seed"],
        "git": {
            "commit": commit,
            "dirty": bool(git_status),
            "status_at_recording": git_status,
        },
        "software_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": version("scipy"),
            "matplotlib": version("matplotlib"),
            "pyyaml": version("PyYAML"),
        },
    }

    configuration_text = yaml.safe_dump(
        configuration,
        sort_keys=True,
        allow_unicode=True,
    )
    metadata_text = (
        json.dumps(
            metadata,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=False,
        )
        + "\n"
    )

    with configuration_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(configuration_text)

    with metadata_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(metadata_text)

    return configuration_path, metadata_path


def save_payload_manifest(
    run: PayloadRun,
    output_dir: str | Path,
    project_root: str | Path,
) -> tuple[Path, Path]:
    """Save configuration and metadata for an existing payload history."""

    directory = Path(output_dir).resolve()
    root = Path(project_root).resolve()

    configuration = build_payload_configuration(run)
    configuration_hash = compute_configuration_sha256(configuration)
    payload_mass = configuration["actual_model"]["payload_mass"]
    filenames = configuration["output"]

    history_path = directory / filenames["history"]
    configuration_path = directory / filenames["configuration"]
    metadata_path = directory / filenames["metadata"]

    for destination in (configuration_path, metadata_path):
        if destination.exists():
            raise FileExistsError(f"Output already exists: {destination}")

    with np.load(history_path, allow_pickle=False) as history:
        if history["controller"].item() != run.controller:
            raise ValueError("History belongs to another controller.")

        if history["payload_mass_kg"].item() != payload_mass:
            raise ValueError("History payload mass does not match.")

        if history["configuration_sha256"].item() != configuration_hash:
            raise ValueError("History configuration hash does not match.")

        if history["tuning_configuration_sha256"].item() != run.configuration_sha256:
            raise ValueError("History tuning configuration hash does not match.")

    def git_output(*arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout.rstrip("\r\n")

    commit = git_output("rev-parse", "HEAD")
    git_status = git_output("status", "--short")

    metadata = {
        "schema_version": 1,
        "experiment": "payload",
        "controller": run.controller,
        "payload_mass_kg": float(payload_mass),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration_file": configuration_path.name,
        "configuration_sha256": configuration_hash,
        "tuning_configuration_sha256": run.configuration_sha256,
        "history_file": history_path.name,
        "history_sha256": hashlib.sha256(history_path.read_bytes()).hexdigest(),
        "seed": configuration["seed"],
        "git": {
            "commit": commit,
            "dirty": bool(git_status),
            "status_at_recording": git_status,
        },
        "software_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": version("scipy"),
            "matplotlib": version("matplotlib"),
            "pyyaml": version("PyYAML"),
        },
    }

    configuration_text = yaml.safe_dump(
        configuration,
        sort_keys=True,
        allow_unicode=True,
    )
    metadata_text = (
        json.dumps(
            metadata,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=False,
        )
        + "\n"
    )

    with configuration_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(configuration_text)

    with metadata_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(metadata_text)

    return configuration_path, metadata_path


def save_model_uncertainty_manifest(
    run: ModelUncertaintyRun,
    output_dir: str | Path,
    project_root: str | Path,
) -> tuple[Path, Path]:
    """Save configuration and metadata for an existing uncertainty history."""

    directory = Path(output_dir).resolve()
    root = Path(project_root).resolve()

    configuration = build_model_uncertainty_configuration(run)
    configuration_hash = compute_configuration_sha256(configuration)
    relative_error = configuration["model_uncertainty"]["relative_error"]
    filenames = configuration["output"]

    history_path = directory / filenames["history"]
    configuration_path = directory / filenames["configuration"]
    metadata_path = directory / filenames["metadata"]

    for destination in (configuration_path, metadata_path):
        if destination.exists():
            raise FileExistsError(f"Output already exists: {destination}")

    with np.load(history_path, allow_pickle=False) as history:
        if history["controller"].item() != run.controller:
            raise ValueError("History belongs to another controller.")

        if history["relative_error"].item() != relative_error:
            raise ValueError("History relative error does not match.")

        if history["configuration_sha256"].item() != configuration_hash:
            raise ValueError("History configuration hash does not match.")

        if history["tuning_configuration_sha256"].item() != run.configuration_sha256:
            raise ValueError("History tuning configuration hash does not match.")

    def git_output(*arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout.rstrip("\r\n")

    commit = git_output("rev-parse", "HEAD")
    git_status = git_output("status", "--short")

    metadata = {
        "schema_version": 1,
        "experiment": "model_uncertainty",
        "controller": run.controller,
        "relative_error": float(relative_error),
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration_file": configuration_path.name,
        "configuration_sha256": configuration_hash,
        "tuning_configuration_sha256": run.configuration_sha256,
        "history_file": history_path.name,
        "history_sha256": hashlib.sha256(history_path.read_bytes()).hexdigest(),
        "seed": configuration["seed"],
        "git": {
            "commit": commit,
            "dirty": bool(git_status),
            "status_at_recording": git_status,
        },
        "software_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": version("scipy"),
            "matplotlib": version("matplotlib"),
            "pyyaml": version("PyYAML"),
        },
    }

    configuration_text = yaml.safe_dump(
        configuration,
        sort_keys=True,
        allow_unicode=True,
    )
    metadata_text = (
        json.dumps(
            metadata,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=False,
        )
        + "\n"
    )

    with configuration_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(configuration_text)

    with metadata_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(metadata_text)

    return configuration_path, metadata_path


def save_nominal_summary(
    runs: Sequence[NominalRun],
    path: str | Path,
) -> Path:
    """Save one summary row per controller in a fixed order."""

    destination = Path(path).resolve()
    if destination.suffix.lower() != ".csv":
        raise ValueError("The output path must end with .csv.")
    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")

    controller_order = ("pid", "pid_gravity", "computed_torque")

    if len(runs) != len(controller_order):
        raise ValueError("Exactly three nominal runs are required.")

    runs_by_controller = {run.controller: run for run in runs}

    if set(runs_by_controller) != set(controller_order):
        raise ValueError("Expected one result for each nominal controller.")

    rows = [
        summarize_nominal_run(runs_by_controller[controller])
        for controller in controller_order
    ]

    for row in rows:
        numeric_values = [value for name, value in row.items() if name != "controller"]
        if not np.all(np.isfinite(numeric_values)):
            raise ValueError("Cannot save non-finite summary metrics.")

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("x", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)

    return destination


def save_payload_summary(
    runs: Sequence[PayloadRun],
    path: str | Path,
) -> Path:
    """Save the complete payload grid in a fixed row order."""

    destination = Path(path).resolve()
    if destination.suffix.lower() != ".csv":
        raise ValueError("The output path must end with .csv.")
    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")

    payload_masses = (0.0, 0.25, 0.50, 0.75, 1.00)
    controller_order = ("pid", "pid_gravity", "computed_torque")

    expected_keys = [
        (mass, controller) for mass in payload_masses for controller in controller_order
    ]

    if len(runs) != len(expected_keys):
        raise ValueError("Exactly 15 payload runs are required.")

    runs_by_key = {}

    for run in runs:
        mass = float(run.scenario.params.payload_mass)

        if not np.isfinite(mass) or mass not in payload_masses:
            raise ValueError("Payload mass is outside the prescribed grid.")
        if run.controller not in controller_order:
            raise ValueError(f"Unknown controller: {run.controller}")

        key = (mass, run.controller)
        if key in runs_by_key:
            raise ValueError(f"Duplicate payload run: {key}")

        runs_by_key[key] = run

    if set(runs_by_key) != set(expected_keys):
        raise ValueError("Expected one run for every payload-controller pair.")

    rows = [summarize_payload_run(runs_by_key[key]) for key in expected_keys]

    for row in rows:
        numeric_values = [value for name, value in row.items() if name != "controller"]
        if not np.all(np.isfinite(numeric_values)):
            raise ValueError("Cannot save non-finite summary metrics.")

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("x", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)

    return destination


def save_model_uncertainty_summary(
    runs: Sequence[ModelUncertaintyRun],
    path: str | Path,
) -> Path:
    """Save the complete model uncertainty grid in a fixed row order."""

    destination = Path(path).resolve()
    if destination.suffix.lower() != ".csv":
        raise ValueError("The output path must end with .csv.")
    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")

    relative_errors = (-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3)
    controller_order = ("pid", "pid_gravity", "computed_torque")

    expected_keys = [
        (error, controller)
        for error in relative_errors
        for controller in controller_order
    ]

    if len(runs) != len(expected_keys):
        raise ValueError("Exactly 21 model uncertainty runs are required.")

    runs_by_key = {}

    for run in runs:
        error = float(run.scenario.relative_error)

        if not np.isfinite(error) or error not in relative_errors:
            raise ValueError("Relative error is outside the prescribed grid.")
        if run.controller not in controller_order:
            raise ValueError(f"Unknown controller: {run.controller}")

        key = (error, run.controller)
        if key in runs_by_key:
            raise ValueError(f"Duplicate model uncertainty run: {key}")

        runs_by_key[key] = run

    if set(runs_by_key) != set(expected_keys):
        raise ValueError("Expected one run for every error-controller pair.")

    rows = [summarize_model_uncertainty_run(runs_by_key[key]) for key in expected_keys]

    for row in rows:
        numeric_values = [value for name, value in row.items() if name != "controller"]
        if not np.all(np.isfinite(numeric_values)):
            raise ValueError("Cannot save non-finite summary metrics.")

    destination.parent.mkdir(parents=True, exist_ok=True)

    with destination.open("x", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(
            output,
            fieldnames=list(rows[0]),
        )
        writer.writeheader()
        writer.writerows(rows)

    return destination


def save_disturbance_history(run: DisturbanceRun, path: str | Path) -> Path:
    """Save sampled histories; external torques remain separate from motor torques."""
    destination = Path(path).resolve()
    if destination.suffix.lower() != ".npz":
        raise ValueError("The output path must end with .npz.")
    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")

    configuration = build_disturbance_configuration(run)
    configuration_hash = compute_configuration_sha256(configuration)
    # Validate tracking, actuation, recovery inputs before writing any output.
    summarize_disturbance_run(run)
    history = run.simulation
    arrays = {
        field.name: np.asarray(getattr(history, field.name))
        for field in fields(history)
    }
    for name, values in arrays.items():
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Cannot save non-finite history: {name}")

    time = history.time_values
    if not np.allclose(np.diff(time), run.scenario.step, rtol=0, atol=1e-12):
        raise ValueError("History intervals must match the configured step.")
    actual_xy = np.array(
        [
            forward_kinematics(q, run.scenario.params)
            for q in history.state_history[:, :2]
        ]
    )
    reference_xy = np.array(
        [
            forward_kinematics(q, run.scenario.params)
            for q in history.reference_position_history
        ]
    )
    arrays["end_effector_position_history"] = actual_xy
    arrays["reference_end_effector_position_history"] = reference_xy
    arrays["end_effector_error_history_m"] = np.linalg.norm(
        reference_xy - actual_xy, axis=1
    )

    external_torque = np.empty((time.size, 2))
    force = np.zeros((time.size, 2))
    pulse = configuration["disturbance"]
    for index, sample_time in enumerate(time):
        if index < time.size - 1:
            torque_function = run.scenario.external_tau_factory(
                float(sample_time),
                run.scenario.step,
                run.scenario.params,
            )
            external_torque[index] = torque_function(
                float(sample_time),
                history.state_history[index, :2],
            )
            force_time = sample_time + run.scenario.step / 2
        else:
            # Terminal sample has no following integration interval.
            force_time = sample_time
        if pulse["start_time_s"] <= force_time < pulse["end_time_s"]:
            force[index] = pulse["force_n"]
        if index == time.size - 1:
            external_torque[index] = end_effector_force_to_joint_torque(
                history.state_history[index, :2],
                force[index],
                run.scenario.params,
            )
    arrays["external_force_history_n"] = force
    arrays["external_torque_history"] = external_torque
    for name, values in arrays.items():
        if not np.all(np.isfinite(values)):
            raise ValueError(f"Cannot save non-finite history: {name}")
    arrays["controller"] = np.array(run.controller)
    arrays["tuning_configuration_sha256"] = np.array(run.configuration_sha256)
    arrays["configuration_sha256"] = np.array(configuration_hash)

    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("xb") as output:
        np.savez_compressed(output, **arrays)
    return destination


def save_disturbance_summary(runs: Sequence[DisturbanceRun], path: str | Path) -> Path:
    """Save all three controllers; leave unconfirmed recovery cells empty."""
    destination = Path(path).resolve()
    if destination.suffix.lower() != ".csv":
        raise ValueError("The output path must end with .csv.")
    if destination.exists():
        raise FileExistsError(f"Output already exists: {destination}")
    order = ("pid", "pid_gravity", "computed_torque")
    by_controller = {run.controller: run for run in runs}
    if len(runs) != 3 or set(by_controller) != set(order):
        raise ValueError("Expected exactly one run per disturbance controller.")
    rows = [summarize_disturbance_run(by_controller[name]) for name in order]
    for row in rows:
        for key, value in row.items():
            if key == "controller" or (key == "recovery_time_s" and value is None):
                continue
            if not np.isfinite(value):
                raise ValueError("Cannot save non-finite summary metrics.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return destination


def save_disturbance_manifest(
    run: DisturbanceRun,
    output_dir: str | Path,
    project_root: str | Path,
) -> tuple[Path, Path]:
    """Save configuration and metadata for an existing disturbance history."""

    directory = Path(output_dir).resolve()
    root = Path(project_root).resolve()

    configuration = build_disturbance_configuration(run)
    configuration_hash = compute_configuration_sha256(configuration)
    filenames = configuration["output"]

    history_path = directory / filenames["history"]
    configuration_path = directory / filenames["configuration"]
    metadata_path = directory / filenames["metadata"]

    for destination in (configuration_path, metadata_path):
        if destination.exists():
            raise FileExistsError(f"Output already exists: {destination}")

    with np.load(history_path, allow_pickle=False) as history:
        if history["controller"].item() != run.controller:
            raise ValueError("History belongs to another controller.")

        if history["configuration_sha256"].item() != configuration_hash:
            raise ValueError("History configuration hash does not match.")

        if history["tuning_configuration_sha256"].item() != run.configuration_sha256:
            raise ValueError("History tuning configuration hash does not match.")

    def git_output(*arguments: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout.rstrip("\r\n")

    commit = git_output("rev-parse", "HEAD")
    git_status = git_output("status", "--short")

    source_paths = (
        "src/robot2dof/benchmark.py",
        "src/robot2dof/disturbances.py",
        "src/robot2dof/simulation.py",
        "src/robot2dof/state.py",
        "src/robot2dof/metrics.py",
        "src/robot2dof/results_io.py",
        "src/robot2dof/dynamics.py",
        "src/robot2dof/kinematics.py",
        "src/robot2dof/controllers.py",
        "src/robot2dof/actuation.py",
        "src/robot2dof/parameters.py",
        "src/robot2dof/trajectory.py",
        "experiments/run_disturbance_benchmark.py",
        "experiments/plot_disturbance_benchmark.py",
    )
    source_hashes = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest()
        for name in source_paths
    }
    metadata = {
        "schema_version": 1,
        "source_sha256": source_hashes,
        "experiment": "disturbance",
        "controller": run.controller,
        "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
        "configuration_file": configuration_path.name,
        "configuration_sha256": configuration_hash,
        "tuning_configuration_sha256": run.configuration_sha256,
        "history_file": history_path.name,
        "history_sha256": hashlib.sha256(history_path.read_bytes()).hexdigest(),
        "seed": configuration["seed"],
        "git": {
            "commit": commit,
            "dirty": bool(git_status),
            "status_at_recording": git_status,
        },
        "software_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": version("scipy"),
            "matplotlib": version("matplotlib"),
            "pyyaml": version("PyYAML"),
        },
    }

    configuration_text = yaml.safe_dump(
        configuration,
        sort_keys=True,
        allow_unicode=True,
    )
    metadata_text = (
        json.dumps(
            metadata,
            indent=2,
            sort_keys=True,
            allow_nan=False,
            ensure_ascii=False,
        )
        + "\n"
    )

    with configuration_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(configuration_text)

    with metadata_path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(metadata_text)

    return configuration_path, metadata_path
