from datetime import datetime, timezone
from pathlib import Path

from plot_nominal_benchmark import plot_nominal_benchmark

from robot2dof.benchmark import load_frozen_gains, run_nominal_controller
from robot2dof.results_io import (
    save_nominal_history,
    save_nominal_manifest,
    save_nominal_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_PATH = PROJECT_ROOT / "results" / "tuning_search.json"
CONTROLLERS = ("pid", "pid_gravity", "computed_torque")


def main() -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    output_dir = PROJECT_ROOT / "results" / "nominal" / timestamp
    output_dir.mkdir(parents=True, exist_ok=False)

    frozen_snapshot = output_dir / "tuning_search.json"
    with frozen_snapshot.open("xb") as output:
        output.write(FROZEN_PATH.read_bytes())

    # Validate all three gain records before running any controller.
    for controller in CONTROLLERS:
        load_frozen_gains(frozen_snapshot, controller)

    print(f"Output directory: {output_dir}", flush=True)
    runs = []

    for controller in CONTROLLERS:
        print(f"Running {controller}...", flush=True)

        run = run_nominal_controller(
            frozen_path=frozen_snapshot,
            controller=controller,
        )

        save_nominal_history(
            run,
            output_dir / f"{controller}.npz",
        )
        save_nominal_manifest(
            run,
            output_dir=output_dir,
            project_root=PROJECT_ROOT,
        )

        runs.append(run)
        print(f"Saved {controller}.", flush=True)

    summary_path = save_nominal_summary(
        runs,
        output_dir / "nominal_metrics.csv",
    )

    figure_path = plot_nominal_benchmark(output_dir)

    print(f"Completed. Summary: {summary_path}", flush=True)
    print(f"Figure: {figure_path}", flush=True)


if __name__ == "__main__":
    main()
