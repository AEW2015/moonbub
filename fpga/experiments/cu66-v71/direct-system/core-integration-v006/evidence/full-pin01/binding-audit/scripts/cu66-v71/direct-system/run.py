"""Source-frozen DY71 control then actual-controller chronological KEY/P replay."""
from pathlib import Path
import argparse,hashlib,json,shlex,subprocess,time
p=argparse.ArgumentParser();p.add_argument('--output',required=True);p.add_argument('--frames',type=int,default=2);p.add_argument('--control-only',action='store_true');p.add_argument('--flight',type=float,default=.757);p.add_argument('--access',type=float,default=2.223);p.add_argument('--hold',type=float,default=2.223);a=p.parse_args();assert 1<=a.frames<=3
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';old=r/'fpga/experiments/cu66-v70/system';mem=r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01';maps=r/'fpga/experiments/cu66-v70/memory';o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();lin=lambda f:'/mnt/'+f.resolve().drive[0].lower()+f.resolve().as_posix()[2:]
m=json.loads((d/'sources.json').read_text())
for n,h in m['sources_sha256'].items():assert sha(r/n)==h,n
model=(mem/'model.sv').read_text();assert model.count('#0;')==1;model=model.replace('#0;','// Explicit1psmonitorcompatibility forVerilator; exactIcarusmodel retained.\n #0.001;');(o/'model-verilator.sv').write_text(model,newline='\n')
top=(d/'cu71_system_direct.sv').read_text();header=top[:top.index(');')+2].replace('module cu71_system_direct','module cu71_direct_system_sim').replace('POWERUP_CYCLES=20000','POWERUP_CYCLES=20')
idx=header.index('    output wire [12:0] sdram_a');header=header[:idx]+'''    input logic [23:0] peek_address,output logic [15:0] peek_data,
    output logic [31:0] model_writes,model_reads,model_refreshes,model_acts,model_pres,
    output logic [31:0] write_event_sequence,output logic [23:0] write_event_address,output logic [15:0] write_event_data,
    output wire [31:0] rgb_completed_writes
);
'''
legacy=(old/'cu70_system_sim.sv').read_text();body=legacy[legacy.index(' wire[12:0] sdram_a'):].replace(' cu70_system #(',' cu71_system_direct #(').replace('.USE_STRIP(USE_STRIP),','')
body=body.replace(' cu70_sdram_model #(.REFRESH_CYCLES(REFRESH_CYCLES)) model(.reset(rst),',f' sdram_model_burst #(.MEM_WORDS(16777216),.T_AC_NS({a.access:.3f}),.CLOCK_FLIGHT_NS({a.flight:.3f}),.T_OH_NS({a.hold:.3f})) model(')
body=body.replace('endmodule',' assign rgb_completed_writes=hardware.memory.rgb_completed_writes;\nendmodule');(o/'cu71_direct_system_sim.sv').write_text(header+body,newline='\n')
def cpp(kind):
 name='test_control.cpp'if kind=='control'else'tb_system.cpp';s=(old/name).read_text().replace('Vcu70_system_sim','Vcu71_direct_system_sim')
 s=s.replace('#include "../../../../experiments/cu66-native-v69/decoder.hpp"','#include "'+lin(r/'experiments/cu66-native-v69/decoder.hpp')+'"').replace('#include "../../cu66-v69/hud-partition/hud_gate.hpp"','#include "'+lin(r/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp')+'"').replace('#include "../memory/memory_map.hpp"','#include "'+lin(maps/'memory_map.hpp')+'"')
 s=s.replace('t+2750','t+2625').replace('t+7750','t+7625').replace('d.painter_busy','d.cache_prepare_busy').replace('d.painter_error_code','d.error_code').replace('d.painter_error','d.cache_prepare_fault').replace('d.painter_cycles','d.cache_prepare_cycles')
 if kind=='control':s=s.replace('before+1','before+8').replace('before+2','before+16')
 else:
  # Independent native planes remain the oracle; only physical address lookup
  # changes to the explicitly versioned tile-major storage profile.
  oldpeek='auto w=peek(base+off+i);';assert oldpeek in s
  s=s.replace(oldpeek,"unsigned width=a?360:720,x=(i*2)%width,y=(i*2)/width;unsigned addr=base+off+((y/8)*(width/8)+x/8)*32+(y%8)*4+(x%8)/2;auto w=peek(addr);")
  start=s.index('  // Candidate RGB slot remains bound');end=s.index('\n }\n void run(',start)
  s=s[:start]+'''  need(d.rgb_completed_writes==0,"DY71 emitted RGB burst write");
  need(d.profile_magic==0x44593731&&d.profile_abi==0x10000&&d.profile_capabilities==15,"DY71 profile identity");
'''+s[end:]
  start=s.index('if(d.write_event_sequence!=last_write_sequence)');end=s.index('if(rising)pixel_check();',start);s=s[:start]+s[end:]
  s=s.replace('RGB_words_per_frame=384000','RGB_reads_or_writes=0').replace('painter_cycles=','cache_prepare_cycles=')
 s=s.replace('int main(','int run(');assert s.count('}catch(const std::exception&e)')==1;s=s.replace('}catch(const std::exception&e)','return 0;}catch(const std::exception&e)');at=s.index('static void need');return s[:at]+'\nnamespace '+kind+' {\n'+s[at:]+'\n}\n'
tb=cpp('control')+'\n'+cpp('frames')+'''int main(int argc,char**argv){
 if(argc>1&&std::string(argv[1])=="--control")return control::run(argc-1,argv+1);
 if(argc>1&&std::string(argv[1])=="--frames")return frames::run(argc-1,argv+1);
 return 2;
}
''';(o/'tb.cpp').write_text(tb,newline='\n')
rtl=[r/n for n in m['sources']]+[o/'cu71_direct_system_sim.sv',o/'model-verilator.sv',mem/'primitives.sv'];compiled=[];pins={};inputs=o/'inputs'
for f in rtl:
 dest=inputs/f.relative_to(r);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(f.read_bytes());compiled.append(dest);pins[f.relative_to(r).as_posix()]=sha(f)
native=r/'experiments/cu66-native-v69';index=native/'index.tsv';fixtures=[native/line.split('\t')[2]for line in index.read_text().splitlines()[:a.frames]]
for f in [maps/'memory_map.hpp',maps/'cu70_memory_map.svh',r/'fpga/experiments/cu66-v69/packet/cu66_profile.svh',r/'fpga/experiments/cu66-v69/inverse/cu66_quant_rom.svh',r/'fpga/experiments/cu66-v69/hud-partition/hud_gate.hpp',*native.glob('*.hpp'),index,*fixtures,d/'sources.json',Path(__file__).resolve()]:pins[f.relative_to(r).as_posix()]=sha(f)
(o/'source-freeze.json').write_text(json.dumps(pins,indent=2)+'\n');commands=[]
def run(label,args,timeout):
 cmd=['wsl','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment; '+shlex.join(args)];start=time.monotonic()
 with(o/(label+'.log')).open('wb')as f:q=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 commands.append({'label':label,'command':cmd,'returncode':q.returncode,'seconds':time.monotonic()-start,'log_sha256':sha(o/(label+'.log'))});(o/'execution.json').write_text(json.dumps(commands,indent=2)+'\n');print(label,q.returncode,flush=True);assert q.returncode==0,(label,o);return(o/(label+'.log')).read_text()
b=o/'build';args=['verilator','--cc','--exe','--build','-j','2','--timing','--assert','--Wall','-Wno-fatal','-Wno-BLKSEQ','-Wno-PINCONNECTEMPTY','--top-module','cu71_direct_system_sim','--Mdir',lin(b),'-CFLAGS','-O1 -std=c++20']+['-I'+lin(r/n)for n in m['include_dirs']]+[lin(f)for f in compiled]+[lin(o/'tb.cpp')]
run('build',args,1800);exe=b/'Vcu71_direct_system_sim';ct=run('control',[lin(exe),'--control',lin(fixtures[0])],600);assert 'SYSTEM_CONTROL_PASS' in ct
if not a.control_only:
 ft=run('frames',[lin(exe),'--frames',lin(index),str(a.frames)],5400);assert 'SYSTEM_PASS complete_frames='+str(a.frames) in ft
for n,h in pins.items():assert sha(r/n)==h,n
(o/'result.json').write_text(json.dumps({'status':'PASS_CONTROL_ONLY'if a.control_only else'PASS_FUNCTIONAL_DY71_KEY_P_CANONICAL_HUD_AND_LCD','frames':0 if a.control_only else a.frames,'hardware':False,'routed_timing':False,'RGB_traffic':False,'profile_magic':'0x44593731','canonical_layout':'tile_major64','display_slots':'cache_context','cadence':'Exactorwholeblackline scoring;inspectunderrunsseparately. No30fpsclaim.','scope':'ActualqualifiedBL8controllermodel;actualnativeHUDsemanticserviceoutsideHDLtime;1psVerilatormonitorcompatibility. NoESP/liveQSPI/CSR/networkproof.','source_freeze_sha256':sha(o/'source-freeze.json')},indent=2)+'\n')
