`timescale 1ns/1ps
module tb_tile_address;
 logic clk=0;always #5 clk=~clk;
 logic rst=1,abort_i=0,read_valid=0,write_valid=0,read_rsp_ready=0,write_done_ready=0;
 logic[63:0]read_generation=1,write_generation=1;
 logic[1:0]read_bank=0,read_plane=0,write_bank=0,write_plane=0;
 logic[16:0]read_index=0,write_index=0;logic[511:0]write_pixels=0;
 wire[1:0]read_ready,write_ready,read_rsp_valid,write_done_valid,tile_busy,tile_aborted;
 wire[1:0]read_rsp_error,write_done_error,word_req_valid,word_req_ready,word_req_write,word_rsp_ready;
 wire[63:0]read_rsp_generation[2],write_done_generation[2];
 wire[1:0]read_rsp_bank[2],read_rsp_plane[2],write_done_bank[2],write_done_plane[2];
 wire[16:0]read_rsp_index[2],write_done_index[2];wire[511:0]read_rsp_pixels[2];
 wire[23:0]word_req_addr[2];wire[15:0]word_req_data[2],word_req_burst_mask[2];wire[127:0]word_req_burst_data[2];
 logic[1:0]word_rsp_valid=0,word_rsp_error=0;logic[15:0]word_rsp_data[2];
 logic[15:0]memory[0:1][0:777599];
 integer ordinal[2],wait_cycles[2],saved_serial[2];logic[1:0]pending=0,seen_aborted=0;
 integer cycles=0,serial=0,checks=0,requests=0,cancel_checks=0;
 integer expected_bank=0,expected_plane=0,expected_index=0;logic expected_write=0;
 logic[511:0]expected_pixels=0;logic request_stall=0,release_hold=1;
 integer hold_at=0,error_at=0;
 `define PORTS .clk,.rst,.abort_i,.read_valid,.read_ready(read_ready[g]),.read_generation,.read_bank,.read_plane,.read_index, \
 .read_rsp_valid(read_rsp_valid[g]),.read_rsp_ready,.read_rsp_generation(read_rsp_generation[g]),.read_rsp_bank(read_rsp_bank[g]),.read_rsp_plane(read_rsp_plane[g]),.read_rsp_index(read_rsp_index[g]),.read_rsp_pixels(read_rsp_pixels[g]),.read_rsp_error(read_rsp_error[g]), \
 .write_valid,.write_ready(write_ready[g]),.write_generation,.write_bank,.write_plane,.write_index,.write_pixels, \
 .write_done_valid(write_done_valid[g]),.write_done_ready,.write_done_generation(write_done_generation[g]),.write_done_bank(write_done_bank[g]),.write_done_plane(write_done_plane[g]),.write_done_index(write_done_index[g]),.write_done_error(write_done_error[g]), \
 .tile_busy(tile_busy[g]),.tile_aborted(tile_aborted[g]),.word_req_valid(word_req_valid[g]),.word_req_ready(word_req_ready[g]),.word_req_write(word_req_write[g]),.word_req_addr(word_req_addr[g]),.word_req_data(word_req_data[g]),.word_req_burst_data(word_req_burst_data[g]),.word_req_burst_mask(word_req_burst_mask[g]), \
 .word_rsp_valid(word_rsp_valid[g]),.word_rsp_ready(word_rsp_ready[g]),.word_rsp_data(word_rsp_data[g]),.word_rsp_error(word_rsp_error[g])
 generate for(genvar g=0;g<2;g=g+1)begin:peer
  if(g==0)begin:original cu71_tile_memory dut(`PORTS);end
  else begin:candidate cu71_tile_memory_address_pipe dut(`PORTS);end
  assign word_req_ready[g]=!pending[g]&&!word_rsp_valid[g]&&!request_stall&&((cycles+g)%5!=0);
 end endgenerate
 `undef PORTS
 function automatic integer address(input integer bank,plane,index,word_number);
  integer base,pitch,columns;
  begin
   base=bank==0?'h080000:bank==1?'h480000:'h880000;
   pitch=plane==0?360:180;columns=plane==0?90:45;
   address=base+(plane==0?0:plane==1?172800:216000)+(index/columns)*8*pitch+(index%columns)*4+(word_number/4)*pitch+(word_number%4);
  end
 endfunction
 function automatic integer mapped(input integer addr);
  begin
   if(addr>='h080000&&addr<'h080000+259200)mapped=addr-'h080000;
   else if(addr>='h480000&&addr<'h480000+259200)mapped=259200+addr-'h480000;
   else if(addr>='h880000&&addr<'h880000+259200)mapped=518400+addr-'h880000;
   else begin $fatal(1,"unmapped physical request %h",addr);mapped=0;end
  end
 endfunction
 function automatic logic[511:0]pattern(input integer bank,plane,index);
  logic[511:0]v;
  begin for(integer n=0;n<32;n=n+1)v[n*16+:16]=16'(bank*27631+plane*5327+index*53+n*257);return v;end
 endfunction
 always @(posedge clk)begin
  cycles<=cycles+1;
  for(integer g=0;g<2;g=g+1)begin:backend
   integer wi,addr,aligned,at;logic[127:0]payload;logic[15:0]mask;
   if(rst)begin pending[g]<=0;word_rsp_valid[g]<=0;ordinal[g]=0;saved_serial[g]=serial;seen_aborted[g]<=0;end
   else begin
    if(saved_serial[g]!=serial)begin ordinal[g]=0;saved_serial[g]=serial;seen_aborted[g]<=0;end
    if(tile_aborted[g])seen_aborted[g]<=1;
    if(word_rsp_valid[g]&&word_rsp_ready[g])begin word_rsp_valid[g]<=0;pending[g]<=0;end
    else if(pending[g]&&!word_rsp_valid[g]&&(ordinal[g]!=hold_at||release_hold))begin
     if(wait_cycles[g]==0)word_rsp_valid[g]<=1;else wait_cycles[g]=wait_cycles[g]-1;
    end
    if(word_req_valid[g]&&word_req_ready[g])begin
     ordinal[g]=ordinal[g]+1;requests=requests+1;
     wi=expected_write?(ordinal[g]-1)*4:ordinal[g]-1;
     if(wi>31)$fatal(1,"too many requests peer=%0d",g);
     addr=address(expected_bank,expected_plane,expected_index,wi);
     if(word_req_addr[g]!==24'(addr)||word_req_write[g]!==expected_write)$fatal(1,"physical address mismatch peer=%0d plane=%0d index=%0d wi=%0d got=%h expected=%h",g,expected_plane,expected_index,wi,word_req_addr[g],addr);
     aligned=addr&'hfffff8;mask=16'hffff^(16'h00ff<<((addr%8)*2));
     if(word_req_burst_mask[g]!==mask)$fatal(1,"mask mismatch");
     if(expected_write)begin
      payload=128'(expected_pixels[(wi/4)*64+:64])<<((addr%8)*16);
      if(word_req_burst_data[g]!==payload||word_req_data[g]!==expected_pixels[wi*16+:16])$fatal(1,"write payload mismatch");
      for(integer n=0;n<8;n=n+1)begin
       at=mapped(aligned+n);
       if(!mask[n*2])memory[g][at][7:0]=payload[n*16+:8];
       if(!mask[n*2+1])memory[g][at][15:8]=payload[n*16+8+:8];
      end
     end
     word_rsp_data[g]<=memory[g][mapped(addr)];word_rsp_error[g]<=(error_at==ordinal[g]);
     pending[g]<=1;wait_cycles[g]=2+(ordinal[g]+g)%4;
    end
   end
  end
 end
 task automatic tick;begin @(posedge clk);#1;end endtask
 task automatic send(input bit wr,input integer b,p,i,input logic[63:0]generation,input bit both_valid=0);
  begin
   @(negedge clk);while(tile_busy!=0)@(negedge clk);
   expected_write=wr;expected_bank=b;expected_plane=p;expected_index=i;expected_pixels=pattern(b,p,i);serial=serial+1;
   write_pixels=expected_pixels;write_bank=2'(b);read_bank=2'(b);write_plane=2'(p);read_plane=2'(p);write_index=17'(i);read_index=17'(i);write_generation=generation;read_generation=generation;
   write_valid=wr||both_valid;read_valid=!wr||both_valid;#1;
   if(wr?write_ready!==2'b11:read_ready!==2'b11)$fatal(1,"not jointly ready");
   tick();@(negedge clk);write_valid=0;read_valid=0;
  end
 endtask
 task automatic complete(input bit wr,input integer b,p,i,input logic[63:0]generation,input bit bad,input integer stall);
  logic[511:0]expected;integer timeout;
  begin
   timeout=0;
   while(wr?write_done_valid!==2'b11:read_rsp_valid!==2'b11)begin tick();if(timeout++>1000)$fatal(1,"response timeout");end
   expected=bad?512'd0:pattern(b,p,i);
   if(bad&&error_at>0&&!wr)for(integer n=0;n<error_at-1;n=n+1)expected[n*16+:16]=expected_pixels[n*16+:16];
   for(integer g=0;g<2;g=g+1)begin
    if(wr)begin
     if(write_done_generation[g]!==generation||write_done_bank[g]!==2'(b)||write_done_plane[g]!==2'(p)||write_done_index[g]!==17'(i)||write_done_error[g]!==bad)$fatal(1,"write identity/error");
    end else if(read_rsp_generation[g]!==generation||read_rsp_bank[g]!==2'(b)||read_rsp_plane[g]!==2'(p)||read_rsp_index[g]!==17'(i)||read_rsp_error[g]!==bad||(!bad&&read_rsp_pixels[g]!==expected))$fatal(1,"read identity/pixels peer=%0d",g);
   end
   repeat(stall)begin tick();if(wr?write_done_valid!==2'b11:read_rsp_valid!==2'b11)$fatal(1,"stalled result lost");if(!wr&&(read_rsp_pixels[0]!==expected||read_rsp_pixels[1]!==expected))$fatal(1,"stalled payload changed");end
   @(negedge clk);if(wr)write_done_ready=1;else read_rsp_ready=1;tick();@(negedge clk);write_done_ready=0;read_rsp_ready=0;checks=checks+1;
  end
 endtask
 initial begin
  for(integer g=0;g<2;g=g+1)for(integer n=0;n<777600;n=n+1)memory[g][n]=16'ha55a;
  repeat(3)tick();@(negedge clk);rst=0;
  // Exhaustive valid row/column, all three banks and planes. Every physical
  // canonical word is written/read; masked neighboring words remain intact.
  for(integer b=0;b<3;b=b+1)for(integer p=0;p<3;p=p+1)begin
   for(integer i=0;i<(p==0?5400:1350);i=i+1)begin
    send(1,b,p,i,64'h123456789abcdef0);complete(1,b,p,i,64'h123456789abcdef0,0,i%509==0?257:0);
    send(0,b,p,i,64'hfedcba9876543210);complete(0,b,p,i,64'hfedcba9876543210,0,i%509==0?257:0);
   end
  end
  for(integer n=0;n<777600;n=n+1)if(memory[0][n]!==memory[1][n])$fatal(1,"full physical contents mismatch %0d",n);
  // Invalid-bank/plane/index/generation acceptance emits an error and no words.
  for(integer wr=0;wr<2;wr=wr+1)begin
   send(1'(wr),3,0,0,1);complete(1'(wr),3,0,0,1,1,3);if(ordinal[0]||ordinal[1])$fatal(1,"bad bank issued memory");
   send(1'(wr),0,3,0,1);complete(1'(wr),0,3,0,1,1,3);if(ordinal[0]||ordinal[1])$fatal(1,"bad plane issued memory");
   for(integer p=0;p<3;p=p+1)begin
    send(1'(wr),0,p,p==0?5400:1350,1);complete(1'(wr),0,p,p==0?5400:1350,1,1,3);if(ordinal[0]||ordinal[1])$fatal(1,"bad index issued memory");
   end
   send(1'(wr),0,0,131071,1);complete(1'(wr),0,0,131071,1,1,3);
   send(1'(wr),0,0,0,0);complete(1'(wr),0,0,0,0,1,3);
  end
  // Abort and reset at every newly added address microstep, before any word
  // is accepted; parent is stalled at ISSUE for a latency-independent comparison.
  request_stall=1;
  for(integer reset_kind=0;reset_kind<2;reset_kind=reset_kind+1)for(integer wr=0;wr<2;wr=wr+1)for(integer delay_count=0;delay_count<13;delay_count=delay_count+1)begin
   send(1'(wr),2,2,1349,55);repeat(delay_count)tick();
   @(negedge clk);if(reset_kind)rst=1;else abort_i=1;#1;
   if(word_req_valid||read_rsp_valid||write_done_valid)$fatal(1,"cancel immediate gating");tick();
   if(tile_busy||ordinal[0]||ordinal[1])$fatal(1,"address cancellation issued or failed idle");
   if(!reset_kind&&tile_aborted!==2'b11)$fatal(1,"abort pulse missing");
   @(negedge clk);rst=0;abort_i=0;repeat(13)tick();if(read_rsp_valid||write_done_valid)$fatal(1,"cancel phantom result");cancel_checks=cancel_checks+1;
  end
  request_stall=0;
  // Cancel each accepted read-word/write-row response position. The peer
  // backend withholds the selected completion until abort is latched, proving
  // that ownership is retained until the actual accepted operation drains.
  for(integer wr=0;wr<2;wr=wr+1)for(integer at=1;at<=(wr?8:32);at=at+1)begin
   hold_at=at;release_hold=0;send(1'(wr),1,1,44,88);
   while(!(pending==2'b11&&ordinal[0]==at&&ordinal[1]==at))tick();
   @(negedge clk);abort_i=1;tick();if(tile_busy!==2'b11)$fatal(1,"accepted abort abandoned owner");
   @(negedge clk);abort_i=0;repeat(7)begin tick();if(tile_busy!==2'b11||read_rsp_valid||write_done_valid)$fatal(1,"accepted abort leaked before drain");end
   release_hold=1;while(tile_busy!=0)tick();repeat(2)tick();if(seen_aborted!==2'b11||ordinal[0]!=at||ordinal[1]!=at)$fatal(1,"accepted abort drain mismatch");cancel_checks=cancel_checks+1;
   hold_at=0;
  end
  for(integer n=0;n<777600;n=n+1)if(memory[0][n]!==memory[1][n])$fatal(1,"abort physical contents mismatch");
  // Backend failure at every response ordinal terminates without issuing the
  // next word, retaining the same read prefix and exact response identity.
  for(integer wr=0;wr<2;wr=wr+1)for(integer at=1;at<=(wr?8:32);at=at+1)begin
   error_at=at;send(1'(wr),0,2,1349,123);complete(1'(wr),0,2,1349,123,1,17);
   if(ordinal[0]!=at||ordinal[1]!=at)$fatal(1,"error issued extra words");error_at=0;
  end
  // A continuous simultaneous read/write choice alternates by the retained
  // arbitration preference. Both ports carry different valid identities.
  for(integer n=0;n<6;n=n+1)begin
   send(1'(n%2),1,2,1349,456,1);complete(1'(n%2),1,2,1349,456,0,7);
  end
  $display("CU71_TILE_ADDRESS_PASS full_tiles=48600 physical_words=777600 checks=%0d cancellations=%0d requests=%0d cycles=%0d",checks,cancel_checks,requests,cycles);$finish;
 end
 initial begin #2000000000;$fatal(1,"watchdog");end
endmodule
