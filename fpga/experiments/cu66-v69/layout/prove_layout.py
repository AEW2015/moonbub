#!/usr/bin/env python3
"""Prove CU66 sample coordinates against existing Rev4 portrait scanout RTL."""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPO = ROOT
NATIVE = ROOT / 'experiments/cu66-native-v69'
V66 = ROOT / 'experiments/python-game-canonical-tag-v66-study'
V67_FILTER = ROOT / 'experiments/python-game-filter-qual-v67-study'
PLANES = (
    ('Y', 720, 480),
    ('Cb', 360, 240),
    ('Cr', 360, 240),
)
LAYOUTS = ('canonical_row_major', 'plane_transposed',
           'tile_major_coded', 'tile_major_physical_scan')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha_bytes(path.read_bytes())


def expand_rgb565(words):
    words = np.asarray(words, dtype=np.uint16)
    r, g, b = (words >> 11) & 31, (words >> 5) & 63, words & 31
    return np.stack(((r << 3) | (r >> 2), (g << 2) | (g >> 4),
                     (b << 3) | (b >> 2)), axis=2)


def physical_stream(words):
    if words.shape != (480, 720) or words.dtype != np.uint16:
        raise ValueError('expected coded RGB565 shape [480,720]')
    physical = np.zeros((800, 480), dtype=np.uint16)
    physical[40:760, :] = words.T
    # Check every physical active coordinate and both 40-line black bars.
    coded_seen = 0
    for py in range(800):
        for px in range(480):
            coded = layout.physical_to_coded(px, py)
            actual = int(physical[py, px])
            if coded is None:
                assert actual == 0
            else:
                u, v = coded
                assert layout.coded_to_physical(u, v) == (px, py)
                assert actual == int(words[v, u])
                coded_seen += 1
    assert coded_seen == 720 * 480
    return physical


def trace(layout_name, width, height, order):
    for u, v in order:
        yield layout.storage_index(layout_name, u, v, width, height)


