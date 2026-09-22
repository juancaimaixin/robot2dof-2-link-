import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml

CONTROLLERS = (
    ("pid", "PID", "tab:blue"),
    ("pid_gravity", "PID + Gravity", "tab:orange"),
    ("computed_torque", "Computed Torque", "tab:green"),
)


def plot_nominal_benchmark(result_dir: str | Path) -> Path:
    """Plot saved nominal histories without rerunning simulations."""

    directory = Path(result_dir).resolve()

    with (directory / "pid.yaml").open(encoding="utf-8") as source:
        configuration = yaml.safe_load(source)

    waypoint_times = configuration["trajectory"]["waypoint_times"]
    torque_limit = configuration["actuator"]["limit_nm"]

    histories = {}
    for controller, _, _ in CONTROLLERS:
        with np.load(
            directory / f"{controller}.npz",
            allow_pickle=False,
        ) as archive:
            histories[controller] = {
                name: archive[name]
                for name in (
                    "time_values",
                    "state_history",
                    "reference_position_history",
                    "applied_torque_history",
                )
            }

    time = histories["pid"]["time_values"]
    reference = histories["pid"]["reference_position_history"]

    for history in histories.values():
        if not np.array_equal(history["time_values"], time):
            raise ValueError("Controllers must use the same time grid.")
        if not np.array_equal(history["reference_position_history"], reference):
            raise ValueError("Controllers must use the same reference.")

    figure, axes = plt.subplots(
        3,
        2,
        figsize=(13, 10),
        sharex=True,
        layout="constrained",
    )

    for joint in range(2):
        axes[0, joint].plot(
            time,
            np.degrees(reference[:, joint]),
            color="black",
            linestyle="--",
            linewidth=1.8,
            label="Reference",
            zorder=4,
        )

        for controller, label, color in CONTROLLERS:
            history = histories[controller]
            position = history["state_history"][:, joint]
            error = reference[:, joint] - position
            torque = history["applied_torque_history"][:, joint]

            axes[0, joint].plot(
                time,
                np.degrees(position),
                color=color,
                linewidth=1.2,
                label=label,
            )
            axes[1, joint].plot(
                time,
                np.degrees(error),
                color=color,
                linewidth=1.2,
                label=label,
            )
            axes[2, joint].stairs(
                torque[:-1],
                time,
                baseline=None,
                color=color,
                linewidth=1.2,
                label=label,
            )

        axes[0, joint].set_title(f"Joint {joint + 1}")
        axes[0, joint].set_ylabel("Position [deg]")
        axes[1, joint].set_ylabel("Reference - actual [deg]")
        axes[2, joint].set_ylabel("Applied torque [N m]")
        axes[2, joint].set_xlabel("Time [s]")

        axes[1, joint].axhline(0.0, color="black", linewidth=0.7, alpha=0.5)

        for limit in (-torque_limit, torque_limit):
            axes[2, joint].axhline(
                limit,
                color="tab:red",
                linestyle=":",
                linewidth=1.2,
                label="Torque limits" if limit > 0 else "_nolegend_",
            )

        axes[2, joint].set_ylim(-1.1 * torque_limit, 1.1 * torque_limit)

    for axis in axes.flat:
        axis.set_xlim(time[0], time[-1])
        axis.set_xticks(waypoint_times)
        axis.grid(True, alpha=0.25)
        axis.legend(fontsize=8, loc="best")

    figure.suptitle("Nominal Benchmark: Frozen Controller Gains")

    destination = directory / "nominal_comparison.png"
    figure.savefig(destination, dpi=200)
    plt.close(figure)

    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "result_dir",
        type=Path,
        help="Directory containing the saved nominal results.",
    )
    arguments = parser.parse_args()

    destination = plot_nominal_benchmark(arguments.result_dir)
    print(f"Saved: {destination}")


if __name__ == "__main__":
    main()
