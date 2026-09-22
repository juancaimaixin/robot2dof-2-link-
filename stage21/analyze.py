"""Rebuild stage 21 from saved experiments; never run or tune a controller."""

import argparse
import csv
import hashlib
import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import yaml

from robot2dof.metrics import compute_actuation_metrics, compute_recovery_time

ROOT = Path(__file__).resolve().parents[1]
HERE = Path(__file__).resolve().parent
CONTROLLERS = ("pid", "pid_gravity", "computed_torque")
LABELS = ("PID", "PID + Gravity", "CTC")
COLORS = ("#2878B5", "#D97922", "#238B57")
GRIDS = {
    "nominal": (None,),
    "payload": (0.0, 0.25, 0.5, 0.75, 1.0),
    "model_uncertainty": (-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3),
    "disturbance": (None,),
}
FROZEN = "50247f53d83e161b5419f0e59216c5064f2d6f8700eca295f6dc253e140ec3da"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stem_for(experiment, controller, value):
    suffix = {
        "nominal": "",
        "payload": f"_payload_{value}kg",
        "model_uncertainty": f"_model_error_{value}",
        "disturbance": "_disturbance",
    }
    return controller + suffix[experiment]


def measure(history):
    """Metrics on saved joint/Cartesian arrays with explicit units."""
    t = history["time_values"]
    if t.ndim != 1 or t.size < 2 or not np.all(np.isfinite(t)):
        raise ValueError("Invalid time grid")
    if not np.allclose(np.diff(t), 0.001, rtol=0, atol=1e-12):
        raise ValueError("Expected uniform 0.001 s grid")
    shapes = {
        "state_history": (len(t), 4),
        "reference_position_history": (len(t), 2),
        "end_effector_position_history": (len(t), 2),
        "reference_end_effector_position_history": (len(t), 2),
        "applied_torque_history": (len(t), 2),
        "saturation_history": (len(t), 2),
    }
    for key, shape in shapes.items():
        if history[key].shape != shape or not np.all(np.isfinite(history[key])):
            raise ValueError(f"Invalid history: {key}")
    e = history["reference_position_history"] - history["state_history"][:, :2]
    distance = np.linalg.norm(
        history["reference_end_effector_position_history"]
        - history["end_effector_position_history"],
        axis=1,
    )
    joint = np.sqrt(np.mean(e**2, axis=0))
    overall = float(np.sqrt(np.mean(e**2)))
    act = compute_actuation_metrics(
        t,
        history["applied_torque_history"],
        history["state_history"][:, 2:],
        history["saturation_history"],
    )
    return {
        "joint_1_rmse_rad": float(joint[0]),
        "joint_2_rmse_rad": float(joint[1]),
        "overall_joint_rmse_rad": overall,
        "joint_1_rmse_deg": float(np.degrees(joint[0])),
        "joint_2_rmse_deg": float(np.degrees(joint[1])),
        "overall_joint_rmse_deg": float(np.degrees(overall)),
        "end_effector_rmse_m": float(np.sqrt(np.mean(distance**2))),
        "maximum_end_effector_error_m": float(distance.max()),
        "control_effort_nm2_s": act.control_effort,
        "saturation_fraction": act.saturation_fraction,
        "absolute_mechanical_work_j": act.absolute_mechanical_work_j,
    }, distance


def validate_summary(rows, experiment):
    field = {"payload": "payload_mass_kg", "model_uncertainty": "relative_error"}.get(
        experiment
    )
    keyed = {}
    for row in rows:
        key = (row["controller"], float(row[field]) if field else None)
        if key in keyed:
            raise ValueError(f"Duplicate summary row: {key}")
        keyed[key] = row
    expected = {(c, v) for v in GRIDS[experiment] for c in CONTROLLERS}
    if set(keyed) != expected:
        raise ValueError(f"Incomplete or unexpected {experiment} grid")
    return keyed


