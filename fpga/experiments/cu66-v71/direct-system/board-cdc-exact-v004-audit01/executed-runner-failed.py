from pathlib import Path
import argparse,csv,hashlib,json,os,re,shutil,subprocess,time,zipfile
r=Path(__file__).resolve().parents[4]
b=r/'fpga/experiments/cu66-v71/direct-system/board-implementation01'
s=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/board-source-v004'
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--wait-seconds',type=int,default=0);a=p.parse_args();checkpoint=b/'synthesized.dcp';deadline=time.monotonic()+a.wait_seconds
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
while True:
 try:
  assert checkpoint.is_file()
  with zipfile.ZipFile(checkpoint)as z:assert z.testzip()is None
  before=sha(checkpoint);time.sleep(.2);assert before==sha(checkpoint);break
 except (AssertionError,zipfile.BadZipFile,PermissionError):
  if time.monotonic()>=deadline:print('WAITING_FOR_COMPLETE_IMMUTABLE_CONSTRAINED_DCP_NO_AUDIT_PASS');raise SystemExit(2)
  time.sleep(1)
o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);(o/'tmp').mkdir();shutil.copy2(checkpoint,o/'input-synthesized.dcp');assert sha(o/'input-synthesized.dcp')==before
sf=json.loads((b/'source-freeze.json').read_text())
for name,h in sf.items():assert sha(r/name)==h and sha(b/'inputs'/name)==h,name
assert json.loads((s/'selection.json').read_text())['part']=='xc7a100tcsg324-1'
v36=r/'fpga/experiments/cu66-v71/bus-split/platform-syncsafe/manifest-v001.json';vm=json.loads(v36.read_text())
for entry in vm['artifacts']:assert sha(Path(entry['path']))==entry['sha256'],entry['path']
pins={str(checkpoint):before,str(b/'source-freeze.json'):sha(b/'source-freeze.json'),str(s/'selection.json'):sha(s/'selection.json'),str(s/'source-freeze.json'):sha(s/'source-freeze.json'),str(v36):sha(v36),str(Path(__file__)):sha(Path(__file__))}
shutil.copy2(Path(__file__).with_name('audit-fixed.tcl'),o/'audit.tcl');pins[str(Path(__file__).with_name('audit-fixed.tcl'))]=sha(o/'audit.tcl')
shutil.copytree(s/'constraints',o/'candidate-constraints')
for f in(s/'constraints').iterdir():
 if f.is_file():pins[str(f)]=sha(f)
for name,h in json.loads((s/'source-freeze.json').read_text()).items():assert sha(r/name)==h,name
(o/'source-binding.json').write_text(json.dumps(dict(status='BOUND_NEW_CONSTRAINTS_ON_V002_UNCONSTRAINED_SYNTH_DCP_NO_V004_RTL_QUALIFICATION',originals=pins,checkpoint_copy_sha256=before,all_build_original_and_compiled_sources_verified=len(sf),exact_v36_manifest_integrity=True,native_threads=1,constraint_application_only=True,RTL_placement_route_mutation=False,DCP_RTL_source_version='v002_old_stager',selected_constraints_version='v004_exact_bundles',physical_timing='NOT_QUALIFIED'),indent=2)+'\n')
cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(o/'audit.tcl'),'-log',str(o/'vivado.log'),'-journal',str(o/'vivado.jou'),'-tclargs',str(o)];start=time.monotonic()
with(o/'native.log').open('wb')as out:q=subprocess.run(cmd,cwd=o,env=dict(os.environ,TEMP=str(o/'tmp'),TMP=str(o/'tmp')),stdout=out,stderr=subprocess.STDOUT,timeout=1200)
(o/'execution.json').write_text(json.dumps(dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-start),indent=2)+'\n');assert q.returncode==0,('native_audit_failed',o)
def rows(name):
 with(o/name).open()as f:return list(csv.DictReader(f,delimiter='\t'))
fan=rows('lcd-first-stage.tsv');assert len(fan)==6 and all(x['match']=='1'for x in fan)
bounds=rows('bound-registers.tsv');counts={}
for group,width in [('request_line0',10),('request_line1',10),('underrun_gray',32)]:
 current=[x for x in bounds if x['group']==group];counts[group]={k:sum(x['role']==k for x in current)for k in('source','destination')};assert counts[group]==dict(source=width,destination=width)
 assert all(x['REF_PIN_NAME']==('C'if x['role']=='source'else'D') and x['REF_NAME'].startswith('FD')for x in current)
