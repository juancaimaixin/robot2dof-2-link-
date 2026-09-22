from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle

from robot2dof.kinematics import forward_kinematics, inverse_kinematics
from robot2dof.parameters import RobotParams


def joint_positions(
    q: tuple[float, float],
    params: RobotParams,
) -> np.ndarray:
    """Return base, elbow, and end-effector positions."""

    q1, _ = q

    elbow = np.array(
        [
            params.l1 * np.cos(q1),
            params.l1 * np.sin(q1),
        ]
    )
    end_effector = np.array(forward_kinematics(q, params))

    return np.vstack(([0.0, 0.0], elbow, end_effector))


def main() -> None:
    params = RobotParams()
    target = (0.50, 0.35)

    minimum_radius = abs(params.l1 - params.l2)
    maximum_radius = params.l1 + params.l2

    figure, axes = plt.subplots(figsize=(8, 8))

    outer_workspace = Circle(
        (0.0, 0.0),
        maximum_radius,
        facecolor="tab:blue",
        edgecolor="tab:blue",
        alpha=0.12,
        label="Reachable workspace",
    )
    inner_hole = Circle(
        (0.0, 0.0),
        minimum_radius,
        facecolor="white",
        edgecolor="tab:blue",
        linestyle="--",
    )

    axes.add_patch(outer_workspace)
    axes.add_patch(inner_hole)

    branch_colors = {
        "elbow_up": "tab:orange",
        "elbow_down": "tab:green",
    }

    for branch, color in branch_colors.items():
        joint_angles = inverse_kinematics(target, params, branch)
        positions = joint_positions(joint_angles, params)
        angles_degrees = np.degrees(joint_angles)

        axes.plot(
            positions[:, 0],
            positions[:, 1],
            marker="o",
            linewidth=3,
            color=color,
            label=(
                f"{branch}: q1={angles_degrees[0]:.1f}°, q2={angles_degrees[1]:.1f}°"
            ),
        )

    axes.scatter(
        target[0],
        target[1],
        marker="*",
        s=220,
        color="red",
        label="Target",
        zorder=5,
    )
    axes.scatter(0.0, 0.0, color="black", s=60, label="Base", zorder=5)

    plot_limit = maximum_radius + 0.10
    axes.set_xlim(-plot_limit, plot_limit)
    axes.set_ylim(-plot_limit, plot_limit)
    axes.set_aspect("equal")
    axes.set_xlabel("x [m]")
    axes.set_ylabel("y [m]")
    axes.set_title("2-DOF Workspace and Inverse-Kinematics Branches")
    axes.grid(True, alpha=0.3)
    axes.legend(loc="upper right")

    output_path = Path("results") / "ik_workspace_branches.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    figure.savefig(output_path, dpi=200, bbox_inches="tight")
    print(f"Saved figure to: {output_path.resolve()}")

    plt.show()


if __name__ == "__main__":
    main()
