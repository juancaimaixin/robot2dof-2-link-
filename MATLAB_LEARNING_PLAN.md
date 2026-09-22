# MATLAB / Simulink Two-Link Robot Arm: Stage-Gated Learning Roadmap

This standalone learning plan can be moved into a new project. Its organization follows the Python project's `PLAN.md`.

Route: MATLAB basics → kinematics and planar animation → Simulink basics → equation-based dynamics → Simscape Multibody physical model → PID control.

Advance by demonstrated understanding, without fixed dates. This is a plan, not evidence that its stages are complete.

## Collaboration and Context Recovery

1. **The user implements; the assistant teaches and reviews.** The user writes MATLAB code, builds Simulink blocks, and operates the software. The assistant explains, guides the current block, checks file changes, and validates. Do not write the source, build the full model automatically, or complete later stages without explicit authorization.
2. **One concept or complete functional block at a time.** Explain the principle, let the user operate and report, check/explain, and summarize. Providing a tutorial does not establish acceptance.
3. **Explain terminology and purpose.** The original learning workflow used Chinese explanations with English terms such as Workspace, Integrator, and Plant. This edition is English; every step still identifies purpose and expected results.
4. **Separate memory and history.** `PROGRESS.md` contains the current stage, mastered skills, recent evidence, environment/license status, known issues, and next step. `PROGRESS_HISTORY.md` receives concise dated milestones, not entries for each line or repeated format check.
5. **Recover context on demand.** Read this plan on first entry. Later, start with progress, Git status if available, and relevant files; consult the plan at stage transitions or when rules are unclear. Do not scan the whole project at startup. Search history only when needed; inspect caches, images, and older results only for the task.
6. **Record a theory index.** Add brief concepts, English terms, and stage references to `THEORY_NOTES.md`, without long derivations in the progress summary.
7. **Validate by functional block.** Check key normal and failure paths, without repeating full-project checks absent changes or uncertainty. This project uses MATLAB checks and model simulations, not Python's pytest/Ruff requirements.
8. **Model manually at first.** Understand blocks, ports, signals, and connections before scripted batch construction. Move from sufficient MATLAB basics into arm practice.
9. **Synchronize milestones.** Update progress and append date, result, evidence, and next step after meaningful completion. After context compaction, continue from the summary without restarting completed stages.

## 1. Project Overview

### Goal

Starting with no MATLAB/Simulink experience, independently build two dynamic descriptions of the same vertical-plane two-link arm:

1. **Equation-based model:** implement dynamics in MATLAB and integrate motion with Simulink.
2. **Physical model:** connect rigid bodies and joints in Simscape Multibody, configuring masses, inertias, and gravity.
3. After cross-validation, connect the same independent-joint PID to both for position holding and trajectory tracking.

The objective is to explain, build, modify, and check the models. Gates depend on understanding and evidence, not course completion, playable animation, or absence of simulation errors.

**Question:** How can the same two-link arm be modeled, validated, and controlled in MATLAB, Simulink, and Simscape Multibody?

Learn the roles of scripts/functions/workspace variables/models; distinguish prescribed-angle animation from torque-driven motion; understand how integrators turn dynamics into states; align coordinates/parameters/initial states/inputs across models; and study PID terms, sampling, and saturation.

The Python project already implements dynamics, trajectories, PID, gravity compensation, and CTC, but this does not establish the user's theoretical understanding. This new project uses the parameters/formulas below independently, without the old repository, Python environment, or selected gains.

### Deliverables

- Rerunnable parameter initialization, kinematics, dynamics, and plotting functions.
- Static forward-kinematic plots and planar animation.
- MATLAB reference simulation, Simulink equation model, and Multibody physical model.
- Checks/results for open-loop equilibrium, free motion, energy, and model comparisons.
- Shared PID, position holding, and quintic tracking demonstrations.
- Joint position/error/requested/applied torque plots and metrics with units.
- Environment records, run instructions, theory index, and progress sufficient to resume in a new session.

## 2. Learning Stages

