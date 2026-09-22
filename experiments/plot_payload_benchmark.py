import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

CONTROLLERS = (
    ("pid", "PID", "tab:blue", "o"),
    ("pid_gravity", "PID + Gravity", "tab:orange", "s"),
    ("computed_torque", "Computed Torque", "tab:green", "^"),
)

PAYLOAD_MASSES = (0.0, 0.25, 0.50, 0.75, 1.00)

METRICS = (
    (
        "overall_joint_rmse_deg",
        "Tracking error",
        "Overall joint RMSE [deg]",
        1.0,
    ),
    (
        "control_effort_nm2_s",
        "Control effort",
        r"Control effort [$(N\,m)^2\,s$]",
        1.0,
    ),
    (
        "saturation_fraction",
        "Torque saturation",
        "Saturated time [%]",
        100.0,
    ),
)


def plot_payload_benchmark(result_dir: str | Path) -> Path:
    """Plot the saved payload summary without rerunning simulations."""

    directory = Path(result_dir).resolve()

    with (directory / "payload_metrics.csv").open(
        encoding="utf-8",
        newline="",
    ) as source:
        rows = list(csv.DictReader(source))

    expected_keys = {
        (mass, controller)
        for mass in PAYLOAD_MASSES
        for controller, _, _, _ in CONTROLLERS
    }

    rows_by_key = {
        (float(row["payload_mass_kg"]), row["controller"]): row for row in rows
    }

    if len(rows) != len(expected_keys) or set(rows_by_key) != expected_keys:
        raise ValueError("Expected exactly one row for each payload-controller pair.")

    values_by_controller = {}

    for controller, _, _, _ in CONTROLLERS:
        values = np.array(
            [
                [
                    float(rows_by_key[(mass, controller)][key]) * scale
                    for key, _, _, scale in METRICS
                ]
                for mass in PAYLOAD_MASSES
            ],
            dtype=float,
        )

        if not np.all(np.isfinite(values)):
            raise ValueError("Plot metrics must be finite.")

        values_by_controller[controller] = values

    figure, axes = plt.subplots(
        1,
        3,
        figsize=(15, 4.8),
        sharex=True,
        layout="constrained",
    )

    for index, (_, title, ylabel, _) in enumerate(METRICS):
        axis = axes[index]

        for controller, label, color, marker in CONTROLLERS:
            axis.plot(
                PAYLOAD_MASSES,
                values_by_controller[controller][:, index],
                color=color,
                marker=marker,
                linewidth=1.6,
                markersize=5,
                label=label,
            )

        axis.set_title(title)
        axis.set_xlabel("Payload mass [kg]")
        axis.set_ylabel(ylabel)
        axis.set_xticks(PAYLOAD_MASSES)
        axis.set_xlim(-0.03, 1.03)
        axis.grid(True, alpha=0.25)
        axis.legend(fontsize=8, loc="best")

    axes[0].set_ylim(bottom=0.0)
    axes[1].set_ylim(bottom=0.0)
    axes[2].set_ylim(-2.0, 102.0)

    figure.suptitle("Payload Benchmark: Frozen Gains, Unloaded Controller Models")

    destination = directory / "payload_comparison.png"
    figure.savefig(destination, dpi=200)
    plt.close(figure)

    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "result_dir",
        type=Path,
        help="Directory containing payload_metrics.csv.",
    )
    arguments = parser.parse_args()

    destination = plot_payload_benchmark(arguments.result_dir)
    print(f"Saved: {destination}")


if __name__ == "__main__":
    main()
