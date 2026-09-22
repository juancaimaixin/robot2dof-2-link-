from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Reference:
    """Desired joint position, velocity, and acceleration."""

    q_ref: Sequence[float]
    q_dot_ref: Sequence[float]
    q_ddot_ref: Sequence[float]


def sample_quintic_segment(
    time: float,
    start_time: float,
    end_time: float,
    start_position: Sequence[float],
    end_position: Sequence[float],
) -> Reference:
    """Sample a stop-to-stop quintic joint trajectory segment."""

    if end_time <= start_time:
        raise ValueError("end_time must be later than start_time.")

    if time < start_time or time > end_time:
        raise ValueError("time must lie within the trajectory segment.")

    start_array = np.asarray(
        start_position,
        dtype=float,
    )
    end_array = np.asarray(
        end_position,
        dtype=float,
    )

    if start_array.shape != (2,) or end_array.shape != (2,):
        raise ValueError("Joint positions must contain exactly two values.")

    duration = end_time - start_time
    normalized_time = (time - start_time) / duration
    position_change = end_array - start_array

    blend = (
        10.0 * normalized_time**3 - 15.0 * normalized_time**4 + 6.0 * normalized_time**5
    )

    blend_first_derivative = (
        30.0 * normalized_time**2
        - 60.0 * normalized_time**3
        + 30.0 * normalized_time**4
    )

    blend_second_derivative = (
        60.0 * normalized_time - 180.0 * normalized_time**2 + 120.0 * normalized_time**3
    )

    q_ref = start_array + position_change * blend
    q_dot_ref = position_change * blend_first_derivative / duration
    q_ddot_ref = position_change * blend_second_derivative / duration**2

    return Reference(
        q_ref=q_ref,
        q_dot_ref=q_dot_ref,
        q_ddot_ref=q_ddot_ref,
    )


def sample_quintic_trajectory(
    time: float,
    waypoint_times: Sequence[float],
    waypoint_positions: Sequence[Sequence[float]],
) -> Reference:
    """Sample a multi-segment stop-to-stop quintic trajectory."""

    time_array = np.asarray(
        waypoint_times,
        dtype=float,
    )
    position_array = np.asarray(
        waypoint_positions,
        dtype=float,
    )

    if time_array.ndim != 1:
        raise ValueError("waypoint_times must be one-dimensional.")

    if time_array.size < 2:
        raise ValueError("At least two waypoint times are required.")

    if position_array.shape != (time_array.size, 2):
        raise ValueError("waypoint_positions must have shape (number_of_waypoints, 2).")

    if np.any(np.diff(time_array) <= 0.0):
        raise ValueError("waypoint_times must be strictly increasing.")

    if time < time_array[0] or time > time_array[-1]:
        raise ValueError("time must lie within the trajectory.")

    segment_index = int(
        np.searchsorted(
            time_array,
            time,
            side="right",
        )
        - 1
    )

    segment_index = min(
        segment_index,
        time_array.size - 2,
    )

    return sample_quintic_segment(
        time=time,
        start_time=float(time_array[segment_index]),
        end_time=float(time_array[segment_index + 1]),
        start_position=position_array[segment_index],
        end_position=position_array[segment_index + 1],
    )
