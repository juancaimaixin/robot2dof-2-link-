import numpy as np
import pytest
from scipy.integrate import solve_ivp

from robot2dof.controllers import (
    ComputedTorqueGains,
    PIDGains,
)
from robot2dof.dynamics import (
    coriolis_vector,
    gravity_vector,
    mass_matrix,
)
from robot2dof.parameters import RobotParams
from robot2dof.simulation import (
    computed_torque_closed_loop_step,
    integrate_fixed_steps,
    pid_closed_loop_step,
    rk4_step,
    simulate_computed_torque_trajectory,
    simulate_pid_trajectory,
    state_derivative,
)
from robot2dof.trajectory import Reference

PARAMS = RobotParams()


def exponential_derivative(
    _time: float,
    state_vector: np.ndarray,
) -> np.ndarray:
    return state_vector


def unactuated_robot_derivative(
    time: float,
    state_vector: np.ndarray,
) -> np.ndarray:
    return state_derivative(
        time,
        state_vector,
        tau=np.zeros(2),
        params=PARAMS,
        external_tau=np.zeros(2),
    )


def mechanical_energy(
    state_vector: np.ndarray,
) -> float:
    q = state_vector[:2]
    q_dot = state_vector[2:]

    kinetic_energy = 0.5 * float(q_dot @ mass_matrix(q, PARAMS) @ q_dot)

    q1, q2 = q

    potential_energy = PARAMS.g * (
        (PARAMS.m1 * PARAMS.lc1 + PARAMS.m2 * PARAMS.l1) * np.sin(q1)
        + PARAMS.m2 * PARAMS.lc2 * np.sin(q1 + q2)
    )

    return float(kinetic_energy + potential_energy)


def test_rk4_step_matches_known_exponential_update():
    initial_state = np.array([1.0])
    step = 0.1

    result = rk4_step(
        exponential_derivative,
        time=0.0,
        state_vector=initial_state,
        step=step,
    )

    expected = np.array([1.0 + step + step**2 / 2.0 + step**3 / 6.0 + step**4 / 24.0])

    assert result == pytest.approx(
        expected,
        abs=1e-12,
    )


def test_state_derivative_is_zero_under_gravity_balance():
    state_vector = np.zeros(4)

    balancing_torque = gravity_vector(
        state_vector[:2],
        PARAMS,
    )

    result = state_derivative(
        0.0,
        state_vector,
        balancing_torque,
        PARAMS,
        external_tau=np.zeros(2),
    )

    assert result == pytest.approx(
        np.zeros(4),
        abs=1e-12,
    )


def test_state_derivative_combines_velocity_and_acceleration():
    q = np.array(
        [
            0.30,
            -0.70,
        ]
    )
    q_dot = np.array(
        [
            0.40,
            -0.20,
        ]
    )
    expected_q_ddot = np.array(
        [
            1.20,
            -0.80,
        ]
    )
    external_tau = np.array(
        [
            0.50,
            -0.30,
        ]
    )

    state_vector = np.concatenate(
        (
            q,
            q_dot,
        )
    )

    applied_torque = (
        mass_matrix(q, PARAMS) @ expected_q_ddot
        + coriolis_vector(q, q_dot, PARAMS)
        + gravity_vector(q, PARAMS)
        - external_tau
    )

    result = state_derivative(
        0.0,
        state_vector,
        applied_torque,
        PARAMS,
        external_tau,
    )

    expected_result = np.concatenate(
        (
            q_dot,
            expected_q_ddot,
        )
    )

    assert result == pytest.approx(
        expected_result,
        abs=1e-12,
    )


