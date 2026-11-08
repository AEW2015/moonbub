"""One-time V44 source derivation; never builds, flashes or modifies V43."""
from pathlib import Path
import hashlib, json

p=Path(__file__).resolve().parents[1]
f=p/'handheld/src/cu66/network_driver.rs'
s=f.read_text()
assert 'pub const MAX_FRAMES' not in s
s=s.replace('//! Two network-supplied CU66 frames through unchanged scalar DY71 control semantics.', '//! Explicit bounded three-frame lab driver; original pair remains run() control.')
s=s.replace('pub const MAGIC:', 'pub const MAX_FRAMES:usize=3;\npub const MAGIC:',1)
s=s.replace('[u64;2]','[u64;MAX_FRAMES]')
s=s.replace('pub allocator:[usize;6],', 'pub allocator:[usize;6],pub hud_pending_us:[u64;MAX_FRAMES],pub hud_snapshot_us:[u64;MAX_FRAMES],pub hu_extract_start_us:[u64;MAX_FRAMES],pub hu_extract_done_us:[u64;MAX_FRAMES],pub native_start_us:[u64;MAX_FRAMES],pub native_done_us:[u64;MAX_FRAMES],pub hu_extract_commands:[u32;MAX_FRAMES],')
old='pub fn run<B:Bus,S:Source>(bus:&mut B,hud:&mut Hud,source:&mut S)->Result<(Report,Completed),Error>{'
assert old in s
s=s.replace(old,old+'\n run_sequence(bus,hud,source,2)\n}\npub fn run_sequence<B:Bus,S:Source>(bus:&mut B,hud:&mut Hud,source:&mut S,frame_count:usize)->Result<(Report,Completed),Error>{\n if frame_count==0||frame_count>MAX_FRAMES{return Err(Error::Bounds)}')
s=s.replace('=[0;2]', '=[0;MAX_FRAMES]')
s=s.replace(' for index in 0..2{', ' let mut hud_pending_us=[0;MAX_FRAMES];let mut hud_snapshot_us=[0;MAX_FRAMES];let mut hu_extract_start_us=[0;MAX_FRAMES];let mut hu_extract_done_us=[0;MAX_FRAMES];let mut native_start_us=[0;MAX_FRAMES];let mut native_done_us=[0;MAX_FRAMES];let mut hu_extract_commands=[0;MAX_FRAMES];\n for index in 0..frame_count{')
s=s.replace('  let h=d.hud_request()?;', '  hud_pending_us[index]=d.bus.now();\n  let h=d.hud_request()?;hud_snapshot_us[index]=d.bus.now();')
s=s.replace('  for pos in(0..h.length).step_by(4){', '  hu_extract_start_us[index]=d.bus.now();\n  for pos in(0..h.length).step_by(4){hu_extract_commands[index]+=1;')
s=s.replace('  wire[..4].copy_from_slice(b"HC70");', '  hu_extract_done_us[index]=d.bus.now();\n  wire[..4].copy_from_slice(b"HC70");')
s=s.replace('  let start=d.bus.now();let response=ok(hud,&wire,&mut out)?;cpu[index]=d.bus.now().saturating_sub(start);', '  let start=d.bus.now();native_start_us[index]=start;let response=ok(hud,&wire,&mut out)?;native_done_us[index]=d.bus.now();cpu[index]=native_done_us[index].saturating_sub(start);')
s=s.replace('Report{frames:2,', 'Report{frames:frame_count as u32,')
s=s.replace('allocator:hud.stats().map_err(|_|Error::Hud)?,', 'allocator:hud.stats().map_err(|_|Error::Hud)?,hud_pending_us,hud_snapshot_us,hu_extract_start_us,hu_extract_done_us,native_start_us,native_done_us,hu_extract_commands,')
f.write_text(s)
# Explicit new invocation profile, unchanged byte-level lab framing and fail-held lifecycle.
f=p/'handheld/src/cu66/network_usb.rs';s=f.read_text().replace('frames=2','frames=3').replace('profile=DY71_ABI2_BULK','profile=DY71_ABI2_BULK_LAB3').replace('network_driver::run(&mut io,&mut hud,&mut source)', 'network_driver::run_sequence(&mut io,&mut hud,&mut source,3)');f.write_text(s)
base=Path('C:/moon/dev/experiments/cu66-native-v69')
m=json.loads((base/'manifest.json').read_text())
case=next(c for c in m['cases'] if c['scene']=='mass-effect-10000')
row=next(r for r in case['rows'] if r['id']==2)
packet=base/row['packet']['path'];b=packet.read_bytes()
assert hashlib.sha256(b).hexdigest()==row['packet']['sha256']
(p/'handheld/src/cu66/fixtures/packet2.cu66').write_bytes(b)
(p/'parent-v43-and-third-fixture.json').write_text(json.dumps({'parent':'v43-dy71-bulk-hud-20261107','fixture':row,'source_manifest_sha256':hashlib.sha256((base/'manifest.json').read_bytes()).hexdigest()},indent=2)+'\n')
print('V44_SOURCE_PREPARED',len(b),row['packet']['sha256'])
