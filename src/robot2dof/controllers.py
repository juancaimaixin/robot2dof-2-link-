from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from .actuation import ActuatorOutput
from .dynamics import (
    coriolis_vector,
    gravity_vector,
    mass_matrix,
)
from .parameters import RobotParams
from .state import State
from .trajectory import Reference


@dataclass(frozen=True)
class PIDGains:
    """Per-joint proportional, integral, and derivative gains."""

    kp: Sequence[float]
    ki: Sequence[float]
    kd: Sequence[float]


@dataclass(frozen=True)
class ComputedTorqueGains:
    """Per-joint gains for the virtual acceleration command."""

    kp: Sequence[float]
    kd: Sequence[float]


@dataclass(frozen=True)
class ControllerOutput:
    """Unsaturated torque request and controller diagnostics."""

    requested_torque: np.ndarray
    position_error: np.ndarray
    velocity_error: np.ndarray
    integral_error: np.ndarray


def _as_joint_vector(
    values: Sequence[float],
    name: str,
) -> np.ndarray:
    array = np.asarray(
        values,
        dtype=float,
    )

    if array.shape != (2,):
        raise ValueError(f"{name} must contain exactly two values.")

    if not np.all(np.isfinite(array)):
        raise ValueError(f"{name} must contain only finite values.")

    return array


def compute_independent_joint_pid(
    state: State,
    reference: Reference,
    integral_error: Sequence[float],
    gains: PIDGains,
) -> ControllerOutput:
    """Compute an unsaturated independent-joint PID torque."""

    q = _as_joint_vector(
        state.q,
        "state.q",
    )
    q_dot = _as_joint_vector(
        state.q_dot,
        "state.q_dot",
    )

    q_ref = _as_joint_vector(
        reference.q_ref,
        "reference.q_ref",
    )
    q_dot_ref = _as_joint_vector(
        reference.q_dot_ref,
        "reference.q_dot_ref",
    )

    integral_error_array = _as_joint_vector(
        integral_error,
        "integral_error",
    )

    kp = _as_joint_vector(
        gains.kp,
        "gains.kp",
    )
    ki = _as_joint_vector(
        gains.ki,
        "gains.ki",
    )
    kd = _as_joint_vector(
        gains.kd,
        "gains.kd",
    )

    if np.any(kp < 0.0) or np.any(ki < 0.0) or np.any(kd < 0.0):
        raise ValueError("PID gains must be non-negative.")

    position_error = q_ref - q
    velocity_error = q_dot_ref - q_dot

    requested_torque = (
        kp * position_error + kd * velocity_error + ki * integral_error_array
    )

    return ControllerOutput(
        requested_torque=requested_torque,
        position_error=position_error,
        velocity_error=velocity_error,
        integral_error=integral_error_array,
    )


def compute_pid_with_gravity_compensation(
    state: State,
    reference: Reference,
    integral_error: Sequence[float],
    gains: PIDGains,
    controller_params: RobotParams,
) -> ControllerOutput:
    """Compute independent-joint PID plus model-based gravity compensation."""

    pid_output = compute_independent_joint_pid(
        state=state,
        reference=reference,
        integral_error=integral_error,
        gains=gains,
    )

    gravity_compensation = gravity_vector(
        state.q,
        controller_params,
    )

    return ControllerOutput(
        requested_torque=(pid_output.requested_torque + gravity_compensation),
        position_error=pid_output.position_error,
        velocity_error=pid_output.velocity_error,
        integral_error=pid_output.integral_error,
    )


def compute_computed_torque(
    state: State,
    reference: Reference,
    gains: ComputedTorqueGains,
    controller_params: RobotParams,
) -> ControllerOutput:
    """Compute model-based feedback-linearizing joint torque."""

    q = _as_joint_vector(
        state.q,
        "state.q",
    )
    q_dot = _as_joint_vector(
        state.q_dot,
        "state.q_dot",
    )
    q_ref = _as_joint_vector(
        reference.q_ref,
        "reference.q_ref",
    )
    q_dot_ref = _as_joint_vector(
        reference.q_dot_ref,
        "reference.q_dot_ref",
    )
    q_ddot_ref = _as_joint_vector(
        reference.q_ddot_ref,
        "reference.q_ddot_ref",
    )
    kp = _as_joint_vector(
        gains.kp,
        "gains.kp",
    )
    kd = _as_joint_vector(
        gains.kd,
        "gains.kd",
    )

    if np.any(kp < 0.0) or np.any(kd < 0.0):
        raise ValueError("Computed Torque gains must be non-negative.")

    position_error = q_ref - q
    velocity_error = q_dot_ref - q_dot

    virtual_acceleration = q_ddot_ref + kd * velocity_error + kp * position_error

    requested_torque = (
        mass_matrix(
            q,
            controller_params,
        )
        @ virtual_acceleration
        + coriolis_vector(
            q,
            q_dot,
            controller_params,
        )
        + gravity_vector(
            q,
            controller_params,
        )
    )

    return ControllerOutput(
        requested_torque=requested_torque,
        position_error=position_error,
        velocity_error=velocity_error,
        integral_error=np.zeros(2),
    )


def update_integral_error_conditionally(
    integral_error: Sequence[float],
    position_error: Sequence[float],
    actuator_output: ActuatorOutput,
    step: float,
) -> np.ndarray:
    """Update PID integral error using conditional integration."""

    integral_error_array = _as_joint_vector(
        integral_error,
        "integral_error",
    )
    position_error_array = _as_joint_vector(
        position_error,
        "position_error",
    )
    applied_torque = _as_joint_vector(
        actuator_output.applied_torque,
        "actuator_output.applied_torque",
    )

    saturated = np.asarray(
        actuator_output.saturated,
        dtype=bool,
    )

    if saturated.shape != (2,):
        raise ValueError("actuator_output.saturated must contain exactly two values.")

    if not np.isfinite(step) or step <= 0.0:
        raise ValueError("step must be a positive finite value.")

    pushes_further_into_saturation = saturated & (
        applied_torque * position_error_array > 0.0
    )

    error_to_integrate = np.where(
        pushes_further_into_saturation,
        0.0,
        position_error_array,
    )

    return integral_error_array + step * error_to_integrate
