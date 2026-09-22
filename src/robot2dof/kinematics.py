from collections.abc import Sequence
from math import acos, atan2, cos, hypot, sin

import numpy as np

from .parameters import RobotParams


def is_reachable(
    xy: Sequence[float],
    params: RobotParams,
) -> bool:
    """Return whether a Cartesian point lies in the arm's workspace."""

    x, y = xy
    radius = hypot(x, y)
    minimum_radius = abs(params.l1 - params.l2)
    maximum_radius = params.l1 + params.l2

    return minimum_radius <= radius <= maximum_radius


def inverse_kinematics(
    xy: Sequence[float],
    params: RobotParams,
    branch: str,
) -> tuple[float, float]:
    """Return joint angles for a reachable Cartesian target."""
    if branch not in {"elbow_up", "elbow_down"}:
        raise ValueError("branch must be 'elbow_up' or 'elbow_down'.")
    if not is_reachable(xy, params):
        raise ValueError("Target is outside the robot workspace.")

    x, y = xy
    cos_q2 = (x**2 + y**2 - params.l1**2 - params.l2**2) / (2.0 * params.l1 * params.l2)
    cos_q2 = max(-1.0, min(1.0, cos_q2))
    q2_magnitude = acos(cos_q2)
    q2 = -q2_magnitude if branch == "elbow_up" else q2_magnitude

    target_angle = atan2(y, x)
    offset_angle = atan2(
        params.l2 * sin(q2),
        params.l1 + params.l2 * cos(q2),
    )
    q1 = target_angle - offset_angle
    q1 = atan2(sin(q1), cos(q1))

    return q1, q2


def rotation_transform(angle: float) -> np.ndarray:
    """Return a 2D homogeneous rotation transform."""

    c = cos(angle)
    s = sin(angle)

    return np.array(
        [
            [c, -s, 0.0],
            [s, c, 0.0],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def translation_transform(dx: float, dy: float) -> np.ndarray:
    """Return a 2D homogeneous translation transform."""

    return np.array(
        [
            [1.0, 0.0, dx],
            [0.0, 1.0, dy],
            [0.0, 0.0, 1.0],
        ],
        dtype=float,
    )


def forward_kinematics_transform(
    q: Sequence[float],
    params: RobotParams,
) -> tuple[float, float]:
    """Return the end-effector position using homogeneous transforms."""

    q1, q2 = q

    transform = (
        rotation_transform(q1)
        @ translation_transform(params.l1, 0.0)
        @ rotation_transform(q2)
        @ translation_transform(params.l2, 0.0)
    )

    end_effector_origin = np.array([0.0, 0.0, 1.0])
    position = transform @ end_effector_origin

    return float(position[0]), float(position[1])


def forward_kinematics(
    q: Sequence[float],
    params: RobotParams,
) -> tuple[float, float]:
    """Return the end-effector position for joint angles in radians."""

    q1, q2 = q

    x = params.l1 * cos(q1) + params.l2 * cos(q1 + q2)
    y = params.l1 * sin(q1) + params.l2 * sin(q1 + q2)

    return x, y


def jacobian(
    q: Sequence[float],
    params: RobotParams,
) -> np.ndarray:
    """Return the end-effector linear-velocity Jacobian."""

    q1, q2 = q
    sin_q1 = sin(q1)
    cos_q1 = cos(q1)
    sin_q12 = sin(q1 + q2)
    cos_q12 = cos(q1 + q2)

    return np.array(
        [
            [
                -params.l1 * sin_q1 - params.l2 * sin_q12,
                -params.l2 * sin_q12,
            ],
            [
                params.l1 * cos_q1 + params.l2 * cos_q12,
                params.l2 * cos_q12,
            ],
        ],
        dtype=float,
    )


def end_effector_force_to_joint_torque(
    q: Sequence[float],
    force: Sequence[float],
    params: RobotParams,
) -> np.ndarray:
    """Map an end-effector force to joint torques."""

    force_vector = np.asarray(
        force,
        dtype=float,
    )

    return jacobian(q, params).T @ force_vector