| Stage | Goal and learning | Work | Gate |
|---|---|---|---|
| 0. Environment and project | Command Window, Editor, Workspace, Current Folder, products/licenses | Check MATLAB/Simulink startup and Simscape/Multibody availability; handwrite a length-parameter script; separately build a minimal Simulink model | Prefer R2023b; rerunnable script; model saves/reopens/runs; environment recorded |
| 1. MATLAB foundations | Variables, column vectors, matrices, indexing, matrix/elementwise operators, scripts/functions/structs/plots | Small arm-parameter exercises, parameter struct, function call, two plotted curves | Explain dimensions/operators/results; units and legends |
| 2. Kinematics/animation | Forward kinematics, relative/absolute angles, frames, radians, graphics | Handwrite FK; plot base/links/endpoint; animate a supplied angle sequence | Three known configurations correct, lengths fixed; explain that no torques/dynamics are solved |
| 3. Simulink basics | Constant, Step, Sum, Gain, Integrator, Scope, logging, Subsystem, Solver | Manually build a first-order system, initial conditions and step time; export signals | Zero-initial-state dx/dt=-x+u with a unit step at t=0 agrees with x=1-exp(-t); distinguish simulation/output times and step |
| 4. MATLAB dynamics reference | M/c/G, state space, linear solves, ODEs, mechanical energy | Implement dynamics in blocks; four-state derivative; ode45 equilibrium/free motion | Pass known-value, balance, and energy checks; explain physical quantities |
| 5. Simulink equation model | MATLAB Function, vectors, continuous states, feedback, logging | Compute acceleration, integrate twice for speed/angle, plot/animate | Match MATLAB reference within thresholds for equal inputs/states/output times |
| 6. Multibody basics | World Frame, Solid, Rigid Transform, Revolute Joint, Mechanism/Solver Configuration, signal conversion | Build one link, then two; configure centers/inertias/axes/gravity/initial states/sensors | Correct structure, zero pose/signs, gravity-driven free motion, measured angles/speeds |
| 7. Cross-validation | Coordinate mapping, initial/input consistency, time alignment, convergence | Overlay free-motion/equilibrium histories, calculate maximum angle differences, record solver settings | Pass thresholds and explain equation versus physical connections |
| 8. Independent-joint PID | Feedback, PD/PID, steady-state error, overshoot, sampled hold, saturation/anti-windup, quintic trajectories | No-gravity PD → gravity PD → PID/anti-windup → holding → quintic tracking → physical model | Holding/RMSE thresholds, finite states, no sustained divergence, ±20 N·m actual torque limits |

If Multibody is unavailable at Stage 0, record the missing product and complete Stages 1-5 first. Resolve availability before Stage 6. Planar animation cannot replace physical-dynamics validation.

After Stages 0-8, separately plan gravity compensation, CTC, payload/model-error/disturbance studies, or IK/Jacobian/Cartesian trajectories. The current scope requires only FK and joint-space trajectories; do not import the old benchmark wholesale.

## 3. Fixed Model and Protocol

### Coordinates and Parameters

Motion is in the vertical xy plane: x right, y up, gravity down. Both positive joint directions are counterclockwise about +z. q1 is relative to +x; q2 is relative to link 1, so link 2's absolute angle is q1+q2. At q=[0,0]^T both links point right. Internally use metres, kilograms, seconds, radians, and newton-metres; figures may use degrees.

| Parameter | Link 1 | Link 2 |
|---|---:|---:|
| Length l | 0.50 m | 0.40 m |
| Mass m | 2.00 kg | 1.50 kg |
| Center distance lc from proximal joint | 0.25 m | 0.20 m |
| Centroidal out-of-plane inertia I | 0.0416666667 kg·m² | 0.0200000000 kg·m² |

Calculate `I_i=m_i*l_i^2/12` in code instead of using rounded table values. Gravity is 9.81 m/s². There is no payload, friction, backlash, delay, or sensor noise. Later actuator limits are [-20,20] N·m per joint. Initial work is simulation only, without motors, hardware, or real-time systems.

### Kinematic and Dynamic Reference

\[
p_1=\begin{bmatrix}l_1\cos q_1\\l_1\sin q_1\end{bmatrix},\qquad
p_2=p_1+\begin{bmatrix}l_2\cos(q_1+q_2)\\l_2\sin(q_1+q_2)\end{bmatrix}.
\]

\[
M(q)\ddot q+c(q,\dot q)+G(q)=\tau+\tau_{\mathrm{ext}}.
\]

Use zero external torque for this project while retaining the input for extensions.

\[
\begin{aligned}
M_{11}&=I_1+I_2+m_1l_{c1}^2+m_2(l_1^2+l_{c2}^2+2l_1l_{c2}\cos q_2),\\
M_{12}&=M_{21}=I_2+m_2(l_{c2}^2+l_1l_{c2}\cos q_2),\\
M_{22}&=I_2+m_2l_{c2}^2.
\end{aligned}
\]

