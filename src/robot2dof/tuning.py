from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from .controllers import ComputedTorqueGains, PIDGains
from .parameters import RobotParams
from .simulation import (
    ComputedTorqueSimulationResult,
    PIDSimulationResult,
    simulate_computed_torque_trajectory,
    simulate_pid_trajectory,
)


@dataclass(frozen=True)
class TuningWeights:
    """Weights used by the common tuning objective."""

    tracking_error: float
    control_effort: float
    saturation: float


@dataclass(frozen=True)
class TuningMetrics:
    """Dimensionless metrics and total tuning score."""

    normalized_joint_rmse: float
    normalized_control_effort: float
    saturation_fraction: float
    score: float


DEFAULT_TUNING_WEIGHTS = TuningWeights(
    tracking_error=0.7,
    control_effort=0.2,
    saturation=0.1,
)


def _as_joint_vector(
    values: Sequence[float],
    name: str,
) -> np.ndarray:
    array = np.asarray(values, dtype=float)

    if array.shape != (2,):
        raise ValueError(f"{name} must contain exactly two values.")

    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values.")

    return array


def _as_positive_joint_vector(
    values: Sequence[float],
    name: str,
) -> np.ndarray:
    array = _as_joint_vector(values, name)

    if np.any(array <= 0.0):
        raise ValueError(f"{name} must contain only positive values.")

    return array


def computed_torque_gains_from_targets(
    natural_frequency: Sequence[float],
    damping_ratio: Sequence[float],
) -> ComputedTorqueGains:
    """Convert second-order targets into Computed Torque gains."""

    omega = _as_positive_joint_vector(
        natural_frequency,
        "natural_frequency",
    )
    zeta = _as_positive_joint_vector(
        damping_ratio,
        "damping_ratio",
    )

    return ComputedTorqueGains(
        kp=omega**2,
        kd=2.0 * zeta * omega,
    )


def compute_tuning_metrics(
    time_values: Sequence[float],
    actual_positions: Sequence[Sequence[float]],
    reference_positions: Sequence[Sequence[float]],
    applied_torque_history: Sequence[Sequence[float]],
    saturation_history: Sequence[Sequence[bool]],
    torque_limit: float | Sequence[float],
    weights: TuningWeights,
) -> TuningMetrics:
    """Compute the common dimensionless controller-tuning objective."""

    time_array = np.asarray(time_values, dtype=float)
    actual_array = np.asarray(actual_positions, dtype=float)
    reference_array = np.asarray(reference_positions, dtype=float)
    torque_array = np.asarray(applied_torque_history, dtype=float)
    saturation_array = np.asarray(saturation_history, dtype=bool)

    if time_array.ndim != 1 or time_array.size < 2:
        raise ValueError("time_values must contain at least two samples.")

    if not np.all(np.isfinite(time_array)):
        raise ValueError("time_values must contain only finite values.")

    if np.any(np.diff(time_array) <= 0.0):
        raise ValueError("time_values must be strictly increasing.")

    expected_shape = (time_array.size, 2)

    numeric_histories = (
        (actual_array, "actual_positions"),
        (reference_array, "reference_positions"),
        (torque_array, "applied_torque_history"),
    )

    for history, name in numeric_histories:
        if history.shape != expected_shape:
            raise ValueError(f"{name} must have shape {expected_shape}.")

        if not np.all(np.isfinite(history)):
            raise ValueError(f"{name} must contain only finite values.")

    if saturation_array.shape != expected_shape:
        raise ValueError(f"saturation_history must have shape {expected_shape}.")

    limit_array = np.asarray(torque_limit, dtype=float)

    if limit_array.ndim == 0:
        limit_array = np.full(2, limit_array.item())
    elif limit_array.shape != (2,):
        raise ValueError("torque_limit must be scalar or contain two values.")

    if not np.all(np.isfinite(limit_array)) or np.any(limit_array <= 0.0):
        raise ValueError("torque_limit must contain positive finite values.")

    weight_array = np.array(
        [
            weights.tracking_error,
            weights.control_effort,
            weights.saturation,
        ],
        dtype=float,
    )

    if not np.all(np.isfinite(weight_array)) or np.any(weight_array < 0.0):
        raise ValueError("Tuning weights must be non-negative and finite.")

    if not np.isclose(np.sum(weight_array), 1.0, atol=1e-12):
        raise ValueError("Tuning weights must sum to one.")

    position_span = np.ptp(reference_array, axis=0)

    if np.any(position_span <= 0.0):
        raise ValueError("Each reference joint must have a positive range.")

    normalized_error = (reference_array - actual_array) / position_span

    normalized_joint_rmse = float(np.sqrt(np.mean(normalized_error**2)))

    interval_durations = np.diff(time_array)
    duration = float(time_array[-1] - time_array[0])

    # Each torque sample is held over the following control interval.
    effort_per_interval = np.sum(torque_array[:-1] ** 2, axis=1)
    control_effort = float(np.sum(effort_per_interval * interval_durations))

    maximum_effort = duration * np.sum(limit_array**2)

    normalized_control_effort = float(control_effort / maximum_effort)

    # An interval is saturated when either joint is saturated.
    saturated_intervals = np.any(
        saturation_array[:-1],
        axis=1,
    )

    saturation_fraction = float(
        np.sum(saturated_intervals * interval_durations) / duration
    )

    score = (
        weights.tracking_error * normalized_joint_rmse
        + weights.control_effort * normalized_control_effort
        + weights.saturation * saturation_fraction
    )

    return TuningMetrics(
        normalized_joint_rmse=normalized_joint_rmse,
        normalized_control_effort=normalized_control_effort,
        saturation_fraction=saturation_fraction,
        score=float(score),
    )


