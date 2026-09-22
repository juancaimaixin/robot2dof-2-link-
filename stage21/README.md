# Stage 21: Data Analysis and Core Figures

## Run

From this project root with the project environment active:

```powershell
python stage21/analyze.py --output stage21/reproduced_results
```

Without `--output`, the default is `output_2f080606329f`, named from fixed input fingerprints. Existing directories are protected. To rebuild the default, remove only that generated output directory first. Preserve raw experiments under `results/`, this program, and `sources.json`. No simulation or tuning rerun is needed.

```powershell
python -m pytest tests stage21/test_analysis.py -p no:cacheprovider -q
python -m ruff check stage21
python -m ruff format --check stage21
```

## Implementation

1. `sources.json` fixes four accepted run directories rather than choosing the latest directory, which could contain unaccepted or learning-only results.
2. `load_inputs()` reads 3 nominal, 15 payload, 21 model-error, and 3 disturbance runs: 42 NPZ histories, corresponding YAML configurations, and four existing metric CSV files.
3. `measure()` recomputes RMSE and peaks from joint and endpoint histories. Existing interval-metric functions compute effort, absolute mechanical work, and saturation. Recomputed metrics must agree with existing CSV values or processing stops. The simulator is not called.
4. The unified table adds scenario RMSE divided by the same controller's nominal RMSE. Each row retains project-relative NPZ/YAML paths and the configuration hash. CSV uses a UTF-8 BOM, unrounded numbers, and blanks for missing or inapplicable values.
5. The same in-memory data generate eight fixed figures and Markdown tables and explanations. Values are not transcribed manually and degraded runs are retained. `manifest.json` stores input/output SHA-256 hashes and Python, NumPy, and Matplotlib versions.
6. Tests cover normal metrics, units, endpoint semantics, missing/duplicate/unknown controllers, NaN, dimensions, time grids, all 42 inputs, and overwrite protection. Visual checks and reconstruction checks complete acceptance.

The pipeline uses existing NumPy, Matplotlib, PyYAML, and standard-library CSV, without Pandas, a new Conda environment, or an Excel workbook. The full Quarto report belongs to Stage 22; this stage's `report.md` supplies its results.

## Outputs

The generated directory contains 11 files: `summary.csv`, `report.md`, `manifest.json`, and eight PNGs.

| ID | Figure | Question |
|---|---|---|
| 01 | nominal_tracking | Can both joints track the shared reference? |
| 02 | nominal_error | What error remains behind overlapping position curves? |
| 03 | nominal_torque | How does motor torque change relative to the ±20 N·m limits? |
| 04 | nominal_metrics | How do accuracy, effort, and absolute work compare? |
| 05 | payload | How does unknown payload affect error, effort, and saturation? |
| 06 | model_uncertainty | How does controller-model error affect performance? |
| 07 | disturbance_response | How do reference error and additional nominal-relative deviation differ? |
| 08 | disturbance_metrics | How do recovery delays and post-disturbance peaks rank? |

The fixed figure list follows the original protocol. All labels, narrative, and learning explanations in this edition are English.

## Interpretation

- `control_effort_nm2_s` is the integral of summed squared motor torques, in (N·m)^2·s, not energy. `absolute_mechanical_work_j` integrates the absolute sum of joint powers, in J, not electrical consumption.
- Overall joint RMSE takes the square root after averaging squared errors over all samples and joints; it is not the arithmetic mean of individual joint RMSE values. Full-run and post-disturbance endpoint peaks differ.
- Blank `recovered` means not applicable; False means recovery was not confirmed in the observation window. Blank recovery time is not zero. The formal criterion is error at or below 10 mm for at least 0.5 s after force removal.
- CTC's near-zero nominal baseline produces large normalized ratios; read them alongside absolute error. Joint-angle and endpoint metrics may rank controllers differently.
- Deterministic simulations provide no independent random replicates, so no standard deviations, error bars, or confidence intervals are invented.
- Large payloads combine model mismatch and saturation; degradation cannot be assigned solely to controller algorithms. Separately tuned gains also prevent isolating the causal benefit of gravity compensation.

## Findings and Limits

See generated `report.md` for full values. CTC is most accurate nominally with the correct model. Payloads cause substantial degradation and saturation, so nominal rankings do not generalize. PID is unchanged by controller-model error, while gravity-compensated PID and CTC respond to it. Recovery depends on baseline tracking error; Figure 7's nominal-relative diagnostic helps explain this without replacing the formal metric.

Findings apply to the frozen gains, trajectory, and grids. Friction, backlash, delay, and sensor noise are absent; hardware performance is not established. Stage 22 produces the technical report.

## Original Acceptance Record (2026-09-17)

- Full suite: `198 passed in 7.38s`, including nine new Stage 21 cases.
- Stage 21 Ruff lint/format passed; eight figures visually inspected.
- Rebuilding after removal of generated outputs reproduced all 11 SHA-256 hashes, including PNGs, CSV, report, and manifest.
- Raw simulations and frozen gains were unchanged; no simulations, tuning, or environment changes were performed.

This historical record refers to the original edition. See `LOCALIZATION_VALIDATION.json` at the project root for this English edition's checks.
