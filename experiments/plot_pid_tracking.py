from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from robot2dof.controllers import PIDGains
from robot2dof.dynamics import gravity_vector
from robot2dof.parameters import RobotParams
from robot2dof.simulation import simulate_pid_trajectory


def main() -> None:
    params = RobotParams()

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

    integral_gain = np.array(
        [
            30.0,
            20.0,
        ]
    )

    gains = PIDGains(
        kp=np.array(
            [
                150.0,
                100.0,
            ]
        ),
        ki=integral_gain,
        kd=np.array(
            [
                25.0,
                15.0,
            ]
        ),
    )

    initial_state = np.concatenate(
        (
            waypoint_positions[0],
            np.zeros(2),
        )
    )

    initial_integral_error = (
        gravity_vector(
            waypoint_positions[0],
            params,
        )
        / integral_gain
    )

    torque_limit = 20.0

    result = simulate_pid_trajectory(
        waypoint_times=waypoint_times,
        waypoint_positions=waypoint_positions,
        initial_state=initial_state,
        initial_integral_error=initial_integral_error,
        gains=gains,
        params=params,
        torque_limit=torque_limit,
        external_tau=np.zeros(2),
        step=0.002,
    )

    reference_position_degrees = np.degrees(result.reference_position_history)
    actual_position_degrees = np.degrees(result.state_history[:, :2])
    position_error_degrees = reference_position_degrees - actual_position_degrees

    figure, axes = plt.subplots(
        3,
        2,
        figsize=(13, 10),
        sharex="col",
    )

    for joint_index in range(2):
        axes[0, joint_index].plot(
            result.time_values,
            reference_position_degrees[:, joint_index],
            color="black",
            linestyle="--",
            linewidth=1.8,
            label="Reference",
        )
        axes[0, joint_index].plot(
            result.time_values,
            actual_position_degrees[:, joint_index],
            color="tab:blue",
            linewidth=1.5,
            label="Actual",
        )
        axes[0, joint_index].scatter(
            waypoint_times,
            np.degrees(waypoint_positions[:, joint_index]),
            color="tab:red",
            s=35,
            zorder=5,
            label="Waypoints",
        )
        axes[0, joint_index].set_title(f"Joint {joint_index + 1}")
        axes[0, joint_index].set_ylabel("Position [degree]")
        axes[0, joint_index].legend()

        axes[1, joint_index].plot(
            result.time_values,
            position_error_degrees[:, joint_index],
            color="tab:orange",
            linewidth=1.5,
            label="Position error",
        )
        axes[1, joint_index].axhline(
            0.0,
            color="black",
            linewidth=0.8,
        )
        axes[1, joint_index].axhline(
            2.5,
            color="tab:red",
            linestyle=":",
            linewidth=1.2,
            label="Error limit",
        )
        axes[1, joint_index].axhline(
            -2.5,
            color="tab:red",
            linestyle=":",
            linewidth=1.2,
        )
        axes[1, joint_index].set_ylabel("Error [degree]")
        axes[1, joint_index].legend()

        axes[2, joint_index].plot(
            result.time_values,
            result.requested_torque_history[:, joint_index],
            color="tab:orange",
            linestyle="--",
            linewidth=1.5,
            label="Requested",
        )
        axes[2, joint_index].plot(
            result.time_values,
            result.applied_torque_history[:, joint_index],
            color="tab:blue",
            linewidth=1.2,
            label="Applied",
        )
        axes[2, joint_index].axhline(
            torque_limit,
            color="tab:red",
            linestyle=":",
            linewidth=1.2,
            label="Torque limit",
        )
        axes[2, joint_index].axhline(
            -torque_limit,
            color="tab:red",
            linestyle=":",
            linewidth=1.2,
        )
        axes[2, joint_index].set_ylabel("Torque [N·m]")
        axes[2, joint_index].set_xlabel("Time [s]")
        axes[2, joint_index].legend()

        for axis in axes[:, joint_index]:
            for waypoint_time in waypoint_times:
                axis.axvline(
                    waypoint_time,
                    color="black",
                    linestyle="--",
                    linewidth=0.7,
                    alpha=0.2,
                )

            axis.grid(
                True,
                alpha=0.3,
            )

    figure.suptitle("Independent-Joint PID Trajectory Tracking")
    figure.tight_layout(
        rect=(
            0.0,
            0.0,
            1.0,
            0.97,
        )
    )

    output_path = Path("results") / "pid_trajectory_tracking.png"
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    figure.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    maximum_error = np.max(
        np.abs(position_error_degrees),
        axis=0,
    )
    final_error = np.abs(position_error_degrees[-1])
    maximum_requested_torque = np.max(
        np.abs(result.requested_torque_history),
        axis=0,
    )

    print(f"Saved figure to: {output_path.resolve()}")
    print(f"Maximum position error [degree]: {maximum_error}")
    print(f"Final position error [degree]: {final_error}")
    print(f"Maximum requested torque [N·m]: {maximum_requested_torque}")
    print(f"Saturated samples: {np.count_nonzero(result.saturation_history)}")

    plt.show()


if __name__ == "__main__":
    main()