def load_inputs(source_file=HERE / "sources.json"):
    sources = json.loads(source_file.read_text(encoding="utf-8"))
    if set(sources) != set(GRIDS):
        raise ValueError("Expected four experiment sources")
    rows, histories, inputs = [], {}, {}
    for experiment, grid in GRIDS.items():
        directory = ROOT / sources[experiment]
        csv_path = directory / f"{experiment}_metrics.csv"
        inputs[csv_path.relative_to(ROOT).as_posix()] = sha(csv_path)
        with csv_path.open(encoding="utf-8", newline="") as stream:
            original = validate_summary(list(csv.DictReader(stream)), experiment)
        for value in grid:
            for controller in CONTROLLERS:
                stem = stem_for(experiment, controller, value)
                npz, config_path = directory / f"{stem}.npz", directory / f"{stem}.yaml"
                config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
                with np.load(npz, allow_pickle=False) as archive:
                    h = {k: archive[k] for k in archive.files}
                if str(h["controller"]) != controller:
                    raise ValueError("Controller identity mismatch")
                if str(h["tuning_configuration_sha256"]) != FROZEN:
                    raise ValueError("Frozen tuning identity mismatch")
                metrics, distance = measure(h)
                reference = original[(controller, value)]
                for key, actual in metrics.items():
                    if not np.isclose(
                        actual, float(reference[key]), rtol=1e-10, atol=1e-12
                    ):
                        raise ValueError(f"Saved summary disagrees: {stem}/{key}")
                if not (len(h["time_values"]) == 8001 and h["time_values"][0] == 0):
                    raise ValueError("Expected complete 0–8 s history")
                recovery = None
                recovered = None
                peak = None
                if experiment == "disturbance":
                    rule = config["metrics"]["recovery_time"]
                    recovery = compute_recovery_time(
                        h["time_values"],
                        distance,
                        rule["disturbance_end_time_s"],
                        rule["threshold_m"],
                        rule["hold_duration_s"],
                    )
                    recovered = recovery is not None
                    saved = reference["recovery_time_s"]
                    if (
                        reference["recovered"] != str(recovered)
                        or (
                            recovered
                            and (
                                not saved
                                or not np.isclose(
                                    float(saved), recovery, rtol=0, atol=1e-12
                                )
                            )
                        )
                        or (not recovered and saved)
                    ):
                        raise ValueError("Recovery summary disagrees")
                    peak = float(
                        distance[
                            h["time_values"] >= config["disturbance"]["start_time_s"]
                        ].max()
                    )
                row = {
                    "experiment": experiment,
                    "controller": controller,
                    "payload_mass_kg": value if experiment == "payload" else None,
                    "relative_error": value
                    if experiment == "model_uncertainty"
                    else None,
                    **metrics,
                    "recovered": recovered,
                    "recovery_time_s": recovery,
                    "post_disturbance_peak_m": peak,
                    "source_npz": npz.relative_to(ROOT).as_posix(),
                    "source_yaml": config_path.relative_to(ROOT).as_posix(),
                    "configuration_sha256": str(h["configuration_sha256"]),
                }
                for path in (npz, config_path):
                    inputs[path.relative_to(ROOT).as_posix()] = sha(path)
                rows.append(row)
                h["distance"] = distance
                histories[(experiment, controller, value)] = h
    # All comparisons use the same retained reference and time grid.
    base = histories[("nominal", "pid", None)]
    for h in histories.values():
        for key in ("time_values", "reference_position_history"):
            if not np.array_equal(h[key], base[key]):
                raise ValueError("Experiments use different references/time grids")
    nominal = {r["controller"]: r for r in rows if r["experiment"] == "nominal"}
    for row in rows:
        denominator = nominal[row["controller"]]["overall_joint_rmse_deg"]
        row["rmse_ratio_to_own_nominal"] = (
            row["overall_joint_rmse_deg"] / denominator if denominator > 0 else None
        )
    return rows, histories, inputs


