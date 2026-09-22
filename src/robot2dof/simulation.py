from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from .actuation import (
    ActuatorOutput,
    saturate_joint_torque,
)
from .controllers import (
    ComputedTorqueGains,
    ControllerOutput,
    PIDGains,
    compute_computed_torque,
    compute_independent_joint_pid,
    compute_pid_with_gravity_compensation,
    update_integral_error_conditionally,
)
from .dynamics import forward_dynamics
from .parameters import RobotParams
from .state import State
from .trajectory import (
    Reference,
    sample_quintic_trajectory,
)

ExternalTorque = Sequence[float] | Callable[[float, np.ndarray], Sequence[float]]


ExternalTorqueFactory = Callable[
    [float, float, RobotParams],
    ExternalTorque,
]


def evaluate_external_torque(
    external_tau: ExternalTorque,
    time: float,
    q: np.ndarray,
) -> np.ndarray:
    """Evaluate a fixed or time- and configuration-dependent torque."""

    values = external_tau(time, q) if callable(external_tau) else external_tau
    torque = np.asarray(values, dtype=float)

    if torque.shape != (2,):
        raise ValueError("external_tau must contain exactly two values.")

    if not np.all(np.isfinite(torque)):
        raise ValueError("external_tau must contain only finite values.")

    return torque


def rk4_step(
    derivative: Callable[[float, np.ndarray], np.ndarray],
    time: float,
    state_vector: Sequence[float],
    step: float,
) -> np.ndarray:
    """Advance one fixed RK4 integration step."""

    state_array = np.asarray(
        state_vector,
        dtype=float,
    )

    k1 = np.asarray(
        derivative(time, state_array),
        dtype=float,
    )

    k2 = np.asarray(
        derivative(
            time + step / 2.0,
            state_array + step * k1 / 2.0,
        ),
        dtype=float,
    )

    k3 = np.asarray(
        derivative(
            time + step / 2.0,
            state_array + step * k2 / 2.0,
        ),
        dtype=float,
    )

    k4 = np.asarray(
        derivative(
            time + step,
            state_array + step * k3,
        ),
        dtype=float,
    )

    return state_array + step * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0


def state_derivative(
    time: float,
    state_vector: Sequence[float],
    tau: Sequence[float],
    params: RobotParams,
    external_tau: ExternalTorque,
) -> np.ndarray:
    """Return x_dot for x = [q1, q2, q1_dot, q2_dot]."""

    state_array = np.asarray(state_vector, dtype=float)

    if state_array.shape != (4,):
        raise ValueError("state_vector must contain [q1, q2, q1_dot, q2_dot].")

    q = state_array[:2]
    q_dot = state_array[2:]

    state = State(q=q, q_dot=q_dot)

    external_tau_array = evaluate_external_torque(
        external_tau=external_tau,
        time=time,
        q=q,
    )

    q_ddot = forward_dynamics(
        state,
        tau,
        params,
        external_tau_array,
    )

    return np.concatenate((q_dot, q_ddot))


