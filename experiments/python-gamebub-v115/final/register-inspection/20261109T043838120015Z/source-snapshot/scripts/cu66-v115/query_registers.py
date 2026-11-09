#!/usr/bin/env python3
"""Read-only DCP inspection, separately bound from fresh-RTL timing results."""
import argparse,datetime,hashlib,importlib.util,json,subprocess,time,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[2]
A=R/'experiments/python-gamebub-v115/final/register-inspection'
T=R/'fpga/experiments/cu66-v115-inspect/registers.tcl'
N=R/'scripts/cu66-v115/native_final.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def pin(p):return dict(path=str(p.relative_to(R)),sha256=sha(p))
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--receipt',required=True,type=Path);ap.add_argument('--run',action='store_true');a=ap.parse_args()
 receipt=a.receipt.resolve();d=json.loads(receipt.read_text())
 assert receipt.parent.parent==(R/'experiments/python-gamebub-v115/final/native').resolve()
 assert d['status']=='COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN'and d['component_route_finished']and d['source_snapshot_unchanged']and d['recipe_unchanged']
 assert d['synthesis_executed']and not d['checkpoint_read']
 assert d['part']=='xc7a100tcsg324-1' and d['top']=='cs88_pipeline_v91k'
 selection=R/'experiments/python-gamebub-v115/results.json';selection_bytes=selection.read_bytes();selection_pin=pin(selection)
 chosen=[v for v in json.loads(selection_bytes)['native_trials']if v['receipt']==pin(receipt)]
 assert len(chosen)==1 and chosen[0]['composition']=='final' and chosen[0]['result']==d['result']
 for name,want in d['retained_artifact_sha256'].items():assert sha(receipt.parent/name)==want,name
 for alias,v in d['source_contract']['source_origins'].items():
  assert sha(R/v['path'])==v['sha256']
  snapshot=receipt.parent/'source-snapshot'/alias
  assert sha(snapshot)==v['sha256']==d['retained_artifact_sha256'][str(snapshot.relative_to(receipt.parent))]
 meta=d['artifacts']['route.dcp'];dcp=Path(meta['external_path'])
 assert dcp==(Path(d['build_external'])/'results/route.dcp') and dcp.is_file()
 assert dcp.stat().st_size==meta['bytes'] and sha(dcp)==meta['sha256']
 with zipfile.ZipFile(dcp)as archive:checkpoint_xml=archive.read('dcp.xml')
 manifest=ET.fromstring(checkpoint_xml)
 identity={name:manifest.find(name).attrib['Name']for name in ['Top','Part','BUILD_NUMBER','PRODUCT']}
 assert identity==dict(Top=d['top'],Part=d['part'],BUILD_NUMBER='6511674',PRODUCT='Vivado v2026.1 (64-bit)')
 assert sha(receipt.parent/'inputs.json')==d['retained_artifact_sha256']['inputs.json']
 assert json.loads((receipt.parent/'inputs.json').read_text())['source_contract']==d['source_contract']
 spec=importlib.util.spec_from_file_location('v115_native_resources',N);n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
 if not a.run:print('READ_ONLY_QUERY_PREPARED',receipt);return
 gate=n.memory();assert gate['MemAvailable_bytes']>=8*1024**3 and gate['PSI_full_avg10']<1 and gate['combined_used_fraction']<.85,gate
 stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out=A/stamp;out.mkdir(parents=True)
 work=Path('/home/lori/gamebub-build/cu66-v69')/('v115-inspect-'+stamp);work.mkdir()
 source_files=[Path(__file__).resolve(),T,N]
 source_hashes={str(p.relative_to(R)):sha(p)for p in source_files}
 for p in source_files:
  target=out/'source-snapshot'/p.relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes());assert sha(target)==source_hashes[str(p.relative_to(R))]
 source_snapshot=out/'source-snapshot'
 query_snapshot=source_snapshot/T.relative_to(R)
 (out/'checkpoint-manifest.xml').write_bytes(checkpoint_xml)
 (out/'selection-snapshot.json').write_bytes(selection_bytes)
 assert sha(out/'selection-snapshot.json')==selection_pin['sha256']
 before=sha(dcp);assert before==meta['sha256'];name='gamebub-v115-inspect-'+stamp.lower();license_file=Path('/home/lori/acorn-nexys4-ddr/cache/vivado.lic')
 cmd=['docker','run','--rm','--init','--name',name,'--memory','8g','--memory-swap','8g','--cpus','2','--pids-limit','2048','--network','host','--ulimit','core=0','--mount','type=bind,src=/home/lori/acorn-nexys4-ddr/tools,dst=/opt/amd-tools,readonly','--mount',f'type=bind,src={dcp},dst=/input/route.dcp,readonly','--mount',f'type=bind,src={query_snapshot},dst=/input/query.tcl,readonly','--mount',f'type=bind,src={license_file},dst=/root/.Xilinx/license.dat,readonly','--mount',f'type=bind,src={out},dst=/output','--mount',f'type=bind,src={source_snapshot},dst=/output/source-snapshot,readonly','--mount',f'type=bind,src={work},dst=/work','-e','LD_PRELOAD=/lib/x86_64-linux-gnu/libudev.so.1','-e','XILINXD_LICENSE_FILE=/root/.Xilinx/license.dat','-w','/work',d['image_id'],'timeout','--kill-after=10s','240s','/opt/amd-tools/2026.1/Vivado/bin/vivado','-mode','batch','-nojournal','-nolog','-notrace','-source','/input/query.tcl','-tclargs','/input/route.dcp','/output',str(d['clock_period_ns'])]
 r=dict(status='FAIL',schema='v115-read-only-routed-register-inspection-v1',source_native_receipt=pin(receipt),selected_summary=selection_pin,selected_summary_archived_as='selection-snapshot.json',native_checkpoint_artifact=meta,archived_native_artifacts_verified=len(d['retained_artifact_sha256']),source_composition=d['source_contract'],external_checkpoint=dict(path=str(dcp),sha256=before),tool_work_external=str(work),checkpoint_read_for_inspection_only=True,new_synthesis_or_implementation=False,source_sha256=source_hashes,source_snapshot_readonly_mount=True,checkpoint_manifest_identity=identity,command=cmd,memory=[],limits='Read-only mapping/fanin evidence. Does not alter or replace the fresh-RTL timing run, add an implementation trial, qualify board I/O or establish throughput.')
 started=time.monotonic()
 try:
  with(out/'query.log').open('w')as log:
   proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT);high=0
   while proc.poll()is None:
    sample=dict(elapsed=time.monotonic()-started,**n.memory());r['memory'].append(sample);high=high+1 if sample['PSI_full_avg10']>=5 else 0
    if sample['MemAvailable_bytes']<4*1024**3 or high>=2 or sample['combined_used_fraction']>=.9 or sample['elapsed']>260:
     r['resource_stop']=sample;subprocess.run(['docker','stop','--time','5',name],capture_output=True,timeout=15);break
    time.sleep(2)
   r['exit_code']=proc.wait(timeout=20)
  assert r['exit_code']==0 and 'resource_stop'not in r
  assert 'V115_READ_ONLY_REGISTER_INSPECTION_COMPLETE'in(out/'query.log').read_text()
  assert sha(dcp)==before==meta['sha256'] and pin(receipt)==r['source_native_receipt']
  for p in [Path(__file__),T,N]:assert sha(p)==r['source_sha256'][str(p.relative_to(R))]
  rows=[l.split('\t')for l in(out/'registers.tsv').read_text().splitlines()[1:]]
  r['surviving_flipflops']={label:[row for row in rows if label in row[0]and row[1].startswith('FD')]for label in ['base_kill_authorized','base_kill_owner','next_address_at_request','prepared_request_addr','prepared_request_in_bounds']}
  r['status']='PASS_READ_ONLY_MAPPING_QUERY'
 except BaseException as e:r['error']=repr(e);raise
 finally:
  r['wall_seconds']=time.monotonic()-started;r['artifact_sha256']={str(p.relative_to(out)):sha(p)for p in sorted(out.rglob('*'))if p.is_file()}
  (out/'receipt.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(r['status'],out,flush=True)
if __name__=='__main__':main()
