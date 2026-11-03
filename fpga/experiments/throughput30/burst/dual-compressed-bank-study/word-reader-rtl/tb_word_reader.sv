`timescale 1ns/1ps
module tb_word_reader;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,begin_valid=0,byte_valid=0,commit_valid=0,abort_valid=0,ingress_overflow=0;
 reg[31:0] begin_id=0,begin_crc=0;reg[15:0] begin_length=0;reg[7:0]byte_data=0;
 wire begin_accept,reject,decode_grant,decode_bank,present,front_valid,read_ready,read_valid,read_error;
 wire[3:0]reject_reason;wire[31:0]decode_id,front_id,accepted_frames,dropped_frames;wire[15:0]decode_length;wire[7:0]read_data;
 reg decode_request=0,decode_done=0,decode_fail=0,vblank=0;
 wire byte_req;wire[15:0]byte_addr;
 reg start=0;wire start_accept,active,error,frame_done,out_valid;wire[31:0]out_data;wire[3:0]out_strb;
 reg out_ready=0,force_hold=0,scoreboard=0;reg[7:0]pattern_xor=0;integer cycles=0,frame_len=0,expected_offset=0,total_bytes=0,total_words=0,stall_samples=0;
 reg prev_stall=0;reg[31:0]prev_data=0;reg[3:0]prev_strb=0;integer k;reg[31:0] expected_word;reg[3:0] expected_strb;integer expected_count;
 two_bank_storage store(.clk(clk),.reset(reset),.begin_valid(begin_valid),.begin_id(begin_id),.begin_length(begin_length),.begin_crc(begin_crc),.byte_valid(byte_valid),.byte_data(byte_data),.commit_valid(commit_valid),.abort_valid(abort_valid),.ingress_overflow(ingress_overflow),.begin_accept(begin_accept),.reject(reject),.reject_reason(reject_reason),.decode_request(decode_request),.decode_done(decode_done),.decode_fail(decode_fail),.decode_grant(decode_grant),.decode_bank(decode_bank),.decode_id(decode_id),.decode_length(decode_length),.read_req(byte_req),.read_addr(byte_addr),.read_ready(read_ready),.read_valid(read_valid),.read_error(read_error),.read_data(read_data),.vblank(vblank),.present(present),.front_valid(front_valid),.front_id(front_id),.accepted_frames(accepted_frames),.dropped_frames(dropped_frames));
 word_reader dut(.clk(clk),.reset(reset),.start(start),.owned(read_ready && !decode_done && !decode_fail),.granted_length(decode_length),.start_accept(start_accept),.active(active),.error(error),.frame_done(frame_done),.byte_req(byte_req),.byte_addr(byte_addr),.byte_valid(read_valid),.byte_error(read_error),.byte_data(read_data),.out_valid(out_valid),.out_data(out_data),.out_strb(out_strb),.out_ready(out_ready));
 function automatic [7:0] pattern(input integer n);pattern=8'(n*7+32'h31);endfunction
 always @(negedge clk)begin cycles=cycles+1;out_ready=(!force_hold && ((cycles%7)<4));end
 always @(posedge clk)begin
  if(reset)begin prev_stall<=0;end else begin
   if(prev_stall && read_ready && !decode_done && !decode_fail && (!out_valid||out_data!==prev_data||out_strb!==prev_strb))$fatal(1,"backpressure stability");
   prev_stall<=out_valid&&!out_ready;prev_data<=out_data;prev_strb<=out_strb;
   if(out_valid&&!out_ready)stall_samples<=stall_samples+1;
   if(scoreboard && out_valid && out_ready)begin
    expected_word=0;expected_strb=0;expected_count=0;
    for(k=0;k<4;k=k+1)if(expected_offset+k<frame_len)begin expected_word[k*8+:8]=pattern(expected_offset+k)^pattern_xor;expected_strb[k]=1;expected_count=expected_count+1;end
    if(expected_count==0||out_data!==expected_word||out_strb!==expected_strb)$fatal(1,"word mismatch offset=%0d data=%h expected=%h strb=%b expected_strb=%b",expected_offset,out_data,expected_word,out_strb,expected_strb);
    expected_offset=expected_offset+expected_count;total_bytes=total_bytes+expected_count;total_words=total_words+1;
   end
  end
 end
 task begin_frame(input[31:0]id,input[15:0]len,input[31:0]crc);begin @(negedge clk);begin_id=id;begin_length=len;begin_crc=crc;begin_valid=1;@(posedge clk);#1;if(!begin_accept||reject)$fatal(1,"begin");@(negedge clk);begin_valid=0;end endtask
 task put(input[7:0]v);begin @(negedge clk);byte_data=v;byte_valid=1;@(posedge clk);#1;if(reject)$fatal(1,"byte");@(negedge clk);byte_valid=0;end endtask
 task commit;begin @(negedge clk);commit_valid=1;@(posedge clk);#1;if(reject)$fatal(1,"commit");@(negedge clk);commit_valid=0;end endtask
 task grant(input[31:0]id,input[15:0]len);begin @(negedge clk);decode_request=1;@(posedge clk);#1;if(!decode_grant||decode_id!=id||decode_length!=len)$fatal(1,"grant");@(negedge clk);decode_request=0;@(posedge clk);#1;if(!read_ready)$fatal(1,"not owned");end endtask
 task begin_reader;begin @(negedge clk);start=1;@(posedge clk);#1;if(!start_accept||error||!active)$fatal(1,"reader start");@(negedge clk);start=0;end endtask
 task done_and_show(input[31:0]id);begin @(negedge clk);decode_done=1;@(posedge clk);#1;@(negedge clk);decode_done=0;vblank=1;@(posedge clk);#1;if(!present||front_id!=id)$fatal(1,"presentation");@(negedge clk);vblank=0;end endtask
 task run_frame(input[31:0]id,input integer len,input[31:0]crc,input bit test_duplicate);
 integer j;begin
  begin_frame(id,16'(len),crc);for(j=0;j<len;j=j+1)put(pattern(j));commit();grant(id,16'(len));
  frame_len=len;expected_offset=0;scoreboard=1;begin_reader();
  if(test_duplicate)begin @(negedge clk);start=1;@(posedge clk);#1;if(!error||start_accept)$fatal(1,"duplicate start not rejected");@(negedge clk);start=0;end
  while(!frame_done)begin @(posedge clk);#1;end
  if(active||expected_offset!=len)$fatal(1,"frame read incomplete");scoreboard=0;done_and_show(id);
 end endtask
 initial begin
  repeat(3)@(negedge clk);reset=0;
  // Start with no decoder-owned bank must be rejected.
  @(negedge clk);start=1;@(posedge clk);#1;if(!error||active||start_accept)$fatal(1,"unowned start");@(negedge clk);start=0;
  run_frame(1,1,32'h83dcefb7,1);run_frame(2,2,32'haf86add3,0);run_frame(3,3,32'h7b11c773,0);
  run_frame(4,5,32'hee85c166,0);run_frame(5,6,32'h1a3b3bcc,0);run_frame(6,7,32'hbc73d251,0);
  run_frame(7,49149,32'ha12b3b5d,0);run_frame(8,49150,32'hd378b5b0,0);run_frame(9,49151,32'hbbd755c6,0);run_frame(10,49152,32'h7b05968b,0);
  // Leave frame 20 decoder-owned while ingesting frame 21 into bank 1.
  begin_frame(20,3,32'h7b11c773);for(integer j=0;j<3;j=j+1)put(pattern(j));commit();grant(20,3);
  begin_frame(21,5,32'h8534c724);for(integer j=0;j<5;j=j+1)put(pattern(j)^8'h80);commit();
  frame_len=3;expected_offset=0;scoreboard=1;begin_reader();while(!frame_done)begin @(posedge clk);#1;end
  if(expected_offset!=3)$fatal(1,"bank0 reader incomplete");scoreboard=0;done_and_show(20);
  grant(21,5);if(!decode_bank)$fatal(1,"expected bank1 ownership");
  frame_len=5;pattern_xor=8'h80;expected_offset=0;scoreboard=1;begin_reader();while(!frame_done)begin @(posedge clk);#1;end
  if(expected_offset!=5)$fatal(1,"bank1 reader incomplete");scoreboard=0;pattern_xor=0;done_and_show(21);
  // Cancel a backpressured word if ownership is released, then reject a new start.
  begin_frame(99,5,32'hee85c166);for(integer j=0;j<5;j=j+1)put(pattern(j));commit();grant(99,5);force_hold=1;begin_reader();
  while(!out_valid)begin @(posedge clk);#1;end
  @(negedge clk);decode_done=1;@(posedge clk);#1;if(!error||active||out_valid)$fatal(1,"released bank word not cancelled");@(negedge clk);decode_done=0;
  @(negedge clk);start=1;@(posedge clk);#1;if(!error||active)$fatal(1,"released bank start");@(negedge clk);start=0;force_hold=0;
  @(negedge clk);vblank=1;@(posedge clk);#1;if(!present||front_id!=99)$fatal(1,"release setup presentation");@(negedge clk);vblank=0;
  // Reset while a word is held invalidates the reader and storage ownership.
  begin_frame(100,5,32'hee85c166);for(integer j=0;j<5;j=j+1)put(pattern(j));commit();grant(100,5);force_hold=1;begin_reader();
  while(!out_valid)begin @(posedge clk);#1;end
  @(negedge clk);reset=1;@(posedge clk);#1;if(active||out_valid||frame_done||read_ready)$fatal(1,"reset did not revoke reader");
  @(negedge clk);reset=0;force_hold=0;
  // Inject a byte-port error while the reader waits; no partial word may escape.
  begin_frame(101,5,32'hee85c166);for(integer j=0;j<5;j=j+1)put(pattern(j));commit();grant(101,5);begin_reader();
  while(!byte_req)begin @(posedge clk);#1;end
  @(negedge clk);force read_error=1;@(posedge clk);#1;if(!error||active||out_valid)$fatal(1,"byte port error not contained");
  @(negedge clk);release read_error;
  @(negedge clk);reset=1;@(posedge clk);#1;@(negedge clk);reset=0;
  // With a pending word and downstream ready, revoke ownership at the same
  // edge: the externally visible valid must drop before any handshake.
  begin_frame(102,5,32'hee85c166);for(integer j=0;j<5;j=j+1)put(pattern(j));commit();grant(102,5);force_hold=1;begin_reader();
  while(!out_valid)begin @(posedge clk);#1;end
  @(negedge clk);force out_ready=1;decode_done=1;#1;if(out_valid)$fatal(1,"valid not gated during release");
  @(posedge clk);#1;if(!error||active||frame_done)$fatal(1,"release/ready collision");
  @(negedge clk);decode_done=0;release out_ready;force_hold=0;
  if(stall_samples==0)$fatal(1,"no backpressure observed");
  if(total_bytes!=196634)$fatal(1,"byte accounting %0d",total_bytes);
  $display("TEST_PASS_WORD_READER frames=12 bytes=%0d words=%0d stalls=%0d cap=49152",total_bytes,total_words,stall_samples);$finish;
 end
 initial begin #100000000;$fatal(1,"watchdog");end
endmodule
