from dataclasses import replace

import numpy as np
import pytest

import robot2dof.tuning as tuning
from robot2dof.dynamics import gravity_vector
from robot2dof.simulation import PIDSimulationResult


@pytest.fixture(scope="module")
def baseline_evaluations():
    pid = tuning.generate_pid_tuning_candidates()[0]
    ctc = tuning.generate_computed_torque_tuning_candidates()[0]
    return {
        "pid": tuning.evaluate_training_candidate("pid", pid),
        "pid_gravity": tuning.evaluate_training_candidate("pid_gravity", pid),
        "computed_torque": tuning.evaluate_training_candidate("computed_torque", ctc),
    }


@pytest.mark.parametrize("controller", ["pid", "pid_gravity", "computed_torque"])
def test_baselines_use_complete_fixed_training_history(
    baseline_evaluations, controller
):
    evaluation = baseline_evaluations[controller]
    assert evaluation.succeeded, evaluation.failure_reason
    assert evaluation.controller == controller
    assert evaluation.candidate.candidate_id == 0
    assert evaluation.failure_reason is None
    assert np.isfinite(evaluation.score)
    assert evaluation.score == evaluation.metrics.score

    simulation = evaluation.simulation
    assert simulation.time_values.shape == (4001,)
    np.testing.assert_allclose(np.diff(simulation.time_values), 0.001, atol=1e-12)
    assert simulation.time_values[[0, -1]] == pytest.approx([0.0, 4.0])
    assert simulation.state_history[0] == pytest.approx(
        [*np.radians([-35.0, -45.0]), 0.0, 0.0]
    )
    assert simulation.reference_position_history[-1] == pytest.approx(
        np.radians([50.0, 60.0])
    )

    expected_initial_torque = np.zeros(2)
    if controller != "pid":
        scenario = tuning.create_training_scenario()
        expected_initial_torque = gravity_vector(
            simulation.state_history[0, :2], scenario.controller_params
        )
    assert simulation.requested_torque_history[0] == pytest.approx(
        expected_initial_torque
    )
    if isinstance(simulation, PIDSimulationResult):
        np.testing.assert_array_equal(simulation.integral_error_history[0], np.zeros(2))


@pytest.fixture
def valid_history():
    reference = np.array([[0.0, 0.0], [0.5, 0.5], [1.0, 1.0]])
    return PIDSimulationResult(
        time_values=np.array([0.0, 2.0, 4.0]),
        state_history=np.column_stack((reference, np.zeros((3, 2)))),
        reference_position_history=reference,
        reference_velocity_history=np.zeros((3, 2)),
        reference_acceleration_history=np.zeros((3, 2)),
        integral_error_history=np.zeros((3, 2)),
        requested_torque_history=np.zeros((3, 2)),
        applied_torque_history=np.zeros((3, 2)),
        saturation_history=np.zeros((3, 2), dtype=bool),
    )


def evaluate_history(monkeypatch, history):
    monkeypatch.setattr(tuning, "simulate_pid_trajectory", lambda **kwargs: history)
    return tuning.evaluate_training_candidate("pid", tuning.PID_BASELINE)


@pytest.mark.parametrize("sample_index", [1, -1])
@pytest.mark.parametrize(
    "column,value,reason",
    [
        (0, np.pi, None),
        (1, -np.pi, None),
        (0, np.nextafter(np.pi, np.inf), "joint_position_limit"),
        (1, np.nextafter(-np.pi, -np.inf), "joint_position_limit"),
        (2, 50.0, None),
        (3, -50.0, None),
        (2, np.nextafter(50.0, np.inf), "joint_velocity_limit"),
        (3, np.nextafter(-50.0, -np.inf), "joint_velocity_limit"),
    ],
)
def test_limits_include_boundaries_and_screen_intermediate_and_final_states(
    monkeypatch, valid_history, sample_index, column, value, reason
):
    valid_history.state_history[sample_index, column] = value
    evaluation = evaluate_history(monkeypatch, valid_history)
    assert evaluation.failure_reason == reason
    assert evaluation.succeeded == (reason is None)
    assert evaluation.simulation is valid_history
    if reason is not None:
        assert evaluation.metrics is None
        assert evaluation.score == float("inf")


@pytest.mark.parametrize("value", [np.nan, np.inf])
@pytest.mark.parametrize(
    "field",
    [
        "time_values",
        "state_history",
        "reference_position_history",
        "reference_velocity_history",
        "reference_acceleration_history",
        "integral_error_history",
        "requested_torque_history",
        "applied_torque_history",
    ],
)
def test_non_finite_histories_are_failed_before_scoring(
    monkeypatch, valid_history, field, value
):
    history = getattr(valid_history, field).copy()
    history.flat[-1] = value
    evaluation = evaluate_history(
        monkeypatch, replace(valid_history, **{field: history})
    )
    assert evaluation.failure_reason == f"non_finite_history: {field}"
    assert not evaluation.succeeded
    assert evaluation.metrics is None
    assert evaluation.score == float("inf")


