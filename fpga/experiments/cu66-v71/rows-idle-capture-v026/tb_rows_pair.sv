`timescale 1ns/1ps
module tb_rows_pair;
 parameter integer BANKS=1;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,abort_i=0,start_valid=0,key=0,tile_valid=0,tile_key=0,tile_last=0,data_ready=0;
 reg[31:0]frame_id=1,tile_frame_id=1;reg[511:0]tile_pixels=0;reg[1:0]tile_plane=0;reg[16:0]tile_index=0;
 wire[1:0]sr,tr,dv,dl,busy,done,error,aborted,wb;wire[7:0]data[0:1],ec[0:1];wire[31:0]at[0:1],eb[0:1],ww[0:1],wr[0:1],ist[0:1],ost[0:1];wire[1:0]ep[0:1];wire[16:0]ei[0:1];
 cu71_tile_rows_reference #(.STRIP_BANKS(BANKS)) old(.clk,.rst,.abort_i,.start_valid,.start_ready(sr[0]),.frame_id,.key,.tile_valid,.tile_ready(tr[0]),.tile_pixels,.tile_frame_id,.tile_key,.tile_plane,.tile_index,.tile_last,.data_valid(dv[0]),.data_ready,.data(data[0]),.data_last(dl[0]),.busy(busy[0]),.done(done[0]),.error(error[0]),.aborted(aborted[0]),.error_code(ec[0]),.accepted_tiles(at[0]),.emitted_bytes(eb[0]),.strip_word_writes(ww[0]),.strip_word_reads(wr[0]),.input_stall_cycles(ist[0]),.output_stall_cycles(ost[0]),.write_busy(wb[0]),.expected_plane(ep[0]),.expected_index(ei[0]));
 cu71_tile_rows #(.STRIP_BANKS(BANKS)) dut(.clk,.rst,.abort_i,.start_valid,.start_ready(sr[1]),.frame_id,.key,.tile_valid,.tile_ready(tr[1]),.tile_pixels,.tile_frame_id,.tile_key,.tile_plane,.tile_index,.tile_last,.data_valid(dv[1]),.data_ready,.data(data[1]),.data_last(dl[1]),.busy(busy[1]),.done(done[1]),.error(error[1]),.aborted(aborted[1]),.error_code(ec[1]),.accepted_tiles(at[1]),.emitted_bytes(eb[1]),.strip_word_writes(ww[1]),.strip_word_reads(wr[1]),.input_stall_cycles(ist[1]),.output_stall_cycles(ost[1]),.write_busy(wb[1]),.expected_plane(ep[1]),.expected_index(ei[1]));
 integer cycles=0,qualified=0,accepted=0,frames=0,abort_checks=0,reset_checks=0,bad_checks=0;reg[31:0]random_state=32'h90ac12fe;
 always @(negedge clk)begin random_state={random_state[30:0],random_state[31]^random_state[21]^random_state[1]^random_state[0]};data_ready=(cycles%113<87)&&random_state[1:0]!=0;end
 always @(posedge clk)begin
  cycles<=cycles+1;
  if(dv[0]&&data_ready)qualified<=qualified+1;
  if(tile_valid&&tr[0])accepted<=accepted+1;
  #1;
  if(cycles>2)begin
   if({sr[0],tr[0],dv[0],busy[0],done[0],error[0],aborted[0],ec[0],at[0],eb[0],ww[0],wr[0],ist[0],ost[0],wb[0],ep[0],ei[0]}!=={sr[1],tr[1],dv[1],busy[1],done[1],error[1],aborted[1],ec[1],at[1],eb[1],ww[1],wr[1],ist[1],ost[1],wb[1],ep[1],ei[1]})$fatal(1,"control divergence cycle%0d",cycles);
   if(dv[0]&&{dl[0],data[0]}!=={dl[1],data[1]})$fatal(1,"qualified data divergence cycle%0d",cycles);
   if(wb[0]&&old.captured_tile!==dut.captured_tile)$fatal(1,"authoritative payload mismatch cycle%0d",cycles);
   if(old.ram_write_enable!==dut.ram_write_enable)$fatal(1,"RAM write authority divergence");
  end
 end
 task tick;begin @(posedge clk);#2;end endtask
 task begin_frame(input[31:0]id,input k);
 begin @(negedge clk);frame_id=id;key=k;start_valid=1;while(!sr[0])tick();tick();@(negedge clk);start_valid=0;end endtask
 task offer(input[1:0]p,input integer index,input integer bad);
 reg take;
 begin
  @(negedge clk);tile_plane=p;tile_index=index;tile_frame_id=frame_id+(bad==1);tile_key=key;tile_last=(p==2&&index==1349)^(bad==2);tile_valid=1;
  for(integer j=0;j<64;j=j+1)tile_pixels[j*8+:8]=(index*7+j*19+p*83+frame_id);
  take=0;while(!take)begin @(posedge clk);take=tr[0];#2;end
  @(negedge clk);tile_valid=0;
 end endtask
 task complete_frame(input[31:0]id,input k);
 begin begin_frame(id,k);for(integer p=0;p<3;p=p+1)for(integer i=0;i<(p==0?5400:1350);i=i+1)offer(p,i,0);while(!done[0])tick();if(eb[0]!=518404||at[0]!=8100||error[0])$fatal(1,"frame count/error");frames=frames+1;repeat(4)tick();end endtask
 initial begin
  repeat(5)tick();@(negedge clk);rst=0;
  begin_frame(10,1);offer(0,0,0);@(negedge clk);abort_i=1;tick();if(!aborted[0])$fatal(1,"abort missing");abort_checks=abort_checks+1;@(negedge clk);abort_i=0;
  begin_frame(11,1);offer(0,0,0);@(negedge clk);rst=1;repeat(3)tick();reset_checks=reset_checks+1;@(negedge clk);rst=0;
  begin_frame(12,1);offer(0,0,1);if(!error[0]||ec[0]!=2)$fatal(1,"identity failure missing");bad_checks=bad_checks+1;
  begin_frame(13,0);offer(0,0,2);if(!error[0]||ec[0]!=3)$fatal(1,"last flag failure missing");bad_checks=bad_checks+1;
  complete_frame(20,1);complete_frame(21,0);
  if(qualified<1036808||abort_checks!=1||reset_checks!=1||bad_checks!=2)$fatal(1,"coverage missing");
  $display("ROW_IDLE_CAPTURE_PAIR_PASS banks%0d frames%0d qualified_bytes%0d accepted%0d cycles%0d abort%0d reset%0d invalid%0d authoritative_payload_and_RAM_write_authority_equal",BANKS,frames,qualified,accepted,cycles,abort_checks,reset_checks,bad_checks);$finish;
 end
 initial begin #100000000;$fatal(1,"pair watchdog");end
endmodule
