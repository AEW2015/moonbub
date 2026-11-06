"""Freeze bounded completed board diagnostics; never package an image."""
from pathlib import Path
import argparse,hashlib,json,shutil
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--build',required=True,type=Path)
p.add_argument('--output',required=True,type=Path)
a=p.parse_args();build=a.build.resolve();out=a.output.resolve()
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
execution=json.loads((build/'execution.json').read_text())
assert execution['completion_marker']and execution['required_reports_present']
out.mkdir(parents=True,exist_ok=False)
names=['execution.json','selection.json','source-freeze.json','executed-builder.py','executed.tcl',
       'console.log','vivado.log','synthesized-utilization.rpt','synthesized-clocks.rpt',
       'exceptions-postsynth.rpt','cdc-postsynth.rpt','check-timing-postsynth.rpt',
       'placed-timing-summary.rpt','placed-setup-paths.rpt','timing-summary.rpt','setup-paths.rpt',
       'hold-paths.rpt','utilization.rpt','route-status.rpt','drc.rpt','cdc.rpt','exceptions.rpt',
       'clock-interaction.rpt','bus-skew.rpt','check-timing.rpt']
records={}
for name in names:
    source=build/name
    assert source.is_file()and 0<source.stat().st_size<=2_000_000,name
    expected=sha(source);shutil.copyfile(source,out/name)
    assert sha(source)==sha(out/name)==expected
    records[name]=expected
omitted={n:dict(path=str(build/n),bytes=(build/n).stat().st_size,sha256=sha(build/n))
         for n in ['synthesized.dcp','constrained.dcp','placed.dcp','routed.dcp']}
shutil.copyfile(__file__,out/'executed-archiver.py')
(out/'REPORTS.json').write_text(json.dumps(dict(status='DIAGNOSTIC_REPORTS_NOT_RELEASE',
    source_build=str(build),execution_status=execution['status'],files_sha256=records,
    omitted_local_checkpoints=omitted,selected_inputs='Published separately at exact paths in source-freeze.json; private build inputs rehashed by executed builder.',
    BIT=False,hardware=False,qualified_image=False),indent=2)+'\n')
print(json.dumps(dict(reports=len(records),output=str(out),BIT=False)))