With \(h=m_2l_1l_{c2}\sin q_2\),

\[
c=\begin{bmatrix}-h(2\dot q_1\dot q_2+\dot q_2^2)\\h\dot q_1^2\end{bmatrix},\qquad
G=\begin{bmatrix}g[(m_1l_{c1}+m_2l_1)\cos q_1+m_2l_{c2}\cos(q_1+q_2)]\\gm_2l_{c2}\cos(q_1+q_2)\end{bmatrix}.
\]

Use MATLAB `M \ (tau + tau_ext - c - G)` for acceleration, not an explicit inverse. These are later reference formulas, not a requirement to understand or enter everything in lesson one.

### Model Organization and Interfaces

Keep initialization, functions, models, checks, and results separate without copying the old project's many experiments.

- q, dq, ddq, tau, and tau_ext are 2×1 columns.
- State order: `[q1,q2,dq1,dq2]^T`.
- Centralize parameter initialization rather than duplicating constants across blocks.
- Export a time column and N×2 angle, velocity, reference, and torque arrays.
- Both models expose torque inputs and angle/velocity outputs for the same controller.
- MATLAB Function computes instantaneous acceleration only; Integrator blocks store state. Do not add another integration loop inside the function.

Use two z-axis Revolute Joints with gravity `[0 -9.81 0]`. Links extend along local x, centers lie at midpoints, and joints connect at endpoints. Explicitly match masses and centroidal Izz; visual shape alone does not establish equivalent dynamics.

