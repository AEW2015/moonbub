"""Fail-closed DY71 routed-image audit/eligibility/emitter. Never accesses hardware.

Default mode qualifies only; audit is read-only native Vivado. Emit requires a
previous exact eligibility document and explicit signed internal root review.
No report-only build or positive unplaced slack alone authorizes an image.
"""
from pathlib import Path
import argparse,datetime,hashlib,json,os,re,shutil,struct,subprocess,time

ROOT=Path(__file__).resolve().parents[2]
PART='xc7a100tcsg324-1';TOP='moonshine_top_dy71';IDENTITY=0x44593731
BUILD_FILES=['execution.json','source-freeze.json','selection.json','executed-builder.py','executed.tcl',
 'console.log','vivado.log','synthesized.dcp','constrained.dcp','placed.dcp','routed.dcp',
 'placed-timing-summary.rpt','placed-setup-paths.rpt','timing-summary.rpt','setup-paths.rpt',
 'hold-paths.rpt','utilization.rpt','route-status.rpt','drc.rpt','cdc.rpt','exceptions.rpt',
 'clock-interaction.rpt','bus-skew.rpt','check-timing.rpt','exceptions-postsynth.rpt',
 'cdc-postsynth.rpt','check-timing-postsynth.rpt','synthesized-clocks.rpt','synthesized-utilization.rpt']
AUDIT_FILES=['execution.json','binding.json','executed.tcl','console.log','vivado.log','routed-input.dcp',
 'identity.tsv','bitstream-properties.tsv','native-drc.tsv','drc-uncapped.rpt',
 'timing-summary.rpt','route-status.rpt','cdc.rpt','exceptions.rpt','clock-interaction.rpt',
 'bus-skew.rpt','check-timing.rpt']
REVIEW_CHECKS=['cdc','io_sdram','bus_skew','exceptions_and_coverage','clock_reset',
 'functional_source_binding','application_profile_binding','warnings_and_drc',
 'manual_handoff_integrity']

def require(ok,message):
 if not ok:raise ValueError(message)
def sha(p):
 p=Path(p);require(p.is_file()and p.stat().st_size>0,'Missing/empty artifact: '+str(p))
 return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
def artifact_map(base,names):return {n:sha(base/n)for n in names}
def native_clean(base):
 for name in ('console.log','vivado.log'):
  require(not re.search(r'^\s*ERROR:',(base/name).read_text(),re.M),'Native ERROR in '+str(base/name))
def timing_metrics(text):
 require('Fully Routed'in text,'Timing report is not Fully Routed')
 match=re.search(r'\n\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+\d+\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+\d+\s+(-?[\d.]+)\s+(-?[\d.]+)\s+(\d+)\s+\d+\s*\n',text)
 require(match is not None,'Unrecognized global timing table')
 wns,tns,nsetup,whs,ths,nhold,pulse,tpws,npulse=map(float,match.groups())
 require(min(wns,whs,pulse)>0,'Nonpositive global routed setup/hold/pulse slack')
 require(tns==ths==tpws==0 and nsetup==nhold==npulse==0,'Global timing violations')
 return dict(wns_ns=wns,whs_ns=whs,wpws_ns=pulse)
def route_metrics(text):
 def number(label):
  m=re.search(r'# of '+re.escape(label)+r'\.+\s*:\s*(\d+)\s*:',text)
  require(m is not None,'Missing route count '+label);return int(m[1])
 routable=number('routable nets');fully=number('fully routed nets');errors=number('nets with routing errors')
 require(routable>0 and fully==routable and errors==0,'Incomplete/error routing')
 return dict(routable=routable,fully_routed=fully,routing_errors=errors)
