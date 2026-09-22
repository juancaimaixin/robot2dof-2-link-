# Two-DOF Robot Arm Project Progress

> Updated: 2026-09-20. Full dated archive: [PROGRESS_HISTORY.md](PROGRESS_HISTORY.md).

## Current Status

- Python Stages 3-22 are accepted. Stage 22 assembles HTML and a 12-page PDF from frozen results, retaining all 42 evaluation runs and eight core figures. Stage 16's 900 candidates and protocol remain frozen.
- English edition completed on 2026-09-20: documentation, internal stage/document names, report tables, analysis prose, and the derivation figure are English. Raw experiments, configuration, gains, and all 14 core Python modules are unchanged.
- English validation: 202 tests passed; Ruff lint and Stage 21/22 formatting passed. All three nominal controllers were rerun from this source tree and every simulation-history array exactly matched the saved nominal run. HTML browser inspection and all 12 PDF pages passed visual checks.
- One pre-existing malformed test line was repaired only in this copy. `run.ps1` selects this copy's source and prevents Git discovery from inheriting the parent project. `LOCALIZATION_VALIDATION.json` records the checks.
- Original uncommitted work includes Stages 13-22. Latest recorded checkpoint: `6ea478f`, `feat: add quintic trajectory animation`. No commit, push, or public release was performed for this translation.
- Report entry point: `stage22/build_report.py`; outputs: `stage22/output/report.html` and `stage22/output/report.pdf`; instructions: `stage22/README.md`.
- The original 2026-09-17 report passed deterministic rebuilding: identical HTML bytes and PDF extracted text/page pixels, excluding variable PDF timestamps. Its browser check was blocked then; this English edition's browser check succeeded.
- MATLAB handoff: `MATLAB_LEARNING_PLAN.md` was created on 2026-09-11. Only its plan is complete; MATLAB Stage 0 has not been accepted.
- Next research stage: Stage 23, demo and public release. Publication requires separate explicit authorization.

## Working Agreement

- The user normally writes source; the assistant explains, reviews, and verifies one concept or complete functional block at a time.
- Earlier implementation authorizations covered tuning changes and Stages 20, 21, and 22 individually. The current authorization covers this English copy; it does not authorize publication.
- Use the cycle: complete functional block → consolidated pytest/Ruff validation → milestone record.
- Do not create progress entries for individual lines, whitespace repairs, or separate tests. Since 2026-09-08, check new key normal/failure paths and avoid repeating previously verified dynamics/metrics/hashes without a new concern; do not create validation JSON for every small block.
- Keep this summary current; put detailed dated records in `PROGRESS_HISTORY.md`. Add only concise theory indexes to `THEORY_NOTES.md`.
- Internal units are SI and radians.

## Stage Overview

| Stage | Status | Key evidence |
|---|---|---|
| 0. Research charter | Passed | Main question, four subquestions, predictions, variables, success criteria, limitations |
| 1. Environment | Passed | Conda robot2dof, Python, VS Code, Git, Quarto, Jupyter |
| 2. Project skeleton | Passed | Installable package, tests, Ruff, structure, environment; checkpoint d4a9409 |
| 3. Foundations | Passed | Linear solves, centered differences, scalar RK4, broadcasting; repeated unit-conversion exercise waived based on existing evidence |
| 4. Reproducibility | Passed | Seeds, modules, tests, environment, checkpoints, consolidated acceptance |
| 5. Coordinates/parameters | Current scope passed | Planar relative angles, SI/radians, consistent geometry; dynamics parameters added before Stage 9 |
| 6. FK | Passed | Analytic/transform methods, known poses, 100 random checks; checkpoint 790c248 |
| 7. IK | Passed | Reachability, both branches, normalization, invalid inputs, round trips, figure; checkpoint 40459a1 |
| 8. Jacobian | Passed | Maximum finite-difference discrepancy 1.579e-10; singularity, J^T F, determinant figure |
| 9. Lagrangian dynamics | Passed | T/V from center motion; M/G/c independently verified with Hessian, potential gradient, Christoffel formulas |
| 10. Numerical dynamics | Passed | M/c/G/forward dynamics; 1000 random symmetric positive-definite matrices; gravity and dynamics checks |
| 11. Simulator | Passed | RK4 step-halving ratio 14.484629; DOP853 difference 1.248e-8; energy drift 2.451e-9 J |
| 12. Quintic trajectory | Passed | Single/multisegment endpoint constraints; five-waypoint three-panel figure |
| 13. PID | Passed | Conditional integration, common limiter, sampled loops/history, stable training, plots |
| 14. PID+Gravity | Passed | Static, one-step, and multistep nonzero-pose balance; separate plant/controller models |
| 15. CTC | Passed | Correct-model error dynamics, one/multistep loops, stable training |
| 16. Tuning/freeze | Passed | 300 candidates/controller, 900 total; configuration SHA-256 50247f53d83e161b5419f0e59216c5064f2d6f8700eca295f6dc253e140ec3da |
| 17. Nominal | Passed | One-command data/metrics/six-panel rebuild; arrays/CSV match first run |
| 18. Payload | Passed | Five masses × three controllers; data and three-panel plot reproduced; lint passed |
| 19. Model error | Passed | 21 runs, metrics, three-panel plot; 66-file acceptance; gains frozen |
| 20. Disturbance | Passed | Three runs, six-panel plot; recovery 1.555/0.087/0.263 s; 13 files; no saturation |
| 21. Analysis | Passed | 42 runs/eight figures/report; all 11 output files reproduced byte-identically; 198 tests |
| 22. Report | Passed | Common-source HTML/12-page PDF, research narrative/all runs; clean renders; 202 tests |

## Preserved Stage Records

The following records describe the project when written. Earlier pending items, trajectories, and validation results are historical; the current status above takes precedence. Archive translation used offline assistance, while the current summary and main research documents were edited directly.

## Stage 22 Current progress

- 2026-09-17: Newly built data-binding constructor in `stage22/`, Quarto template, style, 4 key test and README. Using the installed Quarto 1.10.18 and Typst 0.15.1, the same source generates HTML/PDF without modifying the environment or original simulation. 
- The report contains Chinese-language headings and abstracts, Introduction/Model/Trajectory/Controllers/Methodology/Results/Discussion/Limitations/Conclusion, methods of reproduction and 42 group annexes; Automatically input numerical values, configuration, gain, grid with 8 graphs, responding step by step to four predictions and distinguishing indicators and explanations of causes. 
- The complete pytest for 202 passed in 6.22s, the phase 22 Ruff lint/format passed through; Two logs constructed with no warnings/error. HTML byte is consistent, PDF extracts text is consistent, and 12 pages are consistent with the pixels after being rendered at a 1100-pixel scale; PDFs are created/modified differently, and do not require byte consistency. 
- PDF full-page visual inspection passed; HTML static checks for 8 embedded images, 42 a MathML formula, internal references are complete, no external script/style dependence. The actual HTML browser preview is automatically approved for use of quantitative restrictions denied, not bypassed, not claimed by browser visual checks. See also `stage22/verification.json`. 

## Stage 21 Current progress