def test_rk4_step_integrates_robot_state_with_constant_acceleration():
    initial_q = np.array(
        [
            0.30,
            -0.70,
        ]
    )
    initial_q_dot = np.array(
        [
            0.40,
            -0.20,
        ]
    )
    expected_q_ddot = np.array(
        [
            1.20,
            -0.80,
        ]
    )
    external_tau = np.array(
        [
            0.50,
            -0.30,
        ]
    )

    initial_state = np.concatenate(
        (
            initial_q,
            initial_q_dot,
        )
    )

    def constant_acceleration_derivative(
        time: float,
        state_vector: np.ndarray,
    ) -> np.ndarray:
        q = state_vector[:2]
        q_dot = state_vector[2:]

        applied_torque = (
            mass_matrix(q, PARAMS) @ expected_q_ddot
            + coriolis_vector(q, q_dot, PARAMS)
            + gravity_vector(q, PARAMS)
            - external_tau
        )

        return state_derivative(
            time,
            state_vector,
            applied_torque,
            PARAMS,
            external_tau,
        )

    step = 0.01

    result = rk4_step(
        constant_acceleration_derivative,
        time=0.0,
        state_vector=initial_state,
        step=step,
    )

    expected_q = initial_q + initial_q_dot * step + 0.5 * expected_q_ddot * step**2
    expected_q_dot = initial_q_dot + expected_q_ddot * step

    expected_result = np.concatenate(
        (
            expected_q,
            expected_q_dot,
        )
    )

    assert result == pytest.approx(
        expected_result,
        abs=1e-12,
    )


def test_integrate_fixed_steps_reaches_exponential_solution():
    time_values, state_history = integrate_fixed_steps(
        exponential_derivative,
        initial_state=np.array([1.0]),
        start_time=0.0,
        end_time=1.0,
        step=0.1,
    )

    expected_times = np.linspace(
        0.0,
        1.0,
        11,
    )

    assert time_values == pytest.approx(
        expected_times,
        abs=1e-12,
    )
    assert state_history.shape == (11, 1)
    assert state_history[0] == pytest.approx(
        np.array([1.0]),
        abs=1e-12,
    )
    assert state_history[-1] == pytest.approx(
        np.array([np.e]),
        abs=3e-6,
    )


def test_integrate_fixed_steps_preserves_gravity_equilibrium():
    initial_state = np.zeros(4)

    balancing_torque = gravity_vector(
        initial_state[:2],
        PARAMS,
    )

    def equilibrium_derivative(
        time: float,
        state_vector: np.ndarray,
    ) -> np.ndarray:
        return state_derivative(
            time,
            state_vector,
            balancing_torque,
            PARAMS,
            external_tau=np.zeros(2),
        )

    time_values, state_history = integrate_fixed_steps(
        equilibrium_derivative,
        initial_state=initial_state,
        start_time=0.0,
        end_time=0.1,
        step=0.001,
    )

    assert time_values[-1] == pytest.approx(
        0.1,
        abs=1e-12,
    )
    assert state_history.shape == (101, 4)
    assert state_history == pytest.approx(
        np.zeros((101, 4)),
        abs=1e-12,
    )


def test_robot_rk4_converges_when_step_is_halved():
    initial_state = np.array(
        [
            0.30,
            -0.70,
            0.40,
            -0.20,
        ]
    )

    step_values = (
        0.002,
        0.001,
        0.0005,
    )

    final_states = []

    for step in step_values:
        _, state_history = integrate_fixed_steps(
            unactuated_robot_derivative,
            initial_state=initial_state,
            start_time=0.0,
            end_time=0.5,
            step=step,
        )

        final_states.append(state_history[-1])

    coarse_to_medium_error = float(np.linalg.norm(final_states[0] - final_states[1]))
    medium_to_fine_error = float(np.linalg.norm(final_states[1] - final_states[2]))

    assert medium_to_fine_error < coarse_to_medium_error

    error_ratio = coarse_to_medium_error / medium_to_fine_error

    assert error_ratio > 10.0


