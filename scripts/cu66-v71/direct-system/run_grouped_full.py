"""Same DY71 full-system tests with isolated grouped memory-source binding."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';group=d/'grouped-v001';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['component-fast01','component-slow01','fairness01']:assert (group/'evidence'/name/'result.json').exists(),name
manifest=group/'sources.json'
if not manifest.exists():
 m=json.loads((d/'sources.json').read_text());m['sources']=[(group/'source'/Path(n).name).relative_to(r).as_posix()if Path(n).name in ['cu71_memory_system_direct.sv','cu71_word_bridge_direct.sv','cu71_tile_memory_direct.sv','moonshine_sdram_burst.sv']else n for n in m['sources']];m['sources_sha256']={n:sha(r/n)for n in m['sources']};m['scope']='DY718:4groupedphysicalscheduleronly;grace18LCD/4BG,controller/map/codec/baseownerunchanged;functional/performanceexperimentnotHWrelease';manifest.write_text(json.dumps(m,indent=2)+'\n')
def wrap(text):
 names={'group_lcd_count':'group_lcd_accepted','group_bg_count':'group_bg_accepted','group_idle':'group_reserved_idle','group_lcd_idle':'group_lcd_reserved_idle','group_bg_idle':'group_bg_reserved_idle','group_lcd_expiry':'group_lcd_expiry','group_bg_expiry':'group_bg_expiry','group_bg_wait':'group_bg_max_wait'}
 text=text.replace('output wire [31:0] rgb_completed_writes\n','output wire [31:0] rgb_completed_writes,\n    output wire [31:0] '+','.join(names)+',group_lcd_wait\n')
 binds=''.join(' assign '+name+'=hardware.memory.bridge.'+target+';\n'for name,target in names.items())+' assign group_lcd_wait=hardware.memory.lcd_max_wait;\n'
 return text.replace('endmodule',binds+'endmodule')
def instrument(text):
 text=text.replace('<<" processor_commit_calls="<<soft_calls<<std::endl;','<<" processor_commit_calls="<<soft_calls<<" group_LCD="<<d.group_lcd_count<<" group_BG="<<d.group_bg_count<<" reserved_idle="<<d.group_idle<<" LCD_idle="<<d.group_lcd_idle<<" BG_idle="<<d.group_bg_idle<<" LCD_expiry="<<d.group_lcd_expiry<<" BG_expiry="<<d.group_bg_expiry<<" LCD_maxwait="<<d.group_lcd_wait<<" BG_maxwait="<<d.group_bg_wait<<std::endl;')
 text=text.replace('<<" physical_fps_proven=0"','<<" group_LCD="<<s.d.group_lcd_count<<" group_BG="<<s.d.group_bg_count<<" reserved_idle="<<s.d.group_idle<<" LCD_maxwait="<<s.d.group_lcd_wait<<" BG_maxwait="<<s.d.group_bg_wait<<" physical_fps_proven=0"')
 return text
script=Path(__file__).with_name('run.py');source=script.read_text().replace("m=json.loads((d/'sources.json').read_text())","m=json.loads((d/'grouped-v001/sources.json').read_text())")
source=source.replace("(o/'cu71_direct_system_sim.sv').write_text(header+body,newline='\\n')","(o/'cu71_direct_system_sim.sv').write_text(wrap(header+body),newline='\\n')")
source=source.replace(" s=s.replace('int main(','int run(')"," if kind=='frames':s=instrument(s)\n s=s.replace('int main(','int run(')")
source=source.replace("d/'sources.json',Path(__file__).resolve()","d/'sources.json',d/'grouped-v001/sources.json',script,Path(__file__).resolve()")
exec(compile(source,str(script),'exec'),globals())
