"""Run and save the complete fixed-protocol disturbance experiment."""

import json
from datetime import datetime, timezone
from pathlib import Path

from plot_disturbance_benchmark import plot_disturbance_benchmark

from robot2dof.benchmark import (
    load_frozen_gains,
    run_disturbance_controller,
    summarize_disturbance_run,
)
from robot2dof.results_io import (
    build_disturbance_configuration,
    save_disturbance_history,
    save_disturbance_manifest,
    save_disturbance_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONTROLLERS = ("pid", "pid_gravity", "computed_torque")


def main() -> None:
    frozen_path = PROJECT_ROOT / "results" / "tuning_search.json"
    for controller in CONTROLLERS:
        load_frozen_gains(frozen_path, controller)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    output_dir = PROJECT_ROOT / "results" / "disturbance" / timestamp
    output_dir.mkdir(parents=True, exist_ok=False)
    frozen_snapshot = output_dir / "tuning_search.json"
    with frozen_snapshot.open("xb") as output:
        output.write(frozen_path.read_bytes())
    for controller in CONTROLLERS:
        load_frozen_gains(frozen_snapshot, controller)
    print(f"Output directory: {output_dir}", flush=True)

    runs = []
    for index, controller in enumerate(CONTROLLERS, start=1):
        print(f"[{index}/3] Running {controller}...", flush=True)
        run = run_disturbance_controller(frozen_snapshot, controller)
        configuration = build_disturbance_configuration(run)
        save_disturbance_history(run, output_dir / configuration["output"]["history"])
        save_disturbance_manifest(run, output_dir, PROJECT_ROOT)
        runs.append(run)
        row = summarize_disturbance_run(run)
        recovery = row["recovery_time_s"]
        label = "not confirmed" if recovery is None else f"{recovery:.3f} s"
        print(f"Saved {controller}; recovery: {label}", flush=True)

    summary_path = save_disturbance_summary(
        runs, output_dir / "disturbance_metrics.csv"
    )
    # JSON retains unconfirmed recovery as null; CSV uses an empty cell.
    with (output_dir / "disturbance_metrics.json").open(
        "x", encoding="utf-8", newline="\n"
    ) as output:
        json.dump(
            [summarize_disturbance_run(run) for run in runs],
            output,
            indent=2,
            allow_nan=False,
        )
        output.write("\n")
    figure_path = plot_disturbance_benchmark(output_dir)
    print(f"Completed. Summary: {summary_path}", flush=True)
    print(f"Figure: {figure_path}", flush=True)


if __name__ == "__main__":
    main()