def test_robot_rk4_matches_high_accuracy_solve_ivp():
    initial_state = np.array(
        [
            0.30,
            -0.70,
            0.40,
            -0.20,
        ]
    )

    start_time = 0.0
    end_time = 0.5
    step = 0.001

    time_values, rk4_history = integrate_fixed_steps(
        unactuated_robot_derivative,
        initial_state=initial_state,
        start_time=start_time,
        end_time=end_time,
        step=step,
    )

    reference_solution = solve_ivp(
        unactuated_robot_derivative,
        t_span=(
            start_time,
            end_time,
        ),
        y0=initial_state,
        method="DOP853",
        t_eval=time_values,
        rtol=1e-11,
        atol=1e-13,
    )

    assert reference_solution.success, reference_solution.message

    reference_history = reference_solution.y.T

    assert reference_history.shape == rk4_history.shape

    maximum_error = float(np.max(np.abs(rk4_history - reference_history)))

    assert maximum_error < 5e-8


def test_unactuated_robot_conserves_mechanical_energy():
    initial_state = np.array(
        [
            0.30,
            -0.70,
            0.40,
            -0.20,
        ]
    )

    _, state_history = integrate_fixed_steps(
        unactuated_robot_derivative,
        initial_state=initial_state,
        start_time=0.0,
        end_time=2.0,
        step=0.001,
    )

    energy_history = np.array(
        [mechanical_energy(state_vector) for state_vector in state_history]
    )

    energy_drift = np.abs(energy_history - energy_history[0])

    maximum_energy_drift = float(np.max(energy_drift))

    assert maximum_energy_drift < 1e-7


def test_pid_closed_loop_step_preserves_gravity_equilibrium():
    initial_state = np.zeros(4)
    balancing_torque = gravity_vector(
        initial_state[:2],
        PARAMS,
    )

    reference = Reference(
        q_ref=np.zeros(2),
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )

    gains = PIDGains(
        kp=np.zeros(2),
        ki=np.ones(2),
        kd=np.zeros(2),
    )

    result = pid_closed_loop_step(
        time=0.0,
        state_vector=initial_state,
        integral_error=balancing_torque,
        reference=reference,
        gains=gains,
        params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
    )

    assert result.controller_output.requested_torque == (
        pytest.approx(
            balancing_torque,
            abs=1e-12,
        )
    )
    assert result.actuator_output.applied_torque == (
        pytest.approx(
            balancing_torque,
            abs=1e-12,
        )
    )
    assert result.next_state_vector == pytest.approx(
        np.zeros(4),
        abs=1e-12,
    )
    assert result.next_integral_error == pytest.approx(
        balancing_torque,
        abs=1e-12,
    )


def test_pid_closed_loop_step_saturates_and_freezes_integral():
    reference = Reference(
        q_ref=np.array(
            [
                1.0,
                -1.0,
            ]
        ),
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )

    gains = PIDGains(
        kp=np.array(
            [
                100.0,
                100.0,
            ]
        ),
        ki=np.ones(2),
        kd=np.zeros(2),
    )

    result = pid_closed_loop_step(
        time=0.0,
        state_vector=np.zeros(4),
        integral_error=np.zeros(2),
        reference=reference,
        gains=gains,
        params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
    )

    assert result.controller_output.requested_torque == (
        pytest.approx(
            np.array(
                [
                    100.0,
                    -100.0,
                ]
            ),
            abs=1e-12,
        )
    )
    assert result.actuator_output.applied_torque == (
        pytest.approx(
            np.array(
                [
                    20.0,
                    -20.0,
                ]
            ),
            abs=1e-12,
        )
    )
    assert np.array_equal(
        result.actuator_output.saturated,
        np.array(
            [
                True,
                True,
            ]
        ),
    )
    assert result.next_integral_error == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )
    assert np.all(np.isfinite(result.next_state_vector))
    assert not np.allclose(
        result.next_state_vector,
        np.zeros(4),
    )


