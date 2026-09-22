from datetime import datetime, timezone
from pathlib import Path

from plot_model_uncertainty_benchmark import plot_model_uncertainty_benchmark

from robot2dof.benchmark import (
    load_frozen_gains,
    run_model_uncertainty_controller,
)
from robot2dof.results_io import (
    build_model_uncertainty_configuration,
    save_model_uncertainty_history,
    save_model_uncertainty_manifest,
    save_model_uncertainty_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_PATH = PROJECT_ROOT / "results" / "tuning_search.json"
CONTROLLERS = ("pid", "pid_gravity", "computed_torque")
RELATIVE_ERRORS = (-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3)


def main() -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    output_dir = PROJECT_ROOT / "results" / "model_uncertainty" / timestamp
    output_dir.mkdir(parents=True, exist_ok=False)

    frozen_snapshot = output_dir / "tuning_search.json"
    with frozen_snapshot.open("xb") as output:
        output.write(FROZEN_PATH.read_bytes())

    # Validate all three gain records before starting any simulation.
    for controller in CONTROLLERS:
        load_frozen_gains(frozen_snapshot, controller)

    print(f"Output directory: {output_dir}", flush=True)

    runs = []
    total_runs = len(RELATIVE_ERRORS) * len(CONTROLLERS)

    for relative_error in RELATIVE_ERRORS:
        for controller in CONTROLLERS:
            run_number = len(runs) + 1
            print(
                f"[{run_number}/{total_runs}] "
                f"Running {controller}, model error={relative_error:+.0%}...",
                flush=True,
            )

            run = run_model_uncertainty_controller(
                frozen_path=frozen_snapshot,
                controller=controller,
                relative_error=relative_error,
            )

            configuration = build_model_uncertainty_configuration(run)

            save_model_uncertainty_history(
                run,
                output_dir / configuration["output"]["history"],
            )
            save_model_uncertainty_manifest(
                run,
                output_dir=output_dir,
                project_root=PROJECT_ROOT,
            )

            runs.append(run)
            print(
                f"Saved {controller}, model error={relative_error:+.0%}.",
                flush=True,
            )

    summary_path = save_model_uncertainty_summary(
        runs,
        output_dir / "model_uncertainty_metrics.csv",
    )

    figure_path = plot_model_uncertainty_benchmark(output_dir)

    print(f"Completed. Summary: {summary_path}", flush=True)
    print(f"Figure: {figure_path}", flush=True)


if __name__ == "__main__":
    main()
