import sympy as sp


def main() -> None:
    q1, q2 = sp.symbols(
        "q1 q2",
        real=True,
    )
    q1_dot, q2_dot = sp.symbols(
        "q1_dot q2_dot",
        real=True,
    )

    l1, lc1, lc2 = sp.symbols(
        "l1 lc1 lc2",
        positive=True,
    )

    q = sp.Matrix([q1, q2])
    q_dot = sp.Matrix([q1_dot, q2_dot])

    p_c1 = sp.Matrix(
        [
            lc1 * sp.cos(q1),
            lc1 * sp.sin(q1),
        ]
    )

    p_c2 = sp.Matrix(
        [
            l1 * sp.cos(q1) + lc2 * sp.cos(q1 + q2),
            l1 * sp.sin(q1) + lc2 * sp.sin(q1 + q2),
        ]
    )

    v_c1 = p_c1.jacobian(q) @ q_dot
    v_c2 = p_c2.jacobian(q) @ q_dot

    expected_v_c1 = sp.Matrix(
        [
            -lc1 * sp.sin(q1) * q1_dot,
            lc1 * sp.cos(q1) * q1_dot,
        ]
    )

    expected_v_c2 = sp.Matrix(
        [
            -l1 * sp.sin(q1) * q1_dot - lc2 * sp.sin(q1 + q2) * (q1_dot + q2_dot),
            l1 * sp.cos(q1) * q1_dot + lc2 * sp.cos(q1 + q2) * (q1_dot + q2_dot),
        ]
    )

    assert (v_c1 - expected_v_c1).applyfunc(sp.simplify) == sp.zeros(2, 1)

    assert (v_c2 - expected_v_c2).applyfunc(sp.simplify) == sp.zeros(2, 1)

    m1, m2, I1, I2 = sp.symbols(
        "m1 m2 I1 I2",
        positive=True,
    )

    half = sp.Rational(1, 2)

    kinetic_energy = (
        half * m1 * v_c1.dot(v_c1)
        + half * I1 * q1_dot**2
        + half * m2 * v_c2.dot(v_c2)
        + half * I2 * (q1_dot + q2_dot) ** 2
    )

    expected_kinetic_energy = (
        half * (m1 * lc1**2 + I1) * q1_dot**2
        + half
        * m2
        * (
            l1**2 * q1_dot**2
            + lc2**2 * (q1_dot + q2_dot) ** 2
            + 2 * l1 * lc2 * sp.cos(q2) * q1_dot * (q1_dot + q2_dot)
        )
        + half * I2 * (q1_dot + q2_dot) ** 2
    )

    assert sp.simplify(sp.trigsimp(kinetic_energy - expected_kinetic_energy)) == 0

    g = sp.symbols(
        "g",
        positive=True,
    )

    potential_energy = m1 * g * p_c1[1] + m2 * g * p_c2[1]

    expected_potential_energy = g * (
        (m1 * lc1 + m2 * l1) * sp.sin(q1) + m2 * lc2 * sp.sin(q1 + q2)
    )

    assert sp.simplify(potential_energy - expected_potential_energy) == 0

    mass_matrix = sp.hessian(
        kinetic_energy,
        q_dot,
    )

    expected_mass_matrix = sp.Matrix(
        [
            [
                I1
                + I2
                + m1 * lc1**2
                + m2 * (l1**2 + lc2**2 + 2 * l1 * lc2 * sp.cos(q2)),
                I2 + m2 * (lc2**2 + l1 * lc2 * sp.cos(q2)),
            ],
            [
                I2 + m2 * (lc2**2 + l1 * lc2 * sp.cos(q2)),
                I2 + m2 * lc2**2,
            ],
        ]
    )

    mass_matrix_error = (mass_matrix - expected_mass_matrix).applyfunc(
        lambda expression: sp.simplify(sp.trigsimp(expression))
    )

    assert mass_matrix_error == sp.zeros(2, 2)

    gravity_vector = sp.Matrix(
        [
            sp.diff(potential_energy, q1),
            sp.diff(potential_energy, q2),
        ]
    )

    expected_gravity_vector = sp.Matrix(
        [
            g * ((m1 * lc1 + m2 * l1) * sp.cos(q1) + m2 * lc2 * sp.cos(q1 + q2)),
            g * m2 * lc2 * sp.cos(q1 + q2),
        ]
    )

    gravity_vector_error = (gravity_vector - expected_gravity_vector).applyfunc(
        sp.simplify
    )

    assert gravity_vector_error == sp.zeros(2, 1)

    coriolis_vector = sp.zeros(2, 1)

    for i in range(2):
        for j in range(2):
            for k in range(2):
                christoffel_symbol = half * (
                    sp.diff(mass_matrix[i, j], q[k])
                    + sp.diff(mass_matrix[i, k], q[j])
                    - sp.diff(mass_matrix[j, k], q[i])
                )

                coriolis_vector[i] += christoffel_symbol * q_dot[j] * q_dot[k]

    coriolis_vector = coriolis_vector.applyfunc(
        lambda expression: sp.simplify(sp.trigsimp(expression))
    )

    h = m2 * l1 * lc2 * sp.sin(q2)

    expected_coriolis_vector = sp.Matrix(
        [
            -h * (2 * q1_dot * q2_dot + q2_dot**2),
            h * q1_dot**2,
        ]
    )

    coriolis_vector_error = (coriolis_vector - expected_coriolis_vector).applyfunc(
        sp.simplify
    )

    assert coriolis_vector_error == sp.zeros(2, 1)

    print("SymPy M(q), c(q, q_dot), and G(q) checks passed.")


if __name__ == "__main__":
    main()