def test_saturation_is_scored_without_failing_candidate(monkeypatch, valid_history):
    valid_history.requested_torque_history[:] = 25.0
    valid_history.applied_torque_history[:] = 20.0
    valid_history.saturation_history[:] = True
    evaluation = evaluate_history(monkeypatch, valid_history)
    assert evaluation.succeeded
    assert evaluation.metrics.normalized_joint_rmse == 0.0
    assert evaluation.metrics.normalized_control_effort == pytest.approx(1.0)
    assert evaluation.metrics.saturation_fraction == pytest.approx(1.0)
    assert evaluation.score == pytest.approx(0.3)


@pytest.mark.parametrize(
    "field",
    [
        "normalized_joint_rmse",
        "normalized_control_effort",
        "saturation_fraction",
        "score",
    ],
)
def test_non_finite_metrics_are_failures(monkeypatch, valid_history, field):
    metrics = replace(tuning.TuningMetrics(0.0, 0.0, 0.0, 0.0), **{field: np.inf})
    monkeypatch.setattr(tuning, "compute_tuning_metrics", lambda **kwargs: metrics)
    evaluation = evaluate_history(monkeypatch, valid_history)
    assert evaluation.failure_reason == "non_finite_metrics"
    assert not evaluation.succeeded
    assert evaluation.metrics is None
    assert evaluation.score == float("inf")


@pytest.mark.parametrize(
    "error_type", [FloatingPointError, OverflowError, np.linalg.LinAlgError]
)
def test_numerical_exceptions_are_recorded(monkeypatch, error_type):
    def fail(**kwargs):
        raise error_type("synthetic numerical failure")

    monkeypatch.setattr(tuning, "simulate_pid_trajectory", fail)
    evaluation = tuning.evaluate_training_candidate("pid", tuning.PID_BASELINE)
    assert not evaluation.succeeded
    assert error_type.__name__ in evaluation.failure_reason
    assert evaluation.simulation is None
    assert evaluation.metrics is None


@pytest.mark.parametrize("error_type", [ValueError, RuntimeError])
def test_programming_and_configuration_errors_are_not_hidden(monkeypatch, error_type):
    def fail(**kwargs):
        raise error_type("unexpected simulation error")

    monkeypatch.setattr(tuning, "simulate_pid_trajectory", fail)
    with pytest.raises(error_type, match="unexpected simulation error"):
        tuning.evaluate_training_candidate("pid", tuning.PID_BASELINE)


def test_numpy_error_policy_is_local_and_overflow_is_recorded(monkeypatch):
    before = np.geterr()

    def overflow(**kwargs):
        np.array([1e308]) * 1e308

    monkeypatch.setattr(tuning, "simulate_pid_trajectory", overflow)
    evaluation = tuning.evaluate_training_candidate("pid", tuning.PID_BASELINE)
    assert "FloatingPointError" in evaluation.failure_reason
    assert np.geterr() == before


def test_invalid_controller_or_candidate_is_rejected_before_simulation(monkeypatch):
    def must_not_run(**kwargs):
        pytest.fail("invalid calls must not start a simulation")

    monkeypatch.setattr(tuning, "simulate_pid_trajectory", must_not_run)
    monkeypatch.setattr(tuning, "simulate_computed_torque_trajectory", must_not_run)
    with pytest.raises(ValueError, match="Unknown controller"):
        tuning.evaluate_training_candidate("typo", tuning.PID_BASELINE)
    with pytest.raises(TypeError, match="ComputedTorqueTuningCandidate"):
        tuning.evaluate_training_candidate("computed_torque", tuning.PID_BASELINE)
    ctc = tuning.generate_computed_torque_tuning_candidates()[0]
    with pytest.raises(TypeError, match="PIDTuningCandidate"):
        tuning.evaluate_training_candidate("pid", ctc)
    with pytest.raises(ValueError, match="kp"):
        tuning.evaluate_training_candidate(
            "pid", replace(tuning.PID_BASELINE, kp=(-1.0, 1.0))
        )


def test_each_evaluation_gets_fresh_inputs_and_correct_model(
    monkeypatch, valid_history
):
    calls = []

    def simulate(**kwargs):
        assert kwargs["initial_state"] == pytest.approx(
            [*np.radians([-35.0, -45.0]), 0.0, 0.0]
        )
        np.testing.assert_array_equal(kwargs["initial_integral_error"], np.zeros(2))
        calls.append(kwargs)
        kwargs["initial_state"][:] = 100.0
        kwargs["initial_integral_error"][:] = 100.0
        return valid_history

    monkeypatch.setattr(tuning, "simulate_pid_trajectory", simulate)
    tuning.evaluate_training_candidate("pid", tuning.PID_BASELINE)
    tuning.evaluate_training_candidate("pid_gravity", tuning.PID_BASELINE)
    assert calls[0]["controller_params"] is None
    assert calls[1]["controller_params"] == calls[1]["params"]
    assert calls[1]["controller_params"] is not calls[1]["params"]
    assert calls[0]["params"] is not calls[1]["params"]


