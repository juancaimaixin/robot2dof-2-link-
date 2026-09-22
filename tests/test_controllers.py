import numpy as np
import pytest

from robot2dof.actuation import (
    ActuatorOutput,
    saturate_joint_torque,
)
from robot2dof.controllers import (
    ComputedTorqueGains,
    PIDGains,
    compute_computed_torque,
    compute_independent_joint_pid,
    compute_pid_with_gravity_compensation,
    update_integral_error_conditionally,
)
from robot2dof.dynamics import (
    forward_dynamics,
    gravity_vector,
)
from robot2dof.parameters import RobotParams
from robot2dof.state import State
from robot2dof.trajectory import Reference


def test_independent_joint_pid_matches_known_answer():
    state = State(
        q=np.array(
            [
                0.20,
                -0.40,
            ]
        ),
        q_dot=np.array(
            [
                0.10,
                -0.20,
            ]
        ),
    )

    reference = Reference(
        q_ref=np.array(
            [
                0.50,
                -0.10,
            ]
        ),
        q_dot_ref=np.array(
            [
                -0.30,
                0.40,
            ]
        ),
        q_ddot_ref=np.zeros(2),
    )

    integral_error = np.array(
        [
            0.20,
            -0.10,
        ]
    )

    gains = PIDGains(
        kp=np.array(
            [
                10.0,
                20.0,
            ]
        ),
        ki=np.array(
            [
                3.0,
                4.0,
            ]
        ),
        kd=np.array(
            [
                2.0,
                5.0,
            ]
        ),
    )

    output = compute_independent_joint_pid(
        state=state,
        reference=reference,
        integral_error=integral_error,
        gains=gains,
    )

    expected_position_error = np.array(
        [
            0.30,
            0.30,
        ]
    )
    expected_velocity_error = np.array(
        [
            -0.40,
            0.60,
        ]
    )

    expected_requested_torque = np.array(
        [
            2.80,
            8.60,
        ]
    )

    assert output.position_error == pytest.approx(
        expected_position_error,
        abs=1e-12,
    )
    assert output.velocity_error == pytest.approx(
        expected_velocity_error,
        abs=1e-12,
    )
    assert output.integral_error == pytest.approx(
        integral_error,
        abs=1e-12,
    )
    assert output.requested_torque == pytest.approx(
        expected_requested_torque,
        abs=1e-12,
    )


def test_independent_joint_pid_returns_zero_for_zero_error():
    state = State(
        q=np.array(
            [
                0.30,
                -0.70,
            ]
        ),
        q_dot=np.array(
            [
                0.20,
                -0.10,
            ]
        ),
    )

    reference = Reference(
        q_ref=state.q,
        q_dot_ref=state.q_dot,
        q_ddot_ref=np.array(
            [
                1.0,
                -2.0,
            ]
        ),
    )

    gains = PIDGains(
        kp=np.array(
            [
                10.0,
                20.0,
            ]
        ),
        ki=np.array(
            [
                3.0,
                4.0,
            ]
        ),
        kd=np.array(
            [
                2.0,
                5.0,
            ]
        ),
    )

    output = compute_independent_joint_pid(
        state=state,
        reference=reference,
        integral_error=np.zeros(2),
        gains=gains,
    )

    assert output.requested_torque == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )


def test_independent_joint_pid_rejects_negative_gain():
    state = State(
        q=np.zeros(2),
        q_dot=np.zeros(2),
    )
    reference = Reference(
        q_ref=np.zeros(2),
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )
    gains = PIDGains(
        kp=np.array(
            [
                10.0,
                -1.0,
            ]
        ),
        ki=np.zeros(2),
        kd=np.zeros(2),
    )

    with pytest.raises(
        ValueError,
        match="non-negative",
    ):
        compute_independent_joint_pid(
            state=state,
            reference=reference,
            integral_error=np.zeros(2),
            gains=gains,
        )


def test_independent_joint_pid_rejects_invalid_joint_shape():
    state = State(
        q=np.array([0.0]),
        q_dot=np.zeros(2),
    )
    reference = Reference(
        q_ref=np.zeros(2),
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )
    gains = PIDGains(
        kp=np.ones(2),
        ki=np.zeros(2),
        kd=np.zeros(2),
    )

    with pytest.raises(
        ValueError,
        match="state.q",
    ):
        compute_independent_joint_pid(
            state=state,
            reference=reference,
            integral_error=np.zeros(2),
            gains=gains,
        )


def test_independent_joint_pid_rejects_non_finite_input():
    state = State(
        q=np.zeros(2),
        q_dot=np.zeros(2),
    )
    reference = Reference(
        q_ref=np.zeros(2),
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )
    gains = PIDGains(
        kp=np.ones(2),
        ki=np.ones(2),
        kd=np.ones(2),
    )

    with pytest.raises(
        ValueError,
        match="integral_error",
    ):
        compute_independent_joint_pid(
            state=state,
            reference=reference,
            integral_error=np.array(
                [
                    0.0,
                    np.inf,
                ]
            ),
            gains=gains,
        )


def test_conditional_integration_updates_when_not_saturated():
    actuator_output = saturate_joint_torque(
        requested_torque=np.array(
            [
                5.0,
                -6.0,
            ]
        ),
        torque_limit=20.0,
    )

    updated_integral_error = update_integral_error_conditionally(
        integral_error=np.array(
            [
                0.10,
                -0.20,
            ]
        ),
        position_error=np.array(
            [
                2.0,
                -3.0,
            ]
        ),
        actuator_output=actuator_output,
        step=0.10,
    )

    assert updated_integral_error == pytest.approx(
        np.array(
            [
                0.30,
                -0.50,
            ]
        ),
        abs=1e-12,
    )


