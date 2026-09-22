# Stage 20: External-Force Disturbance Results

Stage 20 was completed on 2026-09-13. Stage 16's frozen gains, candidates, trajectories, and experimental protocol were unchanged.

## Conditions and Outputs

- The nominal 0-8 s held-out five-waypoint trajectory, initial state, and model; 0.001 s control period and ±20 N·m motor limits.
- A 10 N endpoint force along positive base-frame x during [4.5, 4.7) s, spanning 200 integration intervals.
- Actual-configuration `J(q)^T F` acts on the plant. Endpoint force is held per interval; joint external torque is recomputed at every RK4 substep. Motor commands retain the existing sampled hold.
- Latest results: [20260913T114926_385587Z](20260913T114926_385587Z/). Each run produces 13 files: three NPZ/YAML/metadata sets, a frozen snapshot, CSV, summary JSON, and a six-panel figure.

## Numerical Results

| Controller | Full-run joint RMSE (deg) | Full-run endpoint peak (mm) | Endpoint peak from 4.5 s (mm) | Peak time (s) | Recovery delay (s) | Saturation |
|---|---:|---:|---:|---:|---:|---:|
| PID | 1.103720 | 54.107 | 27.644 | 4.711 | 1.555 | 0.0% |
| PID + Gravity | 0.176402 | 17.564 | 17.564 | 4.706 | 0.087 | 0.0% |
| CTC | 2.237485 | 102.448 | 102.448 | 4.714 | 0.263 | 0.0% |

The peak from 4.5 s is computed from raw NPZ errors over 4.5-8 s. It is the reference-to-actual endpoint distance, not a pure disturbance increment obtained by subtracting nominal motion. The CSV field `maximum_end_effector_error_m` covers 0-8 s. PID's peaks differ because its full-run maximum occurs before the disturbance.

Recovery requires endpoint error at or below 10 mm for at least 0.5 s after force removal. The returned value is the qualifying window's start minus 4.7 s, not the later confirmation time. Window starts are 6.255 s for PID, 4.787 s for PID+Gravity, and 4.963 s for CTC; confirmation occurs at 6.755, 5.287, and 5.463 s. All recover here. Unconfirmed recovery is represented by `recovered=False`, JSON null, and blank CSV fields, with test coverage.

## Execution Flow

1. `run_disturbance_controller` validates frozen settings/gains, creates an independent disturbance scenario, and selects PID, PID+Gravity, or CTC.
2. Each control interval calls `external_tau_factory(time, step, actual_params)`. The factory determines whether force is active and returns a closure retaining F and the actual model.
3. The closed-loop step computes and saturates the motor command. Each of RK4's four derivative evaluations passes its predicted configuration to the closure to compute `J(q)^T F`.
4. Dynamics solve `M(q) q_ddot = tau_motor + tau_external - c - G`, and RK4 advances the state.
5. Summary functions calculate tracking error, actual-motor effort, saturation, and mechanical work, then scan qualifying recovery windows.
6. Saved records include full histories, endpoint errors, sampled forces/external torques, configuration hashes, software versions, Git state, and relevant source hashes. Plotting reads saved results only.

Recorded external torque uses the actual interval-start configuration; the final sample records its instantaneous value. It is neither a constant joint torque over the interval nor a record of every internal RK4 substep. Motor and external torques are stored separately; effort includes actual motor output only.

## Interpreting CTC's Larger Peak

CTC compensates known inertia, Coriolis, and gravity, not unknown external force. With an exact model and ideal continuous unsaturated control, `e = q_ref - q` satisfies `e_ddot + Kd e_dot + Kp e = -M(q)^(-1) tau_external`. External force still drives error through actual inertia. This sampled implementation also has discrete-update effects.

Frozen gains were selected on the predefined training task, not this disturbance. PID+Gravity has the smallest response peak and fastest recovery here; CTC has a larger peak but recovers faster than PID. These findings apply only to this trajectory, force direction/magnitude/duration, and gains. None saturates, so CTC's peak cannot be attributed to motor clipping.

