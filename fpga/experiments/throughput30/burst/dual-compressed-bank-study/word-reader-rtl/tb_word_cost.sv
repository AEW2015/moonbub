`timescale 1ns/1ps
module tb_word_cost;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,begin_valid=0,byte_valid=0,commit_valid=0,abort_valid=0,ingress_overflow=0;
 reg[31:0] begin_id=0,begin_crc=0;reg[15:0] begin_length=0;reg[7:0] byte_data=0;
 wire begin_accept,reject,decode_grant,decode_bank,present,front_valid,read_ready,read_valid,read_error;
 wire[3:0]reject_reason;wire[31:0]decode_id,front_id,accepted_frames,dropped_frames;wire[15:0]decode_length;wire[7:0]read_data;
 reg decode_request=0,decode_done=0,decode_fail=0,vblank=0;
 wire byte_req;wire[15:0]byte_addr;
 reg start=0;wire start_accept,active,error,frame_done,out_valid;wire[31:0]out_data;wire[3:0]out_strb;
 wire out_ready=1'b1;
 integer cycles=0,expected_len=0,offset=0,requests=0,responses=0,words=0,start_cycle=0,first_cycle=-1,last_cycle=-1;
 integer min_gap=999999,max_gap=0,last_gap=0;reg monitor=0;integer k,count;reg[31:0]expected_word;reg[3:0]expected_strb;
 two_bank_storage store(.clk(clk),.reset(reset),.begin_valid(begin_valid),.begin_id(begin_id),.begin_length(begin_length),.begin_crc(begin_crc),.byte_valid(byte_valid),.byte_data(byte_data),.commit_valid(commit_valid),.abort_valid(abort_valid),.ingress_overflow(ingress_overflow),.begin_accept(begin_accept),.reject(reject),.reject_reason(reject_reason),.decode_request(decode_request),.decode_done(decode_done),.decode_fail(decode_fail),.decode_grant(decode_grant),.decode_bank(decode_bank),.decode_id(decode_id),.decode_length(decode_length),.read_req(byte_req),.read_addr(byte_addr),.read_ready(read_ready),.read_valid(read_valid),.read_error(read_error),.read_data(read_data),.vblank(vblank),.present(present),.front_valid(front_valid),.front_id(front_id),.accepted_frames(accepted_frames),.dropped_frames(dropped_frames));
 word_reader dut(.clk(clk),.reset(reset),.start(start),.owned(read_ready && !decode_done && !decode_fail),.granted_length(decode_length),.start_accept(start_accept),.active(active),.error(error),.frame_done(frame_done),.byte_req(byte_req),.byte_addr(byte_addr),.byte_valid(read_valid),.byte_error(read_error),.byte_data(read_data),.out_valid(out_valid),.out_data(out_data),.out_strb(out_strb),.out_ready(out_ready));
 function automatic[7:0] pattern(input integer n);pattern=8'(n*7+32'h31);endfunction
 always @(negedge clk)cycles=cycles+1;
 always @(posedge clk)if(monitor && !reset)begin
  if(byte_req)requests=requests+1;
  if(read_valid)responses=responses+1;
  if(read_error||error)$fatal(1,"unexpected reader error");
  if(out_valid)begin
   expected_word=0;expected_strb=0;count=0;
   for(k=0;k<4;k=k+1)if(offset+k<expected_len)begin expected_word[k*8+:8]=pattern(offset+k);expected_strb[k]=1;count=count+1;end
   if(count==0||out_data!==expected_word||out_strb!==expected_strb)$fatal(1,"word mismatch offset=%0d",offset);
   if(words==0)$display("WORD_FIRST bytes=%0d cycle=%0d",expected_len,cycles);
   else begin last_gap=cycles-last_cycle;if(last_gap<min_gap)min_gap=last_gap;if(last_gap>max_gap)max_gap=last_gap;end
   if(offset+count==expected_len)$display("WORD_TAIL bytes=%0d strobe=%0d cycle=%0d",expected_len,out_strb,cycles);
   words=words+1;offset=offset+count;last_cycle=cycles;
  end
 end
 task begin_frame(input[31:0]id,input[15:0]len,input[31:0]crc);begin @(negedge clk);begin_id=id;begin_length=len;begin_crc=crc;begin_valid=1;@(posedge clk);#1;if(!begin_accept||reject)$fatal(1,"begin");@(negedge clk);begin_valid=0;end endtask
 task put(input[7:0]v);begin @(negedge clk);byte_data=v;byte_valid=1;@(posedge clk);#1;if(reject)$fatal(1,"byte");@(negedge clk);byte_valid=0;end endtask
 task commit;begin @(negedge clk);commit_valid=1;@(posedge clk);#1;if(reject)$fatal(1,"commit");@(negedge clk);commit_valid=0;end endtask
 task grant(input[31:0]id,input[15:0]len);begin @(negedge clk);decode_request=1;@(posedge clk);#1;if(!decode_grant||decode_id!=id||decode_length!=len)$fatal(1,"grant");@(negedge clk);decode_request=0;@(posedge clk);#1;if(!read_ready)$fatal(1,"not owned");end endtask
 task run_frame(input[31:0]id,input integer len,input[31:0]crc);
 integer j,elapsed;begin
  begin_frame(id,16'(len),crc);for(j=0;j<len;j=j+1)put(pattern(j));commit();grant(id,16'(len));
  expected_len=len;offset=0;requests=0;responses=0;words=0;first_cycle=-1;last_cycle=-1;min_gap=999999;max_gap=0;last_gap=0;
  @(negedge clk);start=1;@(posedge clk);#1;if(!start_accept||error||!active)$fatal(1,"start");start_cycle=cycles;monitor=1;@(negedge clk);start=0;
  while(!frame_done)begin @(posedge clk);#1;end
  elapsed=cycles-start_cycle;
  if(offset!=len||requests!=len||responses!=len||words!=(len+3)/4||last_cycle!=cycles)$fatal(1,"count mismatch len=%0d offset=%0d req=%0d resp=%0d words=%0d",len,offset,requests,responses,words);
  $display("WORD_COST id=%0d bytes=%0d requests=%0d responses=%0d words=%0d start_cycle=%0d last_cycle=%0d total_cycles=%0d min_gap=%0d max_gap=%0d final_gap=%0d",id,len,requests,responses,words,start_cycle,last_cycle,elapsed,min_gap,max_gap,last_gap);
  monitor=0;@(negedge clk);decode_done=1;@(posedge clk);#1;@(negedge clk);decode_done=0;vblank=1;@(posedge clk);#1;if(!present||front_id!=id)$fatal(1,"presentation");@(negedge clk);vblank=0;
 end endtask
 initial begin
  repeat(3)@(negedge clk);reset=0;
  run_frame(0,26159,32'h935e02c7);run_frame(1,49152,32'h7b05968b);
  $display("TEST_PASS_WORD_COST");$finish;
 end
 initial begin #50000000;$fatal(1,"watchdog");end
endmodule