def test_conditional_integration_freezes_when_error_pushes_outward():
    actuator_output = saturate_joint_torque(
        requested_torque=np.array(
            [
                20.0,
                -20.0,
            ]
        ),
        torque_limit=20.0,
    )

    initial_integral_error = np.array(
        [
            0.10,
            -0.20,
        ]
    )

    updated_integral_error = update_integral_error_conditionally(
        integral_error=initial_integral_error,
        position_error=np.array(
            [
                2.0,
                -3.0,
            ]
        ),
        actuator_output=actuator_output,
        step=0.10,
    )

    assert updated_integral_error == pytest.approx(
        initial_integral_error,
        abs=1e-12,
    )


def test_conditional_integration_allows_unwinding():
    actuator_output = saturate_joint_torque(
        requested_torque=np.array(
            [
                20.0,
                -20.0,
            ]
        ),
        torque_limit=20.0,
    )

    updated_integral_error = update_integral_error_conditionally(
        integral_error=np.array(
            [
                0.10,
                -0.20,
            ]
        ),
        position_error=np.array(
            [
                -2.0,
                3.0,
            ]
        ),
        actuator_output=actuator_output,
        step=0.10,
    )

    assert updated_integral_error == pytest.approx(
        np.array(
            [
                -0.10,
                0.10,
            ]
        ),
        abs=1e-12,
    )


def test_conditional_integration_handles_joints_independently():
    actuator_output = saturate_joint_torque(
        requested_torque=np.array(
            [
                25.0,
                5.0,
            ]
        ),
        torque_limit=20.0,
    )

    updated_integral_error = update_integral_error_conditionally(
        integral_error=np.zeros(2),
        position_error=np.array(
            [
                2.0,
                -3.0,
            ]
        ),
        actuator_output=actuator_output,
        step=0.10,
    )

    assert updated_integral_error == pytest.approx(
        np.array(
            [
                0.0,
                -0.30,
            ]
        ),
        abs=1e-12,
    )


@pytest.mark.parametrize(
    "step",
    [
        0.0,
        -0.01,
        np.inf,
        np.nan,
    ],
)
def test_conditional_integration_rejects_invalid_step(step):
    actuator_output = saturate_joint_torque(
        requested_torque=np.zeros(2),
        torque_limit=20.0,
    )

    with pytest.raises(
        ValueError,
        match="positive finite",
    ):
        update_integral_error_conditionally(
            integral_error=np.zeros(2),
            position_error=np.zeros(2),
            actuator_output=actuator_output,
            step=step,
        )


def test_conditional_integration_rejects_invalid_saturation_shape():
    actuator_output = ActuatorOutput(
        requested_torque=np.zeros(2),
        applied_torque=np.zeros(2),
        saturated=np.array([False]),
    )

    with pytest.raises(
        ValueError,
        match="saturated",
    ):
        update_integral_error_conditionally(
            integral_error=np.zeros(2),
            position_error=np.zeros(2),
            actuator_output=actuator_output,
            step=0.01,
        )


def test_pid_with_gravity_compensation_balances_static_gravity():
    params = RobotParams()

    q = np.array(
        [
            0.30,
            -0.40,
        ]
    )

    state = State(
        q=q,
        q_dot=np.zeros(2),
    )

    reference = Reference(
        q_ref=q,
        q_dot_ref=np.zeros(2),
        q_ddot_ref=np.zeros(2),
    )

    gains = PIDGains(
        kp=np.array(
            [
                100.0,
                80.0,
            ]
        ),
        ki=np.array(
            [
                20.0,
                10.0,
            ]
        ),
        kd=np.array(
            [
                15.0,
                10.0,
            ]
        ),
    )

    result = compute_pid_with_gravity_compensation(
        state=state,
        reference=reference,
        integral_error=np.zeros(2),
        gains=gains,
        controller_params=params,
    )

    expected_gravity_torque = gravity_vector(
        q,
        params,
    )

    assert result.requested_torque == pytest.approx(
        expected_gravity_torque,
        abs=1e-12,
    )
    assert result.position_error == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )
    assert result.velocity_error == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )


def test_computed_torque_recovers_commanded_error_acceleration():
    params = RobotParams()

    state = State(
        q=np.array(
            [
                0.30,
                -0.40,
            ]
        ),
        q_dot=np.array(
            [
                0.20,
                -0.10,
            ]
        ),
    )

    reference = Reference(
        q_ref=np.array(
            [
                0.50,
                -0.20,
            ]
        ),
        q_dot_ref=np.array(
            [
                -0.10,
                0.30,
            ]
        ),
        q_ddot_ref=np.array(
            [
                0.40,
                -0.60,
            ]
        ),
    )

    gains = ComputedTorqueGains(
        kp=np.array(
            [
                12.0,
                8.0,
            ]
        ),
        kd=np.array(
            [
                5.0,
                4.0,
            ]
        ),
    )

    result = compute_computed_torque(
        state=state,
        reference=reference,
        gains=gains,
        controller_params=params,
    )

    expected_acceleration = (
        reference.q_ddot_ref
        + np.asarray(gains.kd) * (reference.q_dot_ref - state.q_dot)
        + np.asarray(gains.kp) * (reference.q_ref - state.q)
    )

    actual_acceleration = forward_dynamics(
        state=state,
        tau=result.requested_torque,
        params=params,
        external_tau=np.zeros(2),
    )

    assert actual_acceleration == pytest.approx(
        expected_acceleration,
        abs=1e-12,
    )
    assert result.position_error == pytest.approx(
        reference.q_ref - state.q,
        abs=1e-12,
    )
    assert result.velocity_error == pytest.approx(
        reference.q_dot_ref - state.q_dot,
        abs=1e-12,
    )
    assert result.integral_error == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )
    