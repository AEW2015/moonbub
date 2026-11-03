`timescale 1ns/1ps
module tb_bank_display;
 reg clk=0,pclk=0,read_clk;always #5 clk=~clk;always #17.029 pclk=~pclk; always @(clk)read_clk <= #2.75 ~clk;
 reg reset=1,dec_reset=1,begin_valid=0,byte_valid=0,commit_valid=0;
 reg [31:0] begin_id=0,begin_crc=0; reg [15:0]begin_length=0;reg [7:0]byte_data=0;
 wire begin_accept,reject,decode_grant,decode_bank,present,front_valid,read_ready,read_valid,read_error;
 wire [3:0] reject_reason;wire [31:0]decode_id,front_id,accepted_frames,dropped_frames;wire [15:0]decode_length;wire [7:0]read_data;
 reg decode_request=0,decode_done=0,start=0;wire vblank;reg front=0;
 wire byte_req;wire [15:0]byte_addr;wire start_accept,active,error,frame_done,out_valid,dec_accept;wire [31:0]out_data;wire [3:0]out_strb;
 wire pix_valid,dec_idle;wire [15:0]width,height,px,py;wire [7:0]red,green,blue;
 two_bank_storage store(.clk(clk),.reset(reset),.begin_valid(begin_valid),.begin_id(begin_id),.begin_length(begin_length),.begin_crc(begin_crc),.byte_valid(byte_valid),.byte_data(byte_data),.commit_valid(commit_valid),.abort_valid(1'b0),.ingress_overflow(1'b0),.begin_accept(begin_accept),.reject(reject),.reject_reason(reject_reason),.decode_request(decode_request),.decode_done(decode_done),.decode_fail(1'b0),.decode_grant(decode_grant),.decode_bank(decode_bank),.decode_id(decode_id),.decode_length(decode_length),.read_req(byte_req),.read_addr(byte_addr),.read_ready(read_ready),.read_valid(read_valid),.read_error(read_error),.read_data(read_data),.vblank(vblank),.present(present),.front_valid(front_valid),.front_id(front_id),.accepted_frames(accepted_frames),.dropped_frames(dropped_frames));
 word_reader reader(.clk(clk),.reset(reset),.start(start),.owned(read_ready&&!decode_done),.granted_length(decode_length),.start_accept(start_accept),.active(active),.error(error),.frame_done(frame_done),.byte_req(byte_req),.byte_addr(byte_addr),.byte_valid(read_valid),.byte_error(read_error),.byte_data(read_data),.out_valid(out_valid),.out_data(out_data),.out_strb(out_strb),.out_ready(dec_accept));
 jpeg_core #(.SUPPORT_WRITABLE_DHT(0)) decoder(.clk_i(clk),.rst_i(reset||dec_reset),.inport_valid_i(out_valid),.inport_data_i(out_data),.inport_strb_i(out_strb),.inport_last_i(1'b0),.inport_accept_o(dec_accept),.outport_accept_i(tile_ready),.outport_valid_o(pix_valid),.outport_width_o(width),.outport_height_o(height),.outport_pixel_x_o(px),.outport_pixel_y_o(py),.outport_pixel_r_o(red),.outport_pixel_g_o(green),.outport_pixel_b_o(blue),.idle_o(dec_idle));
 wire tile_ready,tile_valid,tile_fault,tile_first,tile_last,tile_out_ready,mem_idle,protocol_fault;
 wire [23:0] tile_addr;wire [15:0] tile_data;
 wire [23:0] pixel_addr={4'b0,!front,(({9'd0,px[9:0]}+19'd40)*19'd480)+{10'd0,py[8:0]}};
 wire [15:0] pixel_color={red[7:3],green[7:2],blue[7:3]};
 wire line_req,line_ready,line_valid;wire [23:0]line_address;wire [15:0]line_data;wire [31:0]underruns;
 wire hs,vs,de;wire [9:0]lcd_x,lcd_y;wire [7:0]lcd_r,lcd_g,lcd_b;
 wire [12:0]a;wire [1:0]ba,cke,cs;wire [15:0]dq;wire sclk,ras,cas,we,lm,um;
 moonbub_tile_transpose tile(.clk(clk),.reset(reset),.abort(1'b0),.in_valid(pix_valid&&!dec_reset),.in_ready(tile_ready),.in_address(pixel_addr),.in_data(pixel_color),.out_valid(tile_valid),.out_ready(tile_out_ready),.out_address(tile_addr),.out_data(tile_data),.out_burst_first(tile_first),.out_burst_last(tile_last),.fault(tile_fault));
 moonshine_memory_burst memory(.clk(clk),.read_clk(read_clk),.reset(reset),.pixel_valid(tile_valid),.pixel_ready(tile_out_ready),.pixel_address(tile_addr),.pixel_rgb565(tile_data),.line_req_valid(line_req),.line_req_ready(line_ready),.line_req_address(line_address),.line_data_valid(line_valid),.line_data(line_data),.idle(mem_idle),.protocol_fault(protocol_fault),.sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
 moonshine_lcd lcd(.pixel_clk(pclk),.reset_n(!reset),.mem_clk(clk),.mem_reset(reset),.front_valid(1'b1),.front_buffer(front),.pattern_enable(1'b0),.line_req_valid(line_req),.line_req_ready(line_ready),.line_req_address(line_address),.line_data_valid(line_valid),.line_data(line_data),.frame_boundary(vblank),.underruns(underruns),.hsync(hs),.vsync(vs),.data_enable(de),.physical_x(lcd_x),.physical_y(lcd_y),.red(lcd_r),.green(lcd_g),.blue(lcd_b));
 sdram_model_burst model(.clk(sclk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
 reg[15:0] expected[0:345599];integer base,baseline_underruns,baseline_writes,baseline_bursts;
 reg [7:0] jpg0[0:49151],jpg1[0:49151];reg seen[0:345599];reg [2047:0] f0,f1,d0,d1;integer fd,n0,n1,dump,pixels=0,requests=0,responses=0,words=0,bytes_out=0;reg finished=0;integer k,i;reg[31:0]crc0,crc1;
 function automatic [31:0] cb(input [31:0]old,input[7:0]b);reg[31:0]v;integer j;begin v=old^b;for(j=0;j<8;j=j+1)v=v[0]?((v>>1)^32'hedb88320):v>>1;cb=v;end endfunction
 always @(posedge clk)if(!reset)begin
  if(error||read_error)$fatal(1,"reader error");
  if(byte_req)requests=requests+1;if(read_valid)responses=responses+1;
  if(frame_done)finished=1;
  if(out_valid&&dec_accept)begin words=words+1;for(integer z=0;z<4;z=z+1)if(out_strb[z])bytes_out=bytes_out+1;end
  if(tile_fault||protocol_fault)$fatal(1,"memory path fault");
  if(pix_valid&&!dec_reset&&tile_ready)begin
   if(px>=720||py>=480||width!=720||height!=480)$fatal(1,"pixel coordinate/dimensions %0d %0d %0d %0d",px,py,width,height);
   if(seen[px*480+py])$fatal(1,"duplicate pixel");seen[px*480+py]=1;expected[px*480+py]=pixel_color;pixels=pixels+1;
   $fdisplay(dump,"%0d %0d %04h",px,py,{red[7:3],green[7:2],blue[7:3]});
  end
 end
 task ingress(input integer id,input integer n,input [31:0]crc);integer j;begin
  @(negedge clk);begin_id=id;begin_length=16'(n);begin_crc=crc;begin_valid=1;@(posedge clk);#1;if(!begin_accept||reject)$fatal(1,"begin failed");@(negedge clk);begin_valid=0;
  for(j=0;j<n;j=j+1)begin @(negedge clk);byte_data=id==0?jpg0[j]:jpg1[j];byte_valid=1;@(posedge clk);#1;if(reject)$fatal(1,"byte rejected");@(negedge clk);byte_valid=0;end
  @(negedge clk);commit_valid=1;@(posedge clk);#1;if(reject)$fatal(1,"commit rejected");@(negedge clk);commit_valid=0;
 end endtask
 task start_frame(input integer id,input integer n);begin
  @(negedge clk);decode_request=1;@(posedge clk);#1;if(!decode_grant||decode_id!=id||decode_length!=n||decode_bank!=id[0])$fatal(1,"wrong grant");@(negedge clk);decode_request=0;
  repeat(4)@(negedge clk);dec_reset=0;@(negedge clk);start=1;@(posedge clk);#1;if(!start_accept)$fatal(1,"start failed");@(negedge clk);start=0;
 end endtask
 task finish_frame(input integer id,input integer n);begin
  while(pixels<345600 || !finished)begin @(posedge clk);#1;end
  if(pixels!=345600||requests!=n||responses!=n||bytes_out!=n||words!=(n+3)/4)$fatal(1,"accounting pixels=%0d req=%0d resp=%0d bytes=%0d words=%0d",pixels,requests,responses,bytes_out,words);
  while(!mem_idle||!tile_ready||tile_valid)@(negedge clk);
  if(model.writes-baseline_writes!=345600||model.write_bursts-baseline_bursts!=43200||underruns!=baseline_underruns)$fatal(1,"write/burst/underrun failure");
  base=front ? 0:24'h080000;for(integer j=0;j<345600;j=j+1)if(!seen[j]||model.mem[base+((j/480)+40)*480+(j%480)]!==expected[j])$fatal(1,"framebuffer mismatch index=%0d",j);
  $fclose(dump);$display("FRAME_PASS id=%0d bytes=%0d words=%0d pixels=%0d",id,n,words,pixels);
  @(negedge clk);decode_done=1;dec_reset=1;@(negedge clk);decode_done=0;while(!present)begin @(posedge clk);#1;end if(front_id!=id||!front_valid)$fatal(1,"presentation");front=!front;
  for(integer j=0;j<345600;j=j+1)if(model.mem[base+((j/480)+40)*480+(j%480)]!==expected[j])$fatal(1,"post-presentation framebuffer mismatch index=%0d",j);
  $display("PRESENT_PASS id=%0d front=%0d writes=345600 bursts=43200 underruns=0 framebuffer_pixels=345600",id,front);
 end endtask
 initial begin
  if(!$value$plusargs("JPEG0=%s",f0)||!$value$plusargs("JPEG1=%s",f1)||!$value$plusargs("DUMP0=%s",d0)||!$value$plusargs("DUMP1=%s",d1))$fatal(1,"missing paths");
  fd=$fopen(f0,"rb");if(!fd)$fatal(1,"jpeg0");n0=$fread(jpg0,fd);$fclose(fd);fd=$fopen(f1,"rb");if(!fd)$fatal(1,"jpeg1");n1=$fread(jpg1,fd);$fclose(fd);
  if(n0<=0||n1<=0||n0>=49152||n1>=49152)$fatal(1,"bad lengths");crc0=32'hffffffff;for(i=0;i<n0;i=i+1)crc0=cb(crc0,jpg0[i]);crc0=~crc0;crc1=32'hffffffff;for(i=0;i<n1;i=i+1)crc1=cb(crc1,jpg1[i]);crc1=~crc1;
  for(i=0;i<345600;i=i+1)seen[i]=0;
  for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24'h080000+i]=0;end
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);repeat(2000000)@(negedge clk);baseline_underruns=underruns;baseline_writes=model.writes;baseline_bursts=model.write_bursts;ingress(0,n0,crc0);dump=$fopen(d0,"w");if(!dump)$fatal(1,"dump0");start_frame(0,n0);
  ingress(1,n1,crc1);if(pixels<=0 || pixels>=345600)$fatal(1,"second frame was not committed during first decode");$display("OVERLAP_SECOND_ACCEPTED pixels_so_far=%0d",pixels);finish_frame(0,n0);
  for(i=0;i<345600;i=i+1)seen[i]=0;pixels=0;requests=0;responses=0;words=0;bytes_out=0;finished=0;
  baseline_writes=model.writes;baseline_bursts=model.write_bursts;dump=$fopen(d1,"w");if(!dump)$fatal(1,"dump1");start_frame(1,n1);finish_frame(1,n1);
  if(accepted_frames!=2||dropped_frames!=0)$fatal(1,"frame accounting");$display("TEST_PASS_BANK_DISPLAY");$finish;
 end
 initial begin #800000000;$fatal(1,"watchdog");end
endmodule
