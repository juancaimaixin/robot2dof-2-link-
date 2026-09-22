import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path

import numpy as np

from .controllers import ComputedTorqueGains, PIDGains
from .disturbances import create_disturbance_torque_for_step
from .kinematics import forward_kinematics
from .metrics import (
    compute_actuation_metrics,
    compute_recovery_time,
    compute_tracking_metrics,
)
from .parameters import RobotParams
from .simulation import (
    ComputedTorqueSimulationResult,
    ExternalTorqueFactory,
    PIDSimulationResult,
    simulate_computed_torque_trajectory,
    simulate_pid_trajectory,
)


@dataclass(frozen=True)
class NominalScenario:
    """Common simulation inputs for one nominal benchmark run."""

    waypoint_times: np.ndarray
    waypoint_positions: np.ndarray
    initial_state: np.ndarray
    initial_integral_error: np.ndarray
    params: RobotParams
    controller_params: RobotParams
    torque_limit: float
    external_tau: np.ndarray
    step: float


def create_nominal_scenario() -> NominalScenario:
    """Create fresh inputs for the fixed held-out trajectory."""

    waypoint_positions = np.radians(
        [
            [20.0, -35.0],
            [-40.0, 25.0],
            [55.0, 45.0],
            [5.0, -50.0],
            [-30.0, 15.0],
        ]
    )

    initial_state = np.concatenate(
        (
            waypoint_positions[0],
            np.zeros(2),
        )
    )

    return NominalScenario(
        waypoint_times=np.array([0.0, 2.0, 4.0, 6.0, 8.0]),
        waypoint_positions=waypoint_positions,
        initial_state=initial_state,
        initial_integral_error=np.zeros(2),
        params=RobotParams(),
        controller_params=RobotParams(),
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
    )


@dataclass(frozen=True)
class PayloadScenario:
    """Simulation inputs with a loaded plant and an unloaded controller."""

    waypoint_times: np.ndarray
    waypoint_positions: np.ndarray
    initial_state: np.ndarray
    initial_integral_error: np.ndarray
    params: RobotParams
    controller_params: RobotParams
    torque_limit: float
    external_tau: np.ndarray
    step: float


def create_payload_scenario(payload_mass: float) -> PayloadScenario:
    """Create fresh inputs for one end-effector payload experiment."""

    mass = float(payload_mass)
    if not np.isfinite(mass) or mass < 0.0:
        raise ValueError("Payload mass must be finite and non-negative.")

    nominal = create_nominal_scenario()

    plant_params = replace(
        nominal.params,
        payload_mass=mass,
    )

    return PayloadScenario(
        waypoint_times=nominal.waypoint_times,
        waypoint_positions=nominal.waypoint_positions,
        initial_state=nominal.initial_state,
        initial_integral_error=nominal.initial_integral_error,
        params=plant_params,
        controller_params=nominal.controller_params,
        torque_limit=nominal.torque_limit,
        external_tau=nominal.external_tau,
        step=nominal.step,
    )


@dataclass(frozen=True)
class ModelUncertaintyScenario:
    """Simulation inputs with biased controller model parameters."""

    relative_error: float
    waypoint_times: np.ndarray
    waypoint_positions: np.ndarray
    initial_state: np.ndarray
    initial_integral_error: np.ndarray
    params: RobotParams
    controller_params: RobotParams
    torque_limit: float
    external_tau: np.ndarray
    step: float


def create_model_uncertainty_scenario(
    relative_error: float,
) -> ModelUncertaintyScenario:
    """Keep the plant nominal and scale controller model m2 and I2."""

    error = float(relative_error)
    if not np.isfinite(error) or error <= -1.0:
        raise ValueError("Relative error must be finite and greater than -1.")

    nominal = create_nominal_scenario()
    scale = 1.0 + error

    controller_params = replace(
        nominal.controller_params,
        m2=nominal.controller_params.m2 * scale,
        I2=nominal.controller_params.I2 * scale,
    )

    return ModelUncertaintyScenario(
        relative_error=error,
        waypoint_times=nominal.waypoint_times,
        waypoint_positions=nominal.waypoint_positions,
        initial_state=nominal.initial_state,
        initial_integral_error=nominal.initial_integral_error,
        params=nominal.params,
        controller_params=controller_params,
        torque_limit=nominal.torque_limit,
        external_tau=nominal.external_tau,
        step=nominal.step,
    )


