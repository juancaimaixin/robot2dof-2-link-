"""Compare absolute tracking error with deviation from the nominal trajectory.

This is a supplementary learning analysis, not a change to the frozen benchmark.
"""

import argparse
import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import yaml

from robot2dof.dynamics import mass_matrix
from robot2dof.metrics import compute_recovery_time
from robot2dof.parameters import RobotParams

CONTROLLERS = (
    ("pid", "PID", "tab:blue"),
    ("pid_gravity", "PID + Gravity", "tab:orange"),
    ("computed_torque", "Computed Torque", "tab:green"),
)


def analyze(disturbance_dir: Path, nominal_dir: Path, output_dir: Path) -> None:
    rows = []
    fig, axes = plt.subplots(3, 2, figsize=(14, 10), layout="constrained")
    for index, (name, label, color) in enumerate(CONTROLLERS):
        with (
            np.load(
                disturbance_dir / f"{name}_disturbance.npz", allow_pickle=False
            ) as perturbed,
            np.load(nominal_dir / f"{name}.npz", allow_pickle=False) as nominal,
        ):
            time = perturbed["time_values"]
            np.testing.assert_array_equal(time, nominal["time_values"])
            reference = perturbed["reference_end_effector_position_history"]
            np.testing.assert_array_equal(
                reference, nominal["reference_end_effector_position_history"]
            )
            nominal_error = np.linalg.norm(
                reference - nominal["end_effector_position_history"], axis=1
            )
            tracking_error = np.linalg.norm(
                reference - perturbed["end_effector_position_history"], axis=1
            )
            deviation = np.linalg.norm(
                perturbed["end_effector_position_history"]
                - nominal["end_effector_position_history"],
                axis=1,
            )
            before = time <= 4.5
            np.testing.assert_array_equal(
                perturbed["state_history"][before], nominal["state_history"][before]
            )
            onset = int(np.searchsorted(time, 4.5))
            q = perturbed["state_history"][onset, :2]
            with (disturbance_dir / f"{name}_disturbance.yaml").open(
                encoding="utf-8"
            ) as source:
                config = yaml.safe_load(source)
            inertia = mass_matrix(q, RobotParams(**config["actual_model"]))
            proportional = np.diag(config["controller"]["gains"]["kp"])
            if name == "computed_torque":
                proportional = inertia @ proportional
            torque_for_error = proportional @ np.array([0.0, np.pi / 180])
            acceleration = np.linalg.solve(
                inertia, perturbed["external_torque_history"][onset]
            )

        absolute_delay = compute_recovery_time(time, tracking_error)
        nominal_delay = compute_recovery_time(time, nominal_error)
        deviation_delay = compute_recovery_time(time, deviation)
        rows.append(
            {
                "controller": name,
                "tracking_peak_after_4_5_mm": float(
                    tracking_error[onset:].max() * 1000
                ),
                "formal_recovery_delay_s": absolute_delay,
                "nominal_same_threshold_delay_s": nominal_delay,
                "deviation_from_nominal_peak_mm": float(deviation[onset:].max() * 1000),
                "deviation_same_threshold_delay_s": deviation_delay,
                "proportional_joint1_torque_for_e2_1deg_nm": float(torque_for_error[0]),
                "proportional_joint2_torque_for_e2_1deg_nm": float(torque_for_error[1]),
                "instantaneous_external_acceleration_joint1_rad_s2": float(
                    acceleration[0]
                ),
                "instantaneous_external_acceleration_joint2_rad_s2": float(
                    acceleration[1]
                ),
            }
        )
        left, right = axes[index]
        left.plot(time, tracking_error * 1000, color=color, label="With disturbance")
        left.plot(
            time,
            nominal_error * 1000,
            color=color,
            linestyle="--",
            label="Nominal (no disturbance)",
        )
        right.plot(
            time,
            deviation * 1000,
            color=color,
            label="Distance between the two trajectories",
        )
        maximum = (
            max(
                tracking_error[onset:].max(),
                nominal_error[onset:].max(),
                deviation.max(),
            )
            * 1000
        )
        for axis in (left, right):
            axis.axhline(
                10, color="black", linestyle=":", linewidth=1, label="10 mm threshold"
            )
            axis.axvspan(4.5, 4.7, color="gray", alpha=0.15)
            axis.set_ylim(0, maximum * 1.22)
            axis.set_ylabel("Distance [mm]")
            axis.set_xlabel("Time [s]")
            axis.grid(True, alpha=0.25)
            axis.legend(fontsize=8)
        left.set_xlim(4.3, 8)
        right.set_xlim(4.3, 5.8)
        left.set_title(f"{label} | distance to reference")
        right.set_title(f"{label} | extra deviation from nominal")
        for axis, delay in ((left, absolute_delay), (right, deviation_delay)):
            if delay is not None:
                first = 4.7 + delay
                axis.plot(
                    [first, first + 0.5],
                    [1.5, 1.5],
                    color="black",
                    linewidth=4,
                    solid_capstyle="butt",
                )
                axis.text(
                    0.98,
                    0.68,
                    f"First qualifying 0.5 s window:\n{first:.3f}-{first + 0.5:.3f} s",
                    transform=axis.transAxes,
                    fontsize=9,
                    ha="right",
                )
    fig.suptitle(
        "Tracking accuracy and disturbance rejection are different measurements",
        fontsize=14,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        fig.savefig(output_dir / "nominal_vs_disturbance.png", dpi=180)
    finally:
        plt.close(fig)
    with (output_dir / "diagnostics.csv").open(
        "w", encoding="utf-8", newline=""
    ) as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Saved supplementary analysis: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("disturbance_dir", type=Path)
    parser.add_argument("nominal_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    analyze(args.disturbance_dir, args.nominal_dir, args.output_dir)


if __name__ == "__main__":
    main()
