`timescale 1ns/1ps
module tb_packets;
reg clk=0,rst=1,abort_i=0; always #5 clk=~clk;
reg cfg_valid=0;reg[15:0]cfg_packet_bytes=0;reg cfg_last_valid=0,cfg_reference_valid=0;
reg[31:0]cfg_last_frame_id=0,cfg_reference_id=0;reg[127:0]cfg_reference_tag=0;
wire cfg_ready,rd_req_valid,rd_rsp_ready,metadata_valid,qmap_req_ready,qmap_rsp_valid,commit_ready,busy,done,aborted,error;
reg rd_req_ready=0,rd_rsp_valid=0,metadata_ready=0,qmap_req_valid=0,commit_valid=0;
wire[15:0]rd_req_addr;reg[7:0]rd_rsp_data=0;reg[10:0]qmap_req_index=0;
wire[10:0]qmap_rsp_index;wire[1:0]qmap_rsp_code;wire[7:0]error_code,debug_state;wire[31:0]memory_reads;
wire metadata_key;wire[31:0]metadata_frame_id,metadata_reference_id;wire[127:0]metadata_reference_tag,metadata_output_tag;
wire[7:0]metadata_block_size;wire[15:0]metadata_plane_addr[0:2],metadata_plane_bytes[0:2];
wire[2:0]metadata_plane_dispatch[0:2];wire[16:0]metadata_plane_blocks[0:2];wire[8:0]metadata_plane_blocks_w[0:2];
wire[15:0]metadata_hud_addr,metadata_hud_bytes;wire[127:0]metadata_hud_reference_tag,metadata_hud_output_tag;
cu71_packet_rxstage_v001 dut(.*);
reg[7:0]mem[0:49151];reg pending=0;reg[15:0]pending_addr=0;integer delay_left=0,ticks=0,req_count=0;
reg stall=0,run_enable=0;reg[31:0]req_hash=0;
function automatic[31:0]mix(input[31:0]h,input[31:0]v);mix={h[26:0],h[31:27]}^v;endfunction
function automatic[31:0]mem32(input integer at);mem32={mem[at+3],mem[at+2],mem[at+1],mem[at]};endfunction
function automatic[127:0]mem128(input integer at);
 begin for(integer j=0;j<16;j++)mem128[127-8*j-:8]=mem[at+j];end
endfunction
task check_meta;
 integer first,hud,dispatch;begin
  if(metadata_key!==mem[5][0]||metadata_frame_id!==mem32(8)||metadata_reference_id!==mem32(12)||metadata_reference_tag!==mem128(36)||metadata_output_tag!==mem128(52)||metadata_block_size!==mem[98])$fatal(1,"exact metadata header oracle");
  first=474+mem32(120);hud=76+mem32(68);
  for(integer j=0;j<3;j++)begin
   dispatch=mem[first];
   if(metadata_plane_addr[j]!==16'(first+1)||metadata_plane_bytes[j]!==16'(mem32(124+4*j)-1)||metadata_plane_dispatch[j]!==3'(dispatch))$fatal(1,"exact plane address/bytes/dispatch oracle");
   if(metadata_plane_blocks[j]!==17'((dispatch==6)?((j==0)?5144:1331):((j==0)?5400:1350))||metadata_plane_blocks_w[j]!==9'((dispatch==6)?1:((j==0)?90:45)))$fatal(1,"exact plane blocks oracle");
   first=first+mem32(124+4*j);
  end
  if(metadata_hud_addr!==16'(hud)||metadata_hud_bytes!==16'(mem32(72))||metadata_hud_reference_tag!==mem128(hud+22)||metadata_hud_output_tag!==mem128(hud+38))$fatal(1,"exact HUD metadata oracle");
 end
endtask
function automatic[31:0]meta_hash;
 reg[31:0]h;begin
  h=mix(0,metadata_key);h=mix(h,metadata_frame_id);h=mix(h,metadata_reference_id);h=mix(h,metadata_block_size);
  for(integer j=0;j<4;j++)begin
   h=mix(h,metadata_reference_tag[32*j+:32]);h=mix(h,metadata_output_tag[32*j+:32]);
   h=mix(h,metadata_hud_reference_tag[32*j+:32]);h=mix(h,metadata_hud_output_tag[32*j+:32]);
  end
  for(integer j=0;j<3;j++)begin
   h=mix(h,metadata_plane_addr[j]);h=mix(h,metadata_plane_bytes[j]);h=mix(h,metadata_plane_dispatch[j]);
   h=mix(h,metadata_plane_blocks[j]);h=mix(h,metadata_plane_blocks_w[j]);
  end
  h=mix(h,metadata_hud_addr);h=mix(h,metadata_hud_bytes);meta_hash=h;
 end
endfunction
always @(negedge clk)begin
 rd_req_ready=run_enable&&(!stall||(ticks%4!=0));
 rd_rsp_valid=pending&&(delay_left==0);rd_rsp_data=pending?mem[pending_addr]:8'hXX;
end
always @(posedge clk)begin
 ticks=ticks+1;
 if(rst)begin pending=0;delay_left=0;end
 else begin
  if(pending&&delay_left>0)delay_left=delay_left-1;
  if(rd_rsp_valid&&rd_rsp_ready)pending=0;
  if(rd_req_valid&&rd_req_ready)begin
   if(pending)$fatal(1,"multiple outstanding requests");
   if(rd_req_addr!==16'(req_count))$fatal(1,"read address duplicated/skipped got%0d wanted%0d",rd_req_addr,req_count);
   pending=1;pending_addr=rd_req_addr;delay_left=stall?(1+(rd_req_addr%3)):0;
   req_hash=mix(req_hash,rd_req_addr);req_count=req_count+1;
  end
 end
end
task tick;begin @(posedge clk);#1;end endtask
task run_case(input integer id,input string path,input integer n,input bit use_stall,input bit ref_valid,input reg[31:0]ref_id,input reg[127:0]ref_tag,input integer want,input bit last_valid,input reg[31:0]last_id);
 integer start_tick,limit;reg[31:0]mh,qh;begin
  @(negedge clk);if(busy||pending)$fatal(1,"not idle before next ownership snapshot");
  $readmemh(path,mem,0,n-1);stall=use_stall;run_enable=1;req_hash=0;req_count=0;
  cfg_packet_bytes=n;cfg_reference_valid=ref_valid;cfg_reference_id=ref_id;cfg_reference_tag=ref_tag;
  cfg_last_valid=last_valid;cfg_last_frame_id=last_id;cfg_valid=1;start_tick=ticks;
  tick();@(negedge clk);
  // All these cfg inputs change while busy. The accepted snapshot must remain owner-local.
  cfg_packet_bytes=1;cfg_reference_valid=0;cfg_reference_id=32'hBAADF00D;cfg_reference_tag=128'hXX;cfg_last_valid=1;cfg_last_frame_id=32'hFFFFFFFF;
  limit=0;
  while(!done&&!metadata_valid)begin tick();limit=limit+1;if(limit>600000)$fatal(1,"case%0d timeout state%0d",id,debug_state);end
  if(want==0)begin
   if(!metadata_valid||error||aborted||memory_reads!=n||req_count!=n||pending)$fatal(1,"case%0d valid parser outcome",id);
   check_meta();
   mh=meta_hash();
   repeat(7)begin tick();if(!metadata_valid||meta_hash()!==mh||rd_req_valid||commit_ready)$fatal(1,"metadata backpressure not stable");end
   @(negedge clk);metadata_ready=1;tick();@(negedge clk);metadata_ready=0;
   if(!commit_ready||metadata_valid||rd_req_valid)$fatal(1,"WAIT_COMMIT fence");
   qh=0;
   for(integer j=0;j<1350;j++)begin
    @(negedge clk);qmap_req_valid=1;qmap_req_index=j;tick();
    if(!qmap_rsp_valid||qmap_rsp_index!=j)$fatal(1,"qmap sequencing");
    if(qmap_rsp_code!==2'((mem[136+j/4]>>(6-2*(j%4)))&3))$fatal(1,"exact qmap payload oracle");
    qh=mix(qh,qmap_rsp_code);
   end
   @(negedge clk);qmap_req_valid=0;commit_valid=1;tick();
   if(!done||busy||error||aborted)$fatal(1,"commit outcome");
   $display("CASE %0d code=0 reads=%0d req=%08x meta=%08x qmap=%08x cycles=%0d",id,memory_reads,req_hash,mh,qh,ticks-start_tick);
  end else begin
   if(!done||busy||!error||error_code!=want||metadata_valid||aborted)$fatal(1,"case%0d expected%0d gotcode%0d state%0d",id,want,error_code,debug_state);
   $display("CASE %0d code=%0d reads=%0d req=%08x meta=NONE qmap=NONE cycles=%0d",id,error_code,memory_reads,req_hash,ticks-start_tick);
  end
  @(negedge clk);cfg_valid=0;commit_valid=0;run_enable=0;
 end
endtask
initial begin
 repeat(2)tick();@(negedge clk);rst=0;
 `include "packet-cases.svh"
 $display("PACKET_SEQUENTIAL_DIFFERENTIAL_PASS");$finish;
end
endmodule
