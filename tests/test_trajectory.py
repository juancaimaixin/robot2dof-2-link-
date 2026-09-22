import numpy as np
import pytest

from robot2dof.trajectory import (
    Reference,
    sample_quintic_segment,
    sample_quintic_trajectory,
)


def test_quintic_segment_satisfies_endpoint_conditions():
    start_position = np.array(
        [
            -0.40,
            0.70,
        ]
    )
    end_position = np.array(
        [
            0.80,
            -0.20,
        ]
    )

    start_reference = sample_quintic_segment(
        time=1.0,
        start_time=1.0,
        end_time=3.0,
        start_position=start_position,
        end_position=end_position,
    )
    end_reference = sample_quintic_segment(
        time=3.0,
        start_time=1.0,
        end_time=3.0,
        start_position=start_position,
        end_position=end_position,
    )

    assert isinstance(start_reference, Reference)

    assert start_reference.q_ref == pytest.approx(
        start_position,
        abs=1e-12,
    )
    assert start_reference.q_dot_ref == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )
    assert start_reference.q_ddot_ref == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )

    assert end_reference.q_ref == pytest.approx(
        end_position,
        abs=1e-12,
    )
    assert end_reference.q_dot_ref == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )
    assert end_reference.q_ddot_ref == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )


def test_quintic_segment_matches_known_quarter_point():
    reference = sample_quintic_segment(
        time=0.5,
        start_time=0.0,
        end_time=2.0,
        start_position=np.array(
            [
                0.0,
                -1.0,
            ]
        ),
        end_position=np.array(
            [
                2.0,
                3.0,
            ]
        ),
    )

    assert reference.q_ref == pytest.approx(
        np.array(
            [
                0.20703125,
                -0.5859375,
            ]
        ),
        abs=1e-12,
    )
    assert reference.q_dot_ref == pytest.approx(
        np.array(
            [
                1.0546875,
                2.109375,
            ]
        ),
        abs=1e-12,
    )
    assert reference.q_ddot_ref == pytest.approx(
        np.array(
            [
                2.8125,
                5.625,
            ]
        ),
        abs=1e-12,
    )


def test_quintic_segment_rejects_invalid_time_interval():
    with pytest.raises(
        ValueError,
        match="end_time",
    ):
        sample_quintic_segment(
            time=1.0,
            start_time=1.0,
            end_time=1.0,
            start_position=np.zeros(2),
            end_position=np.ones(2),
        )


@pytest.mark.parametrize(
    "time",
    [
        -0.1,
        2.1,
    ],
)
def test_quintic_segment_rejects_time_outside_segment(time):
    with pytest.raises(
        ValueError,
        match="time",
    ):
        sample_quintic_segment(
            time=time,
            start_time=0.0,
            end_time=2.0,
            start_position=np.zeros(2),
            end_position=np.ones(2),
        )


@pytest.mark.parametrize(
    (
        "start_position",
        "end_position",
    ),
    [
        (
            [0.0],
            [1.0, 2.0],
        ),
        (
            [0.0, 1.0],
            [1.0, 2.0, 3.0],
        ),
    ],
)
def test_quintic_segment_rejects_invalid_joint_shape(
    start_position,
    end_position,
):
    with pytest.raises(
        ValueError,
        match="exactly two",
    ):
        sample_quintic_segment(
            time=0.5,
            start_time=0.0,
            end_time=1.0,
            start_position=start_position,
            end_position=end_position,
        )


WAYPOINT_TIMES = np.array(
    [
        0.0,
        2.0,
        5.0,
    ]
)

WAYPOINT_POSITIONS = np.array(
    [
        [0.0, 0.0],
        [2.0, -2.0],
        [5.0, 1.0],
    ]
)


def test_multi_segment_trajectory_satisfies_all_waypoints():
    for time, expected_position in zip(
        WAYPOINT_TIMES,
        WAYPOINT_POSITIONS,
        strict=True,
    ):
        reference = sample_quintic_trajectory(
            time=time,
            waypoint_times=WAYPOINT_TIMES,
            waypoint_positions=WAYPOINT_POSITIONS,
        )

        assert reference.q_ref == pytest.approx(
            expected_position,
            abs=1e-12,
        )
        assert reference.q_dot_ref == pytest.approx(
            np.zeros(2),
            abs=1e-12,
        )
        assert reference.q_ddot_ref == pytest.approx(
            np.zeros(2),
            abs=1e-12,
        )


@pytest.mark.parametrize(
    (
        "time",
        "expected_position",
        "expected_velocity",
    ),
    [
        (
            1.0,
            np.array([1.0, -1.0]),
            np.array([1.875, -1.875]),
        ),
        (
            3.5,
            np.array([3.5, -0.5]),
            np.array([1.875, 1.875]),
        ),
    ],
)
def test_multi_segment_trajectory_selects_correct_segment(
    time,
    expected_position,
    expected_velocity,
):
    reference = sample_quintic_trajectory(
        time=time,
        waypoint_times=WAYPOINT_TIMES,
        waypoint_positions=WAYPOINT_POSITIONS,
    )

    assert reference.q_ref == pytest.approx(
        expected_position,
        abs=1e-12,
    )
    assert reference.q_dot_ref == pytest.approx(
        expected_velocity,
        abs=1e-12,
    )
    assert reference.q_ddot_ref == pytest.approx(
        np.zeros(2),
        abs=1e-12,
    )


@pytest.mark.parametrize(
    (
        "waypoint_times",
        "waypoint_positions",
        "expected_message",
    ),
    [
        (
            [[0.0, 1.0], [2.0, 3.0]],
            np.zeros((4, 2)),
            "one-dimensional",
        ),
        (
            [0.0],
            [[0.0, 0.0]],
            "At least two",
        ),
        (
            [0.0, 1.0, 2.0],
            [[0.0, 0.0], [1.0, 1.0]],
            "shape",
        ),
        (
            [0.0, 1.0, 1.0],
            [[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]],
            "strictly increasing",
        ),
    ],
)
def test_multi_segment_trajectory_rejects_invalid_waypoint_data(
    waypoint_times,
    waypoint_positions,
    expected_message,
):
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        sample_quintic_trajectory(
            time=0.5,
            waypoint_times=waypoint_times,
            waypoint_positions=waypoint_positions,
        )


@pytest.mark.parametrize(
    "time",
    [
        -0.1,
        5.1,
    ],
)
def test_multi_segment_trajectory_rejects_time_outside_trajectory(
    time,
):
    with pytest.raises(
        ValueError,
        match="within the trajectory",
    ):
        sample_quintic_trajectory(
            time=time,
            waypoint_times=WAYPOINT_TIMES,
            waypoint_positions=WAYPOINT_POSITIONS,
        )
