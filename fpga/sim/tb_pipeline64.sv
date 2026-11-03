`timescale 1ns/1ps
module tb_pipeline64;
 reg clk=0;always #5 clk=!clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 reg reset=1,wr=0,boundary=0;reg[11:0]addr=0;reg[31:0]data=0;wire[31:0]rd;
 wire front,fvalid,pattern,pv,pr,mi;wire[23:0]pa;wire[15:0]pd;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,lm,um;
 reg lr=0;wire lready,ldv;reg[23:0]la=0;wire[15:0]ld;
 moonshine_core #(.WIDTH(64),.HEIGHT(64),.WATCHDOG_CYCLES(100000)) core(
 .clk(clk),.reset(reset),.bus_write(wr),.bus_address(addr),.bus_wdata(data),.bus_rdata(rd),
 .frame_boundary(boundary),.memory_idle(mi),.front_buffer(front),.front_valid(fvalid),.pattern_enable(pattern),
 .pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_rgb565(pd),.scanout_underruns(32'd0),.transport_overflows(loss_count));
 moonshine_memory memory(.clk(clk),.read_clk(read_clk),.reset(reset),.pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_rgb565(pd),
 .line_req_valid(lr),.line_req_ready(lready),.line_req_address(la),.line_data_valid(ldv),.line_data(ld),.idle(mi),
 .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),
 .sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
 sdram_model model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 reg[7:0]jpeg[0:4095];reg[15:0]expected[0:4095];reg[31:0]crc;
 integer max_y=0;
 integer fd,n,i,x,y,pixels=0,totalcycles=0,base,frame,words,fault_before;
 reg[31:0]loss_count=0;
 always @(posedge clk)begin totalcycles<=totalcycles+1;
 if(core.decoder.u_jpeg_output.y_level_w>max_y)max_y<=core.decoder.u_jpeg_output.y_level_w;
 if(pv&&pr)begin
  base=front ? 0:24'h080000;x=((pa-base)/480)-40;y=(pa-base)%480;
  if(x<0||x>=64||y<0||y>=64)$fatal(1,"bad decoder coordinate");
  expected[x*64+y]<=pd;pixels<=pixels+1;
  if(fvalid && ((front&&pa>=24'h080000)||(!front&&pa<24'h080000)))$fatal(1,"decoder overwrites front");
 end end
 task write_reg(input[11:0]a,input[31:0]d);begin @(negedge clk);addr=a;data=d;wr=1;@(negedge clk);wr=0;end endtask
 task send_frame(input[31:0]id);begin
  write_reg('h14,id);write_reg('h18,n);write_reg('h1c,{16'd64,16'd64});write_reg('h20,crc);write_reg('h24,1);
  for(i=0;i<n;i=i+1)write_reg('h100,jpeg[i]);write_reg('h24,4);
 end endtask
 initial begin
  fd=$fopen("pipeline64-420.jpg","rb");n=$fread(jpeg,fd);$fclose(fd);
  crc=32'hffffffff;for(i=0;i<n;i=i+1)crc=core.crc_byte(crc,jpeg[i]);crc=~crc;
  repeat(8)@(negedge clk);reset=0;
  // Real baseline decoder, transposed writes, SDRAM commands and readback.
  for(frame=0;frame<2;frame=frame+1)begin
   send_frame(frame+1);while(!core.pending && core.faults==0)@(negedge clk);
   if(!core.pending)$fatal(1,"decode fault");
   base=front ? 0:24'h080000;
   for(x=0;x<64;x=x+1)for(y=0;y<64;y=y+1)
    if(model.mem[base+(x+40)*480+y]!==expected[x*64+y])$fatal(1,"SDRAM pixel differs x%d y%d",x,y);
   if(model.writes!=(frame+1)*4096)$fatal(1,"pixel writes not drained before publication");
   boundary=1;@(negedge clk);boundary=0;repeat(3)@(negedge clk);
   if(!fvalid||front!=(frame==0))$fatal(1,"front ownership");
   // Fetch actual first portrait line through the burst arbitrator.
   la=base+40*480;lr=1;while(!lready)@(negedge clk);@(negedge clk);lr=0;words=0;
   while(words<480)begin @(negedge clk);if(ldv)begin
    if(words<64 && ld!==expected[words])$fatal(1,"readback mismatch %d",words);words=words+1;end end
  end
  if(pixels!=8192)$fatal(1,"wrong pixel total");
  // A lost control/data queue word faults both receive and pending states,
  // while the current front buffer and its presented ID remain unchanged.
  write_reg('h24,1);write_reg('h100,'hff);loss_count=1;repeat(3)@(negedge clk);
  if(core.receiving||core.decoding||core.pending||!core.fault||!fvalid||front)$fatal(1,"receive transport loss not contained");
  write_reg('h24,2);send_frame(3);
  while(!core.pending && core.faults==1)@(negedge clk);
  if(!core.pending)$fatal(1,"third frame did not decode");
  loss_count=2;boundary=1;@(negedge clk);boundary=0;repeat(2)@(negedge clk);
  if(core.pending||core.decoding||!core.fault||!fvalid||front||core.last_presented!=2)$fatal(1,"pending transport loss damaged front");
  write_reg('h24,2);fault_before=core.faults;
  // A syntactically framed but unsupported progressive/garbage stream must
  // trip the bounded decoder watchdog while preserving the displayed image.
  n=8;jpeg[0]='hff;jpeg[1]='hd8;jpeg[2]='hff;jpeg[3]='hc2;jpeg[4]=0;jpeg[5]=0;jpeg[6]='hff;jpeg[7]='hd9;
  crc=32'hffffffff;for(i=0;i<n;i=i+1)crc=core.crc_byte(crc,jpeg[i]);crc=~crc;
  send_frame(4);while(core.faults==fault_before)@(negedge clk);
  if(!fvalid||front||core.pending)$fatal(1,"bad frame damaged display ownership");
  write_reg('h24,2);@(negedge clk);addr='h10;#1;if(rd!==1)$fatal(1,"abort did not recover readiness %x",rd);
  if(pixels!=12288||model.writes!=12288)$fatal(1,"third frame pixel conservation");
  if(max_y<384)$fatal(1,"decoder backpressure never reached RAM threshold %d",max_y);
  $display("PIPELINE64_PASS maxY=%0d realJPEG64x64_decodes3 presented2 pixels12288 SDRAM_writes12288 readback960 watchdog_recovery1 transport_receive_pending_abort1 cycles%0d",max_y,totalcycles);$finish;
 end
 initial begin #10000000;$fatal(1,"timeout");end
endmodule