def test_pid_closed_loop_step_allows_integral_unwinding():
    reference = Reference(
        q_ref=np.array(
            [
                -1.0,
                1.0,
            ]
        ),
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )

    gains = PIDGains(
        kp=np.zeros(2),
        ki=np.ones(2),
        kd=np.zeros(2),
    )

    result = pid_closed_loop_step(
        time=0.0,
        state_vector=np.zeros(4),
        integral_error=np.array(
            [
                30.0,
                -30.0,
            ]
        ),
        reference=reference,
        gains=gains,
        params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.10,
    )

    assert result.controller_output.requested_torque == (
        pytest.approx(
            np.array(
                [
                    30.0,
                    -30.0,
                ]
            ),
            abs=1e-12,
        )
    )
    assert result.actuator_output.applied_torque == (
        pytest.approx(
            np.array(
                [
                    20.0,
                    -20.0,
                ]
            ),
            abs=1e-12,
        )
    )
    assert result.next_integral_error == pytest.approx(
        np.array(
            [
                29.90,
                -29.90,
            ]
        ),
        abs=1e-12,
    )


def test_simulate_pid_trajectory_preserves_gravity_equilibrium():
    initial_state = np.zeros(4)
    balancing_torque = gravity_vector(
        initial_state[:2],
        PARAMS,
    )

    gains = PIDGains(
        kp=np.zeros(2),
        ki=np.ones(2),
        kd=np.zeros(2),
    )

    result = simulate_pid_trajectory(
        waypoint_times=np.array(
            [
                0.0,
                0.003,
            ]
        ),
        waypoint_positions=np.zeros((2, 2)),
        initial_state=initial_state,
        initial_integral_error=balancing_torque,
        gains=gains,
        params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
    )

    assert result.time_values == pytest.approx(
        np.array(
            [
                0.0,
                0.001,
                0.002,
                0.003,
            ]
        ),
        abs=1e-12,
    )

    assert result.state_history.shape == (4, 4)
    assert result.reference_position_history.shape == (4, 2)
    assert result.reference_velocity_history.shape == (4, 2)
    assert result.reference_acceleration_history.shape == (4, 2)
    assert result.integral_error_history.shape == (4, 2)
    assert result.requested_torque_history.shape == (4, 2)
    assert result.applied_torque_history.shape == (4, 2)
    assert result.saturation_history.shape == (4, 2)

    assert result.state_history == pytest.approx(
        np.zeros((4, 4)),
        abs=1e-12,
    )
    assert result.reference_position_history == pytest.approx(
        np.zeros((4, 2)),
        abs=1e-12,
    )
    assert result.reference_velocity_history == pytest.approx(
        np.zeros((4, 2)),
        abs=1e-12,
    )
    assert result.reference_acceleration_history == pytest.approx(
        np.zeros((4, 2)),
        abs=1e-12,
    )

    expected_torque_history = np.tile(
        balancing_torque,
        (4, 1),
    )

    assert result.integral_error_history == pytest.approx(
        expected_torque_history,
        abs=1e-12,
    )
    assert result.requested_torque_history == pytest.approx(
        expected_torque_history,
        abs=1e-12,
    )
    assert result.applied_torque_history == pytest.approx(
        expected_torque_history,
        abs=1e-12,
    )
    assert not np.any(result.saturation_history)


def test_simulate_pid_trajectory_tracks_development_trajectory_stably():
    waypoint_times = np.array(
        [
            0.0,
            2.0,
            4.0,
            6.0,
            8.0,
        ]
    )

    waypoint_positions = np.radians(
        np.array(
            [
                [-20.0, 50.0],
                [35.0, 25.0],
                [65.0, -35.0],
                [10.0, 55.0],
                [-30.0, 20.0],
            ]
        )
    )

    integral_gain = np.array(
        [
            30.0,
            20.0,
        ]
    )

    gains = PIDGains(
        kp=np.array(
            [
                150.0,
                100.0,
            ]
        ),
        ki=integral_gain,
        kd=np.array(
            [
                25.0,
                15.0,
            ]
        ),
    )

    initial_state = np.concatenate(
        (
            waypoint_positions[0],
            np.zeros(2),
        )
    )

    initial_integral_error = (
        gravity_vector(
            waypoint_positions[0],
            PARAMS,
        )
        / integral_gain
    )

    result = simulate_pid_trajectory(
        waypoint_times=waypoint_times,
        waypoint_positions=waypoint_positions,
        initial_state=initial_state,
        initial_integral_error=initial_integral_error,
        gains=gains,
        params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.002,
    )

    numeric_histories = (
        result.state_history,
        result.reference_position_history,
        result.reference_velocity_history,
        result.reference_acceleration_history,
        result.integral_error_history,
        result.requested_torque_history,
        result.applied_torque_history,
    )

    for history in numeric_histories:
        assert np.all(np.isfinite(history))

    position_error_history = (
        result.reference_position_history - result.state_history[:, :2]
    )

    maximum_position_error = float(np.max(np.abs(position_error_history)))
    final_position_error = float(np.max(np.abs(position_error_history[-1])))

    assert maximum_position_error < np.radians(2.5)
    assert final_position_error < np.radians(0.75)
    assert not np.any(result.saturation_history)
    assert result.applied_torque_history == pytest.approx(
        result.requested_torque_history,
        abs=1e-12,
    )


