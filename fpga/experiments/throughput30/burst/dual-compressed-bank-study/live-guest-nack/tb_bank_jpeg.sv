`timescale 1ns/1ps
module tb_live_multiframe;
 import "DPI-C" function int bridge_next();
 import "DPI-C" function int bridge_byte(input int idx);
 import "DPI-C" function int bridge_ack(input int status);
 function automatic [31:0] get32(input integer o);get32={8'(bridge_byte(o)),8'(bridge_byte(o+1)),8'(bridge_byte(o+2)),8'(bridge_byte(o+3))};endfunction
 reg clk=0,pclk=0,read_clk;always #5 clk=~clk;always #17.029 pclk=~pclk; always @(clk)read_clk <= #2.75 ~clk;
 reg reset=1,dec_reset=1;
 wire begin_valid,byte_valid,commit_valid,abort_valid;wire [31:0]begin_id,begin_crc;wire[15:0]begin_length;wire[7:0]byte_data;
 reg clk200=0;always #2.5 clk200=~clk200;reg qcs=1,qck=0;reg[3:0]qhost=0;wire[3:0]qout,qoe;
 wire swrite,sread,cdc_overflow,wr;wire[11:0]saddr,addr;wire[31:0]swdata,srdata,data,rd,gray;wire[6:0]fifo_free;
 moonshine_qspi_endpoint_credit endpoint(.fifo_free(fifo_free),.clk200(clk200),.rst_n(!reset),.qspi_sck(qck),.qspi_cs_n(qcs),.qspi_dq_i(qhost),.dq_o(qout),.dq_oe(qoe),.buttons_native(12'd0),.vblank(1'b0),.irq_request(),.control(),.force_buttons_native(),.display_external(),.color_correct_enable(),.overlay_xctrl(),.overlay_yctrl(),.ov_wr(),.ov_addr(),.ov_data(),.core_write(swrite),.core_read(sread),.core_address(saddr),.core_wdata(swdata),.core_rdata(srdata));
 moonshine_bus_cdc_credit bridge(.spi_free(fifo_free),.spi_clk(clk200),.spi_reset(reset),.spi_write(swrite),.spi_read(sread),.spi_address(saddr),.spi_wdata(swdata),.spi_rdata(srdata),.overflow(cdc_overflow),.overflow_gray(gray),.core_clk(clk),.core_reset(reset),.core_write(wr),.core_address(addr),.core_wdata(data),.core_rdata(rd));
 bank_bus_adapter adapter(.clk(clk),.reset(reset),.wr(wr),.addr(addr),.data(data),.rd(rd),.accepted_frames(accepted_frames),.begin_valid(begin_valid),.begin_id(begin_id),.begin_length(begin_length),.begin_crc(begin_crc),.byte_valid(byte_valid),.byte_data(byte_data),.commit_valid(commit_valid),.abort_valid(abort_valid));
 wire begin_accept,reject,decode_grant,decode_bank,present,front_valid,read_ready,read_valid,read_error;
 wire [3:0] reject_reason;wire [31:0]decode_id,front_id,accepted_frames,dropped_frames;wire [15:0]decode_length;wire [7:0]read_data;
 reg decode_request=0,decode_done=0,start=0;wire vblank;reg front=0;
 wire byte_req;wire [15:0]byte_addr;wire start_accept,active,error,frame_done,out_valid,dec_accept;wire [31:0]out_data;wire [3:0]out_strb;
 wire pix_valid,dec_idle;wire [15:0]width,height,px,py;wire [7:0]red,green,blue;
 two_bank_storage store(.clk(clk),.reset(reset),.begin_valid(begin_valid),.begin_id(begin_id),.begin_length(begin_length),.begin_crc(begin_crc),.byte_valid(byte_valid),.byte_data(byte_data),.commit_valid(commit_valid),.abort_valid(abort_valid),.ingress_overflow(1'b0),.begin_accept(begin_accept),.reject(reject),.reject_reason(reject_reason),.decode_request(decode_request),.decode_done(decode_done),.decode_fail(1'b0),.decode_grant(decode_grant),.decode_bank(decode_bank),.decode_id(decode_id),.decode_length(decode_length),.read_req(byte_req),.read_addr(byte_addr),.read_ready(read_ready),.read_valid(read_valid),.read_error(read_error),.read_data(read_data),.vblank(vblank),.present(present),.front_valid(front_valid),.front_id(front_id),.accepted_frames(accepted_frames),.dropped_frames(dropped_frames));
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
 reg[15:0] expected[0:345599], expected0[0:345599], expected1[0:345599];
 integer base,baseline_underruns,baseline_writes,baseline_bursts,current_id=0;
 integer scan_pixels=0,scan_id=0,display_id=-1,scan_done0=0,scan_done1=0,scan_overlap=0;
 reg scan_enable=0,scan_in_frame=0;reg[15:0]scan_word,scan_expected;
 always @(posedge pclk)begin
  #0.001;
  if(scan_enable && de && lcd_x==0 && lcd_y==40)begin
   if(scan_in_frame)$fatal(1,"overlapping scan");scan_in_frame=1;scan_pixels=0;scan_id=display_id;
  end
  if(scan_in_frame && de && lcd_y>=40 && lcd_y<760 && lcd_x<480)begin
   if(display_id!=scan_id)$fatal(1,"front changed mid-scan");
   if(lcd_x!=scan_pixels%480 || lcd_y!=40+scan_pixels/480)$fatal(1,"scan order index=%0d x=%0d y=%0d",scan_pixels,lcd_x,lcd_y);
   scan_word={lcd_r[7:3],lcd_g[7:2],lcd_b[7:3]};
   scan_expected=scan_id==0?expected0[(lcd_y-40)*480+lcd_x]:expected1[(lcd_y-40)*480+lcd_x];
   if(scan_word!==scan_expected)$fatal(1,"scan mismatch id=%0d x=%0d y=%0d got=%h expected=%h",scan_id,lcd_x,lcd_y,scan_word,scan_expected);
   scan_pixels=scan_pixels+1;
   if(scan_pixels==345600)begin
    if(scan_id==0)scan_done0=scan_done0+1;else if(scan_id==2||scan_id==3)scan_done1=scan_done1+1;else $fatal(1,"invalid scan id");
    $display("SCAN_PASS id=%0d pixels=%0d",scan_id,scan_pixels);scan_in_frame=0;
   end
  end
 end
 reg [7:0] jpg0[0:49151],jpg1[0:49151];reg seen[0:345599];reg [2047:0] f0,f1,d0,d1;integer fd,n0,n1,dump,pixels=0,requests=0,responses=0,words=0,bytes_out=0;reg finished=0;integer k,i;reg[31:0]crc0,crc1;
 function automatic [31:0] cb(input [31:0]old,input[7:0]b);reg[31:0]v;integer j;begin v=old^b;for(j=0;j<8;j=j+1)v=v[0]?((v>>1)^32'hedb88320):v>>1;cb=v;end endfunction
 reg expect_crc_reject=0,crc_reject_seen=0;integer injected=0;
 always @(posedge clk)if(!reset)begin
  if(reject)begin if(expect_crc_reject&&reject_reason==3)crc_reject_seen=1;else $fatal(1,"unexpected bank reject reason=%0d",reject_reason);end
  if(cdc_overflow)$fatal(1,"QSPI overflow");
  if(error||read_error)$fatal(1,"reader error");
  if(byte_req)requests=requests+1;if(read_valid)responses=responses+1;
  if(frame_done)finished=1;
  if(out_valid&&dec_accept)begin words=words+1;for(integer z=0;z<4;z=z+1)if(out_strb[z])bytes_out=bytes_out+1;end
  if(tile_fault||protocol_fault)$fatal(1,"memory path fault");
  if(pix_valid&&!dec_reset&&tile_ready)begin
   if(px>=720||py>=480||width!=720||height!=480)$fatal(1,"pixel coordinate/dimensions %0d %0d %0d %0d",px,py,width,height);
   if(seen[px*480+py])$fatal(1,"duplicate pixel");seen[px*480+py]=1;expected[px*480+py]=pixel_color;if(current_id==0)expected0[px*480+py]=pixel_color;else expected1[px*480+py]=pixel_color;pixels=pixels+1;if(current_id==1&&scan_in_frame&&scan_id==0)scan_overlap=scan_overlap+1;
   $fdisplay(dump,"%0d %0d %04h",px,py,{red[7:3],green[7:2],blue[7:3]});
  end
 end
 task begin_transaction;begin qck=0;qhost=0;qcs=0;#100;end endtask
 task end_transaction;begin qck=0;qcs=1;#1;if(qoe!==0)$fatal(1,"CS bus not released");#99;end endtask
 task shift(input[31:0]value,input integer bits,input integer lanes,input realtime half_period);
 integer bitidx;begin for(bitidx=bits-lanes;bitidx>=0;bitidx=bitidx-lanes)begin
 qhost=(value>>bitidx)&((1<<lanes)-1);#(half_period);qck=1;#(half_period);qck=0;end end endtask
 task header(input[7:0]command,input[31:0]address,input realtime half_period);
 begin begin_transaction();shift(command,8,1,half_period);shift(address,32,4,half_period);end endtask
 task write_reg(input[11:0]a0,input[31:0]d0);
 reg[31:0]available;begin read_reg(12'h054,available);if(available<1||available>63)$fatal(1,"metadata write no credit");header(8'h54,32'he0000000|{20'd0,a0},12.5);shift(d0,32,4,12.5);end_transaction();end endtask
 task read_reg(input[11:0]a0,output[31:0]value);
 integer k;begin header(8'h55,32'he0000000|{20'd0,a0},31.25);shift(0,64,4,31.25);value=0;
 for(k=0;k<8;k=k+1)begin #31.25;qck=1;value=(value<<4)|qout;#31.25;qck=0;end end_transaction();end endtask
 task start_frame(input integer id,input integer n);begin
  current_id=id;
  @(negedge clk);decode_request=1;@(posedge clk);#1;if(!decode_grant||decode_id!=id||decode_length!=n)$fatal(1,"wrong grant");@(negedge clk);decode_request=0;
  repeat(4)@(negedge clk);dec_reset=0;@(negedge clk);start=1;@(posedge clk);#1;if(!start_accept)$fatal(1,"start failed");@(negedge clk);start=0;
 end endtask
 task finish_frame(input integer id,input integer n);begin
  while(pixels<345600 || !finished)begin @(posedge clk);#1;end
  if(pixels!=345600||requests!=n||responses!=n||bytes_out!=n||words!=(n+3)/4)$fatal(1,"accounting pixels=%0d req=%0d resp=%0d bytes=%0d words=%0d",pixels,requests,responses,bytes_out,words);
  while(!mem_idle||!tile_ready||tile_valid)@(negedge clk);
  if(model.writes-baseline_writes!=345600||model.write_bursts-baseline_bursts!=43200||underruns!=baseline_underruns)$fatal(1,"write/burst/underrun failure");
  base=front ? 0:24'h080000;for(integer j=0;j<345600;j=j+1)if(!seen[j]||model.mem[base+((j/480)+40)*480+(j%480)]!==expected[j])$fatal(1,"framebuffer mismatch index=%0d",j);
  $fclose(dump);$display("FRAME_PASS id=%0d bytes=%0d words=%0d pixels=%0d",id,n,words,pixels);
  @(negedge clk);decode_done=1;dec_reset=1;@(negedge clk);decode_done=0;while(!present)begin @(posedge clk);#1;end if(front_id!=id||!front_valid)$fatal(1,"presentation");front=!front;display_id=id;scan_enable=1;
  for(integer j=0;j<345600;j=j+1)if(model.mem[base+((j/480)+40)*480+(j%480)]!==expected[j])$fatal(1,"post-presentation framebuffer mismatch index=%0d",j);
  $display("PRESENT_PASS id=%0d front=%0d writes=345600 bursts=43200 underruns=0 framebuffer_pixels=345600",id,front);
 end endtask
 initial begin : main
  integer msglen,msgtype,seq,id,n,offset,len,i0,j,chunk,credit,tmp,rx_bytes=0,rx_active=0,rx_id=-1,published=0,aborts=0,expect_seq=0,nack_done=0;
  integer captured_pixels,captured_writes,saved_front=0,scans_before=0;reg[31:0]header_crc,stream_crc,rb;string dump_dir,outfile;
  if(!$value$plusargs("DUMP_DIR=%s",dump_dir))$fatal(1,"need dump dir");
  for(i=0;i<345600;i=i+1)seen[i]=0;
  for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24'h080000+i]=0;end
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);repeat(2000000)@(negedge clk);baseline_underruns=underruns;
  begin : transactions
   forever begin
    msglen=bridge_next();if(msglen<9)$fatal(1,"bad bridge message");msgtype=bridge_byte(0);seq=get32(1);id=get32(5);
    if(seq!=expect_seq)$fatal(1,"bad sequence");expect_seq=expect_seq+1;
    case(msgtype)
     8'h42:begin
      if(msglen!=17||rx_active||!((published==0&&id==0)||(published==1&&aborts==0&&id==1)||(published==1&&aborts==1&&!nack_done&&id==2)||(published==1&&aborts==1&&nack_done&&id==3)))$fatal(1,"begin order");
      n=get32(9);header_crc=get32(13);if(n<1||n>49152)$fatal(1,"length cap");
      rx_active=1;rx_id=id;rx_bytes=0;stream_crc=32'hffffffff;captured_pixels=pixels;captured_writes=model.writes;
      write_reg('h14,id);write_reg('h18,n);write_reg('h1c,{16'd720,16'd480});write_reg('h20,header_crc);write_reg('h24,1);
      read_reg('h028,rb);if(rb!=0)$fatal(1,"begin fence");
      $display("MULTI_BEGIN seq=%0d id=%0d bytes=%0d",seq,id,n);$fflush();if(bridge_ack(0)!=0)$fatal(1,"ack");
     end
     8'h44:begin
      offset=get32(9);len=(bridge_byte(13)<<8)|bridge_byte(14);
      if(!rx_active||id!=rx_id||msglen!=15+len||offset!=rx_bytes||len<1||len>1024||rx_bytes+len>n)$fatal(1,"bad data");
      for(i0=0;i0<len;i0=i0+chunk)begin
       read_reg('h028,rb);if(rb!=rx_bytes+i0)$fatal(1,"received fence");read_reg('h054,rb);credit=rb;if(credit>63)$fatal(1,"credit");chunk=(len-i0<credit)?len-i0:credit;
       if(chunk!=0)begin header(8'h40,32'he0000100,12.5);for(j=0;j<chunk;j=j+1)begin tmp=bridge_byte(15+i0+j);if(tmp<0||tmp>255)$fatal(1,"payload");if(id==2 && offset+i0+j==1234)begin shift(tmp^1,8,4,12.5);injected=injected+1;end else shift(tmp,8,4,12.5);stream_crc=cb(stream_crc,8'(tmp));end end_transaction();end
      end
      rx_bytes=rx_bytes+len;if(bridge_ack(0)!=0)$fatal(1,"data ack");
     end
     8'h43:begin
      if(msglen!=9||!rx_active||id!=rx_id||rx_bytes!=n||~stream_crc!=header_crc)$fatal(1,"commit");
      read_reg('h028,rb);if(rb!=n)$fatal(1,"last fence");
      if(id==2)begin
       if(injected!=1)$fatal(1,"mutation count");scans_before=scan_done0;expect_crc_reject=1;write_reg('h24,4);read_reg('h02c,rb);
       if(rb!=1||!crc_reject_seen||dropped_frames!=2)$fatal(1,"expected CRC rejection missing");rx_active=0;
       repeat(2)begin do @(negedge clk);while(!vblank);end
       if(front!=saved_front||front_id!=0||model.writes!=captured_writes||pixels!=captured_pixels||accepted_frames!=1||cdc_overflow||underruns!=baseline_underruns||scan_done0<=scans_before)$fatal(1,"CRC reject state/scan");
       for(i=0;i<345600;i=i+1)if(model.mem[(saved_front?24'h080000:0)+((i/480)+40)*480+(i%480)]!==expected0[i])$fatal(1,"CRC reject changed front");
       $display("POST_GUEST_CRC_REJECT seq=%0d id=2 mutated_bytes=%0d crc_reject=1 prior_front_intact=1 full_scan_after=1 commits=1",seq,injected);$fflush();
       if(bridge_ack(5)!=0)$fatal(1,"negative ack send");nack_done=1;expect_crc_reject=0;$display("TEST_PASS_POST_GUEST_CRC_REJECT");continue;
      end
      write_reg('h24,4);read_reg('h02c,rb);if(rb!=published+1)$fatal(1,"commit fence");rx_active=0;
      for(i=0;i<345600;i=i+1)seen[i]=0;pixels=0;requests=0;responses=0;words=0;bytes_out=0;finished=0;baseline_writes=model.writes;baseline_bursts=model.write_bursts;
      outfile=$sformatf("%s/frame-%0d-rgb565.txt",dump_dir,id);dump=$fopen(outfile,"w");if(!dump)$fatal(1,"dump");
      start_frame(id,n);finish_frame(id,n);published=published+1;
      if(id==0)begin saved_front=front;while(!scan_done0)@(negedge clk);end
      else begin if(front==saved_front)$fatal(1,"front not changed on second commit");for(i=0;i<345600;i=i+1)if(model.mem[(saved_front?24'h080000:0)+((i/480)+40)*480+(i%480)]!==expected0[i])$fatal(1,"prior front changed during recovery");while(!scan_done1)@(negedge clk);end
      $display("MULTI_PRESENT seq=%0d id=%0d bytes=%0d published=%0d pixels=345600",seq,id,n,published);$fflush();
      if(bridge_ack(0)!=0)$fatal(1,"commit ack");
      if(published==2)begin if(aborts!=1||!nack_done||id!=3)$fatal(1,"missing abort/nack/recovery");$display("TEST_PASS_LIVE_GUEST_NACK");disable transactions;end
     end
     8'h41:begin
      if(msglen!=9||!rx_active||id!=rx_id||id!=1||published!=1||rx_bytes<=0||rx_bytes>=n)$fatal(1,"abort");write_reg('h24,2);read_reg('h02c,rb);if(rb!=1)$fatal(1,"abort fence");rx_active=0;aborts=aborts+1;
      repeat(2)begin do @(negedge clk);while(!vblank);end
      if(front!=saved_front||front_id!=0||model.writes!=captured_writes||pixels!=captured_pixels||accepted_frames!=1||dropped_frames!=1||cdc_overflow||underruns!=baseline_underruns)$fatal(1,"abort state");
      for(i=0;i<345600;i=i+1)if(model.mem[(saved_front?24'h080000:0)+((i/480)+40)*480+(i%480)]!==expected0[i])$fatal(1,"prior front changed at abort");
      $display("MULTI_ABORT seq=%0d id=%0d bytes=%0d prior_front_intact=1",seq,id,rx_bytes);$fflush();if(bridge_ack(0)!=0)$fatal(1,"abort ack");
     end
     default:$fatal(1,"bad message type");
    endcase
   end
  end
  $finish;
 end
 initial begin #1200000000;$fatal(1,"watchdog");end
endmodule

// Test-only register adapter: frame registers/commands are ordered CDC writes.
// It is NOT production MMIO; status 0x28 and 0x2c are CDC-draining fences.
module bank_bus_adapter(input wire clk,reset,wr,input wire[11:0]addr,input wire[31:0]data,output reg[31:0]rd,input wire[31:0]accepted_frames,
 output wire begin_valid,output reg[31:0]begin_id,output reg[15:0]begin_length,output reg[31:0]begin_crc,output wire byte_valid,output wire[7:0]byte_data,output wire commit_valid,output wire abort_valid);
 reg[31:0]dimensions,received;assign begin_valid=wr&&addr==12'h024&&data==1;assign commit_valid=wr&&addr==12'h024&&data==4;assign abort_valid=wr&&addr==12'h024&&data==2;
 assign byte_valid=wr&&addr==12'h100;assign byte_data=data[7:0];
 always @* begin rd=0;case(addr)12'h028:rd=received;12'h02c:rd=accepted_frames;default:rd=0;endcase end
 always @(posedge clk)begin
  if(reset)begin begin_id<=0;begin_length<=0;begin_crc<=0;dimensions<=0;received<=0;end
  else if(wr)case(addr)
   12'h014:begin_id<=data;12'h018:begin_length<=data[15:0];12'h01c:dimensions<=data;12'h020:begin_crc<=data;
   12'h024:if(data==1)begin if(dimensions!={16'd720,16'd480})$fatal(1,"bad dimensions");received<=0;end
   12'h100:received<=received+1;
   default:$fatal(1,"unknown adapter write %h",addr);
  endcase
 end
endmodule
