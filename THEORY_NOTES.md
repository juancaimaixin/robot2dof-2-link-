# Two-DOF Robot Arm: Theory Notes

## Homogeneous Transformations

- World and local coordinate frames.
- Frames attached to link 1, link 2, and the end effector.
- Relative and absolute joint angles: link 2's absolute orientation is `q1 + q2`.
- Homogeneous coordinates of a planar point: `[x, y, 1]`.
- Homogeneous representation of a planar direction vector: `[vx, vy, 0]`.
- Planar rotation matrices and translation matrices.
- Structure of a planar rigid-body homogeneous transformation.
- Transform notation from a child frame to its parent frame.
- Multiplication of transformations along a serial arm.
- Two-link chain: `R(q1) @ Tx(l1) @ R(q2) @ Tx(l2)`.
- Matrix multiplication order and noncommutativity; the rightmost matrix acts first on column vectors.
- Link displacement `(l2, 0)` is expressed in link 2's local frame.
- Transforming a local link vector into parent and world frames.
- The end effector is the origin `[0, 0, 1]` in its own frame.
- End-effector position is the translation part of the full transform.
- Forward kinematics by direct trigonometry and by homogeneous transforms.
- Cross-validation with known configurations and a fixed random seed.
- Radians for internal angles and metres for positions and link lengths.

## Inverse Kinematics

- The two-link annular workspace and reachable radial interval.
- The law of cosines gives the second joint angle.
- Two analytic branches of `q2`: elbow-up and elbow-down.
- `atan2` and angle decomposition give `q1`.
- Under these conventions, `q2 < 0` is elbow-up and `q2 > 0` is elbow-down.
- Branches merge at fully extended or folded singular configurations.
- Floating-point clipping of inverse-cosine inputs.
- Angle normalization to `[-pi, pi]`.

## Numerical Tools

- SciPy supplies scientific computing algorithms built on NumPy.
- `scipy.integrate.solve_ivp` provides an independent reference for the custom RK4 robot ODE solver.
- `DOP853` is an adaptive explicit eighth-order Runge-Kutta method; strict tolerances produce a high-accuracy reference.

## State Space and Simulation

- Convert second-order robot dynamics into a first-order state-space ODE.
- State `x = [q, q_dot]` and derivative `x_dot = [q_dot, q_ddot]`.
- `forward_dynamics` computes `q_ddot` from state, motor torque, and external torque.
- A derivative callback lets generic RK4 integrate scalar and vector states.
- Constant-acceleration identity `q(t+h) = q(t) + q_dot(t)h + 0.5*q_ddot*h**2` provides an independent integration check.
- A fixed grid with `N` integration steps has `N + 1` state samples, including both endpoints.
- RK4 global error is `O(h**4)`; in the asymptotic regime, halving the step typically reduces error by about `2**4 = 16`.
- Without actuation, external force, or friction, total mechanical energy `E = T + V` is conserved.
- Maximum energy drift from the initial value over the whole trajectory diagnoses integration error.

## Quintic Trajectories

- Normalized time `s = (t - t0) / (tf - t0)` maps an interval to `[0, 1]`.
- A rest-to-rest quintic satisfies six endpoint constraints on position, velocity, and acceleration.
- Time scaling introduces `1 / T` in the first derivative and `1 / T**2` in the second through the chain rule.
- Matplotlib `FuncAnimation` updates configurations frame by frame; animation duration is approximately `frame_count / FPS`.
- The current GIF shows reference motion, not a controlled plant trajectory with tracking errors.

## PID Control

