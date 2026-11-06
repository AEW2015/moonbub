"""Isolate explicit CU71/DY71 local profile selection; never alter sealed v35."""
from pathlib import Path
import argparse,hashlib,json,shutil
a=argparse.ArgumentParser();a.add_argument('--source',type=Path,required=True);a.add_argument('--output',type=Path,required=True);args=a.parse_args()
source=args.source.resolve();out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source/'evidence/build-manifest.json')=='6213ad182c99b82cb08c3d8c3e3ad8004eb1287e3c6d85cbb2f42536ac5445de'
snapshot=json.loads((source/'evidence/source-snapshot-v004.json').read_text())
for name,h in snapshot['files'].items():
 assert sha(source/name)==h,name
 p=out/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source/name,p)
(out/'evidence').mkdir();(out/'provenance').mkdir()
for name in['build-manifest.json','source-snapshot-v004.json']:
 shutil.copyfile(source/'evidence'/name,out/'provenance'/('parent-v35-'+name))
shutil.copyfile(source/'evidence/hud.def',out/'evidence/hud.def')
shutil.copytree(source/'licenses',out/'licenses')
for name in['review_source.py','target_retry.py','host_check.py','package_release.py']:
 text=(source/name).read_text().replace('v35-cu71-local-fixture-20261105','v36-dual-local-fixture-20261106').replace('source-snapshot-v004','source-snapshot-v001').replace('target-{action}-v004','target-{action}-v001').replace('C:/mv35a','C:/mv36a').replace('V35_SOURCE_MATCH','V36_SOURCE_MATCH')
 if name=='host_check.py':text=text.replace('v007','v001').replace('12 passed','18 passed').replace("'tests':12","'tests':18").replace('PASS12','PASS18')
 if name=='package_release.py':
  text=text.replace("parent=p.parent/'v34-cu66-hud-20261105'","parent=p.parent/'v35-cu71-local-fixture-20261105'").replace('release-cu71-local-fixture-v002','release-dual-local-fixture-v001').replace("'CU71_G':12288","'CU71_G_or_DY71_Y':12288").replace('LAB_ONLY_CU71_FIXED_KEY_P','LAB_ONLY_EXPLICIT_CU71_G_DY71_Y_FIXED_KEY_P')
 (out/name).write_text(text,newline='\n')

def change(name,old,new):
 p=out/name;text=p.read_text();assert text.count(old)==1,(name,old);p.write_text(text.replace(old,new),newline='\n')
local='handheld/src/cu66/local.rs'
change(local,'pub const MAGIC:u32=0x43553731;pub const ABI:u32=0x10000;', '''pub const MAGIC:u32=0x43553731;pub const ABI:u32=0x10000;
#[derive(Debug,Clone,Copy,PartialEq,Eq)]pub enum Profile{Cu71,Dy71}
impl Profile{
 pub const fn magic(self)->u32{match self{Self::Cu71=>0x43553731,Self::Dy71=>0x44593731}}
 pub const fn capabilities(self)->u32{match self{Self::Cu71=>7,Self::Dy71=>15}}
}''')
change(local,"struct Driver<'a,B:Bus>{bus:","struct Driver<'a,B:Bus>{profile:Profile,bus:")
change(local,'self.r(0)?!=MAGIC||self.r(4)?!=ABI||self.r(8)?!=7','self.r(0)?!=self.profile.magic()||self.r(4)?!=ABI||self.r(8)?!=self.profile.capabilities()')
change(local,'pub fn run<B:Bus>(bus:&mut B,hud:&mut Hud)->Result<(Report,Completed),Error>{','''pub fn run<B:Bus>(bus:&mut B,hud:&mut Hud)->Result<(Report,Completed),Error>{run_with_profile(bus,hud,Profile::Cu71)}
pub fn run_with_profile<B:Bus>(bus:&mut B,hud:&mut Hud,profile:Profile)->Result<(Report,Completed),Error>{''')
change(local,'Driver{bus,sequence:0','Driver{profile,bus,sequence:0')
change(local,'d.r(0)?!=MAGIC||d.r(4)?!=ABI||d.r(8)?!=7','d.r(0)?!=d.profile.magic()||d.r(4)?!=ABI||d.r(8)?!=d.profile.capabilities()')
usb='handheld/src/cu66/local_usb.rs'
change(usb,'struct Spawn;','struct Spawn{profile:local::Profile}')
change(usb,'fn spawn_empty(&mut self)->Result<Self::Sender,()>{let(tx,rx)', 'fn spawn_empty(&mut self)->Result<Self::Sender,()>{let profile=self.profile;let(tx,rx)')
change(usb,'worker(p);REQUESTS.finished();','worker(p,profile);REQUESTS.finished();')
change(usb,'pub fn start(){let(free,largest)=heap();','''pub fn start(){start_profile(local::Profile::Cu71)}
pub fn start_direct(){start_profile(local::Profile::Dy71)}
fn start_profile(profile:local::Profile){log::info!("USB_CU71_LOCAL requested_profile={:?} network_capability=false",profile);let(free,largest)=heap();''')
change(usb,'&mut Spawn);','&mut Spawn{profile});')
change(usb,'fn worker(mut guard:MaintenanceGuard){','fn worker(mut guard:MaintenanceGuard,profile:local::Profile){')
change(usb,'let result=local::run(&mut io,&mut hud);','let result=local::run_with_profile(&mut io,&mut hud,profile);')
change(usb,'let succeeded=result.is_ok();','let succeeded=result.is_ok();log::info!("USB_CU71_LOCAL completed_profile={:?} success={}",profile,succeeded);')
change('handheld/src/usb_test.rs',"        b'G' => crate::cu66::local_usb::start(),","        b'G' => crate::cu66::local_usb::start(),\n        b'Y' => crate::cu66::local_usb::start_direct(),")
change('handheld/src/diag_pages.rs','v35-cu71-local-fixture-20261105','v36-dual-local-fixture-20261106')

