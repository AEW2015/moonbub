`timescale 1ns/1ps
// Integration test only: 64x64 real JPEG -> decoder -> tile transpose -> BL8
// writer -> functional SDRAM, while LCD scans the other buffer.
module tb_abort_full #(parameter FLUSH_COLLECTOR=0);
 reg clk=0,pclk=0,read_clk; always #5 clk=~clk; always #17.029 pclk=~pclk;
 always @(clk)read_clk <= #2.75 ~clk;
 reg reset=1,wr=0;reg[11:0]addr=0;reg[31:0]data=0;wire[31:0]rd;
 wire front,fvalid,pattern,pv,pr,mem_idle,core_idle;
 wire [23:0]pa,tile_addr;wire[15:0]pd,tile_data;
 wire tile_ready,tile_valid,tile_fault,tile_first,tile_last,protocol_fault;
 wire line_req,line_ready,line_valid,frame_boundary;wire[23:0]line_address;wire[15:0]line_data;
 wire[31:0]underruns;wire hs,vs,de;wire[9:0]px,py;wire[7:0]red,green,blue;
 wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sclk,ras,cas,we,lm,um;
 // Tile and burst stages must both be empty before core may publish a frame.
 assign pr=tile_ready;
 assign core_idle=mem_idle && tile_ready && !tile_valid && !tile_fault && !protocol_fault;
 moonshine_core #(.WIDTH(64),.HEIGHT(64),.WATCHDOG_CYCLES(3000000)) core(
 .clk(clk),.reset(reset),.bus_write(wr),.bus_address(addr),.bus_wdata(data),.bus_rdata(rd),
 .frame_boundary(frame_boundary),.memory_idle(core_idle),.front_buffer(front),.front_valid(fvalid),.pattern_enable(pattern),
 .pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_rgb565(pd),.scanout_underruns(underruns),.transport_overflows(32'd0));
 moonbub_tile_transpose tile(.clk(clk),.reset(reset),.abort(wr && addr==12'h024 && data[1]),
 .in_valid(pv),.in_ready(tile_ready),.in_address(pa),.in_data(pd),
 .out_valid(tile_valid),.out_ready(tile_out_ready),.out_address(tile_addr),.out_data(tile_data),
 .out_burst_first(tile_first),.out_burst_last(tile_last),.fault(tile_fault));
 wire tile_out_ready;
 moonshine_memory_burst_abort memory(.clk(clk),.read_clk(read_clk),.reset(reset),.abort(FLUSH_COLLECTOR && wr && addr==12'h024 && data[1]),
 .pixel_valid(tile_valid),.pixel_ready(tile_out_ready),.pixel_address(tile_addr),.pixel_rgb565(tile_data),
 .line_req_valid(line_req),.line_req_ready(line_ready),.line_req_address(line_address),
 .line_data_valid(line_valid),.line_data(line_data),.idle(mem_idle),.protocol_fault(protocol_fault),
 .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),
 .sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
 moonshine_lcd lcd(.pixel_clk(pclk),.reset_n(!reset),.mem_clk(clk),.mem_reset(reset),
 // Scan initialized buffer 0 before the first frame; follow true ownership after publication.
 .front_valid(1'b1),.front_buffer(front),.pattern_enable(1'b0),.line_req_valid(line_req),
 .line_req_ready(line_ready),.line_req_address(line_address),.line_data_valid(line_valid),
 .line_data(line_data),.frame_boundary(frame_boundary),.underruns(underruns),.hsync(hs),.vsync(vs),
 .data_enable(de),.physical_x(px),.physical_y(py),.red(red),.green(green),.blue(blue));
 sdram_model_burst model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 reg[7:0]jpeg[0:4095];reg[15:0]old_pixels[0:4095],new_pixels[0:4095];reg[31:0]crc;
 reg [2047:0]jpeg_file;
 integer fd,n,i,x,y,pixels=0,phase=0,baseline_underruns,base;
 always @(posedge clk)if(!reset && pv&&pr)begin
  base=front ? 0:24'h080000;x=((pa-base)/480)-40;y=(pa-base)%480;
  if(x<0||x>=64||y<0||y>=64)$fatal(1,"bad decoder coordinates");
  if(phase==1)old_pixels[x*64+y]<=pd;
  if(phase==3)begin if(!front || core.last_presented!=1)$fatal(1,"front changed before recovered decode completed");new_pixels[x*64+y]<=pd;end
  pixels<=pixels+1;
 end
 task write_reg(input[11:0]a0,input[31:0]d0);begin @(negedge clk);addr=a0;data=d0;wr=1;@(negedge clk);wr=0;end endtask
 task send_frame(input[31:0]id);begin
  write_reg('h14,id);write_reg('h18,n);write_reg('h1c,{16'd64,16'd64});write_reg('h20,crc);write_reg('h24,1);
  for(i=0;i<n;i=i+1)write_reg('h100,jpeg[i]);write_reg('h24,4);
 end endtask
 initial begin
  if(!$value$plusargs("JPEG_FILE=%s",jpeg_file))jpeg_file="pipeline64-420.jpg";
  fd=$fopen(jpeg_file,"rb");if(!fd)$fatal(1,"missing JPEG fixture");n=$fread(jpeg,fd);$fclose(fd);
  if(n<=0||n>4096)$fatal(1,"bad fixture length");
  crc=32'hffffffff;for(i=0;i<n;i=i+1)crc=core.crc_byte(crc,jpeg[i]);crc=~crc;
  for(i=0;i<384000;i=i+1)model.mem[i]=0;
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);repeat(2000000)@(negedge clk);
  baseline_underruns=underruns;phase=1;send_frame(1);
  while(core.presented_frames<1 && core.faults==0 && !tile_fault && !protocol_fault)@(negedge clk);
  if(!fvalid||!front||core.last_presented!=1||core.faults||tile_fault||protocol_fault)$fatal(1,"first frame failed");
  if(pixels!=4096)$fatal(1,"initial frame pixel count");
  for(i=0;i<4096;i=i+1)if(model.mem[24'h080000+((i/64)+40)*480+(i%64)]!==old_pixels[i])$fatal(1,"first frame memory mismatch");
  // Abort while a subsequent decode is partway through collecting a tile.
  phase=2;send_frame(2);
  while(!(memory.write_full && !memory.req_ready) && !tile_fault && !protocol_fault)@(negedge clk);
  if(tile_fault||protocol_fault)$fatal(1,"fault before requested abort");
  $display("FULL_BEFORE_ABORT full=%0d ready=%0d",memory.write_full,memory.req_ready);
  addr='h24;data=2;wr=1; @(negedge clk);wr=0;repeat(4)@(negedge clk);
  if(core.decoding||core.pending||core.receiving)$fatal(1,"core did not abort");
  if(!fvalid||!front||core.last_presented!=1||core.presented_frames!=1)$fatal(1,"front changed during abort");
  begin : bounded_drain
   integer waited;
   waited=0;while(!mem_idle && waited<10000)begin @(negedge clk);waited=waited+1;end
   if(!mem_idle)$fatal(1,"ABORT_STAGING_NOT_DRAINED index=%0d full=%0d",memory.write_index,memory.write_full);
  end
  // Host deliberately waits for memory to drain; this test does not model a
  // fully automatic cleanup handshake or concurrent fault recovery.
  for(i=0;i<4096;i=i+1)if(model.mem[24'h080000+((i/64)+40)*480+(i%64)]!==old_pixels[i])$fatal(1,"old front buffer damaged");
  phase=3;send_frame(3);
  while(core.presented_frames<2 && core.faults==0 && !tile_fault && !protocol_fault)@(negedge clk);
  if(tile_fault||protocol_fault||core.faults)$fatal(1,"RECOVERY_FAULT tile=%0d stage=%0d core=%0d tile_index=%0d",tile_fault,protocol_fault,core.faults,tile.input_index);
  if(core.last_presented!=3||front||!fvalid)$fatal(1,"recovery publication mismatch");
  for(i=0;i<4096;i=i+1)begin
   if(model.mem[((i/64)+40)*480+(i%64)]!==new_pixels[i] || new_pixels[i]!==old_pixels[i])$fatal(1,"recovery pixel differs from original valid frame i=%0d",i);
   if(model.mem[24'h080000+((i/64)+40)*480+(i%64)]!==old_pixels[i])$fatal(1,"old front damaged during recovery");
  end
  if(underruns!=baseline_underruns)$fatal(1,"underrun during run");
  $display("TEST_PASS_ABORT_FULL flush=%0d front_preserved=1 recovered_id=3",FLUSH_COLLECTOR);$finish;
 end
 initial begin #150000000;$fatal(1,"watchdog");end

endmodule