def make_search_evaluation(
    controller,
    candidate,
    *,
    score=0.0,
    effort=0.0,
    failure_reason=None,
):
    if isinstance(candidate, tuning.PIDTuningCandidate):
        gains = tuning.build_pid_candidate_gains(candidate)
    else:
        gains = tuning.build_computed_torque_candidate_gains(candidate)

    metrics = None
    if failure_reason is None:
        metrics = tuning.TuningMetrics(
            normalized_joint_rmse=0.0,
            normalized_control_effort=effort,
            saturation_fraction=0.0,
            score=score,
        )

    return tuning.CandidateEvaluation(
        controller=controller,
        candidate=candidate,
        gains=gains,
        simulation=None,
        metrics=metrics,
        failure_reason=failure_reason,
    )


@pytest.mark.parametrize(
    ("controller", "generate"),
    [
        ("pid", tuning.generate_pid_tuning_candidates),
        ("pid_gravity", tuning.generate_pid_tuning_candidates),
        (
            "computed_torque",
            tuning.generate_computed_torque_tuning_candidates,
        ),
    ],
)
def test_training_search_evaluates_full_budget_and_keeps_failures(
    monkeypatch,
    controller,
    generate,
):
    expected_candidates = generate()
    observed_candidates = []
    failed_ids = {41, 219}

    def evaluate(observed_controller, candidate):
        assert observed_controller == controller
        observed_candidates.append(candidate)

        failure_reason = None
        if candidate.candidate_id in failed_ids:
            failure_reason = "synthetic_failure"

        return make_search_evaluation(
            controller,
            candidate,
            score=1.0 + candidate.candidate_id,
            effort=0.5,
            failure_reason=failure_reason,
        )

    monkeypatch.setattr(tuning, "evaluate_training_candidate", evaluate)

    result = tuning.run_training_search(controller)

    assert result.controller == controller
    assert len(result.evaluations) == tuning.TUNING_CANDIDATE_COUNT
    assert tuple(observed_candidates) == expected_candidates
    assert (
        tuple(evaluation.candidate for evaluation in result.evaluations)
        == expected_candidates
    )
    assert {
        evaluation.candidate.candidate_id
        for evaluation in result.evaluations
        if not evaluation.succeeded
    } == failed_ids
    assert result.best_evaluation.candidate.candidate_id == 0


def test_training_search_uses_full_lexicographic_ranking(monkeypatch):
    candidates = tuple(
        replace(tuning.PID_BASELINE, candidate_id=candidate_id)
        for candidate_id in (9, 8, 7, 6)
    )
    ranking_values = {
        9: (0.4, 0.1),
        8: (0.3, 0.9),
        7: (0.3, 0.4),
        6: (0.3, 0.4),
    }

    monkeypatch.setattr(
        tuning,
        "generate_pid_tuning_candidates",
        lambda: candidates,
    )

    def evaluate(controller, candidate):
        score, effort = ranking_values[candidate.candidate_id]
        return make_search_evaluation(
            controller,
            candidate,
            score=score,
            effort=effort,
        )

    monkeypatch.setattr(tuning, "evaluate_training_candidate", evaluate)

    result = tuning.run_training_search("pid")

    assert [evaluation.candidate.candidate_id for evaluation in result.evaluations] == [
        9,
        8,
        7,
        6,
    ]
    assert result.best_evaluation.candidate.candidate_id == 6


def test_training_search_reports_no_best_when_all_candidates_fail(
    monkeypatch,
):
    def evaluate(controller, candidate):
        return make_search_evaluation(
            controller,
            candidate,
            failure_reason="synthetic_failure",
        )

    monkeypatch.setattr(tuning, "evaluate_training_candidate", evaluate)

    result = tuning.run_training_search("computed_torque")

    assert len(result.evaluations) == tuning.TUNING_CANDIDATE_COUNT
    assert all(not evaluation.succeeded for evaluation in result.evaluations)
    assert result.best_evaluation is None


def test_training_search_rejects_unknown_controller_before_generation(
    monkeypatch,
):
    def must_not_generate():
        pytest.fail("invalid controller must not generate candidates")

    monkeypatch.setattr(
        tuning,
        "generate_pid_tuning_candidates",
        must_not_generate,
    )
    monkeypatch.setattr(
        tuning,
        "generate_computed_torque_tuning_candidates",
        must_not_generate,
    )

    with pytest.raises(ValueError, match="Unknown controller"):
        tuning.run_training_search("typo")
