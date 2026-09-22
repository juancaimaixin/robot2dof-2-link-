from math import pi

import numpy as np
import pytest

from robot2dof.kinematics import (
    end_effector_force_to_joint_torque,
    forward_kinematics,
    forward_kinematics_transform,
    inverse_kinematics,
    is_reachable,
    jacobian,
    rotation_transform,
)
from robot2dof.parameters import RobotParams

PARAMS = RobotParams()


def numerical_jacobian(
    q: np.ndarray,
    step: float = 1e-6,
) -> np.ndarray:
    result = np.empty((2, 2), dtype=float)

    for joint_index in range(2):
        perturbation = np.zeros(2, dtype=float)
        perturbation[joint_index] = step

        forward_position = np.array(
            forward_kinematics(
                q + perturbation,
                PARAMS,
            )
        )
        backward_position = np.array(
            forward_kinematics(
                q - perturbation,
                PARAMS,
            )
        )

        result[:, joint_index] = (forward_position - backward_position) / (2.0 * step)

    return result


def test_reachability_accepts_point_inside_workspace():
    assert is_reachable((0.60, 0.0), PARAMS)


def test_reachability_rejects_point_beyond_maximum_radius():
    assert not is_reachable((1.00, 0.0), PARAMS)


def test_reachability_rejects_point_inside_minimum_radius():
    assert not is_reachable((0.0, 0.0), PARAMS)


def test_reachability_accepts_maximum_radius_boundary():
    position = (PARAMS.l1 + PARAMS.l2, 0.0)

    assert is_reachable(position, PARAMS)


def test_inverse_kinematics_elbow_down_known_target():
    joint_angles = inverse_kinematics(
        (0.50, 0.40),
        PARAMS,
        "elbow_down",
    )

    assert joint_angles == pytest.approx((0.0, pi / 2), abs=1e-12)


def test_inverse_kinematics_elbow_up_known_target():
    joint_angles = inverse_kinematics(
        (0.50, -0.40),
        PARAMS,
        "elbow_up",
    )

    assert joint_angles == pytest.approx((0.0, -pi / 2), abs=1e-12)


def test_inverse_kinematics_rejects_unreachable_target():
    with pytest.raises(ValueError, match="outside the robot workspace"):
        inverse_kinematics(
            (1.00, 0.0),
            PARAMS,
            "elbow_down",
        )


def test_inverse_kinematics_rejects_unknown_branch():
    with pytest.raises(ValueError, match="elbow_up.*elbow_down"):
        inverse_kinematics(
            (0.50, 0.40),
            PARAMS,
            "up",
        )


def test_inverse_kinematics_round_trip_for_random_targets():
    rng = np.random.default_rng(20260821)
    original_joint_angles = rng.uniform(-pi, pi, size=(100, 2))

    for original_q in original_joint_angles:
        target_position = forward_kinematics(original_q, PARAMS)

        for branch in ("elbow_up", "elbow_down"):
            recovered_q = inverse_kinematics(
                target_position,
                PARAMS,
                branch,
            )
            recovered_q1, recovered_q2 = recovered_q

            assert -pi <= recovered_q1 <= pi
            assert -pi <= recovered_q2 <= pi

            recovered_position = forward_kinematics(recovered_q, PARAMS)

            assert recovered_position == pytest.approx(
                target_position,
                abs=1e-9,
            )


def test_rotation_transform_quarter_turn():
    transform = rotation_transform(pi / 2)
    point = np.array([1.0, 0.0, 1.0])

    rotated_point = transform @ point

    assert rotated_point == pytest.approx((0.0, 1.0, 1.0), abs=1e-12)


def test_forward_kinematics_zero_angles():
    position = forward_kinematics((0.0, 0.0), PARAMS)

    assert position == pytest.approx((0.90, 0.0), abs=1e-12)


def test_forward_kinematics_right_angle():
    position = forward_kinematics((0.0, pi / 2), PARAMS)

    assert position == pytest.approx((0.50, 0.40), abs=1e-12)


def test_forward_kinematics_folded_pose():
    position = forward_kinematics((0.0, pi), PARAMS)

    assert position == pytest.approx((0.10, 0.0), abs=1e-12)


def test_transform_fk_matches_analytic_fk_for_random_angles():
    rng = np.random.default_rng(20260820)
    joint_angles = rng.uniform(-pi, pi, size=(100, 2))

    for q in joint_angles:
        analytic_position = forward_kinematics(q, PARAMS)
        transform_position = forward_kinematics_transform(q, PARAMS)

        assert transform_position == pytest.approx(
            analytic_position,
            abs=1e-12,
        )


def test_jacobian_at_zero_angles():
    result = jacobian((0.0, 0.0), PARAMS)

    expected = np.array(
        [
            [0.0, 0.0],
            [0.90, 0.40],
        ]
    )

    assert result == pytest.approx(
        expected,
        abs=1e-12,
    )


def test_analytic_jacobian_matches_central_difference():
    rng = np.random.default_rng(20260822)
    joint_angles = rng.uniform(
        -pi,
        pi,
        size=(100, 2),
    )
    maximum_error = 0.0

    for q in joint_angles:
        analytic_result = jacobian(q, PARAMS)
        numerical_result = numerical_jacobian(q)

        error = float(np.max(np.abs(analytic_result - numerical_result)))
        maximum_error = max(maximum_error, error)

    assert maximum_error < 1e-6


def test_jacobian_determinant_matches_analytic_formula():
    q1 = 0.37

    for q2 in (
        0.0,
        pi / 2.0,
        -pi / 2.0,
        pi,
    ):
        result = jacobian(
            (q1, q2),
            PARAMS,
        )
        numerical_determinant = float(np.linalg.det(result))
        expected_determinant = PARAMS.l1 * PARAMS.l2 * np.sin(q2)

        assert numerical_determinant == pytest.approx(
            expected_determinant,
            abs=1e-12,
        )


def test_end_effector_force_maps_to_joint_torques():
    joint_torques = end_effector_force_to_joint_torque(
        (0.0, 0.0),
        (0.0, -10.0),
        PARAMS,
    )

    assert joint_torques == pytest.approx(
        (-9.0, -4.0),
        abs=1e-12,
    )