@dataclass(frozen=True)
class DisturbanceScenario:
    """Nominal simulation inputs with an interval-based disturbance."""

    waypoint_times: np.ndarray
    waypoint_positions: np.ndarray
    initial_state: np.ndarray
    initial_integral_error: np.ndarray
    params: RobotParams
    controller_params: RobotParams
    torque_limit: float
    step: float
    external_tau_factory: ExternalTorqueFactory


def create_disturbance_scenario() -> DisturbanceScenario:
    """Create fresh inputs for the fixed end-effector disturbance experiment."""

    nominal = create_nominal_scenario()

    return DisturbanceScenario(
        waypoint_times=nominal.waypoint_times,
        waypoint_positions=nominal.waypoint_positions,
        initial_state=nominal.initial_state,
        initial_integral_error=nominal.initial_integral_error,
        params=nominal.params,
        controller_params=nominal.controller_params,
        torque_limit=nominal.torque_limit,
        step=nominal.step,
        external_tau_factory=create_disturbance_torque_for_step,
    )


FROZEN_CONFIGURATION_SHA256 = (
    "50247f53d83e161b5419f0e59216c5064f2d6f8700eca295f6dc253e140ec3da"
)

FROZEN_BEST_IDS = {
    "pid": 154,
    "pid_gravity": 233,
    "computed_torque": 208,
}


