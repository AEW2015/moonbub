#!/usr/bin/env python3
"""Generate/check hashes for frozen inputs to the CU66 v69 work package."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE_SET = HERE / 'source-set.json'
OUTPUT = ROOT / 'docs/cu66-v69/source-pins.json'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def current():
    spec = json.loads(SOURCE_SET.read_text())
    paths = set()
    for pattern in spec['globs']:
        matches = list(ROOT.glob(pattern))
        assert matches, f'no matches: {pattern}'
        paths.update(p for p in matches if p.is_file())
    files = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(paths)}
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT,
                                   text=True).strip()
    return {
        'schema': 'cu66-v69-source-pins-v1',
        'baseline_commit': head,
        'source_set_sha256': digest(SOURCE_SET),
        'generator_sha256': digest(Path(__file__)),
        'files_sha256': files,
        'external_sources': {
            'gamebub_rev4_1_pcb': {
                'repository': 'https://github.com/gamebub/gamebub-pcb',
                'commit': '88f578a1a4c4096a33ab038eae82348cafab1229',
                'files_sha256': {
                    'handheld_rev4_1/ram.kicad_sch': '757e907b7d0d800f371916269453231c1512a39f3b22ca553150fb93fe0d9b42',
                    'handheld_rev4_1/schematic.pdf': '79f5a4c54345166d140a0f5447a5c8769829882a2ce38bdb194cd8a5853483aa',
                },
            },
            'winbond_w9825g6kh_datasheet': {
                'url': 'https://www.winbond.com/resource-files/w9825g6kh_a04.pdf',
                'revision': 'A04, 2017-03-20',
                'sha256': '9530f7a59a18e062b6832dc96c7a60725b97d85c295631434a12538ee6e1aaf3',
            },
            'issi_sram_datasheet': {
                'url': 'https://www.issi.com/WW/pdf/61-64WV25616EDBLL.pdf',
                'retrieval': 'Manufacturer site blocks automated local retrieval; URL is primary schematic datasheet link.',
            },
            'local_vivado_build_provisioning': {
                'project': '/home/lori/amd-docker',
                'dockerfile_sha256': '1ccf3cc4d8ac95b129e30f9b67b55f090e5f11c9362aa86814d8620a0708243e',
                'artix7_install_config': 'install_config_vivado_2025.2_artix7.txt',
                'artix7_install_config_sha256': '81bd2ced2275e09026efd209ea233dec7437a020b89555f179d5b4730bdd0173',
                'install_config_selection': 'Vivado ML Standard, Vivado, Artix-7 FPGAs:1',
                'vivado_container_image_id': 'sha256:6d2f9bb53968bff852af10ab37eb7e64872aab557a94c261cf605dc82f6dac58',
                'xsetup': '/opt/Xilinx/.xinstall/2025.2/xsetup',
                'part_query': 'xc7a100tcsg324-1 missing at preflight; Vivado batch Add attempted but exited before installation because installer authentication token generation is required.',
                'install_attempt': 'Dedicated Vivado container; reviewed Artix-7 config; failed before installation at authentication-token prerequisite; no token material read.',
                'cached_resources_checked': 'Filename-only check limited to /home/lori/amd-docker/resources and named XEM8320 installer tree; no matching 2025.2/Artix filename found. This does not show a full installer payload is required.',
            },
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true',
                        help='compare current inputs with the recorded source pins')
    parser.add_argument('--refresh', action='store_true',
                        help='replace pins after source review')
    args = parser.parse_args()
    assert args.check ^ args.refresh, 'choose exactly one of --check or --refresh'
    data = current()
    encoded = json.dumps(data, indent=2, sort_keys=True) + '\n'
    if args.refresh:
        OUTPUT.write_text(encoded)
        print(f'Wrote {OUTPUT.relative_to(ROOT)}: {len(data["files_sha256"])} local source files')
        return
    previous = json.loads(OUTPUT.read_text())
    # The pin baseline is the commit when the reviewed source set was frozen;
    # a later docs/scripts commit must not invalidate unchanged input hashes.
    data['baseline_commit'] = previous['baseline_commit']
    if previous != data:
        raise SystemExit('CU66 source pin mismatch; review source changes before --refresh')
    print(f'CU66_SOURCE_PINS_PASS {len(data["files_sha256"])} local sources, baseline {data["baseline_commit"]}')


if __name__ == '__main__':
    main()