def build_binding(build,selection,expected):
 require(sha(selection)==expected,'Selection does not match explicit expected SHA256')
 s=load(selection)
 require(s['part']==PART and s['top']==TOP,'Wrong target')
 require(s['UID_USR_ACCESS']==s['CSR_magic']=='0x44593731'and s['ABI']=='0x00010000'and s['capabilities']=='0x0f','Wrong DY71 profile')
 require(s['BUILD_ALLOWED']is True and s['SIMULATION']is False and s['clock_IO_SDRAM_budget_changes']is False,'Wrong selection gate')
 require(s['BIT_ALLOWED']is False and s['PROGRAM_ALLOWED']is False,'Report-only parent selection expected; image review is separate')
 require(sha(build/'selection.json')==expected,'Build selection differs')
 artifacts=artifact_map(build,BUILD_FILES);execution=load(build/'execution.json')
 require(execution['status']=='REPORTS_COMPLETE_NOT_TIMING_QUALIFIED'and execution['returncode']==0 and execution['completion_marker']and execution['required_reports_present'],'Build is incomplete')
 require(execution['selection_sha256']==expected and not execution['native_error_lines'],'Build native-error/selection gate')
 native_clean(build)
 pins={}
 for category in('sources_sha256','headers_sha256','constraints_sha256'):
  for name,h in s[category].items():
   require(name not in pins or pins[name]==h,'Inconsistent source maps');pins[name]=h
 require(set(s['sources'])==set(s['sources_sha256'])and len(s['sources'])==len(set(s['sources'])),'Duplicate/missing source')
 require(load(build/'source-freeze.json')==pins,'Build source freeze is not exact selected map')
 for name,h in pins.items():
  require((ROOT/name).resolve().is_relative_to(ROOT)and(build/'inputs'/name).resolve().is_relative_to(build/'inputs'),'Source map escapes expected tree')
  require(sha(build/'inputs'/name)==h,'Frozen build input changed: '+name)
  require(sha(ROOT/name)==h,'Live source/header/constraint changed: '+name)
 guards=s['native_guard_references']
 for name,h in guards.items():require(sha(ROOT/name)==h,'Source/proof reference changed: '+name)
 timing=timing_metrics((build/'timing-summary.rpt').read_text());routes=route_metrics((build/'route-status.rpt').read_text())
 require(not re.search(r'\|\s*[^|]+\|\s*Error\s*\|',(build/'drc.rpt').read_text()),'Reported build DRC Error')
 return dict(selection_sha256=expected,build=str(build),artifacts_sha256=artifacts,source_freeze=pins,
  native_guard_references=guards,profile=dict(part=PART,top=TOP,USERID='44593731',USR_ACCESS='44593731',ABI='00010000',capabilities='0f'),timing=timing,routes=routes)
def tcl_path(p):
 text=Path(p).resolve().as_posix();require(not any(c in text for c in '{}\n\r'),'Unsupported Tcl path')
 return '{'+text+'}'
def native_script(build,out,emit=False):
 # No PLL/route/constraint changes and no hardware API. DRC MAX_MESSAGES only.
 text='''set_param general.maxThreads 2
open_checkpoint @DCP@
set out @OUT@
if {[get_property PART [current_design]] ne "xc7a100tcsg324-1" || [get_property NAME [current_design]] ne "moonshine_top_dy71"} {error "Wrong DY71 design/part"}
foreach key {BITSTREAM.CONFIG.USERID BITSTREAM.CONFIG.USR_ACCESS} {
 set value [get_property $key [current_design]]
 if {![string is entier -strict $value] || $value != 0x44593731} {error "Wrong DY71 image identity at $key: $value"}
}
set f [open [file join $out identity.tsv] w]
foreach key {NAME PART BITSTREAM.CONFIG.USERID BITSTREAM.CONFIG.USR_ACCESS} {puts $f "$key\t[get_property $key [current_design]]"}
close $f
set f [open [file join $out bitstream-properties.tsv] w]
foreach key [lsort [list_property [current_design]]] {if {[string match BITSTREAM.* $key]} {puts $f "$key\t[get_property $key [current_design]]"}}
close $f
foreach type {max min} {
 set paths [get_timing_paths -delay_type $type -max_paths 1]
 if {[llength $paths] != 1 || [get_property SLACK $paths] <= 0} {error "Nonpositive routed slack"}
}
foreach check [get_drc_checks] {if {[lsearch -exact [list_property $check] MAX_MESSAGES]>=0} {set_property MAX_MESSAGES 100000 $check}}
report_drc -no_waivers -file [file join $out drc-uncapped.rpt]
set f [open [file join $out native-drc.tsv] w]
set errors 0
foreach violation [get_drc_violations] {
 set severity [get_property SEVERITY $violation]
 puts $f "$violation\t$severity"
 if {[string equal -nocase $severity Error]} {incr errors}
}
puts $f "ERROR_COUNT\t$errors"
close $f
if {$errors != 0} {error "Native unwaived DRC errors"}
report_timing_summary -delay_type min_max -report_unconstrained -file [file join $out timing-summary.rpt]
report_route_status -file [file join $out route-status.rpt]
report_cdc -details -file [file join $out cdc.rpt]
report_exceptions -coverage -file [file join $out exceptions.rpt]
report_clock_interaction -file [file join $out clock-interaction.rpt]
report_bus_skew -file [file join $out bus-skew.rpt]
check_timing -verbose -file [file join $out check-timing.rpt]
@WRITE@
close_design
puts @MARKER@
'''
 return text.replace('@DCP@',tcl_path(out/'routed-input.dcp')).replace('@OUT@',tcl_path(out)).replace('@WRITE@','write_bitstream [file join $out moonbub-dy71.bit]'if emit else '# Read-only native audit: no image write').replace('@MARKER@','DY71_IMAGE_EMITTED_NO_HARDWARE'if emit else'DY71_NATIVE_READONLY_AUDIT_COMPLETE_NO_BIT')