@dataclass(frozen=True)
class TrainingScenario:
    """Common simulation inputs for one training candidate."""

    waypoint_times: np.ndarray
    waypoint_positions: np.ndarray
    initial_state: np.ndarray
    initial_integral_error: np.ndarray
    params: RobotParams
    controller_params: RobotParams
    torque_limit: float
    external_tau: np.ndarray
    step: float


def create_training_scenario() -> TrainingScenario:
    """Create fresh nominal training inputs for each candidate."""

    waypoint_positions = np.radians(
        [
            [-35.0, -45.0],
            [50.0, 60.0],
        ]
    )

    initial_state = np.concatenate(
        (
            waypoint_positions[0],
            np.zeros(2),
        )
    )

    return TrainingScenario(
        waypoint_times=np.array([0.0, 4.0]),
        waypoint_positions=waypoint_positions,
        initial_state=initial_state,
        initial_integral_error=np.zeros(2),
        params=RobotParams(),
        controller_params=RobotParams(),
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
    )


TUNING_CANDIDATE_COUNT = 300
TUNING_SEED = 20260905

# Sampling order: kp1, ki1, kd1, kp2, ki2, kd2.
# Direct engineering ranges containing the existing development baseline.
PID_GAIN_LOWER_BOUNDS = (20.0, 0.0, 1.0, 10.0, 0.0, 0.5)
PID_GAIN_UPPER_BOUNDS = (300.0, 100.0, 60.0, 200.0, 80.0, 40.0)


@dataclass(frozen=True)
class PIDTuningCandidate:
    """Six independent gains shared by PID and PID + Gravity tuning."""

    candidate_id: int
    kp: tuple[float, float]
    ki: tuple[float, float]
    kd: tuple[float, float]


PID_BASELINE = PIDTuningCandidate(
    candidate_id=0,
    kp=(150.0, 100.0),
    ki=(30.0, 20.0),
    kd=(25.0, 15.0),
)


def generate_pid_tuning_candidates() -> tuple[PIDTuningCandidate, ...]:
    """Generate one direct-gain baseline and 299 uniform random candidates.

    PID and PID + Gravity evaluate the same returned table independently.
    Each gain is sampled directly, without any robot-model transformation.
    """

    rng = np.random.Generator(np.random.PCG64(TUNING_SEED))
    candidates = [PID_BASELINE]

    for candidate_id in range(1, TUNING_CANDIDATE_COUNT):
        values = rng.uniform(PID_GAIN_LOWER_BOUNDS, PID_GAIN_UPPER_BOUNDS)
        candidates.append(
            PIDTuningCandidate(
                candidate_id=candidate_id,
                kp=(float(values[0]), float(values[3])),
                ki=(float(values[1]), float(values[4])),
                kd=(float(values[2]), float(values[5])),
            )
        )

    return tuple(candidates)