## Original Validation and Reproduction

- Full pytest: `189 passed in 5.42s`; Ruff lint/format passed for nine related files.
- Through 4.5 s, all three controllers' states, references, motor torques, saturation, and PID integral histories exactly match nominal results.
- Independent window scanning confirms recovery; force lasts exactly 200 intervals; external torque matches the actual Jacobian mapping; all histories are finite.
- First directory `20260913T114801_430829Z` and reproduction directory `20260913T114926_385587Z` have identical NPZ fields, shapes, and dtypes. YAML, CSV, summary JSON, and frozen snapshots are byte-identical; the 2800×2200 six-panel figures are pixel-identical. Metadata timestamps and Git state may differ; file/configuration hash associations were checked.
- No per-block validation JSON files were added. Twelve persistent test cases cover boundaries, recovery windows, file saving, unrecovered status, and plotting failures.

From the installed project root:

```powershell
python experiments/run_disturbance_benchmark.py
```

Redraw existing results only:

```powershell
python experiments/plot_disturbance_benchmark.py results/disturbance/20260913T114926_385587Z
```

[Six-panel figure](20260913T114926_385587Z/disturbance_comparison.png) · [Summary CSV](20260913T114926_385587Z/disturbance_metrics.csv)

The next stage at the time of this record was Stage 21: combine nominal, payload, model-error, and force-disturbance data into unified tables and planned core figures.

## Learning Supplement (2026-09-14): Tracking Error and Additional Disturbance Deviation

The read-only script `experiments/analyze_disturbance_response.py` reads existing nominal and Stage 20 NPZ files. It does not rerun simulations, change frozen gains, or replace official metrics. Outputs are the [comparison figure](learning_analysis/nominal_vs_disturbance.png) and [diagnostic table](learning_analysis/diagnostics.csv).

- Formal error compares the actual endpoint with the reference. The diagnostic compares disturbed and undisturbed endpoints for the same controller, measuring additional trajectory deviation. These distances are distinct.
- PID's formal delay is 1.555 s. Applying the same criterion to nominal data from 4.7 s takes 2.755 s to find a qualifying window. Its additional deviation returns within 10 mm for 0.5 s after only 0.119 s. The entire 1.555 s therefore cannot be interpreted as slow disturbance decay.
- PID / PID+Gravity / CTC additional-deviation peaks are 34.680 / 22.895 / 102.366 mm, with diagnostic delays 0.119 / 0.136 / 0.262 s. These supplement the official metrics and do not justify retuning.
- Freeze the actual configuration at 4.5 s and add only 1 degree of joint-2 position error, holding other terms fixed: proportional joint-2 torques are 1.793 N·m for PID, 3.383 N·m for PID+Gravity, and 0.199 N·m for CTC. CTC also produces about 0.504 N·m at joint 1. PID directly outputs proportional torque; CTC outputs virtual acceleration mapped through M(q). Gain numbers are not directly comparable.
- Initial additional joint-2 acceleration is approximately -65 to -66 rad/s² for all controllers, but subsequent closed-loop resistance differs. CTC's joint-2 peak error is about 20.795 degrees, consistent with its weaker proportional torque response here. Coupling, derivative/integral terms, and trajectory changes prevent a single-cause explanation.
- PID+Gravity and PID have separately tuned gains, so this compares complete controller designs. Isolating gravity compensation requires an additional matched-gain comparison. Nominal tracking, disturbance peaks, threshold recovery, and internal stability are separate issues; finite simulations cannot establish global stability.

Theory references: [Modern Robotics 11.4](https://modernrobotics.northwestern.edu/nu-gm-book-resource/11-4-motion-control-with-torque-or-force-inputs-part-3-of-3/) and [MIT Manipulator Control](https://manipulation.mit.edu/force.html). Numerical explanations come from the local raw histories and controller implementation.
