# Two-DOF Robot Arm Control Research: Stage-Gated Roadmap

This document preserves the original research roadmap and fixed protocol. Statements about planned or not-yet-completed work describe the time the plan was written; consult `PROGRESS.md` for current status. This edition presents all deliverables in English.

## Collaboration and Context

1. Advance the project step by step and monitor relevant file changes. The user writes source code; the assistant teaches, reviews, and verifies unless implementation is explicitly authorized.
2. `PROGRESS.md` is concise working memory: current stage, completed capabilities, recent evidence, known issues, collaboration/validation rhythm, and the next step. `PROGRESS_HISTORY.md` is the full chronological archive. Use targeted `rg` searches for old commands, versions, dates, failures, decisions, acceptance evidence, reports, and releases only when needed. Do not read the entire archive routinely.
3. After meaningful milestones, update the progress summary and append a short history entry. Do not log each blank-line repair, test wait, or repeated confirmation separately. After context compaction, recover from the summary and consult history only for missing details.
4. Explain the purpose of every step. The original learning workflow combined Chinese explanations with English terminology to support international communication; this deliverable is fully English.
5. Add new concepts to `THEORY_NOTES.md` as brief topic indexes, not lengthy derivations.
6. Teach one concept or complete functional block at a time: explain, let the user implement and report, review, explain the result, then update progress. Do not complete later stages in advance without authorization.

## 1. Project Overview

### Final Goal

Build a rigid two-DOF robot arm moving in a vertical plane. Starting from kinematics, Lagrangian dynamics, trajectory generation, and numerical integration, independently implement and compare:

1. Independent-joint PID.
2. PID with gravity compensation.
3. Computed torque control (CTC).

Use identical trajectories, initial states, actuator limits, and simulation accuracy to study payload changes, model-parameter errors, and endpoint force disturbances.

**Research question:** How do independent-joint PID, gravity-compensated PID, and computed-torque control compare under nominal and uncertain manipulator dynamics?

Subquestions address the benefit of accurate model compensation, degradation with payload, CTC sensitivity to incorrect masses, recovery after identical forces, and whether improved tracking requires greater control effort or saturation. Success requires fair experiments, reproducibility, and evidence, not a predetermined CTC victory.

### Planned Deliverables

- An installable, testable Python project.
- Complete kinematic and dynamic derivations.
- Three controllers with a unified simulator.
- Configuration-driven batch benchmarks.
- Raw data, summary tables, and 6-8 core figures.
- A Quarto technical report in HTML and PDF; the original plan was bilingual, while this edition is English.
- An English GitHub README.
- A 1-2 minute video or GIF.
- MIT License, environment file, tests, and a formal GitHub release.
- Quantitative findings suitable for a CV or interview.

Progress is governed by stage gates, not fixed weekly deadlines. Do not start a later stage before the current gate passes.

## 2. Learning and Implementation Stages

### A. Project and Tools

| Stage | Goal and learning | Implementation | Tools and acceptance |
|---|---|---|---|
| 0. Research charter | Testable questions, hypotheses, variables, controls, falsifiability | One-page charter separating plant/controller models, inputs/outputs, and core/extensions | Quarto, VS Code; one main question, four subquestions, predictions, success criteria, limitations |
| 1. Environment | Conda, interpreter, packages, terminal, Git | User-level Windows Miniconda; `robot2dof` environment; VS Code interpreter; Quarto | Python 3.12, Git; `python --version`, `pytest --version`, `quarto check jupyter` succeed |
| 2. Project skeleton | Packages, modules, configuration, tests, relative imports, commits | Source/config/experiment/test/note/report/result directories; environment, ignore, and project metadata | Git, Ruff, pytest; local package installs and a minimal test passes |
| 3. Mathematics and Python | Vectors, matrices, linear solves, partial derivatives, chain rule, ODEs, radians, broadcasting, functions, dataclasses | Exercises on planar rotation, linear equations, finite differences, scalar RK4, and unit conversion | Jupyter, NumPy, SciPy; numerical assertions for every exercise |
| 4. Reproducible workflow | Notebooks versus production modules, seeds, configuration, metadata | Derive, implement, test, record; reusable logic in source; stage-end Git checkpoints | Jupyter, Git, YAML; repeated configurations reproduce results |

