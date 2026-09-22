from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from robot2dof.kinematics import forward_kinematics
from robot2dof.parameters import RobotParams
from robot2dof.trajectory import sample_quintic_trajectory


def main() -> None:
    waypoint_times = np.array(
        [
            0.0,
            2.0,
            4.0,
            6.0,
            8.0,
        ]
    )

    waypoint_positions = np.radians(
        np.array(
            [
                [-20.0, 50.0],
                [35.0, 25.0],
                [65.0, -35.0],
                [10.0, 55.0],
                [-30.0, 20.0],
            ]
        )
    )

    time_values = np.linspace(
        waypoint_times[0],
        waypoint_times[-1],
        8001,
    )

    references = [
        sample_quintic_trajectory(
            time=float(time),
            waypoint_times=waypoint_times,
            waypoint_positions=waypoint_positions,
        )
        for time in time_values
    ]

    position_history = np.array([reference.q_ref for reference in references])
    velocity_history = np.array([reference.q_dot_ref for reference in references])
    acceleration_history = np.array([reference.q_ddot_ref for reference in references])

    histories = (
        np.degrees(position_history),
        np.degrees(velocity_history),
        np.degrees(acceleration_history),
    )

    y_labels = (
        "Position [degree]",
        "Velocity [degree/s]",
        "Acceleration [degree/s²]",
    )

    colors = (
        "tab:blue",
        "tab:orange",
    )

    joint_labels = (
        "q1 reference",
        "q2 reference",
    )

    figure, axes = plt.subplots(
        3,
        1,
        figsize=(10, 9),
        sharex=True,
    )

    for axis, history, y_label in zip(
        axes,
        histories,
        y_labels,
        strict=True,
    ):
        for joint_index in range(2):
            axis.plot(
                time_values,
                history[:, joint_index],
                color=colors[joint_index],
                linewidth=2.0,
                label=joint_labels[joint_index],
            )

        for waypoint_time in waypoint_times:
            axis.axvline(
                waypoint_time,
                color="black",
                linewidth=0.8,
                linestyle="--",
                alpha=0.25,
            )

        axis.axhline(
            0.0,
            color="black",
            linewidth=0.8,
            alpha=0.4,
        )
        axis.set_ylabel(y_label)
        axis.grid(
            True,
            alpha=0.3,
        )
        axis.legend()

    axes[0].scatter(
        waypoint_times,
        np.degrees(waypoint_positions[:, 0]),
        color=colors[0],
        marker="o",
        s=45,
        zorder=5,
    )
    axes[0].scatter(
        waypoint_times,
        np.degrees(waypoint_positions[:, 1]),
        color=colors[1],
        marker="o",
        s=45,
        zorder=5,
    )

    axes[-1].set_xlabel("Time [s]")

    figure.suptitle("Stop-to-Stop Multi-Segment Quintic Trajectory")
    figure.tight_layout()

    output_path = Path("results") / "quintic_trajectory.png"
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    print(f"Saved figure to: {output_path.resolve()}")

    params = RobotParams()

    animation_output_path = Path("results") / "quintic_trajectory_animation.gif"

    save_arm_animation(
        time_values=time_values,
        position_history=position_history,
        params=params,
        output_path=animation_output_path,
    )

    print(f"Saved animation to: {animation_output_path.resolve()}")

    plt.show()


def save_arm_animation(
    time_values: np.ndarray,
    position_history: np.ndarray,
    params: RobotParams,
    output_path: Path,
) -> None:
    """Save a physically scaled animation of the reference motion."""

    frames_per_second = 25
    duration = float(time_values[-1] - time_values[0])
    frame_count = round(duration * frames_per_second) + 1

    frame_indices = np.linspace(
        0,
        time_values.size - 1,
        frame_count,
        dtype=int,
    )

    animation_times = time_values[frame_indices]
    animation_positions = position_history[frame_indices]

    elbow_history = np.column_stack(
        (
            params.l1 * np.cos(animation_positions[:, 0]),
            params.l1 * np.sin(animation_positions[:, 0]),
        )
    )

    end_effector_history = np.array(
        [
            forward_kinematics(
                joint_position,
                params,
            )
            for joint_position in animation_positions
        ]
    )

    figure, axis = plt.subplots(
        figsize=(7, 7),
    )

    workspace_limit = 1.1 * (params.l1 + params.l2)

    axis.set_xlim(
        -workspace_limit,
        workspace_limit,
    )
    axis.set_ylim(
        -workspace_limit,
        workspace_limit,
    )
    axis.set_aspect(
        "equal",
        adjustable="box",
    )

    axis.axhline(
        0.0,
        color="black",
        linewidth=0.8,
        alpha=0.4,
    )
    axis.axvline(
        0.0,
        color="black",
        linewidth=0.8,
        alpha=0.4,
    )

    axis.plot(
        end_effector_history[:, 0],
        end_effector_history[:, 1],
        color="0.75",
        linewidth=1.5,
        linestyle="--",
        label="Planned end-effector path",
    )

    (arm_line,) = axis.plot(
        [],
        [],
        color="tab:blue",
        linewidth=4.0,
        marker="o",
        markersize=9,
        label="Robot arm",
    )

    (trail_line,) = axis.plot(
        [],
        [],
        color="tab:red",
        linewidth=2.0,
        label="Travelled path",
    )

    time_text = axis.text(
        0.03,
        0.95,
        "",
        transform=axis.transAxes,
    )

    joint_text = axis.text(
        0.03,
        0.89,
        "",
        transform=axis.transAxes,
    )

    axis.set_xlabel("x [m]")
    axis.set_ylabel("y [m]")
    axis.set_title("2-DOF Robot Reference Motion")
    axis.grid(
        True,
        alpha=0.3,
    )
    axis.legend(
        loc="lower right",
    )

    def update(frame_index: int):
        elbow_x, elbow_y = elbow_history[frame_index]
        end_x, end_y = end_effector_history[frame_index]

        arm_line.set_data(
            [
                0.0,
                elbow_x,
                end_x,
            ],
            [
                0.0,
                elbow_y,
                end_y,
            ],
        )

        trail_line.set_data(
            end_effector_history[: frame_index + 1, 0],
            end_effector_history[: frame_index + 1, 1],
        )

        q1, q2 = np.degrees(animation_positions[frame_index])

        time_text.set_text(f"Time: {animation_times[frame_index]:.2f} s")
        joint_text.set_text(f"q1: {q1:.1f}°, q2: {q2:.1f}°")

        return (
            arm_line,
            trail_line,
            time_text,
            joint_text,
        )

    animation = FuncAnimation(
        figure,
        update,
        frames=frame_count,
        interval=1000.0 / frames_per_second,
        blit=True,
        repeat=True,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    animation.save(
        output_path,
        writer=PillowWriter(
            fps=frames_per_second,
        ),
        dpi=120,
    )

    plt.close(figure)


if __name__ == "__main__":
    main()
