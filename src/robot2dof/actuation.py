from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ActuatorOutput:
    """Requested torque, applied torque, and saturation status."""

    requested_torque: np.ndarray
    applied_torque: np.ndarray
    saturated: np.ndarray


def saturate_joint_torque(
    requested_torque: Sequence[float],
    torque_limit: float | Sequence[float],
) -> ActuatorOutput:
    """Apply symmetric per-joint torque limits."""

    requested_array = np.asarray(
        requested_torque,
        dtype=float,
    )

    if requested_array.shape != (2,):
        raise ValueError("requested_torque must contain exactly two values.")

    if not np.all(np.isfinite(requested_array)):
        raise ValueError("requested_torque must contain only finite values.")

    limit_array = np.asarray(
        torque_limit,
        dtype=float,
    )

    if limit_array.ndim == 0:
        limit_array = np.full(
            2,
            float(limit_array),
        )
    elif limit_array.shape != (2,):
        raise ValueError("torque_limit must be a scalar or contain two values.")

    if not np.all(np.isfinite(limit_array)):
        raise ValueError("torque_limit must contain only finite values.")

    if np.any(limit_array <= 0.0):
        raise ValueError("torque_limit must be positive.")

    applied_torque = np.clip(
        requested_array,
        -limit_array,
        limit_array,
    )

    saturated = np.abs(requested_array) >= limit_array

    return ActuatorOutput(
        requested_torque=requested_array,
        applied_torque=applied_torque,
        saturated=saturated,
    )
