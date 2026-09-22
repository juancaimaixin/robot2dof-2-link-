# Planar Two-DOF Robot Arm: Tracking and Robustness

A reproducible Python study comparing **independent-joint PID**, **PID with gravity compensation**, and **computed torque control (CTC)** on a rigid robot arm moving in a vertical plane.

## Start Here

- [Technical report (HTML)](stage22/output/report.html)
- [Technical report (PDF)](stage22/output/report.pdf)
- [All 42 evaluation runs (CSV)](stage22/output/summary.csv)
- [Research questions and advance predictions](RESEARCH_CHARTER.md)
- [Derivation notes](notebooks/09_lagrangian_derivation.md)
- [Theory index](THEORY_NOTES.md)

The report covers the model, trajectories, controllers, fair tuning, nominal tracking, unknown payloads, controller-model errors, force disturbances, limitations, and full results.

## Main Findings

| Metric | PID | PID + Gravity | CTC |
|---|---:|---:|---:|
| Nominal overall joint RMSE (degrees) | 1.115037 | 0.152634 | 0.004992 |
| Formal force-disturbance recovery delay (s) | 1.555 | 0.087 | 0.263 |

CTC is most accurate nominally. Its advantage does not hold across all mismatches and disturbances. Gravity-compensated PID recovers fastest under the specified force-recovery criterion. Findings apply to the frozen gains and tested conditions; they are simulation results, not hardware measurements.

![Nominal tracking errors](stage21/output_2f080606329f/02_nominal_error.png)

## Run on the Original Workstation

Open PowerShell in **this English-edition project root**. The launcher selects this copy's `src` directory, so an editable installation of the original project cannot silently override it.

```powershell
.\run.ps1 -Python 'D:\miniconda\envs\robot2dof\python.exe' -Arguments @('-m', 'pytest', '-p', 'no:cacheprovider', '-q')
.\run.ps1 -Python 'D:\miniconda\envs\robot2dof\python.exe' -Arguments @('stage21/analyze.py', '--output', 'stage21/reproduced_analysis')
.\run.ps1 -Python 'D:\miniconda\envs\robot2dof\python.exe' -Arguments @('stage22/build_report.py', '--output', 'stage22/reproduced_report')
```

Use a new output directory for each rebuild. Existing outputs are protected. Analysis and report generation reuse saved experiments; neither retunes nor reruns the simulations.

## Set Up on Another Computer

```powershell
conda env create -f environment.yml
conda activate robot2dof
python -m pip install -e .
python -m pytest -p no:cacheprovider -q
python -m ruff check --no-cache src tests experiments stage21 stage22
```

Quarto with Typst is needed only to rebuild HTML/PDF. The accepted original environment uses Quarto 1.10.18 and Typst 0.15.1; the English report uses Arial. Already-rendered reports can be read without Python or Quarto.

## Experiments

After installation, or via `run.ps1` to select this source tree:

```powershell
python experiments/run_nominal_benchmark.py
python experiments/run_payload_benchmark.py
python experiments/run_model_uncertainty_benchmark.py
python experiments/run_disturbance_benchmark.py
```

These commands create new simulation results. Frozen gains and the original 900-candidate tuning record are in `results/tuning_search.json`. Do not retune using the held-out benchmark results.

## Project Contents

| Location | Contents |
|---|---|
| `src/robot2dof/` | Kinematics, dynamics, integration, trajectories, controllers, tuning, metrics, and result I/O |
| `tests/` | Numerical and behavioral regression tests |
| `experiments/` | Reproducible experiment and plotting entry points |
| `results/` | Complete saved experiment histories, configurations, metadata, metrics, and figures |
| `notebooks/` | Lagrangian derivation notes and equation figure |
| `stage21/` | Unified analysis, eight core figures, CSV, and provenance manifest |
| `stage22/` | Data-bound Quarto report builder, template, HTML, and PDF |
| `PLAN.md` | Original research roadmap and fixed protocol |
| `PROGRESS.md`, `PROGRESS_HISTORY.md` | Current project summary and full dated development archive |
| `MATLAB_LEARNING_PLAN.md` | Separate MATLAB/Simulink learning roadmap |
| `LOCALIZATION_VALIDATION.json` | English-edition validation and data-preservation evidence |

## English-Edition Notes

This edition retains the working project, including uncommitted source and saved results. Internal stage/document names and references are English. Git internals, package-installation metadata, and disposable caches are excluded. The outer folder name was chosen by the project owner.

Core numerical source, raw NPZ histories, YAML configurations, metric CSV files, and frozen tuning records are preserved. Report/analysis prose and generated reports are localized. A pre-existing malformed line in `tests/test_simulation.py` was repaired in this copy by restoring separate coarse-to-medium and medium-to-fine error calculations. Pytest explicitly selects this copy's `src` and includes Stage 21/22 tests.

Dated progress and learning records describe the project at the time they were written; superseded plans and historical limitations are retained. The long development archive was translated with local offline translation assistance. The report, research charter, theory index, research and MATLAB plans, current summary, and reading instructions received direct editorial translation. Original-record hashes identify the historical runs; regenerated English analysis/report manifests identify the localized artifacts.