- Tracking errors: `e = q_ref - q`, `e_dot = q_dot_ref - q_dot`.
- Independent-joint PID computes `tau = Kp * e + Kd * e_dot + Ki * integral(e)` for each joint without explicitly compensating dynamic coupling.
- P corrects current error, D adds damping from error rate, and I accumulates error to remove steady-state bias.
- PID gains map position, velocity, and integrated error to torque. Retain engineering units even though radians are dimensionless in SI.
- The two-DOF plant has four states. Two integral-error states give a sixth-order augmented system; a single-joint approximation is third-order.
- Actuator saturation is external to the controller. Preserve requested torque; a shared `clip` limiter returns applied torque and saturation flags.
- Conditional-integration anti-windup freezes integration when saturation and error would drive torque farther beyond the limit; inward-driving error may still integrate.
- Sampled control computes one command per period; a zero-order hold maintains applied torque while RK4 advances the plant.
- The implementation applies torque using interval-start error, then updates the integral from the same error and saturation state.
- `N` control intervals have `N + 1` samples. The last reference/output sample is recorded without advancing plant or integral states.
- Initializing PID integral error with `G(q0) / Ki` creates bumpless gravity balance but is an initial-state choice, not continuous model feedforward.
- Stability checks include finite histories, maximum and terminal error, requested/applied torque, and saturation; terminal position alone can hide earlier divergence.

## PID with Gravity Compensation

- `tau = tau_PID + G_hat(q)` adds the controller model's gravity term.
- `G_hat(q)` is model feedforward; feedback PID corrects tracking errors and residual model errors.
- Separate plant parameters from controller-model parameters to study mismatch.
- With a correct model, stationary reference, zero error, and zero integral, output is `G(q)`; without saturation or external force, `q_ddot = 0`.
- Incorrect models leave residual torque `G_hat(q) - G(q)` for feedback to correct; perfect rest is not guaranteed.
- Saturate the total PID-plus-gravity request. Anti-windup uses saturation of the combined request.

## Computed Torque Control

- Full model: `tau = M_hat(q) @ v + c_hat(q, q_dot) + G_hat(q)`.
- Virtual acceleration: `v = q_ddot_ref + Kd * e_dot + Kp * e`; unlike PID, it explicitly uses reference acceleration.
- Decomposition: `tau = [M_hat @ q_ddot_ref + c_hat + G_hat] + M_hat @ (Kd * e_dot + Kp * e)`. The first part is model feedforward/compensation; the second maps error feedback to torque. Zero error does not imply zero torque. At zero initial error, actual velocity, and reference acceleration, output is `G_hat(q0)`. This implementation is PD-type CTC without integration.
- Hats denote estimated controller quantities. In continuous time without external force or saturation, define `d = (M_hat - M) @ v + (c_hat - c) + (G_hat - G)`. Then `q_ddot = v + M^(-1) @ d` and `e_ddot + Kd * e_dot + Kp * e = -M^(-1) @ d`. Exact models give `d = 0`. Sampling at `0.001 s`, the hold, and integration still differ from the ideal continuous result.
- With an exact model, no force, and no saturation, `q_ddot = v` and `e_ddot + Kd * e_dot + Kp * e = 0`.
- CTC gains act on virtual acceleration: `Kp` has units `s^-2` and `Kd` has units `s^-1`. Do not reuse torque-output PID gains directly.
- The controller multiplies `M_hat(q) @ v`; the plant solves a linear system. Neither needs an explicit inverse.
- Mismatch, external force, and saturation break exact feedback linearization.
- Validate CTC by passing requested torque through independent forward dynamics and comparing recovered acceleration with virtual acceleration.

## Mathematics and Python Foundations

- Linear systems `A @ x = b` and `numpy.linalg.solve`, rather than explicit `inv(A) @ b`.
- Central finite differences and second-order truncation error `O(h^2)`.
- Analytic derivatives as independent numerical-derivative references.
- An initial-value problem is determined by initial state and an ODE derivative function.
- RK4's four slopes, `1:2:2:1` weights, and fourth-order global accuracy.
- NumPy broadcasting compares trailing dimensions; equal dimensions or dimensions of length `1` are compatible.
- Joint vectors of shape `(2,)` operate on sample arrays of shape `(n, 2)`.
- Degree-radian conversion: `rad = degree * pi / 180`; array conversion with `numpy.deg2rad` and `numpy.rad2deg`, including round-trip checks.

## Jacobian

