import numpy as np
import pytest

from robot2dof.dynamics import (
    coriolis_vector,
    forward_dynamics,
    gravity_vector,
    mass_matrix,
)
from robot2dof.parameters import RobotParams
from robot2dof.state import State

PARAMS = RobotParams()


def potential_energy(
    q: np.ndarray,
    params: RobotParams,
) -> float:
    q1, q2 = q

    return float(
        params.g
        * (
            (params.m1 * params.lc1 + params.m2 * params.l1) * np.sin(q1)
            + params.m2 * params.lc2 * np.sin(q1 + q2)
        )
    )


def numerical_potential_gradient(
    q: np.ndarray,
    params: RobotParams,
    step: float = 1e-6,
) -> np.ndarray:
    result = np.empty(2, dtype=float)

    for joint_index in range(2):
        perturbation = np.zeros(2, dtype=float)
        perturbation[joint_index] = step

        result[joint_index] = (
            potential_energy(q + perturbation, params)
            - potential_energy(q - perturbation, params)
        ) / (2.0 * step)

    return result


def test_mass_matrix_at_zero_angles():
    result = mass_matrix(
        (0.0, 0.0),
        PARAMS,
    )

    expected = np.array(
        [
            [0.9216666666666666, 0.23],
            [0.23, 0.08],
        ]
    )

    assert result == pytest.approx(
        expected,
        abs=1e-12,
    )


def test_mass_matrix_is_symmetric_positive_definite():
    rng = np.random.default_rng(20260828)
    joint_angles = rng.uniform(
        -np.pi,
        np.pi,
        size=(1000, 2),
    )

    minimum_eigenvalue = np.inf

    for q in joint_angles:
        result = mass_matrix(
            q,
            PARAMS,
        )

        assert np.allclose(
            result,
            result.T,
            atol=1e-12,
            rtol=0.0,
        )

        eigenvalues = np.linalg.eigvalsh(result)
        minimum_eigenvalue = min(
            minimum_eigenvalue,
            float(eigenvalues[0]),
        )

    assert minimum_eigenvalue > 0.0


def test_coriolis_vector_for_known_state():
    result = coriolis_vector(
        (0.0, np.pi / 2.0),
        (1.0, 2.0),
        PARAMS,
    )

    expected = np.array(
        [
            -1.20,
            0.15,
        ]
    )

    assert result == pytest.approx(
        expected,
        abs=1e-12,
    )


def test_gravity_vector_at_horizontal_pose():
    result = gravity_vector(
        (0.0, 0.0),
        PARAMS,
    )

    expected = np.array(
        [
            15.2055,
            2.943,
        ]
    )

    assert result == pytest.approx(
        expected,
        abs=1e-12,
    )


def test_gravity_vector_matches_potential_gradient():
    rng = np.random.default_rng(20260828)
    joint_angles = rng.uniform(
        -np.pi,
        np.pi,
        size=(100, 2),
    )

    for q in joint_angles:
        analytic_result = gravity_vector(
            q,
            PARAMS,
        )
        numerical_result = numerical_potential_gradient(
            q,
            PARAMS,
        )

        assert analytic_result == pytest.approx(
            numerical_result,
            abs=1e-6,
        )


def test_forward_dynamics_gravity_balance():
    q = np.array(
        [
            0.0,
            0.0,
        ]
    )

    state = State(
        q=q,
        q_dot=np.zeros(2),
    )

    balancing_torque = gravity_vector(
        q,
        PARAMS,
    )

    acceleration = forward_dynamics(
        state,
        balancing_torque,
        PARAMS,
        external_tau=np.zeros(2),
    )

    assert acceleration == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )


def test_forward_dynamics_recovers_known_acceleration():
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
    expected_acceleration = np.array(
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

    state = State(
        q=q,
        q_dot=q_dot,
    )

    applied_torque = (
        mass_matrix(q, PARAMS) @ expected_acceleration
        + coriolis_vector(q, q_dot, PARAMS)
        + gravity_vector(q, PARAMS)
        - external_tau
    )

    result = forward_dynamics(
        state,
        applied_torque,
        PARAMS,
        external_tau,
    )

    assert result == pytest.approx(
        expected_acceleration,
        abs=1e-12,
    )
