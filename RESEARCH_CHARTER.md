# Two-DOF Robot Arm Control: Research Charter

## Main Research Question

For the same robot, target motion, and simulation conditions, compare PID, PID with gravity compensation, and computed torque control (CTC): which tracks most accurately under nominal conditions, and which maintains performance better with unknown payloads, model-parameter errors, or external endpoint forces?

## Subquestions

1. How much does gravity compensation or full model compensation improve performance with an accurate model?
2. Which controller degrades fastest with an unknown endpoint payload?
3. How does CTC's advantage over PID change when its mass and inertia parameters are wrong?
4. Which controller recovers fastest after the same endpoint force, and does this require larger control inputs or more torque saturation?

## Predictions Before Experiments

1. CTC will have the smallest tracking error with an accurate nominal model.
2. CTC will degrade fastest when an endpoint payload is unknown to the controller.
3. CTC's advantage over ordinary PID will decrease as internal model-parameter error grows.
4. PID with gravity compensation will return to the target trajectory fastest after the same endpoint force ends.

These are predictions, not predetermined conclusions. A prediction contradicted by data is still a valid research finding.

## Experimental Variables

- Independent: controller type, endpoint payload, controller-model parameter error, and endpoint force disturbance.
- Dependent: joint and endpoint RMSE, peak endpoint error, recovery time, control effort, mechanical work, and torque-saturation fraction.
- Controlled: reference trajectory, initial state, simulation step, torque limits, nominal plant parameters, tuning budget, random seed, and metric definitions.

## Success Criteria

- Fair comparison under identical conditions.
- Repeatable results with the same configuration and seed.
- Raw data, aggregate metrics, and figures supporting every conclusion.
- No requirement that any particular controller wins.

## Core Scope

- A rigid two-DOF robot arm moving in a vertical plane, simulated entirely in Python.
- PID, PID with gravity compensation, and CTC only.
- Nominal, payload, model-uncertainty, and disturbance experiments only.

## Limitations

- The core model excludes friction, backlash, delay, and sensor noise.
- Software results must not be described directly as hardware performance.
- ROS, Gazebo, three-DOF models, MPC, reinforcement learning, vision, and physical hardware are outside the core project.
- Friction, encoder noise, and Cartesian trajectories are extensions after core release `v1.0.0`.