def build_pid_candidate_gains(candidate: PIDTuningCandidate) -> PIDGains:
    """Copy direct candidate gains into an independent controller input."""

    values = {}
    for name in ("kp", "ki", "kd"):
        array = _as_joint_vector(getattr(candidate, name), name)
        if np.any(array < 0.0):
            raise ValueError(f"{name} must contain only non-negative values.")
        values[name] = array.copy()

    return PIDGains(**values)


@dataclass(frozen=True)
class ComputedTorqueTuningCandidate:
    """Second-order targets used only by Computed Torque tuning."""

    candidate_id: int
    natural_frequency: tuple[float, float]
    damping_ratio: tuple[float, float]


def generate_computed_torque_tuning_candidates() -> tuple[
    ComputedTorqueTuningCandidate, ...
]:
    """Preserve the original 300 CTC targets and their sampling order."""

    rng = np.random.Generator(np.random.PCG64(TUNING_SEED))

    candidates = [
        ComputedTorqueTuningCandidate(
            candidate_id=0,
            natural_frequency=(8.0, 8.0),
            damping_ratio=(1.0, 1.0),
        )
    ]

    for candidate_id in range(1, TUNING_CANDIDATE_COUNT):
        natural_frequency = rng.uniform(
            3.0,
            12.0,
            size=2,
        )
        damping_ratio = rng.uniform(
            0.7,
            1.2,
            size=2,
        )
        # The old shared generator consumed this draw after each CTC row.
        # Discard it to preserve every existing CTC target exactly; it is
        # not an integral parameter and does not enter either controller.
        rng.choice((0.0, 0.05, 0.1, 0.2))

        candidates.append(
            ComputedTorqueTuningCandidate(
                candidate_id=candidate_id,
                natural_frequency=(
                    float(natural_frequency[0]),
                    float(natural_frequency[1]),
                ),
                damping_ratio=(
                    float(damping_ratio[0]),
                    float(damping_ratio[1]),
                ),
            )
        )

    return tuple(candidates)


def build_computed_torque_candidate_gains(
    candidate: ComputedTorqueTuningCandidate,
) -> ComputedTorqueGains:
    """Apply the unchanged CTC mapping to one candidate."""

    return computed_torque_gains_from_targets(
        natural_frequency=candidate.natural_frequency,
        damping_ratio=candidate.damping_ratio,
    )


ControllerName = Literal["pid", "pid_gravity", "computed_torque"]
TrainingSimulation = PIDSimulationResult | ComputedTorqueSimulationResult
TUNING_POSITION_LIMIT = np.pi
TUNING_VELOCITY_LIMIT = 50.0


@dataclass(frozen=True)
class CandidateEvaluation:
    """One training run, including diagnostics for failed candidates."""

    controller: ControllerName
    candidate: PIDTuningCandidate | ComputedTorqueTuningCandidate
    gains: PIDGains | ComputedTorqueGains
    simulation: TrainingSimulation | None
    metrics: TuningMetrics | None
    failure_reason: str | None

    @property
    def succeeded(self) -> bool:
        return self.failure_reason is None and self.metrics is not None

    @property
    def score(self) -> float:
        """Failed candidates cannot beat a finite successful score."""
        if self.failure_reason is not None or self.metrics is None:
            return float("inf")
        return self.metrics.score


@dataclass(frozen=True)
class TuningSearchResult:
    """All fixed-budget evaluations and the best successful candidate."""

    controller: ControllerName
    evaluations: tuple[CandidateEvaluation, ...]
    best_evaluation: CandidateEvaluation | None


def _training_history_failure(simulation: TrainingSimulation) -> str | None:
    """Screen every recorded sample, including the final state and output."""

    history_names = (
        "time_values",
        "state_history",
        "reference_position_history",
        "reference_velocity_history",
        "reference_acceleration_history",
        "requested_torque_history",
        "applied_torque_history",
    )
    if isinstance(simulation, PIDSimulationResult):
        history_names += ("integral_error_history",)

    for name in history_names:
        if not np.all(np.isfinite(getattr(simulation, name))):
            return f"non_finite_history: {name}"

    if np.any(np.abs(simulation.state_history[:, :2]) > TUNING_POSITION_LIMIT):
        return "joint_position_limit"
    if np.any(np.abs(simulation.state_history[:, 2:]) > TUNING_VELOCITY_LIMIT):
        return "joint_velocity_limit"
    return None


