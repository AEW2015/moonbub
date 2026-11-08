#!/usr/bin/env python3
"""Prepare a clean repeat with the exact original V107 RTL/include read order.

The initial checkpoint matrix's preparer is frozen. Its unused RTL list is sorted;
this separate entry point restores the parent synthesis read order for clean runs
without changing any already-dispatched tooling or evidence.
"""
import argparse
import datetime
import json
from pathlib import Path
import re
import shutil
import sys
import uuid

import native as frozen

ROOT=frozen.ROOT
AREA=frozen.AREA
FLOW=frozen.FLOW
BUILDER_SHA='c71c0102364d7c54042b7eff96ee9a8e3bba0bc80a929a723b723fdd0ec45b16'

def parent_order(matrix):
    c=matrix['source_contract'];receipt=frozen.load(ROOT/c['parent_receipt'])
    path=(ROOT/c['parent_receipt']).parent/'recipe-snapshot/inputs.tcl'
    raw=path.read_text();prefix='/build/'+Path(receipt['build_external']).name+'/snapshot/'
    def words(key):
        line=next(s for s in raw.splitlines() if s.startswith('set '+key+' '))
        values=re.findall(r'\{([^{}]+)\}',line)
        assert values and all(s.startswith(prefix) for s in values)
        return [s.removeprefix(prefix) for s in values]
    rtl,dirs=words('rtl_sources'),words('include_dirs')
    assert len(rtl)==len(set(rtl))==17 and set(rtl)=={n for n in c['source_sha256'] if n.endswith('.sv')}
    assert all(any(str(Path(n).parent)==d for n in c['source_sha256'] if n.endswith('.svh')) for d in dirs)
    return dict(parent_inputs_tcl=frozen.rel(path),parent_inputs_tcl_sha256=frozen.sha(path),rtl_read_order_aliases=rtl,include_directory_aliases=dirs)

