import numpy as np
import pytest

from robot2dof.actuation import saturate_joint_torque


def test_scalar_torque_limit_clips_each_joint():
    output = saturate_joint_torque(
        requested_torque=np.array(
            [
                25.0,
                -12.0,
            ]
        ),
        torque_limit=20.0,
    )

    assert output.requested_torque == pytest.approx(
        np.array(
            [
                25.0,
                -12.0,
            ]
        ),
        abs=1e-12,
    )
    assert output.applied_torque == pytest.approx(
        np.array(
            [
                20.0,
                -12.0,
            ]
        ),
        abs=1e-12,
    )
    assert np.array_equal(
        output.saturated,
        np.array(
            [
                True,
                False,
            ]
        ),
    )


def test_per_joint_torque_limits_are_applied_independently():
    output = saturate_joint_torque(
        requested_torque=np.array(
            [
                -6.0,
                9.0,
            ]
        ),
        torque_limit=np.array(
            [
                5.0,
                10.0,
            ]
        ),
    )

    assert output.applied_torque == pytest.approx(
        np.array(
            [
                -5.0,
                9.0,
            ]
        ),
        abs=1e-12,
    )
    assert np.array_equal(
        output.saturated,
        np.array(
            [
                True,
                False,
            ]
        ),
    )


def test_torque_at_limit_is_marked_as_saturated():
    output = saturate_joint_torque(
        requested_torque=np.array(
            [
                20.0,
                -20.0,
            ]
        ),
        torque_limit=20.0,
    )

    assert output.applied_torque == pytest.approx(
        output.requested_torque,
        abs=1e-12,
    )
    assert np.array_equal(
        output.saturated,
        np.array(
            [
                True,
                True,
            ]
        ),
    )


@pytest.mark.parametrize(
    "requested_torque",
    [
        [1.0],
        [1.0, 2.0, 3.0],
        [np.nan, 0.0],
        [0.0, np.inf],
    ],
)
def test_torque_saturation_rejects_invalid_requested_torque(
    requested_torque,
):
    with pytest.raises(
        ValueError,
        match="requested_torque",
    ):
        saturate_joint_torque(
            requested_torque=requested_torque,
            torque_limit=20.0,
        )


@pytest.mark.parametrize(
    (
        "torque_limit",
        "expected_message",
    ),
    [
        (
            0.0,
            "positive",
        ),
        (
            -1.0,
            "positive",
        ),
        (
            [10.0],
            "scalar or contain two",
        ),
        (
            [10.0, np.inf],
            "finite",
        ),
    ],
)
def test_torque_saturation_rejects_invalid_limit(
    torque_limit,
    expected_message,
):
    with pytest.raises(
        ValueError,
        match=expected_message,
    ):
        saturate_joint_torque(
            requested_torque=np.zeros(2),
            torque_limit=torque_limit,
        )
