`timescale 1ns/1ps
module tb_eoi_last;
 reg clk=0;always #5 clk=~clk;
 reg reset=1,valid=0,last=0,ready=1;reg[31:0] data=0;wire accept,start,done;wire[15:0]width,height;wire[1:0] mode,yt,cbt,crt;wire qv,ql,hv,hl,dv,dl;wire[7:0]qd,hd,dd;
 jpeg_input dut(.clk_i(clk),.rst_i(reset),.inport_valid_i(valid),.inport_data_i(data),.inport_strb_i(4'hf),.inport_last_i(last),.dqt_cfg_accept_i(1'b1),.dht_cfg_accept_i(1'b1),.data_accept_i(ready),.inport_accept_o(accept),.img_start_o(start),.img_end_o(done),.img_width_o(width),.img_height_o(height),.img_mode_o(mode),.img_dqt_table_y_o(yt),.img_dqt_table_cb_o(cbt),.img_dqt_table_cr_o(crt),.dqt_cfg_valid_o(qv),.dqt_cfg_data_o(qd),.dqt_cfg_last_o(ql),.dht_cfg_valid_o(hv),.dht_cfg_data_o(hd),.dht_cfg_last_o(hl),.data_valid_o(dv),.data_data_o(dd),.data_last_o(dl));
 reg[7:0] bytes[0:262143];reg[2047:0]filename;integer fd,n,i,blocked=0;
 initial begin
  if($value$plusargs("BLOCK=%d",blocked))begin end
  if(!$value$plusargs("JPEG_FILE=%s",filename))$fatal(1,"JPEG_FILE required");
  fd=$fopen(filename,"rb");if(!fd)$fatal(1,"fixture missing");n=$fread(bytes,fd);$fclose(fd);
  if(n<8510||bytes[8503]!==8'hff||bytes[8504]!==8'h00)$fatal(1,"wrong fixture");
  repeat(5)@(negedge clk);reset=0;
  for(i=0;i<=8500;i=i+4)begin
   @(negedge clk);valid=1;data={bytes[i+3],bytes[i+2],bytes[i+1],bytes[i]};
   do @(posedge clk); while(!accept);
   @(negedge clk);valid=0;
  end
  if(dut.state_q!==14 || dut.last_b_q!==8'hff || width!==720 || height!==480)
   $fatal(1,"bad setup state=%0d last=%h dimensions=%dx%d",dut.state_q,dut.last_b_q,width,height);
  // Buffered output data must not send end-of-image until the EOI byte is accepted.
  if(!dut.data_valid_q)$fatal(1,"setup did not retain an entropy output byte");
  data=32'h000000d9;valid=1;ready=0;#1;
  if(dut.inport_accept_w!==0)$fatal(1,"test did not block");
  if(dl!==0)$fatal(1,"unaccepted EOI asserted data_last while blocked: state=%0d dl=%b",dut.state_q,dl);
  @(posedge clk);#1;
  if(dl!==0 || dut.state_q!==14)$fatal(1,"blocked EOI changed state");
  @(negedge clk);ready=1;#1;
  if(dl!==1)$fatal(1,"accepted EOI must deliver data_last");
  @(posedge clk);#1;if(dut.state_q!==0)$fatal(1,"accepted EOI did not end image");
  $display("TEST_PASS_EOI_LAST blocked_last=0 accepted_last=1");$finish;
 end
 initial begin #2000000;$fatal(1,"watchdog");end
endmodule
