`timescale 1ns/1ps
// Ten distinct small JPEGs, real decoder and SDRAM; synthetic boundaries, no LCD.
module tb_pipeline64_multiframe;
 reg clk=0;always #5 clk=!clk;
 wire read_clk;assign #2.75 read_clk=~clk;
 reg reset=1,wr=0,boundary=0;reg[11:0]addr=0;reg[31:0]data=0;wire[31:0]rd;
 wire front,fvalid,pattern,pv,pr,mi;wire[23:0]pa;wire[15:0]pd;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,lm,um;
 wire lready,ldv;wire[15:0]ld;
 moonshine_core #(.WIDTH(64),.HEIGHT(64),.WATCHDOG_CYCLES(100000)) core(
 .clk(clk),.reset(reset),.bus_write(wr),.bus_address(addr),.bus_wdata(data),.bus_rdata(rd),
 .frame_boundary(boundary),.memory_idle(mi),.front_buffer(front),.front_valid(fvalid),.pattern_enable(pattern),
 .pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_rgb565(pd),.scanout_underruns(32'd0),.transport_overflows(32'd0));
 moonshine_memory memory(.clk(clk),.read_clk(read_clk),.reset(reset),.pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_rgb565(pd),
 .line_req_valid(1'b0),.line_req_ready(lready),.line_req_address(24'd0),.line_data_valid(ldv),.line_data(ld),.idle(mi),
 .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),
 .sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
 sdram_model model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 reg[7:0]jpeg[0:4095];reg[15:0]expected[0:4095];reg[31:0]crc;
 integer fd,n,i,x,y,pixels=0,totalcycles=0,base,frame;string filename;
 always @(posedge clk)begin totalcycles<=totalcycles+1;
  if(pv&&pr)begin
   base=front ? 0:24'h080000;x=((pa-base)/480)-40;y=(pa-base)%480;
   if(x<0||x>=64||y<0||y>=64)$fatal(1,"bad pixel address");
   expected[x*64+y]<=pd;pixels<=pixels+1;
   if(fvalid && ((front&&pa>=24'h080000)||(!front&&pa<24'h080000)))$fatal(1,"front overwritten");
  end
 end
 task write_reg(input[11:0]a,input[31:0]d);begin @(negedge clk);addr=a;data=d;wr=1;@(negedge clk);wr=0;end endtask
 initial begin
  repeat(8)@(negedge clk);reset=0;
  for(frame=0;frame<10;frame=frame+1)begin
   filename=$sformatf("frame%02d.jpg",frame);fd=$fopen(filename,"rb");if(!fd)$fatal(1,"fixture missing");
   n=$fread(jpeg,fd);$fclose(fd);if(n<=0||n>=4096)$fatal(1,"invalid JPEG length");
   crc=32'hffffffff;for(i=0;i<n;i=i+1)crc=core.crc_byte(crc,jpeg[i]);crc=~crc;
   write_reg('h14,frame+1);write_reg('h18,n);write_reg('h1c,{16'd64,16'd64});write_reg('h20,crc);write_reg('h24,1);
   for(i=0;i<n;i=i+1)write_reg('h100,jpeg[i]);write_reg('h24,4);
   while(!core.pending && core.faults==0)@(negedge clk);
   if(!core.pending)$fatal(1,"decode fault frame %d",frame);
   if(pixels!=(frame+1)*4096 || model.writes!=(frame+1)*4096)$fatal(1,"pixel conservation");
   base=front ? 0:24'h080000;
   for(x=0;x<64;x=x+1)for(y=0;y<64;y=y+1)
    if(model.mem[base+(x+40)*480+y]!==expected[x*64+y])$fatal(1,"memory mismatch frame=%d x=%d y=%d",frame,x,y);
   boundary=1;@(negedge clk);boundary=0;repeat(3)@(negedge clk);
   if(!fvalid||core.last_presented!=(frame+1)||core.presented_frames!=(frame+1))$fatal(1,"publication mismatch frame=%d",frame);
  end
  $display("MULTIFRAME64_PASS frames=10 distinct_input_files=10 pixels=%0d writes=%0d cycles=%0d",pixels,model.writes,totalcycles);$finish;
 end
 initial begin #50000000;$fatal(1,"timeout");end
endmodule