Use [Modern Robotics resources](https://hades.mech.northwestern.edu/index.php/Modern_Robotics) for rigid motion, velocity kinematics, dynamics, trajectories, and motion control. Use *Feedback Systems* for feedback, stability, second-order response, and PID. Follow the [Conda Windows guide](https://docs.conda.io/projects/conda/en/stable/user-guide/install/windows.html) and [pytest getting-started guide](https://docs.pytest.org/en/latest/getting-started.html).

### B. Kinematics and Dynamics

| Stage | Goal and learning | Implementation | Acceptance |
|---|---|---|---|
| 5. Coordinates and parameters | Generalized coordinates, relative angles, centers of mass, inertia, potential energy, units | Geometry/frame diagram, parameter table, radians internally | Quarto/Matplotlib; identical notation in report, formulas, and code |
| 6. Forward kinematics | Planar rotations, homogeneous transforms, trigonometry | Hand derivation, direct trigonometric and transform implementations | NumPy/pytest; known configurations and random cross-validation |
| 7. Inverse kinematics | Workspace, inverse-cosine domain, multiple solutions, normalization | Analytic IK, reachability, elbow branches, workspace/configuration plots | Random nonsingular FK→IK→FK position error below 1e-9 m |
| 8. Jacobian | Chain rule, singular values, condition number, virtual work | Derive J, finite-difference check, determinant/condition plot, external-force mapping | Maximum analytic/numerical difference below 1e-6 |
| 9. Lagrangian derivation | Kinetic/potential energy, Euler-Lagrange, Christoffel terms, coupling, gravity | Derive centers, velocities, T/V/L, M/c/G; independently check with SymPy | Symbolic simplification or random substitution agrees |
| 10. Numerical dynamics | Symmetric positive-definite M, potential gradient, linear solution | Implement M/c/G and forward dynamics | NumPy/pytest; symmetry, positive definiteness, gravity, known-value checks |
| 11. Simulator | First-order state space, RK4, convergence, energy | Fixed-step integrator, solver cross-check, energy evolution | Step-halving convergence and agreement with high-accuracy solve_ivp |

[SymPy Lagrange's Method](https://docs.sympy.org/latest/explanation/modules/physics/mechanics/lagrange.html) may organize equations, but retain the independent derivation. [SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html) is a cross-check, not a substitute for the custom RK4.

### C. Trajectories and Controllers

| Stage | Goal and learning | Implementation | Acceptance |
|---|---|---|---|
| 12. Quintic trajectory | Six boundary conditions, multiple segments, continuity | Single/multisegment rest-to-rest trajectories | All endpoint position, velocity, and acceleration constraints pass |
| 13. Independent-joint PID | P/D/I, overshoot, steady-state error, windup | Reference-minus-state errors; conditional integration; external shared limiter | Stable training trajectory without NaN or sustained divergence |
| 14. PID+Gravity | Feedforward, model knowledge, static balance | Add controller-model G_hat with the same interface | Correct equilibrium torque at a stationary target with the correct model |
| 15. Computed torque | Feedback linearization, second-order error, mismatch | PD-type CTC; separate plant and controller models | Correct unsaturated model gives expected second-order error dynamics |
| 16. Fair tuning and freezing | Direct gain search, CTC parameterization, train/test separation, budget/objective | Six PID gains; CTC frequency/damping; fixed trajectory, seed, budget; freeze selections | Preserve search space, seed, all scores, and final gains |
| 17. Nominal benchmark | Fair comparison, error interpretation, saturation diagnostics | Three controllers on the held-out trajectory, equal models | One command rebuilds data/figures; no retuning from results |

### D. Robustness, Report, and Release

| Stage | Goal and learning | Implementation | Acceptance |
|---|---|---|---|
| 18. Payload | Point-mass inertia/Coriolis/gravity and mismatch | Payload in plant only; fixed mass grid | Payload versus RMSE, effort, and saturation curves |
| 19. Model error | Relative error, internal model bias, sensitivity | Fixed plant, scaled controller m2/I2; model-independent PID baseline | -30% to +30% curves without retuning |
| 20. External force | Force-to-torque mapping, transients, recovery, nonrecovery | Fixed endpoint force using the actual Jacobian | Recovery and peak errors, with correct nonrecovery labels |
| 21. Analysis | Units, normalization, tables, error bars, effort versus energy | Automatic CSV/tables/eight figures from raw results; explanation by the author | Generated outputs can be deleted and rebuilt with one command |
| 22. Technical report | Methods, references, results versus discussion, limitations | Introduction, Model, Trajectory, Controllers, Methodology, Results, Discussion, Limitations, Conclusion | HTML/PDF render without errors; values come from generated files |
| 23. Demo and public release | README structure, demonstration, versions, licensing | 60-120 s video/GIF, installation/reproduction/results/citation, public GitHub | Green tests, fresh-environment reproduction, MIT License, v1.0.0 |

The planned toolset includes Python, NumPy, SciPy, Matplotlib, YAML, Pandas where needed, and Quarto; later implementations may use standard-library CSV instead of Pandas. See [Quarto with Python](https://quarto.org/docs/computations/python.html) and [Matplotlib animation](https://matplotlib.org/stable/users/explain/animations/animations.html). FFmpeg can produce MP4/GIF.

### E. Extensions Only After v1.0.0

| Level | Extension | Work | Acceptance |
|---|---|---|---|
| First A | Friction uncertainty | Viscous/Coulomb friction in plant, frictionless controllers | Compare error and static oscillation across friction levels |
| First B | Encoder noise | q_m=q+epsilon; estimate velocity by finite differences and low-pass filtering | 30 fixed seeds per noise level; mean, standard deviation, 95% CI |
| Second | Cartesian trajectories | Endpoint lines/arcs, continuous IK branch selection, joint limits, Jacobian conditioning | No workspace violation, branch jumps, or prohibited singular regions |
| Long term | 3-DOF, ROS 2, Gazebo, hardware | Transfer validated models/controllers/benchmarks | Outside the core report; no substitute for incomplete two-DOF foundations |

## 3. Fixed Model, Architecture, and Protocol

### 3.1 Robot Definition

Vertical planar two-link arm: x right, y up, gravity down. q1 is counterclockwise from +x; q2 is counterclockwise relative to link 1. At q=[0,0], both links point right. Use SI units/radians internally; plots may also show degrees.

| Parameter | Value |
|---|---:|
| l1 | 0.50 m |
| l2 | 0.40 m |
| m1 | 2.00 kg |
| m2 | 1.50 kg |
| lc1 | 0.25 m |
| lc2 | 0.20 m |
| I1 | m1*l1^2/12 |
| I2 | m2*l2^2/12 |
| g | 9.81 m/s² |
| Joint torque limits | [-20,20] N·m |
| Core simulation step | 0.001 s |

The core model excludes friction, backlash, delay, and sensor noise. State these limitations explicitly.

### 3.2 Trajectories

Stage 16 training uses one rest-to-rest quintic from `[-35°, -45°]` at t=0 to `[50°, 60°]` at t=4 s, with zero endpoint velocity and acceleration. All controllers share trajectory, state, step, limits, objective, budget, and seed. Training results may guide gain selection.

Training initialization, fixed 2026-09-05:

- Each candidate starts at `[-35°, -45°]` with zero joint velocity, stored in radians.
- PID variants start with integral error `[0,0]`. Reset every candidate; do not inherit state or preload `G(q0)/Ki`. Score all history from t=0, with no warm-up exclusion.
- Control period and single-period RK4 step are `0.001 s`; per-joint limit is `20 N·m`; external joint torque is `[0,0]`.
- Plant and controller models have equal nominal values but separate objects. Pure PID receives no `controller_params`; PID+Gravity/CTC use the scenario's model object.
- `create_training_scenario()` creates fresh arrays and parameter objects per candidate; the factory is implemented and verified.
- PID candidates store six direct gains. Do not derive them from reference inertia, natural frequency, damping ratio, or shared integral ratios. The former midpoint-inertia mapping is historical only.

Stages 17-20 use this locked held-out trajectory, never for tuning:

| Time (s) | q1 (deg) | q2 (deg) |
|---:|---:|---:|
| 0 | 20 | -35 |
| 2 | -40 | 25 |
| 4 | 55 | 45 |
| 6 | 5 | -50 |
| 8 | -30 | 15 |

Each segment is rest-to-rest quintic with zero velocity/acceleration at waypoints. Initialize at the first waypoint with zero velocity. Definitions may be added to configuration/tests, but do not run or inspect errors, torques, saturation, or other performance before freezing all gains, search records, and configuration hashes. Do not retune after unfavorable held-out results.

Older single-segment and five-waypoint trajectories used before 2026-09-04 remain development/regression trajectories. They do not enter Stage 16 scoring or formal Stage 17-20 comparisons.

### 3.3 Controllers and Tuning

- PID uses true noise-free q/q_dot and conditional-integration anti-windup.
- PID+Gravity adds G_hat(q) to the same PID structure.
- CTC uses PD error dynamics without integration.
- All controllers compute unrestricted torque before the same shared limiter.
- Never retune during formal experiments. Keep actual/controller parameters in independent objects.

PID/PID+Gravity search `(kp1,ki1,kd1,kp2,ki2,kd2)` independently, without frequency/damping mapping or shared integral ratios. Joint 1 ranges: Kp `[20,300]`, Ki `[0,100]`, Kd `[1,60]`; joint 2: Kp `[10,200]`, Ki `[0,80]`, Kd `[0.5,40]`. Units are N·m/rad, N·m/(rad·s), and N·m·s/rad. These engineering ranges cover earlier baselines; their optimality is not established.

CTC uses per-joint `omega_n in [3,12]` rad/s and `zeta in [0.7,1.2]`, with `Kp=omega_n**2` and `Kd=2*zeta*omega_n`, without integration. Each controller evaluates 300 fixed-seed candidates. The shared objective combines normalized joint RMSE, effort, and saturation. Failed/NaN/out-of-range candidates are rejected; tied scores prefer lower effort.

Candidate rules, revised 2026-09-05:

- ID 0 is the baseline; IDs 1-299 are random. PID baseline: `Kp=(150,100)`, `Ki=(30,20)`, `Kd=(25,15)`, with zero integral initialization. CTC baseline: `omega=(8,8)`, `zeta=(1,1)`.
- PID variants share the same six-dimensional table but simulate, score, and select independently. CTC has a separate four-dimensional table.
- Generate candidates first, then evaluate them sequentially. This is fixed random search, not a full grid or adaptive proposal process.
- Both generator families use a fresh local `numpy.random.Generator(numpy.random.PCG64(20260905))`. PID draws linear-uniform gains in `(kp1,ki1,kd1,kp2,ki2,kd2)` order. Do not use/reset global randomness.
- CTC draws two `Uniform(3,12)` frequencies and two `Uniform(0.7,1.2)` damping ratios, then retains the old generator's `choice((0,0.05,0.1,0.2))` random-number consumption and discards its value. This preserves all 300 original CTC rows/gains; it adds no integral parameter. A full pre-rewrite snapshot confirmed identity.
- PID APIs: `generate_pid_tuning_candidates()` and `build_pid_candidate_gains(...)`. CTC APIs: `generate_computed_torque_tuning_candidates()` and `build_computed_torque_candidate_gains(...)`. Old mixed/PID-inertia interfaces were removed.
- Equal budget/seed/scoring does not imply equal coverage of six-dimensional PID and four-dimensional CTC spaces. At the time of this rule, generation, gain connection, and single-candidate scoring were verified; full-budget search integration was next.
- Failed candidates consume budget; no replacements or performance-based early stopping. Save status/reason for every candidate. Never change the table from held-out results.
- Screen sampled states, references, integral errors, requested/applied torques, metrics, and confirmed numerical-solver failures. NaN/Inf, `abs(q)>pi` rad, or `abs(q_dot)>50` rad/s fail. Equality at bounds is allowed. Finite-horizon screening does not prove asymptotic stability.
- Saturation is penalized by S rather than rejected by itself. Sort successful candidates by `(score, normalized_control_effort, candidate_id)`, using full precision and exact ties. If all fail, report no usable candidate without automatically expanding the search.
- `evaluate_training_candidate(controller,candidate)` fixes the training scenario and returns `CandidateEvaluation`. Failures retain their reason and available history, expose `score=inf` and `metrics=None`, and use `simulation=None` when no full history exists. Known numerical failures are recorded; ordinary configuration/program errors propagate.

Scoring, fixed 2026-09-05:

- N includes initial and final samples. Each joint's scale A_j is its training-reference range: `[85°,105°]`, converted to radians.
- `R = sqrt(sum_k sum_j (e_kj/A_j)**2/(2*N))`, over all position samples and both joints, including the final position. This is sample RMSE.
- `U = sum_k(dt_k*sum_j tau_kj**2)/(T*sum_j limit_j**2)`, using applied torque over the first N-1 control intervals.
- `S = sum_k(dt_k*any_joint_saturated_k)/T`, also over N-1 intervals; either joint suffices.
- Minimize `J = 0.7*R + 0.2*U + 0.1*S`. Preset weights were fixed before search and do not prescribe realized score contributions.
- `DEFAULT_TUNING_WEIGHTS` supplies the shared constant. Held-out results must not alter definitions or weights.

### 3.4 Formal Experiment Matrix

1. Nominal: identical plant and controller models.
2. Payload: actual endpoint point masses `0,0.25,0.50,0.75,1.00` kg; controllers assume zero.
3. Model uncertainty: fixed plant; controller m2 errors `{-30,-20,-10,0,10,20,30}%`, scaling I2 equally.
4. Disturbance: base-frame `F=[10,0]^T` N during `[4.5,4.7)` s, mapped by actual `J(q)^T F`.
5. First-level noise extension: position standard deviations `0.001,0.005,0.010` rad, with 30 fixed seeds each.

### 3.5 Metrics

- Joint RMSE: per joint and overall, in radians and degrees.
- End-effector RMSE and peak error: metres.
- Recovery: earliest post-force window with endpoint error at or below 0.01 m for 0.5 s. Mark unconfirmed recovery explicitly.
- Stage 20 convention (2026-09-13): a 0.001 s grid needs 501 points over 0.5 s. Return qualifying-window start minus 4.7 s; unconfirmed is None/JSON null/blank CSV with recovered=False. Full-run peak covers 0-8 s; post-disturbance peak covers 4.5-8 s and is not a nominal-subtracted increment. Hold pulse gating per interval; update J(q)^T F at RK4 substeps, with switching aligned to boundaries.
- Control effort: integral of tau^T tau, never described as energy.
- Supplementary mechanical work: integral of absolute tau^T q_dot.
- Stage 17 convention (2026-09-06): integrate applied saturated motor torque by zero-order-held intervals. Effort/saturation exclude the final output record. Work uses interval-start torque and velocity with a left-rectangle approximation, summing joint power before taking the absolute value; it is not exact integration. Tracking error includes all positions, including the endpoint.
- Saturation fraction: sampled duration with either joint reaching its torque limit.
- Noise extensions report mean, standard deviation, and 95% confidence intervals; deterministic core experiments do not invent statistical error bars.

### 3.6 Software Interfaces

Planned core types: `RobotParams` (lengths, masses, centers, inertias, gravity, payload); `State` (q/q_dot); `Reference` (q_ref/q_dot_ref/q_ddot_ref); `ControllerOutput` (requested torque and diagnostics); `SimulationResult` (time/state/reference/requested/applied torque/endpoint position/force/saturation).

Core boundaries:

```text
forward_kinematics(q, params)
inverse_kinematics(xy, params, branch)
jacobian(q, params)
mass_matrix(q, params)
coriolis_vector(q, q_dot, params)
gravity_vector(q, params)
forward_dynamics(state, tau, params, external_tau)
trajectory.sample(t)
controller.compute(t, state, reference)
simulate(experiment_config)
compute_metrics(simulation_result)
```

YAML configuration sections: `actual_model`, `controller_model`, `trajectory`, `controller`, `simulation`, `actuator`, `disturbance`, `seed`, `output`. Store high-frequency arrays in compressed NPZ, metadata in JSON, and metrics in CSV. Record configuration hashes, Git commit, software versions, and seed.

## 4. Tests and Research Quality

### Mathematical and Unit Checks

- FK at zero, right-angle, and folded configurations; IK reachable, boundary, unreachable, and both branches.
- Analytic Jacobian versus centered finite differences.
- M symmetric positive definite at at least 1000 valid random configurations; G agrees with a finite-difference potential gradient.
- Check mechanical-energy drift with zero gravity/input as planned, and unactuated conservative cases as implemented.
- All trajectory endpoint constraints and continuous multisegment positions.
- At zero error, PID gives zero, gravity compensation gives G_hat, and CTC gives the correct feedforward torque.
- Applied torque never exceeds 20 N·m; anti-windup prevents unbounded integral growth under prolonged saturation.

### Numerical and Integration Checks

- RK4 convergence at 0.002, 0.001, and 0.0005 s.
- Agreement with high-accuracy solve_ivp for fixed open-loop inputs within preset tolerances.
- Identical repeated configurations/seeds give numerically identical results.
- Formal scenarios have no NaN, Inf, reversed times, or missing fields.
- Automated experiments preserve existing results and use identifiable output paths.
- Every summary row traces to raw history and configuration.

### Final Acceptance Goals

All pytest tests and Ruff checks pass; produce coverage evidence. A fresh Conda environment can install and run a nominal demo. Batch commands rebuild core experiments and all figures/tables. Quarto generates HTML/PDF without manual data edits. README commands are tested by copying them. Report benefits, failures, and limitations without removing unfavorable results or claiming hardware performance. Publish only after core completion, with MIT License and v1.0.0.

## 5. Fixed Assumptions and Boundaries

The original plan assumed an empty workspace and a learner familiar with calculus, linear algebra, mechanics, or control but new to a complete robotics research project. Python is the main route; MATLAB is optional future cross-validation. The original report-language policy was Chinese prose with standard English terms and bilingual title/abstract; this delivery is fully English. Freeze exact Python versions after establishing the environment. Quarto HTML is the primary reproducible artifact and PDF the archive. ROS, Gazebo, 3-DOF, MPC, reinforcement learning, vision, and hardware are outside core stages. Extensions require a published reproducible v1.0.0. Every stage retains learning notes, runnable implementation, automated tests, and a stage conclusion.