- The geometric Jacobian links joint and endpoint velocities: `p_dot = J(q) @ q_dot`.
- Its entries are partial derivatives of forward-kinematic positions with respect to joint angles.
- Apply the chain rule to `q1 + q2`.
- Perturb each joint and apply centered finite differences to construct numerical Jacobian columns.
- Cross-validate analytic and numerical Jacobians at random configurations.
- `det(J) = l1 * l2 * sin(q2)`; collinear links are singular.
- Condition number quantifies sensitivity near singularities.
- Virtual work maps Cartesian force to joint torque: `tau_ext = J(q).T @ F`.

## Lagrangian Dynamics

- Parameters include link masses, center-of-mass distances, centroidal inertias, and gravitational acceleration.
- Uniform slender-link inertia about its center: `I = m * l**2 / 12`.
- Distinguish center-of-mass distance `lc` from full link length `l`.
- Differentiate center-of-mass positions in time to obtain linear velocities.
- Composite-angle derivative: `d(q1 + q2)/dt = q1_dot + q2_dot`.
- Rigid-body kinetic energy combines `0.5 * m * v_c^T v_c` and `0.5 * I * omega**2`.
- Absolute link angular velocities are `q1_dot` and `q1_dot + q2_dot`.
- With y upward and gravity downward, potential energy is `V = m * g * y`.
- The potential-energy zero is arbitrary; dynamics depend on its coordinate gradient.
- Lagrangian: `L = T - V`.
- Euler-Lagrange: `d/dt(∂L/∂q_dot_i) - ∂L/∂q_i = tau_i`.
- Gravity vector: `G(q) = ∂V/∂q`.
- Kinetic-energy quadratic form: `T = 0.5 * q_dot.T @ M(q) @ q_dot`.
- Mass matrix from the velocity Hessian: `M_ij = ∂²T/(∂q_dot_i ∂q_dot_j)`.
- The rigid-robot mass matrix is symmetric positive definite.
- Christoffel symbols use coordinate derivatives of the mass matrix.
- Coriolis/centrifugal vector: `c_i = Σ_j Σ_k Γ_ijk * q_dot_j * q_dot_k`.
- Implement `c(q, q_dot)` directly to avoid relying on a non-unique `C(q, q_dot)` matrix representation.
- SymPy independently verifies manual derivations; symbolic differentiation, Jacobians, and Hessians extract `M` and `G` from `T` and `V`.

## Stage 16: Fair Tuning and Scoring

- Normalize each joint's position error by its reference range, then compute overall RMSE over all samples and joints. Sample RMSE differs from time-weighted error.
- Zero-order-held torque uses left-rectangle integration per control interval. Terminal torque/saturation has no subsequent interval; terminal position still contributes to tracking error.
- Saturation fraction uses interval durations and counts an interval if either joint saturates.
- Weighted dimensionless scores define trade-offs. Preset weights are not the realized contribution fractions; fix definitions and weights before searching.
- Each candidate independently initializes plant and integral states. Zero integral initialization retains PID's gravity-induced startup transient in the common score.
- `dataclass(frozen=True)` prevents field reassignment but not mutation of contained NumPy arrays. Factories create fresh arrays for each candidate.
- Reproducibility requires a fixed random algorithm, seed, draw order, distributions, and budget; use a local generator.
- PID variants search six gains directly; CTC retains natural-frequency/damping-ratio parameters. Baselines and failures consume budget. PID reference-inertia mapping was an abandoned development approach.
- Finite-horizon bounds and non-finite screening reject failed candidates without proving asymptotic stability.
- PID and PID+Gravity share a candidate table but are scored independently and may select different rows. Formal experiments use frozen gains.
- Random search samples combinations; grid search enumerates a Cartesian product. Sequentially evaluating a random candidate table remains random search.
- Five values for each of six gains yield `5**6 = 15625` combinations. A finite random budget finds only the best evaluated candidate, not a guaranteed global optimum.
- Single-candidate evaluation connects gains, independent training scenarios, simulation, screening, and scoring. Diagnostics include terminal state/output; torque cost includes only applied intervals.
- Numerical failures retain reasons and are excluded; ordinary configuration/programming errors propagate. `np.errstate` temporarily controls floating-point exceptions and restores the prior settings.

## Stage 18: Endpoint Point-Mass Payload

