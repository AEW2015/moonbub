`timescale 1ns/1ps
module tb;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,abort=0,start_valid=0,start_check_epoch=1,in_valid=0,in_last=0,envelope_ready=0,error_ready=0;
 reg[63:0]start_owner=0;reg[31:0]start_bytes=0,start_expected_epoch=1;reg[7:0]in_data=0;
 wire start_ready,in_ready,envelope_validated,error_valid;wire[3:0]error_code;
 wire[63:0]desc_owner;wire[31:0]desc_epoch,desc_frame,desc_expected_epoch;wire desc_epoch_checked;
 wire[7:0]desc_flags,desc_reference_bank,desc_destination_bank;
 wire[31:0]desc_reference_id,desc_inner_bytes,desc_patch_bytes,desc_patch_blob_offset;
 wire[127:0]desc_reference_tag,desc_stored_tag,desc_patch_offsets,desc_patch_lengths;wire[2:0]desc_patch_count;
 reg rd_req_valid=0,rd_rsp_ready=0,retire_valid=0;
 reg[31:0]rd_req_address=0,rd_req_epoch=0,retire_epoch=0;reg[63:0]rd_req_owner=0,retire_owner=0;
 wire rd_req_ready,rd_rsp_valid,rd_rsp_error,retire_ready;wire[7:0]rd_rsp_data;wire[63:0]rd_rsp_owner;wire[31:0]rd_rsp_epoch;
 ar03_envelope dut(.*);
 reg[7:0]bytes[0:65535];
 integer fd,rc,n,i,case_id=0,declared,actual,expected,ep,check_ep,skip_data;
 integer cycles=0,accepted=0,rejected=0,replay_bytes=0,cancel_cases=0,seed=32'h6b4103ab;
 reg[63:0]active_owner;reg[1023:0]held_descriptor;reg[104:0]held_response;
 reg held_desc=0,held_rsp=0;reg[3:0]held_error;reg held_err=0;
 wire[1023:0]descriptor_bus={desc_owner,desc_epoch,desc_frame,desc_expected_epoch,desc_epoch_checked,desc_flags,desc_reference_bank,desc_destination_bank,desc_reference_id,desc_inner_bytes,desc_patch_bytes,desc_reference_tag,desc_stored_tag,desc_patch_count,desc_patch_blob_offset,desc_patch_offsets,desc_patch_lengths};
 always @(posedge clk)begin
  cycles=cycles+1;if(cycles>20000000)$fatal(1,"watchdog");
  if(reset||abort)begin held_desc<=0;held_rsp<=0;held_err<=0;end
  else begin
   if(held_desc&&(!envelope_validated||descriptor_bus!==held_descriptor))$fatal(1,"held descriptor changed");
   held_desc<=envelope_validated&&!envelope_ready;if(envelope_validated&&!envelope_ready)held_descriptor<=descriptor_bus;
   if(held_rsp&&(!rd_rsp_valid||{rd_rsp_data,rd_rsp_error,rd_rsp_owner,rd_rsp_epoch}!==held_response))$fatal(1,"held read response changed");
   held_rsp<=rd_rsp_valid&&!rd_rsp_ready;if(rd_rsp_valid&&!rd_rsp_ready)held_response<={rd_rsp_data,rd_rsp_error,rd_rsp_owner,rd_rsp_epoch};
   if(held_err&&(!error_valid||error_code!==held_error))$fatal(1,"held error changed");
   held_err<=error_valid&&!error_ready;if(error_valid&&!error_ready)held_error<=error_code;
  end
 end
 function[31:0]le32(input integer at);begin le32={bytes[at+3],bytes[at+2],bytes[at+1],bytes[at]};end endfunction
 task launch(input integer size,input[63:0]own,input integer epoch_value,input integer epoch_check);
 begin @(negedge clk);start_valid=1;start_bytes=size;start_owner=own;start_expected_epoch=epoch_value;start_check_epoch=epoch_check;
 while(!start_ready)@(negedge clk);@(negedge clk);start_valid=0;end endtask
 task feed(input integer count,input integer gaps);
 integer j;
 begin
 for(j=0;j<count;j=j+1)begin
  if(gaps&&(($random(seed)&31)==0))begin in_valid=0;repeat(2)@(negedge clk);end
  in_valid=1;in_data=bytes[j];in_last=j==count-1;
  if(!in_ready)$fatal(1,"unexpected ingress backpressure case%0d byte%0d",case_id,j);
  @(posedge clk);if(envelope_validated||rd_rsp_valid)$fatal(1,"output before envelope completion");
  @(negedge clk);
 end
 in_valid=0;in_last=0;
 end endtask
 task check_descriptor;
 integer j,pos,size;
 begin
 if(desc_owner!==active_owner||desc_epoch!==le32(6)||desc_frame!==le32(10)||desc_expected_epoch!==ep||desc_epoch_checked!==check_ep[0])$fatal(1,"identity descriptor case%0d",case_id);
 if(desc_flags!==bytes[5]||desc_reference_bank!==bytes[14]||desc_destination_bank!==bytes[15]||desc_reference_id!==le32(16)||desc_inner_bytes!==le32(52)||desc_patch_bytes!==le32(57)||desc_patch_count!==bytes[56])$fatal(1,"header descriptor case%0d",case_id);
 for(j=0;j<16;j=j+1)if(desc_reference_tag[j*8+:8]!==bytes[20+j]||desc_stored_tag[j*8+:8]!==bytes[36+j])$fatal(1,"tag descriptor");
 pos=61+le32(52);if(desc_patch_blob_offset!==pos)$fatal(1,"blob descriptor");
 for(j=0;j<4;j=j+1)begin
  if(j<bytes[56])begin size=le32(pos);if(desc_patch_offsets[j*32+:32]!==pos+4||desc_patch_lengths[j*32+:32]!==size)$fatal(1,"patch descriptor%0d",j);pos=pos+4+size;end
  else if(desc_patch_offsets[j*32+:32]!==0||desc_patch_lengths[j*32+:32]!==0)$fatal(1,"unused patch descriptor stale");
 end
 if(pos!=actual-4)$fatal(1,"patch section end");
 end endtask
 task accept_certificate;
 begin
 while(!envelope_validated&&!error_valid)@(negedge clk);
 if(error_valid)$fatal(1,"unexpected error case%0d code%0d",case_id,error_code);
 check_descriptor();repeat(9)@(negedge clk);
 // No replay access until the certificate handshake.
 rd_req_valid=1;rd_req_owner=active_owner;rd_req_epoch=desc_epoch;rd_req_address=0;
 repeat(3)begin @(negedge clk);if(rd_req_ready||rd_rsp_valid)$fatal(1,"replay before descriptor handshake");end
 rd_req_valid=0;envelope_ready=1;@(negedge clk);envelope_ready=0;
 end endtask
 task read_check(input[31:0]addr,input[63:0]own,input[31:0]epoch_value,input integer bad,input integer hold_cycles);
 begin
 @(negedge clk);rd_req_valid=1;rd_req_address=addr;rd_req_owner=own;rd_req_epoch=epoch_value;rd_rsp_ready=0;
 while(!rd_req_ready)@(negedge clk);@(negedge clk);rd_req_valid=0;
 if(rd_rsp_valid)$fatal(1,"read response was not synchronous");
 while(!rd_rsp_valid)@(negedge clk);
 if(rd_rsp_error!==bad[0]||rd_rsp_owner!==own||rd_rsp_epoch!==epoch_value||rd_rsp_data!==(bad?8'b0:bytes[addr]))$fatal(1,"read mismatch case%0d addr%0d bad%0d got%h",case_id,addr,bad,rd_rsp_data);
 repeat(hold_cycles)@(negedge clk);
 rd_rsp_ready=1;@(negedge clk);rd_rsp_ready=0;
 end endtask
 task retire;
 begin @(negedge clk);retire_valid=1;retire_owner=active_owner;retire_epoch=desc_epoch;
 if(!retire_ready)begin #1;if(!retire_ready)$fatal(1,"retire not ready after drain");end
 @(negedge clk);retire_valid=0;#1;if(!start_ready||rd_rsp_valid)$fatal(1,"retire failed");end endtask
 task retire_while_read_held;
 begin
 @(negedge clk);rd_req_valid=1;rd_req_address=61;rd_req_owner=active_owner;rd_req_epoch=desc_epoch;rd_rsp_ready=0;
 while(!rd_req_ready)@(negedge clk);@(negedge clk);rd_req_valid=0;retire_valid=1;retire_owner=active_owner;retire_epoch=desc_epoch;
 #1;if(retire_ready||rd_req_ready)$fatal(1,"retire ignored pending read");
 while(!rd_rsp_valid)@(negedge clk);
 repeat(12)begin @(negedge clk);if(retire_ready||rd_req_ready||!rd_rsp_valid)$fatal(1,"retire discarded held response");end
 rd_rsp_ready=1;@(negedge clk);rd_rsp_ready=0;
 #1;if(!retire_ready)$fatal(1,"retire did not resume after response drain");
 @(negedge clk);retire_valid=0;#1;if(!start_ready||rd_rsp_valid)$fatal(1,"read-drained retire failed");
 end endtask
 task cancel(input integer use_reset);
 begin
 if(use_reset)reset=1;else abort=1;in_valid=0;in_last=0;rd_req_valid=0;rd_rsp_ready=0;envelope_ready=0;error_ready=0;retire_valid=0;
 @(negedge clk);reset=0;abort=0;#1;
 if(!start_ready||envelope_validated||error_valid||rd_rsp_valid)$fatal(1,"cancel left stale output");
 repeat(3)begin @(negedge clk);if(rd_rsp_valid||envelope_validated)$fatal(1,"delayed stale output after cancel");end
 cancel_cases=cancel_cases+1;
 end endtask
 integer mode,phase;
 initial begin
 repeat(4)@(negedge clk);reset=0;
 fd=$fopen("vectors.hex","r");if(!fd)$fatal(1,"missing vectors");
 while(!$feof(fd))begin
  rc=$fscanf(fd,"%h %h %h %h %h %h\n",declared,actual,expected,ep,check_ep,skip_data);
  if(rc==6)begin
   for(i=0;i<actual;i=i+1)begin rc=$fscanf(fd,"%h\n",bytes[i]);if(rc!=1)$fatal(1,"short fixture");end
   active_owner=64'h100000000+case_id;launch(declared,active_owner,ep,check_ep);
   if(!skip_data)feed(actual,1);
   while(!envelope_validated&&!error_valid)@(negedge clk);
   if(expected)begin
    accept_certificate();accepted=accepted+1;
    if(case_id==0)begin
     // A foreign retire cannot quiesce or free the current owner's RAM.
     retire_valid=1;retire_owner=active_owner^64'h100000000;retire_epoch=desc_epoch;#1;if(retire_ready)$fatal(1,"foreign retire accepted");
     read_check(0,active_owner,desc_epoch,0,11);retire_valid=0;
    end
    read_check(0,active_owner^1,desc_epoch,1,5);read_check(0,active_owner^64'h100000000,desc_epoch,1,5);read_check(0,active_owner,desc_epoch^1,1,5);read_check(actual,active_owner,desc_epoch,1,5);read_check(32'hffffffff,active_owner,desc_epoch,1,5);
    for(n=0;n<actual;n=n+1)begin read_check(n,active_owner,desc_epoch,0,(n%1024==0)?7:0);replay_bytes=replay_bytes+1;end
    if(case_id==0)retire_while_read_held();else retire();
   end else begin
    if(envelope_validated)$fatal(1,"invalid fixture certified case%0d",case_id);
    if(!error_valid||error_code==0||desc_owner!==active_owner||rd_req_ready||rd_rsp_valid)$fatal(1,"invalid error state");
    repeat(8)@(negedge clk);error_ready=1;@(negedge clk);error_ready=0;rejected=rejected+1;
   end
   $display("CASE_PASS id=%0d expected=%0d bytes=%0d",case_id,expected,actual);$fflush();case_id=case_id+1;
  end
 end
 // Last stored fixture is a valid native key, even though its start was oversized.
 declared=actual;ep=1;check_ep=1;
 for(mode=0;mode<2;mode=mode+1)begin
  for(phase=0;phase<6;phase=phase+1)begin
   active_owner=64'h200000000+mode*16+phase;launch(actual,active_owner,ep,check_ep);
   if(phase==0)begin for(i=0;i<32;i=i+1)begin in_valid=1;in_data=bytes[i];in_last=0;@(negedge clk);end cancel(mode);end
   else begin
    if(phase==5)bytes[actual-1]=bytes[actual-1]^128;
    feed(actual,0);
    if(phase==1)cancel(mode); // CHECK: complete ingress, certificate not emitted yet.
    else if(phase==2)begin while(!envelope_validated)@(negedge clk);cancel(mode);end
    else if(phase==5)begin while(!error_valid)@(negedge clk);cancel(mode);bytes[actual-1]=bytes[actual-1]^128;end
    else begin
     accept_certificate();
     @(negedge clk);rd_req_valid=1;rd_req_address=61;rd_req_owner=active_owner;rd_req_epoch=desc_epoch;
     while(!rd_req_ready)@(negedge clk);@(negedge clk);rd_req_valid=0;
     if(phase==4)begin while(!rd_rsp_valid)@(negedge clk);repeat(7)@(negedge clk);end
     cancel(mode);
    end
   end
  end
 end
 active_owner=64'h300000000;launch(actual,active_owner,ep,check_ep);feed(actual,0);accept_certificate();read_check(61,active_owner,desc_epoch,0,15);read_check(61,64'h200000014,desc_epoch,1,15);retire();
 begin: issued_read_cancel
  integer mode2;
  for(mode2=0;mode2<2;mode2=mode2+1)begin
   active_owner=64'h500000000+mode2;
   launch(actual,active_owner,ep,check_ep);feed(actual,0);accept_certificate();
   @(negedge clk);rd_req_valid=1;rd_req_address=61;rd_req_owner=active_owner;rd_req_epoch=desc_epoch;
   while(!rd_req_ready)@(negedge clk);@(negedge clk);rd_req_valid=0;
   wait(dut.read_pending);@(negedge clk);
   if(dut.request_pending||!dut.read_pending||rd_rsp_valid)$fatal(1,"issued-read cancellation coverage");
   cancel(mode2);
  end
  active_owner=64'h600000000;launch(actual,active_owner,ep,check_ep);feed(actual,0);accept_certificate();
  read_check(61,active_owner,desc_epoch,0,7);retire();
  $display("EXTRA_PIPELINE_CANCEL_PASS issued_read_abort=1 issued_read_reset=1 fresh_owner_replay=1");
 end
 $display("ENVELOPE_PASS cases=%0d certified=%0d rejected=%0d full_replay_bytes=%0d cancel_cases=%0d cycles=%0d seed=6b4103ab",case_id,accepted,rejected,replay_bytes,cancel_cases,cycles);$finish;
 end
endmodule
