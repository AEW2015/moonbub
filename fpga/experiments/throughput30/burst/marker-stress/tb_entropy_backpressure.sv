`timescale 1ns/1ps
// Legal word-level source holds data/valid until accepted; output stalls.
module tb_entropy_backpressure;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,valid=0,ready=1;reg[31:0] data=0;reg[3:0]strb=4'hf;
 wire accept,start,done,dv,dl;wire[15:0]width,height;wire[1:0]mode,yt,cbt,crt;wire qv,ql,hv,hl;wire[7:0]qd,hd,dd;
 jpeg_input dut(.clk_i(clk),.rst_i(reset),.inport_valid_i(valid),.inport_data_i(data),.inport_strb_i(strb),.inport_last_i(1'b0),
 .dqt_cfg_accept_i(1'b1),.dht_cfg_accept_i(1'b1),.data_accept_i(ready),.inport_accept_o(accept),
 .img_start_o(start),.img_end_o(done),.img_width_o(width),.img_height_o(height),.img_mode_o(mode),
 .img_dqt_table_y_o(yt),.img_dqt_table_cb_o(cbt),.img_dqt_table_cr_o(crt),
 .dqt_cfg_valid_o(qv),.dqt_cfg_data_o(qd),.dqt_cfg_last_o(ql),.dht_cfg_valid_o(hv),.dht_cfg_data_o(hd),.dht_cfg_last_o(hl),
 .data_valid_o(dv),.data_data_o(dd),.data_last_o(dl));
 reg[7:0] bytes[0:262143];string filename,outfile;integer fd,out,n,i,random_mode=0,noise_gaps=0,seed=42,emitted=0,last_count=0,cycle=0;
 reg[31:0]rng;
 function automatic [31:0] xorshift(input [31:0] input_value); reg [31:0] v; begin v=input_value^(input_value<<13); v=v^(v>>17); v=v^(v<<5); xorshift=v; end endfunction
 always @(negedge clk)begin
  if(reset)ready=1;
  else if(random_mode)begin rng=xorshift(rng);ready=(rng[1:0]!=0);end
  else ready=1;
 end
 always @(posedge clk)if(!reset)begin
  cycle<=cycle+1;
  if(dv && ready)begin $fwrite(out,"%c",dd);emitted<=emitted+1;end
  if(dl)begin if(!ready)$fatal(1,"data_last while !ready");last_count<=last_count+1;end
 end
 initial begin
  if($value$plusargs("RANDOM=%d",random_mode))begin end
  if($value$plusargs("SEED=%d",seed))begin end
  if($value$plusargs("NOISE_GAPS=%d",noise_gaps))begin end
  rng=seed;if(rng==0)$fatal(1,"nonzero seed required");
  if(!$value$plusargs("JPEG_FILE=%s",filename))$fatal(1,"JPEG_FILE required");
  if(!$value$plusargs("OUT_FILE=%s",outfile))$fatal(1,"OUT_FILE required");
  fd=$fopen(filename,"rb");if(!fd)$fatal(1,"input open failed");n=$fread(bytes,fd);$fclose(fd);
  if(n<8||bytes[n-2]!==8'hff||bytes[n-1]!==8'hd9)$fatal(1,"fixture dimensions/EOI");
  out=$fopen(outfile,"wb");if(!out)$fatal(1,"output open failed");
  repeat(5)@(negedge clk);#1;reset=0;
  for(i=0;i<n;i=i+4)begin
   @(negedge clk); valid=1; data={i+3<n ? bytes[i+3] : 8'd0,i+2<n ? bytes[i+2] : 8'd0,i+1<n ? bytes[i+1] : 8'd0,bytes[i]}; strb=(n-i>=4) ? 4'b1111 : (n-i==3) ? 4'b0111 : (n-i==2) ? 4'b0011 : 4'b0001;
   do @(posedge clk); while(!accept);
   @(negedge clk);valid=0;
   if(noise_gaps)begin
    case(rng[1:0])
     0:data=32'h000000d9;
     1:data=32'h000000c0;
     2:data=32'h000000d8;
     3:data=32'h000000da;
    endcase
   end
   if(random_mode && (i%12==0))repeat(2)@(negedge clk);
  end
  repeat(8)@(negedge clk);$fclose(out);
  if(last_count!=1)$fatal(1,"expected exactly one data_last, got %0d",last_count);
  $display("TEST_PASS_ENTROPY seed=%0d random=%0d emitted=%0d cycles=%0d",seed,random_mode,emitted,cycle);$finish;
 end
 initial begin #20000000;$fatal(1,"watchdog");end
endmodule