def integrate_fixed_steps(
    derivative: Callable[[float, np.ndarray], np.ndarray],
    initial_state: Sequence[float],
    start_time: float,
    end_time: float,
    step: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate an ODE on a fixed time grid using RK4."""

    if step <= 0.0:
        raise ValueError("step must be positive.")

    if end_time < start_time:
        raise ValueError("end_time must not be earlier than start_time.")

    duration = end_time - start_time
    step_count = round(duration / step)

    if not np.isclose(
        step_count * step,
        duration,
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError("The integration interval must be divisible by step.")

    initial_array = np.asarray(
        initial_state,
        dtype=float,
    )

    if initial_array.ndim != 1:
        raise ValueError("initial_state must be one-dimensional.")

    time_values = start_time + step * np.arange(
        step_count + 1,
        dtype=float,
    )

    state_history = np.empty(
        (
            step_count + 1,
            initial_array.size,
        ),
        dtype=float,
    )
    state_history[0] = initial_array

    for index in range(step_count):
        state_history[index + 1] = rk4_step(
            derivative,
            time=float(time_values[index]),
            state_vector=state_history[index],
            step=step,
        )

    return time_values, state_history


@dataclass(frozen=True)
class PIDStepResult:
    """Result of one sampled PID control cycle."""

    next_state_vector: np.ndarray
    next_integral_error: np.ndarray
    controller_output: ControllerOutput
    actuator_output: ActuatorOutput


def pid_closed_loop_step(
    time: float,
    state_vector: Sequence[float],
    integral_error: Sequence[float],
    reference: Reference,
    gains: PIDGains,
    params: RobotParams,
    torque_limit: float | Sequence[float],
    external_tau: ExternalTorque,
    step: float,
    controller_params: RobotParams | None = None,
) -> PIDStepResult:
    """Advance one sampled PID control cycle."""

    if not np.isfinite(step) or step <= 0.0:
        raise ValueError("step must be a positive finite value.")

    state_array = np.asarray(
        state_vector,
        dtype=float,
    )

    if state_array.shape != (4,):
        raise ValueError("state_vector must contain [q1, q2, q1_dot, q2_dot].")

    if not callable(external_tau):
        external_tau = evaluate_external_torque(
            external_tau=external_tau,
            time=time,
            q=state_array[:2],
        )

    state = State(
        q=state_array[:2],
        q_dot=state_array[2:],
    )

    if controller_params is None:
        controller_output = compute_independent_joint_pid(
            state=state,
            reference=reference,
            integral_error=integral_error,
            gains=gains,
        )
    else:
        controller_output = compute_pid_with_gravity_compensation(
            state=state,
            reference=reference,
            integral_error=integral_error,
            gains=gains,
            controller_params=controller_params,
        )

    actuator_output = saturate_joint_torque(
        requested_torque=controller_output.requested_torque,
        torque_limit=torque_limit,
    )

    def held_torque_derivative(
        stage_time: float,
        stage_state_vector: np.ndarray,
    ) -> np.ndarray:
        return state_derivative(
            stage_time,
            stage_state_vector,
            tau=actuator_output.applied_torque,
            params=params,
            external_tau=external_tau,
        )

    next_state_vector = rk4_step(
        held_torque_derivative,
        time=time,
        state_vector=state_array,
        step=step,
    )

    next_integral_error = update_integral_error_conditionally(
        integral_error=integral_error,
        position_error=controller_output.position_error,
        actuator_output=actuator_output,
        step=step,
    )

    return PIDStepResult(
        next_state_vector=next_state_vector,
        next_integral_error=next_integral_error,
        controller_output=controller_output,
        actuator_output=actuator_output,
    )


@dataclass(frozen=True)
class ComputedTorqueStepResult:
    """Result of one sampled Computed Torque control cycle."""

    next_state_vector: np.ndarray
    controller_output: ControllerOutput
    actuator_output: ActuatorOutput


def computed_torque_closed_loop_step(
    time: float,
    state_vector: Sequence[float],
    reference: Reference,
    gains: ComputedTorqueGains,
    params: RobotParams,
    controller_params: RobotParams,
    torque_limit: float | Sequence[float],
    external_tau: ExternalTorque,
    step: float,
) -> ComputedTorqueStepResult:
    """Advance one sampled Computed Torque control cycle."""

    if not np.isfinite(step) or step <= 0.0:
        raise ValueError("step must be a positive finite value.")

    state_array = np.asarray(state_vector, dtype=float)

    if state_array.shape != (4,):
        raise ValueError("state_vector must contain [q1, q2, q1_dot, q2_dot].")

    if not callable(external_tau):
        external_tau = evaluate_external_torque(
            external_tau=external_tau,
            time=time,
            q=state_array[:2],
        )

    state = State(
        q=state_array[:2],
        q_dot=state_array[2:],
    )

    controller_output = compute_computed_torque(
        state=state,
        reference=reference,
        gains=gains,
        controller_params=controller_params,
    )

    actuator_output = saturate_joint_torque(
        requested_torque=controller_output.requested_torque,
        torque_limit=torque_limit,
    )

    def held_torque_derivative(
        stage_time: float,
        stage_state_vector: np.ndarray,
    ) -> np.ndarray:
        return state_derivative(
            stage_time,
            stage_state_vector,
            tau=actuator_output.applied_torque,
            params=params,
            external_tau=external_tau,
        )

    next_state_vector = rk4_step(
        held_torque_derivative,
        time=time,
        state_vector=state_array,
        step=step,
    )

    return ComputedTorqueStepResult(
        next_state_vector=next_state_vector,
        controller_output=controller_output,
        actuator_output=actuator_output,
    )


@dataclass(frozen=True)
class PIDSimulationResult:
    """Histories from a sampled PID trajectory simulation."""

    time_values: np.ndarray
    state_history: np.ndarray
    reference_position_history: np.ndarray
    reference_velocity_history: np.ndarray
    reference_acceleration_history: np.ndarray
    integral_error_history: np.ndarray
    requested_torque_history: np.ndarray
    applied_torque_history: np.ndarray
    saturation_history: np.ndarray


def simulate_pid_trajectory(
    waypoint_times: Sequence[float],
    waypoint_positions: Sequence[Sequence[float]],
    initial_state: Sequence[float],
    initial_integral_error: Sequence[float],
    gains: PIDGains,
    params: RobotParams,
    torque_limit: float | Sequence[float],
    external_tau: ExternalTorque | None,
    step: float,
    controller_params: RobotParams | None = None,
    external_tau_factory: ExternalTorqueFactory | None = None,
) -> PIDSimulationResult:
    """Simulate PID tracking with exactly one external-torque input mode.

    A factory receives each interval's time, step, and actual plant params.
    Pass external_tau=None when providing external_tau_factory.
    """

    if not np.isfinite(step) or step <= 0.0:
        raise ValueError("step must be a positive finite value.")

    if (external_tau is None) == (external_tau_factory is None):
        raise ValueError("Provide exactly one of external_tau or external_tau_factory.")

    if external_tau_factory is not None and not callable(external_tau_factory):
        raise ValueError("external_tau_factory must be callable.")

    waypoint_time_array = np.asarray(
        waypoint_times,
        dtype=float,
    )
    waypoint_position_array = np.asarray(
        waypoint_positions,
        dtype=float,
    )

    if waypoint_time_array.ndim != 1 or waypoint_time_array.size < 2:
        raise ValueError(
            "waypoint_times must be one-dimensional and contain at least two values."
        )

    if not np.all(np.isfinite(waypoint_time_array)):
        raise ValueError("waypoint_times must contain only finite values.")

    if np.any(np.diff(waypoint_time_array) <= 0.0):
        raise ValueError("waypoint_times must be strictly increasing.")

    if waypoint_position_array.shape != (
        waypoint_time_array.size,
        2,
    ):
        raise ValueError("waypoint_positions must have shape (number_of_waypoints, 2).")

    if not np.all(np.isfinite(waypoint_position_array)):
        raise ValueError("waypoint_positions must contain only finite values.")

    initial_state_array = np.asarray(
        initial_state,
        dtype=float,
    )
    initial_integral_array = np.asarray(
        initial_integral_error,
        dtype=float,
    )

    if initial_state_array.shape != (4,):
        raise ValueError("initial_state must contain [q1, q2, q1_dot, q2_dot].")

    if not np.all(np.isfinite(initial_state_array)):
        raise ValueError("initial_state must contain only finite values.")

    if initial_integral_array.shape != (2,):
        raise ValueError("initial_integral_error must contain two values.")

    if not np.all(np.isfinite(initial_integral_array)):
        raise ValueError("initial_integral_error must contain only finite values.")

    start_time = float(waypoint_time_array[0])
    end_time = float(waypoint_time_array[-1])
    duration = end_time - start_time
    step_count = round(duration / step)

    if not np.isclose(
        step_count * step,
        duration,
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError("The trajectory duration must be divisible by step.")

    sample_count = step_count + 1

    time_values = start_time + step * np.arange(
        sample_count,
        dtype=float,
    )

    state_history = np.empty(
        (
            sample_count,
            4,
        ),
        dtype=float,
    )
    reference_position_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    reference_velocity_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    reference_acceleration_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    integral_error_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    requested_torque_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    applied_torque_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    saturation_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=bool,
    )

    state_history[0] = initial_state_array
    integral_error_history[0] = initial_integral_array

    for index in range(step_count):
        reference = sample_quintic_trajectory(
            time=float(time_values[index]),
            waypoint_times=waypoint_time_array,
            waypoint_positions=waypoint_position_array,
        )

        reference_position_history[index] = reference.q_ref
        reference_velocity_history[index] = reference.q_dot_ref
        reference_acceleration_history[index] = reference.q_ddot_ref

        step_external_tau = external_tau

        if external_tau_factory is not None:
            step_external_tau = external_tau_factory(
                float(time_values[index]),
                step,
                params,
            )

        step_result = pid_closed_loop_step(
            time=float(time_values[index]),
            state_vector=state_history[index],
            integral_error=integral_error_history[index],
            reference=reference,
            gains=gains,
            params=params,
            torque_limit=torque_limit,
            external_tau=step_external_tau,
            step=step,
            controller_params=controller_params,
        )

        requested_torque_history[index] = step_result.controller_output.requested_torque
        applied_torque_history[index] = step_result.actuator_output.applied_torque
        saturation_history[index] = step_result.actuator_output.saturated

        state_history[index + 1] = step_result.next_state_vector
        integral_error_history[index + 1] = step_result.next_integral_error

    final_index = sample_count - 1

    final_reference = sample_quintic_trajectory(
        time=float(time_values[final_index]),
        waypoint_times=waypoint_time_array,
        waypoint_positions=waypoint_position_array,
    )

    reference_position_history[final_index] = final_reference.q_ref
    reference_velocity_history[final_index] = final_reference.q_dot_ref
    reference_acceleration_history[final_index] = final_reference.q_ddot_ref

    final_state = State(
        q=state_history[final_index, :2],
        q_dot=state_history[final_index, 2:],
    )

    if controller_params is None:
        final_controller_output = compute_independent_joint_pid(
            state=final_state,
            reference=final_reference,
            integral_error=integral_error_history[final_index],
            gains=gains,
        )
    else:
        final_controller_output = compute_pid_with_gravity_compensation(
            state=final_state,
            reference=final_reference,
            integral_error=integral_error_history[final_index],
            gains=gains,
            controller_params=controller_params,
        )

    final_actuator_output = saturate_joint_torque(
        requested_torque=(final_controller_output.requested_torque),
        torque_limit=torque_limit,
    )

    requested_torque_history[final_index] = final_controller_output.requested_torque
    applied_torque_history[final_index] = final_actuator_output.applied_torque
    saturation_history[final_index] = final_actuator_output.saturated

    return PIDSimulationResult(
        time_values=time_values,
        state_history=state_history,
        reference_position_history=(reference_position_history),
        reference_velocity_history=(reference_velocity_history),
        reference_acceleration_history=(reference_acceleration_history),
        integral_error_history=integral_error_history,
        requested_torque_history=requested_torque_history,
        applied_torque_history=applied_torque_history,
        saturation_history=saturation_history,
    )


@dataclass(frozen=True)
class ComputedTorqueSimulationResult:
    """Histories from a sampled Computed Torque trajectory simulation."""

    time_values: np.ndarray
    state_history: np.ndarray
    reference_position_history: np.ndarray
    reference_velocity_history: np.ndarray
    reference_acceleration_history: np.ndarray
    requested_torque_history: np.ndarray
    applied_torque_history: np.ndarray
    saturation_history: np.ndarray


def simulate_computed_torque_trajectory(
    waypoint_times: Sequence[float],
    waypoint_positions: Sequence[Sequence[float]],
    initial_state: Sequence[float],
    gains: ComputedTorqueGains,
    params: RobotParams,
    controller_params: RobotParams,
    torque_limit: float | Sequence[float],
    external_tau: ExternalTorque | None,
    step: float,
    external_tau_factory: ExternalTorqueFactory | None = None,
) -> ComputedTorqueSimulationResult:
    """Simulate CTC tracking with exactly one external-torque input mode.

    A factory receives each interval's time, step, and actual plant params.
    Pass external_tau=None when providing external_tau_factory.
    """
    if not np.isfinite(step) or step <= 0.0:
        raise ValueError("step must be a positive finite value.")

    if (external_tau is None) == (external_tau_factory is None):
        raise ValueError("Provide exactly one of external_tau or external_tau_factory.")

    if external_tau_factory is not None and not callable(external_tau_factory):
        raise ValueError("external_tau_factory must be callable.")

    waypoint_time_array = np.asarray(
        waypoint_times,
        dtype=float,
    )
    waypoint_position_array = np.asarray(
        waypoint_positions,
        dtype=float,
    )

    if waypoint_time_array.ndim != 1 or waypoint_time_array.size < 2:
        raise ValueError(
            "waypoint_times must be one-dimensional and contain at least two values."
        )

    if not np.all(np.isfinite(waypoint_time_array)):
        raise ValueError("waypoint_times must contain only finite values.")

    if np.any(np.diff(waypoint_time_array) <= 0.0):
        raise ValueError("waypoint_times must be strictly increasing.")

    if waypoint_position_array.shape != (
        waypoint_time_array.size,
        2,
    ):
        raise ValueError("waypoint_positions must have shape (number_of_waypoints, 2).")

    if not np.all(np.isfinite(waypoint_position_array)):
        raise ValueError("waypoint_positions must contain only finite values.")

    initial_state_array = np.asarray(
        initial_state,
        dtype=float,
    )

    if initial_state_array.shape != (4,):
        raise ValueError("initial_state must contain [q1, q2, q1_dot, q2_dot].")

    if not np.all(np.isfinite(initial_state_array)):
        raise ValueError("initial_state must contain only finite values.")

    start_time = float(waypoint_time_array[0])
    end_time = float(waypoint_time_array[-1])
    duration = end_time - start_time
    step_count = round(duration / step)

    if not np.isclose(
        step_count * step,
        duration,
        atol=1e-12,
        rtol=0.0,
    ):
        raise ValueError("The trajectory duration must be divisible by step.")

    sample_count = step_count + 1

    time_values = start_time + step * np.arange(
        sample_count,
        dtype=float,
    )

    state_history = np.empty(
        (
            sample_count,
            4,
        ),
        dtype=float,
    )
    reference_position_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    reference_velocity_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    reference_acceleration_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    requested_torque_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    applied_torque_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=float,
    )
    saturation_history = np.empty(
        (
            sample_count,
            2,
        ),
        dtype=bool,
    )

    state_history[0] = initial_state_array

    for index in range(step_count):
        reference = sample_quintic_trajectory(
            time=float(time_values[index]),
            waypoint_times=waypoint_time_array,
            waypoint_positions=waypoint_position_array,
        )

        reference_position_history[index] = reference.q_ref
        reference_velocity_history[index] = reference.q_dot_ref
        reference_acceleration_history[index] = reference.q_ddot_ref

        step_external_tau = external_tau

        if external_tau_factory is not None:
            step_external_tau = external_tau_factory(
                float(time_values[index]),
                step,
                params,
            )

        step_result = computed_torque_closed_loop_step(
            time=float(time_values[index]),
            state_vector=state_history[index],
            reference=reference,
            gains=gains,
            params=params,
            controller_params=controller_params,
            torque_limit=torque_limit,
            external_tau=step_external_tau,
            step=step,
        )

        requested_torque_history[index] = step_result.controller_output.requested_torque
        applied_torque_history[index] = step_result.actuator_output.applied_torque
        saturation_history[index] = step_result.actuator_output.saturated

        state_history[index + 1] = step_result.next_state_vector

    final_index = sample_count - 1

    final_reference = sample_quintic_trajectory(
        time=float(time_values[final_index]),
        waypoint_times=waypoint_time_array,
        waypoint_positions=waypoint_position_array,
    )

    reference_position_history[final_index] = final_reference.q_ref
    reference_velocity_history[final_index] = final_reference.q_dot_ref
    reference_acceleration_history[final_index] = final_reference.q_ddot_ref

    final_state = State(
        q=state_history[final_index, :2],
        q_dot=state_history[final_index, 2:],
    )

    final_controller_output = compute_computed_torque(
        state=final_state,
        reference=final_reference,
        gains=gains,
        controller_params=controller_params,
    )

    final_actuator_output = saturate_joint_torque(
        requested_torque=(final_controller_output.requested_torque),
        torque_limit=torque_limit,
    )

    requested_torque_history[final_index] = final_controller_output.requested_torque
    applied_torque_history[final_index] = final_actuator_output.applied_torque
    saturation_history[final_index] = final_actuator_output.saturated

    return ComputedTorqueSimulationResult(
        time_values=time_values,
        state_history=state_history,
        reference_position_history=reference_position_history,
        reference_velocity_history=reference_velocity_history,
        reference_acceleration_history=reference_acceleration_history,
        requested_torque_history=requested_torque_history,
        applied_torque_history=applied_torque_history,
        saturation_history=saturation_history,
    )
