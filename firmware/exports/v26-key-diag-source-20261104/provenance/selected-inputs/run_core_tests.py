"""Host-only production-core tests and compiler ownership rejections."""
from pathlib import Path
import hashlib,json,subprocess,re
P=Path(__file__).resolve().parent;O=P/'evidence';RUSTC=str(Path.home()/'.cargo/bin/rustc.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parent_guard():
 d=json.loads((P/'parent-v25.json').read_text());base=Path(d['origin'])
 assert sha(base/'evidence/manifest.json')==d['manifest_sha256']
 for rel,h in d['sources'].items():assert sha(base/rel)==h,rel
 for rel,row in d['artifacts'].items():assert sha(base/rel)==row['sha256'],rel
 return {'source_inputs':len(d['sources']),'artifacts':len(d['artifacts']),'manifest_sha256':d['manifest_sha256'],'status':'PASS'}
def main():
 guard=parent_guard();exe=O/'key-diag-tests.exe';command=[RUSTC,'+stable','--edition=2021','--test',str(P/'tests/key_diag_core.rs'),'-o',str(exe)]
 r=subprocess.run(command,capture_output=True,text=True);(O/'core-compile.log').write_text(r.stdout+r.stderr);r.check_returncode()
 r=subprocess.run([str(exe),'--nocapture','--test-threads=1'],capture_output=True,text=True);(O/'core-tests.log').write_text(r.stdout+r.stderr);r.check_returncode()
 match=re.search(r'test result: ok\. (\d+) passed; 0 failed',r.stdout);assert match
 header='\n'.join(f'#[path="{(P/"handheld/src"/name).as_posix()}"]mod {name[:-3]};' for name in ['core_admission.rs','key_diag_core.rs'])+'\nuse core_admission::*;use key_diag_core::*;\n'
 setups={
 'manager':'let x=CoreAdmission::new(1);',
 'video':'let mut a=CoreAdmission::new(1);let x=a.reserve_video().unwrap();',
 'av':'let mut a=CoreAdmission::new(1);let x=a.reserve_av().unwrap();',
 'program':'let mut a=CoreAdmission::new(1);let x=a.reserve_program().unwrap();',
 'diagnostic':'let mut a=CoreAdmission::new(1);let x=a.reserve_diagnostic().unwrap();',
 'core':'let mut a=CoreAdmission::new(1);let p=a.reserve_diagnostic().unwrap();let x=DiagnosticCore::new(p,0,0,Budgets::default());',
 'operation':'let mut a=CoreAdmission::new(1);let p=a.reserve_diagnostic().unwrap();let mut c=DiagnosticCore::new(p,0,0,Budgets::default());let x=c.next_operation(0).unwrap();',
 'exit_proof':'let mut a=CoreAdmission::new(1);let p=a.reserve_diagnostic().unwrap();let mut c=DiagnosticCore::new(p,0,0,Budgets::default());let op=c.next_operation(0).unwrap();c.complete(op,Outcome::Read(0),0,0);let(_,x,_)=c.into_exit().unwrap();',
 }
 cases=[]
 setups['authorization']='let mut a=CoreAdmission::new(1);let mut p=a.reserve_program().unwrap();let x=p.authorize_call().unwrap();'
 for name,setup in setups.items():
  cases.extend([(name+'-move',setup+'let moved=x;let reused=x;drop((moved,reused));','E0382'),(name+'-clone',setup+'let copied=x.clone();drop(copied);','E0599')])
 cases.extend([
  ('authorization-one-use','let mut a=CoreAdmission::new(1);let mut p=a.reserve_program().unwrap();let auth=p.authorize_call().unwrap();let call=auth.begin().unwrap();call.succeeded();let _again=auth.begin();','E0382'),
  ('authorization-exclusive-borrow','let mut a=CoreAdmission::new(1);let mut p=a.reserve_program().unwrap();let auth=p.authorize_call().unwrap();let again=p.authorize_call();let call=auth.begin();drop((again,call));','E0499'),
  ('release-consumes-program','let mut a=CoreAdmission::new(1);let p=a.reserve_program().unwrap();a.release_program(p,ProgramFinish::NoSideEffects).unwrap();let _=p.id();','E0382'),
  ('core-consumes-diagnostic','let mut a=CoreAdmission::new(1);let p=a.reserve_diagnostic().unwrap();let _c=DiagnosticCore::new(p,0,0,Budgets::default());let _=p.id();','E0382'),
  ('release-consumes-video','let mut a=CoreAdmission::new(1);let p=a.reserve_video().unwrap();a.begin_video_drain(&p).unwrap();a.release_video(p,VideoDrain{worker_joined:true,receivers_closed:true,local_cleanup_complete:true}).unwrap();let _=p.id();','E0382'),
  ('release-consumes-av','let mut a=CoreAdmission::new(1);let v=a.reserve_video().unwrap();a.activate_video(&v).unwrap();let p=a.reserve_av().unwrap();a.begin_av_drain(&p).unwrap();a.release_av(p,AvDrain{session_cleared:true,feeder_idle:true,io_drained:true,power_restored:true}).unwrap();let _=p.id();','E0382'),
 ])
 negatives=[]
 for name,body,expected in cases:
  src=O/(name+'.rs');src.write_text(header+'fn main(){'+body+'}\n');cmd=[RUSTC,'+stable','--edition=2021',str(src),'-o',str(O/(name+'.exe'))]
  r=subprocess.run(cmd,capture_output=True,text=True);log=r.stdout+r.stderr;(O/(name+'.log')).write_text(log)
  assert r.returncode!=0 and expected in log,(name,r.returncode,log)
  negatives.append({'case':name,'expected_error':expected,'source_sha256':sha(src),'command':cmd,'status':'EXPECTED_REJECTION'})
 source_hashes={str(p.relative_to(P)).replace('\\','/'):sha(p) for folder in ['handheld','handheld-dfu','tests','tools'] for p in(P/folder).rglob('*')if p.is_file()and not any(x in p.parts for x in ['target','__pycache__'])}
 main=(P/'handheld/src/main.rs').read_text();assert 'mod core_admission' in main and 'mod key_diag_core' in main
 for name in ['core_admission.rs','key_diag_core.rs']:
  text=(P/'handheld/src'/name).read_text();assert not any(x in text for x in ['esp_idf_svc','Device::','std::sync','Vec<','String','Box<','thread::'])
 result={'status':'HOST_PASS_STAGE_ONLY','tests':int(match[1]),'compiler_rejections':negatives,'parent_guard':parent_guard(),'source_hashes':source_hashes,'target_build':'NOT_RUN_PENDING_REVIEW','SDK_adapters':'SOURCE_IMPLEMENTED_TARGET_NOT_RUN','hardware_actions':'NONE','scope':'Production source/adapters connected. Host instances and fake I/O are not target ABI, physical exclusion/drain or stack evidence.'}
 (O/'core-results.json').write_text(json.dumps(result,indent=2)+'\n');print('HOST_PASS',match[1],'tests;',len(negatives),'expected compiler rejections; parent unchanged; SDK source connected, target pending review')
if __name__=='__main__':main()