def run_native(build,out,binding,emit):
 shutil.copyfile(build/'routed.dcp',out/'routed-input.dcp')
 require(sha(out/'routed-input.dcp')==binding['artifacts_sha256']['routed.dcp'],'Copied DCP differs before operation')
 dump(out/'binding.json',binding);(out/'executed.tcl').write_text(native_script(build,out,emit),newline='\n')
 # Native Windows workaround: short unique private temp; never edit machine env.
 tmp=Path('C:/vtmp')/('dyimg-'+str(time.time_ns()));tmp.mkdir(parents=True,exist_ok=False)
 cmd=['C:/Xilinx/2025.2/Vivado/bin/vivado.bat','-mode','batch','-source',str(out/'executed.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou')]
 start=time.monotonic()
 with(out/'console.log').open('w')as log:q=subprocess.run(cmd,cwd=out,stdout=log,stderr=subprocess.STDOUT,env=dict(os.environ,TEMP=str(tmp),TMP=str(tmp)))
 dump(out/'execution.json',dict(command=cmd,returncode=q.returncode,seconds=time.monotonic()-start,hardware=False,emission_requested=emit,private_TEMP_TMP=str(tmp)))
 require(q.returncode==0,'Native audit/image operation failed');native_clean(out)
 marker='DY71_IMAGE_EMITTED_NO_HARDWARE'if emit else'DY71_NATIVE_READONLY_AUDIT_COMPLETE_NO_BIT'
 require(marker in(out/'console.log').read_text(),'Missing native completion marker')
 require(sha(build/'routed.dcp')==binding['artifacts_sha256']['routed.dcp'],'Routed DCP changed during operation')
 require(sha(out/'routed-input.dcp')==binding['artifacts_sha256']['routed.dcp'],'Private DCP changed during operation')
def audit_binding(audit,binding):
 require(load(audit/'binding.json')==binding,'Audit bound to different build/source/report snapshot')
 e=load(audit/'execution.json');require(e['returncode']==0 and e['hardware']is False and e['emission_requested']is False,'Wrong/failed audit execution')
 native_clean(audit);require('DY71_NATIVE_READONLY_AUDIT_COMPLETE_NO_BIT'in(audit/'console.log').read_text(),'Audit completion missing')
 require((audit/'executed.tcl').read_text()==native_script(Path(binding['build']),audit,False),'Audit script not exact guarded read-only writer')
 require(sha(audit/'routed-input.dcp')==binding['artifacts_sha256']['routed.dcp'],'Audit used a different DCP')
 timing_metrics((audit/'timing-summary.rpt').read_text());route_metrics((audit/'route-status.rpt').read_text())
 inventory=(audit/'native-drc.tsv').read_text().splitlines()
 require(inventory.count('ERROR_COUNT\t0')==1 and not any(x.split('\t')[-1].lower()=='error'for x in inventory),'Native uncapped DRC Error')
 props=dict(line.split('\t',1)for line in(audit/'identity.tsv').read_text().splitlines())
 require(props['NAME']==TOP and props['PART']==PART and int(props['BITSTREAM.CONFIG.USERID'],0)==int(props['BITSTREAM.CONFIG.USR_ACCESS'],0)==IDENTITY,'Native audit identity mismatch')
 require(bool((audit/'bitstream-properties.tsv').read_text().strip()),'Missing bitstream property inventory')
 return artifact_map(audit,AUDIT_FILES)
