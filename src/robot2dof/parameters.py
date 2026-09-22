from dataclasses import dataclass


@dataclass(frozen=True)
class RobotParams:
    """Physical parameters of the planar 2-DOF robot arm."""

    l1: float = 0.50
    l2: float = 0.40

    m1: float = 2.00
    m2: float = 1.50

    lc1: float = 0.25
    lc2: float = 0.20

    I1: float = 2.00 * 0.50**2 / 12.0
    I2: float = 1.50 * 0.40**2 / 12.0

    g: float = 9.81

    # Point mass fixed at the end effector, in kilograms.
    payload_mass: float = 0.0