paths=rows('bound-paths.tsv');assert all(abs(float(x['requirement'])-10)<.001 for x in paths)
segmentation_properties=[x['segmentation_properties']for x in paths if x['segmentation_properties']]
assert not any(re.search(r'(?:=)(?:1|true)(?:;|$)',x,re.I)for x in segmentation_properties)
log=(o/'native.log').read_text();assert not re.search(r'^(?:WARNING|CRITICAL WARNING|ERROR):.*(?:segment|not a valid startpoint)',log,re.M|re.I)
initial=(o/'initial-unconstrained.xdc').read_text();assert not re.search(r'^set_(?:max_delay|min_delay|false_path|multicycle_path|bus_skew)\b',initial,re.M), 'inherited timing exceptions would stack'
for key,width in [('address',12),('response',32)]:
 rr=[x for x in rows('exact-bundle-paths.tsv')if x['bundle']==key];assert len(set(x['start']for x in rr))==width and len(set(x['end']for x in rr))==width;assert all(float(x['requirement'])==10.0 for x in rr)
sdram=rows('sdram-paths.tsv');req={k:sorted(set(round(float(x['requirement']),6)for x in sdram if x['type']==k))for k in('max','min')};assert req==dict(max=[12.625],min=[2.625]),('SDRAM_requirement',req)
xdc=(o/'effective.xdc').read_text();multi=[line for line in xdc.splitlines()if line.startswith('set_multicycle_path')];assert any('-setup'in line and re.search(r'(?:^|\s)2(?:\s|$)',line)and'dq_capture'in line for line in multi);assert not any('-hold'in line for line in multi),multi
expected_pins={}
for file in(s/'constraints').glob('*.xdc'):
 text=file.read_text()
 for m in re.finditer(r'set_property\s+-dict\s+\{([^}]+)\}\s*\[get_ports\s+(?:\{([^}]+)\}|([^\]]+))\]',text):
  fields=m[1].split();values=dict(zip(fields[0::2],fields[1::2]));port=(m[2]or m[3]).strip()
  if'PACKAGE_PIN'in values:expected_pins[port]=values['PACKAGE_PIN']
actual={x['port']:x['package_pin']for x in rows('ports.tsv')};assert expected_pins and all(actual.get(k)==v for k,v in expected_pins.items()),[(k,v,actual.get(k))for k,v in expected_pins.items()if actual.get(k)!=v]
assert all(sha(Path(k))==h for k,h in pins.items());assert sha(checkpoint)==before
artifacts={str(f.relative_to(o)):sha(f)for f in o.rglob('*')if f.is_file()and f.name!='result.json'}
result=dict(status='PASS_V004_EXACT_CONSTRAINTS_ON_V002_SYNTH_CDC_TOPOLOGY_NOT_V004_RTL_OR_ROUTED_SIGNOFF',checkpoint_sha256=before,lcd_first_stage_exact_fanout=6,legal_C_D_endpoints=counts,direct_bound_path_count=len(paths),segmentation=dict(selected_starts='All52primitiveFDclockC; destinationD; timedstart/endsets_exact',native_exposed_properties=segmentation_properties,native_segmentation_warnings=0,scope='Selecteddirectboundpathsverified; no assertion about unseenoptimized/routedfuturepaths'),SDRAM_setup_requirement_ns=12.625,SDRAM_hold_requirement_ns=2.625,SDRAM_capture_endpoints=16,multicycle_commands=multi,no_hold_relaxation=True,expected_package_pins_verified=len(expected_pins),thread_count=1,source_binding_sha256=sha(o/'source-binding.json'),all_build_sources_unchanged=True,frozen_v36_integration_unchanged=True,exact_bundle_C_D_counts=dict(address=[12,12],response=[32,32]),DCP_source_version='v002_old_stager',selected_constraint_version='v004',V004_RTL_qualification=False,routed_qualification=False,BIT=False,hardware=False,artifacts=artifacts)
(o/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(status=result['status'],result_sha256=sha(o/'result.json'),checkpoint_sha256=before,endpoint_counts=counts,SDRAM_requirements=req,package_pins=len(expected_pins)),indent=2))
