`timescale 1ns/1ps
module tb_sha;
 reg clk=0;always #5 clk=!clk;
 reg reset=1,abort=0,start_valid=0,in_valid=0,in_last=0,out_ready=0,error_ready=0;
 reg [63:0] start_owner=0,start_length=0;reg [31:0] start_epoch=0;reg [7:0] in_byte=0;
 wire start_ready,in_ready,out_valid,error_valid;wire [255:0] out_digest;wire [63:0] out_owner;wire [31:0] out_epoch;wire [1:0] error_code;
 sha256_bytes dut(.*);
 reg [7:0] data[0:8191];reg [255:0] expected;
 reg [63:0] owner_ref;reg [31:0] epoch_ref;
 integer fd,mfd,rc,ncases,id,nbytes,repeated,i,j,cycles=0,cases=0,errors=0,flushes=0,accepted=0,backpressure=0;
 integer began,first_byte,last_byte,first_digest;reg metric=0,held=0;reg [351:0] held_payload;
 always @(posedge clk)begin
  cycles=cycles+1;if(cycles>12000000)$fatal(1,"SHA timeout");
  if(reset||abort)held<=0;
  else begin
   if(held && (!out_valid || {out_digest,out_owner,out_epoch}!==held_payload))$fatal(1,"SHA stalled result changed");
   held<=out_valid&&!out_ready;if(out_valid&&!out_ready)held_payload<={out_digest,out_owner,out_epoch};
  end
  if(metric)begin
   if(start_valid&&start_ready)began=cycles;
   if(in_valid&&!in_ready)backpressure=backpressure+1;
   if(in_valid&&in_ready)begin if(first_byte<0)first_byte=cycles;last_byte=cycles;accepted=accepted+1;end
   if(out_valid&&first_digest<0)first_digest=cycles;
  end
 end
 task launch(input [63:0] length,input integer tag);
 begin
  @(negedge clk);if(!start_ready)$fatal(1,"SHA not idle");
  owner_ref=64'hf19abcde00000000+tag;epoch_ref=32'h81ab0000+tag;
  start_owner=owner_ref;start_epoch=epoch_ref;start_length=length;start_valid=1;
  @(negedge clk);start_valid=0;start_owner=64'hbad0000000000000;start_epoch=32'hbad;
 end endtask
 task put(input [7:0] value,input integer last);
 begin
  in_valid=1;in_byte=value;in_last=last;
  @(posedge clk);while(!in_ready)@(posedge clk);@(negedge clk);
 end endtask
 task finish(input [255:0] digest);
 begin
  while(!out_valid)begin @(negedge clk);if(error_valid)$fatal(1,"SHA unexpected error%0d",error_code);end
  repeat(23)begin
   if(out_digest!==digest||out_owner!==owner_ref||out_epoch!==epoch_ref||start_ready||in_ready)$fatal(1,"SHA mismatch id%0d got%h expected%h",id,out_digest,digest);
   @(negedge clk);
  end
  start_valid=0;in_valid=0;out_ready=1;@(negedge clk);out_ready=0;cases=cases+1;
 end endtask
 task error_result(input [1:0] code);
 begin
  while(!error_valid)@(negedge clk);
  repeat(13)begin
   if(error_code!==code||out_valid||start_ready||in_ready||out_owner!==owner_ref||out_epoch!==epoch_ref)$fatal(1,"SHA held error");@(negedge clk);
  end
  error_ready=1;@(negedge clk);error_ready=0;errors=errors+1;
 end endtask
 task flush(input integer hard_reset);
 begin
  if(hard_reset)reset=1;else abort=1;
  #1;if(start_ready||in_ready||out_valid||error_valid)$fatal(1,"SHA flush mask");
  @(negedge clk);reset=0;abort=0;in_valid=0;start_valid=0;
  repeat(3)@(negedge clk);
  if(out_valid||error_valid||!start_ready||out_epoch!==0||out_owner!==0||out_digest!==0)$fatal(1,"SHA stale hash/owner after abort");flushes=flushes+1;
 end endtask
 initial begin
  repeat(3)@(negedge clk);reset=0;
  fd=$fopen("sha-fixtures.hex","r");rc=$fscanf(fd,"%h",ncases);mfd=$fopen("sha-cycle-metrics.csv","w");
  $fdisplay(mfd,"case,bytes,start,first_byte,last_byte,first_digest,input_backpressure,accepted");
  for(id=0;id<ncases;id=id+1)begin
   rc=$fscanf(fd,"%h %h %h %h",j,nbytes,repeated,expected);if(rc!=4||j!=id)$fatal(1,"SHA fixture prefix");
   if(!repeated)for(i=0;i<nbytes;i=i+1)rc=$fscanf(fd,"%h",data[i]);
   first_byte=-1;last_byte=-1;first_digest=-1;accepted=0;backpressure=0;metric=1;
   launch(nbytes,id);
   for(i=0;i<nbytes;i=i+1)put(repeated?8'h61:data[i],i==nbytes-1);
   in_valid=0;finish(expected);metric=0;
   if(accepted!=nbytes)$fatal(1,"SHA accepted length mismatch");
   $fdisplay(mfd,"%0d,%0d,%0d,%0d,%0d,%0d,%0d,%0d",id,nbytes,began,first_byte,last_byte,first_digest,backpressure,accepted);
   $display("SHA_CASE_PASS id%0d bytes%0d cycles%0d pressure%0d",id,nbytes,first_digest-began,backpressure);
  end
  $fclose(fd);$fclose(mfd);
  launch(1036805,1000);error_result(1);
  launch(64'h2000000000000000,1001);error_result(1);
  launch(3,1002);put(8'h61,1);in_valid=0;error_result(2);
  launch(3,1003);put(8'h61,0);put(8'h62,0);put(8'h63,0);in_valid=0;error_result(2);
  for(j=0;j<16;j=j+1)begin launch(64,2000+j);for(i=0;i<j;i=i+1)put(i,0);in_valid=0;flush(j%2);end
  for(j=0;j<68;j=j+1)begin launch(64,3000+j);for(i=0;i<64;i=i+1)put(i,i==63);in_valid=0;repeat(j)@(negedge clk);flush(j%2);end
  for(j=0;j<211;j=j+1)begin launch(56,4000+j);for(i=0;i<56;i=i+1)put(i,i==55);in_valid=0;repeat(j)@(negedge clk);flush(j%2);end
  launch(3,5000);put(8'h61,0);put(8'h62,0);put(8'h63,1);in_valid=0;
  finish(256'hba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad);
  $display("SHA256_RTL_PASS KAT_and_boundary_cases=%0d negatives=%0d reset_abort=%0d recovery=1 cycles=%0d",ncases,errors,flushes,cycles);$finish;
 end
endmodule
