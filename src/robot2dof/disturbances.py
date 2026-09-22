from collections.abc import Callable

import numpy as np

from .kinematics import end_effector_force_to_joint_torque
from .parameters import RobotParams


def create_disturbance_torque_for_step(
    time: float,
    step: float,
    params: RobotParams,
) -> Callable[[float, np.ndarray], np.ndarray]:
    """Create the fixed-protocol disturbance for one integration interval."""

    if not np.isfinite(time):
        raise ValueError("time must be finite.")

    if not np.isfinite(step) or step <= 0.0:
        raise ValueError("step must be a positive finite value.")

    interval_end = time + step

    if not np.isfinite(interval_end) or interval_end <= time:
        raise ValueError("The integration interval must advance time.")

    pulse_start = 4.5
    pulse_end = 4.7
    tolerance = 1e-12

    for boundary in (pulse_start, pulse_end):
        if time + tolerance < boundary < interval_end - tolerance:
            raise ValueError("An integration interval must not cross a pulse boundary.")

    midpoint = time + step / 2.0
    active = pulse_start <= midpoint < pulse_end

    force = np.array([10.0, 0.0]) if active else np.zeros(2)

    def external_torque(
        _stage_time: float,
        stage_q: np.ndarray,
    ) -> np.ndarray:
        return end_effector_force_to_joint_torque(
            q=stage_q,
            force=force,
            params=params,
        )

    return external_torque
