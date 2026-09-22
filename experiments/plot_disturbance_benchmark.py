"""Plot saved disturbance histories and recovery outcomes without simulation."""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml

from robot2dof.metrics import compute_recovery_time

CONTROLLERS = (
    ("pid", "PID", "tab:blue"),
    ("pid_gravity", "PID + Gravity", "tab:orange"),
    ("computed_torque", "Computed Torque", "tab:green"),
)


def plot_disturbance_benchmark(result_dir: str | Path) -> Path:
    """Read all inputs and validate recovery labels before creating a figure."""
    directory = Path(result_dir).resolve()
    with (directory / "disturbance_metrics.csv").open(
        encoding="utf-8", newline=""
    ) as source:
        rows = list(csv.DictReader(source))
    by_controller = {row["controller"]: row for row in rows}
    if len(rows) != 3 or set(by_controller) != {item[0] for item in CONTROLLERS}:
        raise ValueError("Expected exactly one summary row per controller.")
    with (directory / "pid_disturbance.yaml").open(encoding="utf-8") as source:
        configuration = yaml.safe_load(source)
    pulse = configuration["disturbance"]
    recovery_rule = configuration["metrics"]["recovery_time"]
    start, end = pulse["start_time_s"], pulse["end_time_s"]
    threshold = recovery_rule["threshold_m"]
    hold = recovery_rule["hold_duration_s"]
    histories = {}
    recoveries = {}
    for controller, _, _ in CONTROLLERS:
        row = by_controller[controller]
        for key, value in row.items():
            if key not in ("controller", "recovered", "recovery_time_s"):
                if not np.isfinite(float(value)):
                    raise ValueError("Plot metrics must be finite.")
        if row["recovered"] not in ("True", "False"):
            raise ValueError("Invalid recovered flag.")
        recovery = (
            None if row["recovery_time_s"] == "" else float(row["recovery_time_s"])
        )
        if (recovery is not None) != (row["recovered"] == "True"):
            raise ValueError("Recovery flag and value disagree.")
        if recovery is not None and (not np.isfinite(recovery) or recovery < 0):
            raise ValueError("Recovery delay must be finite and non-negative.")
        with np.load(
            directory / f"{controller}_disturbance.npz", allow_pickle=False
        ) as archive:
            history = {
                key: archive[key]
                for key in (
                    "time_values",
                    "state_history",
                    "reference_position_history",
                    "end_effector_error_history_m",
                    "external_torque_history",
                )
            }
        time = history["time_values"]
        if time.ndim != 1 or time.size < 2:
            raise ValueError("Invalid saved time grid.")
        shapes = {
            "state_history": (time.size, 4),
            "reference_position_history": (time.size, 2),
            "end_effector_error_history_m": (time.size,),
            "external_torque_history": (time.size, 2),
        }
        for key, values in history.items():
            if not np.all(np.isfinite(values)) or (
                key in shapes and values.shape != shapes[key]
            ):
                raise ValueError(f"Invalid saved history: {key}")
        measured = compute_recovery_time(
            time,
            history["end_effector_error_history_m"],
            disturbance_end_time=end,
            threshold_m=threshold,
            hold_duration=hold,
        )
        if (measured is None) != (recovery is None):
            raise ValueError("Saved recovery disagrees with error history.")
        if measured is not None and not np.isclose(
            measured, recovery, rtol=0, atol=1e-12
        ):
            raise ValueError("Saved recovery delay disagrees with error history.")
        histories[controller] = history
        recoveries[controller] = recovery
    time = histories["pid"]["time_values"]
    for history in histories.values():
        if not np.array_equal(history["time_values"], time):
            raise ValueError("Controllers must share the same time grid.")
        if not np.array_equal(
            history["reference_position_history"],
            histories["pid"]["reference_position_history"],
        ):
            raise ValueError("Controllers must share the same reference.")

    fig, axes = plt.subplots(3, 2, figsize=(14, 11), layout="constrained")
    full, zoom, q1, q2, external, recovery_axis = axes.flat
    zoom_end = min(
        time[-1],
        max(
            [end + 1.5]
            + [
                end + delay + hold + 0.1
                for delay in recoveries.values()
                if delay is not None
            ],
        ),
    )
    for controller, label, color in CONTROLLERS:
        history = histories[controller]
        error = history["end_effector_error_history_m"]
        for axis in (full, zoom):
            axis.plot(time, error * 1000, color=color, label=label, linewidth=1.4)
        joint_error = np.degrees(
            history["reference_position_history"] - history["state_history"][:, :2]
        )
        for joint, axis in enumerate((q1, q2)):
            axis.plot(
                time, joint_error[:, joint], color=color, label=label, linewidth=1.4
            )
        for joint, style in enumerate(("-", "--")):
            external.plot(
                time,
                history["external_torque_history"][:, joint],
                color=color,
                linestyle=style,
                label=f"{label}: joint {joint + 1}",
                linewidth=1.3,
            )
    full.set_title("End-effector tracking error | full trajectory")
    zoom.set_title("Disturbance response | detail")
    full.set_xlim(time[0], time[-1])
    for axis in (full, zoom):
        axis.axhline(
            threshold * 1000,
            color="black",
            linestyle=":",
            label="Recovery threshold (10 mm)",
        )
        axis.set_ylabel("End-effector error [mm]")
        axis.set_ylim(bottom=0)
        axis.legend(fontsize=8)
    for joint, axis in enumerate((q1, q2), start=1):
        axis.set_title(f"Joint {joint} tracking error | detail")
        axis.set_ylabel("Reference - actual [deg]")
        axis.legend(fontsize=8)
    for axis in (zoom, q1, q2):
        axis.set_xlim(max(time[0], start - 0.2), zoom_end)
    external.set_title("External joint torque | sampled actual posture")
    external.set_ylabel("External torque [N m]")
    external.set_xlim(start - 0.05, end + 0.05)
    external.legend(fontsize=8, ncol=2)
    for axis in (full, zoom, q1, q2, external):
        axis.axvspan(start, end, color="gray", alpha=0.16)
        axis.set_xlabel("Time [s]")
        axis.grid(True, alpha=0.25)

    max_delay = max(
        [delay for delay in recoveries.values() if delay is not None] + [0.1]
    )
    for index, (controller, _, color) in enumerate(CONTROLLERS):
        delay = recoveries[controller]
        if delay is None:
            recovery_axis.text(
                0.03 * max_delay,
                index,
                f"Not confirmed by {time[-1]:g} s",
                va="center",
                color=color,
            )
        else:
            recovery_axis.barh(index, delay, color=color, alpha=0.85, height=0.5)
            recovery_axis.text(
                delay + 0.03 * max_delay,
                index,
                f"{delay:.3f} s",
                va="center",
                color=color,
            )
    recovery_axis.set_yticks(range(3), [label for _, label, _ in CONTROLLERS])
    recovery_axis.set_ylim(2.6, -0.6)
    recovery_axis.set_xlim(0, max_delay * 1.7)
    recovery_axis.set_title("Recovery delay from pulse end")
    recovery_axis.set_xlabel("Delay [s] | error <= 10 mm for 0.5 s")
    recovery_axis.grid(True, axis="x", alpha=0.25)
    fig.suptitle(
        "End-effector disturbance: +10 N along base x, 4.5-4.7 s | frozen gains",
        fontsize=14,
    )
    destination = directory / "disturbance_comparison.png"
    try:
        fig.savefig(destination, dpi=200)
    finally:
        plt.close(fig)
    return destination


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir", type=Path)
    args = parser.parse_args()
    print(f"Saved: {plot_disturbance_benchmark(args.result_dir)}")


if __name__ == "__main__":
    main()
