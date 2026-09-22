from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class State:
    """Joint position and velocity state."""

    q: Sequence[float]
    q_dot: Sequence[float]