- Payload position uses full `l2`, unlike the second link's center of mass at `lc2`.
- `v_p = J(q) @ q_dot` and `T_p = 0.5 * m_p * v_p.T @ v_p`. A point mass adds no rotational energy about its own center.
- With y upward, `V_p = m_p * g * (l1*sin(q1) + l2*sin(q1+q2))`.
- Energies add: `T = T_0 + T_p`, `V = V_0 + V_p`. This note was recorded before payload source implementation.
- From `T_p = 0.5 * q_dot.T @ Delta_M @ q_dot`, the cross-term coefficient inside the brackets is `2 * Delta_M12`, contributed by both symmetric off-diagonal entries.
- `Delta_M = m_p * J.T @ J`; independent entries are `m_p*(l1**2+l2**2+2*l1*l2*cos(q2))`, `m_p*(l2**2+l1*l2*cos(q2))`, and `m_p*l2**2`.
- Nonnegative payload gives a symmetric positive-semidefinite increment and nonnegative kinetic energy. The increment can be singular at kinematic singularities; adding it to the positive-definite base mass matrix remains positive definite.
- `Delta_G = m_p*g*[l1*cos(q1)+l2*cos(q1+q2), l2*cos(q1+q2)]`, also checked by `J.T @ [0, m_p*g]`.
- Left-side `Delta_G` is opposite to actual downward generalized force `J.T @ [0, -m_p*g]`. Static support requires adding `Delta_G`; Stage 18 controllers retain the unloaded model.
- Form `d/dt(partial T_p / partial q_dot_i) - partial T_p / partial q_i` and subtract `Delta_M @ q_ddot` to obtain the Coriolis/centrifugal increment.
- With `h_p = m_p*l1*l2*sin(q2)`, `Delta_c = [-h_p*(2*q1_dot*q2_dot+q2_dot**2), h_p*q1_dot**2]`. Distinguish coordinate partial derivatives from time derivatives along motion.
- Temporary SymPy checks verified these increments and `q_dot.T @ Delta_c = 0.5*q_dot.T @ Delta_M_dot @ q_dot`. This is not a friction term.

## Stage 20: Force Disturbance and Recovery (2026-09-13)

- Map endpoint force by actual `J(q)^T F`; hold F per interval and update q at each RK4 substep. Switching boundaries align with integration intervals.
- An interval factory creates a torque-function closure retaining the interval force and actual model parameters.
- Recovery requires error at or below 0.01 m for at least 0.5 s after force removal. Report the qualifying window's start delay. A 0.001 s grid needs 501 points spanning 500 intervals; None means recovery was not confirmed within the record.
- Under exact-model, continuous, unsaturated CTC, external force still drives `e_ddot + Kd e_dot + Kp e = -M(q)^(-1) tau_external`. Distinguish full-run peaks, post-disturbance peaks, and nominal-relative increments. See `results/disturbance/STAGE20_RESULTS.md`.
- Learning analysis (2026-09-14): absolute tracking error versus extra nominal-relative deviation; baseline effects on threshold recovery; PID torque-gain versus CTC acceleration-gain units; `M(q)Kp` proportional torque mapping at a fixed configuration; matched-gain comparisons needed to isolate gravity compensation. See the learning supplement in the same results document.

## Stage 21: Analysis Index (2026-09-17)

- Unified tables, source provenance, and fixed figures; overall versus per-joint RMSE; effort in (N·m)^2·s versus absolute work in J.
- Own-nominal denominator effects; no statistical error bars for deterministic runs; metric-dependent rankings; combined payload mismatch and saturation effects.
- Methods: `stage21/README.md`. Full generated values: `stage21/output_2f080606329f/report.md`.

## Stage 22: Report Index (2026-09-17)

- Separate methods, results, and discussion; evaluate advance predictions; state conditional conclusions and limits of causal explanations; distinguish rankings across error metrics.
- Data-bound Quarto templates, cross-references, and common-source HTML/Typst PDF; distinguish render success, content identity, pixel identity, and byte identity.
- Methods: `stage22/README.md`. Full report: `stage22/output/report.html` and `stage22/output/report.pdf`.
