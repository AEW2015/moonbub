`timescale 1ns/1ps
// Integration test only: ten 720x480 real JPEGs -> decoder -> tile transpose -> BL8
// writer -> functional SDRAM, while LCD scans the other buffer.
module tb_sync_adapter;
 import "DPI-C" function int bridge_next();
 import "DPI-C" function int bridge_byte(input int idx);
 import "DPI-C" function int bridge_ack(input int status);
 function automatic [31:0] get32(input integer o);
  get32={8'(bridge_byte(o)),8'(bridge_byte(o+1)),8'(bridge_byte(o+2)),8'(bridge_byte(o+3))};
 endfunction
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
 reg[15:0]oracle[0:345599]; reg[15:0]expected[0:345599];reg seen[0:345599];reg[31:0]crc;
 string fixture_dir,dump_dir,jpeg_file,dump_file,trace_file;
 integer packet_at[0:63],packet_offset[0:63],packet_len[0:63],packet_count=0;
 integer ring_offset[0:4],ring_len[0:4],ring_head=0,ring_tail=0,ring_count=0,ring_bytes=0,ring_high=0,queue_drop=0;
 integer corrupt_offset=-1,drop_packet=-1,tx_byte,abort_cycle=0,gap_cycle=0,gap_expected=0,gap_actual=0;
 reg abort_detected=0;
 integer n_packets=0,bytes_streamed=0,first_arrival=-1,first_send=-1,last_arrival=-1,last_send=-1,pkt_off,pkt_len,final_crc;
 reg packet_done=0;
 integer completed=0, target_frames=10, corrupt_test=0, reset_test=0, resets=0, queue_wait_cycles=0; string oracle_file;
 integer message_len,msg_type,received_bytes=0,payload_len,payload_offset,bridge_data,active=0,abort_count=0,finish_after_abort=0;
 reg[31:0] expected_sequence=0,message_sequence,message_id,active_id,header_crc,stream_crc;
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
   if(pd!==oracle[x*480+y])$fatal(1,"independent oracle mismatch frame=%0d x=%0d y=%0d actual=%h expected=%h",frame,x,y,pd,oracle[x*480+y]);
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
  if(!$value$plusargs("ORACLE=%s",oracle_file))$fatal(1,"need oracle");
  $readmemh(oracle_file,oracle);
  if(!$value$plusargs("FRAMES=%d",target_frames))target_frames=10;
  if(!$value$plusargs("CORRUPT_TEST=%d",corrupt_test))corrupt_test=0;
  if(!$value$plusargs("RESET_TEST=%d",reset_test))reset_test=0;
  if(!$value$plusargs("FINISH_AFTER_ABORT=%d",finish_after_abort))finish_after_abort=0;
  if(finish_after_abort!=0 && finish_after_abort!=1)$fatal(1,"invalid abort test mode");
  if(!$value$plusargs("DUMP_DIR=%s",dump_dir))$fatal(1,"need DUMP_DIR");
  for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24'h080000+i]=0;end
  for(i=0;i<345600;i=i+1)seen[i]=0;
  dump_file=$sformatf("%s/live-rgb565.txt",dump_dir);dump=$fopen(dump_file,"w");if(!dump)$fatal(1,"dump open");
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);
  repeat(2000000)@(negedge clk);baseline_underruns=underruns;
  // File-backed source adapter, one bounded event; no socket and no guest time claim.
  // Polling yields actual RTL time: all core/memory/pixel clocks continue during idle.
  begin : transaction_loop
  forever begin
   message_len=0;
   while(message_len==0)begin
    message_len=bridge_next();
    if(message_len==0)begin queue_wait_cycles=queue_wait_cycles+1;@(negedge clk);end
   end
   if(message_len<0)$fatal(1,"bridge socket read error %0d",message_len);
   msg_type=bridge_byte(0);message_sequence=get32(1);message_id=get32(5);
   if(message_sequence!==expected_sequence)begin i=bridge_ack(2);$fatal(1,"sequence expected=%0d got=%0d",expected_sequence,message_sequence);end
   expected_sequence=expected_sequence+1;
   case(msg_type)
    8'h42:begin
     if(active!=0)begin i=bridge_ack(3);$fatal(1,"begin while active");end
     n=get32(9);header_crc=get32(13);
     if(n<1||n>262144||!core.ready_state)begin i=bridge_ack(3);$fatal(1,"bad begin/busy");end
     for(i=0;i<345600;i=i+1)seen[i]=0;
     frame_start_pixels=pixels;frame_start_writes=model.writes;frame_start_bursts=model.write_bursts;
     active_id=message_id;frame=message_id;received_bytes=0;stream_crc=32'hffffffff;active=1;
     write_reg('h14,active_id);write_reg('h18,n);write_reg('h1c,{16'd720,16'd480});write_reg('h20,header_crc);write_reg('h24,1);
     $display("BRIDGE_BEGIN seq=%0d id=%0d bytes=%0d cycle=%0d",message_sequence,active_id,n,cycles);$fflush();
     if(bridge_ack(0)!=0)$fatal(1,"begin ack failed");
    end
    8'h44:begin
     payload_offset=get32(9);payload_len=(bridge_byte(13)<<8)|bridge_byte(14);
     if(active!=1||message_id!=active_id||payload_len<1||payload_len>1024||payload_offset!=received_bytes||received_bytes+payload_len>n)begin i=bridge_ack(4);$fatal(1,"bad data header/offset");end
     for(i=0;i<payload_len;i=i+chunk)begin
      read_reg('h00c,readback);if(readback!==n-received_bytes-i)$fatal(1,"remaining mismatch");
      read_reg('h054,readback);credit=readback;credit_reads=credit_reads+1;if(credit>63)$fatal(1,"bad FIFO credit");
      chunk=(payload_len-i<credit)?payload_len-i:credit;
      if(chunk!=0)begin
       header(8'h40,32'he0000100,12.5);
       for(j=0;j<chunk;j=j+1)begin
        bridge_data=bridge_byte(15+i+j);if(bridge_data<0||bridge_data>255)$fatal(1,"bridge byte unavailable");
        shift(bridge_data,8,4,12.5);stream_crc=core.crc_byte(stream_crc,bridge_data[7:0]);
       end
       end_transaction();
      end
     end
     received_bytes=received_bytes+payload_len;
     if(cdc_overflow||lost!=0)$fatal(1,"QSPI overflow");
     $display("BRIDGE_DATA seq=%0d id=%0d offset=%0d bytes=%0d cycle=%0d",message_sequence,active_id,payload_offset,payload_len,cycles);$fflush();
     if(bridge_ack(0)!=0)$fatal(1,"data ack failed");
    end
    8'h43:begin
     if(active!=1||message_id!=active_id||received_bytes!=n)begin i=bridge_ack(5);$fatal(1,"invalid commit size/CRC");end
     read_reg('h028,readback);if(readback!==n)$fatal(1,"receive count mismatch");
     write_reg('h24,4);commit_cycle=cycles;active=0;
     if(corrupt_test)begin
      repeat(100)@(negedge clk);
      read_reg('h038,readback);
      if(readback!=1||core.presented_frames!=0||pixels!=0||model.writes!=0)$fatal(1,"corruption must be rejected by actual RTL");
      $display("RTL_CORRUPTION_REJECTED seq=%0d faults=%0d time_ps=%0d",message_sequence,readback,($time*64'd1000));
      if(bridge_ack(0)!=0)$fatal(1,"corrupt response trace");
      $display("TEST_PASS_CORRUPTION_REJECTION");disable transaction_loop;
     end
     while(core.presented_frames<completed+1&&core.faults==0&&!tile_fault&&!protocol_fault)@(negedge clk);
     if(core.faults!=0||tile_fault||protocol_fault||!fvalid||core.last_presented!=active_id||core.presented_frames!=completed+1)$fatal(1,"publication failure");
     if(pixels-frame_start_pixels!=345600||model.writes-frame_start_writes!=345600||model.write_bursts-frame_start_bursts!=43200)$fatal(1,"pixel conservation");
     base=front ? 24'h080000:0;
     for(i=0;i<345600;i=i+1)begin
      readback_i=base+((i/480)+40)*480+(i%480);
      if(!seen[i]||model.mem[readback_i]!==oracle[i])$fatal(1,"framebuffer oracle mismatch i=%0d",i);
     end
     if(underruns!=baseline_underruns||core.drops!=abort_count||core.overflows!=0)$fatal(1,"core counters");
     read_reg('h048,readback);if(readback!=active_id)$fatal(1,"actual presented-id response");
     completed=completed+1;
     $display("BRIDGE_PRESENT seq=%0d id=%0d bytes=%0d events=%0d commit_cycle=%0d present_cycle=%0d pixels=%0d credit_reads=%0d time_ps=%0d refreshes=%0d",message_sequence,active_id,n,expected_sequence,commit_cycle,cycles,pixels,credit_reads,($time*64'd1000),model.refreshes);$fflush();
     if(bridge_ack(0)!=0)$fatal(1,"commit ack failed");
     if(completed==target_frames)begin
      $display("TEST_PASS_SYNC_ADAPTER frames=%0d exact_pixels=%0d idle_cycles=%0d resets=%0d",completed,pixels,queue_wait_cycles,resets);disable transaction_loop;
     end
    end
    8'h41:begin
     if(active!=1||message_id!=active_id)begin i=bridge_ack(6);$fatal(1,"invalid abort");end
     write_reg('h24,2);active=0;abort_count=abort_count+1;
     repeat(50)@(negedge clk);
     if(finish_after_abort)begin
      if(received_bytes<=0||received_bytes>=n)$fatal(1,"abort test requires partial data");
      repeat(2)begin do @(negedge clk); while(!frame_boundary);end
     end
     if(core.receiving||core.decoding||core.pending||core.complete_frames!=0||core.decoded_frames!=0||core.presented_frames!=0||fvalid||front||pixels!=0||model.writes!=0||cdc_overflow||lost!=0||underruns!=baseline_underruns||core.drops!=abort_count)$fatal(1,"abort failure");
     $display("BRIDGE_ABORT seq=%0d id=%0d bytes=%0d cycle=%0d presented=%0d pixels=%0d writes=%0d",message_sequence,message_id,received_bytes,cycles,core.presented_frames,pixels,model.writes);$fflush();
     if(bridge_ack(0)!=0)$fatal(1,"abort ack failed");
     if(finish_after_abort)begin $display("TEST_PASS_LIVE_ABORT");disable transaction_loop;end
     if(reset_test)begin
      reset=1;repeat(8)@(negedge clk);reset=0;resets=resets+1;abort_count=0;
      while(!mem_idle)@(negedge clk);
      repeat(2000000)@(negedge clk);baseline_underruns=underruns;
      if(core.presented_frames||core.faults||core.receiving||core.pending)$fatal(1,"reset did not clear core");
      $display("RTL_RESET_RECOVERY time_ps=%0d",($time*64'd1000));
     end
     received_bytes=0;
    end
    default:begin i=bridge_ack(7);$fatal(1,"bad event type");end
   endcase
  end
  end
  $finish;
 end
 initial begin #1000000000;$fatal(1,"live bridge watchdog");end
endmodule
