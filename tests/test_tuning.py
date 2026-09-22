import hashlib
from dataclasses import replace

import numpy as np
import pytest

from robot2dof.trajectory import sample_quintic_trajectory
from robot2dof.tuning import (
    DEFAULT_TUNING_WEIGHTS,
    ComputedTorqueTuningCandidate,
    PIDTuningCandidate,
    TuningWeights,
    build_computed_torque_candidate_gains,
    build_pid_candidate_gains,
    compute_tuning_metrics,
    computed_torque_gains_from_targets,
    create_training_scenario,
    generate_computed_torque_tuning_candidates,
    generate_pid_tuning_candidates,
)


def test_computed_torque_gains_match_second_order_targets():
    gains = computed_torque_gains_from_targets(
        natural_frequency=np.array([8.0, 6.0]),
        damping_ratio=np.array([1.0, 0.8]),
    )

    assert gains.kp == pytest.approx([64.0, 36.0])
    assert gains.kd == pytest.approx([16.0, 9.6])


def test_compute_tuning_metrics_matches_known_answer():
    time_values = np.array([0.0, 1.0, 2.0])

    reference_positions = np.array(
        [
            [0.0, 0.0],
            [1.0, 2.0],
            [2.0, 4.0],
        ]
    )

    actual_positions = reference_positions - np.array([0.2, 0.4])

    metrics = compute_tuning_metrics(
        time_values=time_values,
        actual_positions=actual_positions,
        reference_positions=reference_positions,
        applied_torque_history=np.tile([2.0, 1.0], (3, 1)),
        saturation_history=np.array(
            [
                [False, False],
                [True, False],
                [False, False],
            ]
        ),
        torque_limit=np.array([4.0, 2.0]),
        weights=TuningWeights(
            tracking_error=0.7,
            control_effort=0.2,
            saturation=0.1,
        ),
    )

    assert metrics.normalized_joint_rmse == pytest.approx(0.1)
    assert metrics.normalized_control_effort == pytest.approx(0.25)
    assert metrics.saturation_fraction == pytest.approx(0.5)
    assert metrics.score == pytest.approx(0.17)


@pytest.mark.parametrize(
    "final_torque",
    [
        [0.0, 0.0],
        [4.0, 2.0],
    ],
)
@pytest.mark.parametrize(
    "final_saturated",
    [
        [False, False],
        [True, True],
    ],
)
def test_compute_tuning_metrics_uses_held_control_intervals(
    final_torque,
    final_saturated,
):
    reference_positions = np.array(
        [
            [0.0, 0.0],
            [1.0, 2.0],
            [2.0, 4.0],
        ]
    )

    metrics = compute_tuning_metrics(
        time_values=np.array([0.0, 0.5, 2.0]),
        actual_positions=(reference_positions - np.array([0.2, 0.4])),
        reference_positions=reference_positions,
        applied_torque_history=np.array(
            [
                [4.0, 0.0],
                [0.0, 1.0],
                final_torque,
            ]
        ),
        saturation_history=np.array(
            [
                [True, False],
                [False, False],
                final_saturated,
            ]
        ),
        torque_limit=np.array([4.0, 2.0]),
        weights=TuningWeights(
            tracking_error=0.7,
            control_effort=0.2,
            saturation=0.1,
        ),
    )

    assert metrics.normalized_joint_rmse == pytest.approx(0.1)
    assert metrics.normalized_control_effort == pytest.approx(0.2375)
    assert metrics.saturation_fraction == pytest.approx(0.25)
    assert metrics.score == pytest.approx(0.1425)


def test_compute_tuning_metrics_includes_terminal_position_error():
    reference_positions = np.array(
        [
            [0.0, 0.0],
            [1.0, 2.0],
            [2.0, 4.0],
        ]
    )

    actual_positions = reference_positions.copy()
    actual_positions[-1] -= np.array([0.4, 0.4])

    metrics = compute_tuning_metrics(
        time_values=np.array([0.0, 0.5, 2.0]),
        actual_positions=actual_positions,
        reference_positions=reference_positions,
        applied_torque_history=np.zeros((3, 2)),
        saturation_history=np.zeros((3, 2), dtype=bool),
        torque_limit=np.array([4.0, 2.0]),
        weights=DEFAULT_TUNING_WEIGHTS,
    )

    expected_rmse = np.sqrt(1.0 / 120.0)

    assert metrics.normalized_joint_rmse == pytest.approx(expected_rmse)
    assert metrics.normalized_control_effort == pytest.approx(0.0)
    assert metrics.saturation_fraction == pytest.approx(0.0)
    assert metrics.score == pytest.approx(0.7 * expected_rmse)


def test_training_scenario_starts_on_reference_with_zero_integral():
    scenario = create_training_scenario()

    initial_reference = sample_quintic_trajectory(
        time=float(scenario.waypoint_times[0]),
        waypoint_times=scenario.waypoint_times,
        waypoint_positions=scenario.waypoint_positions,
    )

    np.testing.assert_allclose(
        scenario.initial_state[:2],
        initial_reference.q_ref,
        rtol=0.0,
        atol=1e-12,
    )
    np.testing.assert_allclose(
        scenario.initial_state[2:],
        initial_reference.q_dot_ref,
        rtol=0.0,
        atol=1e-12,
    )
    np.testing.assert_array_equal(
        scenario.initial_integral_error,
        np.zeros(2),
    )

    assert scenario.params == scenario.controller_params
    assert scenario.params is not scenario.controller_params


