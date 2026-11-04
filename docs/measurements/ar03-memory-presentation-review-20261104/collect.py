"""Read-only source binding and arithmetic; writes only this review's record."""
from pathlib import Path
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
KIT = Path('C:/Users/lavat/codex/moonbub-ar03-v20-20261104')
SUN = Path('C:/Users/lavat/codex/sunshine-gamebub-dxgi-work')
KP = '27a4dde6a7e2ea4fab09d892551ef542f05c8965'
SP = 'c9c0bf4bcbe5c95f38b50bf6e190b84822886d53'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def local(rel):
    data = (ROOT / rel).read_bytes()
    return {'path': rel, 'bytes': len(data), 'sha256': sha(data)}

def git_binding(repo, pin, rel):
    spec = pin + ':' + rel
    data = subprocess.check_output(['git', 'show', spec], cwd=repo)
    obj = subprocess.check_output(['git', 'rev-parse', spec], cwd=repo, text=True).strip()
    return {'repository': str(repo), 'commit': pin, 'path': rel,
            'git_object': obj, 'bytes': len(data), 'sha256': sha(data)}

def main():
    baseline = 'fpga/candidates/v21-audio/'
    selected = ['moonshine_memory_burst.sv', 'moonshine_sdram_burst.sv',
                'moonshine_burst_packer.sv', 'moonshine_lcd_720p.sv',
                'moonshine_core_overlap.sv', 'moonshine_top_dual_burst.sv',
                'tile_coalescer_dual.sv', 'moonshine_timing_control.sv']
    bindings = json.loads((ROOT / baseline / 'build/source-bindings.json').read_text())
    native = {r['path']: r['sha256'] for r in bindings}
    baseline_files = [local(baseline + 'rtl/' + name) for name in selected]
    for row in baseline_files:
        assert native[row['path']] == row['sha256'], row['path']
    extra = [baseline + 'manifest.json', baseline + 'build/source-bindings.json',
             baseline + 'build/utilization.rpt',
             'fpga/candidates/akd1-compute-lcd-prune-20261104/build/utilization.rpt',
             'fpga/candidates/akd1-compute-lcd-prune-20261104/compute/ar03_key_tagged.sv',
             'fpga/candidates/akd1-compute-lcd-prune-20261104/compute/ar03_raster_stripes.sv',
             'fpga/experiments/sdram_burstlab/sdram_model_burst.sv',
             'host/ar03-contract-20261104/development-profile.json']
    pinned = [git_binding(SUN, SP, 'tools/gamebub/native/body_decoder.h'),
              git_binding(KIT, KP, 'hardware/gamebub-v20/development-profile.json'),
              git_binding(KIT, KP, 'hardware/gamebub-v20/README.md')]
    exported_profile = (ROOT / 'host/ar03-contract-20261104/development-profile.json').read_bytes()
    original_profile = subprocess.check_output(['git', 'show', KP + ':hardware/gamebub-v20/development-profile.json'], cwd=KIT)
    assert exported_profile == original_profile, 'Exported profile must match pinned Git bytes'
    width, height, fps = 720, 480, 30
    pclk = 50_000_000 * 56.375 / 3 / 32
    refresh = pclk / (541 * 834)
    rgb = width * height * 2
    yuv = width * height * 3 // 2
    scan = rgb * refresh
    arithmetic = {
        'scope': 'Arithmetic lower bounds and peak bus width only; not measured throughput',
        'width': width, 'height': height, 'target_fps': fps,
        'pixel_clock_Hz': pclk, 'preset0_htotal': 541, 'preset0_vtotal': 834,
        'panel_refresh_Hz': refresh, 'RGB565_frame_bytes': rgb,
        'YUV420_u8_frame_bytes': yuv,
        'two_logical_YUV_banks_bytes': 2 * yuv,
        'two_logical_plus_scratch_YUV_bytes': 3 * yuv,
        'RGB_front_back_bytes': 2 * rgb,
        'SDRAM_raw_16bit_100MHz_bytes_per_second': 200_000_000,
        'scanout_bytes_per_second': scan,
        'RGB_write30_bytes_per_second': rgb * fps,
        'YUV_write30_bytes_per_second': yuv * fps,
        'ideal_single_read_YUV_render30_bytes_per_second': yuv * fps,
        'KEY_store_render_scanout_min_bytes_per_second': 2 * yuv * fps + rgb * fps + scan,
        'P_with_single_predictor_read_min_bytes_per_second': 3 * yuv * fps + rgb * fps + scan,
        'mandatory_patch_words_per_frame': 21120,
        'optional_separate_patch_write30_bytes_per_second': 21120 * 2 * fps,
        'RGB_buffer_word_bases': [0, 0x80000],
        'legacy_sim_memory_words': 1048576,
        'legacy_sim_memory_bytes': 1048576 * 2,
        'AKD1_prune_RAMB36_used': 106, 'device_RAMB36_tiles': 135,
        'AKD1_prune_free_RAMB36_tiles': 29,
        'whole_YUV_min_RAMB36_tile_equivalents': yuv / 4608,
        'build50_RAM_tile_equivalents_used': 120.5,
        'excluded_costs': ['refresh', 'row activate/precharge', 'request/turnaround cycles',
                           'masked burst wastage', 'redundant chroma reads', 'patch writes if separate',
                           'queueing/CDC', 'QSPI/transport/host/ESP32/radio service'],
    }
    out = {'status': 'READ_ONLY_REVIEW', 'hardware_actions': 'NONE', 'builds': 'NONE',
           'selected_build50_source_bindings_verified': True,
           'baseline_sources': baseline_files, 'other_local_inputs': [local(x) for x in extra],
           'pinned_git_inputs': pinned, 'arithmetic': arithmetic,
           'collector_sha256': sha(Path(__file__).read_bytes())}
    target = HERE / 'bindings-and-arithmetic.json'
    if target.exists():
        raise SystemExit('Use a fresh review directory; refusing to overwrite prior evidence')
    target.write_text(json.dumps(out, indent=2) + '\n', encoding='utf-8')
    print('PASS read-only bindings/arithmetic; no build or hardware access')

if __name__ == '__main__':
    main()
