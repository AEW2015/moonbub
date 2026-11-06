"""Source-pinned safe DY71 CSR/stager on explicitly selected validpipe/SYNCsafe RTL.

Native HUD/SDK execution is a separate next gate. This run posts no invented
HUD_RESULT, HUD_DRAIN or SOFTWARE_ACK and leaves post-HUD abort owned/pending.
The same executable also offers the existing stdin/stdout CSR RPC server.
"""
from pathlib import Path
import argparse,hashlib,json,shlex,shutil,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--build-only',action='store_true');a=p.parse_args()
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-system/final-local-v008';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();lin=lambda f:'/mnt/'+f.resolve().drive[0].lower()+f.resolve().as_posix()[2:]
selection=r/'fpga/experiments/cu66-v71/direct-system/final-integration-v008/sources.json';m=json.loads(selection.read_text());assert m['SIMULATION']is False and m['top']=='cu71_system_final_v008'
for n,h in m['sources_sha256'].items():assert sha(r/n)==h,n
proof=selection.with_name('derivation.json');proof_data=json.loads(proof.read_text())
assert sha(selection)=='15cc325a837720ae4f54dbb98b30d457d76271f416b7ef1576c198a68fde4b69'
for field in ['parent_core_manifest','owner_source','event_patch']:
 assert sha(r/proof_data[field])==proof_data[field+'_sha256'],field
parent=r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/qualification-v001.json';assert json.loads(parent.read_text())['status']=='PASS_ISOLATED_SAFETY_FUNCTIONAL_GATE_TIMING_UNMEASURED'
for name,h in json.loads(parent.read_text())['sources_sha256'].items():assert sha(r/name)==h,name
derivation=json.loads((d/'derivation.json').read_text());assert sha(selection)==derivation['selected_manifest_sha256'];assert sha(d/'dy71_platform_sim.sv')==derivation['wrapper_sha256'];assert sha(r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/dy71_local_control_safe.sv')==derivation['control_sha256'];assert sha(r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/cu71_packet_staging_safe.sv')==derivation['stager_sha256'];assert sha(d/'model-verilator.sv')==derivation['model_sha256']
rtl=[r/n for n in m['sources']]+[r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/dy71_local_control_safe.sv',r/'fpga/experiments/cu66-v71/staging-timing/safety-v002/cu71_packet_staging_safe.sv',r/'fpga/experiments/cu66-v71/system/cu71_packet_arbiter.sv',d/'dy71_platform_sim.sv',d/'model-verilator.sv',r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01/primitives.sv']
pins={};compiled=[]
for f in rtl:
    dest=o/'inputs'/f.relative_to(r);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);pins[str(f)]=sha(f);compiled.append(dest)
includes=[]
for n in m['include_dirs']:
    dest=o/'inputs'/n;dest.mkdir(parents=True,exist_ok=True);includes.append(dest)
    for f in(r/n).glob('*.svh'):shutil.copy2(f,dest/f.name);pins[str(f)]=sha(f)
shutil.copy2(d/'driver.cpp',o/'driver.cpp');pins[str(d/'driver.cpp')]=sha(d/'driver.cpp')
native=r/'experiments/cu66-native-v69';index=native/'index.tsv';packet=native/index.read_text().splitlines()[0].split('\t')[2];shutil.copy2(packet,o/'key.cu66');assert packet.stat().st_size<=49152
for f in[packet,index,parent,selection,proof,d/'derivation.json',Path(__file__)]:pins[str(f)]=sha(f)
(o/'source-freeze.json').write_text(json.dumps(dict(originals=pins,compiled={str(f.relative_to(o)):sha(f)for f in compiled},headers={str(f.relative_to(o)):sha(f)for inc in includes for f in inc.glob('*.svh')},packet=dict(path=str(packet),sha256=sha(packet),bytes=packet.stat().st_size),wrapper=dict(path=str(d/'dy71_platform_sim.sv'),sha256=sha(d/'dy71_platform_sim.sv')),watchdog_unsigned_cycles=3000000000,profile=dict(magic='44593731',abi='00010000',capabilities='0000000f'),hardware=False),indent=2)+'\n')
steps=[]
def run(label,command,timeout=1800):
    start=time.monotonic()
    with(o/(label+'.log')).open('wb')as f:q=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    steps.append(dict(label=label,command=command,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o)
def wsl(command):return['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && '+shlex.join(command)]
cmd=['verilator','--cc','--exe','--build','-j','2','--timing','--assert','--Wall','-Wno-fatal','-Wno-BLKSEQ','-Wno-PINCONNECTEMPTY','--top-module','dy71_platform_sim','--Mdir',lin(o/'build'),'-CFLAGS','-O1 -std=c++20','-LDFLAGS','-lz',*['-I'+lin(f)for f in includes],*[lin(f)for f in compiled],lin(o/'driver.cpp')]
run('build',wsl(cmd),2400)
if a.build_only:print('BUILD_ONLY_NO_FUNCTIONAL_PASS');raise SystemExit(0)
run('control',wsl([lin(o/'build/Vdy71_platform_sim'),'--control',lin(o/'key.cu66')]),600)
text=(o/'control.log').read_text();assert 'DY71_LOCAL_CSR_PASS'in text and 'DY71_LOCAL_CSR_FAIL'not in text
assert 'no_fake_ACK=1 pending_actual_native_ABORT=1'in text
assert all(sha(Path(n))==h for n,h in pins.items())
(o/'result.json').write_text(json.dumps(dict(status='PASS_ACTUAL_DY71_LOCAL_CSR_STAGING_ABORT_AND_SDRAM_HUD_READBACK',source_freeze_sha256=sha(o/'source-freeze.json'),profile_magic='0x44593731',profile_abi='0x00010000',capabilities='0x0f',full_native_HUD_key_P='NEXT_GATE_NOT_RUN',physical_SPI=False,hardware=False,BIT=False,scope='Actual explicitly selected finalv008 owner/groupedbackend/safeCSR/safeStager/arbiter/qualifiedSDRAMpins; typedCSRrequests. No native semantic success was fabricated. Final post-HUDabort remains waiting actualnativeABORTack and prevents reuse.',report=text),indent=2)+'\n');print('DY71_LOCAL_CSR_PASS_NO_NATIVE_HUD_OR_HARDWARE_CLAIM')
