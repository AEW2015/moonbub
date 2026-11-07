#!/usr/bin/env python3
"""Prepare deterministic common RGB inputs for the Gamebub V98 comparison.

Game sources are decoded at their native timestamps. No frame-rate conversion,
interpolation, or duplicate-frame scheduling is performed. The generated
synthetic clip is a separate, explicitly synthetic 30 fps fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from fractions import Fraction
from pathlib import Path
from typing import Any

import av
import numpy as np
import PIL
from PIL import Image, ImageDraw, ImageFont


HERE = Path(__file__).resolve().parent
DEFAULT_MEDIA = HERE.parents[3] / "media"
OUTPUT = HERE / "sources"
WIDTH, HEIGHT = 720, 480
FRAME_COUNT = 30


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def frame_hash(rgb: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(rgb).tobytes()).hexdigest()


def letterbox(rgb: np.ndarray) -> tuple[np.ndarray, tuple[int, int, int, int]]:
    h, w = rgb.shape[:2]
    scale = min(WIDTH / w, HEIGHT / h)
    out_w = max(1, min(WIDTH, round(w * scale)))
    out_h = max(1, min(HEIGHT, round(h * scale)))
    resized = Image.fromarray(rgb, "RGB").resize((out_w, out_h), Image.Resampling.BOX)
    x, y = (WIDTH - out_w) // 2, (HEIGHT - out_h) // 2
    canvas = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    canvas[y:y + out_h, x:x + out_w] = np.asarray(resized)
    return canvas, (x, y, out_w, out_h)


def extract_game(clip_id: str, source: Path, start_seconds: str = "1",
                 decimation: int = 1) -> tuple[np.ndarray, dict[str, Any]]:
    if decimation <= 0:
        raise ValueError("decimation must be positive")
    frames: list[np.ndarray] = []
    stamps: list[dict[str, Any]] = []
    active_rects: list[list[int]] = []
    with av.open(str(source)) as container:
        stream = next((item for item in container.streams if item.type == "video"), None)
        if stream is None:
            raise ValueError(f"No video stream in {source}")
        source_fps = str(stream.average_rate) if stream.average_rate is not None else None
        reported_frames = int(stream.frames) if stream.frames else None
        stream_tb = Fraction(stream.time_base) if stream.time_base is not None else None
        stream_duration = (Fraction(stream.duration) * stream_tb
                           if stream.duration is not None and stream_tb is not None else None)
        start_time = Fraction(start_seconds)
        eligible_index = 0
        for decoded in container.decode(stream):
            if decoded.pts is None or decoded.time_base is None:
                raise ValueError(f"Frame without native PTS/time_base in {source}")
            tb = Fraction(decoded.time_base)
            timestamp = Fraction(decoded.pts) * tb
            if timestamp < start_time:
                continue
            if eligible_index % decimation:
                eligible_index += 1
                continue
            eligible_index += 1
            fitted, rect = letterbox(decoded.to_ndarray(format="rgb24"))
            frames.append(fitted)
            active_rects.append(list(rect))
            stamps.append({
                "pts": int(decoded.pts),
                "time_base": f"{tb.numerator}/{tb.denominator}",
                "seconds": f"{timestamp.numerator}/{timestamp.denominator}",
            })
            if len(frames) == FRAME_COUNT:
                break
    if len(frames) != FRAME_COUNT:
        raise ValueError(f"{source} yielded only {len(frames)} frames at/after 1 second")
    rgb = np.stack(frames).astype(np.uint8, copy=False)
    # Verify aspect-fit output geometry remains consistent across selected frames.
    if any(rect != active_rects[0] for rect in active_rects):
        raise ValueError(f"Source dimensions changed within selected segment: {source}")
    selected_fps_fraction = Fraction(source_fps) / decimation if source_fps else None
    selected_fps = (f"{selected_fps_fraction.numerator}/{selected_fps_fraction.denominator}"
                    if selected_fps_fraction is not None else None)
    data = {
        "clip_id": clip_id,
        "kind": "game_video_source",
        "raw_capture": False,
        "quality_scope": "decoded_source_video; not a raw gameplay capture",
        "source": str(source),
        "source_sha256": sha256_file(source),
        "source_width": int(stream.codec_context.width),
        "source_height": int(stream.codec_context.height),
        "source_codec": stream.codec_context.name,
        "source_fps": source_fps,
        "stream_time_base": (f"{stream_tb.numerator}/{stream_tb.denominator}" if stream_tb else None),
        "source_duration_seconds": (f"{stream_duration.numerator}/{stream_duration.denominator}"
                                     if stream_duration is not None else None),
        "source_frame_count_reported": reported_frames,
        "source_metadata": {
            "path": str(source),
            "sha256": sha256_file(source),
            "width": int(stream.codec_context.width),
            "height": int(stream.codec_context.height),
            "codec": stream.codec_context.name,
            "source_fps": source_fps,
            "selected_fps": selected_fps,
            "selection_decimation": decimation,
            "stream_time_base": (f"{stream_tb.numerator}/{stream_tb.denominator}" if stream_tb else None),
            "duration_seconds": (f"{stream_duration.numerator}/{stream_duration.denominator}"
                                 if stream_duration is not None else None),
            "frame_count_reported": reported_frames,
        },
        "selection": (f"first 30 decoded frames with native PTS timestamp >= {start_seconds} seconds; "
                      f"select every {decimation} decoded frame(s)"),
        "start_seconds": start_seconds,
        "selection_decimation": decimation,
        "frame_rate_conversion": ("decimation only, no interpolation or duplication"
                                  if decimation > 1 else "none; native decoded sequence"),
        "selected_fps": selected_fps,
        "resampler": "Pillow BOX",
        "active_rect": active_rects[0],
        "roi": {
            "type": "generic_visual_interest_region",
            "rectangles": [[16, 48, 192, 80], [160, 352, 400, 80]],
            "verified_hud_semantics": False,
            "note": "Generic geometric probes only; HUD semantics and gameplay meaning are not verified.",
        },
        "timestamps": stamps,
    }
    return rgb, data


def synthetic_frame(index: int) -> np.ndarray:
    """Create a fully deterministic, original motion/text/HUD fixture frame."""
    yy, xx = np.mgrid[0:HEIGHT, 0:WIDTH]
    if index < 15:
        # Changing blue/teal scene with broad gradients and a moving checker field.
        phase = index
        image = np.stack((
            (22 + xx // 12 + phase * 2) % 100,
            (45 + yy // 5 + phase * 3) % 150,
            (90 + (xx // 16 + yy // 12 + phase) % 80),
        ), axis=-1).astype(np.uint8)
        image[((xx + phase * 13) // 24 + (yy // 18)) % 2 == 0] = np.minimum(
            image[((xx + phase * 13) // 24 + (yy // 18)) % 2 == 0].astype(np.uint16) + 18, 255
        ).astype(np.uint8)
        base = Image.fromarray(image, "RGB")
        draw = ImageDraw.Draw(base)
        # Moving foreground object and horizon provide temporal motion.
        x = 70 + (index * 17) % 520
        y = 155 + (index * 5) % 80
        draw.ellipse((x, y, x + 74, y + 54), fill=(232, 154, 72), outline=(255, 232, 176), width=3)
        draw.rectangle((0, 340 + (index % 3) * 4, WIDTH, HEIGHT), fill=(24, 36, 43))
        scene_label = "ORIGINAL SIMULATION / ZONE A"
        accent = (64, 218, 181)
    else:
        # Hard scene cut at frame 15; distinct warm scene and a second moving object.
        image = np.stack((
            np.clip(100 + xx // 5 + (yy // 8), 0, 255),
            (28 + xx // 22 + yy // 20) % 90,
            (35 + yy // 7 + (xx // 25)) % 110,
        ), axis=-1).astype(np.uint8)
        base = Image.fromarray(image, "RGB")
        draw = ImageDraw.Draw(base)
        x = 80 + ((index - 15) * 23) % 500
        y = 175 + ((index - 15) * 9) % 70
        draw.polygon(((x, y + 36), (x + 48, y), (x + 96, y + 36), (x + 48, y + 68)),
                     fill=(74, 212, 247), outline=(220, 250, 255))
        draw.rectangle((0, 342, WIDTH, HEIGHT), fill=(54, 22, 25))
        scene_label = "ORIGINAL SIMULATION / ZONE B"
        accent = (255, 186, 60)

    draw = ImageDraw.Draw(base)
    font = ImageFont.load_default()
    # Explicit synthetic HUD regions: top-left status panel and lower-right meter.
    draw.rounded_rectangle((18, 16, 282, 86), radius=8, fill=(8, 14, 24), outline=accent, width=2)
    draw.text((30, 26), scene_label, font=font, fill=(241, 246, 250))
    draw.text((30, 50), f"FRAME {index:02d}   SIGNAL {((index * 7) % 100):02d}%", font=font, fill=accent)
    draw.rounded_rectangle((552, 414, 704, 463), radius=6, fill=(8, 14, 24), outline=accent, width=2)
    draw.text((564, 423), "SYNC", font=font, fill=(240, 244, 248))
    bar_width = 72 + ((index * 11) % 48)
    draw.rectangle((612, 441, min(692, 612 + bar_width), 450), fill=accent)
    # Small persistent reticle makes spatial alignment easy to inspect.
    cx, cy = 360 + ((index * 9) % 31) - 15, 237 + ((index * 4) % 19) - 9
    draw.line((cx - 13, cy, cx + 13, cy), fill=(245, 245, 238), width=2)
    draw.line((cx, cy - 13, cx, cy + 13), fill=(245, 245, 238), width=2)
    return np.asarray(base, dtype=np.uint8)


def add_clip_manifest(rgb: np.ndarray, metadata: dict[str, Any], filename: str) -> dict[str, Any]:
    output_path = OUTPUT / filename
    np.savez_compressed(output_path, rgb=rgb)
    metadata.update({
        "npz_path": filename,
        "npz_sha256": sha256_file(output_path),
        "rgb_key": "rgb",
        "dtype": "uint8",
        "shape": list(rgb.shape),
        "frame_count": int(rgb.shape[0]),
        "frame_sha256": [frame_hash(frame) for frame in rgb],
        "unique_rgb_count": len({frame_hash(frame) for frame in rgb}),
    })
    return metadata


def prepare(media_dir: Path, user_source: Path | None = None) -> dict[str, Any]:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    clips: list[dict[str, Any]] = []
    for clip_id, filename in (("mass-effect-2600", "mass-effect-2600.mp4"),
                              ("mass-effect-combat", "mass-effect-combat.mp4")):
        rgb, metadata = extract_game(clip_id, media_dir / filename, "1")
        clips.append(add_clip_manifest(rgb, metadata, f"{clip_id}.npz"))

    if user_source is not None:
        rgb, metadata = extract_game("mass-effect-legendary-combat-20s", user_source, "20", 2)
        metadata["provenance"] = "User-supplied local source video; decoded source video, not a raw gameplay capture."
        clips.append(add_clip_manifest(rgb, metadata, "mass-effect-legendary-combat-20s.npz"))

    synthetic = np.stack([synthetic_frame(i) for i in range(FRAME_COUNT)]).astype(np.uint8, copy=False)
    synthetic_data: dict[str, Any] = {
        "clip_id": "synthetic-motion-hud-cut",
        "kind": "synthetic_original_fixture",
        "raw_capture": False,
        "quality_scope": "synthetic_only",
        "provenance": "Generated locally by source_prepare.py; not a captured game/video source.",
        "generator": "deterministic NumPy/Pillow drawing; Pillow default bitmap font",
        "frame_rate": "30/1",
        "source_metadata": {"source_type": "synthetic", "source_fps": "30/1"},
        "frame_rate_conversion": False,
        "timestamps": [{"pts": i, "time_base": "1/30", "seconds": f"{i}/30"}
                       for i in range(FRAME_COUNT)],
        "scene_cut": {"frame_index": 15, "from": "zone A", "to": "zone B"},
        "active_rect": [0, 0, WIDTH, HEIGHT],
        "roi": {
            "type": "synthetic_hud_rectangles",
            "rectangles": [
                {"name": "status_panel", "rect": [18, 16, 264, 70]},
                {"name": "sync_meter", "rect": [552, 414, 152, 49]},
                {"name": "reticle_region", "rect": [329, 213, 62, 48]},
            ],
            "verified_hud_semantics": True,
            "note": "Rectangles label elements explicitly drawn by this synthetic generator.",
        },
    }
    clips.append(add_clip_manifest(synthetic, synthetic_data, "synthetic-motion-hud-cut.npz"))

    script = Path(__file__).resolve()
    manifest = {
        "schema_version": 1,
        "corpus_id": "gamebub-v98-common-inputs-720x480",
        "description": "Common 30-frame RGB inputs for comparing Gamebub V98 encoders.",
        "canvas": {"width": WIDTH, "height": HEIGHT, "channels": "RGB"},
        "array_contract": "Each NPZ contains only key rgb: uint8[N,480,720,3].",
        "preparation": {
            "script": script.name,
            "script_sha256": sha256_file(script),
            "python": platform.python_version(),
            "pyav": av.__version__,
            "ffmpeg_libraries": {key: str(value) for key, value in av.library_versions.items()},
            "numpy": np.__version__,
            "pillow": PIL.__version__,
        },
        "clips": clips,
    }
    manifest_path = OUTPUT / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--media-dir", type=Path, default=DEFAULT_MEDIA,
                        help="directory containing mass-effect-2600.mp4 and mass-effect-combat.mp4")
    parser.add_argument("--user-source", type=Path,
                        help="optional user-supplied game video; adds a 30-frame segment starting at native PTS >= 20 seconds")
    args = parser.parse_args()
    manifest = prepare(args.media_dir, args.user_source)
    print(json.dumps({"manifest": str(OUTPUT / "manifest.json"),
                      "clips": [{"clip_id": c["clip_id"], "frames": c["frame_count"],
                                 "unique_rgb_count": c["unique_rgb_count"], "npz": c["npz_path"]}
                                for c in manifest["clips"]]}, indent=2))


if __name__ == "__main__":
    main()
