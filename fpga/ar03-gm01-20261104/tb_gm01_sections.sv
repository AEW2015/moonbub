`timescale 1ns/1ps
module tb;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,abort=0,start_valid=0,in_valid=0,in_last=0,certificate_ready=0,error_ready=0;
 reg[63:0]start_owner=0;reg[31:0]start_bytes=0,start_epoch=0,start_frame=0,start_reference=0;reg start_key=0;reg[7:0]in_data=0;
 wire start_ready,in_ready,inner_sections_validated,error_valid;wire[3:0]error_code;wire[63:0]error_owner;
 wire[63:0]desc_owner;wire[31:0]desc_epoch,desc_frame,desc_reference,desc_map_bytes;wire desc_key;
 wire[15:0]desc_width,desc_height;wire[95:0]desc_plane_offsets,desc_plane_lengths;wire[47:0]desc_blocks_w,desc_blocks_h;
 reg block_req_valid=0,block_ready=0,retire_valid=0;
 reg[63:0]block_req_owner=0,retire_owner=0;reg[31:0]block_req_epoch=0,retire_epoch=0;
 reg[1:0]block_req_plane=0;reg[15:0]block_req_x=0,block_req_y=0;
 wire block_req_ready,block_valid,block_error,retire_ready;
 wire[63:0]block_owner;wire[31:0]block_epoch,block_index;wire[1:0]block_plane;wire[15:0]block_x,block_y;wire[5:0]block_scale;
 gm01_sections dut(.*);
 reg[7:0]bytes[0:65535];integer fd,rc,declared,actual,expected,ep,fr,refid,key,skip_data;
 integer case_id=0,i,plane,x,y,bw,bh,cycles=0,certified=0,rejected=0,blocks=0,cancels=0,seed=32'h639c241a;
 reg[63:0]active_owner;reg[1023:0]held_desc;reg[199:0]held_block;reg[67:0]held_error;
 reg hold_desc=0,hold_block=0,hold_error=0;
 wire[1023:0]descriptor_bus={desc_owner,desc_epoch,desc_frame,desc_reference,desc_key,desc_width,desc_height,desc_map_bytes,desc_plane_offsets,desc_plane_lengths,desc_blocks_w,desc_blocks_h};
 wire[199:0]block_bus={block_error,block_owner,block_epoch,block_plane,block_x,block_y,block_index,block_scale};
 always @(posedge clk)begin
  cycles=cycles+1;if(cycles>5000000)$fatal(1,"watchdog");
  if(reset||abort)begin hold_desc<=0;hold_block<=0;hold_error<=0;end else begin
   if(hold_desc&&(!inner_sections_validated||descriptor_bus!==held_desc))$fatal(1,"held certificate changed");
   hold_desc<=inner_sections_validated&&!certificate_ready;if(inner_sections_validated&&!certificate_ready)held_desc<=descriptor_bus;
   if(hold_block&&(!block_valid||block_bus!==held_block))$fatal(1,"held block changed");
   hold_block<=block_valid&&!block_ready;if(block_valid&&!block_ready)held_block<=block_bus;
   if(hold_error&&(!error_valid||{error_owner,error_code}!==held_error))$fatal(1,"held error changed");
   hold_error<=error_valid&&!error_ready;if(error_valid&&!error_ready)held_error<={error_owner,error_code};
  end
 end
 function[31:0]le32(input integer at);begin le32={bytes[at+3],bytes[at+2],bytes[at+1],bytes[at]};end endfunction
 function[15:0]le16(input integer at);begin le16={bytes[at+1],bytes[at]};end endfunction
 task launch(input integer size,input[63:0]own);
 begin @(negedge clk);start_valid=1;start_bytes=size;start_owner=own;start_epoch=ep;start_frame=fr;start_reference=refid;start_key=key;
 while(!start_ready)@(negedge clk);@(negedge clk);start_valid=0;end endtask
 task feed(input integer count,input integer gaps,input integer final_last);
 integer j;begin
 for(j=0;j<count;j=j+1)begin
  if(gaps&&(($random(seed)&31)==0))begin in_valid=0;repeat(2)@(negedge clk);end
  in_valid=1;in_data=bytes[j];in_last=final_last&&(j==count-1);
  if(!in_ready)$fatal(1,"ingress unexpected backpressure case%0d byte%0d",case_id,j);
  @(posedge clk);if(inner_sections_validated||block_valid)$fatal(1,"publication before full validation");@(negedge clk);
 end in_valid=0;in_last=0;
 end endtask
 task check_descriptor;
 integer p,pos,pw,ph;begin
 if(desc_owner!==active_owner||desc_epoch!==le32(6)||desc_frame!==le32(10)||desc_reference!==le32(14)||desc_key!==bytes[5][0]||desc_width!==le16(18)||desc_height!==le16(20)||desc_map_bytes!==le32(30))$fatal(1,"certificate header case%0d",case_id);
 pos=46+le32(30);
 for(p=0;p<3;p=p+1)begin
  pw=p?le16(18)/2:le16(18);ph=p?le16(20)/2:le16(20);
  if(desc_plane_offsets[p*32+:32]!==pos||desc_plane_lengths[p*32+:32]!==le32(34+4*p)||desc_blocks_w[p*16+:16]!==((pw+7)/8)||desc_blocks_h[p*16+:16]!==((ph+7)/8))$fatal(1,"plane descriptor p%0d",p);
  pos=pos+le32(34+4*p);
 end if(pos!=actual-4)$fatal(1,"plane end");
 end endtask
 task accept_certificate;
 begin
 while(!inner_sections_validated&&!error_valid)@(negedge clk);
 if(error_valid)$fatal(1,"unexpected error case%0d code%0d",case_id,error_code);
 check_descriptor();repeat(5)@(negedge clk);
 block_req_valid=1;block_req_owner=active_owner;block_req_epoch=ep;
 repeat(3)begin @(negedge clk);if(block_req_ready||block_valid)$fatal(1,"query before certificate handshake");end
 block_req_valid=0;certificate_ready=1;@(negedge clk);certificate_ready=0;
 end endtask
 task query(input integer p,input integer xx,input integer yy,input[63:0]own,input[31:0]epoch_value,input integer bad,input integer stalls);
 integer cell_index,scale,index,bw_;begin
 @(negedge clk);block_req_valid=1;block_req_owner=own;block_req_epoch=epoch_value;block_req_plane=p;block_req_x=xx;block_req_y=yy;block_ready=0;
 while(!block_req_ready)@(negedge clk);@(negedge clk);block_req_valid=0;
 if(block_valid)$fatal(1,"map response not synchronous");
 while(!block_valid)@(negedge clk);
 cell_index=(p?yy:yy/2)*le16(26)+(p?xx:xx/2);scale=bad?0:8<<((bytes[46+cell_index/4]>>(6-2*(cell_index%4)))&3);
 bw_=((p?le16(18)/2:le16(18))+7)/8;index=bad?0:yy*bw_+xx;
 if(block_owner!==own||block_epoch!==epoch_value||block_error!==bad[0]||block_plane!==p[1:0]||block_x!==xx[15:0]||block_y!==yy[15:0]||block_index!==index||block_scale!==scale[5:0])$fatal(1,"block mismatch case%0d p%0d xy%0d,%0d scale%0d/%0d bad%0d",case_id,p,xx,yy,block_scale,scale,bad);
 repeat(stalls)@(negedge clk);block_ready=1;@(negedge clk);block_ready=0;blocks=blocks+!bad;
 end endtask
 task retire;
 begin @(negedge clk);retire_valid=1;retire_owner=active_owner;retire_epoch=ep;#1;
 if(!retire_ready)$fatal(1,"drained retire not ready");@(negedge clk);retire_valid=0;#1;
 if(!start_ready||block_valid)$fatal(1,"retire failed");end endtask
 task drain_retire;
 begin
 // Foreign high-half owner cannot block requests or release the lease.
 @(negedge clk);retire_valid=1;retire_owner=active_owner^64'h100000000;retire_epoch=ep;#1;
 if(retire_ready||!block_req_ready)$fatal(1,"foreign retire interfered");
 @(negedge clk);retire_valid=0;
 // Request enters synchronous map pipe. Matching retire fences new queries.
 block_req_valid=1;block_req_owner=active_owner;block_req_epoch=ep;block_req_plane=0;block_req_x=0;block_req_y=0;
 @(negedge clk);block_req_valid=0;retire_valid=1;retire_owner=active_owner;retire_epoch=ep;#1;
 if(retire_ready||block_req_ready)$fatal(1,"retire skipped pending query");
 while(!block_valid)@(negedge clk);
 repeat(4)begin @(negedge clk);if(retire_ready||block_req_ready||!block_valid)$fatal(1,"retire skipped held result");end
 block_ready=1;@(negedge clk);block_ready=0;#1;if(!retire_ready)$fatal(1,"retire remained blocked after drain");
 @(negedge clk);retire_valid=0;#1;if(!start_ready||block_valid)$fatal(1,"drained retire failed");
 end endtask
 task cancel_now(input integer use_reset);
 begin @(negedge clk);if(use_reset)reset=1;else abort=1;#1;
 if(inner_sections_validated||block_valid||error_valid||in_ready||block_req_ready)$fatal(1,"valid during cancellation");
 @(negedge clk);reset=0;abort=0;start_valid=0;in_valid=0;in_last=0;block_req_valid=0;block_ready=0;certificate_ready=0;error_ready=0;retire_valid=0;
 repeat(3)@(negedge clk);if(!start_ready||block_valid||inner_sections_validated||error_valid)$fatal(1,"stale outputs after cancel");cancels=cancels+1;
 end endtask
 task cancellation_cases;
 integer mode,phase;begin
 // Caller preserves a known valid packet; exercise all ownership pipeline states.
 for(mode=0;mode<2;mode=mode+1)for(phase=0;phase<6;phase=phase+1)begin
  active_owner=64'h9e00000000+mode*16+phase;launch(actual,active_owner);
  if(phase==0)feed(20,0,0);
  else if(phase==5)begin feed(actual-1,0,1);while(!error_valid)@(negedge clk);end
  else begin
   feed(actual,0,1);
   if(phase==1)begin if(dut.state!==2)$fatal(1,"not CHECK");end
   else begin
    while(!inner_sections_validated)@(negedge clk);
    if(phase>2)begin
     certificate_ready=1;@(negedge clk);certificate_ready=0;
     block_req_valid=1;block_req_owner=active_owner;block_req_epoch=ep;block_req_plane=0;block_req_x=0;block_req_y=0;
     @(negedge clk);block_req_valid=0;
     if(phase==3)begin if(!dut.read_pending)$fatal(1,"not pending");end
     else while(!block_valid)@(negedge clk);
    end
   end
  end
  // Assert cancellation immediately in selected phase, before another clock.
  if(mode)reset=1;else abort=1;#1;if(inner_sections_validated||block_valid||error_valid)$fatal(1,"cancel valid mask");
  @(negedge clk);reset=0;abort=0;start_valid=0;in_valid=0;block_req_valid=0;certificate_ready=0;
  repeat(3)@(negedge clk);if(!start_ready||inner_sections_validated||block_valid||error_valid)$fatal(1,"cancel stale result");cancels=cancels+1;
 end
 active_owner=64'hfeed00000001;launch(actual,active_owner);feed(actual,1,1);accept_certificate();
 query(0,0,0,64'h9e00000000,ep,1,2);query(0,0,0,active_owner,ep,0,2);retire();
 end endtask
 initial begin
 repeat(4)@(negedge clk);reset=0;
 fd=$fopen("vectors.hex","r");if(!fd)$fatal(1,"no vectors");
 while(!$feof(fd))begin
  rc=$fscanf(fd,"%h %h %h %h %h %h %h %h",declared,actual,expected,ep,fr,refid,key,skip_data);
  if(rc==-1||(rc==0&&$feof(fd)))begin end else begin
   if(rc!=8)$fatal(1,"bad metadata %0d",rc);
   for(i=0;i<actual;i=i+1)begin rc=$fscanf(fd,"%h",bytes[i]);if(rc!=1)$fatal(1,"bad byte");end
   active_owner=64'h123400000000+case_id;launch(declared,active_owner);$display("START case=%0d bytes=%0d",case_id,actual);
   if(!skip_data)feed(actual,1,1);
   while(!inner_sections_validated&&!error_valid)@(negedge clk);
   if(expected)begin
    accept_certificate();
    for(plane=0;plane<3;plane=plane+1)begin
     bw=((plane?le16(18)/2:le16(18))+7)/8;bh=((plane?le16(20)/2:le16(20))+7)/8;
     for(y=0;y<bh;y=y+1)for(x=0;x<bw;x=x+1)query(plane,x,y,active_owner,ep,0,(($random(seed)&15)==0)?3:0);
    end
    query(0,0,0,active_owner^1,ep,1,2);query(0,0,0,active_owner^64'h100000000,ep,1,2);
    query(0,0,0,active_owner,ep^1,1,2);query(3,0,0,active_owner,ep,1,2);
    query(0,65535,0,active_owner,ep,1,2);query(0,0,65535,active_owner,ep,1,2);
    if(case_id==0)drain_retire();else retire();certified=certified+1;
    if(case_id==0)cancellation_cases();
   end else begin
    if(!error_valid)$fatal(1,"unexpected certificate case%0d",case_id);
    if(error_owner!==active_owner)$fatal(1,"error owner");
    repeat(6)@(negedge clk);$display("REJECT case=%0d code=%0d",case_id,error_code);
    error_ready=1;@(negedge clk);error_ready=0;rejected=rejected+1;
   end
   $display("CASE_PASS id=%0d expected=%0d bytes=%0d",case_id,expected,actual);$fflush();case_id=case_id+1;
  end
 end
 $fclose(fd);$display("GM01_SECTIONS_PASS cases=%0d certified=%0d rejected=%0d block_descriptors=%0d cancel_cases=%0d cycles=%0d seed=639c241a",case_id,certified,rejected,blocks,cancels,cycles);$finish;
 end
endmodule