tests='tests/local.rs'
change(tests,'magic:u32,ack:u32','magic:u32,caps:u32,read_contentions:u32,write_contentions:u32,ack:u32')
change(tests,'magic:local::MAGIC,ack:0','magic:local::MAGIC,caps:7,read_contentions:0,write_contentions:0,ack:0')
change(tests,'self.tick();Ok(match o','self.tick();if self.read_contentions!=0{self.read_contentions-=1;return Err(Error::Contended)}Ok(match o')
change(tests,'8=>7,','8=>self.caps,')
change(tests,'self.tick();self.physical_writes+=1;','self.tick();if self.write_contentions!=0{self.write_contentions-=1;return Err(Error::Contended)}self.physical_writes+=1;')
with(out/tests).open('a',newline='\n')as f:f.write('''
fn dy_fake()->Fake{let mut b=Fake::new();b.magic=local::Profile::Dy71.magic();b.caps=local::Profile::Dy71.capabilities();b}
fn run_dy(b:&mut Fake)->Result<(local::Report,local::Completed),Error>{let mut h=hud::Hud::new(131072).unwrap();local::run_with_profile(b,&mut h,local::Profile::Dy71)}
#[test]fn dy71_actual_native_key_p_all_words(){let mut b=dy_fake();let(r,_)=run_dy(&mut b).unwrap();assert_eq!((r.accepted,r.presented,r.words_written,r.words_verified),(2,2,42240,42240));assert_eq!(b.drains,2);}
#[test]fn cu71_refuses_dy71_before_writes(){let mut b=dy_fake();assert!(matches!(run(&mut b),Err(Error::Identity)));assert_eq!(b.physical_writes,0);}
#[test]fn dy71_refuses_cu71_before_writes(){let mut b=Fake::new();assert!(matches!(run_dy(&mut b),Err(Error::Identity)));assert_eq!(b.physical_writes,0);}
#[test]fn dy71_refuses_wrong_capability_before_writes(){let mut b=dy_fake();b.caps=7;assert!(matches!(run_dy(&mut b),Err(Error::Identity)));assert_eq!(b.physical_writes,0);}
#[test]fn transient_device_contention_is_retried(){let mut b=dy_fake();b.read_contentions=8;b.write_contentions=8;let(r,_)=run_dy(&mut b).unwrap();assert_eq!(r.presented,2);assert_eq!((b.read_contentions,b.write_contentions),(0,0));}
#[test]fn permanent_contention_has_deadline_without_writes(){let mut b=dy_fake();b.read_contentions=u32::MAX;assert!(matches!(run_dy(&mut b),Err(Error::Deadline)));assert_eq!(b.physical_writes,0);}
''')
(out/'README.md').write_text('''# V36 explicit local CU71 / DY71 fixture firmware

Development successor of sealed v35, not installed. `G` selects only CU71
magic43553731/cap7. New `Y` selects only DY71 magic44593731/cap15. Both require
ABI00010000, fresh typed owner/staging counters, real original HU/native decode,
all21120 HUD word writes/readbacks per frame and real COMMIT/presentation.
There is no profile autodetection, identity alias, new network transport or FPS
claim. Wrong profiles are refused before writes. The one-shot worker retains
accepted native cache and maintenance lease after completion/mutation exactly
as v35; confirmed paired reset/reconfiguration is required before reuse.

Native CPU W, JPEG/AV, settings/SD and default firmware features are retained.
The SDK/exception/PSRAM profile is unchanged. Shared G/Y worker stack12288bytes
and heap gate170000/largest24576 are unchanged. Target build, SRAM, source/image
review, real CSR integration and physical gates must finish before flashing.
''',newline='\n')
changed={name:sha(out/name)for name in snapshot['files']if sha(out/name)!=snapshot['files'][name]}
(out/'provenance/derivation.json').write_text(json.dumps(dict(status='DERIVED_UNBUILT_UNINSTALLED',parent_manifest_sha256=sha(source/'evidence/build-manifest.json'),
 parent_source_sha256=sha(source/'evidence/source-snapshot-v004.json'),changed_selected_sources=changed,
 profile_commands={'G':{'magic':'43553731','abi':'00010000','capabilities':7},'Y':{'magic':'44593731','abi':'00010000','capabilities':15}},
 network_CU66=False,hardware=False),indent=2)+'\n')
assert all(sha(source/n)==h for n,h in snapshot['files'].items())
print(json.dumps(dict(output=str(out),changed_source_files=len(changed),hardware=False)))
