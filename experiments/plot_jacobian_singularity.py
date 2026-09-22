from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from robot2dof.kinematics import jacobian
from robot2dof.parameters import RobotParams


def main() -> None:
    params = RobotParams()

    q2_values = np.linspace(
        -np.pi,
        np.pi,
        721,
    )

    determinants = np.array(
        [np.linalg.det(jacobian((0.0, q2), params)) for q2 in q2_values]
    )

    figure, axes = plt.subplots(
        figsize=(8, 5),
    )

    axes.plot(
        np.degrees(q2_values),
        determinants,
        linewidth=2.5,
        color="tab:blue",
        label="det(J)",
    )

    axes.axhline(
        0.0,
        color="black",
        linewidth=1.0,
    )

    axes.scatter(
        [-180.0, 0.0, 180.0],
        [0.0, 0.0, 0.0],
        color="tab:red",
        marker="x",
        s=100,
        label="Singular configuration",
        zorder=5,
    )

    axes.set_xticks([-180, -90, 0, 90, 180])
    axes.set_xlabel("q2 [degree]")
    axes.set_ylabel("det(J) [m²]")
    axes.set_title("2-DOF Jacobian Determinant")
    axes.grid(True, alpha=0.3)
    axes.legend()

    output_path = Path("results") / "jacobian_determinant.png"
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

    plt.show()


if __name__ == "__main__":
    main()
