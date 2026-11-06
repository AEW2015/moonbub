"""Frozen v71 actual-controller system control and chronological KEY/P replay.

No Vivado or hardware. Native HUD semantic CPU service is outside HDL time.
"""
from pathlib import Path
import argparse,hashlib,json,os,re,shlex,subprocess,time

p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--frames',type=int,default=2)
p.add_argument('--flight',type=float,default=.757);p.add_argument('--access',type=float,default=2.223);p.add_argument('--hold',type=float,default=2.223)
p.add_argument('--distro',default='MRS-HDL-Research');p.add_argument('--control-only',action='store_true');p.add_argument('--sanitize',action='store_true')
p.add_argument('--manifest',type=Path);p.add_argument('--map',type=Path);a=p.parse_args()
assert 1<=a.frames<=20
root=Path(__file__).resolve().parents[3];old=root/'fpga/experiments/cu66-v70/system';mem=root/'fpga/experiments/cu66-v71/memory'
out=Path(a.output).resolve();out.mkdir(parents=True,exist_ok=False)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
linux=lambda f:'/mnt/'+f.resolve().drive[0].lower()+f.resolve().as_posix()[2:]
selected_manifest=json.loads(a.manifest.read_text())if a.manifest else None
if selected_manifest:
 assert selected_manifest['SIMULATION'] is False
 for n,h in selected_manifest['sources_sha256'].items():assert sha(root/n)==h,n
hardware_top=selected_manifest['top']if selected_manifest else'cu71_system'
map_dir=a.map.resolve()if a.map else root/'fpga/experiments/cu66-v70/memory'
# Actual component pin model retains the Icarus-qualified zero-delay version.
component=mem/'evidence/lookahead-fast01'
model=(component/'model.sv').read_text()
assert model.count('#0;')==1
model=model.replace('#0;', '''// Explicit Verilator compatibility variant:1ps monitor scheduling step.
 // Functional commands/DQ scheduling unchanged; Icarus counterpart uses#0.
 #0.001;''')
(out/'model-verilator.sv').write_text(model,newline='\n')
wrapper=(old/'cu70_system_sim.sv').read_text().replace('module cu70_system_sim','module cu71_system_sim')
wrapper=wrapper.replace(' cu70_system #(', ' '+hardware_top+' #(')
wrapper=wrapper.replace(' cu70_sdram_model #(.REFRESH_CYCLES(REFRESH_CYCLES)) model(.reset(rst),',
 f' sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS({a.access:.3f}),.CLOCK_FLIGHT_NS({a.flight:.3f}),.T_OH_NS({a.hold:.3f})) model(')
assert 'cu70_sdram_model' not in wrapper
(out/'cu71_system_sim.sv').write_text(wrapper,newline='\n')

