"""Render the README schematic using the model's relative joint angles."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Polygon

from robot2dof.kinematics import forward_kinematics
from robot2dof.parameters import RobotParams


def main() -> None:
    params = RobotParams()
    q1, q2 = np.deg2rad([32.0, 58.0])
    base = np.zeros(2)
    elbow = params.l1 * np.array([np.cos(q1), np.sin(q1)])
    tip = np.array(forward_kinematics((q1, q2), params))
    blue, teal, ink, grey = "#2563eb", "#0f766e", "#243247", "#94a3b8"

    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 13}):
        fig, ax = plt.subplots(figsize=(10, 7), facecolor="white")
        ax.set_aspect("equal")
        ax.set_xlim(-0.16, 0.85)
        ax.set_ylim(-0.12, 0.80)
        ax.axis("off")

        for end, label, offset in [
            ((0.77, 0), "$x$", (0.02, -0.005)),
            ((0, 0.70), "$y$", (-0.035, 0.01)),
        ]:
            ax.annotate(
                "",
                xy=end,
                xytext=base,
                arrowprops={"arrowstyle": "->", "color": grey, "lw": 1.6},
            )
            ax.text(end[0] + offset[0], end[1] + offset[1], label, color=ink)

        ax.add_patch(
            Polygon(
                [(-0.045, -0.057), (0.045, -0.057), (0, 0)],
                facecolor="#e2e8f0",
                edgecolor=ink,
                lw=1.4,
            )
        )
        ax.plot([-0.07, 0.07], [-0.06, -0.06], color=ink, lw=2)
        ax.text(0, -0.097, "Fixed base", ha="center", color=ink, fontsize=11)

        direction = np.array([np.cos(q1), np.sin(q1)])
        extension = elbow + 0.24 * direction
        ax.plot(
            [elbow[0], extension[0]],
            [elbow[1], extension[1]],
            color=grey,
            lw=1.5,
            linestyle=(0, (4, 4)),
        )
        ax.text(
            extension[0] + 0.018,
            extension[1] - 0.018,
            "Link 1\nextension",
            color="#64748b",
            fontsize=10,
            va="center",
        )

        for start, end, color in [(base, elbow, blue), (elbow, tip, teal)]:
            ax.plot(
                [start[0], end[0]],
                [start[1], end[1]],
                color=color,
                lw=14,
                solid_capstyle="round",
                zorder=3,
            )
        for joint in [base, elbow]:
            ax.add_patch(Circle(joint, 0.021, fc="white", ec=ink, lw=2, zorder=5))
            ax.add_patch(Circle(joint, 0.006, fc=ink, zorder=6))
        ax.add_patch(Circle(tip, 0.015, fc="white", ec=teal, lw=2.5, zorder=5))

        def angle(center, start, stop, radius, label, color):
            theta = np.linspace(start, stop, 80)
            points = center + radius * np.column_stack((np.cos(theta), np.sin(theta)))
            ax.plot(points[:, 0], points[:, 1], color=color, lw=2, zorder=7)
            ax.annotate(
                "",
                xy=points[-1],
                xytext=points[-7],
                zorder=8,
                arrowprops={"arrowstyle": "-|>", "color": color, "lw": 2},
            )
            mid = (start + stop) / 2
            pos = center + (radius + 0.04) * np.array([np.cos(mid), np.sin(mid)])
            ax.text(*pos, label, color=color, fontsize=23, ha="center", va="center")

        angle(base, 0, q1, 0.14, "$q_1$", blue)
        angle(elbow, q1, q1 + q2, 0.13, "$q_2$", teal)
        ax.text(0.15, 0.22, "Link 1\n$l_1 = 0.50$ m", color=blue, ha="center")
        ax.text(elbow[0] - 0.05, 0.48, "Link 2\n$l_2 = 0.40$ m", color=teal, ha="right")
        ax.text(
            tip[0] + 0.045, tip[1], "End effector\n$(x_e, y_e)$", color=ink, va="center"
        )
        ax.text(
            elbow[0] + 0.03, elbow[1] - 0.06, "Elbow", color=ink, ha="left", fontsize=11
        )
        ax.annotate(
            "",
            xy=(0.73, 0.48),
            xytext=(0.73, 0.66),
            arrowprops={"arrowstyle": "-|>", "color": ink, "lw": 2},
        )
        ax.text(0.77, 0.565, "$g$", color=ink, fontsize=20, va="center")
        ax.text(
            -0.115, 0.79, "PLANAR TWO-LINK ARM", color=ink, fontsize=15, weight="bold"
        )
        ax.text(
            -0.115,
            0.755,
            "Vertical plane  |  Positive angles: counterclockwise",
            color="#64748b",
            fontsize=11,
        )

        output = Path(__file__).resolve().parents[1] / "docs" / "images"
        output.mkdir(parents=True, exist_ok=True)
        fig.savefig(
            output / "two_link_arm.png", dpi=180, bbox_inches="tight", pad_inches=0.2
        )
        plt.close(fig)


if __name__ == "__main__":
    main()
