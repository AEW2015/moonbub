`timescale 1ns/1ps
module tb_prefix;
 reg clk=0,rst=0,abort_i=0;
 always #5 clk=~clk;
 wire[7:0]error_code,debug_state;wire error,done,busy,aborted,rd_req_valid,metadata_valid,commit_ready,qmap_req_ready;
 wire[15:0]pa[0:2];
 cu71_packet_presum dut(.clk,.rst,.abort_i,.cfg_valid(1'b0),.cfg_packet_bytes(16'd0),.cfg_last_valid(1'b0),.cfg_last_frame_id(32'd0),.cfg_reference_valid(1'b0),.cfg_reference_id(32'd0),.cfg_reference_tag(128'd0),
 .rd_req_ready(1'b0),.rd_rsp_valid(1'b0),.rd_rsp_data(8'd0),.metadata_ready(1'b0),.qmap_req_valid(1'b0),.qmap_req_index(11'd0),.commit_valid(1'b0),
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
 task legal(input bit key,input reg[31:0]m,y,u,v);reg[15:0]p0,p1,p2;begin
  setup(key,m,y,u,v);tick();check(debug_state==10,"successful CHECK_INNER enters PREFIX_STARTS");
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
  tick();check(done&&error&&error_code==wanted&&!busy&&!metadata_valid,"exact inner error priority/code");
 end endtask
 reg[31:0]bounds[0:9];reg[15:0]a,b,c,oldp,newp;
 initial begin
  $readmemh("header.hex",header);
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
  setup(1,0,47,47,47);dut.inner_bytes=dut.inner_bytes+1;tick();check(error&&error_code==7,"length equation failure");
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
   seed=seed*1664525+1013904223;setup(1,seed,seed^32'hfedcba98,seed+32'h12345678,seed-32'hc0000000);tick();check(error&&error_code==7,"wide malformed operand rejection after exact modular sum");
  end
  $display("PACKET_PRESUM_FOCUSED_PASS checks=%0d",checks);$finish;
 end
endmodule
