import hashlib
import json
from dataclasses import asdict
from pathlib import Path

from robot2dof import tuning

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = PROJECT_ROOT / "results" / "tuning_search.json"
CONTROLLERS = ("pid", "pid_gravity", "computed_torque")


def build_configuration():
    scenario = tuning.create_training_scenario()

    return {
        "candidate_count_per_controller": tuning.TUNING_CANDIDATE_COUNT,
        "seed": tuning.TUNING_SEED,
        "weights": asdict(tuning.DEFAULT_TUNING_WEIGHTS),
        "pid_candidates": [
            asdict(candidate) for candidate in tuning.generate_pid_tuning_candidates()
        ],
        "computed_torque_candidates": [
            asdict(candidate)
            for candidate in (tuning.generate_computed_torque_tuning_candidates())
        ],
        "training_scenario": {
            "waypoint_times": scenario.waypoint_times.tolist(),
            "waypoint_positions": scenario.waypoint_positions.tolist(),
            "initial_state": scenario.initial_state.tolist(),
            "initial_integral_error": (scenario.initial_integral_error.tolist()),
            "plant_params": asdict(scenario.params),
            "controller_params": asdict(scenario.controller_params),
            "torque_limit": scenario.torque_limit,
            "external_tau": scenario.external_tau.tolist(),
            "step": scenario.step,
        },
        "screening": {
            "position_limit": float(tuning.TUNING_POSITION_LIMIT),
            "velocity_limit": tuning.TUNING_VELOCITY_LIMIT,
        },
        "ranking": [
            "score",
            "normalized_control_effort",
            "candidate_id",
        ],
    }


def serialize_evaluation(evaluation):
    gains = {
        name: getattr(evaluation.gains, name).tolist()
        for name in ("kp", "ki", "kd")
        if hasattr(evaluation.gains, name)
    }

    return {
        "candidate": asdict(evaluation.candidate),
        "gains": gains,
        "succeeded": evaluation.succeeded,
        "metrics": (None if evaluation.metrics is None else asdict(evaluation.metrics)),
        "failure_reason": evaluation.failure_reason,
    }


def write_results(payload):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = OUTPUT_PATH.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(OUTPUT_PATH)


def main():
    configuration = build_configuration()
    canonical_configuration = json.dumps(
        configuration,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    configuration_hash = hashlib.sha256(
        canonical_configuration.encode("utf-8")
    ).hexdigest()

    payload = {
        "status": "in_progress",
        "configuration_sha256": configuration_hash,
        "configuration": configuration,
        "searches": {},
    }
    write_results(payload)

    for controller in CONTROLLERS:
        print(f"Running {controller}...", flush=True)
        result = tuning.run_training_search(controller)
        evaluations = [
            serialize_evaluation(evaluation) for evaluation in result.evaluations
        ]
        best = result.best_evaluation

        payload["searches"][controller] = {
            "evaluated": len(evaluations),
            "successful": sum(evaluation["succeeded"] for evaluation in evaluations),
            "failed": sum(not evaluation["succeeded"] for evaluation in evaluations),
            "best_candidate_id": (
                None if best is None else best.candidate.candidate_id
            ),
            "evaluations": evaluations,
        }
        write_results(payload)

        print(
            f"{controller}: best candidate "
            f"{None if best is None else best.candidate.candidate_id}",
            flush=True,
        )

    payload["status"] = "complete"
    write_results(payload)
    print(f"Saved: {OUTPUT_PATH}", flush=True)


if __name__ == "__main__":
    main()
