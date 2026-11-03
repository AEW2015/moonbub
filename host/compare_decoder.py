"""Independently measure RTL JPEG pixel output against two software decoders.

No tolerance is automatically turned into a functional PASS. Coverage and
orientation checks are reported separately from numerical decoder differences.
"""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image


def rgb565(rgb):
    rgb = np.asarray(rgb, dtype=np.uint16)
    return ((rgb[..., 0] >> 3) << 11) | ((rgb[..., 1] >> 2) << 5) | (rgb[..., 2] >> 3)


def expand565(words):
    r = (words >> 11) & 31
    g = (words >> 5) & 63
    b = words & 31
    return np.stack(((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2)), axis=-1).astype(np.int16)


def errors(actual, reference):
    error = actual.astype(np.int16) - reference.astype(np.int16)
    absolute = np.abs(error)
    mse = float(np.mean(error.astype(float) ** 2))
    return {"rgb8_mae": float(np.mean(absolute)), "rgb8_max_error": int(np.max(absolute)),
            "rgb8_channel_mae": np.mean(absolute, axis=(0, 1)).tolist(),
            "rgb8_channel_max": np.max(absolute, axis=(0, 1)).tolist(),
            "rgb8_error_percentiles": {str(p): float(np.percentile(absolute, p)) for p in (50, 90, 95, 99, 99.9)},
            "rgb8_psnr_db": None if mse == 0 else float(10 * np.log10(255 ** 2 / mse))}


def main():
    root = Path(__file__).resolve().parent.parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dump", type=Path, default=root / "fpga/sim/decoded-rgb565.txt")
    parser.add_argument("--jpeg", type=Path, default=root / "host/fixtures/pattern-720x480-420-q65.jpg")
    parser.add_argument("--c-model", type=Path, default=root / "host/evidence/pattern-c-model.ppm")
    parser.add_argument("--fixed-color-model", type=Path, default=root / "host/evidence/pattern-c-model-fixed-color.ppm")
    parser.add_argument("--require-fixed-exact", action="store_true", help="fail unless fixed-color C-model RGB565 is bit identical")
    parser.add_argument("--output", type=Path, default=root / "host/evidence/decoder-comparison.json")
    args = parser.parse_args()
    pillow = Image.open(args.jpeg).convert("RGB")
    width, height = pillow.size
    count = width * height
    values = np.zeros(count, dtype=np.uint16)
    seen = np.zeros(count, dtype=np.uint16)
    out_of_range = 0
    records = 0
    for line in args.dump.read_text().splitlines():
        index, word = line.split()
        index, word = int(index), int(word, 16)
        records += 1
        if not 0 <= index < count or not 0 <= word <= 0xffff:
            out_of_range += 1
            continue
        values[index] = word
        seen[index] += 1
    values = values.reshape(height, width)
    expanded = expand565(values)
    reference = expand565(rgb565(pillow))
    result = {"scope": "RTL decoded RGB565 dump, not SDRAM/display/hardware", "dimensions": [width, height],
              "coverage": {"records": records, "expected": count, "missing_pixels": int(np.sum(seen == 0)),
                           "duplicate_pixels": int(np.sum(seen > 1)), "out_of_range": out_of_range},
              "pillow_reference_rgb565": errors(expanded, reference),
              "orientation_mae": {"normal": float(np.mean(np.abs(expanded - reference))),
                                  "horizontal_flip": float(np.mean(np.abs(expanded[:, ::-1] - reference))),
                                  "vertical_flip": float(np.mean(np.abs(expanded[::-1] - reference))),
                                  "red_blue_swap": float(np.mean(np.abs(expanded[..., ::-1] - reference)))},
              "reference_limitations": "Pillow interpolates420 chroma; core uses nearest replication and different integer IDCT/color rounding. C model shares upstream algorithms and is not an independent JPEG implementation.",
              "files": {}}
    result["pillow_reference_rgb565"]["exact_pixels"] = int(np.sum(values == rgb565(pillow)))
    if args.c_model.exists():
        model = Image.open(args.c_model).convert("RGB")
        if model.size != pillow.size:
            raise ValueError("C-model dimensions mismatch")
        model_words = rgb565(model)
        result["upstream_c_model_rgb565"] = errors(expanded, expand565(model_words))
        result["upstream_c_model_rgb565"]["exact_pixels"] = int(np.sum(values == model_words))
        result["upstream_c_model_rgb565"]["per_channel_code_max_error"] = [
            int(np.max(np.abs(((values >> shift) & mask).astype(np.int16) - ((model_words >> shift) & mask).astype(np.int16))))
            for shift, mask in ((11, 31), (5, 63), (0, 31))]
        # Distinguish coefficient/color rounding near boundaries from damaged
        # spatial blocks using per8x8 maximum MAE, without loosening a test gate.
        pixel_error = np.mean(np.abs(expanded - expand565(model_words)), axis=2)
        result["upstream_c_model_rgb565"]["worst_8x8_block_mae"] = float(np.max(pixel_error.reshape(height // 8, 8, width // 8, 8).mean(axis=(1, 3))))
    draft = Image.open(args.jpeg)
    # Pillow10.4.0's JPEG decoder enables nearest upsampling/fast IDCT when
    # decoderconfig draft flag is1. draft() at full size leaves that flag0.
    draft.decoderconfig = (1, 1)
    result["pillow_fast_nearest_rgb565"] = errors(expanded, expand565(rgb565(draft.convert("RGB"))))
    result["coverage_pass"] = records == count and np.all(seen == 1).item() and out_of_range == 0
    scores = result["orientation_mae"]
    result["orientation_pass"] = scores["normal"] < min(scores[key] for key in scores if key != "normal")
    result["pixel_identity_pass"] = int(result.get("upstream_c_model_rgb565", {}).get("exact_pixels", 0)) == count
    if args.fixed_color_model.exists():
        model = Image.open(args.fixed_color_model).convert("RGB")
        if model.size != pillow.size:
            raise ValueError("fixed-color model dimensions mismatch")
        model_words = rgb565(model)
        result["fixed_color_c_model_rgb565"] = errors(expanded, expand565(model_words))
        result["fixed_color_c_model_rgb565"]["exact_pixels"] = int(np.sum(values == model_words))
        result["fixed_color_bitexact_pass"] = bool(np.array_equal(values, model_words))
    for path in (args.dump, args.jpeg, args.c_model, args.fixed_color_model):
        if path.exists():
            result["files"][str(path.relative_to(root))] = {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "bytes": path.stat().st_size}
    # PNG previews are derived by standard plotting/data conversion, not AI.
    Image.fromarray(expanded.astype(np.uint8)).save(args.output.parent / "rtl-decoded-preview.png")
    delta = np.abs(expanded - reference).clip(0, 255).astype(np.uint8)
    Image.fromarray(delta).save(args.output.parent / "rtl-versus-pillow-difference.png")
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if not result["coverage_pass"] or not result["orientation_pass"] or (args.require_fixed_exact and not result.get("fixed_color_bitexact_pass")):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
