`timescale 1ns/1ps
// Integration test only: 720x480 real JPEG -> decoder -> tile transpose -> BL8
// writer -> functional SDRAM, while LCD scans the other buffer.
module tb_jpeg720_burst;
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
 moonshine_core #(.WIDTH(720),.HEIGHT(480),.WATCHDOG_CYCLES(50000000)) core(
 .clk(clk),.reset(reset),.bus_write(wr),.bus_address(addr),.bus_wdata(data),.bus_rdata(rd),
 .frame_boundary(frame_boundary),.memory_idle(core_idle),.front_buffer(front),.front_valid(fvalid),.pattern_enable(pattern),
 .pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_rgb565(pd),.scanout_underruns(underruns),.transport_overflows(32'd0));
 moonbub_tile_transpose tile(.clk(clk),.reset(reset),.abort(1'b0),
 .in_valid(pv),.in_ready(tile_ready),.in_address(pa),.in_data(pd),
 .out_valid(tile_valid),.out_ready(tile_out_ready),.out_address(tile_addr),.out_data(tile_data),
 .out_burst_first(tile_first),.out_burst_last(tile_last),.fault(tile_fault));
 wire tile_out_ready;
 moonshine_memory_burst memory(.clk(clk),.read_clk(read_clk),.reset(reset),
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
 reg[7:0]jpeg[0:262143];reg[15:0]expected[0:345599];reg seen[0:345599];reg[31:0]crc;
 reg [2047:0] jpeg_file,dump_file;
 integer fd,dump,n,i,x,y,pixels=0,cycles=0,begin_cycle,readback_i,baseline_underruns;
 always @(posedge clk)begin
  cycles<=cycles+1;
  if(pv&&pr)begin
   x=((pa-24'h080000)/480)-40;y=(pa-24'h080000)%480;
   if(x<0||x>=720||y<0||y>=480)$fatal(1,"invalid decoder coordinate x=%0d y=%0d address=%h",x,y,pa);
   if(seen[x*480+y])$fatal(1,"duplicate decoder pixel x=%0d y=%0d",x,y);
   expected[x*480+y]<=pd;seen[x*480+y]<=1;pixels<=pixels+1;
   $fdisplay(dump,"%0d %0d %04h",x,y,pd);
  end
 end
 task write_reg(input[11:0]a0,input[31:0]d0);begin @(negedge clk);addr=a0;data=d0;wr=1;@(negedge clk);wr=0;end endtask
 initial begin
  if(!$value$plusargs("JPEG_FILE=%s",jpeg_file))jpeg_file="pattern-720x480-420-q65.jpg";
  if(!$value$plusargs("DUMP_FILE=%s",dump_file))dump_file="jpeg720-burst-rtl-rgb565.txt";
  fd=$fopen(jpeg_file,"rb");if(!fd)$fatal(1,"missing JPEG fixture");n=$fread(jpeg,fd);$fclose(fd);if(n<=0 || n>262144)$fatal(1,"bad fixture length");
  dump=$fopen(dump_file,"w");if(!dump)$fatal(1,"dump open failed");
  crc=32'hffffffff;for(i=0;i<n;i=i+1)crc=core.crc_byte(crc,jpeg[i]);crc=~crc;
  for(i=0;i<384000;i=i+1)model.mem[i]=0;
  for(i=0;i<345600;i=i+1)begin seen[i]=0;model.mem[24'h080000+((i/480)+40)*480+(i%480)]=16'hdead;end
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);
  repeat(2000000)@(negedge clk);baseline_underruns=underruns;
  write_reg('h14,1);write_reg('h18,n);write_reg('h1c,{16'd720,16'd480});write_reg('h20,crc);write_reg('h24,1);
  for(i=0;i<n;i=i+1)write_reg('h100,jpeg[i]);
  begin_cycle=cycles;write_reg('h24,4);
  while(core.presented_frames==0 && core.faults==0 && !tile_fault && !protocol_fault)@(negedge clk);
  if(core.faults!=0 || tile_fault || protocol_fault)$fatal(1,"decode/staging fault core=%0d tile=%0d stage=%0d",core.faults,tile_fault,protocol_fault);
  if(!fvalid||!front||core.last_presented!=1||core.decoded_frames!=1||core.presented_frames!=1)$fatal(1,"publication state");
  if(pixels!=345600||model.writes!=345600||model.write_bursts!=43200)$fatal(1,"pixel conservation pix=%0d writes=%0d bursts=%0d",pixels,model.writes,model.write_bursts);
  for(i=0;i<345600;i=i+1)begin
   readback_i=24'h080000+((i/480)+40)*480+(i%480);
   if(!seen[i]||model.mem[readback_i]!==expected[i])$fatal(1,"framebuffer mismatch i=%0d got=%h expected=%h",i,model.mem[readback_i],expected[i]);
  end
  if(underruns!=baseline_underruns)$fatal(1,"LCD underrun while decoding baseline=%0d after=%0d",baseline_underruns,underruns);
  $fclose(dump);
  $display("TEST_PASS_JPEG720_BURST pixels=%0d writes=%0d bursts=%0d presented=%0d decode_to_present_cycles=%0d underruns=%0d",pixels,model.writes,model.write_bursts,core.presented_frames,cycles-begin_cycle,underruns-baseline_underruns);$finish;
 end
 initial begin $display("JPEG720_TEST watchdog_armed"); #500000000;$fatal(1,"watchdog JPEG720");end
endmodule