def cpp(kind):
 name='test_control.cpp'if kind=='control'else'tb_system.cpp'
 text=(old/name).read_text().replace('Vcu70_system_sim','Vcu71_system_sim')
 text=text.replace('#include "../../../../experiments/cu66-native-v69/decoder.hpp"','#include "'+linux(root/'experiments/cu66-native-v69/decoder.hpp')+'"')
 text=text.replace('#include "../../cu66-v69/hud-partition/hud_gate.hpp"','#include "'+linux(root/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp')+'"')
 text=text.replace('#include "../memory/memory_map.hpp"','#include "'+linux(map_dir/'memory_map.hpp')+'"')
 text=text.replace('t+2750','t+2625').replace('t+7750','t+7625')
 if kind=='control':
  text=text.replace('before+1','before+8').replace('before+2','before+16')
 text=text.replace('int main(', 'int run(')
 # Only main has implicit success return. A renamed function must return0.
 assert text.count('}catch(const std::exception&e)')==1
 text=text.replace('}catch(const std::exception&e)', 'return 0;}catch(const std::exception&e)')
 pos=text.index('static void need')
 return text[:pos]+'\nnamespace '+kind+' {\n'+text[pos:]+'\n}\n'
cpp_text=cpp('control')+'\n'+cpp('frames')+'''
int main(int argc,char**argv){
 if(argc>1&&std::string(argv[1])=="--control")return control::run(argc-1,argv+1);
 if(argc>1&&std::string(argv[1])=="--frames")return frames::run(argc-1,argv+1);
 return 2;
}
'''
(out/'tb.cpp').write_text(cpp_text,newline='\n')
spec=json.loads((old/'sources.json').read_text())
replacement={
 'fpga/experiments/cu66-v70/system/cu70_system_sim.sv':out/'cu71_system_sim.sv',
 'fpga/experiments/cu66-v70/system/cu70_system.sv':root/'fpga/experiments/cu66-v71/system/cu71_system.sv',
 'fpga/experiments/cu66-v70/memory/cu70_tile_memory.sv':mem/'cu71_tile_memory.sv',
 'fpga/experiments/cu66-v70/memory/cu70_word_bridge.sv':mem/'cu71_word_bridge.sv',
 'fpga/experiments/cu66-v70/memory/cu70_memory_system.sv':mem/'cu71_memory_system.sv',
 'fpga/experiments/cu66-v70/memory/cu70_sdram_controller.sv':mem/'moonshine_sdram_burst.sv',
 'fpga/experiments/cu66-v70/memory/cu70_sdram_model.sv':out/'model-verilator.sv',
 'fpga/experiments/cu66-v70/display/cu70_scanout.sv':root/'fpga/experiments/cu66-v71/display/cu71_scanout_prefetch.sv',
 'fpga/experiments/cu66-v70/display/cu70_lcd_lines.sv':root/'fpga/experiments/cu66-v71/display/cu71_lcd_lines.sv'}
rtl=[replacement.get(n,root/n)for n in spec['rtl_sources']]+[component/'primitives.sv']
if selected_manifest:
 rtl=[root/n for n in selected_manifest['sources']]+[out/'cu71_system_sim.sv',out/'model-verilator.sv',component/'primitives.sv']
 spec['include_dirs']=selected_manifest['include_dirs']
# Copy every compiled RTL dependency, preserving relative paths for exact provenance.
inputs=out/'inputs';inputs.mkdir()
compiled=[];origins={}
for f in rtl:
 target=inputs/f.relative_to(root);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(f.read_bytes())
 compiled.append(target);origins[f.relative_to(root).as_posix()]=sha(f)
native=root/'experiments/cu66-native-v69';index=native/'index.tsv'
fixtures=[native/line.split('\t')[2]for line in index.read_text().splitlines()[:a.frames]]
headers=[map_dir/'memory_map.hpp',map_dir/'cu70_memory_map.svh',root/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',root/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',root/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',*native.glob('*.hpp'),index,*fixtures]
if a.manifest:headers.append(a.manifest.resolve())
for f in headers:origins[f.relative_to(root).as_posix()]=sha(f)
origins[Path(__file__).relative_to(root).as_posix()]=sha(Path(__file__))
(out/'source-freeze.json').write_text(json.dumps(origins,indent=2)+'\n')
(out/'simulation-scope.json').write_text(json.dumps({'SIMULATION_define':False,'memory_clock_period_ps':10000,'read_phase_degrees':274.5,'model_monitor_compatibility':'One#0monitor scheduling changedto#0.001nsforVerilator; exact#0componentpassesIcarus separately.2stateunknownchecksnotindependentXproof.','model_source_sha256':sha(component/'model.sv'),'model_variant_sha256':sha(out/'model-verilator.sv'),'flight_ns':a.flight,'access_ns':a.access,'hold_ns':a.hold,'HUD':'ActualnativeC++HudGateonoriginalpacketbytes; typedsidebands, CPUtimeoutsideHDL; notESP32orHC70wireproof'},indent=2)+'\n')
commands=[]
def run(label,argv,timeout):
 t=time.monotonic()
 with(out/(label+'.log')).open('wb')as f:q=subprocess.run(argv,cwd=root,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 commands.append({'label':label,'command':argv,'returncode':q.returncode,'seconds':time.monotonic()-t,'log_sha256':sha(out/(label+'.log'))})
 (out/'execution.json').write_text(json.dumps(commands,indent=2)+'\n')
 print(label,q.returncode,flush=True)
 assert q.returncode==0,(label,out/(label+'.log'))
 return(out/(label+'.log')).read_text()
def wsl(argv):
 return['wsl','-d',a.distro,'--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; '+shlex.join(argv)]
build=out/'build'
sanitize=' -fsanitize=address,undefined -fno-omit-frame-pointer -g'if a.sanitize else''
args=['verilator','--cc','--exe','--build','-j','2','--timing','--assert','--Wall','-Wno-fatal','-Wno-BLKSEQ','-Wno-PINCONNECTEMPTY','--top-module','cu71_system_sim','-GUSE_STRIP=1','--Mdir',linux(build),'-CFLAGS','-O1 -std=c++20'+sanitize]
if a.sanitize:args+=['-LDFLAGS','-fsanitize=address,undefined']
args +=['-I'+linux(map_dir),*['-I'+linux(root/d)for d in spec['include_dirs']],*[linux(f)for f in compiled],linux(out/'tb.cpp')]
run('build',wsl(args),1800)
exe=build/'Vcu71_system_sim'
control=run('control',wsl([linux(exe),'--control',linux(fixtures[0])]),600)
assert 'SYSTEM_CONTROL_PASS' in control and 'FAIL'not in control
if not a.control_only:
 frames=run('frames',wsl([linux(exe),'--frames',linux(index),str(a.frames)]),5400)
 assert 'SYSTEM_PASS complete_frames='+str(a.frames)in frames and 'FAIL'not in frames
for n,h in origins.items():assert sha(root/n)==h,('Sourcechanged',n)
(out/'result.json').write_text(json.dumps({'status':'PASS_CONTROL_ONLY'if a.control_only else'PASS_FUNCTIONAL_KEY_P_CANONICAL_HUD_RGB_READBACK','frames':0 if a.control_only else a.frames,'hardware':False,'routed_timing':False,'cadence':'Mustreadactualunderruncounters; descriptorACKisnotcleanpresentation','source_freeze_sha256':sha(out/'source-freeze.json'),'limits':['NativeHUDCPUtimeoutsideHDL','ImmutablepacketbyteportnotliveQSPI','Verilator1psmonitorcompatibilityand2state semantics','Notfullframeclean30fpsorESP32fit']},indent=2)+'\n')
