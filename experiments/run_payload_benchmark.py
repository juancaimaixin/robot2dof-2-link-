from datetime import datetime, timezone
from pathlib import Path

from plot_payload_benchmark import plot_payload_benchmark

from robot2dof.benchmark import load_frozen_gains, run_payload_controller
from robot2dof.results_io import (
    build_payload_configuration,
    save_payload_history,
    save_payload_manifest,
    save_payload_summary,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FROZEN_PATH = PROJECT_ROOT / "results" / "tuning_search.json"
CONTROLLERS = ("pid", "pid_gravity", "computed_torque")
PAYLOAD_MASSES = (0.0, 0.25, 0.50, 0.75, 1.00)


def main() -> None:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    output_dir = PROJECT_ROOT / "results" / "payload" / timestamp
    output_dir.mkdir(parents=True, exist_ok=False)

    frozen_snapshot = output_dir / "tuning_search.json"
    with frozen_snapshot.open("xb") as output:
        output.write(FROZEN_PATH.read_bytes())

    # Validate all three gain records before starting any simulation.
    for controller in CONTROLLERS:
        load_frozen_gains(frozen_snapshot, controller)

    print(f"Output directory: {output_dir}", flush=True)

    runs = []
    total_runs = len(PAYLOAD_MASSES) * len(CONTROLLERS)

    for payload_mass in PAYLOAD_MASSES:
        for controller in CONTROLLERS:
            run_number = len(runs) + 1
            print(
                f"[{run_number}/{total_runs}] "
                f"Running {controller}, payload={payload_mass} kg...",
                flush=True,
            )

            run = run_payload_controller(
                frozen_path=frozen_snapshot,
                controller=controller,
                payload_mass=payload_mass,
            )

            configuration = build_payload_configuration(run)

            save_payload_history(
                run,
                output_dir / configuration["output"]["history"],
            )
            save_payload_manifest(
                run,
                output_dir=output_dir,
                project_root=PROJECT_ROOT,
            )

            runs.append(run)
            print(
                f"Saved {controller}, payload={payload_mass} kg.",
                flush=True,
            )

    summary_path = save_payload_summary(
        runs,
        output_dir / "payload_metrics.csv",
    )

    figure_path = plot_payload_benchmark(output_dir)

    print(f"Completed. Summary: {summary_path}", flush=True)
    print(f"Figure: {figure_path}", flush=True)


if __name__ == "__main__":
    main()