def write_csv(path, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def make_figures(rows, histories, output):
    plt.rcParams.update(
        {"font.size": 10, "axes.spines.top": False, "axes.spines.right": False}
    )
    figures = []

    def save(fig, name, title):
        fig.suptitle(title, fontsize=14)
        for ax in fig.axes:
            ax.grid(alpha=0.22)
        fig.savefig(output / f"{name}.png", dpi=180)
        plt.close(fig)
        figures.append((name, title))

    nominal = [r for r in rows if r["experiment"] == "nominal"]
    t = histories[("nominal", "pid", None)]["time_values"]
    for number, kind, ylabel in (
        (1, "tracking", "Position [deg]"),
        (2, "error", "Reference - actual [deg]"),
        (3, "torque", "Applied motor torque [N m]"),
    ):
        fig, axes = plt.subplots(1, 2, figsize=(12, 4), layout="constrained")
        for joint, ax in enumerate(axes):
            for c, label, color in zip(CONTROLLERS, LABELS, COLORS):
                h = histories[("nominal", c, None)]
                q = h["state_history"][:, joint]
                ref = h["reference_position_history"][:, joint]
                y = np.degrees(q if kind == "tracking" else ref - q)
                if kind == "torque":
                    ax.stairs(
                        h["applied_torque_history"][:-1, joint],
                        t,
                        baseline=None,
                        label=label,
                        color=color,
                    )
                else:
                    ax.plot(t, y, label=label, color=color)
            if kind == "tracking":
                ax.plot(t, np.degrees(ref), "k--", label="Reference", linewidth=1.3)
            if kind == "torque":
                for limit in (-20, 20):
                    ax.axhline(limit, color="gray", linestyle="--", linewidth=1)
            ax.set(xlabel="Time [s]", ylabel=ylabel, title=f"Joint {joint + 1}")
            ax.legend(fontsize=8)
        save(fig, f"0{number}_nominal_{kind}", f"Nominal | {kind}")
    metrics = (
        ("overall_joint_rmse_deg", "Joint RMSE [deg]", 1),
        ("end_effector_rmse_m", "End-effector RMSE [mm]", 1000),
        ("control_effort_nm2_s", "Control effort [(N m)^2 s]", 1),
        ("absolute_mechanical_work_j", "Absolute total mechanical work [J]", 1),
    )
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout="constrained")
    for ax, (key, title, scale) in zip(axes.flat, metrics):
        bars = ax.bar(LABELS, [r[key] * scale for r in nominal], color=COLORS)
        ax.bar_label(bars, fmt="%.4g", padding=4)
        ax.set(title=title, ylim=(0, max(r[key] * scale for r in nominal) * 1.22))
    save(fig, "04_nominal_metrics", "Nominal | accuracy and actuation")
    sensitivity = (
        ("overall_joint_rmse_deg", "Joint RMSE [deg]", 1),
        ("control_effort_nm2_s", "Control effort [(N m)^2 s]", 1),
        ("saturation_fraction", "Saturated time [%]", 100),
    )
    for number, experiment, field, xlabel, xscale in (
        (5, "payload", "payload_mass_kg", "Payload [kg]", 1),
        (6, "model_uncertainty", "relative_error", "Controller model error [%]", 100),
    ):
        fig, axes = plt.subplots(1, 3, figsize=(14, 4.2), layout="constrained")
        for ax, (metric, title, scale) in zip(axes, sensitivity):
            for c, label, color, marker in zip(
                CONTROLLERS, LABELS, COLORS, ("o", "s", "^")
            ):
                selected = [
                    r
                    for r in rows
                    if r["experiment"] == experiment and r["controller"] == c
                ]
                ax.plot(
                    [r[field] * xscale for r in selected],
                    [r[metric] * scale for r in selected],
                    color=color,
                    marker=marker,
                    label=label,
                    markersize=5,
                    fillstyle="none",
                )
            ax.set(xlabel=xlabel, ylabel=title)
            if metric == "saturation_fraction":
                group = [r for r in rows if r["experiment"] == experiment]
                ax.set_ylim(-1, 101 if max(r[metric] for r in group) > 0 else 5)
                if all(r[metric] == 0 for r in group):
                    ax.text(
                        0.5,
                        0.5,
                        "All controllers: 0% saturation",
                        transform=ax.transAxes,
                        ha="center",
                    )
            ax.legend(fontsize=8)
        save(
            fig,
            f"0{number}_{experiment}",
            f"{experiment.replace('_', ' ').title()} | frozen gains",
        )
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    for c, label, color in zip(CONTROLLERS, LABELS, COLORS):
        h = histories[("disturbance", c, None)]
        base = histories[("nominal", c, None)]
        axes[0].plot(t, h["distance"] * 1000, label=label, color=color)
        deviation = np.linalg.norm(
            h["end_effector_position_history"] - base["end_effector_position_history"],
            axis=1,
        )
        axes[1].plot(t, deviation * 1000, label=label, color=color)
    for ax, title in zip(
        axes, ("Formal tracking error", "Extra deviation from nominal (diagnostic)")
    ):
        ax.axvspan(4.5, 4.7, alpha=0.15, color="gray", label="Force pulse")
        ax.axhline(
            10, color="black", linestyle="--", linewidth=1, label="10 mm threshold"
        )
        ax.set(
            xlim=(4.3, 8),
            xlabel="Time [s]",
            ylabel="End-effector distance [mm]",
            title=title,
        )
        ax.legend(fontsize=8)
    save(
        fig,
        "07_disturbance_response",
        "Disturbance | absolute tracking and nominal baseline",
    )
    perturbed = [r for r in rows if r["experiment"] == "disturbance"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    for ax, key, title, scale in (
        (axes[0], "recovery_time_s", "Formal recovery delay [s]", 1),
        (axes[1], "post_disturbance_peak_m", "Peak tracking error, 4.5–8 s [mm]", 1000),
    ):
        values = [r[key] * scale if r[key] is not None else 0 for r in perturbed]
        bars = ax.bar(LABELS, values, color=COLORS)
        labels = [
            f"{v:.3f}" if r[key] is not None else "Not recovered"
            for r, v in zip(perturbed, values)
        ]
        ax.bar_label(bars, labels=labels, padding=4)
        ax.set(title=title, ylim=(0, max(max(values) * 1.25, 0.1)))
    save(
        fig,
        "08_disturbance_metrics",
        "Disturbance | <=10 mm for at least 0.5 s after pulse end",
    )
    return figures


def write_report(rows, figures, output):
    lines = [
        "# Stage 21: Data Analysis and Core Figures",
        "",
        "This page and all values are generated by analyze.py from frozen runs: 42 deterministic simulations, without statistical error bars or confidence intervals.",
        "",
        "## Metric Definitions",
        "",
        "Joint RMSE includes all 8001 samples and both joints; end-effector error is Euclidean distance. Control effort is the integral of squared actual motor torque, in (N.m)^2.s, not energy. Absolute mechanical work is the integral of absolute total joint power, in J, and does not represent electrical consumption. Saturation is measured by the duration of intervals with either joint saturated.",
        "",
        "Recovery is measured from 4.7 s: error must stay at or below 10 mm for at least 0.5 s. Unconfirmed recovery is identified explicitly; non-disturbance runs show a dash. Peak columns cover 0-8 s; post-disturbance peaks over 4.5-8 s are stored separately in the CSV.",
        "",
        "The normalized column is scenario RMSE / the same controller nominal RMSE. CTC has a very small nominal baseline; ratios alone cannot rank different controllers. A zero denominator leaves the value blank.",
        "",
        "## All Runs",
        "",
        "|Experiment|Parameter|Controller|Joint RMSE (deg)|EE RMSE (mm)|Full-run peak (mm)|Effort ((N.m)^2s)|Absolute work (J)|Saturation (%)|Recovery (s)|RMSE / own nominal|",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        parameter = (
            r["payload_mass_kg"]
            if r["experiment"] == "payload"
            else r["relative_error"]
        )
        recovery = (
            "—"
            if r["experiment"] != "disturbance"
            else (
                "Unconfirmed" if not r["recovered"] else f"{r['recovery_time_s']:.3f}"
            )
        )
        ratio = r["rmse_ratio_to_own_nominal"]
        lines.append(
            f"|{r['experiment']}|{parameter if parameter is not None else '—'}|{r['controller']}|{r['overall_joint_rmse_deg']:.6f}|{r['end_effector_rmse_m'] * 1000:.3f}|{r['maximum_end_effector_error_m'] * 1000:.3f}|{r['control_effort_nm2_s']:.3f}|{r['absolute_mechanical_work_j']:.3f}|{r['saturation_fraction'] * 100:.3f}|{recovery}|{ratio if ratio is None else f'{ratio:.3f}'}|"
        )
    lines += [
        "",
        "## Interpretation",
        "",
        "With these frozen gains, model-compensating controllers have smaller nominal tracking errors. Payload and model-error curves show that nominal superiority does not guarantee superiority under mismatch. Controllers were tuned separately, so differences cannot be attributed solely to adding one compensation term.",
        "",
        "Formal disturbance recovery is affected by both baseline tracking error and additional deviation. The right panel of Figure 7 is diagnostic and does not replace the formal criterion in Figure 8. Unknown external force is not compensated by nominal CTC; nominal accuracy does not establish the strongest disturbance rejection.",
        "",
        "Conclusions apply only to the frozen gains, held-out trajectory, payload/error grids, and force protocol. They do not predict hardware performance. The model excludes friction, backlash, delay, and sensor noise.",
        "",
        "## Core Figures",
        "",
    ]
    for name, title in figures:
        lines += [f"### {name}: {title}", "", f"![{title}]({name}.png)", ""]
    (output / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(output=None, sources=HERE / "sources.json"):
    rows, histories, inputs = load_inputs(sources)
    signature = hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()[
        :12
    ]
    output = Path(output) if output else HERE / f"output_{signature}"
    if output.exists():
        raise FileExistsError(
            f"Output already exists: {output}; choose --output NEW_DIRECTORY"
        )
    output.mkdir(parents=True)
    write_csv(output / "summary.csv", rows)
    figures = make_figures(rows, histories, output)
    write_report(rows, figures, output)
    manifest = {
        "input_sha256": inputs,
        "source_selection": json.loads(sources.read_text(encoding="utf-8")),
        "builder_sha256": sha(Path(__file__)),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "matplotlib": matplotlib.__version__,
        "tuning_configuration_sha256": FROZEN,
        "run_count": len(rows),
        "outputs_sha256": {p.name: sha(p) for p in sorted(output.iterdir())},
    }
    (output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(output)
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        help="New output directory; existing directories are never overwritten",
    )
    parser.add_argument("--sources", type=Path, default=HERE / "sources.json")
    args = parser.parse_args()
    build(args.output, args.sources)
