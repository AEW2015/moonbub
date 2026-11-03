"""Arithmetic/capacity scenarios, not a codec, FPGA fit, or timing model.

All bandwidth is decimal bytes/s. Memory allocation is in bytes; MiB is 2**20.
No external packages, RTL execution, hardware access, or network access.
"""
from dataclasses import asdict, dataclass
from math import ceil, isfinite
import json


@dataclass(frozen=True)
class Scenario:
    width: int = 720
    height: int = 480
    display_width: int = 720
    display_height: int = 480
    decode_fps: float = 30
    display_hz: float = 60
    bus_mhz: float = 100
    bus_bits: int = 16
    efficiency: float = 0.6
    references_stored: int = 1
    prediction_sources: int = 1
    predicted_fraction: float = 1
    luma_block: int = 16
    luma_taps: int = 8
    chroma_taps: int = 4
    compressed_mbps: float = 8
    compressed_sdram_passes: int = 2  # staging write and read
    full_yuv_filter_passes: int = 0  # each pass reads and writes whole YUV
    separate_color_conversion: bool = True

    def __post_init__(self):
        if type(self.separate_color_conversion) is not bool:
            raise ValueError("separate_color_conversion must be a boolean")
        for name in ("width", "height", "display_width", "display_height", "bus_bits", "luma_block", "luma_taps", "chroma_taps"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.width % 2 or self.height % 2 or self.luma_block % 2:
            raise ValueError("4:2:0 requires even dimensions and an even luma block")
        if self.bus_bits % 8:
            raise ValueError("bus_bits must be a multiple of eight")
        for name in ("references_stored", "prediction_sources", "compressed_sdram_passes", "full_yuv_filter_passes"):
            if type(getattr(self, name)) is not int or getattr(self, name) < 0:
                raise ValueError(f"{name} must be a nonnegative integer")
        if self.prediction_sources > self.references_stored:
            raise ValueError("simultaneous prediction sources exceed stored references")
        for name in ("decode_fps", "display_hz", "bus_mhz"):
            if not isfinite(getattr(self, name)) or getattr(self, name) <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if not isfinite(self.efficiency) or not 0 < self.efficiency <= 1:
            raise ValueError("efficiency must lie in (0, 1]")
        if not isfinite(self.predicted_fraction) or not 0 <= self.predicted_fraction <= 1:
            raise ValueError("predicted_fraction must lie in [0, 1]")
        if not isfinite(self.compressed_mbps) or self.compressed_mbps < 0:
            raise ValueError("compressed_mbps must be finite and nonnegative")


def plane_fetch_samples(width, height, block, taps):
    """Independent blocks with taps-1 total halo in each dimension.

    Fetch every halo sample, including replicated edges; no inter-block cache,
    burst/row alignment, scaling, warp, or duplicate elimination. Partial blocks
    use their actual output dimensions. This is an illustrative access pattern,
    neither a universal upper nor lower bound for either standard.
    """
    return sum((min(block, width - x) + taps - 1)
               * (min(block, height - y) + taps - 1)
               for y in range(0, height, block)
               for x in range(0, width, block))


def evaluate(s):
    pixels = s.width * s.height
    yuv = pixels * 3 // 2  # tightly packed 8-bit planar 4:2:0
    # Display-sized RGB output; coded video may be scaled to fill/fit this.
    # Scaling arithmetic/cache traffic beyond one coded-YUV read is unmodeled.
    rgb = s.display_width * s.display_height * 2
    halo = plane_fetch_samples(s.width, s.height, s.luma_block, s.luma_taps)
    halo += 2 * plane_fetch_samples(s.width // 2, s.height // 2,
                                    s.luma_block // 2, s.chroma_taps)
    traffic = {
        "display_rgb565_read": rgb * s.display_hz,
        "reconstruction_yuv_write": yuv * s.decode_fps,
        "display_rgb565_write": rgb * s.decode_fps,
        "color_conversion_yuv_read": yuv * s.decode_fps if s.separate_color_conversion else 0,
        "reference_no_halo_read": yuv * s.decode_fps * s.predicted_fraction * s.prediction_sources,
        "compressed_staging": s.compressed_mbps * 1e6 / 8 * s.compressed_sdram_passes,
        "filter_read_write": 2 * yuv * s.decode_fps * s.full_yuv_filter_passes,
    }
    total = sum(traffic.values())
    halo_extra = ((halo - yuv) * s.decode_fps * s.predicted_fraction * s.prediction_sources)
    available = s.bus_mhz * 1e6 * (s.bus_bits // 8) * s.efficiency
    return {
        "inputs": asdict(s),
        "pixels": pixels,
        "display_pixels": s.display_width * s.display_height,
        "yuv420_frame_bytes": yuv,
        "rgb565_frame_bytes": rgb,
        "frame_allocation_bytes": (s.references_stored + 1) * yuv + 2 * rgb,
        "sram_yuv_spare_bytes": 512 * 1024 - yuv,
        "traffic_bytes_s": traffic,
        "halo_fetch_samples_per_predicted_frame_per_source": halo,
        "halo_amplification": halo / yuv,
        "total_no_halo_bytes_s": total,
        "total_independent_halo_bytes_s": total + halo_extra,
        "assumed_available_bytes_s": available,
        "average_slack_no_halo_bytes_s": available - total,
        "average_slack_independent_halo_bytes_s": available - total - halo_extra,
    }


def transform_budget(n, width=720, height=480, fps=30, mhz=150, mac_lanes=8):
    """Dense separable NxN two-pass matrix transform: 2*N**3 MAC/block.

    Round each plane up to complete blocks (padding counted). This counts a
    naive all-nonzero transform, not codec butterflies, zeros, rounding,
    coefficient parsing, DSP mappings, or pipeline utilization. One abstract
    lane does one counted MAC/clock; this does not equate lanes to DSP blocks.
    """
    if type(n) is not int or n <= 0 or n & (n - 1):
        raise ValueError("n must be a positive power of two")
    if width <= 0 or height <= 0 or width % 2 or height % 2 or fps <= 0 or mhz <= 0 or mac_lanes <= 0:
        raise ValueError("positive even dimensions and positive rates/lanes required")
    blocks = ceil(width / n) * ceil(height / n)
    blocks += 2 * ceil((width // 2) / n) * ceil((height // 2) / n)
    mac_frame = blocks * 2 * n**3
    rate = mac_frame * fps
    return {"n": n, "padded_blocks": blocks, "mac_per_frame": mac_frame,
            "mac_per_second": rate, "mac_lanes": mac_lanes, "mhz": mhz,
            "ideal_lane_utilization": rate / (mac_lanes * mhz * 1e6)}


def resource_inventory():
    # Retained routed JPEG baseline, not a future codec's fixed overhead.
    return {"device": "xc7a100tcsg324-1", "lut_total": 63400, "lut_used": 7362,
            "lut_arithmetic_remaining": 56038, "dsp_total": 240, "dsp_used": 32,
            "dsp_arithmetic_remaining": 208, "bram36_tiles_total": 135,
            "bram36_tiles_used": 120.5, "bram36_tiles_arithmetic_remaining": 14.5,
            "bram_nominal_bits_total": 135 * 36864,
            "bram_nominal_bits_arithmetic_remaining": int(14.5 * 36864),
            "uram_total": 0}


def study():
    def scenario(**kwargs):
        return evaluate(Scenario(**kwargs))
    profiles = [(720, 480, 30), (512, 288, 30), (512, 288, 20),
                (480, 270, 30), (480, 270, 20), (320, 180, 30)]
    reduced = []
    for width, height, fps in profiles:
        row = scenario(width=width, height=height, decode_fps=fps)
        row["cycles_per_coded_luma_pixel_at_150mhz"] = 150e6 / (width * height * fps)
        row["dense_8x8_transform"] = transform_budget(8, width=width, height=height, fps=fps)
        row["capacity_by_references"] = [
            {"references_stored": count, "frame_allocation_bytes":
             (count + 1) * row["yuv420_frame_bytes"] + 2 * row["rgb565_frame_bytes"]}
            for count in (1, 2, 4, 8)]
        reduced.append(row)
    return {
        "kind": "unmeasured_parameter_model_not_resource_fit_or_deadline_proof",
        "resource_inventory": resource_inventory(),
        "capacity_reference_sweep": [scenario(references_stored=r) for r in (1, 2, 4, 8)],
        "shared_sdram_efficiency_sweep": [scenario(efficiency=e) for e in (0.3, 0.4, 0.6, 0.8)],
        "halo_block_sweep": [scenario(luma_block=b) for b in (8, 16, 32, 64)],
        "fused_color_output": scenario(separate_color_conversion=False),
        "compound_two_source": scenario(references_stored=2, prediction_sources=2),
        "three_full_frame_filter_passes": scenario(full_yuv_filter_passes=3),
        "intra_only": scenario(references_stored=0, prediction_sources=0),
        "reduced_coded_resolution_fps_sweep": reduced,
        "alternate_800x480_display": scenario(width=512, height=288, display_width=800),
        "cycles_per_luma_pixel": [
            {"mhz": mhz, "cycles_at_30fps": mhz * 1e6 / (720 * 480 * 30),
             "cycles_at_60fps": mhz * 1e6 / (720 * 480 * 60)}
            for mhz in (100, 150, 200)],
        "dense_transform_sweep": [transform_budget(n) for n in (4, 8, 16, 32, 64)],
    }


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario-json", type=Path,
                        help="evaluate Scenario fields from a JSON object instead of the default sweep")
    args = parser.parse_args()
    result = evaluate(Scenario(**json.loads(args.scenario_json.read_text()))) if args.scenario_json else study()
    print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
