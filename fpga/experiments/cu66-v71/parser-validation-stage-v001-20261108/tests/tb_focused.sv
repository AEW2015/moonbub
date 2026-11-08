`timescale 1ns/1ps
module tb_prefix;
 reg clk=0,rst=0,abort_i=0;
 reg test_rsp_valid=0,test_cfg_valid=0;reg[7:0]test_rsp_data=0;reg[15:0]test_cfg_bytes=0;
 always #5 clk=~clk;
 wire[7:0]error_code,debug_state;wire error,done,busy,aborted,rd_req_valid,metadata_valid,commit_ready,qmap_req_ready;
 wire[15:0]pa[0:2];
 cu71_packet_rxstage_v001 dut(.clk,.rst,.abort_i,.cfg_valid(test_cfg_valid),.cfg_packet_bytes(test_cfg_bytes),.cfg_last_valid(1'b0),.cfg_last_frame_id(32'd0),.cfg_reference_valid(1'b0),.cfg_reference_id(32'd0),.cfg_reference_tag(128'd0),
 .rd_req_ready(1'b0),.rd_rsp_valid(test_rsp_valid),.rd_rsp_data(test_rsp_data),.metadata_ready(1'b0),.qmap_req_valid(1'b0),.qmap_req_index(11'd0),.commit_valid(1'b0),
 .error_code,.debug_state,.error,.done,.busy,.aborted,.rd_req_valid,.metadata_valid,.commit_ready,.qmap_req_ready,.metadata_plane_addr(pa));
 reg[7:0]header[0:59];integer checks=0;reg[31:0]seed=32'h71439;
 task tick;begin @(posedge clk);#1;end endtask
 task check(input bit ok,input string msg);begin checks=checks+1;if(!ok)$fatal(1,"%s state=%0d code=%0d",msg,debug_state,error_code);end endtask
 task put32(input integer at,input reg[31:0]v);begin for(integer i=0;i<4;i++)dut.inner_header[at+i]=v[8*i+:8];end endtask
 task setup(input bit key,input reg[31:0]m,y,u,v);begin
  @(negedge clk);rst=1;tick();@(negedge clk);rst=0;abort_i=0;
  for(integer i=0;i<60;i++)dut.inner_header[i]=header[i];
  dut.metadata_key=key;dut.inner_header[5]={7'd0,key};
  dut.metadata_frame_id={header[13],header[12],header[11],header[10]};
  dut.metadata_reference_id={header[17],header[16],header[15],header[14]};
  for(integer i=0;i<16;i++)dut.metadata_reference_tag[127-8*i-:8]=header[24+i];
  dut.packet_bytes=49152;dut.inner_bytes=(338+m+y+u+v+64>49152)?16'd49152:16'(338+m+y+u+v+64);
  put32(40,338);put32(44,m);put32(48,y);put32(52,u);put32(56,v);
  dut.state=dut.INNER_SUM_PAIRS;
  tick();check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready,"sum pair stage private");
  tick();check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready,"sum merge stage private");
  tick();check(dut.inner_length_total===32'(338+m+y+u+v+64),"full-width modulo32 length sum");
 end endtask
 task decide;begin tick();if(debug_state==19)begin check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready&&!dut.inner_validated,"new length validation stage private");tick();end end endtask
 task legal(input bit key,input reg[31:0]m,y,u,v);reg[15:0]p0,p1,p2;begin
  setup(key,m,y,u,v);decide();check(debug_state==10,"successful CHECK_INNER enters PREFIX_STARTS");
  check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready&&!dut.inner_validated,"no early visibility in stage1");
  tick();check(debug_state==11,"PREFIX_ADDRESSES reached");check(!rd_req_valid&&!dut.inner_validated,"no scan before addresses");
  tick();p0=16'd474+16'(m);p1=16'd474+16'(m)+16'(y);p2=16'd474+16'(m)+16'(y)+16'(u);
  check(debug_state==1&&dut.inner_validated,"resume byte requests only after address stage");
  check(dut.vector_end===p0&&dut.plane_start[0]===p0&&dut.plane_start[1]===p1&&dut.plane_start[2]===p2,"exact modular starts");
  check(pa[0]===16'(p0+1)&&pa[1]===16'(p1+1)&&pa[2]===16'(p2+1),"exact payload addresses");
  check(dut.metadata_plane_bytes[0]===16'(y-1)&&dut.metadata_plane_bytes[1]===16'(u-1)&&dut.metadata_plane_bytes[2]===16'(v-1),"exact length narrowing");
 end endtask
 task reject(input reg[31:0]m,y,u,v,input bit bad_header,input reg[7:0]wanted);begin
  setup(1,m,y,u,v);if(bad_header)dut.inner_header[0]=0;
  decide();check(done&&error&&error_code==wanted&&!busy&&!metadata_valid,"exact inner error priority/code");
 end endtask
 reg[31:0]bounds[0:9];reg[15:0]a,b,c,oldp,newp;

 reg[7:0]hh[0:105];
 task hput32(input integer at,input reg[31:0]v);begin for(integer i=0;i<4;i++)dut.hud_header[at+i]=v[8*i+:8];end endtask
 task setuphud(input bit key,input reg[31:0]a,b,c,d);begin
  @(negedge clk);rst=1;tick();@(negedge clk);rst=0;abort_i=0;
  for(integer i=0;i<106;i++)dut.hud_header[i]=hh[i];
  dut.metadata_key=key;if(!key)dut.hud_header[22]=1;
  dut.metadata_frame_id={hh[13],hh[12],hh[11],hh[10]};dut.metadata_reference_id={hh[17],hh[16],hh[15],hh[14]};
  dut.packet_bytes=49152;dut.metadata_hud_bytes=(a+b+c+d+110>49152)?16'd49152:16'(a+b+c+d+110);
  hput32(54,a);hput32(58,b);hput32(62,c);hput32(66,d);dut.state=dut.HUD_SUM_PAIRS;
  tick();check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready,"HUD pairs private");
  tick();check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready,"HUD merge private");
  tick();check(dut.hud_length_total===32'(a+b+c+d+110),"HUD exact modulo32 staged sum");
 end endtask
 task legalhud(input bit key,input reg[31:0]a,b,c,d);begin
  setuphud(key,a,b,c,d);tick();check(debug_state==1&&!error&&!metadata_valid,"legal HUD header resumes exact scan");
  for(integer i=0;i<16;i++)begin
   check(dut.metadata_hud_output_tag[127-8*i-:8]===hh[38+i],"HUD output tag packing");
   check(dut.metadata_hud_reference_tag[127-8*i-:8]===((!key&&i==0)?8'd1:hh[22+i]),"HUD reference tag packing");
  end
 end endtask
 task rejecthud(input reg[31:0]a,b,c,d,input bit bad_header,input bit bad_rect,input bit bad_type,input reg[7:0]wanted);begin
  setuphud(1,a,b,c,d);if(bad_header)dut.hud_header[0]=0;if(bad_rect)dut.hud_header[74]=dut.hud_header[74]^8'd1;if(bad_type)dut.hud_header[70]=0;
  tick();check(done&&error&&error_code==wanted&&!busy&&!metadata_valid,"exact HUD11-before12 priority and grammar");
 end endtask


 task rx_setup(input reg[15:0]at,input reg[7:0]value);begin
  @(negedge clk);rst=1;abort_i=0;test_rsp_valid=0;test_cfg_valid=0;tick();@(negedge clk);rst=0;
  dut.packet_bytes=49152;dut.scan_addr=at;dut.outer_validated=1;dut.inner_validated=(at>=136&&at<474);dut.inner_bytes=1924;dut.metadata_hud_addr=2000;
  dut.state=dut.READ_RESPONSE;test_rsp_valid=1;test_rsp_data=value;
 end endtask
 task rx_good(input reg[15:0]at);reg[7:0]value;begin
  value=(at>=136&&at<474)?8'h50:8'ha7;rx_setup(at,value);
  dut.receive_byte=8'hxx;dut.receive_index=16'hxxxx;tick();check(debug_state==18&&busy&&!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready&&!dut.rd_rsp_ready&&!dut.cfg_ready,"RX_COMMIT stage private and valid");
  check(dut.receive_byte===value&&dut.receive_index===at&&dut.scan_addr===at,"full byte/index capture overwrites Xstartup");
  @(negedge clk);test_rsp_valid=0;test_rsp_data=8'hxx;test_cfg_valid=1;test_cfg_bytes=1;tick();
  check(!error&&dut.scan_addr===16'(at+1)&&dut.packet_bytes===16'd49152,"commit uses captured index and ignores livebus/config");
  if(at<76)check(dut.outer_header[at[6:0]]===value,"outer header uses staged byte");
  if(at>=76&&at<136)check(dut.inner_header[6'(at-76)]===value,"inner header uses staged byte");
  if(at>=136&&at<474)check(dut.qmap_mem[9'(at-136)]===value,"qmap uses staged byte");
  if(at>=2000&&at<2106)check(dut.hud_header[7'(at-2000)]===value,"HUD header uses staged byte");
  @(negedge clk);test_cfg_valid=0;test_rsp_data=0;
 end endtask
 task rx_bad(input reg[7:0]code,input bit concurrent_abort);reg[15:0]at;reg[7:0]value;begin
  at=code==8?136:(code==9?475:512);value=code==8?8'hc0:8'd7;rx_setup(at,value);dut.inner_validated=1;
  if(code==9)begin dut.vector_start=474;dut.vector_end=477;end
  if(code==10)dut.plane_start[0]=512;
  dut.receive_byte=8'h5a;dut.receive_index=16'h7654;abort_i=concurrent_abort;tick();
  check(done&&!busy&&!metadata_valid&&debug_state==0,"bad byte or abort terminates at response edge");
  if(concurrent_abort)check(aborted&&!error,"abort must retain priority over byte error");else check(error&&error_code==code,"byte error8/9/10 not deferred into new stage");
  check(dut.receive_byte===8'h5a&&dut.receive_index===16'h7654,"bad or aborted byte never staged");
  @(negedge clk);abort_i=0;test_rsp_valid=0;
 end endtask
 task rx_cancel(input bit do_reset);reg[31:0]old_crc;reg[7:0]old_header;begin
  rx_setup(0,8'h43);tick();check(debug_state==18,"cancel at actual new stage");
  old_crc=dut.crc_outer;old_header=dut.outer_header[0];@(negedge clk);test_rsp_valid=0;dut.receive_byte=8'hxx;dut.receive_index=16'hxxxx;abort_i=1;rst=do_reset;test_cfg_valid=1;tick();
  check(!busy&&!metadata_valid&&!rd_req_valid&&debug_state==0,"cancel new stage immediately");
  check(dut.receive_byte===8'hxx&&dut.receive_index===16'hxxxx&&dut.outer_header[0]===old_header,"unreset payload not consumed or cleared on cancel");
  if(do_reset)check(!error&&!aborted&&!done&&dut.crc_outer===32'hffffffff,"reset dominates abort/config");else check(aborted&&done&&!error&&dut.crc_outer===old_crc,"abort precedes staged parse writes");
  @(negedge clk);rst=0;abort_i=0;test_cfg_valid=0;test_rsp_data=0;rx_good(0);
 end endtask

 initial begin
  $readmemh("header.hex",header);$readmemh("hud.hex",hh);
  legal(1,0,47,47,47);legal(0,3,47,47,47);legal(1,0,48000,47,47);
  for(integer n=0;n<1000;n++)begin
   seed=seed*1664525+1013904223;a=47+(seed%12000);seed=seed*1664525+1013904223;b=47+(seed%12000);seed=seed*1664525+1013904223;c=47+(seed%12000);
   legal(n[0],n[0]?0:3,a,b,c);
  end
  bounds[0]=0;bounds[1]=46;bounds[2]=47;bounds[3]=49152;bounds[4]=49153;bounds[5]=65535;bounds[6]=65536;bounds[7]=32'hffffffff;bounds[8]=32'h80000000;bounds[9]=32'hffff0000;
  for(integer n=0;n<10;n++)begin
   // code6 wins even when the lengths are independently invalid.
   reject(0,bounds[n],47,47,1,6);
   if(n!=2)reject(0,bounds[n],47,47,0,7);
   reject(bounds[n]==0?1:bounds[n],47,47,47,0,7);
  end
  setup(1,0,47,47,47);dut.inner_bytes=dut.inner_bytes+1;decide();check(error&&error_code==7,"length equation failure");
  // Exercise full-width modular equations independently of acceptance guards.
  for(integer n=0;n<10000;n++)begin
   seed=seed*1664525+1013904223;a=seed[15:0];seed=seed*1664525+1013904223;b=seed[15:0];seed=seed*1664525+1013904223;c=seed[15:0];
   oldp=16'd475+a+b+c;newp=16'((16'd474+a)+16'(b+c))+16'd1;check(oldp===newp,"wrap-equivalent reassociation");
  end
  for(integer stage=0;stage<2;stage++)begin
   setup(1,0,47,47,47);tick();if(stage)tick();@(negedge clk);abort_i=1;tick();check(done&&aborted&&!busy&&!metadata_valid&&!rd_req_valid,"new state abort releases without read");@(negedge clk);abort_i=0;
   legal(1,0,47,47,47);
   setup(1,0,47,47,47);tick();if(stage)tick();@(negedge clk);rst=1;tick();check(!busy&&!error&&!aborted&&!dut.inner_validated&&pa[0]===0&&pa[1]===0&&pa[2]===0,"new state reset clears qualified outputs");@(negedge clk);rst=0;
   legal(0,3,47,47,47);
  end
  for(integer stage=0;stage<3;stage++)begin
   setup(1,0,47,47,47);@(negedge clk);dut.state=dut.INNER_SUM_PAIRS;
   for(integer k=0;k<stage;k++)tick();@(negedge clk);abort_i=1;tick();check(done&&aborted&&!busy&&!metadata_valid&&!rd_req_valid,"sum state abort");@(negedge clk);abort_i=0;legal(1,0,47,47,47);
   setup(1,0,47,47,47);@(negedge clk);dut.state=dut.INNER_SUM_PAIRS;
   for(integer k=0;k<stage;k++)tick();@(negedge clk);rst=1;tick();check(!busy&&!error&&!aborted&&!dut.inner_validated&&dut.inner_length_total===0,"sum state reset");@(negedge clk);rst=0;legal(0,3,47,47,47);
  end
  for(integer n=0;n<1000;n++)begin
   seed=seed*1664525+1013904223;setup(1,seed,seed^32'hfedcba98,seed+32'h12345678,seed-32'hc0000000);decide();check(error&&error_code==7,"wide malformed operand rejection after exact modular sum");
  end
  legalhud(1,1,1,1,1);legalhud(0,1,1,1,1);
  for(integer n=0;n<1000;n++)begin
   seed=seed*1664525+1013904223;a=1+(seed%10000);seed=seed*1664525+1013904223;b=1+(seed%10000);seed=seed*1664525+1013904223;c=1+(seed%10000);legalhud(n[0],a,b,c,1);
  end
  for(integer n=0;n<10;n++)begin
   rejecthud(bounds[n],1,1,1,1,0,0,11);
   if(n==0||n>=3)rejecthud(bounds[n],1,1,1,0,0,0,12);
   rejecthud(1,1,1,1,0,1,0,12);rejecthud(1,1,1,1,0,0,1,12);
   rejecthud(0,1,1,1,1,1,1,11);
  end
  setuphud(1,1,1,1,1);dut.metadata_hud_bytes=115;tick();check(error&&error_code==12,"HUD total mismatch");
  for(integer n=0;n<1000;n++)begin
   seed=seed*1664525+1013904223;setuphud(1,seed,seed^32'hfedcba98,seed+32'h12345678,seed-32'hc0000000);tick();check(error&&error_code==12,"HUD wide malformed rejection and sum wrap");
  end
  for(integer stage=0;stage<3;stage++)begin
   setuphud(1,1,1,1,1);@(negedge clk);dut.state=dut.HUD_SUM_PAIRS;
   for(integer k=0;k<stage;k++)tick();@(negedge clk);abort_i=1;tick();check(done&&aborted&&!busy&&!metadata_valid&&!rd_req_valid,"HUD sum state abort");@(negedge clk);abort_i=0;legalhud(1,1,1,1,1);
   setuphud(1,1,1,1,1);@(negedge clk);dut.state=dut.HUD_SUM_PAIRS;
   for(integer k=0;k<stage;k++)tick();@(negedge clk);rst=1;tick();check(!busy&&!error&&!aborted&&!dut.inner_validated&&dut.hud_length_total===0,"HUD sum state reset");@(negedge clk);rst=0;legalhud(0,1,1,1,1);
  end
  rx_good(0);rx_good(75);rx_good(76);rx_good(135);rx_good(136);rx_good(473);rx_good(2000);rx_good(2105);rx_good(49151);
  rx_bad(8,0);rx_bad(9,0);rx_bad(10,0);rx_bad(8,1);rx_bad(9,1);rx_bad(10,1);rx_cancel(0);rx_cancel(1);
  for(integer field=0;field<15;field++)begin
   setup(1,0,47,47,47);dut.metadata_block_size=8'hA7;dut.metadata_plane_bytes[0]=16'hCAFE;dut.prefix0=16'hBEEF;
   case(field)
    0:dut.inner_header[0]=0;1:dut.inner_header[4]=2;2:dut.inner_header[5]=2;
    3:put32(6,24);4:put32(10,dut.metadata_frame_id+1);5:put32(14,dut.metadata_reference_id-1);
    6:dut.inner_header[18]=0;7:dut.inner_header[20]=0;8:dut.inner_header[22]=17;9:dut.inner_header[23]=17;
    10:dut.inner_header[24]=dut.inner_header[24]^1;11:dut.inner_header[39]=dut.inner_header[39]^1;
    12:begin dut.inner_header[0]=0;put32(48,0);end
    13:begin dut.inner_header[24]=dut.inner_header[24]^1;put32(48,32'hFFFFFFFF);end
    14:begin dut.inner_header[5]=2;dut.inner_length_total=0;end
   endcase
   decide();check(error&&done&&error_code==6&&!busy&&!metadata_valid,"header/schema/tag/frame/reference and simultaneous6/7 retain code6");
   check(dut.metadata_block_size===8'hA7&&dut.metadata_plane_bytes[0]===16'hCAFE&&dut.prefix0===16'hBEEF,"code6 reject never captures derived fields");
  end
  setup(1,0,47,47,47);put32(48,0);dut.metadata_plane_bytes[0]=16'hCAFE;dut.metadata_block_size=8'hA7;dut.prefix0=16'hBEEF;
  decide();check(error&&done&&error_code==7&&dut.metadata_plane_bytes[0]===16'hCAFE&&dut.metadata_block_size===8'hA7&&dut.prefix0===16'hBEEF,"code7 reject preserves original derived-field visibility");
`ifdef STAGED
  for(integer cancel=0;cancel<3;cancel++)begin
   setup(1,0,47,47,47);dut.metadata_plane_bytes[0]=16'hCAFE;dut.metadata_block_size=8'hA7;dut.prefix0=16'hBEEF;
   tick();check(debug_state==19&&dut.metadata_plane_bytes[0]===16'hCAFE&&dut.metadata_block_size===8'hA7&&dut.prefix0===16'hBEEF,"code6 pass only publishes state fence");
   check(!rd_req_valid&&!dut.rd_rsp_ready&&!metadata_valid&&!commit_ready&&!qmap_req_ready&&!dut.cfg_ready&&!dut.inner_validated,"length stage admits no bus/config/metadata action");
   @(negedge clk);test_cfg_valid=1;test_cfg_bytes=1;test_rsp_valid=1;test_rsp_data=8'hXX;
   if(cancel==1)abort_i=1;if(cancel==2)begin rst=1;abort_i=1;end
   tick();
   if(cancel==0)check(debug_state==10&&!error&&dut.packet_bytes==49152&&dut.metadata_plane_bytes[0]==46,"length commit ignores new cfg/live response");
   else if(cancel==1)check(done&&aborted&&!error&&!busy&&dut.metadata_plane_bytes[0]===16'hCAFE&&!metadata_valid,"new-stage abort prevents capture and wins over incoming cfg/rsp");
   else check(!done&&!aborted&&!error&&!busy&&dut.metadata_plane_bytes[0]==0&&!metadata_valid,"new-stage reset dominates abort and incoming cfg/rsp");
   @(negedge clk);test_cfg_valid=0;test_rsp_valid=0;abort_i=0;rst=0;
   if(cancel==1)begin
    test_cfg_valid=1;test_cfg_bytes=733;tick();
    check(debug_state==1&&dut.packet_bytes==733&&dut.scan_addr==0&&!dut.outer_validated&&!dut.inner_validated&&!metadata_valid&&dut.memory_reads==0,"immediate cfg after added-stage abort owns a fresh parser with no delayed metadata");
    @(negedge clk);test_cfg_valid=0;abort_i=1;tick();check(done&&aborted&&!busy&&!metadata_valid,"fresh owner can cancel before read acceptance");
    @(negedge clk);abort_i=0;
   end
   legal(0,3,47,47,47);
  end
  setup(1,0,47,47,47);put32(48,0);tick();@(negedge clk);abort_i=1;tick();check(done&&aborted&&!error&&!busy,"abort beats pending code7 at new state");@(negedge clk);abort_i=0;
`endif

  $display("PACKET_RX_FOURSTATE_FOCUSED_PASS checks=%0d dirty_Xstartup=1 capture_index=1 livebus_Xignored=1 immediate_bad8_9_10=1 abort_reset_precedence=1",checks);$finish;
 end
endmodule
