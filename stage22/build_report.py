"""Assemble a data-bound Quarto report and render HTML plus Typst PDF."""

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
DATA = ROOT / "stage21" / "output_2f080606329f"
CONTROLLERS = ("pid", "pid_gravity", "computed_torque")
LABELS = {"pid": "PID", "pid_gravity": "PID+G", "computed_torque": "CTC"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def table(headers, rows):
    return "\n".join(
        [
            "|" + "|".join(headers) + "|",
            "|" + "|".join("---" for _ in headers) + "|",
            *["|" + "|".join(str(x) for x in row) + "|" for row in rows],
        ]
    )


def validate_data(data):
    manifest = json.loads((data / "manifest.json").read_text(encoding="utf-8"))
    for filename, expected in manifest["outputs_sha256"].items():
        if sha(data / filename) != expected:
            raise ValueError(f"Stage 21 output changed: {filename}")
    with (data / "summary.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 42:
        raise ValueError("Expected 42 accepted runs")
    keys = [
        (r["experiment"], r["controller"], r["payload_mass_kg"], r["relative_error"])
        for r in rows
    ]
    if len(set(keys)) != len(rows):
        raise ValueError("Duplicate experiment rows")
    for row in rows:
        if row["controller"] not in CONTROLLERS:
            raise ValueError("Unknown controller")
        for key in (
            "overall_joint_rmse_deg",
            "end_effector_rmse_m",
            "maximum_end_effector_error_m",
            "control_effort_nm2_s",
            "absolute_mechanical_work_j",
            "saturation_fraction",
        ):
            if not np.isfinite(float(row[key])):
                raise ValueError(f"Non-finite metric: {key}")
        path = ROOT / row["source_yaml"]
        if sha(path) != manifest["input_sha256"][row["source_yaml"]]:
            raise ValueError("Source configuration changed")
    return rows, manifest


def make_values(rows, manifest):
    def select(experiment, field=None, value=None):
        selected = [
            r
            for r in rows
            if r["experiment"] == experiment
            and (field is None or float(r[field]) == value)
        ]
        return sorted(selected, key=lambda r: CONTROLLERS.index(r["controller"]))

    def numbers(selected, key, scale=1, digits=3):
        return " / ".join(f"{float(r[key]) * scale:.{digits}f}" for r in selected)

    def config(row):
        return yaml.safe_load((ROOT / row["source_yaml"]).read_text(encoding="utf-8"))

    nom = select("nominal")
    dis = select("disturbance")
    cfg = config(nom[0])
    dcfg = config(dis[0])
    tuning = json.loads(
        (ROOT / "results/tuning_search.json").read_text(encoding="utf-8")
    )
    if tuning["configuration_sha256"] != manifest["tuning_configuration_sha256"]:
        raise ValueError("Tuning identity mismatch")
    tc = tuning["configuration"]
    payloads = sorted(
        {float(r["payload_mass_kg"]) for r in rows if r["experiment"] == "payload"}
    )
    errors = sorted(
        {
            float(r["relative_error"])
            for r in rows
            if r["experiment"] == "model_uncertainty"
        }
    )
    maxload = select("payload", "payload_mass_kg", max(payloads))
    light = select("payload", "payload_mass_kg", payloads[1])
    parameters = cfg["actual_model"]
    units = {
        "l1": "m",
        "l2": "m",
        "lc1": "m",
        "lc2": "m",
        "m1": "kg",
        "m2": "kg",
        "I1": "kg·m²",
        "I2": "kg·m²",
        "g": "m/s²",
    }
    gains = []
    for r in nom:
        g = config(r)["controller"]["gains"]
        gains.append(
            [
                LABELS[r["controller"]],
                *[
                    "(" + ", ".join(f"{v:.5g}" for v in g[k]) + ")" if k in g else "N/A"
                    for k in ("kp", "ki", "kd")
                ],
            ]
        )
    appendix = []
    for experiment in manifest["source_selection"]:
        selected = [r for r in rows if r["experiment"] == experiment]
        appendix += [
            f"## {experiment}",
            "",
            table(
                [
                    "Parameter",
                    "Controller",
                    "Joint RMSE",
                    "EE RMSE",
                    "Full-run peak",
                    "Saturation %",
                ],
                [
                    [
                        r["payload_mass_kg"] or r["relative_error"] or "—",
                        LABELS[r["controller"]],
                        f"{float(r['overall_joint_rmse_deg']):.6f}",
                        f"{float(r['end_effector_rmse_m']) * 1000:.3f}",
                        f"{float(r['maximum_end_effector_error_m']) * 1000:.3f}",
                        f"{float(r['saturation_fraction']) * 100:.3f}",
                    ]
                    for r in selected
                ],
            ),
            "",
        ]
    train = tc["training_scenario"]
    pulse = dcfg["disturbance"]
    rule = dcfg["metrics"]["recovery_time"]
    values = {
        "run_count": len(rows),
        "nominal_rmse": numbers(nom, "overall_joint_rmse_deg", digits=6),
        "recovery": numbers(dis, "recovery_time_s"),
        "torque_limit": cfg["actuator"]["limit_nm"],
        "parameter_table": table(
            ["Parameter", "Value", "Unit"],
            [[k, f"{parameters[k]:.8g}", units[k]] for k in units],
        ),
        "training_path": " → ".join(
            "[" + ", ".join(f"{v:.0f}°" for v in np.degrees(q)) + "]"
            for q in train["waypoint_positions"]
        ),
        "training_duration": train["waypoint_times"][-1] - train["waypoint_times"][0],
        "trajectory_table": table(
            ["Time (s)", "q₁ (°)", "q₂ (°)"],
            [
                [t, *[f"{v:.0f}" for v in np.degrees(q)]]
                for t, q in zip(
                    cfg["trajectory"]["waypoint_times"],
                    cfg["trajectory"]["waypoint_positions"],
                )
            ],
        ),
        "gain_table": table(["Controller", "Kp", "Ki", "Kd"], gains),
        "candidate_count": tc["candidate_count_per_controller"],
        "candidate_total": tc["candidate_count_per_controller"] * len(CONTROLLERS),
        "seed": tc["seed"],
        "weight_tracking": tc["weights"]["tracking_error"],
        "weight_effort": tc["weights"]["control_effort"],
        "weight_saturation": tc["weights"]["saturation"],
        "step": cfg["simulation"]["step_s"],
        "sample_count": round(
            (
                cfg["trajectory"]["waypoint_times"][-1]
                - cfg["trajectory"]["waypoint_times"][0]
            )
            / cfg["simulation"]["step_s"]
        )
        + 1,
        "scenario_table": table(
            ["Scenario", "Condition", "Runs"],
            [
                ["Nominal", "Identical plant and controller models", len(nom)],
                [
                    "Payload",
                    ", ".join(map(str, payloads))
                    + " kg; payload added to the plant only",
                    sum(r["experiment"] == "payload" for r in rows),
                ],
                [
                    "Model uncertainty",
                    ", ".join(f"{v * 100:.0f}%" for v in errors),
                    sum(r["experiment"] == "model_uncertainty" for r in rows),
                ],
                [
                    "Disturbance",
                    f"F={pulse['force_n']} N，[{pulse['start_time_s']}, {pulse['end_time_s']}) s",
                    len(dis),
                ],
            ],
        ),
        "threshold_mm": rule["threshold_m"] * 1000,
        "hold": rule["hold_duration_s"],
        "nominal_table": table(
            ["Controller", "RMSE (°)", "EE RMSE (mm)", "Effort", "Work (J)"],
            [
                [
                    LABELS[r["controller"]],
                    f"{float(r['overall_joint_rmse_deg']):.6f}",
                    f"{float(r['end_effector_rmse_m']) * 1000:.4f}",
                    f"{float(r['control_effort_nm2_s']):.3f}",
                    f"{float(r['absolute_mechanical_work_j']):.3f}",
                ]
                for r in nom
            ],
        ),
        "nominal_saturation": numbers(nom, "saturation_fraction", 100) + "%",
        "payload_light": payloads[1],
        "payload_light_rmse": numbers(light, "overall_joint_rmse_deg"),
        "payload_max": max(payloads),
        "payload_max_rmse": numbers(maxload, "overall_joint_rmse_deg"),
        "payload_max_saturation": numbers(maxload, "saturation_fraction", 100) + "%",
        "payload_ratios": numbers(maxload, "rmse_ratio_to_own_nominal"),
        "payload_table": table(
            ["Payload (kg)", "PID", "PID+G", "CTC"],
            [
                [
                    v,
                    *[
                        f"{float(r['overall_joint_rmse_deg']):.6f}"
                        for r in select("payload", "payload_mass_kg", v)
                    ],
                ]
                for v in payloads
            ],
        ),
        "pid_nominal": numbers(nom[:1], "overall_joint_rmse_deg", digits=6),
        "ctc_nominal": numbers(nom[2:], "overall_joint_rmse_deg", digits=6),
        "model_min": f"{min(errors) * 100:.0f}",
        "model_max": f"{max(errors) * 100:.0f}",
        "ctc_model_min": numbers(
            select("model_uncertainty", "relative_error", min(errors))[2:],
            "overall_joint_rmse_deg",
            digits=6,
        ),
        "ctc_model_max": numbers(
            select("model_uncertainty", "relative_error", max(errors))[2:],
            "overall_joint_rmse_deg",
            digits=6,
        ),
        "force": str(pulse["force_n"]),
        "pulse_start": pulse["start_time_s"],
        "pulse_end": pulse["end_time_s"],
        "post_peaks": numbers(dis, "post_disturbance_peak_m", 1000),
        "disturbance_table": table(
            [
                "Controller",
                "Recovery (s)",
                "Full-run peak (mm)",
                "Post-disturbance peak (mm)",
                "Saturation %",
            ],
            [
                [
                    LABELS[r["controller"]],
                    f"{float(r['recovery_time_s']):.3f}",
                    f"{float(r['maximum_end_effector_error_m']) * 1000:.3f}",
                    f"{float(r['post_disturbance_peak_m']) * 1000:.3f}",
                    f"{float(r['saturation_fraction']) * 100:.3f}",
                ]
                for r in dis
            ],
        ),
        "source_table": table(
            ["Scenario", "Run directory under results/"],
            [[k, f"`{Path(v).name}`"] for k, v in manifest["source_selection"].items()],
        ),
        "appendix_tables": "\n".join(appendix),
    }
    return values


def substitute(template, values):
    needed = set(re.findall(r"@@(\w+)@@", template))
    missing = needed - values.keys()
    if missing:
        raise ValueError(f"Missing report fields: {sorted(missing)}")
    return re.sub(r"@@(\w+)@@", lambda m: str(values[m[1]]), template)


def find_quarto():
    found = shutil.which("quarto")
    candidate = (
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs/Quarto/bin/quarto.exe"
    )
    if found:
        return found
    if candidate.is_file():
        return str(candidate)
    raise FileNotFoundError("Quarto is required; install Quarto or add it to PATH")


def build(output=HERE / "output", render=True):
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"Output exists: {output}. Use --output NEW_DIRECTORY")
    rows, manifest = validate_data(DATA)
    values = make_values(rows, manifest)
    qmd = substitute((HERE / "report_template.qmd").read_text(encoding="utf-8"), values)
    quarto = find_quarto() if render else None
    output.mkdir(parents=True)
    (output / "figures").mkdir()
    for name in manifest["outputs_sha256"]:
        if name.endswith(".png"):
            shutil.copy2(DATA / name, output / "figures" / name)
    shutil.copy2(DATA / "summary.csv", output / "summary.csv")
    shutil.copy2(HERE / "styles.css", output / "styles.css")
    (output / "report.qmd").write_text(qmd, encoding="utf-8")
    (output / "report_values.json").write_text(
        json.dumps(values, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    version = None
    if render:
        version = subprocess.check_output([quarto, "--version"], text=True).strip()
        for format_name in ("html", "typst"):
            run = subprocess.run(
                [quarto, "render", "report.qmd", "--to", format_name],
                cwd=output,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            (output / f"render_{format_name}.log").write_text(
                run.stdout + run.stderr, encoding="utf-8"
            )
            if run.returncode:
                raise RuntimeError(
                    f"Quarto {format_name} failed; see render_{format_name}.log"
                )
        for name in ("report.html", "report.pdf"):
            if not (output / name).is_file():
                raise RuntimeError(f"Missing rendered output: {name}")
    evidence = {
        "stage21_manifest_sha256": sha(DATA / "manifest.json"),
        "tuning_sha256": sha(ROOT / "results/tuning_search.json"),
        "source_sha256": {
            p.name: sha(p)
            for p in (
                HERE / "build_report.py",
                HERE / "report_template.qmd",
                HERE / "styles.css",
            )
        },
        "run_count": len(rows),
        "quarto_version": version,
        "rendered": render,
        "outputs_sha256": {
            p.relative_to(output).as_posix(): sha(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
            and not any(part.startswith(".") for part in p.relative_to(output).parts)
        },
    }
    (output / "build_manifest.json").write_text(
        json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=HERE / "output")
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    build(args.output, render=not args.prepare_only)
