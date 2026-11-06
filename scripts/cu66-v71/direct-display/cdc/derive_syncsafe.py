"""Separate syncsafe LCD/PIPE derivation: remove functional first-stage use."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-display';o=d/'cdc';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lcd=d/'cu71_lcd_lines_direct.sv';pipe=d/'cu71_direct_scanout_pipe.sv'
s=lcd.read_text();old='''    assign requests_idle=!receiving&&!line_req_valid&&!address_pending &&
        request_sync0[0]==seen0&&request_sync0[1]==seen0&&
        request_sync1[0]==seen1&&request_sync1[1]==seen1;''';assert s.count(old)==1
new='''    // Stage0 drives only stage1. Functional idle observations use stage1.
    // A qualified frame pulse follows four memory clocks after the observed
    // frame token, and requires two quiet memory clocks. It never waits into
    // active scanout: a busy window is skipped until the next frame event.
    reg [3:0] frame_guard=0;
    reg [1:0] idle_settle=0;
    wire frame_event=frame_sync[1]!=frame_seen;
    wire request_path_idle=!receiving&&!line_req_valid&&!address_pending &&
        request_sync0[1]==seen0&&request_sync1[1]==seen1;
    assign requests_idle=request_path_idle&&idle_settle==2;'''
s=s.replace(old,new).replace('module cu71_lcd_lines_direct (','module cu71_lcd_lines_syncsafe (');s=s.replace('line_req_context<=0;frame_boundary<=0;','line_req_context<=0;frame_boundary<=0;frame_guard<=0;idle_settle<=0;');old='frame_boundary<=frame_sync[1]!=frame_seen;frame_seen<=frame_sync[1];';assert s.count(old)==1;s=s.replace(old,'''frame_guard<={frame_guard[2:0],frame_event};
            frame_boundary<=frame_guard[3]&&requests_idle;
            frame_seen<=frame_sync[1];
            if(frame_event||!request_path_idle)idle_settle<=0;
            else if(idle_settle<2)idle_settle<=idle_settle+1'b1;''');(o/'cu71_lcd_lines_syncsafe.sv').write_text(s,newline='\n')
s=pipe.read_text().replace('module cu71_direct_scanout_pipe(','module cu71_direct_scanout_syncsafe(').replace('cu71_lcd_lines_direct lcd(','cu71_lcd_lines_syncsafe lcd(');(o/'cu71_direct_scanout_syncsafe.sv').write_text(s,newline='\n')
(o/'syncsafe-derivation.json').write_text(json.dumps(dict(status='ISOLATED_CANDIDATE_PROOFS_PENDING',parent_sha256={str(lcd.relative_to(r)):sha(lcd),str(pipe.relative_to(r)):sha(pipe)},candidate_sha256={n:sha(o/n)for n in ['cu71_lcd_lines_syncsafe.sv','cu71_direct_scanout_syncsafe.sv']},changes=['Remove functional request_sync[0] consumption; first stage only feeds syncchain','Use qualified stage1 idle plus2quiet mem clocks','Bound frame observation with4memclock delay; ifbusy skip pulse rather than defer into active scanout'],ports_changed=False,panel_timing_changed=False,clocks_changed=False,extra_frame_observation_latency_memclocks=4,physical_CDC_qualified=False,MTBF_qualified=False,conditions=['Legal source requests only rawx494/rawy62..781;959.77674us source quiet before nextframe','No clock-loss/unilateral pixel-reset recovery claim','Coordinated memory,owner,adapter,pixel reset required']),indent=2)+'\n')
print('SYNCSAFE_DERIVED_ISOLATED_NOT_SELECTED')
