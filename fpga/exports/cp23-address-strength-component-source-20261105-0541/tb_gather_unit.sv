`timescale 1ns/1ps
module tb;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,lv=0;reg[23:0]la=0;
 wire lr,dv,primed,qv,rr;wire[15:0]data;wire[63:0]qo;wire[31:0]qe,qf,qs;wire[23:0]qa;
 reg sv=0;reg[127:0]sd;reg[63:0]so;reg[31:0]se,sf,ss;reg[1:0]st=0;reg[3:0]sw=8;
 wire[31:0]faults,requests,responses,rejects;
 integer cycle=0,delay=0,phase=0,received=0,x=0,checked=0,transactions=0,invalid_cycles=0;
 integer stage_stalls=0;reg held=0;reg[9:0]held_index;reg[127:0]held_y;
 reg pending=0;reg[63:0]savedo;reg[31:0]savede,savedf,saveds;
 wire qr=cycle%11!=0&&!pending;
 ar03_yuv_line_gather dut(.clk(clk),.reset(reset),.line_req_valid(lv),.line_req_ready(lr),.line_req_address(la),
 .line_data_valid(dv),.line_data(data),.primed(primed),.request_valid(qv),.request_ready(qr),.request_rejected(1'b0),
 .request_owner(qo),.request_epoch(qe),.request_frame(qf),.request_sequence(qs),.request_address(qa),
 .response_valid(sv),.response_ready(rr),.response_data(sd),.response_owner(so),.response_epoch(se),.response_frame(sf),.response_sequence(ss),
 .response_status(st),.response_words(sw),.protocol_faults(faults),.requests(requests),.responses(responses),.rejected_response_cycles(rejects));
 reg[15:0]mem[0:259199];reg[15:0]expected[0:345599];integer i;
 always @(posedge clk)begin
  cycle=cycle+1;
  if(!reset)begin
   if(dut.cache_write&&dut.fetch)$fatal(1,"RAM ports overlap load/render");
   if(dut.kiv&&dut.kir&&(!dut.left_hit||(dut.column[0]&&!dut.right_hit)))$fatal(1,"freshness");
   if(phase>0&&phase<7&&rr)$fatal(1,"invalid accepted");
   if(sv&&!rr)invalid_cycles=invalid_cycles+1;
   if(qv&&qr)begin
    if(pending)$fatal(1,"unreserved response");
    for(i=0;i<8;i=i+1)sd[i*16+:16]<=mem[qa-24'h100000+i];
    savedo<=qo;savede<=qe;savedf<=qf;saveds<=qs;
    delay<=1+cycle%9;pending<=1;transactions=transactions+1;
   end
   if(pending)begin
    if(delay>0)delay<=delay-1;
    else if(!sv)begin sv<=1;phase<=1;so<=savedo^1;se<=savede;sf<=savedf;ss<=saveds;end
    else if(phase<7)begin
     phase<=phase+1;so<=savedo;se<=savede;sf<=savedf;ss<=saveds;st<=0;sw<=8;
     case(phase)
      1:se<=savede^1;2:sf<=savedf^1;3:ss<=saveds^1;4:st<=2;5:sw<=7;
     endcase
    end else if(rr)begin pending<=0;sv<=0;phase<=0;end
   end
   if(dv)begin
    if(data!==expected[received*720+x])$fatal(1,"native mismatch x=%0d y=%0d got=%h expected=%h",x,received,data,expected[received*720+x]);
    received=received+1;checked=checked+1;
   end
  end
  if(cycle>3000000)$fatal(1,"timeout");
 end
 // Test-only internal seam: withhold kernel acceptance and its input valid
 // together; proves synchronous RAM outputs/metadata hold across backpressure.
 always @(negedge clk)begin
  if(!reset&&dut.stage_valid&&cycle%97<9)begin
   if(held&&(dut.stage_index!==held_index||dut.yword!==held_y))$fatal(1,"staged data changed under stall");
   held=1;held_index=dut.stage_index;held_y=dut.yword;stage_stalls=stage_stalls+1;
   force dut.kir=0;force dut.rgb.in_valid=0;
  end else begin held=0;release dut.kir;release dut.rgb.in_valid;end
 end
 task line(input integer col);
 begin
  x=col;received=0;wait(lr);@(negedge clk);la=col*480;lv=1;@(negedge clk);lv=0;
  wait(received==480);@(negedge clk);
 end endtask
 initial begin
  $readmemh("fixture-column.hex",mem);$readmemh("native-base-rgb.hex",expected);
  repeat(5)@(negedge clk);reset=0;
  for(integer c=0;c<720;c=c+1)line(c);
  line(719);line(1);line(0);line(358);line(359);line(718);
  // Reset with an occupied synchronous read stage; data RAM is never reset.
  wait(lr);@(negedge clk);la=317*480;lv=1;@(negedge clk);lv=0;
  wait(dut.stage_valid);@(negedge clk);reset=1;pending=0;sv=0;phase=0;
  for(integer w=0;w<259200;w=w+1)mem[w]=mem[w]^16'hffff;
  $readmemh("native-reset-rgb.hex",expected);
  repeat(3)@(negedge clk);reset=0;line(719);line(0);
  if(faults||invalid_cycles<100||requests!=responses||stage_stalls<100)$fatal(1,"accounting");
  $display("GATHER_BRAM_NATIVE_UNIT_PASS checked=%0d transactions=%0d rejected_cycles=%0d cycles=%0d reset_occupied_stage=1 staged_stalls=%0d",checked,transactions,invalid_cycles,cycle,stage_stalls);$finish;
 end

 always @(posedge clk)if(!reset&&dut.request_valid)begin
  if(dut.request_address!==(dut.kind==0?dut.Y_BASE+dut.column*24'd240+dut.block_index*8:dut.kind==1?dut.CB_BASE+dut.load_column*24'd120+dut.block_index*8:dut.CR_BASE+dut.load_column*24'd120+dut.block_index*8))$fatal(1,"registered request address differs from original valid-cycle formula");
 end
endmodule