def root_review(review,expected,binding,audit,artifacts,emission=False):
 require(sha(review)==expected,'Root review differs from explicit hash')
 v=load(review);require(v['schema']=='DY71_FINAL_IMAGE_REVIEW_V1','Wrong review schema')
 signer=v['reviewer'];require(signer['role']=='root-integration'and signer['identity']not in('',None,'UNSIGNED'),'Root reviewer identity absent')
 datetime.datetime.strptime(signer['signed_utc'],'%Y-%m-%dT%H:%M:%SZ')
 require(v['selection_sha256']==binding['selection_sha256']and v['build_artifacts_sha256']==binding['artifacts_sha256'],'Review build/selection mismatch')
 require(v['audit_artifacts_sha256']==artifacts and v['audit_directory']==str(audit),'Review audit mismatch')
 require(v['selected_sources_sha256']==binding['source_freeze'],'Review source coverage not bound')
 require(v['no_unresolved_findings']is True,'Unresolved root review findings')
 for key in REVIEW_CHECKS:
  check=v['checks'][key]
  require(check['status']=='PASS_REVIEWED'and len(check['findings'].strip())>=12 and check['evidence'],'Missing root content review: '+key)
  for item in check['evidence']:require(sha(Path(item['path']))==item['sha256'],'Changed review evidence: '+item['path'])
 require(v['c_check_handoff']=='UNAVAILABLE_MANUAL_INTEGRITY_REVIEW','Do not invent external handoff-tool PASS')
 require(v['limits']and v['physical_playback_qualified']is False,'Required qualification limits absent')
 if emission:require(v['image_emission_authorized']is True,'Root image emission not explicitly selected')
 return v