def prepare(trial_id,repeat_of):
    assert frozen.sha(Path(frozen.__file__))==BUILDER_SHA,'frozen checkpoint preparer changed'
    matrix=frozen.qualification();order=parent_order(matrix);entry=next(x for x in matrix['trials'] if x['id']==trial_id);c=matrix['source_contract'];previous=frozen.load(repeat_of)
    assert previous['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN' and previous['trial_id']==trial_id
    assert previous['native_matrix_sha256']==frozen.sha(frozen.MATRIX) and previous['source_sha256']==c['source_sha256']
    directives={k:entry[k] for k in ('opt','place','phys_opt','phys_opt_stage','route')};assert previous['directives']==directives
    ancestry=dict(path=frozen.rel(repeat_of),sha256=frozen.sha(repeat_of))
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:6]
    build=frozen.BUILD_ROOT/('v108-'+trial_id+'-rtl-'+stamp);build.mkdir();out=AREA/'prepared'/build.name;out.mkdir(parents=True)
    for alias,source in c['source_origins'].items():
        target=build/'snapshot'/alias;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/source['path'],target);assert frozen.sha(target)==c['source_sha256'][alias]
    for name in ('run.tcl','report.tcl','component.xdc'):shutil.copyfile(FLOW/name,build/name)
    mapped=Path('/build')/build.name
    def word(value):
        value=str(value);assert not any(x in value for x in '{}\r\n');return '{'+value+'}'
    lines=['set part xc7a100tcsg324-1','set trial_id '+word(trial_id),'set start_mode {rtl}','set opt_directive '+word(entry['opt']),'set place_directive '+word(entry['place']),'set phys_directive '+word(entry['phys_opt'] or 'NONE'),'set route_directive '+word(entry['route']),
        'set rtl_sources [list '+' '.join(word(mapped/'snapshot'/n) for n in order['rtl_read_order_aliases'])+']',
        'set include_dirs [list '+' '.join(word(mapped/'snapshot'/n) for n in order['include_directory_aliases'])+']','set constraint_file '+word(mapped/'component.xdc')]
    (build/'inputs.tcl').write_text('\n'.join(lines)+'\n')
    recipes={n:frozen.sha(build/n) for n in ('run.tcl','report.tcl','component.xdc','inputs.tcl')}
    inp=dict(schema='v108-prepared-implementation-inputs-v1',preparer_kind='exact_parent_order_clean_repeat',trial_id=trial_id,start_mode='rtl',clean_repeat_of=ancestry,source_order=order,part=matrix['part'],top=matrix['top'],clock_period_ns=10.0,
        native_matrix_path=frozen.rel(frozen.MATRIX),native_matrix_sha256=frozen.sha(frozen.MATRIX),source_contract=c,source_sha256=c['source_sha256'],source_origins=c['source_origins'],parent_synthesis_checkpoint=c['synthesis_checkpoint'],
        directives=directives,recipe_sha256=recipes,closure_files=18,RTL_files=17,timeout_seconds=2400,max_threads=2,cpus=2,memory_limit_bytes=8*1024**3,synthesis_strategy='RuntimeOptimized',synthesis_executed=True,hardware_or_full_parent_signoff=False)
    frozen.write(build/'inputs.json',inp)
    for name in ('inputs.json','inputs.tcl','run.tcl','report.tcl','component.xdc'):shutil.copyfile(build/name,out/name)
    tooling=[Path(__file__).resolve(),Path(frozen.__file__),FLOW/'run_native.py',FLOW/'run.tcl',FLOW/'report.tcl',FLOW/'component.xdc'];(out/'tooling-snapshot').mkdir()
    for source in tooling:shutil.copyfile(source,out/'tooling-snapshot'/source.name)
    preflight=dict(schema='v108-native-preflight-v1',status='PREPARED_NOT_RUN',actual_native_run=False,preparer_kind='exact_parent_order_clean_repeat',trial_id=trial_id,start_mode='rtl',clean_repeat_of=ancestry,source_order=order,prepared_build=str(build),prepared_inputs_sha256=frozen.sha(build/'inputs.json'),native_matrix_path=frozen.rel(frozen.MATRIX),native_matrix_sha256=frozen.sha(frozen.MATRIX),source_contract=c,directives=directives,source_sha256=c['source_sha256'],source_origins=c['source_origins'],recipe_sha256=recipes,tooling_sha256={frozen.rel(p):frozen.sha(p) for p in tooling},parser_self_test=frozen.parser_self_test(),
        source_snapshot_unchanged=all(frozen.sha(build/'snapshot'/n)==h for n,h in c['source_sha256'].items()),parent_checkpoint_sha256_before=frozen.sha(Path(c['synthesis_checkpoint']['external_path'])),limits={k:matrix[k] for k in ('timeout_seconds','max_threads','cpus','memory_limit_bytes','memory_swap_limit_bytes')},clock_period_ns=10.0,part=matrix['part'],hardware_contact=False)
    path=out/'preflight.json';frozen.write(path,preflight);print('V108_CLEAN_PREPARED',frozen.rel(path),frozen.sha(path),flush=True)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--trial',choices=['m'+str(i) for i in range(6)]);ap.add_argument('--repeat-of',type=Path);ap.add_argument('--run',action='store_true');ap.add_argument('--preflight',type=Path);ap.add_argument('--grant',type=Path);ap.add_argument('--audit',type=Path);ap.add_argument('--license-file',type=Path,default=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic'));args=ap.parse_args()
    if args.run:
        assert args.preflight and args.grant and args.audit
        p=frozen.load(args.preflight);assert p['start_mode']=='rtl' and p['preparer_kind']=='exact_parent_order_clean_repeat'
        assert p['source_order']==parent_order(frozen.qualification())
        frozen.launch(args.preflight.resolve(),args.grant.resolve(),args.audit.resolve(),args.license_file)
    else:
        assert args.trial and args.repeat_of and not(args.preflight or args.grant or args.audit)
        prepare(args.trial,args.repeat_of.resolve())

if __name__=='__main__':main()
