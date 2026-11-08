#!/usr/bin/env python3
"""Prepare a portable fresh-RTL source tree; never start Vivado or require a DCP."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
AREA = ROOT/'experiments/python-gamebub-v109'



def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def word(s):
    assert not any(x in s for x in '{}\r\n')
    return '{'+s+'}'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preflight',type=Path,required=True)
    ap.add_argument('--dest',type=Path,required=True)
    args = ap.parse_args()
    dest = args.dest.expanduser().resolve()
    assert not dest.exists(), 'Use a new output directory'
    assert not dest.is_relative_to(ROOT), 'Keep generated builds outside the source checkout'
    card_path = args.preflight.resolve()
    preflight = json.loads(card_path.read_text())
    assert preflight['schema']=='v109-native-preflight-v1'
    inputs=card_path.parent/'inputs.json'
    assert sha(inputs)==preflight['inputs_sha256']
    card=json.loads(inputs.read_text())
    variant=card['variant']
    origins = card['source_origins']
    order = card['source_order']
    rtl = order['rtl_read_order_aliases']
    assert len(origins)==18 and len(rtl)==len(set(rtl))==17
    assert set(rtl)=={n for n in origins if n.endswith('.sv')}
    assert card['clock_period_ns']==10 and card['part']=='xc7a100tcsg324-1'
    assert card['start_mode'] in ('rtl','checkpoint')
    for alias,meta in origins.items():
        assert sha(ROOT/meta['path'])==meta['sha256']==card['source_sha256'][alias]
    recipe_dir = card_path.parent
    for name in ('run.tcl','report.tcl','component.xdc'):
        assert sha(recipe_dir/name)==card['recipe_sha256'][name]
    dest.mkdir(parents=True)
    for alias,meta in origins.items():
        p=dest/'snapshot'/alias
        p.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/meta['path'],p)
    for name in ('run.tcl','report.tcl','component.xdc'):
        shutil.copyfile(recipe_dir/name,dest/name)
    directives=card['directives']
    lines=['set part xc7a100tcsg324-1','set trial_id '+word('portable-'+variant),
           'set start_mode {rtl}','set opt_directive '+word(directives['opt']),
           'set place_directive '+word(directives['place']),
           'set phys_directive '+word(directives['phys_opt'] or 'NONE'),
           'set route_directive '+word(directives['route']),
           'set rtl_sources [list '+' '.join('[file join $build snapshot '+word(n)+']' for n in rtl)+']',
           'set include_dirs [list '+' '.join('[file join $build snapshot '+word(n)+']' for n in order['include_directory_aliases'])+']',
           'set constraint_file [file join $build component.xdc]']
    (dest/'inputs.tcl').write_text('\n'.join(lines)+'\n')
    manifest=dict(schema='v109-portable-fresh-RTL-replay-v1',status='PREPARED_NOT_RUN',
                  variant=variant,preflight=str(card_path.relative_to(ROOT)),preflight_sha256=sha(card_path),
                  part=card['part'],clock_period_ns=10.0,top='cs88_pipeline_v91k',
                  rtl_read_order=rtl,include_directories=order['include_directory_aliases'],
                  source_origins=origins,directives=directives,source_count=18,
                  requires_original_checkpoint=False,requires_original_build_directory=False,
                  actual_native_run=False,hardware_contact=False,
                  files={str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()})
    (dest/'README.md').write_text('''# Fresh RTL replay (prepared, not run)

This tree contains 17 RTL files, the table header, exact build/report Tcl and
the fixed 10-ns XDC. inputs.tcl uses paths relative to the build directory.
It does not read the original synthesis checkpoint or original host paths.

Use Vivado 2026.1 build 6511674 with Artix-7 support and your legitimate license.
Run inside a container or allocation limited to 2 CPUs and 8 GiB, without extra
swap, respecting the host available-RAM/pressure gate and two-heavy-job limit.
The Tcl sets general.maxThreads=2. After loading the Vivado environment, run
from this directory:

```sh
timeout --kill-after=5s 2400s vivado -mode batch -source run.tcl -tclargs "$PWD"
```

Inspect the complete setup/hold/pulse, clock, methodology, route-status and
utilization reports in results/. Negative setup slack is a failure. This source
export has not itself run Vivado; original study outcomes remain in the Git
branch. It creates an out-of-context decoder implementation, not a board
bitstream. Parent I/O/clock/CDC integration and hardware throughput stay open.
''')
    manifest['files']['README.md']=sha(dest/'README.md')
    (dest/'replay-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(status='PREPARED_NOT_RUN',directory=str(dest),variant=variant,source_count=18,original_checkpoint_required=False)))


if __name__ == '__main__':
    main()