- 2026-09-17: Unified reading of validated nominal/payload/model_uncertainty/disturbance 3 / 15 / 21 / 3 group NPZ/YAML/CSV; Recalculation indicators consistent with existing aggregates. Each row retains source paths and configures hashes; New RMSE multiplier relative to its own nominal, without modifying the official indicator. 
- 8 chart includes nominal position, error, motor torque, indicator contrast, load sensitivity, model error sensitivity, disruption response and recovery/peak. Certainties don't add an error bar; Maintenance of all malfunctions and saturation working conditions, differentiation between control effort/mechanical function, formal recovery/nominal deviation diagnosis. 
- `stage21/output_2f080606329f/` together with 11 files ((8 PNG, CSV, Markdown, manifest); Rebuild a single command after clearing the generated directory, aligning all files byte byte. Complete pytest with additional 9 cases for 198 passed in 7.38s; Phase 21 Ruff lint/format with image inspection passed. No simulation or tuning, no changes to the original results and environment. 

## Stage 20 Current progress

- Learning supplement (2026-09-14): analyze_disturbance_response.py reads existing nominal/disturbance data and creates comparison figures/CSV. PID formal recovery of 1.555 s is affected by baseline tracking error; nominal-relative diagnostic delays are 0.119 / 0.136 / 0.262 s for PID / PID+Gravity / CTC. Explained gain units and proportional torque differences. Official metrics/gains were unchanged, no simulations rerun; Stage 21 had not started at that time.

- Final acceptance (2026-09-13): the user authorized the assistant to complete remaining Stage 20 work. Existing user-written scenarios, runner, recovery functions, summaries, and snapshots were extended with NPZ history, YAML/metadata, CSV/summary JSON, unified execution, a six-panel plot, and 12 key tests; related formatting was consolidated.
- External force maintaining fixed protocol: base coordinate system F=[ 10 , 0 ] N, action [ 4.5 , 4.7 ] s, total 200 one 0.001 s interval; Each RK4 sub-step is updated to the actual q by J(q)^T F, engine torque independently saved and statistically. The entire core history of the 4.5s prior to disruption is exactly consistent with the existing nominal. 
- All three controllers are restored without saturation. In the order PID/PID + Gravity/CTC, the recovery delay is 1.555 / 0.087 / 0.263 s, 4.5 8 s end effector peak is 27.644 / 17.564 / 102.448 mm; Full 0 8 s Maximum error is 54.107 / 17.564 / 102.448 mm. The recovery window was verified by independent 501 point scanning, concluding that only this frozen gain and protocol. 
- The unified command generated results/disturbance/20260913T114801_430829Z/ and reproduced it at results/disturbance/20260913T114926_385587Z/, with 13 files each. NPZ fields/shapes/dtypes match, YAML/CSV/summary JSON/frozen snapshots are byte-identical, the 2800×2200 six-panel plot is pixel-identical and visually verified, and metadata file/configuration/source hash associations are correct.
- The ultimate complete pytest is for `189 passed in 5.42s`; 9 related file Ruff lint/format All approved, block by block validation JSON not added, frozen configuration and gain unchanged. The results are explained by the code process see [Stage 20 results](results/disturbance/STAGE20_RESULTS.md). Phase 20 is completed and phase 21 is due to begin. 

## Stage 19 Current progress

- 2026-09-11 Final validation: The user explicitly authorizes the assistant to complete the remaining phase of 19. Assistant adds `experiments/plot_model_uncertainty_benchmark.py`, accesses unified running scripts and organizes formats; The three-dimensional graph shows the overall joint RMSE, control effort and saturation in percentage errors, using the payload graph style. Read existing CSVs, i.e. independent drawings, missing/repeatable lines, and non-finite metrics to reject and not generate images. 
- The Unified Command successfully reconstructed the `results/model_uncertainty/20260911T025328_299278Z/` file under 66: 21 group NPZ/YAML/JSON, frozen snapshots, CSV and PNG. All NPZ fields and YAML configurations of the 21 group are fully consistent with the first official result, CSV is consistent with frozen snapshots byte, PNG 3000 × 960 pixels are consistent and through visual inspection, the new metadata configuration/file hash is associated correctly. 
- Finally, the complete pytest for `177 passed in 4.09s`, benchmark.py, results_io.py, running the Ruff lint and format check of the script and drawing the script all passed. Temporary check file cleared, no additional duration testing or validation JSON, frozen gain unchanged; Stage 19 completed. The next stage is the phase 20 External Disruption Experiment. 

- 2026-09-11 first official experiment: the user has written a unified run script and compiled the module format, running `experiments/run_model_uncertainty_benchmark.py` successfully generated `results/model_uncertainty/20260911T023540_313114Z/`. 7 errors x 3 controllers save NPZ/YAML/JSON, plus frozen snapshots and 21 row/13 column CSV, a total of 65 files that have not yet been mapped. 
- Official results checked: 21 state sample of each 8001 group, actual plant fixed, controller model deviation correct, history and CSV limited, overall joint RMSE consistent with the array recount, configuration/file hash correlation correct, frozen snapshot consistent with the source file byte. All the historical arrays with zero controller errors are consistent with `results/nominal/20260907T024619_815442Z/`; Seven degrees of pure PID, all history is consistent with nominal. All groups have no saturation and peak actual torque `17.976295696 N·m`. 
-  It's a mistake. 30 %, - 20 %, - 10 %,  0 , + 10 %, + 20 %, + 30 Total joint RMSE in % ordered ((degree): all PIDs are `1.1150369719` ; PID + Gravity for `0.372386723 / 0.280691241 / 0.200772255 / 0.152634055 / 0.166760035 / 0.232167956 / 0.318798229`; CTC for `2.828458470 / 1.657619251 / 0.739656293 / 0.004992082 / 0.611065909 / 1.125611951 / 1.566751147`. Conclusions are limited to the frozen gain, trajectory and error grid, and are not retuned accordingly. 
- Unified entrance and two modules of Ruff lint; benchmark.py/results_io.py format check Passed, the new running script only lacks the end of the line. The most recent complete result is `177 passed in 3.49s`, no JSON validation has been added, and Python has not been modified by the wizard. The next block is the drawing script, followed by access to the Unified Input Completion Stage 19 Repeat validation. 

- 2026-09-11: Users have already written to `ModelUncertaintyScenario` and `create_model_uncertainty_scenario(relative_error)`. The actual plant is equivalent to the nominal, controller-only model m2/I2 with the proportional change under the seven-degree default error; The zero-error model is consistent with the nominal, trajectory/initial/external torque arrays called independently, modifying the isolation through; Five unlimited or less errors equal to - 1 rejected prior to the creation of the scene. 
- The complete pytest is for `177 passed in 5.07s` (this time the pytest cache plug-in is turned off), and the benchmark.py is directed by Ruff lint; Format check only requires adding a single line of `raise ValueError(...)`. Special verification runs in memory, no additional duration testing or JSON validation, no modifications to Python, no formal experiments run. 
- 2026-09-11: Users have already written to `ModelUncertaintyRun` and `run_model_uncertainty_controller(...)`. 3 controller x 7 error total 21 A simulator replacement case confirming the complete parameter connection, branch selection and result packaging correctly, independent of the gain/initial state array across calls; 15 An illegal error, an unknown controller and three frozen hash errors were rejected before simulation. 
- Non-zero static gesture `[0.3, -0.7] rad`, 0 0.003 s Four sample real simulation: three controllers zero error all history and short time nominal input results are completely consistent; ± 30 % below pure PID all history unchanged, PID + Gravity / CTC initial request torque changes with model error; Historically limited and actual torque meeting the 20 N·m limit. This is a short-term development inspection, not officially maintained trajectory. 
- Running Input Central Check: The complete pytest is for `177 passed in 3.38s` (closed caching plugins), benchmark.py is directed through Ruff lint; The format check still only tells the scene factory to change ValueError. Special verification runs in memory, no new duration testing or validation JSON is added, and the assistant does not modify Python. 
- 2026-09-11: Users have written to `summarize_model_uncertainty_run(...)`. All three controllers output the controller, relative_error and 11 physical indicators, which are 13 rows; Synthetic history of joint/end effector errors, actual torque control effort, saturation ratios are consistent with mechanical functions, the unit and endpoint statistical semantics of rad/degree/m are correct. actual plant, parameter transmission, common float type, JSON/CSV back and forth, original history maintained and unlimited status refused to pass. 
- Complete pytest for `177 passed in 3.38s` (closed caching plugins), benchmark.py directed by Ruff lint; The format check is still only for the scene factory ValueError. Not running simulation, not adding duration testing or validation JSON, not modifying Python. 
- 2026-09-11: Users have written to `build_model_uncertainty_configuration(...)`. In the 21 group configuration with three controllers x seven grades of error, the actual/controller model, error, frozen gain, trajectory/initial and output names are correct; Controller_model=None for pure PID, initial_integral_error=None for CTC. JSON/YAML is backwards consistent with the hash, and the 21 group filenames differ from the configuration hash; Two-way separation of the configuration from the source array and change of the new configuration hash after modification of the gain/track; Five unlawful errors rejected and hash functions rejected unlimited configurations. 
- Configuring snapshot central check: complete pytest for `177 passed in 3.34s` (closed caching plugins), benchmark.py/results_io.py directed Ruff lint passed, results_io.py format check passed; benchmark.py is still only telling the scene factory ValueError to switch. Checking memory execution, not running simulation, not adding duration testing or validation JSON, not modifying Python. 
- 2026-09-11: Users have written to `save_model_uncertainty_history(...)`. The complete history of the controller can be read back accurately by field, shape, dtype under allow_pickle=False; Actual/reference end effector location, constant external torque, calibration error, controller name and two configuration hashes correct, keeping PID/CTC field difference. Compressed, source history kept and file byte of the same name unchanged; Unlimited state/external torque, illegal errors and incorrect extension names rejected before the output directory is created. 
- Complete pytest for `177 passed in 4.06s` (closed caching plugins), benchmark.py/results_io.py directed through Ruff lint, and results_io.py format passed through; benchmark.py is still only telling the scene factory ValueError to switch. Checking temporary directories using synthetic history and cleared workspaces, not running formal simulation, not adding persistent testing or validation JSON, not modifying Python. 
- 2026-09-11: Users have written to `save_model_uncertainty_manifest(...)`. Three controllers NPZ/YAML/JSON controller, error, configuration/tuning hash and historical files SHA-256 correlated correctly, YAML configuration back and forth, true Git commit/dirty/status, software version and UTC time recording correctly. Repeat Save and keep the three files byte unchanged; Lack of NPZ, four identifier/hashes not matched, separately existing YAML or JSON are both rejected and no new manifest is added, and Git has not yet been called when not matched. 
- Manifest centralized checking: complete pytest for `177 passed in 3.35s` (closed cache plugins), benchmark.py/results_io.py directed by Ruff lint, and results_io.py format by; benchmark.py is still a scene factory ValueError switch. Checking temporary directories using synthetic history and cleared workspaces, not running formal simulation, not adding persistent testing or validation JSON, not modifying Python. 
- 2026-09-11: Users have written to `save_model_uncertainty_summary(...)`. 21 rows, 13 rows written in the prescribed order, read back the line indicator accurately; An inverse input is equivalent to an output byte of CSV. Coverage and protection through; Missing/excess/repeated cases, unknown controllers, grid layouts and unlimited errors, erroneous extension names and non-finite metrics are all rejected before output is created. 
- Complete pytest for `177 passed in 3.49s` (closed caching plugins); Ruff lint reports results_io.py Import order I 001 needs to be moved to summarize_model_uncertainty_run before summarize_nominal_run; Format check Requires rows to be synthesized as a row, benchmark.py original ValueError rows are still to be sorted. Checking temporary directories using synthetic history and cleared workspaces, not running formal simulation, not adding durable testing/validation JSON, not modifying Python. The next block is the Unified Running Script `experiments/run_model_uncertainty_benchmark.py`, which the user writes and connects to. 

## Phase 17 validation results

- The first official experiment has been completed: `results/nominal/20260906T080613_586557Z/` saved three sets of NPZ/YAML/JSON, `nominal_metrics.csv`, frozen copies of the training file with independent `verification.json` (SHA-256, which actually uses source code/environment files). 
- Formal overall joint RMSE ((degree): PID `1.1150369719`, PID + Gravity `0.1526340555`, CTC `0.0049920823`; The end effector RMSE(m): `0.0253661136 / 0.00351928025 / 0.000037206997`. The third saturation instance is 0 and cannot be modified according to frozen gain. 
- Location/error/actual torque Six-dimensional graphs have been generated and verified visually; Users have completed the Unified Input Connection and two script formats. 2026-09-07 Unified Command successfully reconstructed the three sets of data, CSV and PNG, and the phase 17 was finally passed. 

- The user has written `src/robot2dof/benchmark.py`: `NominalScenario` and `create_nominal_scenario()`. 
- The official five waypoints, stop values, nominal plant/model, `0.001 s` step length and `20 N·m` limit are defined. 
- `load_frozen_gains(path, controller)` has been verified: Fixed configuration hashes with optimal ID, candidate/gain consistency, abnormal rejection and newly created gain arrays. 
- `NominalRun` and `run_nominal_controller(...)` have verified three controller branches, independent scenarios, frozen failure pre-stop, and the history of four static development cases of actual simulation machines. 
- In `src/robot2dof/metrics.py`, `TrackingMetrics` and `compute_tracking_metrics(...)` have both joint/total RMSE ((rad and degree) ,  end effector RMSE and maximum error ((m); All location samples include endpoints. 
- `ActuationMetrics` and `compute_actuation_metrics(...)` have verified that the actual torque control effort, saturation interval time ratio is approximate to the absolute mechanical power left rectangle; end effector output exclusion, mechanical power demands total joint power to recover absolute value. 
- `summarize_nominal_run(...)` has verified the 12 column metric sum of the three controllers, containing the controller name and the physical indicator 11; Column names, units, status clips and JSON/CSV read back and forth correctly. 
- `results_io.py`'s `save_nominal_history(...)` has been verified in full history, actual/reference end effector location, nominal constant external torque and tuning configuration hash NPZ saved; Keeping PID/CTC field differences and refusing to cover existing files. 
- `build_nominal_configuration(...)` and `compute_configuration_sha256(...)` have verified that the actual scene/gain snapshot, model and score distinction, JSON/YAML return and key sequence do not affect hash; Nominal seed=None indicates that certainty is running. 
- `save_nominal_manifest(...)` has verified YAML configuration with JSON data stored, NPZ has added a new formal configuration hash; 3 file hash links, Git commit/dirty status, software version, UTC recording time and file protection correctly. PyYAML 6.0.3 has been explicitly recorded to environment.yml. 
- `save_nominal_summary(...)` has verified the three controllers one at a time, fixed sequence, 12 column indicators, finite values, checking with existing CSV protection; The Unified Experimental Script has been connected and completed for the first time. 

## Stage 18 Current progress

- 2026-09-11 Final centralized validation: the user has accessed the unified map and compiled the format, a command successfully reconstructed `results/payload/20260911T014147_244577Z/` under 15 group NPZ/YAML/JSON, frozen file copies, CSV and PNG, all 48 files. All NPZ arrays are the same as the first official result of the YAML configuration, CSV is the same byte, PNG 3000 × 960 pixel is the same, and visual inspection is passed; New metadata hashes are correct, frozen files remain unchanged. 
- The final pytest is for `177 passed in 6.95s` (already caching warnings), with six related file formatter checks passed. 2026-09-11 users have modified the mapping import sequence of `experiments/run_payload_benchmark.py` to direct `ruff check --no-cache experiments/run_payload_benchmark.py` output to `All checks passed!`, phase 18 completed. This time, no simulation, pythest, or format checks were repeated, and the assistant did not modify Python source code. 

- `RobotParams.payload_mass` by default `0.0 kg`; Users have accessed `mass_matrix()`, `coriolis_vector()`, `gravity_vector()` in the end effector point quality increase. `forward_dynamics()` Repeats the same actual parameter object without additional connections. 
- For each `0, 0.25, 0.50, 0.75, 1.00 kg` verify the random state of a fixed seed of 1000: mass increase with `m_p J^T J`; gravity increase with limited power differential and power mapping; Coriolis increase with `m_p J^T J_dot q_dot`. The total mass matrix has a minimum characteristic value of about `0.02124946`, all of which are correct; Known answers, static equilibrium, dynamic energy constant equations and independent Descartes charge recovery acceleration are all passed. 
- 3 Controller Zero Load Full nominal simulation running in memory, full simulation history array exactly the same as `results/nominal/20260907T024619_815442Z/`, frozen file SHA-256 unchanged. The new configuration only adds `payload_mass: 0.0` to the model dictionary, so the new configuration hash is different; After removing the new add-on, the old configuration and hash were fully restored. Old results are not rewritten, do not mistakenly extend this format for retuning. 
-  The validation report: `results/payload_dynamics_verification_20260907T113954_361730Z.json` . Full pytest `177 passed in 6.02s` (both with caching permission warnings), full repository Ruff lint passed; Format check Instructions for dynamics.py Three-dimensional expression switches and parameters.py end switches. This load-specific inspection is a temporary verification, with no new lasting pytest; Python source code not modified by the assistant. 
- `PayloadScenario` and `create_payload_scenario()` have been verified: five preset quality, zero load and nominal phase-by-phase consistency, actual independence from controller models, non-sharing and modified isolation across call arrays; Negative quality and NaN/Inf refused before the creation scene. Formal trajectory, stationary initial value, zero points/out-of-torque, 0.001 s walk length is consistent with the 20 N.m limit. 
- Complete pytest for `177 passed in 3.71s` (already caching warnings), full repository Ruff lint and benchmark.py formatter check; parameters.py/dynamics.py still has previously recorded pure format differences. Special checks are for temporary verification, without adding a persistent pytest, without modifying the source code or running a simulation. 
- `PayloadRun` and `run_payload_controller()` have been verified: three controllers x five masses total 15 simulator replacement wiring case, 12 illegal masses case, unknown controller and frozen damage, hash stop, scene and gain group isolation both passed. 3 Controller Zero Load Full Simulation of 8001 Samples History and Stage 17 Results are completely consistent. 
- 0.5 kg, fixed posture `[0.3,-0.7] rad`, 0 aluminum 0.003 s four samples; Initial actual torque is zero output of pure PID or no load model gravity compensation, with load plant Subsequent movement, history limited, actual torque meeting the upper limit. Officially maintained non-zero load trajectory. 
-  I'm going to run an entry validation report: `results/payload_runner_verification_20260907T121946_105956Z.json` . Complete pytest `177 passed in 3.64s` (already caching warnings), full repository Ruff lint passed; benchmark.py The 326 line has a tail space, and the parameters.py/dynamics.py still has an existing format difference. Special checks running temporarily, with no new endurance testing or modification of the source code, frozen Results file hash unchanged. 
- `summarize_payload_run()` has been verified: controller, `payload_mass_kg` and 11 are 13 rows of physical indicators, and the values are Python float; Three controllers x five masses total 15 A synthetic case checks the quality source, actual geometry, state slices, end effector sample size, actual torque with total power, scaling ratio and JSON/CSV memory back and forth. The known range indicators are control effort `37.5 (N·m)^2·s`, saturation ratio `0.5`, absolute mechanical power `3.5 J`. 
- From the conserved NPZ rebuild the zero load history of the three controllers, the new summary removes the quality list completely in line with the nominal summary and the old CSV; This is not a new simulation. The complete pytest `177 passed in 6.93s` (already with caching warnings), the entire repository Ruff lint is passed, and the three files still have previous format differences.  The validation report: `results/payload_summary_verification_20260908T010537_799824Z.json` ; Special checks are temporary running, endurance tests are not added or the source code is modified, result files are frozen unchanged. 
- `save_payload_history()` has been verified: three controllers × five masses total 15 group complete history NPZ back and forth, PID/CTC field difference, data type, actual load mass with geometry, complete end effector sample, constant external torque, frozen tuning, hash correct; `allow_pickle=False` readable, compression mode, absolute return path, parent directory creation and large-scale extension names are all through. 
- Save refused checks by: 15 group already has file byte protection; 12 illegal quality; 69 unlimited history; 3 illegal extension name; and 6 unlimited scenario/derivative outcome cases; illegal input refused before creating the output parent directory. Temporary files cleared, not running simulation or modifying source code. 
- NPZ foundation preservation validation report for `results/payload_history_verification_20260908T011315_043482Z.json`; At the time, there was no access to hash configuration for load experiments. The complete pytest `177 passed in 3.60s` (both caching warnings), the complete repository Ruff lint and results_io.py format checks are passed, and the other three files still have the same format differences. 
- `build_payload_configuration()` and NPZ `configuration_sha256` have been verified: 15 group configuration, 15 unique experiment hash and 45 non-conflicting NPZ/YAML/JSON filename; Accurate recording of actual load models, controller models, frozen gain, trajectory/initial values/points and indicator calibrations. Two-way modification isolation of the configuration with the original object, JSON/YAML back and forth, key sequence unrelated and independent SHA-256 recalculation passed. 
- 25 A case of actual input changes changing the configuration hash; Distinguishing file names from adjacent floating point quality. NPZ controller, quality, experiment configuration hash and tuning hash configuration consistent; 12 is rejected for illegal quality and 9 for unlimited configuration cases, and file protection has been maintained. Use only synthetic history, temporary files have been cleared, no simulation or rewriting of source code / frozen results. 
- Configuration validation report: `results/payload_configuration_verification_20260908T011935_154843Z.json`; The complete pytest `177 passed in 3.44s` (already with caching warnings), Ruff lint passed. results_io.py Part 126 line hash calls are missing a layer of continuous compression, and the remaining three files have existing format differences that do not affect execution. Special checks not included in persistent pytest. 
- `save_payload_manifest()` has been verified: 15 group YAML configuration is fully consistent with running snapshot, NPZ/YAML/JSON configuration hash and NPZ byte hash associated correctly; Controller, actual load quality, frozen tuning, hash, file name, real Git commit/dirty/status, software version, UTC time and UTF-8/LF exchange checks are passed. 
- Rejected as expected: 12 NPZ controller/mass/experiment-hash/tuning-hash mismatches, 3 missing histories, 6 independently protected existing YAML/JSON cases, and 9 failed Git/version dependencies, without creating configuration/metadata. Original NPZ and existing output bytes remained unchanged. Temporary files were cleared; no simulation or source changes, and frozen results were unchanged.
- Data validation report: `results/payload_manifest_verification_20260908T012440_004759Z.json`; The complete pytest `177 passed in 4.02s` (already with caching warnings), Ruff lint passed; The four relevant documents are still in pure format. Special checks not included in persistent pytest. 
- `save_payload_summary()` has been verified: reverse input generates quality priority, controller sequence fixed 15 line/13 column CSV, read back indicators correctly; Repeat combinations, non-finite metric rejection and already existing file bytes. Full pytest `177 passed in 3.34s` (already cached warning) Ruff lint passed. Only check the new critical path as requested by the user, no repeat of existing special verification or new report, temporary output cleared; Unmodified source code or running simulation. 
- The user has written `experiments/run_payload_benchmark.py`, the first official run of the Unified Command has been completed, and the resulting directory `results/payload/20260908T013358_027633Z/` contains 15 group NPZ/YAML/JSON, frozen copies of the files with `payload_metrics.csv`, together with 47 files. Each set of 8001 samples, time/reference consistent, historically limited, and actual torque meet the 20 N.m. limit; Three map core indicators aligned with NPZ, configuration/file hash associated and frozen copy correct. 
- Five masses followed by `0 / 0.25 / 0.50 / 0.75 / 1.00 kg`, overall joint RMSE ((degree): PID `1.115037 / 1.380694 / 3.851948 / 19.789138 / 32.490911`; PID + Gravity `0.152634 / 0.338827 / 2.936610 / 18.388365 / 32.552774`; CTC `0.004992 / 3.967051 / 15.061124 / 29.155920 / 40.108152`. 
- 1.00 kg saturation time ratio: PID `0.955125`, PID + Gravity `0.92375`, CTC `0.643125`. PID + Gravity and CTC are both saturation-free at 0.25 kg, and PID is `0.01275`; Subsequent interpretation requires a combination of the model deviation and torque limit without modifying the frozen gain depending on the result. The history of the zero load numerical value is completely consistent with the nominal baseline. 
- Full pytest `177 passed in 3.37s` (already cached warning) before running, Ruff lint passed; The new running script only lacks endings and alternate lines. At the user's request, only the necessary consistency of the official output of this round is checked, without repeating previous special tests or re-creating independent validation JSON. The assistant did not modify the source code; The graph has not yet been generated and the phase 18 has not yet been finalized. 
- The user wrote experiments/plot_payload_benchmark.py. The official CSV produced a 3000×960 payload_comparison.png; RMSE/effort/saturation curves, masses, units, colors/markers, legends, and percentages were visually verified. Only new-script lint and actual plotting were run; no simulation/pytest rerun. Formatter differences remained in a dictionary and final newline. The unified runner did not yet call plotting.

## Stage 16 frozen results

- `src/robot2dof/tuning.py` and `tests/test_tuning.py` already exist and have not yet been submitted. 
- Current strategy: PID/PID + Gravity directly search for `(kp1, ki1, kd1, kp2, ki2, kd2)` without natural frequency, damping ratio, reference inertia or score ratio mapping; CTC maintains the `kp = omega**2`, `kd = 2*zeta*omega`. The old `reference_joint_inertia(...)`, `pid_gains_from_targets(...)` and mixed candidate interfaces have been removed. 
- `TuningWeights`, `TuningMetrics` and `compute_tuning_metrics(...)` have achieved unification errors, torque costs, saturation ratios and weighting ratings; torque squared as a left rectangular pointer to the actual control interval, and any interval of joint saturation as a time statistic, both excluding the end effector output record. 
-  Shared `DEFAULT_TUNING_WEIGHTS` It's always been the same. `0.7 / 0.2 / 0.1` The error test is written with the end effector. ; Confirm the error by unifying the joint reference range for the full location sample containing the end effector and for two joint unifying RMSE. Test import sequence fixed. 
- `TrainingScenario` and `create_training_scenario()` have been written and verified: starting point location, zero joint speed, both PID controllers use zero-point starting values, no external torque, `0.001 s` control/RK4 step length, each joint `20 N·m` limit; For each candidate rebuild input, plant/model uses the same numerical but independent nominal parameter objects. 
- PID New interface: `PIDTuningCandidate`, `generate_pid_tuning_candidates()`, `build_pid_candidate_gains(...)`, directly save and copy six gains; PID and PID + Gravity share the same candidate table, generating independent gain arrays each time constructed. 
- CTC New Interface: `ComputedTorqueTuningCandidate`, `generate_computed_torque_tuning_candidates()`, `build_computed_torque_candidate_gains(...)`, with no score parameters. To keep the old CTC table completely unchanged, the generator retains and discards extra choice samples from the old random sequence. 
- `evaluate_training_candidate(controller, candidate)` has been implemented and supports `pid`, `pid_gravity`, `computed_torque`; Each time an independent fixed training scenario is created, build a corresponding gain and access an existing simulation device without accepting external trajectory parameters. 
- `CandidateEvaluation` Preserves controllers, candidates, actual gain, complete simulation available, history, rating indicators and reasons for failure; `succeeded` is successful, `score` is infinite and `metrics` is `None` when it fails. `simulation` is replaced by `None`; Failure to return to historical examination remains historical for diagnosis. 
- `TuningSearchResult` and `run_training_search(controller)` have been implemented: a strictly fixed budget for generator returns, retaining all success/fail evaluations, with no additional replacements; Successful candidate selects the best `(score, normalized_control_effort, candidate_id)`, returning the `best_evaluation=None` after all losses. 
- `experiments/run_tuning_search.py` Saves configuration, actual candidate, gain, all indicators or causes of failure, and updates `results/tuning_search.json` at the end of each controller; The final state is `complete`, and the file contains a sequence of 300 entry ID records for each of the three groups. 
- Freeze configuration of SHA-256 to `50247f53d83e161b5419f0e59216c5064f2d6f8700eca295f6dc253e140ec3da`. Independent recalculation consistent with document records; Optimal IDs for three-tiered independent weightings are PID `154`, PID + Gravity `233`, CTC `208`. 
- All three 900 candidates were successful, all of the indicators were limited and there were no failures. After frozen, no retuning or modification of the candidate table, scoring rules, seeds, budget and training agreement shall be permitted. 
- Check the non-finite values for all returned history (including the end effector), `abs(q)>pi` and `abs(q_dot)>50`; saturation only counts for the target function. Local NumPy error strategy converts overflow/illegal operations/zero to numerical abnormalities; Failure to record floating-point anomalies, overflow and linear algebra solving, common call/configuration errors thrown out directly. 
- Each controller has a 300 budget, a 1 baseline plus a 299 random candidate, `PCG64` seed, `20260905`. PID six-dimensional sampling lower bound `(20,0,1,10,0,0.5)`, upper bound `(300,100,60,200,80,40)`, ordered as `(kp1,ki1,kd1,kp2,ki2,kd2)`; The direct baseline is `Kp=(150,100)`, `Ki=(30,20)`, `Kd=(25,15)`, from the old development script. The scope is pre-set engineering selection, not adjusted according to the formally preserved trajectory. 
- Current training trajectory: `0–4 s` single stage `[-35°, -45°] -> [50°, 60°]`. Officially maintained tracks for the planned new five waypoint tracks; Phase 16 has been frozen, but the trajectory is not yet operational and the user requested not to initiate phase 17. 
- The old single-section `[-20°, 40°] -> [40°, -20°]` and the old five-waypoint trajectory are both classified as development verification trajectories; The corresponding PID/CTC stability test has been named `development_trajectory`. 13 aluminum 15 aluminum training trajectory aluminum in historical evidence according to this understanding. 

## Current coding capabilities

### Parameters

- `src/robot2dof/parameters.py`
- `RobotParams` contains the nominal parameters of pole length, mass, center of mass distance, center of mass inertia and gravitational acceleration. 

### Sports studies

- `src/robot2dof/kinematics.py`
- `rotation_transform(angle)`
- `translation_transform(dx, dy)`
- `forward_kinematics(q, params)`
- `forward_kinematics_transform(q, params)`
- `is_reachable(xy, params)`
- `inverse_kinematics(xy, params, branch)`
- `jacobian(q, params)`
- `end_effector_force_to_joint_torque(q, force, params)`
- IK branch: `elbow_up` and `elbow_down`. 
- IK output angles are unified into `[-pi, pi]`. 

### Dynamics

- `src/robot2dof/dynamics.py`
- `mass_matrix(q, params)`
- `coriolis_vector(q, q_dot, params)`
- `gravity_vector(q, params)`
- `forward_dynamics(state, tau, params, external_tau)`
- `src/robot2dof/state.py` in `State` Save joint location and speed. 
- Forward dynamics uses `numpy.linalg.solve` to solve `M(q) @ q_ddot = net_torque`, not explicitly calculating the inverse of the matrix. 

### The simulation machine

- `src/robot2dof/simulation.py`
- `state_derivative(time, state_vector, tau, params, external_tau)`
- `rk4_step(derivative, time, state_vector, step)`
- `integrate_fixed_steps(derivative, initial_state, start_time, end_time, step)`
- The state sequence is fixed to `[q1, q2, q1_dot, q2_dot]` and the derivative sequence to `[q1_dot, q2_dot, q1_ddot, q2_ddot]`. 
- Multi-step scorer returns the time grid and complete state history of the endpoint containing the endpoint. 
- `PIDStepResult` and `pid_closed_loop_step(...)` will connect reference, controller, public saturation, zero-order hold RK4 plant and conditional points as a control cycle; Selectable `controller_params` separated from the actual plant `params` and kept pure PID when missing. 
- `PIDSimulationResult` Storage time, four-dimensional state, three-dimensional reference, integral error, request/actual torque and complete history of joint saturation marking. 
- `simulate_pid_trajectory(...)` rounds the closed loop step on a fixed-time grid, and the end effector sample records only the reference and control output and no longer advances the state. 
- The `simulate_pid_trajectory(...)` optional `controller_params` runs through the entire control cycle and end effector sample; Failure to maintain pure PID, using PID + gravity compensation for model parameters. 
- `ComputedTorqueStepResult` and `computed_torque_closed_loop_step(...)` connect the CTC, public saturator and zero-order hold RK4 plant in a control cycle, without introducing a point state. 
- `ComputedTorqueSimulationResult` and `simulate_computed_torque_trajectory(...)` save CTC multi-step status, reference, request/actual torque and saturation history and record output only in the end effector sample. 

### Trajectory

- `src/robot2dof/trajectory.py`
- `Reference` Save the `q_ref`, `q_dot_ref` and `q_ddot_ref`. 
- `sample_quintic_segment(...)` uses normalized time to sample double joint single-section stop-to-stop quintic trajectory. 
- `sample_quintic_trajectory(...)` Selects the adjacent waypoint segment based on sampling time, and repeats the single-section sampling function to generate multiple trajectories. 
- Currently refuses to enter ineffective time intervals, extra-periodic samples and non-double joint positions. 

### The controller

- `src/robot2dof/controllers.py`
- `PIDGains` preserves the two joint `kp`, `ki` and `kd`. 
- `ControllerOutput` Saves the requested torque, location errors, speed errors and integral errors Diagnosis. 
- `compute_independent_joint_pid(...)` jointly calculates unsaturated PID requests torque and verifies input shapes, finite values and nonnegative gain. 
- `compute_pid_with_gravity_compensation(...)` superimposes the controller model `gravity_vector(q, controller_params)` on a pure PID request torque, and replicates the `ControllerOutput` interface. 
- `ComputedTorqueGains` Save the virtual acceleration commands by joint `kp`, `kd`; `compute_computed_torque(...)` implemented `M_hat(q)(q_ddot_ref + Kd e_dot + Kp e) + c_hat(q, q_dot) + G_hat(q)` without the use of points. 
- `update_integral_error_conditionally(...)` joint frozen points when the saturation and error continue to push the torque across the boundary, the reverse error can still unwind. 

### Executioners

- `src/robot2dof/actuation.py`
- `ActuatorOutput` simultaneously saves the requested torque, applied torque and joint saturation marking. 
- `saturate_joint_torque(...)` supports public gauges or joint-by-joint symmetry limitations and uses `clip` to generate actual torque. 

### Testing

- `tests/test_package.py`
- `tests/test_kinematics.py`
- `tests/test_dynamics.py`
- `tests/test_simulation.py`
- `tests/test_trajectory.py`
- `tests/test_controllers.py`
- `tests/test_actuation.py`
- Package import, FK/IK, Jacobian, determinant, end effector, external force mapping, mass matrix, gravitational gradient, forward dynamics, state guides, RK4 measurements known to be solved, multi-step gravitational balance, step closure, `solve_ivp` reference trajectory and mechanical ability to remain constant. 
- Trajectory testing covers single-section and multi-section quintic trajectory endpoint constraints, known mean time numeric values, segment selection, total waypoint continuity and input verification. 
- Controller tests cover known P/I/D outputs, zero error, negative gains, input validation, normal/frozen/unwinding/mixed-joint anti-windup states, and PID+Gravity static equilibrium torque.
- Performers test coverage measurements with joint-by-joint constraints, positive-negative cuts, touch limit markings and abnormal inputs. 
- Simulation testing covers pure PID closed-loop single-step gravity balance, request/actual torque saturation, points frozen and reverse unwind, non-zero posture static maintenance of PID + gravity compensation, multi-step gravity balance of complete history, and CTC single-step/multi-step static maintenance and the limited, error gate, no saturation of the true training trajectory. 

### Visualization

- IK script and output: `experiments/plot_ik_branches.py`, `results/ik_workspace_branches.png`. 
- Jacobian script and output: `experiments/plot_jacobian_singularity.py`, `results/jacobian_determinant.png`. 
- Quintic trajectory script and output: `experiments/plot_quintic_trajectory.py`, `results/quintic_trajectory.png`. 
- Quintic trajectory animation: `results/quintic_trajectory_animation.gif`, showing the reference joint movement and end effector trajectory by nominal pole length. 
- PID Tracking script and output: `experiments/plot_pid_tracking.py`, `results/pid_trajectory_tracking.png`; Six sub-graphs showing the reference/actual position, position error and request/actual torque of the two joints. 
- The Jacobian graph shows the determinant at `q2 = -180°, 0°, 180°` as zero and `q2 = ±90°` as `±0.20 m²`. 

### Stage 3 Concentrated Practice

- Written by `experiments/stage3_foundations.py`
- Coverage: `numpy.linalg.solve`, center bounded differential, scale RK4, NumPy broadcasting. 
- Unit conversion exercises skip by user choice; The project already has SI/radian agreements and the actual use of `np.degrees`. 

## Recent evidence of centralized validation

- Date: 2026-09-07. 
- Stage 18 Dynamics incremental validation: 5000 A random case, the maximum error in mass increment `3.331e-16`, the energy gradient `1.693e-9`, the Coriolis increment `4.193e-10`, the independent recovery acceleration `1.340e-9`; Three Controllers Zero Load Full History and Stage 17 is the same item by item. The complete pytest was passed to `177 passed in 6.02s`, Ruff lint, and the two files are still in pure format differences. Detailed evidence see Stage 18 Current progress and independent report. 

- Date: 2026-09-07. 
- Phase 17 Final validation: run `D:\miniconda\envs\robot2dof\python.exe experiments/run_nominal_benchmark.py`, generate three sets of NPZ/YAML/JSON in `results/nominal/20260907T024619_815442Z/`, copies of frozen files, CSV and 2600 × 2000 six graphs. 
- Each set of 8001 samples, all stored arrays are exactly the same as the first official result, and CSV byte is the same; Independent recalculation tracking and executor metrics, vectoring FK, configuration and file hashing are all passed. The source file is still frozen for `f3ca1c928579b0e724d0f80a30dd7f214f2915f3ee5d9fadff40d28962852e60` and the new copy is consistent. The review report and source code/environment hash have been saved to the new `verification.json` directory. 
- The complete pytest is for `177 passed in 5.67s` (both with cache write authorization warnings), the entire repository Ruff lint is passed, and the two experimental script formatter checks are passed. The six-point visual inspection passes; This round does not modify Python source code or frozen gain. 

- Date: 2026-09-07. 
- The user has written `experiments/plot_nominal_benchmark.py` and the assistant runs the script, generating `nominal_comparison.png` (2600 × 2000) from the first official NPZ. Visual inspection confirms that the six subgraphs, coordinates/examples, reference and actual location, error and ± 20 N·m torque limits are normal; CTC near zero, non-strict zero errors below the current error scale. The actual torque is used to express the control intervals using stairs and excluding the end effector output. 
- The complete pytest for `177 passed in 3.69s`, the entire repository Ruff lint passed; formatter instructs the drawing of both the expression line and the end line, running the end line of the script. Unrepeated official simulation; Unified input has not yet called the mapping function. 

- Date: 2026-09-06. 
- First official nominal control: All three controllers complete the `0–8 s` five waypoint trajectory, with 8001 samples for each group; Time/reference is perfectly consistent, initial values, models, scores, zero-out torque and `20 N·m` saturation machines are correct to verify that all values have a finite history. 
- Independent weighting of all 11 indicators from NPZ in line with CSV, independent vectoring FK verification of the actual/reference end effector position correctly; YAML/NPZ/JSON configuration hash is consistent with NPZ file hash. The source frozen result file SHA-256 is still `f3ca1c928579b0e724d0f80a30dd7f214f2915f3ee5d9fadff40d28962852e60` and this copy is the same byte. 
- The official results: two joint RMSE ((degree) PID `[1.3583453347,0.8009449726]` , PID + Gravity `[0.2025613427,0.0745869442]` , CTC `[0.0016681054,0.0068599706]`; Maximum end effector error (m) followed by `0.054107413 / 0.007221444 / 0.000101354`;  The control effort `1440.970462 / 1444.342626 / 1446.348804 (N·m)^2·s` The saturation ratio is: 0 . 
- Formal configuration of SHA-256: PID `7591e764aa27d8a39abc3f731cdadaf199445f00c4871e82064db364896b05b6`; PID + Gravity `34f4f2c3041cf94bcf06d1069fc07b65b8bbbebbea65289057b91fddac858141`; CTC `bfaa416c1753f796513aca722ba7028d8d436798c34614c1264d2b5f95c6da14`. 
- The complete pytest prior to launch was `177 passed in 3.35s`, and the entire repository Ruff lint was passed; The 17 file format was adopted in three core phases, with `run_nominal_benchmark.py` missing only the end-to-end conversion. Unmodified Python source code; The independent review report has been preserved and the map has not yet been implemented. 

- Date: 2026-09-06. 
- CSV save checks through: 6 type input sequences output a fixed triangle of PID/PID + Gravity/CTC with columns of 12, known values such as control effort / mechanical amplification read back correctly, no extra spacing lines; File byte is unchanged, missing/repeating/unknown controller, illegal extension name and three non-finite metrics are rejected before a file is created. 
- Full pytest for `177 passed in 3.23s`, full repository Ruff lint and benchmark.py/metrics.py/results_io.py formatter check all passed. Additional checks use synthetic history with temporary directories that have been cleared, are not included in the persistent pytest, and are not officially closed looped; The Unified Experimental Script has not yet been written. 

- Date: 2026-09-06. 
- Metadata checks passed for all controllers: NPZ/YAML/JSON formal configuration associations, tuning/history hashes, YAML contents, real Git commit/dirty state, versions, UTC timestamps, and LF endings. Existing YAML/JSON are separately protected; missing or mismatched histories are rejected; failed Git/version reads create no metadata.
- The complete pytest for `177 passed in 3.24s`, the complete repository Ruff lint and benchmark.py/metrics.py/results_io.py formatter check all passed. Additional checks use synthetic history with cleared temporary directories, unwritten perpetual pytest, unrunning formal closed loop; CSV saved has not yet been written. 

- Date: 2026-09-06. 
- Formal configuration with hash checks: three controller complete fields, actual model/controller model, frozen gain and point differentiation, output naming, snapshot and source group isolation; Independent recalculation of SHA-256, recursive key recalculation with JSON/YAML back and forth hash stability, model/step/limit/gain changes change hash, non-limited configuration rejection. 
- Full pytest for `177 passed in 3.73s`; The Ruff lint still has the `benchmark.py` imported excess space line I 001, which is the formatter difference between the file and the `results_io.py`. PyYAML 6.0.3 has been confirmed available, the next user should record it explicitly to environment.yml. Additional checks for temporary memory scripts; Not officially closed. 

- Date: 2026-09-06. 
- NPZ save checks through: all three controllers field/shape/dtype read back accurately under `allow_pickle=False`, end effector position calculation and constant external torque correct, compression effective, file of the same name rejected and byte hash unchanged, input maintained; Unlawful extensions and unlimited historical/derivative data cases of 28 were rejected prior to the creation of the file. Verify the temporary directory of synthetic history and cleared work areas. 
- Full pytest for `177 passed in 3.63s`. Ruff lint remaining after `benchmark.py` import zone resulting in excess vacuum line I 001; The formatter instructs the blank line and the hash expression for `results_io.py` to switch lines/end lines, and the `metrics.py` format passes through. Additional verification as a temporary script without adding a permanent pytest; Not officially closed. 

- Date: 2026-09-06. 
- The indicator summary checks are performed through: 12 columns for the three controllers, manual indicators and rad/degree/m units, location/speed snippets, actual torque selection, end effector statistical semantics, normal float type, input history keeping, and JSON/CSV readback. All used synthetic history and not officially closed. 
- Full pytest for `177 passed in 3.99s`; `metrics.py` with `benchmark.py` formatter check Passed by; Ruff lint of the entire repository where `benchmark.py` is left is `I001`, where the metrics are imported and moved between the controllers and parameters imported. Added summary checks for temporary memory scripts that have not yet been written in the persistent pytest. 

- Date: 2026-09-06. 
- Control effort 55; saturation comparison 2 / 3; absolute mechanical performance 10 J); 8 limited end effector sample variation; joint power offset; zero torque; time scales; statistical consistency with the original training score; input maintained and input in the 23 class. 
- The complete pytest is for `177 passed in 3.72s` and the entire repository is for Ruff lint; `metrics.py` formatter check There are three remaining expressions that differ. Additional verification for temporary memory scripts, not written in perpetual pytest; Not officially maintained trajectory. The official index summary has not yet been written. 

- Date: 2026-09-06. 
- Tracking errors known through: zero errors, end-only errors, two joint unequal errors, single-sample folding posture, bar length scaling, unmodified input and invalid input of 12 class. In both samples, only the end-stretched robot arm rotates 90°, where the total joint RMSE = 45°, the end effector RMSE = 0.9 m, the maximum end effector error is about 1.272792206136 m. 
- The complete pytest is for `177 passed in 3.42s` and the entire repository is for Ruff lint; `metrics.py` formatter check. The new indicator is validated as a temporary memory script and has not yet been written in a persistent pytest. No formally maintained trajectory locks are in operation and the executor indicator has not yet been written. 

- Date: 2026-09-06. 
- Unified nominal input line checks pass through: three branches call correctly, all scenario parameters are transmitted in default, PID scores are independent and zero, CTC does not transmit scores, scenes call independent, frozen read fail, do not create scenes or call a simulation machine. 
- Real simulation machines use independent `0–0.003 s` static development cases (`q=[0.2,-0.3] rad`) to validate four samples with historically limited initial values and correct torque limits; The pure PID initial output is zero, the two model compensation controllers remain static and the output is gravitational torque. No official five-waypoint closure. 
- The complete pytest for `177 passed in 3.81s`, the complete repository Ruff lint and the `benchmark.py` formatter check were passed. Added input checks for temporary memory scripts that have not yet been written to the persistent pytest; The official tracking error indicator has not yet been written. 

- Date: 2026-09-06. 
- frozen gain read check through: return type of three controllers; gain accurately matches frozen record; inter-call group isolation; Unusual cases of a memory copy of 45 were rejected, and the illegal controller rejected the file before it was read. Check before and after frozen result file SHA-256 is the same. 
- The complete pytest is for `177 passed in 3.65s` and the entire repository is for Ruff lint; `benchmark.py` formatter check only indicates the variation between hash strings and dictionary derivatives. The above additional checks are executed through temporary memory scripts that have not yet been written to the persistent pytest file; No formal closed-loop performance experiment has been conducted. 

- Date: 2026-09-06. 
- Formal scenarios read-only interface checks through: five waypoint location and zero speed/acceleration, initial state, independent parameters and all input array isolation; No formal closed-circuit simulation. 
- Full pytest for `177 passed in 6.30s`; `benchmark.py` Ruff lint passes, formatter check prompting the end of the file to miss a line, waiting for the user to fill in. Frozen gain Reading functionality has not been written or verified. 

- Date: 2026-09-05. 
-  Stages 16 Finally frozen: `results/tuning_search.json` For example, `complete` The size. `1,077,349 bytes` It has PID, PID + Gravity, CTC. 300 Continuous record of candidates ; 900 candidates were all successful and all scores were limited. 
- Configure SHA-256 to remain as `50247f53d83e161b5419f0e59216c5064f2d6f8700eca295f6dc253e140ec3da` after configuring independently from within the file.  Re-apply `(score, normalized_control_effort, candidate_id)` The best ID to be ranked is consistent with the record: `154 / 233 / 208` . 
- The user completes the search log scripts by importing Ruff, sorting and formatting. Phase 16 is over; Not officially maintained trajectory and stopped before 17 stage as requested by the user. 
- Date: 2026-09-05. 
- The user actually runs three 300 training candidates for each of the controllers. The pure PID is optimized for ID `154`, `Kp=(270.6548361496739,102.72046256778128)`, `Ki=(95.43248337143797,64.3251189257144)`, `Kd=(16.834763264662215,33.57650325213311)`, `R=0.013773001006622676`, `U=0.1726974768932044`, `S=0`, `J=0.04418059608327675`. 
- PID + Gravity is optimized for ID `233`, `Kp=(288.1269373322243,193.81506985439225)`, `Ki=(16.905614402662785,71.1030900140941)`, `Kd=(43.648740694702795,27.902747337359745)`, `R=0.0007751779822952831`, `U=0.17452903048386711`, `S=0`, `J=0.035448430684380125`. 
- Computed Torque is optimized for ID `208`, `omega=(10.312011552420454,11.941334834857992)`, `zeta=(1.184044124807485,0.9341202438888768)`, `Kp=(106.33758226,142.59547764)`, `Kd=(24.41975339,22.30928522)`, `R=4.37189288415089e-05`, `U=0.17487135169277215`, `S=0`, `J=0.03500487358874348`. 
- This time, only fixed training tracks were used and no formally maintained tracks were operated. The interaction session did not preserve all of the 900 line candidates in detail, so the above results have not been finalized as a phase 16 product. 
- Date: 2026-09-05. 
- Fixed budget bulk search and sort function block validation: Directional tuning pytest for `89 passed in 1.89s`; Full pytest for `177 passed in 3.41s`; Ruff lint and two file formatter checks passed through the entire repository. 
- Testing by alternating single-candidate evaluation to verify that the three controllers each pass through a fixed candidate 300, maintain the ID sequence, and fail on budget without additional replacement; At the same time, verify the scores, control costs and candidate IDs according to the original floating-point values, as well as the overall failure and illegal behavior of the controller. 
- There is no real 900 training simulation and no official trajectory assessment; The next step is to sequence verifiable search results, configure hashes and frozen records, and then perform a full search. 
- Date: 2026-09-05. 
- Single candidate evaluation function block: `tests/test_tuning_evaluation.py` directed pytest to `48 passed in 2.02s`; Full pytest for `171 passed in 3.32s`, full repository Ruff lint with two current modified file formatter checks. 
-  PID, PID + Gravity, CTC, all three baselines are fixed. `0–4 s` Trained 4001 A sample with limited scores ; Check the pure PID initial request torque for zero, the initial output of the two model compensating controllers for gravity torque, and the PID class zero point initial value. 
- Exceptions and boundary verification covering negative position/speed thresholds, accurate touch thresholds, just crossing boundaries, middle and end effector samples, all numerical history and indicators of non-finite values, saturation, punishment, numerical anomaly recording, miscalculation transmission and scene isolation. 
- Assessment of only three baselines as connection validation, complete search of 300 group candidates for each controller, and formal retention of trajectories were not evaluated. 
- Date: 2026-09-05. 
- After user authorization is directly rewritten, the complete pytest is `123 passed in 3.18s` (`-p no:cacheprovider`), and the entire repository Ruff lint is passed; Formatter check for `tuning.py` and `test_tuning.py`. 
- The new test verified six direct gain ranges, budget/baseline/repeatability, arbitrary direct gain (with independent zero points) prototype transmission, input effectiveness, PID/PID + Gravity gain array isolation, and local random state independence. 
- All 300 group CTC's ID, frequency, and damping ratio are fully consistent with `Kp/Kd`'s pre-rewrite snapshot, and SHA-256 is `24c30127f23b0187d1933e459abd68eb0adabef57cb829de1ac648206d2343d6`. The old PID mapping interface has no remaining references in the relevant source code, test and experimental scripts. 
- This time, the candidate generation and gain connections were completed without running a 300 group training performance search, nor an official trajectory retention assessment. 
- Date: 2026-09-05. 
- Modify the PID tuning strategy as specifically requested by the user: directly independently select six gains, cancel frequency/damping ratio/reference inertia/share point ratio mapping; Plans, progress and theoretical indices are synchronized. The old connection functions and tests in the source code already exist, this time without modifying Python or repeating the test. 
- Date: 2026-09-05. 
- Successfully verified candidates: orientation pytest for `17 passed in 1.28s`. Ruff reports that one test file is `I001` and two are `F811`, because `create_training_scenario`, `pid_gains_from_targets` was imported repeatedly and the list is not sorted; For the user to replace the entire imported block. Unrepeated total returns. 
- The next block has been checked with an existing gain function for the non-symmetrical targets `omega=(8,6)`, `zeta=(1,0.8)`, `alpha=0.1`: midpoint inertia about `[0.91910013, 0.08]`, PID `kp≈[58.82240801,2.88]`, `kd≈[14.705602,0.768]`, `ki≈[47.0579264,1.728]`. New connection functions and tests have not yet been written or run. 
- Date: 2026-09-05. 
- Shared training scene function block validation: user tuning oriented pytest to `15 passed in 0.20s`, oriented to Ruff through; After verifying the source code, the assistant runs the complete pytest to `103 passed in 2.46s`, and the entire repository Ruff lint passes through. 
- Verify that the initial state of coverage is consistent with the reference, zero-point initial values, nominal plant/model values are the same but independent of objects, and that the five input arrays are not shared among candidates. 
- This assistant only updates documents; The next candidate generator has not yet been written, excluding the above test results. Not officially maintained trajectory. 
- Date: 2026-09-05. 
- Shared weight and end effector position error function block verification: tuning orientation pytest for `9 passed in 0.11s`;  Ruff is in `tests/test_tuning.py` A newspaper `I001` It is necessary to `DEFAULT_TUNING_WEIGHTS` Move to tuning Import top of list . There is no re-run of the full return; See the full evidence of the previous round. 
- The end effector classifies the unification error as `[0.2, 0.1]`, the remaining four errors as zero, the sample RMSE as `sqrt(1/120)`, and the only non-zero error is `0.7*sqrt(1/120)`. 
- Date: 2026-09-05. 
- Score time statistics function block validation: user oriented pytest to `8 passed in 0.17s`, oriented to Ruff lint through; After verifying the source code, the assistant runs the complete pytest to `96 passed in 2.66s` (`-p no:cacheprovider`), and the entire repository Ruff lint passes. 
- Known answer verified: non-equal length interval, change torque down to unified torque at `0.2375`, saturation time ratio at `0.25`, rating at `0.1425`; All four end effector torque/saturation record combinations have no effect on the results. 
- This assistant only updates documents without modifying the Python source code or running a formally preserved trajectory; The next common weight constant and end effector position error test has not yet been written and is not counted in the results of the above test. 
- Date: 2026-09-04. 
- Theoretical indices have been synchronized to the 15 phase: adding sampled PID scores with historical semantics; feedforward/feedback of PID + gravity compensation and plant/model separation; and virtual acceleration of Computed Torque; ideal secondary error dynamics; gain quantity diagrams and forward dynamics verification methods; Python hasn't been changed this time. 
- Date: 2026-09-04. 
- Phase 15 Final validation: correct model, unsaturated condition, Computed Torque forward to restore `q_ddot_ref + Kd e_dot + Kp e` to dynamics; Sampled closed-loop single-step and four-sample static history maintaining non-zero balance posture. 
- The then-planned training trajectory was a single 0-4 s segment from `[-20°,40°]` to `[40°,-20°]`. Baseline `omega_n=8 rad/s`, `zeta=1` gives `Kp=64`, `Kd=16`. Preflight per-joint maximum errors were approximately `[0.0073°,0.0203°]`, terminal errors `[0.00026°,0.00175°]`, and peak requested torques `[15.17,2.82] N·m`. No saturation; all histories finite.
- Final return: controller and simulation orientation pytest to `35 passed in 2.55s`; Full pytest for `88 passed in 2.64s`; Ruff lint passed. The relevant formatter still has purely edition differences, focusing on deferred cleaning according to the user's decision, without affecting the conclusion of control behavior at the stage. 
- Date: 2026-09-03. 
- Phase 14 Final validation: correct controller model, zero PID gain and zero point initial value, non-zero static posture remained unchanged in four multi-step samples; All request/actual torque samples are equivalent to `G(q)`, including only end effector samples that do not record progress and are completely saturation-free. 
- The ultimate return: simulation oriented pytest to `16 passed in 1.44s`; Full pytest for `84 passed in 1.45s`; Ruff lint and two simulation-related file formatter checks all passed; Phase 14 validation Gateway is passed. 
- Date: 2026-09-03. 
- Phase 14 sampled closed-loop: actual plant and controller models are transmitted through `params` and optional `controller_params` respectively; Under the correct model, zero PID gain and zero point initial values, the non-zero static posture remains unchanged after a control cycle, and the request/actual torque is equal to `G(q)`, zero saturation. 
- Concentrated verification: simulation oriented pytest for `15 passed in 1.42s`; Full pytest for `83 passed in 1.44s`; Ruff lint and two simulation-related file formatter checks all passed. 
- Date: 2026-09-03. 
- Stage 14 PID + gravity compensation Control output: When the non-zero static posture and position, speed and integral error are zero, the torque requested is consistent with the correct controller model `G(q)` within the `1e-12` gap. 
- Central verification: The controller directs the pytest to `15 passed in 1.45s`; Full pytest for `82 passed in 2.79s`; Ruff lint and the two controller-related file formatter check all passed. 
- Date: 2026-09-01. 
- Phase 13 Final validation: PID tracking PNG to `2578 × 1969`, `304205 bytes`; Artificial inspection confirms that the reference/actual curve is continuous and highly overlapping, the error is always within the `±2.5°` gate, and the request/actual torque overlapping is far from the `±20 N·m` limit. 
- The final return: complete pytest for `81 passed in 1.65s`; Ruff lint all passed, `simulation.py`, `test_simulation.py` and `plot_pid_tracking.py` formatter checks all passed; Stage 13 Training Trajectory Stability, No NaN, No Continuous Dissemination Validation Gate Passed. 
- Date: 2026-09-01. 
- Stage 13 Fixed training trajectory stability: `0–8 s` Five waypoints, `0.002 s` Control cycle, maximum position error is `[2.1344°, 0.7084°]`, end error is `[0.6197°, 0.5048°]`, maximum request torque is `[15.4298, 3.2417] N·m`, `20 N·m` is limited to zero saturation and all values have a limited history. 
- Concentrated verification: simulation oriented pytest for `14 passed in 1.41s`; Full pytest for `81 passed in 1.44s`; Ruff lint and two simulation-related file formatter checks all passed. 
- Date: 2026-09-01. 
- Phase 13 PID Multi-step trajectory simulation history: the simulation orientation pytest is given as `13 passed in 1.05s`; Full pytest for `80 passed in 1.04s`; Ruff lint all passed, and `simulation.py` and `test_simulation.py` formatter checks passed. 
- Date: 2026-08-31. 
- Phase 13 sampled PID closed loop single step: simulation oriented pytest for `12 passed in 1.63s`; Full pytest for `79 passed in 1.72s`; Ruff lint and two simulation-related file formatter checks all passed. 
- Date: 2026-08-31. 
- Stage 13 conditional-integration anti-windup: the controller directs the pytest to `14 passed in 0.12s`; Full pytest for `76 passed in 1.02s`; Ruff lint and the two controller-related file formatter check all passed. 
- Date: 2026-08-31. 
- Stage 13 Public torque saturator: directed pytest to `11 passed in 0.12s`; Full pytest for `67 passed in 1.20s`; Ruff lint is a file formatter check with two executors. 
- Date: 2026-08-31. 
- Phase 13 unsaturated PID: directed pytest to `5 passed in 0.11s`; Full pytest for `56 passed in 2.13s`; Ruff lint and the two controller-related file formatter check all passed. 
- Date: 2026-08-31. 
- 2-DOF reference animation: GIF for `840 × 840`, `201` `25 FPS`, `1296306 bytes`; Artificial inspection confirms that rod length proportions, initial structure, planning paths and movement trajectories are normal. 
- Validation: Full pytest for `51 passed in 2.06s`; Ruff lint and the three-phase file formatter check all passed. 
- Date: 2026-08-31. 
- Stage 12 Final validation: Fixed `0–8 s` Five waypoints Three linked graphs have been generated, PNG is for `324526 bytes`; Artificial inspection confirms all location waypoints live, speed and acceleration at all waypoints back to zero and curves unchanged. 
- Directed pytest to `16 passed in 0.17s`; Full pytest for `51 passed in 1.37s`; Ruff lint output `All checks passed!`, three stages of related file formatter check all passed. 
- Date: 2026-08-31. 
- Stage 12 Multi-stage quintic trajectory: oriented pytest to `16 passed in 0.13s`; Full pytest for `51 passed in 1.01s`; Ruff lint and two related file formatter checks all passed. 
- Date: 2026-08-30. 
- Stage 12 single-stage quintic trajectory: directed pytest to `7 passed in 0.12s`; Full pytest for `42 passed in 3.98s`; Ruff lint and two related file formatter checks all passed. 
- Date: 2026-08-30. 
- Mechanical energy stability: non-driving torque, non-extrusive and non-friction working condition score `2.0 s`, initial total energy is `2.531869792351 J`, maximum absolute drift of the entire trajectory is `2.4507720e-9 J`, lower than `1e-7 J` validation gate. 
- Stage 11 Concentrated validation: directed pytest to `9 passed in 4.06s`; Full pytest for `35 passed in 4.11s`; Ruff lint and related file formatter checks all passed. 
- Date: 2026-08-30. 
- `solve_ivp` cross-validation: `0.001 s` fixed gauge RK4 with the strictest four-dimensional trajectory difference of `DOP853` is the maximum absolute difference between `1.2482417e-8` and `5e-8` validation gate. 
- Full pytest: `34 passed in 1.16s`; Ruff lint output is `All checks passed!`. 
- Date: 2026-08-30. 
-  I'm not sure what I'm saying. `h = 0.002` with `0.001 s` The end result is `1.2528243e-7` ; `h = 0.001` and `0.0005 s` have the same terminals as `8.6493362e-9`. 
- Reduced error ratio: `14.484629`, theoretical ratio near four-stage RK4 `16`, and through the `> 10` validation gate. 
-  This is a directed pytest: `7 passed in 0.23s` ; Full pytest: `33 passed in 0.29s`; Ruff lint and the formatter check all passed. 
- Date: 2026-08-30. 
- Multi-step pointer: `0–1 s` index ODE generates a 11 time point and reaches the expected end value;  The robot arm is in gravitational equilibrium. `0.001 s` Moving forward 100 Keeping the four-dimensional zero state after the step . 
-  This is a directed pytest: `6 passed in 0.18s` ; Full pytest: `32 passed in 0.27s`. 
- Ruff lint: `All checks passed!`; Both simulation source code and testing have been formatted. 
- Date: 2026-08-30. 
- robot arm Four-dimensional RK4: non-zero initial speed, constant acceleration and external torque case with the solved `q`, `q_dot` single-step result consistent with `1e-12`. 
-  This is a directed pytest: `4 passed in 0.10s` ; Full pytest: `30 passed in 0.17s`. 
- Ruff lint: `All checks passed!`; Both simulation source code and testing have been formatted. 
- Date: 2026-08-30. 
- Stage 11 RK4: The single-step result of `y_dot = y` is consistent with the four-step Taylor polynomial, with the difference `1e-12`. 
-  This is a directed pytest: `3 passed in 0.11s` ; Full pytest: `29 passed in 0.51s`. 
- Ruff lint: `All checks passed!`; Both simulation source code and testing have been formatted. 
- Date: 2026-08-30. 
- Stage 11 State Directors: Four-dimensional State Directors are zero when gravity is balanced; The correct combination of non-zero speed, acceleration and external torque is `[q_dot, q_ddot]`. 
-  This is a directed pytest: `2 passed in 0.20s` ; Full pytest: `28 passed in 0.41s`. 
- Ruff lint: `All checks passed!`; Both the state-directed source code and the test have been formatted. 
- Date: 2026-08-28. 
- Stage 10: `M(0)` in the nominal horizontal gesture is consistent with the hand-calculated matrix; 1000 with a fixed random gesture `M(q)` is symmetric positive definite. 
- Coriolis/centrifugal vector: Test of known responses to non-zero angles and non-zero velocities. 
- Gravity vector: the horizontal gesture result is `[15.2055, 2.943] N·m`; 100 has a fixed, random posture consistent with the finite differential gradient of the power center, and a tolerance difference of `1e-6`. 
- Forward dynamics: Gravitational balance is accelerated to zero; Non-zero speed, non-zero torque cases can restore the default acceleration. 
- Full pytest: `26 passed in 0.16s`; Another pytest cache that doesn't affect the results write permission warnings. 
- Ruff lint: `All checks passed!`; All three new Python files in 10 have been formatted. 
- Date: 2026-08-27. 
- SymPy: center of mass, speed, total momentum, total momentum, mass matrix, gravitational vector and Coriolis/centrifugal vector. 
- Stage 9 control: symbols `M(q)`, `c(q, q_dot)`, `G(q)` are completely consistent with manual parsing by element simplification. 
- Full pytest: `19 passed in 0.33s`; Another pytest cache that doesn't affect the results write permission warnings. 
- Ruff lint: `All checks passed!`; Phase 9's verification scripts and parameter modules are formatted. 
- Date: 2026-08-25. 
- Stage 3 script: The numerical values of the four exercise blocks are all affirmed to pass. 
- RK4 verification: score `y' = y, y(0) = 1` to `t = 1`, resulting in `2.718279744135166` with absolute error of about `2.08e-6`. 
- Full pytest: `19 passed in 0.23s`; Another pytest cache that doesn't affect the results write permission warnings. 
- Ruff lint：`All checks passed!`。
- Format checking at this stage: All related Python files in 4 have been formatted. 
- Jacobian numerical verification: 100 random gesture under fixed seed, with a finite parsing/center differential of `1.579e-10`. 
- External force mapping verification: horizontal configuration obtained by `[0, -10] N` when subjected to `[-9, -4] N·m`. 
- Jacobian PNG: 84014 bytes, has been manually checked to show normal. 
- Random IK verification: 100 target under fixed seed, two branches, total of 200 followed by FK -> IK -> FK verification. 
- Location validation Error: Not more than `1e-9 m`. 
- Visualize PNG: 128807 bytes, which have been manually checked to show normal. 

## Current environmental baseline

- Python：3.12.13
- NumPy：2.5.1
- Matplotlib：3.11.0
- SciPy：1.18.0
- SymPy：1.14.0
- pytest：9.1.1
- Ruff：0.16.3
- Environmental files: `environment.yml`
- SciPy and SymPy have been installed and successfully imported; `solve_ivp` is available. 

## Unfinished business known

- Stage 20 No unfinished validation items; benchmark.py, metrics.py, results_io.py with additional script/test formats have been centrally organized through. 
- Phase 16 18 No validation items have been completed. Stage 18 The previously switched/shortened/end blank of six relevant files has been sorted by the user, format check all passed; The last import ranking has also been through a directed lint. 
- The entire repository Ruff formatter only tells you to change the end of the `tests/test_package.py` file; Ruff lint is unaffected. 
- `src/robot2dof/simulation.py`'s original airline/call encryption has been compiled in 2026-09-13 and through format check; At the end of the two previously recorded phases of the 15 test file, the blank is untreated. 
- The pytest cannot be written to `.pytest_cache` under the current Chinese workspace path, but does not affect test collection and results. 

## The next step

1. Stage 22 has completed program validation; Keep tuning configuration, optimum gain and protocol frozen, not tuning again as a result. 
2. Entry phase 23 Demo and Public Development: Read the relevant chapter of the plan and proceed according to the original collaboration agreement; Public disclosure requires further explicit authorisation. 
3. Stage 22 A command: Specify the environment Python runs `stage22/build_report.py`; Use `--output` to point to a new directory when the output already exists. See also `stage22/README.md`. HTML visual previews can be added after browser approval and validation simulation is not repeated. 