def test_pid_closed_loop_step_with_gravity_compensation_preserves_equilibrium():
    initial_q = np.array(
        [
            0.30,
            -0.40,
        ]
    )

    initial_state = np.concatenate(
        (
            initial_q,
            np.zeros(2),
        )
    )

    reference = Reference(
        q_ref=initial_q,
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )

    gains = PIDGains(
        kp=np.zeros(2),
        ki=np.zeros(2),
        kd=np.zeros(2),
    )

    expected_gravity_torque = gravity_vector(
        initial_q,
        PARAMS,
    )

    result = pid_closed_loop_step(
        time=0.0,
        state_vector=initial_state,
        integral_error=np.zeros(2),
        reference=reference,
        gains=gains,
        params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
        controller_params=PARAMS,
    )

    assert result.controller_output.requested_torque == pytest.approx(
        expected_gravity_torque,
        abs=1e-12,
    )
    assert result.actuator_output.applied_torque == pytest.approx(
        expected_gravity_torque,
        abs=1e-12,
    )
    assert result.next_state_vector == pytest.approx(
        initial_state,
        abs=1e-12,
    )
    assert result.next_integral_error == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )
    assert not np.any(result.actuator_output.saturated)


def test_simulate_pid_trajectory_with_gravity_compensation_preserves_equilibrium():
    initial_q = np.array(
        [
            0.30,
            -0.40,
        ]
    )

    initial_state = np.concatenate(
        (
            initial_q,
            np.zeros(2),
        )
    )

    gains = PIDGains(
        kp=np.zeros(2),
        ki=np.zeros(2),
        kd=np.zeros(2),
    )

    result = simulate_pid_trajectory(
        waypoint_times=np.array(
            [
                0.0,
                0.003,
            ]
        ),
        waypoint_positions=np.tile(
            initial_q,
            (2, 1),
        ),
        initial_state=initial_state,
        initial_integral_error=np.zeros(2),
        gains=gains,
        params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
        controller_params=PARAMS,
    )

    expected_state_history = np.tile(
        initial_state,
        (4, 1),
    )
    expected_torque_history = np.tile(
        gravity_vector(
            initial_q,
            PARAMS,
        ),
        (4, 1),
    )

    assert result.state_history == pytest.approx(
        expected_state_history,
        abs=1e-12,
    )
    assert result.integral_error_history == pytest.approx(
        np.zeros((4, 2)),
        abs=1e-12,
    )
    assert result.requested_torque_history == pytest.approx(
        expected_torque_history,
        abs=1e-12,
    )
    assert result.applied_torque_history == pytest.approx(
        expected_torque_history,
        abs=1e-12,
    )
    assert not np.any(result.saturation_history)


