"""Audit available source windows for a predeclared 30 fps cohort study."""
from __future__ import annotations
import hashlib, importlib.util, json, platform, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
CORPUS_PATH = REPO / "experiments/python-codec-study/corpus.py"
MEDIA_DIR = REPO.parents[1] / "media"
FPS, FRAMES, WIDTH, HEIGHT = 30, 90, 720, 480

def load_corpus_module():
    spec = importlib.util.spec_from_file_location("sibling_codec_corpus", CORPUS_PATH)
    if spec is None or spec.loader is None: raise RuntimeError(f"cannot load {CORPUS_PATH}")
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); return module

def nonoverlap_max_frames(selected_times: Iterable[float | None], next_start: float) -> int:
    """Count observed frames strictly before next_start; never interpolate FPS."""
    if next_start < 0: raise ValueError("next_start must be nonnegative")
    times = list(selected_times)
    if any(t is None for t in times): raise ValueError("cannot determine overlap when a selected frame lacks PTS")
    return sum(float(t) < next_start for t in times)

def compare_shared_pts_hashes(primary_pts, primary_hashes, heldout_pts, heldout_hashes):
    """Compare rendered hashes for every shared source PTS, including repeats."""
    if len(primary_pts) != len(primary_hashes) or len(heldout_pts) != len(heldout_hashes):
        raise ValueError("PTS and image-hash lists must have matching lengths")
    primary = dict(zip(primary_pts, primary_hashes))
    heldout = dict(zip(heldout_pts, heldout_hashes))
    shared = sorted(set(primary) & set(heldout))
    mismatches = [pts for pts in shared if primary[pts] != heldout[pts]]
    return {"shared_pts": shared, "shared_pts_count": len(shared),
            "mismatch_pts": mismatches, "mismatch_count": len(mismatches)}

def covered_metric_window(values: list, required_count: int):
    """Return values only when a complete predeclared window is present."""
    if required_count < 0: raise ValueError("required_count must be nonnegative")
    return values[:required_count] if len(values) >= required_count else None

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): digest.update(block)
    return digest.hexdigest()

def audit_window(corpus, clip: str, role: str, start: float) -> dict:
    path = MEDIA_DIR / clip
    frames, m = corpus.load_video(path, FRAMES, start, WIDTH, HEIGHT)
    times = m["selected_times_seconds"]
    result = {
        "clip": clip, "role": role, "start_seconds": start, "requested_frames": FRAMES,
        "source_path_basename": path.name, "source_sha256": m["source_sha256"],
        "source_pts_time_base": m["time_base"], "source_native_fps": m["source_fps"],
        "target_size": [WIDTH, HEIGHT], "actual_frame_count": m["frame_count"],
        "unique_image_hash_count": m["unique_frame_count"], "image_sha256": m["frame_sha256"],
        "selected_pts": m["selected_pts"], "selected_times_seconds": times,
        "first_selected_pts_seconds": next((t for t in times if t is not None), None),
        "last_selected_pts_seconds": None,
        "source_pts_span_seconds": (times[-1] - times[0] if times and times[0] is not None and times[-1] is not None else None),
        "nominal_30fps_scheduled_duration_seconds": FRAMES / FPS,
        "nominal_30fps_schedule_end_seconds": start + FRAMES / FPS,
        "covered_90_frame_metric_window": covered_metric_window(m["frame_sha256"], FRAMES) is not None,
    }
    result["last_selected_pts_seconds"] = next((t for t in reversed(times) if t is not None), None)
    del frames
    return result

def run_audit() -> dict:
    corpus = load_corpus_module()
    specs = [(clip, role, start) for clip in ("mass-effect-combat.mp4", "mass-effect-2600.mp4") for role, start in (("primary", 1.0), ("heldout", 4.0))]
    windows = [audit_window(corpus, *spec) for spec in specs]
    by_clip = {}
    for w in windows: by_clip.setdefault(w["clip"], {})[w["role"]] = w
    overlaps = []
    for clip, roles in by_clip.items():
        p, h = roles["primary"], roles["heldout"]
        exact_match = compare_shared_pts_hashes(p["selected_pts"], p["image_sha256"],
                                                h["selected_pts"], h["image_sha256"])
        shared = exact_match["shared_pts"]
        max_primary = nonoverlap_max_frames(p["selected_times_seconds"], h["start_seconds"])
        overlaps.append({"clip": clip, "primary_heldout_shared_exact_pts_count": len(shared),
            "primary_heldout_shared_exact_pts": shared,
            "shared_pts_rendered_hash_mismatch_count": exact_match["mismatch_count"],
            "shared_pts_rendered_hash_mismatch_pts": exact_match["mismatch_pts"],
            "shared_pts_all_rendered_hashes_match": exact_match["mismatch_count"] == 0,
            "shared_image_hash_distinct_value_count": len(set(p["image_sha256"]) & set(h["image_sha256"])),
            "primary_frames_before_heldout_start_max": max_primary,
            "primary_requested_frames_overlap_heldout": max_primary < p["actual_frame_count"],
            "recommendation": f"use at most {max_primary} observed primary frames before held-out start, or choose separate corpus windows"})
    import numpy, PIL, av
    return {"evidence": "source availability and native decoded PTS audit; no codec, receiver, or hardware performance claim",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "pinned_versions": {"python": platform.python_version(), "numpy": numpy.__version__, "pillow": PIL.__version__, "pyav": av.__version__,
            "corpus_helper": "sibling experiments/python-codec-study/corpus.py", "corpus_helper_sha256": sha256_file(CORPUS_PATH),
            "audit_source_sha256": sha256_file(HERE / "audit.py")},
        "windows": windows, "overlap_analysis": overlaps,
        "warning": "At 25 fps, 90 native frames span about 3.56 seconds from first to last PTS; a 90-slot 30 fps schedule lasts 3.0 seconds. A start=1 window can extend beyond heldout start=4. Treat overlapping windows as non-independent heldout data."}

def main():
    output = HERE / "audit.json"; result = run_audit(); output.write_text(json.dumps(result, indent=2) + "\n")
    lines = [f"python {sys.version.split()[0]}", f"audit output {output.name}"]
    for w in result["windows"]: lines.append(f"{w['clip']} {w['role']} start={w['start_seconds']} requested={w['requested_frames']} actual={w['actual_frame_count']} unique={w['unique_image_hash_count']} native_fps={w['source_native_fps']}")
    for o in result["overlap_analysis"]: lines.append(f"{o['clip']} shared_pts={o['primary_heldout_shared_exact_pts_count']} shared_pts_hash_mismatches={o['shared_pts_rendered_hash_mismatch_count']} max_primary_before_heldout={o['primary_frames_before_heldout_start_max']} overlapping={o['primary_requested_frames_overlap_heldout']}")
    (HERE / "run.log").write_text("\n".join(lines) + "\n"); print("\n".join(lines))
if __name__ == "__main__": main()