Prescribed motion may help inspect assembly, but dynamic validation/control must use torque actuation with motion solved by the model. The [MathWorks double-pendulum example](https://www.mathworks.com/help/sm/ug/model-double-pendulum.html) teaches connections; this plan defines the parameters and angle conventions.

### Files and Results

Create this structure gradually:

```text
project/
  MATLAB_LEARNING_PLAN.md   # May be renamed PLAN.md; keep only one plan
  PROGRESS.md               # Current working memory
  PROGRESS_HISTORY.md       # Brief milestone archive
  THEORY_NOTES.md           # Concept index
  README.md                # Environment, entry points, run instructions
  startup.m                # Later configures project-local paths
  scripts/                 # Initialization, exercises, simulation entry points
  functions/               # Reusable kinematics, dynamics, and plotting
  models/                  # Manually constructed .slx files
  checks/                  # Functional-block validation
  results/                 # Data, figures, and run configurations
```

Entry points set paths and load parameters instead of depending on old workspace variables. Save numerical histories as MAT, tables as CSV, and figures as PNG, alongside parameters, initial states, solver, tolerances, output interval, and control period. Separate scenarios/runs rather than overwriting an unlabeled file. Label joints, reference/actual state, time, and units; preserve requested and applied torque. Git checkpoints can follow repository creation; neither commits nor publication are prerequisites for lesson one, and remote pushes are not assumed.

### PID and Trajectories

Start with PD and gravity disabled, then enable gravity to observe steady-state bias, then add integration:

\[
\tau_{\rm req}=K_p(q_r-q)+K_d(\dot q_r-\dot q)+K_i z.
\]

Use model-provided velocity, not a numerical angle derivative. The control period is 0.001 s with held output; distinguish it from plant integration steps. Saturate each joint at ±20 N·m. Conditional integration freezes a joint when error would worsen saturation and permits integration when error helps leave saturation.

Learn gains from zero in P, D, I order, recording reasons and results. Gains are an outcome of this stage, not copied from the old optimal set.

**Holding:** start at `[0;0] rad`, zero velocity, target `[0.3;-0.7] rad`, simulate 5 s. Each joint's maximum absolute error during the last second must be below 1 degree.

**Tracking:** move from `[-20;40]°` to `[40;-20]°` in 4 s using

\[
q_r=q_a+(q_b-q_a)(10s^3-15s^4+6s^5),\qquad s=t/4.
\]

Compute velocity/acceleration analytically and initialize consistently with the reference. Initial acceptance requires each joint's RMSE below 2 degrees, finite states, no sustained divergence, and valid torque limits. Then connect the same controller/gains to the physical model. Gravity compensation, CTC, payload, and disturbance studies remain extensions.

## 4. Validation and Learning Quality

Validate complete functional blocks rather than each line.

1. **Geometry:** endpoint positions must be `[0.9,0]^T m` at q=[0,0]^T, `[0,0.9]^T m` at q=[pi/2,0]^T, and `[0.5,0.4]^T m` at q=[0,pi/2]^T. MATLAB FK absolute error must not exceed 1e-10 m.
2. **Known dynamics:**

\[
M(0)=\begin{bmatrix}0.9216666667&0.23\\0.23&0.08\end{bmatrix},\qquad
G(0)=\begin{bmatrix}15.2055\\2.943\end{bmatrix}.
\]

Use absolute tolerance 1e-9 against these rounded values. Check symmetric positive-definite M and c=0 at zero velocity.

3. **Static equilibrium:** initial angles `[0.3;-0.7] rad`, zero velocity, constant G(q0), 2 s. Maximum drift of each joint must be below 1e-6 rad.
4. **Free motion/energy:** same initial state, zero motor torque, 2 s. Check

\[
E=\tfrac12\dot q^TM\dot q+g[(m_1l_{c1}+m_2l_1)\sin q_1+m_2l_{c2}\sin(q_1+q_2)].
\]

Use maximum energy drift 1e-5 J as the initial gate; inspect model and numerical accuracy before changing it.

5. **Cross-validation:** compare at `0:0.001:2` s. Maximum MATLAB-versus-Simulink-equation angle difference must be below 1e-6 rad; physical-versus-equation difference below 1e-4 rad. Compare aligned raw angles; do not use modulo operations to hide signs or zero-offset mistakes.

Reference solver settings: MATLAB/equation models use `ode45`; start the physical model with `ode15s`. Relative tolerance 1e-8, absolute tolerance 1e-10, maximum step 0.001 s. Record actual settings and check convergence by tightening tolerances/reducing maximum step. **Output sampling interval is not the solver's internal step.**

### Final Learning Acceptance

The user can explain each block's inputs, outputs, units, main components, and expected behavior. All three simulations use the same nominal model and conditions; investigate coordinates, inputs, initial states, and accuracy first when they differ. Preserve runnable work, necessary checks, concise theory notes, and conclusions. Retain failed cases for diagnosis; do not silently relax thresholds to declare success. Explain and record any justified acceptance change.

README instructions must work in a fresh MATLAB session without leftover variables. Initialization, models, checks, and figures must be available within the new project without installing the Python repository. Stage 8 is accepted only after the user completes and verifies PID, holding, and tracking, not merely because files were generated early.

## 5. Assumptions and Boundaries

Treat the user as a MATLAB/Simulink beginner; introduce mathematics, mechanics, and control as needed. The goal is credible two-link modeling and basic feedback control, not a paper, batch tuning, GitHub release, or predetermined winning controller. Ideal rigid links and torque sources exclude electrical motors, drives, transmissions, and hardware. Without dissipation, gravity-driven free motion does not stop by itself; do not secretly add damping to stop the animation.

Check display geometry and dynamic parameters separately, especially centers and inertia reference points. Do not repeat the entire Python study or transfer its environment/results/history into the new learning project. ROS, Gazebo, three-DOF models, MPC, reinforcement learning, vision, code generation, and real-time hardware require later planning. Record output interval, integration step, and control period separately; frame rate does not measure numerical accuracy. The original teaching policy favored Chinese with English terms; this plan is translated into English. Findings remain limited to simulation conditions.

## 6. Handoff and Resources

When moving this plan into a new project, read it and start at **Stage 0**. Existing Python results do not justify skipping MATLAB/Simulink foundations. Keep one plan (`MATLAB_LEARNING_PLAN.md` or `PLAN.md`), concise current progress, a brief chronological milestone archive, and the theory index. New sessions read current progress and relevant material rather than traversing the project.

Known local environment: MATLAB **R2023b Update 9**, executable `D:\matlab\bin\matlab.exe`; Simulink and Simscape installation directories were found, but runtime licenses and Multibody availability were not yet verified. Use local R2023b help rather than assuming newer features.

- Stage 1: [MATLAB Onramp](https://matlabacademy.mathworks.com/details/matlab-onramp/gettingstarted).
- Stage 3: [Simulink Onramp](https://matlabacademy.mathworks.com/details/simulink-onramp/simulink).
- Stage 5: [Integrator documentation](https://www.mathworks.com/help/simulink/slref/integrator.html).
- Stages 6-7: [Simulink/Multibody double-pendulum comparison](https://www.mathworks.com/help/sm/ug/double-pendulum-in-simulink-and-simscape-multibody.html).

**Initial status: Stage 0 is not accepted. Prior teaching instructions do not establish completed user operations.**

**Lesson one only: verify the environment, identify the MATLAB interface, and create/run a small script storing the two link lengths.**