@pytest.mark.parametrize(
    "field_name",
    [
        "waypoint_times",
        "waypoint_positions",
        "initial_state",
        "initial_integral_error",
        "external_tau",
    ],
)
def test_training_candidates_do_not_share_input_arrays(field_name):
    first = create_training_scenario()
    second = create_training_scenario()

    first_values = getattr(first, field_name)
    second_values = getattr(second, field_name)
    expected_values = second_values.copy()

    first_values.flat[0] += 1.0

    np.testing.assert_array_equal(
        second_values,
        expected_values,
    )


@pytest.mark.parametrize(
    "generate",
    [generate_pid_tuning_candidates, generate_computed_torque_tuning_candidates],
)
def test_tuning_candidates_are_reproducible_with_fixed_budget(generate):
    candidates = generate()

    assert candidates == generate()
    assert len(candidates) == 300
    assert [candidate.candidate_id for candidate in candidates] == list(range(300))


def test_computed_torque_candidates_stay_within_search_space():
    candidates = generate_computed_torque_tuning_candidates()

    assert candidates[0].natural_frequency == (8.0, 8.0)
    assert candidates[0].damping_ratio == (1.0, 1.0)

    for candidate in candidates:
        assert all(3.0 <= value <= 12.0 for value in candidate.natural_frequency)
        assert all(0.7 <= value <= 1.2 for value in candidate.damping_ratio)

    effective_ctc_targets = {
        (
            candidate.natural_frequency,
            candidate.damping_ratio,
        )
        for candidate in candidates
    }

    assert len(effective_ctc_targets) == len(candidates)


def test_computed_torque_gain_mapping_is_unchanged():
    candidate = ComputedTorqueTuningCandidate(
        candidate_id=7,
        natural_frequency=(8.0, 6.0),
        damping_ratio=(1.0, 0.8),
    )

    gains = build_computed_torque_candidate_gains(candidate)

    assert gains.kp == pytest.approx([64.0, 36.0])
    assert gains.kd == pytest.approx([16.0, 9.6])


def test_computed_torque_full_table_matches_pre_rewrite_snapshot():
    # Captured before splitting PID and CTC: all 300 IDs, targets, kp and kd.
    rows = []
    for candidate in generate_computed_torque_tuning_candidates():
        gains = build_computed_torque_candidate_gains(candidate)
        rows.append(
            [
                candidate.candidate_id,
                *candidate.natural_frequency,
                *candidate.damping_ratio,
                *gains.kp,
                *gains.kd,
            ]
        )

    digest = hashlib.sha256(np.asarray(rows, dtype="<f8").tobytes()).hexdigest()
    assert digest == "24c30127f23b0187d1933e459abd68eb0adabef57cb829de1ac648206d2343d6"


def test_pid_candidates_use_direct_six_gain_ranges_and_baseline():
    candidates = generate_pid_tuning_candidates()
    assert candidates[0].kp == (150.0, 100.0)
    assert candidates[0].ki == (30.0, 20.0)
    assert candidates[0].kd == (25.0, 15.0)

    rows = np.array(
        [[c.kp[0], c.ki[0], c.kd[0], c.kp[1], c.ki[1], c.kd[1]] for c in candidates]
    )
    assert np.all(rows >= [20.0, 0.0, 1.0, 10.0, 0.0, 0.5])
    assert np.all(rows <= [300.0, 100.0, 60.0, 200.0, 80.0, 40.0])
    assert np.unique(rows, axis=0).shape[0] == 300
    # All six coordinates vary, including independent integral gains.
    assert np.all(np.ptp(rows[1:], axis=0) > 0.0)


def test_pid_gain_builder_preserves_arbitrary_direct_gains_and_isolates_runs():
    candidate = PIDTuningCandidate(
        candidate_id=7, kp=(42.0, 17.0), ki=(0.0, 9.0), kd=(3.0, 0.5)
    )
    pid = build_pid_candidate_gains(candidate)
    pid_gravity = build_pid_candidate_gains(candidate)

    np.testing.assert_array_equal(pid.kp, [42.0, 17.0])
    np.testing.assert_array_equal(pid.ki, [0.0, 9.0])
    np.testing.assert_array_equal(pid.kd, [3.0, 0.5])
    for name in ("kp", "ki", "kd"):
        getattr(pid, name)[0] = -1.0
        np.testing.assert_array_equal(
            getattr(pid_gravity, name), getattr(candidate, name)
        )


@pytest.mark.parametrize("name", ["kp", "ki", "kd"])
@pytest.mark.parametrize("values", [(-1.0, 0.0), (np.nan, 1.0), (np.inf, 1.0), (1.0,)])
def test_pid_gain_builder_rejects_invalid_inputs(name, values):
    candidate = replace(generate_pid_tuning_candidates()[0], **{name: values})
    with pytest.raises(ValueError, match=name):
        build_pid_candidate_gains(candidate)


@pytest.mark.parametrize(
    "generate",
    [generate_pid_tuning_candidates, generate_computed_torque_tuning_candidates],
)
def test_candidate_generators_leave_global_random_state_unchanged(generate):
    before = np.random.get_state()
    generate()
    after = np.random.get_state()
    assert before[0] == after[0]
    np.testing.assert_array_equal(before[1], after[1])
    assert before[2:] == after[2:]


def test_ctc_generation_cannot_advance_pid_random_sequence():
    before = generate_pid_tuning_candidates()
    generate_computed_torque_tuning_candidates()
    assert generate_pid_tuning_candidates() == before
