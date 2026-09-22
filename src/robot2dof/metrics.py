from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .kinematics import forward_kinematics
from .parameters import RobotParams


@dataclass(frozen=True)
class TrackingMetrics:
    """Joint and Cartesian tracking errors."""

    joint_rmse_rad: np.ndarray
    overall_joint_rmse_rad: float
    end_effector_rmse_m: float
    maximum_end_effector_error_m: float

    @property
    def joint_rmse_deg(self) -> np.ndarray:
        return np.degrees(self.joint_rmse_rad)

    @property
    def overall_joint_rmse_deg(self) -> float:
        return float(np.degrees(self.overall_joint_rmse_rad))


def compute_tracking_metrics(
    actual_positions: Sequence[Sequence[float]],
    reference_positions: Sequence[Sequence[float]],
    params: RobotParams,
) -> TrackingMetrics:
    """Compute errors over all samples of a uniform time grid."""

    actual = np.asarray(actual_positions, dtype=float)
    reference = np.asarray(reference_positions, dtype=float)

    if actual.ndim != 2 or actual.shape[1] != 2:
        raise ValueError("actual_positions must have shape (N, 2).")
    if actual.shape[0] == 0:
        raise ValueError("At least one position sample is required.")
    if reference.shape != actual.shape:
        raise ValueError("Position histories must have the same shape.")
    if not np.all(np.isfinite(actual)):
        raise ValueError("actual_positions must be finite.")
    if not np.all(np.isfinite(reference)):
        raise ValueError("reference_positions must be finite.")

    joint_error = reference - actual
    squared_joint_error = joint_error**2

    joint_rmse = np.sqrt(np.mean(squared_joint_error, axis=0))
    overall_joint_rmse = float(np.sqrt(np.mean(squared_joint_error)))

    actual_xy = np.array(
        [forward_kinematics(q, params) for q in actual],
        dtype=float,
    )
    reference_xy = np.array(
        [forward_kinematics(q, params) for q in reference],
        dtype=float,
    )

    cartesian_error = reference_xy - actual_xy
    squared_distance = np.sum(cartesian_error**2, axis=1)

    return TrackingMetrics(
        joint_rmse_rad=joint_rmse,
        overall_joint_rmse_rad=overall_joint_rmse,
        end_effector_rmse_m=float(np.sqrt(np.mean(squared_distance))),
        maximum_end_effector_error_m=float(np.sqrt(np.max(squared_distance))),
    )


@dataclass(frozen=True)
class ActuationMetrics:
    """Control effort in (N m)^2 s, saturation fraction, and work in J."""

    control_effort: float
    saturation_fraction: float
    absolute_mechanical_work_j: float


def compute_actuation_metrics(
    time_values: Sequence[float],
    applied_torque_history: Sequence[Sequence[float]],
    velocity_history: Sequence[Sequence[float]],
    saturation_history: Sequence[Sequence[bool]],
) -> ActuationMetrics:
    """Compute interval metrics using applied torques and left samples."""

    time = np.asarray(time_values, dtype=float)
    torque = np.asarray(applied_torque_history, dtype=float)
    velocity = np.asarray(velocity_history, dtype=float)
    saturation = np.asarray(saturation_history)

    if time.ndim != 1 or time.size < 2:
        raise ValueError("time_values must contain at least two samples.")
    if not np.all(np.isfinite(time)):
        raise ValueError("time_values must be finite.")

    interval_durations = np.diff(time)
    if np.any(interval_durations <= 0.0):
        raise ValueError("time_values must be strictly increasing.")

    expected_shape = (time.size, 2)

    for history, name in (
        (torque, "applied_torque_history"),
        (velocity, "velocity_history"),
    ):
        if history.shape != expected_shape:
            raise ValueError(f"{name} must have shape {expected_shape}.")
        if not np.all(np.isfinite(history)):
            raise ValueError(f"{name} must be finite.")

    if saturation.shape != expected_shape:
        raise ValueError(f"saturation_history must have shape {expected_shape}.")
    if saturation.dtype != np.bool_:
        raise ValueError("saturation_history must contain booleans.")

    duration = float(time[-1] - time[0])

    squared_torque = np.sum(torque[:-1] ** 2, axis=1)
    control_effort = float(np.sum(squared_torque * interval_durations))

    saturated_intervals = np.any(saturation[:-1], axis=1)
    saturation_fraction = float(
        np.sum(saturated_intervals * interval_durations) / duration
    )

    # Sum joint powers before taking the absolute value.
    power = np.sum(torque[:-1] * velocity[:-1], axis=1)
    absolute_work = float(np.sum(np.abs(power) * interval_durations))

    return ActuationMetrics(
        control_effort=control_effort,
        saturation_fraction=saturation_fraction,
        absolute_mechanical_work_j=absolute_work,
    )


def compute_recovery_time(
    time_values: Sequence[float],
    end_effector_errors_m: Sequence[float],
    disturbance_end_time: float = 4.7,
    threshold_m: float = 0.01,
    hold_duration: float = 0.5,
) -> float | None:
    """Return recovery delay from sampled errors, or None if unconfirmed."""

    time = np.asarray(time_values, dtype=float)
    errors = np.asarray(end_effector_errors_m, dtype=float)

    if time.ndim != 1 or time.size < 2:
        raise ValueError("time_values must contain at least two samples.")

    if not np.all(np.isfinite(time)):
        raise ValueError("time_values must be finite.")

    if np.any(np.diff(time) <= 0.0):
        raise ValueError("time_values must be strictly increasing.")

    if errors.shape != time.shape:
        raise ValueError("Error history must have the same shape as time_values.")

    if not np.all(np.isfinite(errors)) or np.any(errors < 0.0):
        raise ValueError("End-effector errors must be finite and non-negative.")

    if not np.isfinite(disturbance_end_time):
        raise ValueError("disturbance_end_time must be finite.")

    if not np.isfinite(threshold_m) or threshold_m <= 0.0:
        raise ValueError("threshold_m must be positive and finite.")

    if not np.isfinite(hold_duration) or hold_duration <= 0.0:
        raise ValueError("hold_duration must be positive and finite.")

    tolerance = 1e-12

    if not (time[0] - tolerance <= disturbance_end_time <= time[-1] + tolerance):
        raise ValueError("Time history must cover the disturbance end time.")

    start_index: int | None = None

    for index, current_time in enumerate(time):
        if current_time < disturbance_end_time - tolerance:
            continue

        if errors[index] > threshold_m:
            start_index = None
            continue

        if start_index is None:
            start_index = index

        elapsed = current_time - time[start_index]

        if elapsed >= hold_duration - tolerance:
            return max(
                0.0,
                float(time[start_index] - disturbance_end_time),
            )

    return None
