# Stage 22: Technical Report

## Read the Results

- `output/report.html`: primary reading version, with navigable contents and references, eight embedded images, embedded resources, and MathML equations.
- `output/report.pdf`: English archival report covering the model, trajectory, controllers, methods, results, discussion, limitations, conclusions, and all 42 runs.
- `output/summary.csv`: full-precision results and original NPZ/YAML paths relative to this project root.

## Rebuild

From the project root with the project environment active:

```powershell
python stage22/build_report.py --output stage22/reproduced_results
```

The default output is `stage22/output`. Existing directories are protected; choose a new directory for another build. Removing only this stage's generated output allows the default command to rebuild it. Preserve Stage 21 outputs and raw `results/` data. `--prepare-only` assembles source and resources without rendering HTML/PDF.

The original runtime uses Python environment `robot2dof`, NumPy, PyYAML, Quarto 1.10.18, and bundled Typst 0.15.1. The English PDF uses Arial. Quarto is located through PATH or the standard user installation directory. No Jupyter execution kernel or LaTeX is required. Python assembles data and Quarto renders both formats from one source.

## Implementation

1. `RESEARCH_CHARTER.md` and the Stage 22 plan define the narrative. Results state observations; discussion evaluates four advance predictions and their limits.
2. `build_report.py` validates fixed Stage 21 output hashes and reads all runs, source configurations, and frozen tuning records. Numerical statements and parameter, gain, waypoint, and scenario tables are generated automatically.
3. `report_template.qmd` contains English prose, the abstract, mathematics, and explanations. `@@field@@` placeholders bind generated data; missing fields stop the build. Experimental values are never manually transcribed. Mathematical constants, section numbers, and document dates are not experimental data.
4. Eight figures and the CSV are copied unchanged from Stage 21. Quarto renders the same `report.qmd` to HTML and Typst PDF, retaining logs.
5. `build_manifest.json` records program, template, input, and output hashes and the Quarto version. Edit the template or builder and rebuild into a new directory; do not edit generated HTML/PDF alone.

This stage does not rerun simulations, change frozen gains, retune from results, or publish the Stage 23 release.

## Scope of Interpretation

The report addresses nominal accuracy, unknown payload, model errors, and force recovery, retaining degraded and highly saturated conditions. It distinguishes joint/endpoint errors, full-run/post-disturbance peaks, formal recovery/nominal-relative deviation, and effort/mechanical work. Deterministic runs do not justify statistical error bars or significance tests. Conclusions apply to the frozen gains and tested protocol, without hardware extrapolation.

Modern Robotics teaching material supplies theoretical context; official Quarto Typst documentation supplies rendering guidance. Links appear in the report. Project numerical claims are supported by frozen data and source files.

## Original Acceptance Record (2026-09-17)

- Full pytest across core tests and Stages 21/22: `202 passed in 6.22s`, including four new report tests.
- Ruff lint and format checks passed.
- Two HTML/PDF builds succeeded without warnings or errors.
- All 12 pages of the original bilingual PDF were visually checked for text, equations, captions, page breaks, and repeated table headers.
- HTML, source, values, CSV, styles, and eight figures were byte-identical across rebuilds. PDF extracted text and 1100-pixel page renders matched; timestamps differed, so PDF byte identity was not claimed.
- Static HTML checks found eight embedded images, 42 MathML equations, valid internal references, and no external script/style dependencies.
- Browser visual inspection was not completed: automatic approval rejected local preview because of usage limits. Static inspection was not represented as browser inspection.
- Historical machine-readable evidence is in `verification_original_edition.json`. English report checks are in `verification.json`. English page images under `qa/` are inspection materials regenerated for this edition.

This historical record does not certify the translated report. See root `LOCALIZATION_VALIDATION.json` for English-edition checks.

```powershell
python -m pytest tests stage21/test_analysis.py stage22/test_report.py -p no:cacheprovider -q
python -m ruff check stage22
python -m ruff format --check stage22
```

Stage 23 covers the demo and public release. This work does not commit, push, or publish the project.
