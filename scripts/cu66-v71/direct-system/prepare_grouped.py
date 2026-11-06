"""Isolated8LCD:4BG physical-command scheduler; preserve all frozen memory RTL."""
from pathlib import Path
import hashlib,json,shutil
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/grouped-v001/source';d.mkdir(parents=True,exist_ok=False);base=r/'fpga/experiments/cu66-v71/memory/evidence/direct-fast01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for n in ['cu71_memory_system_direct.sv','cu71_tile_memory_direct.sv','moonshine_sdram_burst.sv','cu70_memory_map.svh','model.sv','primitives.sv']:shutil.copy2(base/n,d/n)
p=base/'cu71_word_bridge_direct.sv';s=p.read_text();s=s.replace('parameter integer LCD_BURSTS_PER_BACKGROUND=2,LCD_LOOKAHEAD_CYCLES=4','parameter integer LCD_BURSTS_PER_BACKGROUND=2,LCD_LOOKAHEAD_CYCLES=4,\n parameter integer LCD_GROUP_COMMANDS=8,BG_GROUP_COMMANDS=4,LCD_GROUP_GRACE=18,BG_GROUP_GRACE=4')
old=''' logic[7:0]lcd_grants,lcd_grace;
 logic background_pending,hold_for_lcd;''';assert old in s
s=s.replace(old,''' // Group quotas charge accepted controller commands, never local/cache replies.
 logic group_phase; //0=LCD,1=background
 logic[7:0]lcd_grants,bg_grants,lcd_grace,bg_grace;
 logic bg_reserved,local_turn;
 logic[1:0]bg_owner,local_selected,local_rr;
 logic[3:0]local_error,local_hit,local_pending,physical_pending;
 logic background_pending,physical_any,local_any,hold_for_lcd;
 logic[31:0]group_lcd_accepted,group_bg_accepted,group_reserved_idle;
 logic[31:0]group_lcd_reserved_idle,group_bg_reserved_idle,group_lcd_expiry,group_bg_expiry,group_uncharged;
 logic[31:0]group_bg_max_wait;
''')
start=s.index(' always_comb begin');end=s.index('  p0_ready=',start)
s=s[:start]+''' function automatic logic bad_request(input integer k);
  bad_request=!map_word_allowed(address[k])||!map_word_allowed({address[k][23:3],3'b000})||
   !map_word_allowed({address[k][23:3],3'b111})||((k==2||k==3)&&address[k][2:0]!=0)||(k==3&&!rgb_block_allowed(address[k]));
 endfunction
 always_comb begin
  for(integer k=0;k<4;k=k+1)begin
   local_error[k]=pending[k]&&bad_request(k);
   local_hit[k]=pending[k]&&k==1&&!writing[k]&&cache_valid[1]&&cache_tag[1]==address[k][23:3]&&!local_error[k];
  end
  local_pending=local_error|local_hit;
  physical_pending=pending&~local_pending;
  physical_any=|physical_pending;local_any=|local_pending;
  local_selected=local_rr;
  for(integer n=3;n>=0;n=n-1)if(local_pending[(int'(local_rr)+n)&3])local_selected=2'((int'(local_rr)+n)&3);
  background_pending=physical_pending[0]||physical_pending[1]||physical_pending[3];
  case(background_phase)
   0:background_selected=physical_pending[0]?0:physical_pending[1]?1:3;
   1:background_selected=physical_pending[1]?1:physical_pending[3]?3:0;
   default:background_selected=physical_pending[3]?3:physical_pending[0]?0:1;
  endcase
  selected=2;hold_for_lcd=0;
  if(!group_phase)begin
   if(physical_pending[2])selected=2;
   else begin selected=background_selected;hold_for_lcd=background_pending&&lcd_grace!=0;end
  end else begin
   if(bg_reserved&&physical_pending[bg_owner])selected=bg_owner;
   else if(bg_reserved&&bg_grace!=0&&physical_any)begin selected=bg_owner;hold_for_lcd=1;end
   else selected=background_pending?background_selected:2;
  end
'''+s[end:]
s=s.replace('owner<=0;background_phase<=0;lcd_grants<=0;lcd_grace<=0;','owner<=0;background_phase<=0;lcd_grants<=0;bg_grants<=0;lcd_grace<=0;bg_grace<=0;group_phase<=0;bg_reserved<=0;bg_owner<=0;local_turn<=1;local_rr<=0;\n   group_lcd_accepted<=0;group_bg_accepted<=0;group_reserved_idle<=0;group_lcd_reserved_idle<=0;group_bg_reserved_idle<=0;group_lcd_expiry<=0;group_bg_expiry<=0;group_uncharged<=0;group_bg_max_wait<=0;')
s=s.replace('   if(lcd_grace!=0)lcd_grace<=lcd_grace-1;','''   if(lcd_grace!=0)lcd_grace<=lcd_grace-1;
   if(bg_grace!=0)bg_grace<=bg_grace-1;
   if(lcd_grace==1&&!physical_pending[2]&&background_pending)group_lcd_expiry<=group_lcd_expiry+1;
   if(bg_grace==1&&bg_reserved&&!physical_pending[bg_owner]&&physical_any)group_bg_expiry<=group_bg_expiry+1;
   if(state==IDLE&&physical_any&&hold_for_lcd&&!(local_any&&local_turn))begin
    group_reserved_idle<=group_reserved_idle+1;
    if(group_phase)group_bg_reserved_idle<=group_bg_reserved_idle+1;else group_lcd_reserved_idle<=group_lcd_reserved_idle+1;
   end''')