def parse_bit(path):
 data=Path(path).read_bytes();pos=0
 def take(n):
  nonlocal pos
  require(pos+n<=len(data),'Truncated BIT');v=data[pos:pos+n];pos+=n;return v
 def n16():return int.from_bytes(take(2),'big')
 take(n16());require(n16()==1 and take(1)==b'a','Unrecognized BIT header')
 header={}
 for key in('a','b','c','d'):
  if key!='a':require(take(1)==key.encode(),'BIT header field order')
  header[key]=take(n16()).rstrip(b'\0').decode('ascii')
 require(take(1)==b'e','Missing BIT payload');payload=take(int.from_bytes(take(4),'big'));require(pos==len(data),'Trailing BIT data')
 require(header['b']=='7a100tcsg324','Wrong BIT package/device')
 require(header['a'].split(';')[0]==TOP and 'COMPRESS=TRUE'in header['a'].split(';'),'Wrong BIT top/compression property')
 uid=re.search(r'(?:^|;)UserID=(?:0[xX])?([0-9A-Fa-f]+)(?:;|$)',header['a']);require(uid is not None and int(uid[1],16)==IDENTITY,'Wrong BIT header USERID')
 sync=payload.find(bytes.fromhex('aa995566'));require(sync>=0 and (len(payload)-sync)%4==0,'Missing/misaligned configuration sync')
 words=struct.unpack('>'+str((len(payload)-sync)//4)+'I',payload[sync:]);writes={};i=1;last=None
 while i<len(words):
  word=words[i];i+=1;typ=word>>29
  if typ==1:
   opcode=(word>>27)&3;reg=(word>>13)&0x3fff;count=word&0x7ff;last=(opcode,reg)
  elif typ==2:
   require(last is not None,'Type2 without Type1');opcode,reg=last;count=word&0x7ffffff
  elif word in(0,0xffffffff):continue
  else:raise ValueError('Unrecognized configuration packet before FDRI')
  if opcode==2:
   require(i+count<=len(words),'Truncated configuration write')
   if reg==2 and count:break # compressed frame data is not parsed as packet headers.
   if count:writes.setdefault(reg,[]).append(list(words[i:i+count]))
   i+=count
  else:require(opcode==0 and count==0,'Unexpected read/reserved packet in programming BIT')
 require(writes.get(13)==[[IDENTITY]],'BIT USR_ACCESS/AXSS register mismatch')
 require(writes.get(12)==[[0x03631093]],'BIT configuration IDCODE mismatch for7a100t')
 return dict(header=header,USR_ACCESS_hex='44593731',IDCODE_hex='03631093',scope='Header USERID and pre-FDRI configuration writes; payload integrity bound by final BIT SHA256, no physical programming')
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--mode',choices=['audit','template','qualify','emit'],default='qualify')
 p.add_argument('--build',required=True,type=Path);p.add_argument('--selection',required=True,type=Path);p.add_argument('--selection-sha256',required=True)
 p.add_argument('--output',required=True,type=Path);p.add_argument('--audit',type=Path);p.add_argument('--review',type=Path);p.add_argument('--review-sha256')
 p.add_argument('--qualification',type=Path);p.add_argument('--qualification-sha256');a=p.parse_args()
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);shutil.copyfile(__file__,out/'executed-helper.py')
 try:
  build=a.build.resolve();selection=a.selection.resolve();binding=build_binding(build,selection,a.selection_sha256)
  if a.mode=='audit':
   run_native(build,out,binding,False);artifacts=audit_binding(out,binding)
   dump(out/'audit-hashes.json',artifacts);print('DY71_READONLY_AUDIT_COMPLETE_NO_IMAGE');return
  require(a.audit is not None,'--audit required');audit=a.audit.resolve();artifacts=audit_binding(audit,binding)
  if a.mode=='template':
   template=dict(schema='DY71_FINAL_IMAGE_REVIEW_V1',reviewer=dict(identity='UNSIGNED',role='root-integration',signed_utc=None),selection_sha256=binding['selection_sha256'],build_artifacts_sha256=binding['artifacts_sha256'],audit_directory=str(audit),audit_artifacts_sha256=artifacts,selected_sources_sha256=binding['source_freeze'],checks={k:dict(status='INCOMPLETE',findings='',evidence=[])for k in REVIEW_CHECKS},no_unresolved_findings=False,image_emission_authorized=False,c_check_handoff='UNAVAILABLE_MANUAL_INTEGRITY_REVIEW',physical_playback_qualified=False,limits=['No hardware playback/30fps/analog PVT or MTBF qualification.'])
   dump(out/'root-review-TEMPLATE.json',template);print('UNSIGNED_REVIEW_TEMPLATE_NOT_ELIGIBLE');return
  require(a.review is not None and a.review_sha256,'Hash-pinned internal root review required')
  review=a.review.resolve();root_review(review,a.review_sha256,binding,audit,artifacts,a.mode=='emit')
  qualification=dict(status='PASS_DY71_IMAGE_ELIGIBILITY_NOT_HARDWARE',binding=binding,audit=str(audit),audit_artifacts_sha256=artifacts,review=str(review),review_sha256=a.review_sha256,hardware=False,physical_playback_qualified=False)
  if a.mode=='qualify':dump(out/'qualification.json',qualification);print('DY71_ELIGIBLE_NO_BIT_WRITTEN');return
  require(a.qualification is not None and a.qualification_sha256,'Explicit prior qualification and SHA required for emission')
  require(sha(a.qualification)==a.qualification_sha256 and load(a.qualification)==qualification,'Prior exact qualification changed')
  run_native(build,out,binding,True)
  # Recheck all proof/report/review/DCP hashes after native operation.
  require(build_binding(build,selection,a.selection_sha256)==binding,'Build changed during emission')
  require(audit_binding(audit,binding)==artifacts,'Read-only audit changed during emission')
  root_review(review,a.review_sha256,binding,audit,artifacts,True)
  require((out/'bitstream-properties.tsv').read_bytes()==(audit/'bitstream-properties.tsv').read_bytes(),'BITSTREAM properties differ from reviewed DCP audit')
  timing_metrics((out/'timing-summary.rpt').read_text());route_metrics((out/'route-status.rpt').read_text())
  require('ERROR_COUNT\t0\n'in(out/'native-drc.tsv').read_text(),'Final native DRC Error')
  info=parse_bit(out/'moonbub-dy71.bit');dump(out/'bit-properties.json',info);dump(out/'qualification.json',qualification)
  files=[x for x in out.iterdir()if x.is_file()]
  imagehash={x.name:sha(x)for x in files};dump(out/'image-hashes.json',imagehash)
  dump(out/'handoff-manifest.json',dict(overall='INCOMPLETE',artifacts=[dict(role='programming_image'if n.endswith('.bit')else'evidence',path=n,sha256=h)for n,h in imagehash.items()],checks=dict(image=dict(status='pass',evidence='bit-properties.json'),routed_timing=dict(status='pass',evidence='timing-summary.rpt'),hardware=dict(status='incomplete',evidence='qualification.json')),scope='Qualified image generated; no hardware action or physical playback claim. c_check_handoff unavailable; manual integrity review required.'))
  print('DY71_BIT_GENERATED_NOT_PROGRAMMED')
 except Exception as exc:
  dump(out/'failure.json',dict(status='INCOMPLETE_NO_IMAGE_AUTHORIZATION',mode=a.mode,error=type(exc).__name__+': '+str(exc),hardware=False,possible_partial_unqualified_BIT=(out/'moonbub-dy71.bit').exists()))
  raise
if __name__=='__main__':main()
