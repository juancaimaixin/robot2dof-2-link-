from collections.abc import Sequence
from math import cos, sin

import numpy as np

from .parameters import RobotParams
from .state import State


def mass_matrix(
    q: Sequence[float],
    params: RobotParams,
) -> np.ndarray:
    """Return the joint-space mass matrix including the payload."""

    _, q2 = q

    m11 = (
        params.I1
        + params.I2
        + params.m1 * params.lc1**2
        + params.m2
        * (params.l1**2 + params.lc2**2 + 2.0 * params.l1 * params.lc2 * cos(q2))
    )

    m12 = params.I2 + params.m2 * (params.lc2**2 + params.l1 * params.lc2 * cos(q2))

    m22 = params.I2 + params.m2 * params.lc2**2

    # Add the inertia of the point mass at the end effector.
    m11 += params.payload_mass * (
        params.l1**2 + params.l2**2 + 2.0 * params.l1 * params.l2 * cos(q2)
    )

    m12 += params.payload_mass * (params.l2**2 + params.l1 * params.l2 * cos(q2))

    m22 += params.payload_mass * params.l2**2

    return np.array(
        [
            [m11, m12],
            [m12, m22],
        ],
        dtype=float,
    )


def coriolis_vector(
    q: Sequence[float],
    q_dot: Sequence[float],
    params: RobotParams,
) -> np.ndarray:
    """Return the Coriolis and centrifugal vector including the payload."""

    _, q2 = q
    q1_dot, q2_dot = q_dot

    h = params.m2 * params.l1 * params.lc2 * sin(q2)

    # Add the contribution of the end-effector point mass.
    h += params.payload_mass * params.l1 * params.l2 * sin(q2)

    return np.array(
        [
            -h * (2.0 * q1_dot * q2_dot + q2_dot**2),
            h * q1_dot**2,
        ],
        dtype=float,
    )


def gravity_vector(
    q: Sequence[float],
    params: RobotParams,
) -> np.ndarray:
    """Return the gravity torque vector including the payload."""

    q1, q2 = q
    q12 = q1 + q2

    g1 = params.g * (
        (params.m1 * params.lc1 + params.m2 * params.l1) * cos(q1)
        + params.m2 * params.lc2 * cos(q12)
    )

    g2 = params.g * params.m2 * params.lc2 * cos(q12)

    # Add the gravity contribution of the end-effector point mass.
    g1 += params.payload_mass * params.g * (params.l1 * cos(q1) + params.l2 * cos(q12))

    g2 += params.payload_mass * params.g * params.l2 * cos(q12)

    return np.array(
        [
            g1,
            g2,
        ],
        dtype=float,
    )


def forward_dynamics(
    state: State,
    tau: Sequence[float],
    params: RobotParams,
    external_tau: Sequence[float],
) -> np.ndarray:
    """Return joint acceleration from applied torques."""

    net_torque = (
        np.asarray(tau, dtype=float)
        + np.asarray(external_tau, dtype=float)
        - coriolis_vector(
            state.q,
            state.q_dot,
            params,
        )
        - gravity_vector(
            state.q,
            params,
        )
    )

    return np.linalg.solve(
        mass_matrix(state.q, params),
        net_torque,
    )
