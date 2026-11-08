#!/usr/bin/env python3
"""Export a hash-bound fresh-RTL source tree; never execute Vivado."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def word(value):
    value = str(value)
    assert not any(c in value for c in '{}\r\n')
    return '{' + value + '}'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preflight', required=True, type=Path)
    ap.add_argument('--dest', required=True, type=Path)
    a = ap.parse_args()
    pf = json.loads(a.preflight.read_text())
    card_path = a.preflight.parent / 'inputs.json'
    card = json.loads(card_path.read_text())
    assert pf == dict(card, inputs_sha256=sha(card_path))
    assert card['schema'] == 'v111-native-preflight-v1' and card['status'] == 'PREPARED_NOT_RUN'
    assert card['start_mode'] == 'rtl' and card['clock_period_ns'] in (8.0, 10.0)
    assert card['synth_directive'] == 'default' and card['synth_directive_cli'] == 'omitted'
    assert card['timeout_seconds'] == 3600
    contract = card['source_contract']
    origins = contract['source_origins']
    order = contract['source_order']
    assert len(origins) == 18 and len(order['rtl_read_order_aliases']) == 17
    assert set(order['rtl_read_order_aliases']) == {x for x in origins if x.endswith('.sv')}
    for alias, metadata in origins.items():
        assert sha(ROOT / metadata['path']) == metadata['sha256'] == contract['source_sha256'][alias]
    for name in ('run.tcl', 'report.tcl', 'component.xdc'):
        assert sha(a.preflight.parent / name) == card['recipe_sha256'][name]
    dest = a.dest.expanduser().resolve()
    assert not dest.exists() and not dest.is_relative_to(ROOT)
    dest.mkdir(parents=True)
    for alias, metadata in origins.items():
        p = dest / 'snapshot' / alias
        p.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / metadata['path'], p)
    for name in ('run.tcl', 'report.tcl', 'component.xdc'):
        shutil.copyfile(a.preflight.parent / name, dest / name)
    lines = ['set part {xc7a100tcsg324-1}', 'set trial_id ' + word('replay-' + card['trial_id']),
             'set start_mode {rtl}', 'set expected_period_ns ' + str(card['clock_period_ns']),
             'set opt_directive {Default}', 'set place_directive {ExtraNetDelay_high}',
             'set phys_directive {NONE}', 'set route_directive {Default}',
             'set rtl_sources [list ' + ' '.join('[file join $build snapshot ' + word(n) + ']' for n in order['rtl_read_order_aliases']) + ']',
             'set include_dirs [list ' + ' '.join('[file join $build snapshot ' + word(n) + ']' for n in order['include_directory_aliases']) + ']',
             'set constraint_file [file join $build component.xdc]']
    (dest / 'inputs.tcl').write_text('\n'.join(lines) + '\n')
    checks = []
    for virtual in (False, True):
        base = '/virtual relocated V111 path' if virtual else str(dest)
        program = ('set build ' + word(base) + '\nsource ' + word(dest / 'inputs.tcl') + '\n'
                   'puts $expected_period_ns\nforeach p $rtl_sources {puts $p}\nputs $constraint_file\n')
        proc = subprocess.run(['tclsh'], input=program, text=True, capture_output=True, check=True)
        output = proc.stdout.splitlines()
        expected = [str(card['clock_period_ns']), *[base + '/snapshot/' + x for x in order['rtl_read_order_aliases']], base + '/component.xdc']
        assert output == expected and not proc.stderr
        checks.append(dict(kind='virtual-relocation' if virtual else 'real-path', status='PASS', tclsh_exit=proc.returncode))
    (dest / 'README.md').write_text(f'''# V111 fresh-RTL replay: prepared, not executed

Trial source: `{card['trial_id']}`. Target period: {card['clock_period_ns']} ns.
Watchdog: 3600 seconds. Exact 17 RTL files plus one header and fixed functional
run/report/XDC are copied from the prepared card. Input paths are relative to
the replay build directory; no original build tree, checkpoint or license
contents are included. Use the legitimate Vivado 2026.1 build 6511674 toolchain.

```sh
timeout --kill-after=15s 3600s vivado -mode batch -source run.tcl -tclargs "$PWD"
```

This exporter ran only source/hash/Tcl-path checks, not synthesis, placement,
routing or hardware. A new run requires its own resource allocation and retained
reports. The original component timing results and full-parent/hardware gates
remain separate. Default synthesis is selected by omitting its directive.
''')
    manifest = dict(schema='v111-portable-source-only-replay-v1', status='PREPARED_NOT_RUN',
                    preflight=dict(path=str(a.preflight), sha256=sha(a.preflight)), inputs_sha256=sha(card_path),
                    source_count=18, RTL_count=17, header_count=1, source_origins=origins,
                    clock_period_ns=card['clock_period_ns'], watchdog_seconds=3600,
                    source_order=order, synthesis='default-by-omission', observations=contract['observability'],
                    original_checkpoint_required=False, actual_native_run=False, timing_claim=False, hardware_contact=False,
                    checks=checks, exporter_sha256=sha(Path(__file__)),
                    files={str(p.relative_to(dest)): sha(p) for p in sorted(dest.rglob('*')) if p.is_file()})
    (dest / 'replay-manifest.json').write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(status='PASS_SOURCE_ONLY_EXPORT_AND_RELOCATION', path=str(dest), files=len(manifest['files']), period_ns=card['clock_period_ns'])))


if __name__ == '__main__':
    main()
