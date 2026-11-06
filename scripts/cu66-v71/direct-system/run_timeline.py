"""Matched DY71 native control/KEY/P/P with noninvasive identity timeline."""
from pathlib import Path
import sys
grouped='--grouped'in sys.argv
if grouped:sys.argv.remove('--grouped')
script=Path(__file__).with_name('run.py');source=script.read_text()
def wrap(text):
 if not grouped:return text
 names={'group_lcd_count':'group_lcd_accepted','group_bg_count':'group_bg_accepted','group_idle':'group_reserved_idle','group_lcd_idle':'group_lcd_reserved_idle','group_bg_idle':'group_bg_reserved_idle','group_lcd_expiry':'group_lcd_expiry','group_bg_expiry':'group_bg_expiry','group_bg_wait':'group_bg_max_wait'}
 text=text.replace('output wire [31:0] rgb_completed_writes\n','output wire [31:0] rgb_completed_writes,\n    output wire [31:0] '+','.join(names)+',group_lcd_wait\n');binds=''.join(' assign '+n+'=hardware.memory.bridge.'+v+';\n'for n,v in names.items())+' assign group_lcd_wait=hardware.memory.lcd_max_wait;\n';return text.replace('endmodule',binds+'endmodule')
def instrument(text):
 fields=r'''
 unsigned timeline_stage=999,timeline_presented=0;
 uint64_t timeline_visible_generation=0,timeline_raster_generation=0;
 unsigned timeline_raster_lines=0,timeline_raster_black=0;bool timeline_raster=false;
 void timeline_cycle(){
  if(unsigned(d.stage)!=timeline_stage){std::cout<<"DY71_STAGE cycle="<<cycles<<" generation="<<d.active_generation<<" fid="<<d.active_frame_id<<" stage="<<unsigned(d.stage)<<std::endl;timeline_stage=d.stage;}
  if(d.lcd_presented_count!=timeline_presented){std::cout<<"DY71_PRESENTED cycle="<<cycles<<" generation="<<d.lcd_front_generation<<" fid="<<d.lcd_front_frame_id<<" count="<<d.lcd_presented_count<<std::endl;timeline_presented=d.lcd_presented_count;}
 }
'''
 text=text.replace(' void pixel_check(){',fields+' void pixel_check(){')
 old='unsigned x=d.physical_x,y=d.physical_y;need(x<480&&y<800,"physical raster bounds");';assert old in text
 text=text.replace(old,old+r'''
  if(x==0&&y==0){timeline_raster=true;timeline_raster_generation=d.lcd_front_generation;timeline_raster_lines=timeline_raster_black=0;}
  if(timeline_raster)need(d.lcd_front_generation==timeline_raster_generation,"generation changed inside tracked raster");
  if(x==0&&y==40&&timeline_visible_generation!=d.lcd_front_generation){timeline_visible_generation=d.lcd_front_generation;std::cout<<"DY71_FIRST_CANVAS cycle="<<cycles<<" generation="<<d.lcd_front_generation<<" fid="<<d.lcd_front_frame_id<<std::endl;}
''')
 old='if(line_matches==480)good_lines++;else black_lines++;';assert old in text
 text=text.replace(old,old+r'''
   if(timeline_raster){timeline_raster_lines++;timeline_raster_black+=line_matches!=480;if(y==799){need(timeline_raster_lines==800,"tracked incomplete raster");std::cout<<"DY71_RASTER cycle="<<cycles<<" generation="<<timeline_raster_generation<<" fid="<<d.lcd_front_frame_id<<" lines="<<timeline_raster_lines<<" black_lines="<<timeline_raster_black<<std::endl;timeline_raster=false;}}
''')
 text=text.replace('cycles++;\n  if(e.packet_rsp)', 'cycles++;timeline_cycle();\n  if(e.packet_rsp)')
 text=text.replace('<<" cycles="<<cycles-begin<<" actual_writes="','<<" cycles="<<cycles-begin<<" ack_cycle="<<cycles<<" actual_writes="')
 if grouped:
  text=text.replace('<<" processor_commit_calls="<<soft_calls<<std::endl;','<<" processor_commit_calls="<<soft_calls<<" group_LCD="<<d.group_lcd_count<<" group_BG="<<d.group_bg_count<<" reserved_idle="<<d.group_idle<<" LCD_idle="<<d.group_lcd_idle<<" BG_idle="<<d.group_bg_idle<<" LCD_timer_expiry="<<d.group_lcd_expiry<<" BG_timer_expiry="<<d.group_bg_expiry<<" LCD_maxwait="<<d.group_lcd_wait<<" BG_maxwait="<<d.group_bg_wait<<std::endl;')
  text=text.replace('<<" physical_fps_proven=0"','<<" group_LCD="<<s.d.group_lcd_count<<" group_BG="<<s.d.group_bg_count<<" reserved_idle="<<s.d.group_idle<<" LCD_maxwait="<<s.d.group_lcd_wait<<" BG_maxwait="<<s.d.group_bg_wait<<" physical_fps_proven=0"')
 return text
if grouped:source=source.replace("m=json.loads((d/'sources.json').read_text())","m=json.loads((d/'grouped-v001/sources.json').read_text())")
source=source.replace("(o/'cu71_direct_system_sim.sv').write_text(header+body,newline='\\n')","(o/'cu71_direct_system_sim.sv').write_text(wrap(header+body),newline='\\n')")
source=source.replace(" s=s.replace('int main(','int run(')"," if kind=='frames':s=instrument(s)\n s=s.replace('int main(','int run(')")
source=source.replace("d/'sources.json',Path(__file__).resolve()","d/'sources.json',d/'grouped-v001/sources.json',script,Path(__file__).resolve()")
exec(compile(source,str(script),'exec'),globals())
