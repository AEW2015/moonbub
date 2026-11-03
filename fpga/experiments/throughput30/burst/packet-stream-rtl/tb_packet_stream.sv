`timescale 1ns/1ps
// Integration test only: ten 720x480 real JPEGs -> decoder -> tile transpose -> BL8
// writer -> functional SDRAM, while LCD scans the other buffer.
module tb_packet_stream;
 reg clk=0,pclk=0,read_clk; always #5 clk=~clk; always #17.029 pclk=~pclk;
 always @(clk)read_clk <= #2.75 ~clk;
 reg reset=1;wire wr;wire[11:0]addr;wire[31:0]data,rd;
 reg clk200=0;always #2.5 clk200=~clk200;
 reg qcs=1,qck=0;reg[3:0]qhost=0;wire[3:0]qout,qoe;
 wire [6:0] fifo_free;wire swrite,sread,cdc_overflow;wire[11:0]saddr;wire[31:0]swdata,srdata,gray;
 reg[31:0]gray_meta=0,gray_sync=0,lost=0;
 function automatic[31:0]ungray(input[31:0]v);integer k;begin for(k=0;k<32;k=k+1)ungray[k]=^(v>>k);end endfunction
 always @(posedge clk)begin if(reset)begin gray_meta<=0;gray_sync<=0;lost<=0;end else begin gray_meta<=gray;gray_sync<=gray_meta;lost<=ungray(gray_sync);end end
 moonshine_qspi_endpoint_credit endpoint(.fifo_free(fifo_free),.clk200(clk200),.rst_n(!reset),.qspi_sck(qck),.qspi_cs_n(qcs),.qspi_dq_i(qhost),.dq_o(qout),.dq_oe(qoe),
 .buttons_native(12'd0),.vblank(1'b0),.irq_request(),.control(),.force_buttons_native(),.display_external(),.color_correct_enable(),
 .overlay_xctrl(),.overlay_yctrl(),.ov_wr(),.ov_addr(),.ov_data(),.core_write(swrite),.core_read(sread),.core_address(saddr),.core_wdata(swdata),.core_rdata(srdata));
 moonshine_bus_cdc_credit bridge(.spi_free(fifo_free),.spi_clk(clk200),.spi_reset(reset),.spi_write(swrite),.spi_read(sread),.spi_address(saddr),.spi_wdata(swdata),.spi_rdata(srdata),.overflow(cdc_overflow),.overflow_gray(gray),
 .core_clk(clk),.core_reset(reset),.core_write(wr),.core_address(addr),.core_wdata(data),.core_rdata(rd));
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
 .pixel_valid(pv),.pixel_ready(pr),.pixel_address(pa),.pixel_rgb565(pd),.scanout_underruns(underruns),.transport_overflows(lost));
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
 string fixture_dir,dump_dir,jpeg_file,dump_file,trace_file;
 integer packet_at[0:63],packet_offset[0:63],packet_len[0:63],packet_count=0;
 integer ring_offset[0:4],ring_len[0:4],ring_head=0,ring_tail=0,ring_count=0,ring_bytes=0,ring_high=0,queue_drop=0;
 integer corrupt_offset=-1,drop_packet=-1,tx_byte,abort_cycle=0,gap_cycle=0,gap_expected=0,gap_actual=0;
 reg abort_detected=0;
 integer n_packets=0,bytes_streamed=0,first_arrival=-1,first_send=-1,last_arrival=-1,last_send=-1,pkt_off,pkt_len,final_crc;
 reg packet_done=0;
 integer trace_id[0:9],trace_fixture[0:9],trace_capture[0:9],trace_ready[0:9];
 integer trace_count, trace_line, trace_status, trace_fd, consumed=0, q_fixture=0, q_ready=0, frame_fixture=0, frame_ready=0;reg producer_done=0;
 integer fd,dump,n,i,j,chunk,credit,credit_reads=0,x,y,pixels=0,cycles=0,readback_i,baseline_underruns,base;reg[31:0]readback;
 integer frame,frame_start_pixels,frame_start_writes,frame_start_bursts,arrival,commit_cycle,target,service_start;
 integer first_present,last_present,epoch,max_latency=0;
 integer q_frame=0,q_arrival=0,enqueued=0,q_highwater=0,q_overflows=0;reg q_valid=0;
 always @(posedge clk)begin
  cycles<=cycles+1;
  if(pv&&pr)begin
   base=front ? 0:24'h080000;x=((pa-base)/480)-40;y=(pa-base)%480;
   if(x<0||x>=720||y<0||y>=480)$fatal(1,"invalid coordinate frame=%0d x=%0d y=%0d address=%h",frame,x,y,pa);
   if(seen[x*480+y])$fatal(1,"duplicate decoder pixel frame=%0d x=%0d y=%0d",frame,x,y);
   expected[x*480+y]<=pd;seen[x*480+y]<=1;pixels<=pixels+1;
   $fdisplay(dump,"%0d %0d %04h",x,y,pd);
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
 begin header(8'h54,32'he0000000|{20'd0,a0},12.5);shift(d0,32,4,12.5);end_transaction();end endtask
 task read_reg(input[11:0]a0,output[31:0]value);
 integer k;begin header(8'h55,32'he0000000|{20'd0,a0},31.25);shift(0,64,4,31.25);value=0;
 for(k=0;k<8;k=k+1)begin #31.25;qck=1;value=(value<<4)|qout;#31.25;qck=0;end end_transaction();end endtask
 initial begin
  if(!$value$plusargs("CORRUPT_OFFSET=%d",corrupt_offset))corrupt_offset=-1;
  if(!$value$plusargs("DROP_PACKET=%d",drop_packet))drop_packet=-1;
  if(!$value$plusargs("FIXTURE_DIR=%s",fixture_dir))$fatal(1,"need FIXTURE_DIR");
  if(!$value$plusargs("DUMP_DIR=%s",dump_dir))$fatal(1,"need DUMP_DIR");
  if(!$value$plusargs("TRACE_FILE=%s",trace_file))$fatal(1,"need TRACE_FILE");
  trace_fd=$fopen(trace_file,"r");if(!trace_fd)$fatal(1,"missing packet trace");
  trace_status=$fscanf(trace_fd,"%d\n",packet_count);
  if(trace_status!=1||packet_count<1||packet_count>64)$fatal(1,"bad count");
  if(drop_packet!=-1 && (drop_packet<1||drop_packet>=packet_count-1))$fatal(1,"drop index must be a middle packet");
  for(trace_line=0;trace_line<packet_count;trace_line=trace_line+1)begin
   trace_status=$fscanf(trace_fd,"%d %d %d\n",packet_at[trace_line],packet_offset[trace_line],packet_len[trace_line]);
   if(trace_status!=3||packet_at[trace_line]<0||packet_offset[trace_line]<0||packet_len[trace_line]<1||packet_len[trace_line]>1024)$fatal(1,"invalid packet");
   if(trace_line==0 && packet_offset[trace_line]!=0)$fatal(1,"first packet not SOF");
   if(trace_line>0 && (packet_at[trace_line]<packet_at[trace_line-1]||packet_offset[trace_line]!=packet_offset[trace_line-1]+packet_len[trace_line-1]))$fatal(1,"packet order/offset");
  end
  $fclose(trace_fd);
  jpeg_file=$sformatf("%s/0000.jpg",fixture_dir);fd=$fopen(jpeg_file,"rb");if(!fd)$fatal(1,"missing jpeg");
  n=$fread(jpeg,fd);$fclose(fd);if(n<=0||n>262144||packet_offset[packet_count-1]+packet_len[packet_count-1]!=n)$fatal(1,"bad length");
  // This expected CRC is the MSV1 SOF metadata, verified against the fixture by the host trace generator.
  crc=32'hffffffff;for(i=0;i<n;i=i+1)crc=core.crc_byte(crc,jpeg[i]);crc=~crc;
  final_crc=32'hffffffff;
  for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24'h080000+i]=0;end
  for(i=0;i<345600;i=i+1)seen[i]=0;
  dump_file=$sformatf("%s/0000-rgb565.txt",dump_dir);dump=$fopen(dump_file,"w");if(!dump)$fatal(1,"dump open");
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);
  repeat(2000000)@(negedge clk);baseline_underruns=underruns;epoch=cycles;frame=0;
  fork
   begin : packet_producer
    integer k;
    for(k=0;k<packet_count;k=k+1)begin
     while(cycles<epoch+packet_at[k])@(negedge clk);
     if(k==0)first_arrival=cycles;last_arrival=cycles;
     if(k!=drop_packet && !abort_detected)begin
     if(ring_count>=5 || ring_bytes+packet_len[k]+40>5320)begin
      queue_drop=queue_drop+1;$fatal(1,"bounded packet queue overflow packet=%0d",k);
     end
     ring_offset[ring_tail]=packet_offset[k];ring_len[ring_tail]=packet_len[k];ring_tail=(ring_tail+1)%5;
     ring_count=ring_count+1;ring_bytes=ring_bytes+packet_len[k]+40;
     if(ring_bytes>ring_high)ring_high=ring_bytes;
     end
    end
    packet_done=1;
   end
   begin : packet_consumer
    integer k,off,plen,z;
    for(k=0;k<packet_count;k=k+1)begin
     @(posedge clk);#0.001;
     while(ring_count==0)begin @(posedge clk);#0.001;end
     off=ring_offset[ring_head];plen=ring_len[ring_head];
     if(off!=bytes_streamed)begin
      if(drop_packet<0 || bytes_streamed==0)$fatal(1,"unexpected gap k=%0d off=%0d expected=%0d",k,off,bytes_streamed);
      gap_cycle=cycles;gap_expected=bytes_streamed;gap_actual=off;abort_detected=1;
      write_reg('h24,2);abort_cycle=cycles;
      ring_count=0;ring_bytes=0;ring_head=ring_tail;
      break;
     end
     if(k==0)begin
      if(!core.ready_state)$fatal(1,"FPGA busy at SOF");
      write_reg('h14,0);write_reg('h18,n);write_reg('h1c,{16'd720,16'd480});write_reg('h20,crc);write_reg('h24,1);
     end
     for(i=off;i<off+plen;i=i+chunk)begin
      read_reg('h00c,readback);if(readback!==n-i)$fatal(1,"remaining mismatch offset=%0d got=%0d",i,readback);
      read_reg('h054,readback);credit=readback;credit_reads=credit_reads+1;if(credit>63)$fatal(1,"invalid fifo credit");
      chunk=(off+plen-i<credit)?off+plen-i:credit;
      if(chunk!=0)begin
       header(8'h40,32'he0000100,12.5);
       for(j=0;j<chunk;j=j+1)begin
        tx_byte=jpeg[i+j];if(i+j==corrupt_offset)tx_byte=tx_byte^1;
        shift(tx_byte,8,4,12.5);if(i+j==0)first_send=cycles;final_crc=core.crc_byte(final_crc,tx_byte[7:0]);
       end
       end_transaction();
      end
     end
     bytes_streamed=bytes_streamed+plen;n_packets=n_packets+1;last_send=cycles;
     // Keep in-flight packet charged to the queue until forwarding completes.
     ring_head=(ring_head+1)%5;ring_count=ring_count-1;ring_bytes=ring_bytes-plen-40;
    end
    if(!abort_detected)begin
    if(!packet_done || ring_count!=0 || ring_bytes!=0 || bytes_streamed!=n || ~final_crc!=crc)$fatal(1,"invalid packet completion or CRC");
    read_reg('h028,readback);if(readback!==n)$fatal(1,"receive count mismatch");
    if(cdc_overflow||lost!=0)$fatal(1,"QSPI overflow");
    write_reg('h24,4);commit_cycle=cycles;
    end
   end
  join
  if(abort_detected)begin
   repeat(2)begin do @(negedge clk); while(!frame_boundary);end
   if(drop_packet<0 || !packet_done || gap_actual<=gap_expected || commit_cycle!=0 || queue_drop!=0 || core.complete_frames!=0 || core.decoded_frames!=0 || core.presented_frames!=0 || fvalid || front || core.receiving || core.decoding || core.pending || pixels!=0 || model.writes!=0 || lost!=0 || cdc_overflow || underruns!=baseline_underruns)$fatal(1,"partial frame published or abort failed");
   $fclose(dump);
   $display("MISSING_PACKET_RESULT dropped_index=%0d forwarded_packets=%0d forwarded_bytes=%0d gap_expected=%0d gap_actual=%0d gap_cycle=%0d abort_cycle=%0d check_cycle=%0d frame_boundaries=2 presented=%0d pixels=%0d writes=%0d",drop_packet,n_packets,bytes_streamed,gap_expected,gap_actual,gap_cycle,abort_cycle,cycles,core.presented_frames,pixels,model.writes);
   $display("TEST_PASS_MISSING_PACKET_ABORT");
  end else begin
  while(core.presented_frames<1&&core.faults==0&&!tile_fault&&!protocol_fault)@(negedge clk);
  if(core.faults!=0||tile_fault||protocol_fault||!fvalid||core.last_presented!=0||core.presented_frames!=1)$fatal(1,"publication failure");
  if(pixels!=345600||model.writes!=345600||model.write_bursts!=43200)$fatal(1,"pixel conservation");
  base=front ? 24'h080000:0;
  for(i=0;i<345600;i=i+1)begin
   readback_i=base+((i/480)+40)*480+(i%480);
   if(!seen[i]||model.mem[readback_i]!==expected[i])$fatal(1,"framebuffer mismatch i=%0d",i);
  end
  if(underruns!=baseline_underruns||core.drops!=0||core.overflows!=0||queue_drop!=0)$fatal(1,"error counters");
  $fclose(dump);
  $display("PACKET_STREAM_RESULT packets=%0d bytes=%0d queue_high_bytes=%0d queue_drops=%0d capture_cycle=%0d first_arrival=%0d first_send=%0d last_arrival=%0d last_send=%0d commit_cycle=%0d present_cycle=%0d writes=%0d bursts=%0d underruns=%0d credit_reads=%0d",n_packets,bytes_streamed,ring_high,queue_drop,epoch,first_arrival,first_send,last_arrival,last_send,commit_cycle,cycles,model.writes,model.write_bursts,underruns-baseline_underruns,credit_reads);
  $display("TEST_PASS_PACKET_STREAM");
  end
  $finish;
 end
 initial begin #600000000;$fatal(1,"multiframe watchdog frame=%0d cycle=%0d",frame,cycles);end
endmodule
