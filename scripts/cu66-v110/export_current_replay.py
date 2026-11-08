#!/usr/bin/env python3
"""Export a source-only, fresh-RTL V110 replay tree. Never runs Vivado."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
VALID_TIMEOUTS={2400,3600}

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()

def word(value):
    value=str(value)
    assert not any(c in value for c in '{}\r\n')
    return '{'+value+'}'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--preflight',type=Path,required=True)
    ap.add_argument('--dest',type=Path,required=True)
    a=ap.parse_args()
    pfpath=a.preflight.resolve(); pf=json.loads(pfpath.read_text())
    assert pf['schema']=='v110-native-preflight-v1' and pf['status']=='PREPARED_NOT_RUN'
    assert pf['start_mode']=='rtl','Portable replay exports require fresh RTL.'
    inputs_path=pfpath.parent/'inputs.json'
    assert sha(inputs_path)==pf['inputs_sha256'],'Prepared input card hash mismatch.'
    card=json.loads(inputs_path.read_text())
    assert card['start_mode']=='rtl' and card.get('checkpoint_from') is None,'Checkpoint-based replay is not exportable.'
    timeout=card.get('timeout_seconds',pf.get('timeout_seconds'))
    assert timeout in VALID_TIMEOUTS, f'Unrecognized watchdog value: {timeout}'
    assert pf.get('timeout_seconds',timeout)==timeout,'Preflight and input watchdog differ.'
    assert card['clock_period_ns']==pf.get('clock_period_ns',10.0)==10.0
    assert card['part']==pf.get('part','xc7a100tcsg324-1')=='xc7a100tcsg324-1'
    assert card['synth_directive']==pf['synth_directive'] and card['synth_directive_cli']==pf['synth_directive_cli']
    assert card['synth_directive'] in ('default','RuntimeOptimized')
    assert card['synth_directive_cli'] in ('omitted','explicit')
    assert (card['synth_directive']=='default')==(card['synth_directive_cli']=='omitted')
    assert card['directives']==pf.get('directives',card['directives'])
    origins=card['source_origins']; order=card['source_order']; rtl=order['rtl_read_order_aliases']; includes=order['include_directory_aliases']
    assert len(origins)==18 and len(rtl)==17 and len(set(rtl))==17
    assert set(rtl)=={alias for alias in origins if alias.endswith('.sv')}
    headers={alias for alias in origins if alias.endswith('.svh')}
    assert len(headers)==1 and set(rtl).isdisjoint(headers)
    assert len(includes)>0 and all(any(meta['path'].startswith(directory+'/') for meta in origins.values()) for directory in includes)
    for alias,meta in origins.items():
        source=ROOT/meta['path']
        assert sha(source)==meta['sha256']==card['source_sha256'][alias], f'Source hash mismatch: {alias}'
    recipe_dir=pfpath.parent
    for name in ('run.tcl','report.tcl','component.xdc'):
        assert sha(recipe_dir/name)==card['recipe_sha256'][name], f'Recipe hash mismatch: {name}'
    dest=a.dest.expanduser().resolve()
    assert not dest.exists(),'Use a new output directory.'
    assert not dest.is_relative_to(ROOT),'Generated export trees must stay outside the checkout.'
    dest.mkdir(parents=True)
    for alias,meta in origins.items():
        target=dest/'snapshot'/alias;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ROOT/meta['path'],target)
    for name in ('run.tcl','report.tcl','component.xdc'):
        shutil.copyfile(recipe_dir/name,dest/name)
    lines=['set part {xc7a100tcsg324-1}',
           'set trial_id '+word('portable-'+card['trial_id']),
           'set start_mode {rtl}',
           'set opt_directive '+word(card['directives']['opt']),
           'set place_directive '+word(card['directives']['place']),
           'set phys_directive '+word(card['directives']['phys_opt'] or 'NONE'),
           'set route_directive '+word(card['directives']['route']),
           'set rtl_sources [list '+' '.join('[file join $build snapshot '+word(n)+']' for n in rtl)+']',
           'set include_dirs [list '+' '.join('[file join $build snapshot '+word(n)+']' for n in includes)+']',
           'set constraint_file [file join $build component.xdc]']
    (dest/'inputs.tcl').write_text('\n'.join(lines)+'\n')
    synth_clause='-directive RuntimeOptimized' if card['synth_directive']=='RuntimeOptimized' else '(directive omitted; Vivado Default)'
    observability=pf.get('observability_contract',card.get('observability_contract'))
    observability_scope=observability if observability is not None else {'qualification_scope':card['source_contract'].get('qualification_scope'),'all_private_state_exact':None}
    manifest={
      'schema':'v110-current-portable-fresh-RTL-replay-v1','status':'PREPARED_NOT_RUN',
      'variant':card['variant'],'trial_id':card['trial_id'],'profile_label':pf['profile_label'],
      'preflight_path':str(pfpath),'preflight_sha256':sha(pfpath),'inputs_sha256':sha(inputs_path),
      'part':card['part'],'clock_period_ns':card['clock_period_ns'],'top':card['top'],
      'start_mode':'rtl','checkpoint_from':None,'requires_original_checkpoint':False,
      'watchdog_seconds':timeout,'synthesis':{'declared_mode':card['synth_directive'],'cli_mode':card['synth_directive_cli'],'vivado_directive':card['synth_directive'],'tcl_clause':synth_clause},
      'observability_contract':observability,'observability_scope':observability_scope,
      'directives':card['directives'],'rtl_read_order':rtl,'include_directories':includes,
      'source_origins':origins,'source_count':18,'rtl_count':17,'header_count':1,
      'recipe_sha256':{n:sha(dest/n) for n in ('run.tcl','report.tcl','component.xdc')},
      'replay_inputs_are_relative':True,'uses_original_host_source_paths':False,
      'actual_native_run':False,'timing_claim':False,'hardware_contact':False,'hardware_qualification':False,
      'files':{str(p.relative_to(dest)):sha(p) for p in sorted(dest.rglob('*')) if p.is_file()}
    }
    readme=f'''# Fresh RTL replay (prepared, not run)

This source-only export contains 17 RTL files, one table header, and the exact
functional run/report Tcl and fixed XDC bound to the selected preflight. The
inputs Tcl resolves RTL, include, and constraint paths relative to the replay
build directory. It starts from RTL and does not load the original synthesis
checkpoint or original build directory.

Declared synthesis mode: `{card['synth_directive']}` (CLI mode: `{card['synth_directive_cli']}`).
Clock: 10 ns. Watchdog: `{timeout}` seconds, copied from the prepared input card.
The synthesis directive and observability contract are recorded in
`replay-manifest.json`. No synthesis, placement, routing, or hardware run has
been performed by this export.

Use the exact watchdog when launching in a separately authorized allocation:

```sh
timeout --kill-after=5s {timeout}s vivado -mode batch -source run.tcl -tclargs "$PWD"
```

This source package is not a timing result or hardware qualification. Review
all setup, hold, pulse-width, clock, methodology, route, and utilization reports
from any separately authorized execution. Complete-parent integration and
hardware performance remain separate gates.
'''
    (dest/'README.md').write_text(readme)
    manifest['files']['README.md']=sha(dest/'README.md')
    (dest/'replay-manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':'PREPARED_NOT_RUN','directory':str(dest),'trial_id':card['trial_id'],'source_count':18,'rtl_count':17,'watchdog_seconds':timeout,'requires_original_checkpoint':False}))

if __name__=='__main__':
    main()
