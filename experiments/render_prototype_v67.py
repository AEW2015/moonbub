#!/usr/bin/env python3
"""Render measured, sampled rate/error points; never infer hardware FPS."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams["svg.hashsalt"] = "gamebub-v67"
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/figures/prototype-v67"
INPUTS = [
    "experiments/python-game-filter-frontier-v63-study/results.json",
    "experiments/python-game-filter-temporal-v62-study/results.json",
    "experiments/python-game-filter-frontier-v63-study/comparison.json",
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    native, custom, comparison = [json.loads((ROOT / p).read_text()) for p in INPUTS]
    scenes = list(dict.fromkeys(c["scene"] for c in native["cases"]))
    colors = {"libx265": "#167d9a", "libsvtav1": "#6a45a5"}
    markers = {"libx265": "o", "libsvtav1": "^"}
    plotted = []
    fig, axes = plt.subplots(2, 2, figsize=(10.8, 7.8), layout="constrained")
    for scene, ax in zip(scenes, axes.flat, strict=True):
        for c in native["cases"]:
            if c["scene"] != scene:
                continue
            s = next(p["summary"] for p in c["presets"] if p["preset"]["name"] == "strong")
            rate = s["complete_bytes"] * 8 * 30 / (s["frames"] * 1e6)
            mse = s["active_squared_error"] / s["active_channel_samples"]
            ax.scatter(rate, mse, c=colors[c["codec"]], marker=markers[c["codec"]],
                       alpha=.7, s=42, linewidth=.6)
            if s["cap_failures"]:
                ax.scatter(rate, mse, marker="x", c="black", s=65, linewidth=1.1)
            plotted.append(dict(scene=scene, kind=c["codec"], source=c["source"],
                                source_case=c["source_case"], complete_bytes=s["complete_bytes"],
                                frames=s["frames"], nominal_Mbps_at30=rate, active_MSE=mse,
                                cap_failures=s["cap_failures"]))
        for c in custom["cases"]:
            if c["scene"] != scene or c["kind"] != "custom":
                continue
            s = next(p["summary"] for p in c["presets"] if p["preset"]["name"] == "strong")
            rate = c["complete_bytes"] * 8 * 30 / (s["frames"] * 1e6)
            zero = c["policy"] == "zero"
            ax.scatter(rate, s["active_MSE"], c="black" if zero else "#d36b13",
                       marker="*" if zero else "D", s=160 if zero else 65, zorder=4)
            plotted.append(dict(scene=scene, kind=c["policy"], source=c["source"],
                                source_case=c["source_case"], complete_bytes=c["complete_bytes"],
                                frames=s["frames"], nominal_Mbps_at30=rate,
                                active_MSE=s["active_MSE"], cap_failures=c["cap_failures"]))
        ax.set_title(scene.replace("mass-effect-", "Mass Effect: "))
        ax.set_xlabel("Complete bytes expressed as Mbps at nominal 30 fps")
        ax.set_ylabel("Active RGB565 MSE (lower is better)")
        ax.grid(alpha=.22)
        ax.set_ylim(bottom=0)
    handles = [Line2D([], [], color=colors[k], marker=markers[k], linestyle="", label=l)
               for k, l in [("libx265", "HEVC / x265"), ("libsvtav1", "AV1 / SVT")]]
    handles += [Line2D([], [], color="black", marker="*", markersize=11, linestyle="", label="Custom zero motion"),
                Line2D([], [], color="#d36b13", marker="D", linestyle="", label="Custom mixed motion (quality trade)"),
                Line2D([], [], color="black", marker="x", linestyle="", label="At least one frame exceeds 49,152 B")]
    fig.suptitle("Same later source window, same fixed display filter\nSampled byte/error points; not an optimal encoder frontier", fontsize=14)
    fig.legend(handles=handles, loc="outside lower center", ncol=3, fontsize=9)
    fig.savefig(OUT / "sampled-rate-error.png", dpi=180, metadata={"Software": "Matplotlib; render_prototype_v67.py"})
    fig.savefig(OUT / "sampled-rate-error.svg", metadata={"Date": None})
    plt.close(fig)
    assert len(plotted) == 77
    assert all(p["frames"] == 24 for p in plotted)
    # A separate table reports the explicit mean-quality AND per-frame byte-cap gate.
    table = []
    for c in comparison["cases"]:
        if c["policy"] != "zero" or c["display_preset"] != "strong":
            continue
        for codec, p in c["best_sampled_native"]["mean"].items():
            table.append(dict(scene=c["scene"], codec=codec,
                              custom_complete_bytes=c["custom_complete_bytes"],
                              native_complete_bytes=p["complete_bytes"],
                              native_display_preset=p["display_preset"],
                              native_fewer_bytes_percent=100*(1-p["complete_bytes"]/c["custom_complete_bytes"])))
    evidence = {"schema": "gamebub-v67-figure-evidence", "inputs": {
        p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in INPUTS},
        "points": plotted, "mean_quality_cap_gated_table": table,
        "scope": ["Source IDs 24..47 in each of four related precompressed Mass Effect clips; 96 canvases.",
                  "All points use fixed strong display-only filtering. Table permits either fixed native display option, using explicit quality and cap gates.",
                  "Complete bytes include codec binding, exact HUD and codec extradata once; source metrics use original RGB565 active pixels.",
                  "The 30 fps conversion is a byte-rate normalization, not measured capture, ESP32, FPGA or display throughput.",
                  "Source lineage is shared; this is an additional temporal window, not an unseen game evaluation.",
                  "No new encodes; all 69 native points are reused from the fresh v61 sweeps."]}
    (OUT / "evidence.json").write_text(json.dumps(evidence, indent=2)+"\n")
    print(json.dumps({"plotted_points": len(plotted), "mean_gate_comparisons": len(table), "output": str(OUT)}))


if __name__ == "__main__":
    main()