def load_frozen_gains(
    path: str | Path,
    controller: str,
) -> PIDGains | ComputedTorqueGains:
    """Load and verify the selected gains from the frozen search."""

    if controller not in FROZEN_BEST_IDS:
        raise ValueError(f"Unknown controller: {controller}")

    payload = json.loads(Path(path).read_text(encoding="utf-8"))

    if payload["status"] != "complete":
        raise ValueError("The tuning search is incomplete.")

    configuration = payload["configuration"]
    canonical = json.dumps(
        configuration,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    actual_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    if (
        actual_hash != FROZEN_CONFIGURATION_SHA256
        or payload["configuration_sha256"] != actual_hash
    ):
        raise ValueError("The frozen configuration hash does not match.")

    search = payload["searches"][controller]
    best_id = FROZEN_BEST_IDS[controller]

    if search["best_candidate_id"] != best_id:
        raise ValueError("The frozen best candidate ID does not match.")

    matches = [
        evaluation
        for evaluation in search["evaluations"]
        if evaluation["candidate"]["candidate_id"] == best_id
    ]
    if len(matches) != 1:
        raise ValueError("Expected exactly one selected evaluation.")

    selected = matches[0]
    if not selected["succeeded"] or selected["failure_reason"] is not None:
        raise ValueError("The selected evaluation was not successful.")

    if controller == "computed_torque":
        candidates = configuration["computed_torque_candidates"]
    else:
        candidates = configuration["pid_candidates"]

    candidate = candidates[best_id]
    if selected["candidate"] != candidate:
        raise ValueError("The selected candidate differs from configuration.")

    if controller == "computed_torque":
        omega = np.array(candidate["natural_frequency"], dtype=float)
        zeta = np.array(candidate["damping_ratio"], dtype=float)
        expected_gains = {
            "kp": omega**2,
            "kd": 2.0 * zeta * omega,
        }
    else:
        expected_gains = {
            name: np.array(candidate[name], dtype=float) for name in ("kp", "ki", "kd")
        }

    gains = {}
    for name, expected in expected_gains.items():
        values = np.array(selected["gains"][name], dtype=float)

        if (
            values.shape != (2,)
            or not np.all(np.isfinite(values))
            or np.any(values < 0.0)
        ):
            raise ValueError(f"Invalid frozen gain: {name}")

        if not np.array_equal(values, expected):
            raise ValueError(f"Frozen gain differs from candidate: {name}")

        gains[name] = values

    if controller == "computed_torque":
        return ComputedTorqueGains(**gains)

    return PIDGains(**gains)


@dataclass(frozen=True)
class NominalRun:
    """Inputs and complete simulation history for one nominal run."""

    controller: str
    configuration_sha256: str
    gains: PIDGains | ComputedTorqueGains
    scenario: NominalScenario
    simulation: PIDSimulationResult | ComputedTorqueSimulationResult


def run_nominal_controller(
    frozen_path: str | Path,
    controller: str,
) -> NominalRun:
    """Run one controller on the fixed nominal benchmark."""

    gains = load_frozen_gains(frozen_path, controller)
    scenario = create_nominal_scenario()

    if controller == "computed_torque":
        simulation = simulate_computed_torque_trajectory(
            waypoint_times=scenario.waypoint_times,
            waypoint_positions=scenario.waypoint_positions,
            initial_state=scenario.initial_state,
            gains=gains,
            params=scenario.params,
            controller_params=scenario.controller_params,
            torque_limit=scenario.torque_limit,
            external_tau=scenario.external_tau,
            step=scenario.step,
        )
    else:
        controller_params = (
            scenario.controller_params if controller == "pid_gravity" else None
        )

        simulation = simulate_pid_trajectory(
            waypoint_times=scenario.waypoint_times,
            waypoint_positions=scenario.waypoint_positions,
            initial_state=scenario.initial_state,
            initial_integral_error=scenario.initial_integral_error,
            gains=gains,
            params=scenario.params,
            controller_params=controller_params,
            torque_limit=scenario.torque_limit,
            external_tau=scenario.external_tau,
            step=scenario.step,
        )

    return NominalRun(
        controller=controller,
        configuration_sha256=FROZEN_CONFIGURATION_SHA256,
        gains=gains,
        scenario=scenario,
        simulation=simulation,
    )


@dataclass(frozen=True)
class PayloadRun:
    """Inputs and complete simulation history for one payload run."""

    controller: str
    configuration_sha256: str
    gains: PIDGains | ComputedTorqueGains
    scenario: PayloadScenario
    simulation: PIDSimulationResult | ComputedTorqueSimulationResult


def run_payload_controller(
    frozen_path: str | Path,
    controller: str,
    payload_mass: float,
) -> PayloadRun:
    """Run one frozen controller with a loaded plant."""

    gains = load_frozen_gains(frozen_path, controller)
    scenario = create_payload_scenario(payload_mass)

    if controller == "computed_torque":
        simulation = simulate_computed_torque_trajectory(
            waypoint_times=scenario.waypoint_times,
            waypoint_positions=scenario.waypoint_positions,
            initial_state=scenario.initial_state,
            gains=gains,
            params=scenario.params,
            controller_params=scenario.controller_params,
            torque_limit=scenario.torque_limit,
            external_tau=scenario.external_tau,
            step=scenario.step,
        )
    else:
        controller_params = (
            scenario.controller_params if controller == "pid_gravity" else None
        )

        simulation = simulate_pid_trajectory(
            waypoint_times=scenario.waypoint_times,
            waypoint_positions=scenario.waypoint_positions,
            initial_state=scenario.initial_state,
            initial_integral_error=scenario.initial_integral_error,
            gains=gains,
            params=scenario.params,
            controller_params=controller_params,
            torque_limit=scenario.torque_limit,
            external_tau=scenario.external_tau,
            step=scenario.step,
        )

    return PayloadRun(
        controller=controller,
        configuration_sha256=FROZEN_CONFIGURATION_SHA256,
        gains=gains,
        scenario=scenario,
        simulation=simulation,
    )


@dataclass(frozen=True)
class ModelUncertaintyRun:
    """Inputs and simulation history for one model uncertainty run."""

    controller: str
    configuration_sha256: str
    gains: PIDGains | ComputedTorqueGains
    scenario: ModelUncertaintyScenario
    simulation: PIDSimulationResult | ComputedTorqueSimulationResult


def run_model_uncertainty_controller(
    frozen_path: str | Path,
    controller: str,
    relative_error: float,
) -> ModelUncertaintyRun:
    """Run one frozen controller with biased model parameters."""

    gains = load_frozen_gains(frozen_path, controller)
    scenario = create_model_uncertainty_scenario(relative_error)

    if controller == "computed_torque":
        simulation = simulate_computed_torque_trajectory(
            waypoint_times=scenario.waypoint_times,
            waypoint_positions=scenario.waypoint_positions,
            initial_state=scenario.initial_state,
            gains=gains,
            params=scenario.params,
            controller_params=scenario.controller_params,
            torque_limit=scenario.torque_limit,
            external_tau=scenario.external_tau,
            step=scenario.step,
        )
    else:
        controller_params = (
            scenario.controller_params if controller == "pid_gravity" else None
        )

        simulation = simulate_pid_trajectory(
            waypoint_times=scenario.waypoint_times,
            waypoint_positions=scenario.waypoint_positions,
            initial_state=scenario.initial_state,
            initial_integral_error=scenario.initial_integral_error,
            gains=gains,
            params=scenario.params,
            controller_params=controller_params,
            torque_limit=scenario.torque_limit,
            external_tau=scenario.external_tau,
            step=scenario.step,
        )

    return ModelUncertaintyRun(
        controller=controller,
        configuration_sha256=FROZEN_CONFIGURATION_SHA256,
        gains=gains,
        scenario=scenario,
        simulation=simulation,
    )


@dataclass(frozen=True)
class DisturbanceRun:
    """Inputs and simulation history for one disturbance run."""

    controller: str
    configuration_sha256: str
    gains: PIDGains | ComputedTorqueGains
    scenario: DisturbanceScenario
    simulation: PIDSimulationResult | ComputedTorqueSimulationResult


def run_disturbance_controller(
    frozen_path: str | Path,
    controller: str,
) -> DisturbanceRun:
    """Run one frozen controller with the fixed end-effector disturbance."""

    gains = load_frozen_gains(frozen_path, controller)
    scenario = create_disturbance_scenario()

    if controller == "computed_torque":
        simulation = simulate_computed_torque_trajectory(
            waypoint_times=scenario.waypoint_times,
            waypoint_positions=scenario.waypoint_positions,
            initial_state=scenario.initial_state,
            gains=gains,
            params=scenario.params,
            controller_params=scenario.controller_params,
            torque_limit=scenario.torque_limit,
            external_tau=None,
            step=scenario.step,
            external_tau_factory=scenario.external_tau_factory,
        )
    else:
        controller_params = (
            scenario.controller_params if controller == "pid_gravity" else None
        )

        simulation = simulate_pid_trajectory(
            waypoint_times=scenario.waypoint_times,
            waypoint_positions=scenario.waypoint_positions,
            initial_state=scenario.initial_state,
            initial_integral_error=scenario.initial_integral_error,
            gains=gains,
            params=scenario.params,
            controller_params=controller_params,
            torque_limit=scenario.torque_limit,
            external_tau=None,
            step=scenario.step,
            external_tau_factory=scenario.external_tau_factory,
        )

    return DisturbanceRun(
        controller=controller,
        configuration_sha256=FROZEN_CONFIGURATION_SHA256,
        gains=gains,
        scenario=scenario,
        simulation=simulation,
    )


def summarize_nominal_run(
    run: NominalRun,
) -> dict[str, str | float]:
    """Build one scalar summary row from a completed nominal run."""

    history = run.simulation

    tracking = compute_tracking_metrics(
        actual_positions=history.state_history[:, :2],
        reference_positions=history.reference_position_history,
        params=run.scenario.params,
    )

    actuation = compute_actuation_metrics(
        time_values=history.time_values,
        applied_torque_history=history.applied_torque_history,
        velocity_history=history.state_history[:, 2:],
        saturation_history=history.saturation_history,
    )

    joint_rmse_deg = tracking.joint_rmse_deg

    return {
        "controller": run.controller,
        "joint_1_rmse_rad": float(tracking.joint_rmse_rad[0]),
        "joint_2_rmse_rad": float(tracking.joint_rmse_rad[1]),
        "overall_joint_rmse_rad": tracking.overall_joint_rmse_rad,
        "joint_1_rmse_deg": float(joint_rmse_deg[0]),
        "joint_2_rmse_deg": float(joint_rmse_deg[1]),
        "overall_joint_rmse_deg": tracking.overall_joint_rmse_deg,
        "end_effector_rmse_m": tracking.end_effector_rmse_m,
        "maximum_end_effector_error_m": (tracking.maximum_end_effector_error_m),
        "control_effort_nm2_s": actuation.control_effort,
        "saturation_fraction": actuation.saturation_fraction,
        "absolute_mechanical_work_j": actuation.absolute_mechanical_work_j,
    }


def summarize_payload_run(
    run: PayloadRun,
) -> dict[str, str | float]:
    """Build one scalar summary row from a completed payload run."""

    history = run.simulation

    tracking = compute_tracking_metrics(
        actual_positions=history.state_history[:, :2],
        reference_positions=history.reference_position_history,
        params=run.scenario.params,
    )

    actuation = compute_actuation_metrics(
        time_values=history.time_values,
        applied_torque_history=history.applied_torque_history,
        velocity_history=history.state_history[:, 2:],
        saturation_history=history.saturation_history,
    )

    joint_rmse_deg = tracking.joint_rmse_deg

    return {
        "controller": run.controller,
        "payload_mass_kg": float(run.scenario.params.payload_mass),
        "joint_1_rmse_rad": float(tracking.joint_rmse_rad[0]),
        "joint_2_rmse_rad": float(tracking.joint_rmse_rad[1]),
        "overall_joint_rmse_rad": tracking.overall_joint_rmse_rad,
        "joint_1_rmse_deg": float(joint_rmse_deg[0]),
        "joint_2_rmse_deg": float(joint_rmse_deg[1]),
        "overall_joint_rmse_deg": tracking.overall_joint_rmse_deg,
        "end_effector_rmse_m": tracking.end_effector_rmse_m,
        "maximum_end_effector_error_m": tracking.maximum_end_effector_error_m,
        "control_effort_nm2_s": actuation.control_effort,
        "saturation_fraction": actuation.saturation_fraction,
        "absolute_mechanical_work_j": actuation.absolute_mechanical_work_j,
    }


def summarize_model_uncertainty_run(
    run: ModelUncertaintyRun,
) -> dict[str, str | float]:
    """Build one scalar summary row for a model uncertainty run."""

    history = run.simulation

    tracking = compute_tracking_metrics(
        actual_positions=history.state_history[:, :2],
        reference_positions=history.reference_position_history,
        params=run.scenario.params,
    )

    actuation = compute_actuation_metrics(
        time_values=history.time_values,
        applied_torque_history=history.applied_torque_history,
        velocity_history=history.state_history[:, 2:],
        saturation_history=history.saturation_history,
    )

    joint_rmse_deg = tracking.joint_rmse_deg

    return {
        "controller": run.controller,
        "relative_error": float(run.scenario.relative_error),
        "joint_1_rmse_rad": float(tracking.joint_rmse_rad[0]),
        "joint_2_rmse_rad": float(tracking.joint_rmse_rad[1]),
        "overall_joint_rmse_rad": tracking.overall_joint_rmse_rad,
        "joint_1_rmse_deg": float(joint_rmse_deg[0]),
        "joint_2_rmse_deg": float(joint_rmse_deg[1]),
        "overall_joint_rmse_deg": tracking.overall_joint_rmse_deg,
        "end_effector_rmse_m": tracking.end_effector_rmse_m,
        "maximum_end_effector_error_m": tracking.maximum_end_effector_error_m,
        "control_effort_nm2_s": actuation.control_effort,
        "saturation_fraction": actuation.saturation_fraction,
        "absolute_mechanical_work_j": actuation.absolute_mechanical_work_j,
    }


def summarize_disturbance_run(
    run: DisturbanceRun,
) -> dict[str, str | float | bool | None]:
    """Build one summary row, preserving unconfirmed recovery as None."""

    history = run.simulation
    params = run.scenario.params

    actual_positions = history.state_history[:, :2]
    reference_positions = history.reference_position_history

    tracking = compute_tracking_metrics(
        actual_positions=actual_positions,
        reference_positions=reference_positions,
        params=params,
    )

    actuation = compute_actuation_metrics(
        time_values=history.time_values,
        applied_torque_history=history.applied_torque_history,
        velocity_history=history.state_history[:, 2:],
        saturation_history=history.saturation_history,
    )

    actual_xy = np.array(
        [forward_kinematics(q, params) for q in actual_positions],
        dtype=float,
    )
    reference_xy = np.array(
        [forward_kinematics(q, params) for q in reference_positions],
        dtype=float,
    )

    end_effector_errors_m = np.linalg.norm(
        reference_xy - actual_xy,
        axis=1,
    )

    recovery_time = compute_recovery_time(
        time_values=history.time_values,
        end_effector_errors_m=end_effector_errors_m,
        disturbance_end_time=4.7,
        threshold_m=0.01,
        hold_duration=0.5,
    )

    joint_rmse_deg = tracking.joint_rmse_deg

    return {
        "controller": run.controller,
        "joint_1_rmse_rad": float(tracking.joint_rmse_rad[0]),
        "joint_2_rmse_rad": float(tracking.joint_rmse_rad[1]),
        "overall_joint_rmse_rad": tracking.overall_joint_rmse_rad,
        "joint_1_rmse_deg": float(joint_rmse_deg[0]),
        "joint_2_rmse_deg": float(joint_rmse_deg[1]),
        "overall_joint_rmse_deg": tracking.overall_joint_rmse_deg,
        "end_effector_rmse_m": tracking.end_effector_rmse_m,
        "maximum_end_effector_error_m": tracking.maximum_end_effector_error_m,
        "control_effort_nm2_s": actuation.control_effort,
        "saturation_fraction": actuation.saturation_fraction,
        "absolute_mechanical_work_j": actuation.absolute_mechanical_work_j,
        "recovered": recovery_time is not None,
        "recovery_time_s": recovery_time,
    }