def main():
    global layout
    layout = module('cu66_v69_layout_math', HERE / 'layout.py')
    helper = module('cu66_layout_v66_helpers', V66 / 'helpers.py')
    old_helpers = sys.modules.get('helpers')
    try:
        sys.modules['helpers'] = helper
        rxmod = module('cu66_layout_v66_receiver', V66 / 'receiver.py')
    finally:
        if old_helpers is None:
            sys.modules.pop('helpers', None)
        else:
            sys.modules['helpers'] = old_helpers

    filter_verify = module('cu66_layout_filter_v67_verify', V67_FILTER / 'verify.py')
    oracle = filter_verify.oracle
    oracle.check_calibration()
    mask = np.repeat(np.repeat(oracle.f.f.safe_blocks()[0], 8, axis=0), 8, axis=1)
    assert mask.shape == (480, 720) and int(mask.sum()) == 16384

    manifest = json.loads((NATIVE / 'manifest.json').read_text())
    case = manifest['cases'][0]
    row = case['rows'][0]
    assert row['id'] == 0 and row['key']
    packet_path = NATIVE / row['packet']['path']
    packet = packet_path.read_bytes()
    assert sha_bytes(packet) == row['packet']['sha256']
    receiver = rxmod.Receiver(profile='CU66')
    planes, patches, meta, _ = receiver.receive(packet)
    assert meta['frame_id'] == 0 and meta['key'] and meta['reference_id'] == 0xFFFFFFFF
    assert [tuple(p.shape) for p in planes] == [(480, 720), (240, 360), (240, 360)]
    canonical = b''.join(p.astype(np.uint8).tobytes() for p in planes)
    hud = b''.join(p['words'].astype('<u2').tobytes() for p in patches)
    assert sha_bytes(canonical) == row['canonical_yuv_u8_sha256']
    assert sha_bytes(hud) == row['hud_words_u16le_sha256']
    assert meta['output_tag'].hex() == row['canonical_tag']

    color = helper.m.C.corpus.rgb565(helper.m.ft.planes_to_rgb(planes)).astype(np.uint16)
    identity_display = helper.f.f.n.overlay(color, tuple(p['words'] for p in patches)).astype(np.uint16)
    assert sha_bytes(identity_display.astype('<u2').tobytes()) == row['display_rgb565_u16le_sha256']
    filtered_y, filter_work = oracle.oracle_filter(planes[0].astype(np.uint8), mask,
                                                   oracle.STRONG)
    strong_color = helper.m.C.corpus.rgb565(
        helper.m.ft.planes_to_rgb((filtered_y, planes[1], planes[2]))).astype(np.uint16)
    strong_display = helper.f.f.n.overlay(
        strong_color, tuple(p['words'] for p in patches)).astype(np.uint16)
    rects = helper.f.f.n.RECTS
    assert len(rects) == len(patches)
    for patch, (x, y, w, h) in zip(patches, rects, strict=True):
        np.testing.assert_array_equal(strong_display[y:y + h, x:x + w], patch['words'])

    physical_identity = physical_stream(identity_display)
    physical_strong = physical_stream(strong_display)
    physical_bar_bytes = 40 * 480 * 2 * 2
    assert physical_bar_bytes == 76800  # bytes in the two RGB565 physical black bars
    stream_identity = physical_identity.astype('<u2').tobytes()
    stream_strong = physical_strong.astype('<u2').tobytes()
    (HERE / 'physical-rgb565-identity.u16le').write_bytes(stream_identity)
    (HERE / 'physical-rgb565-strong-filter.u16le').write_bytes(stream_strong)

    addresses = {}
    totals = {}
    for name, width, height in PLANES:
        plane_entries = {}
        n = width * height
        for layout_name in LAYOUTS:
            write = layout.trace_metrics(trace(layout_name, width, height,
                                               layout.coded_block_order(width, height)), n)
            read = layout.trace_metrics(trace(layout_name, width, height,
                                              layout.physical_scan_order(width, height)), n)
            plane_entries[layout_name] = {'block_writer_order': write,
                                          'unique_physical_scan_order': read}
        addresses[name] = plane_entries

    raw_bytes = sum(w * h for _, w, h in PLANES)
    assert raw_bytes == 518400
    addressed_files = {
        'fpga/experiments/cu66-v69/layout/layout.py': HERE / 'layout.py',
        'fpga/experiments/cu66-v69/layout/prove_layout.py': HERE / 'prove_layout.py',
        'fpga/experiments/cu66-v69/layout/README.md': HERE / 'README.md',
        'fpga/rtl/moonshine_core.sv': ROOT / 'fpga/rtl/moonshine_core.sv',
        'fpga/rtl/moonshine_memory.sv': ROOT / 'fpga/rtl/moonshine_memory.sv',
        'fpga/rtl/moonshine_sdram.sv': ROOT / 'fpga/rtl/moonshine_sdram.sv',
        'fpga/rtl/moonshine_lcd.sv': ROOT / 'fpga/rtl/moonshine_lcd.sv',
        'fpga/sim/moonshine_lcd_tb.sv': ROOT / 'fpga/sim/moonshine_lcd_tb.sv',
        'fpga/README.md': ROOT / 'fpga/README.md',
        'fpga/PROTOCOL.md': ROOT / 'fpga/PROTOCOL.md',
        'experiments/cu66-native-v69/manifest.json': NATIVE / 'manifest.json',
        'experiments/python-game-canonical-tag-v66-study/protocol.py': V66 / 'protocol.py',
        'experiments/python-game-canonical-tag-v66-study/helpers.py': V66 / 'helpers.py',
        'experiments/python-game-canonical-tag-v66-study/receiver.py': V66 / 'receiver.py',
        'experiments/python-game-filter-qual-v67-study/verify.py': V67_FILTER / 'verify.py',
        'experiments/python-game-filter-qual-v67-study/helpers.py': V67_FILTER / 'helpers.py',
        'experiments/python-game-filter-qual-v67-study/results.json': V67_FILTER / 'results.json',
        'experiments/python-game-filter-temporal-v62-study/verify.py': ROOT / 'experiments/python-game-filter-temporal-v62-study/verify.py',
        'experiments/python-game-filter-temporal-v62-study/helpers.py': ROOT / 'experiments/python-game-filter-temporal-v62-study/helpers.py',
        'experiments/python-game-error-quality-v57-study/verify.py': ROOT / 'experiments/python-game-error-quality-v57-study/verify.py',
        'experiments/python-game-error-quality-v57-study/model.py': ROOT / 'experiments/python-game-error-quality-v57-study/model.py',
        'experiments/python-codec-study/corpus.py': ROOT / 'experiments/python-codec-study/corpus.py',
        'experiments/python-transform-study/fixed_codec.py': ROOT / 'experiments/python-transform-study/fixed_codec.py',
        'experiments/python-game-direct-rx-v43-study/helpers.py': ROOT / 'experiments/python-game-direct-rx-v43-study/helpers.py',
        'experiments/python-game-direct-rx-v43-study/receiver.py': ROOT / 'experiments/python-game-direct-rx-v43-study/receiver.py',
        'experiments/python-game-display-filter-v60-study/calibration.json': ROOT / 'experiments/python-game-display-filter-v60-study/calibration.json',
        'experiments/python-game-display-filter-v60-study/model.py': ROOT / 'experiments/python-game-display-filter-v60-study/model.py',
    }
    source_hashes = {path: sha_file(file) for path, file in addressed_files.items()}
    result = {
        'schema': 'cu66-v69-portrait-layout-proof-v1',
        'status': 'PASS',
        'git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                              text=True).strip(),
        'source_sha256': source_hashes,
        'fixture': {
            'scene': case['scene'], 'frame_id': row['id'],
            'packet_path': row['packet']['path'], 'packet_sha256': sha_bytes(packet),
            'profile': 'CU66', 'reference_id': meta['reference_id'],
            'canonical_tag': meta['output_tag'].hex(),
            'canonical_yuv_u8_sha256': sha_bytes(canonical),
            'hud_words_u16le_sha256': sha_bytes(hud),
            'identity_rgb565_sha256': sha_bytes(identity_display.astype('<u2').tobytes()),
            'strong_filter_preset': oracle.STRONG,
            'strong_filter_work': filter_work,
            'strong_filtered_luma_sha256': sha_bytes(filtered_y.tobytes()),
            'strong_rgb565_sha256': sha_bytes(strong_display.astype('<u2').tobytes()),
        },
        'geometry': {
            'physical_scan_active': [480, 800],
            'coded_canvas': [720, 480],
            'coded_to_physical': 'physical_x=v; physical_y=u+40',
            'physical_to_coded': 'u=physical_y-40; v=physical_x when 40<=physical_y<760',
            'black_bars': 'physical_y in [0,40) and [760,800); 480x80=38400 pixels',
            'roundtrip_coded_pixels': 345600,
            'roundtrip_physical_active_pixels': 384000,
            'black_bar_pixels': 38400,
            'black_bar_rgb565_bytes': physical_bar_bytes,
            'physical_rgb565_stream_shape': [800, 480],
            'physical_rgb565_stream_order': 'row-major physical_y then physical_x, little-endian u16',
            'identity_stream_sha256': sha_bytes(stream_identity),
            'strong_filter_stream_sha256': sha_bytes(stream_strong),
            'physical_stream_bytes_each': len(stream_identity),
            'stream_artifacts': {
                'physical-rgb565-identity.u16le': {
                    'bytes': len(stream_identity), 'sha256': sha_bytes(stream_identity)},
                'physical-rgb565-strong-filter.u16le': {
                    'bytes': len(stream_strong), 'sha256': sha_bytes(stream_strong)},
            },
        },
        'plane_storage': {
            'sample_shape_order': 'logical coded coordinate u=x in [0,width), v=y in [0,height); address indices are byte/sample offsets',
            'planes': [{'name': n, 'width': w, 'height': h, 'samples': w*h,
                        'bytes_u8': w*h} for n, w, h in PLANES],
            'total_full_frame_yuv_u8_bytes': raw_bytes,
            'one_P_reference_read_plus_new_reference_write_bytes': 2 * raw_bytes,
            'packed_x16_words_per_full_yuv_if_two_u8_samples_per_word': raw_bytes // 2,
            'packed_x16_words_for_one_P_reference_read_plus_new_write': raw_bytes,
            'physical_rgb565_active_image_bytes': 720*480*2,
            'physical_rgb565_full_scan_canvas_bytes': 480*800*2,
            'physical_RGB565_stream_words': 480*800,
            'active_RGB565_pixel_words_per_frame': 720*480,
            'address_trace_model': '8x8 transform-block writer order versus unique active-raster sample order; each u8 sample one address; independent aligned 16-byte bursts per noncontiguous increasing run, no cross-run cache/coalescing',
            'traces': addresses,
        },
        'memory_hardware_limit': {
            'existing_controller_address': '24-bit word address; RGB565 path uses one 16-bit word per pixel',
            'existing_controller_chip_select': 'sdram_cs_n=2\'b10 selects one chip; design evidence supports one 32 MiB W9825G6KH-6 in this controller',
            'board_population': 'Rev4.1 schematic lists two 32 MiB SDRAMs, but installed board/lot not inspected',
        },
        'limits': [
            'Python coordinate, data-layout and output-stream proof only; not RTL or physical panel execution.',
            'The fixed-profile application filter is run as an independent Python reference; filter is full-plane and no BRAM/line-buffer fit or timing follows.',
            '16-byte burst statistics are a logical packed-byte request model, not SDRAM command cycles or controller measurements.',
            'P-frame traffic gives canonical YUV reference read plus replacement write only; excludes packet staging, decoder arrays, cache effects, HUD, display conversion, SDRAM refresh/arbitration and ESP32/QSPI traffic.',
        ],
    }
    (HERE / 'results.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'status': 'PASS', 'roundtrip_coded_pixels': 345600,
                      'black_bar_pixels': 38400, 'yuv_bytes': raw_bytes,
                      'identity_physical_stream_sha256': sha_bytes(stream_identity),
                      'strong_filter_physical_stream_sha256': sha_bytes(stream_strong)}, indent=2))


if __name__ == '__main__':
    main()