start=s.index('    IDLE:if(any_pending');end=s.index('    REQUEST:',start)
s=s[:start]+'''    IDLE:begin
     // At most one uncharged local reply before an eligible physical command.
     // Local traffic cannot hold a quota open forever or extend its grace.
     if(local_any&&(local_turn||!physical_any))begin
      pending[local_selected]<=0;response_error[local_selected]<=local_error[local_selected];
      response_valid[local_selected]<=1;group_uncharged<=group_uncharged+1;
      local_rr<=local_selected+2'd1;local_turn<=0;
      if(local_error[local_selected])response_data[local_selected]<=0;
      else begin response_data[local_selected]<={112'd0,cache_data[local_selected*8+address[local_selected][2:0]]};cache_hits<=cache_hits+1;end
     end else if(physical_any&&!hold_for_lcd)begin
      pending[selected]<=0;owner<=selected;response_error[selected]<=0;state<=REQUEST;local_turn<=1;
      if(!writing[selected])cache_misses<=cache_misses+1;
      if(writing[selected])for(integer i=0;i<2;i=i+1)if(cache_valid[i]&&cache_tag[i]==address[selected][23:3])cache_valid[i]<=0;
     end
    end
'''+s[end:]
old='    REQUEST:if(mem_req_valid&&mem_req_ready)begin beat<=0;read_payload<=0;state<=writing[owner]?WRITE_WAIT:READ_BURST;end';assert old in s
s=s.replace(old,'''    REQUEST:if(mem_req_valid&&mem_req_ready)begin
     beat<=0;read_payload<=0;state<=writing[owner]?WRITE_WAIT:READ_BURST;
     if(owner==2)begin
      group_lcd_accepted<=group_lcd_accepted+1;bg_grants<=0;bg_grace<=0;bg_reserved<=0;
      if(!group_phase&&lcd_grants+1>=LCD_GROUP_COMMANDS)begin group_phase<=1;lcd_grants<=0;lcd_grace<=0;end
      else begin group_phase<=0;lcd_grants<=group_phase?8'd1:lcd_grants+1;end
     end else begin
      group_bg_accepted<=group_bg_accepted+1;lcd_grants<=0;lcd_grace<=0;
      background_phase<=owner==0?1:owner==1?2:0;
      if(group_phase&&bg_grants+1>=BG_GROUP_COMMANDS)begin group_phase<=0;bg_grants<=0;bg_reserved<=0;bg_grace<=0;end
      else begin group_phase<=1;bg_grants<=group_phase?bg_grants+1:8'd1;bg_reserved<=1;bg_owner<=owner;end
     end
    end''')
s=s.replace("       lcd_grace<=8'(LCD_LOOKAHEAD_CYCLES);","       if(!group_phase&&lcd_grants!=0)lcd_grace<=8'(LCD_GROUP_GRACE);")
s=s.replace('      response_valid[owner]<=1;completed_reads<=completed_reads+1;state<=IDLE;','''      response_valid[owner]<=1;completed_reads<=completed_reads+1;state<=IDLE;
      if(owner!=2)begin
       if(wait_cycles[owner]>group_bg_max_wait)group_bg_max_wait<=wait_cycles[owner];
       if(group_phase&&bg_grants!=0)bg_grace<=8'(BG_GROUP_GRACE);
      end''')
s=s.replace('     response_data[owner]<=0;response_valid[owner]<=1;completed_writes<=completed_writes+1;state<=IDLE;','''     response_data[owner]<=0;response_valid[owner]<=1;completed_writes<=completed_writes+1;state<=IDLE;
     if(wait_cycles[owner]>group_bg_max_wait)group_bg_max_wait<=wait_cycles[owner];
     if(group_phase&&bg_grants!=0)bg_grace<=8'(BG_GROUP_GRACE);''')
s=s.replace('// Three independent request/response slots. LCD reads are explicit aligned BL8.','// Isolated grouped8LCD:4BG scheduler. Original request/response/drain paths retained.')
out=d/'cu71_word_bridge_direct.sv';out.write_text(s,newline='\n');pins={f.name:sha(f)for f in d.iterdir()if f.is_file()};(d.parent/'derivation.json').write_text(json.dumps({'parent_bridge_sha256':sha(p),'candidate_bridge_sha256':sha(out),'source_files':pins,'policy':'8LCD:4BGacceptedphysicalcommands;BGclientreservation;boundedgrace18LCD/4BG;localcache/errornoncharge;1localbeforephysicalfairness','unchanged':['controller','PHY','map','tileadapter','memorywrapper','codec','baseowner'],'hardware':False},indent=2)+'\n');print('PREPARED_GROUPED',sha(out))
