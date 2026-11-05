`timescale 1ns/1ps
module tb;
 reg clk=0;always #5 clk=!clk;
 reg reset=1,bw=0;reg[11:0]addr=0;reg[31:0]wd=0;wire[31:0]rd;
 ar03_fixture_diagnostic dut(.clk(clk),.reset(reset),.bus_write(bw),.bus_address(addr),.bus_wdata(wd),.bus_rdata(rd));
 reg[7:0]expected[0:518399];integer observed=0,cycle=0,start_cycle=-1,result_cycle=-1;
 reg checking=0;reg[31:0]v,elapsed;reg[127:0]tag;
 task write_command(input[31:0]value);begin
  @(negedge clk);bw=1;addr=12'h408;wd=value;@(negedge clk);bw=0;
 end endtask
 task read_csr(input[11:0]address,output[31:0]value);begin
  @(negedge clk);addr=address;#1;value=rd;
 end endtask
 always @(posedge clk)begin
  cycle=cycle+1;
  if(checking&&dut.state==1&&dut.ks)start_cycle=cycle;
  if(checking&&dut.sv)begin
   if(observed>=518400||dut.compute.sample!==expected[observed])$fatal(1,"sample mismatch index=%0d",observed);
   observed=observed+1;
  end
  if(checking&&dut.cv)result_cycle=cycle;
  if(cycle>4000000)$fatal(1,"bench timeout");
 end
 initial begin
  $readmemh("expected.hex",expected);
  repeat(8)@(negedge clk);reset=0;
  read_csr(12'h400,v);if(v!==32'h31444b41)$fatal(1,"magic");
  // Abort while ingress owns a fetched/held byte, then verify a new owner.
  write_command(1);repeat(31)@(negedge clk);write_command(1);
  read_csr(12'h440,v);if(v!=1)$fatal(1,"busy command changed run");
  write_command(2);repeat(4)@(negedge clk);
  read_csr(12'h40c,v);if(v[2:0]!=6)$fatal(1,"abort");
  checking=1;write_command(1);
  wait(dut.state==3||dut.state==4);@(negedge clk);checking=0;
  read_csr(12'h40c,v);if(v[2:0]!=3)$fatal(1,"compute failure stage=%0d code=%0d",dut.fault_stage,dut.fault_code);
  if(observed!=518400)$fatal(1,"sample count");
  read_csr(12'h414,v);if(v!=518400)$fatal(1,"CSR samples");
  read_csr(12'h418,v);if(v!=48203)$fatal(1,"CSR ingress");
  read_csr(12'h420,v);if(v!=2)$fatal(1,"owner reuse");
  read_csr(12'h424,v);if(v!=0)$fatal(1,"owner high");
  read_csr(12'h410,elapsed);if(elapsed!=result_cycle-start_cycle)$fatal(1,"cycle accounting %0d != %0d",elapsed,result_cycle-start_cycle);
  read_csr(12'h430,tag[31:0]);read_csr(12'h434,tag[63:32]);
  read_csr(12'h438,tag[95:64]);read_csr(12'h43c,tag[127:96]);
  if(tag!==128'h855898f019ffddad10bef275ee7dc9c6)$fatal(1,"stored tag byte order");
  repeat(21)@(negedge clk);read_csr(12'h410,v);if(v!=elapsed)$fatal(1,"result changed");
  $display("PASS diagnostic samples=%0d ingress=48203 cycles=%0d tag=%032h owner=2 busy_rejects=1 abort_recovery=1",observed,elapsed,tag);
  $finish;
 end
endmodule
