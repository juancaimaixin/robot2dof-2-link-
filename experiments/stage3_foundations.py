from collections.abc import Callable

import numpy as np


def linear_system_exercise() -> None:
    coefficient_matrix = np.array(
        [
            [2.0, 1.0],
            [1.0, -1.0],
        ]
    )
    right_hand_side = np.array([7.0, -1.0])

    solution = np.linalg.solve(
        coefficient_matrix,
        right_hand_side,
    )

    assert np.allclose(solution, [2.0, 3.0])
    assert np.allclose(
        coefficient_matrix @ solution,
        right_hand_side,
    )

    print(f"Linear-system solution: {solution}")


def central_difference(
    function: Callable[[float], float],
    x: float,
    step: float,
) -> float:
    return float((function(x + step) - function(x - step)) / (2.0 * step))


def finite_difference_exercise() -> None:
    x = 0.7
    step = 1e-5

    numerical_derivative = central_difference(
        np.sin,
        x,
        step,
    )
    exact_derivative = float(np.cos(x))

    assert np.isclose(
        numerical_derivative,
        exact_derivative,
        atol=1e-9,
        rtol=0.0,
    )

    print(
        "Finite-difference derivative:",
        numerical_derivative,
    )


def rk4_step(
    derivative: Callable[[float, float], float],
    time: float,
    state: float,
    step: float,
) -> float:
    k1 = derivative(time, state)
    k2 = derivative(
        time + step / 2.0,
        state + step * k1 / 2.0,
    )
    k3 = derivative(
        time + step / 2.0,
        state + step * k2 / 2.0,
    )
    k4 = derivative(
        time + step,
        state + step * k3,
    )

    return state + step * (k1 + 2.0 * k2 + 2.0 * k3 + k4) / 6.0


def exponential_derivative(
    _time: float,
    state: float,
) -> float:
    return state


def rk4_exercise() -> None:
    time = 0.0
    state = 1.0
    step = 0.1

    for _ in range(10):
        state = rk4_step(
            exponential_derivative,
            time,
            state,
            step,
        )
        time += step

    exact_state = float(np.exp(1.0))

    assert np.isclose(
        state,
        exact_state,
        atol=3e-6,
        rtol=0.0,
    )

    print(f"RK4 final state: {state}")


def broadcasting_exercise() -> None:
    joint_samples = np.array(
        [
            [0.0, 0.0],
            [0.1, -0.2],
            [0.2, -0.4],
        ]
    )
    joint_offsets = np.array([0.01, -0.02])

    adjusted_samples = joint_samples + joint_offsets

    expected_samples = np.array(
        [
            [0.01, -0.02],
            [0.11, -0.22],
            [0.21, -0.42],
        ]
    )

    assert joint_samples.shape == (3, 2)
    assert joint_offsets.shape == (2,)
    assert adjusted_samples.shape == (3, 2)
    assert np.allclose(
        adjusted_samples,
        expected_samples,
    )

    print(
        "Broadcast-adjusted samples:",
        adjusted_samples,
    )


if __name__ == "__main__":
    linear_system_exercise()
    finite_difference_exercise()
    rk4_exercise()
    broadcasting_exercise()