def test_computed_torque_closed_loop_step_preserves_equilibrium():
    initial_q = np.array([0.30, -0.40])
    initial_state = np.concatenate((initial_q, np.zeros(2)))

    reference = Reference(
        q_ref=initial_q,
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )

    gains = ComputedTorqueGains(
        kp=np.array([12.0, 8.0]),
        kd=np.array([5.0, 4.0]),
    )

    result = computed_torque_closed_loop_step(
        time=0.0,
        state_vector=initial_state,
        reference=reference,
        gains=gains,
        params=PARAMS,
        controller_params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
    )

    expected_torque = gravity_vector(initial_q, PARAMS)

    assert result.controller_output.requested_torque == pytest.approx(
        expected_torque,
        abs=1e-12,
    )
    assert result.actuator_output.applied_torque == pytest.approx(
        expected_torque,
        abs=1e-12,
    )
    assert result.next_state_vector == pytest.approx(
        initial_state,
        abs=1e-12,
    )
    assert not np.any(result.actuator_output.saturated)

def test_simulate_computed_torque_trajectory_preserves_equilibrium():
    initial_q = np.array([0.30, -0.40])
    initial_state = np.concatenate((initial_q, np.zeros(2)))

    gains = ComputedTorqueGains(
        kp=np.array([12.0, 8.0]),
        kd=np.array([5.0, 4.0]),
    )

    result = simulate_computed_torque_trajectory(
        waypoint_times=np.array([0.0, 0.003]),
        waypoint_positions=np.tile(initial_q, (2, 1)),
        initial_state=initial_state,
        gains=gains,
        params=PARAMS,
        controller_params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.001,
    )

    expected_state_history = np.tile(initial_state, (4, 1))
    expected_position_history = np.tile(initial_q, (4, 1))
    expected_torque_history = np.tile(
        gravity_vector(initial_q, PARAMS),
        (4, 1),
    )

    assert result.time_values == pytest.approx(
        np.array([0.0, 0.001, 0.002, 0.003]),
        abs=1e-12,
    )
    assert result.state_history == pytest.approx(
        expected_state_history,
        abs=1e-12,
    )
    assert result.reference_position_history == pytest.approx(
        expected_position_history,
        abs=1e-12,
    )
    assert result.reference_velocity_history == pytest.approx(
        np.zeros((4, 2)),
        abs=1e-12,
    )
    assert result.reference_acceleration_history == pytest.approx(
        np.zeros((4, 2)),
        abs=1e-12,
    )
    assert result.requested_torque_history == pytest.approx(
        expected_torque_history,
        abs=1e-12,
    )
    assert result.applied_torque_history == pytest.approx(
        expected_torque_history,
        abs=1e-12,
    )
    assert not np.any(result.saturation_history)


def test_simulate_computed_torque_trajectory_tracks_development_trajectory_stably():
    waypoint_times = np.array([0.0, 4.0])

    waypoint_positions = np.radians(
        np.array(
            [
                [-20.0, 40.0],
                [40.0, -20.0],
            ]
        )
    )

    gains = ComputedTorqueGains(
        kp=np.full(2, 64.0),
        kd=np.full(2, 16.0),
    )

    initial_state = np.concatenate(
        (
            waypoint_positions[0],
            np.zeros(2),
        )
    )

    result = simulate_computed_torque_trajectory(
        waypoint_times=waypoint_times,
        waypoint_positions=waypoint_positions,
        initial_state=initial_state,
        gains=gains,
        params=PARAMS,
        controller_params=PARAMS,
        torque_limit=20.0,
        external_tau=np.zeros(2),
        step=0.002,
    )

    numeric_histories = (
        result.state_history,
        result.reference_position_history,
        result.reference_velocity_history,
        result.reference_acceleration_history,
        result.requested_torque_history,
        result.applied_torque_history,
    )

    for history in numeric_histories:
        assert np.all(np.isfinite(history))

    position_error_history = (
        result.reference_position_history - result.state_history[:, :2]
    )

    maximum_position_error = float(np.max(np.abs(position_error_history)))
    final_position_error = float(np.max(np.abs(position_error_history[-1])))

    assert maximum_position_error < np.radians(0.1)
    assert final_position_error < np.radians(0.01)
    assert not np.any(result.saturation_history)
    assert result.applied_torque_history == pytest.approx(
        result.requested_torque_history,
        abs=1e-12,
    )