def evaluate_training_candidate(
    controller: ControllerName,
    candidate: PIDTuningCandidate | ComputedTorqueTuningCandidate,
) -> CandidateEvaluation:
    """Run one candidate on the fixed training trajectory and score it.

    A fresh nominal scenario is created for every call. No held-out trajectory
    can be supplied through this interface. Invalid calls propagate errors;
    numerical failures are recorded so later search can continue its budget.
    Histories remain available after a completed simulation, including failures
    found during screening. An interrupted simulation has no complete history.
    """

    if controller not in ("pid", "pid_gravity", "computed_torque"):
        raise ValueError(f"Unknown controller: {controller}")
    if controller == "computed_torque":
        if not isinstance(candidate, ComputedTorqueTuningCandidate):
            raise TypeError("computed_torque requires a ComputedTorqueTuningCandidate.")
        gains = build_computed_torque_candidate_gains(candidate)
    else:
        if not isinstance(candidate, PIDTuningCandidate):
            raise TypeError("PID controllers require a PIDTuningCandidate.")
        gains = build_pid_candidate_gains(candidate)

    scenario = create_training_scenario()
    simulation = None
    metrics = None
    failure_reason = None

    try:
        # Raise at the numerical operation that fails, before NaN/Inf reaches
        # an unrelated input validator. Do not catch ordinary API/code errors.
        with np.errstate(over="raise", invalid="raise", divide="raise", under="ignore"):
            common_inputs = dict(
                waypoint_times=scenario.waypoint_times,
                waypoint_positions=scenario.waypoint_positions,
                initial_state=scenario.initial_state,
                params=scenario.params,
                torque_limit=scenario.torque_limit,
                external_tau=scenario.external_tau,
                step=scenario.step,
            )
            if controller == "computed_torque":
                simulation = simulate_computed_torque_trajectory(
                    **common_inputs,
                    gains=gains,
                    controller_params=scenario.controller_params,
                )
            else:
                simulation = simulate_pid_trajectory(
                    **common_inputs,
                    initial_integral_error=scenario.initial_integral_error,
                    gains=gains,
                    controller_params=(
                        scenario.controller_params
                        if controller == "pid_gravity"
                        else None
                    ),
                )

            failure_reason = _training_history_failure(simulation)
            if failure_reason is None:
                metrics = compute_tuning_metrics(
                    time_values=simulation.time_values,
                    actual_positions=simulation.state_history[:, :2],
                    reference_positions=simulation.reference_position_history,
                    applied_torque_history=simulation.applied_torque_history,
                    saturation_history=simulation.saturation_history,
                    torque_limit=scenario.torque_limit,
                    weights=DEFAULT_TUNING_WEIGHTS,
                )
                if not np.all(
                    np.isfinite(
                        [
                            metrics.normalized_joint_rmse,
                            metrics.normalized_control_effort,
                            metrics.saturation_fraction,
                            metrics.score,
                        ]
                    )
                ):
                    failure_reason = "non_finite_metrics"
                    metrics = None
    except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as error:
        failure_reason = f"numerical_failure: {type(error).__name__}: {error}"
        metrics = None

    return CandidateEvaluation(
        controller=controller,
        candidate=candidate,
        gains=gains,
        simulation=simulation,
        metrics=metrics,
        failure_reason=failure_reason,
    )


def _successful_evaluation_key(
    evaluation: CandidateEvaluation,
) -> tuple[float, float, int]:
    if not evaluation.succeeded or evaluation.metrics is None:
        raise ValueError("Only successful evaluations can be ranked.")

    return (
        evaluation.metrics.score,
        evaluation.metrics.normalized_control_effort,
        evaluation.candidate.candidate_id,
    )


def run_training_search(controller: ControllerName) -> TuningSearchResult:
    """Evaluate the complete fixed candidate budget for one controller."""

    if controller not in ("pid", "pid_gravity", "computed_torque"):
        raise ValueError(f"Unknown controller: {controller}")

    if controller == "computed_torque":
        candidates = generate_computed_torque_tuning_candidates()
    else:
        candidates = generate_pid_tuning_candidates()

    evaluations = tuple(
        evaluate_training_candidate(controller, candidate) for candidate in candidates
    )

    successful_evaluations = (
        evaluation for evaluation in evaluations if evaluation.succeeded
    )
    best_evaluation = min(
        successful_evaluations,
        key=_successful_evaluation_key,
        default=None,
    )

    return TuningSearchResult(
        controller=controller,
        evaluations=evaluations,
        best_evaluation=best_evaluation,
    )
