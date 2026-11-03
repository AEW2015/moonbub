`timescale 1ns/1ps
// Integration test only: ten 720x480 real JPEGs -> decoder -> tile transpose -> BL8
// writer -> functional SDRAM, while LCD scans the other buffer.
module tb_scheduled_guest;
 import "DPI-C" function int trace_open(input string name);
 import "DPI-C" function int trace_next();
 import "DPI-C" function int trace_at();
 import "DPI-C" function int trace_byte(input int idx);

 function automatic [31:0] get32(input integer o);
  get32={ring_mem[ring_head][o],ring_mem[ring_head][o+1],ring_mem[ring_head][o+2],ring_mem[ring_head][o+3]};
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
 reg[15:0]expected[0:345599];reg seen[0:345599];reg[31:0]crc;
 string fixture_dir,dump_dir,jpeg_file,dump_file,trace_file;
 integer packet_at[0:63],packet_offset[0:63],packet_len[0:63],packet_count=0;
 integer corrupt_offset=-1,drop_packet=-1,tx_byte,abort_cycle=0,gap_cycle=0,gap_expected=0,gap_actual=0;
 reg abort_detected=0;
 integer n_packets=0,bytes_streamed=0,first_arrival=-1,first_send=-1,last_arrival=-1,last_send=-1,pkt_off,pkt_len,final_crc;
 reg packet_done=0;
 integer message_len,msg_type,received_bytes=0,payload_len,payload_offset,bridge_data,active=0,abort_count=0,finish_after_abort=0;
 reg[31:0] expected_sequence=0,message_sequence,message_id,active_id,header_crc,stream_crc;
 reg[7:0] ring_mem[0:4][0:1038];
 integer ring_sizes[0:4],ring_head=0,ring_tail=0,ring_count=0,ring_bytes=0,ring_high=0;
 integer enqueued=0,seen_events=0,discard_frame=-1,overflow_pending=0,drop_count=0,stall_cycles=0,stall_once=0,source_done=0,sim_epoch=0;
 integer current_len=0,local_offset=0,look_at=0,look_len=0,producer_seq=0,producer_id=0,producer_type=0,producer_index=0,slot_seq=0;
 string trace_name;
 reg[15:0] saved_front_data[0:345599];
 integer published=0,base_pixels=0,base_writes=0,base_bursts=0,saved_front=0,idx,frame_dumps=0;
 integer trace_id[0:9],trace_fixture[0:9],trace_capture[0:9],trace_ready[0:9];
 integer trace_count, trace_line, trace_status, trace_fd, consumed=0, q_fixture=0, q_ready=0, frame_fixture=0, frame_ready=0;reg producer_done=0;
 integer fd,dump,n,i,j,chunk,credit,credit_reads=0,x,y,pixels=0,cycles=0,readback_i,baseline_underruns,base;reg[31:0]readback;
 integer frame,frame_start_pixels,frame_start_writes,frame_start_bursts,arrival,commit_cycle,target,service_start;
 integer first_present,last_present,epoch,max_latency=0;
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
  if(!$value$plusargs("TRACE_FILE=%s",trace_name))$fatal(1,"need TRACE_FILE");
  if(!$value$plusargs("DUMP_DIR=%s",dump_dir))$fatal(1,"need DUMP_DIR");
  if(!$value$plusargs("STALL_CYCLES=%d",stall_cycles))stall_cycles=0;
  if(stall_cycles<0||stall_cycles>2000000)$fatal(1,"bad stall");
  if(trace_open(trace_name)!=0)$fatal(1,"trace open");
  for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24'h080000+i]=0;end
  for(i=0;i<345600;i=i+1)seen[i]=0;
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);
  repeat(2000000)@(negedge clk);baseline_underruns=underruns;sim_epoch=cycles;
  fork
   begin : producer
    integer len,t,typ,fid,seq,jj;
    len=trace_next();
    while(len>0)begin
     t=trace_at();typ=trace_byte(0);
     seq=(trace_byte(1)<<24)|(trace_byte(2)<<16)|(trace_byte(3)<<8)|trace_byte(4);
     fid=(trace_byte(5)<<24)|(trace_byte(6)<<16)|(trace_byte(7)<<8)|trace_byte(8);
     if(seq!=producer_seq||fid<0||fid>2)$fatal(1,"input sequence/id");
     while(cycles<sim_epoch+t)@(negedge clk);
     if(cycles!=sim_epoch+t)$fatal(1,"late arrival scheduling");
     seen_events=seen_events+1;producer_seq=producer_seq+1;
     if(fid==discard_frame)begin
      $display("ARRIVE seq=%0d id=%0d type=%c cycle=%0d action=discard slots=%0d queue_bytes=%0d",seq,fid,typ,cycles,ring_count,ring_bytes);
     end else if(ring_count>=5 || ring_bytes+len>5195)begin
      if(discard_frame!=-1||fid!=0||typ!=8'h44)$fatal(1,"unsupported overflow scenario");
      discard_frame=fid;overflow_pending=1;
      $display("ARRIVE seq=%0d id=%0d type=%c cycle=%0d action=overflow slots=%0d queue_bytes=%0d",seq,fid,typ,cycles,ring_count,ring_bytes);
     end else begin
      for(jj=0;jj<len;jj=jj+1)begin
       x=trace_byte(jj);if(x<0||x>255)$fatal(1,"missing trace byte");ring_mem[ring_tail][jj]=x[7:0];
      end
      ring_sizes[ring_tail]=len;ring_tail=(ring_tail+1)%5;ring_count=ring_count+1;ring_bytes=ring_bytes+len;enqueued=enqueued+1;
      if(ring_bytes>ring_high)ring_high=ring_bytes;
      $display("ARRIVE seq=%0d id=%0d type=%c cycle=%0d action=enqueue slots=%0d queue_bytes=%0d",seq,fid,typ,cycles,ring_count,ring_bytes);
     end
     len=trace_next();
    end
    if(len<0||seen_events!=84)$fatal(1,"trace truncated/count");source_done=1;
   end
   begin : consumer
    integer m,typ,fid,seq,wait_count;
    while(!source_done||ring_count!=0||overflow_pending)begin
     @(posedge clk);#0.001;
     while(ring_count==0&&!source_done&&!overflow_pending)begin @(posedge clk);#0.001;end
     if(overflow_pending)begin
      if(active!=1||active_id!=0)$fatal(1,"overflow without active frame zero");
      for(idx=0;idx<ring_count;idx=idx+1)
       if({ring_mem[(ring_head+idx)%5][5],ring_mem[(ring_head+idx)%5][6],ring_mem[(ring_head+idx)%5][7],ring_mem[(ring_head+idx)%5][8]}!=0)$fatal(1,"overflow queue mixes frame IDs");
      write_reg('h24,2);active=0;abort_count=abort_count+1;drop_count=drop_count+1;overflow_pending=0;
      ring_count=0;ring_bytes=0;ring_head=ring_tail;$fclose(dump);
      repeat(50)@(negedge clk);
      if(core.receiving||core.decoding||core.pending||core.complete_frames!=published||core.decoded_frames!=published||core.presented_frames!=published||pixels!=base_pixels||model.writes!=base_writes||lost!=0||cdc_overflow)$fatal(1,"overflow abort state");
      $display("DROP id=0 reason=overflow cycle=%0d forwarded_bytes=%0d",cycles,received_bytes);
     end else if(ring_count!=0)begin
      current_len=ring_sizes[ring_head];typ=ring_mem[ring_head][0];seq=get32(1);fid=get32(5);
      case(typ)
       8'h42:begin
        if(active!=0||!core.ready_state)$fatal(1,"begin busy");
        n=get32(9);header_crc=get32(13);if(current_len!=17||n<1||n>262144)$fatal(1,"bad begin");
        active_id=fid;frame=fid;received_bytes=0;stream_crc=32'hffffffff;active=1;
        base_pixels=pixels;base_writes=model.writes;base_bursts=model.write_bursts;
        for(i=0;i<345600;i=i+1)seen[i]=0;
        dump_file=$sformatf("%s/frame-%0d-rgb565.txt",dump_dir,fid);dump=$fopen(dump_file,"w");if(!dump)$fatal(1,"dump open");
        write_reg('h14,fid);write_reg('h18,n);write_reg('h1c,{16'd720,16'd480});write_reg('h20,header_crc);write_reg('h24,1);
        $display("BEGIN seq=%0d id=%0d cycle=%0d",seq,fid,cycles);
       end
       8'h44:begin
        payload_offset=get32(9);payload_len=(ring_mem[ring_head][13]<<8)|ring_mem[ring_head][14];
        if(active!=1||fid!=active_id||payload_len<1||payload_len>1024||current_len!=15+payload_len||payload_offset!=received_bytes||received_bytes+payload_len>n)$fatal(1,"bad payload");
       $display("SERVICE seq=%0d id=%0d offset=%0d cycle=%0d",seq,fid,payload_offset,cycles);
        if(!stall_once && stall_cycles>0 && fid==0 && payload_offset==1024)begin stall_once=1;repeat(stall_cycles)@(negedge clk);end
        if(!overflow_pending)begin
         for(i=0;i<payload_len;i=i+chunk)begin
          read_reg('h00c,readback);if(readback!==n-received_bytes-i)$fatal(1,"remaining mismatch");
          read_reg('h054,readback);credit=readback;credit_reads=credit_reads+1;if(credit>63)$fatal(1,"FIFO credit");
          chunk=(payload_len-i<credit)?payload_len-i:credit;
          if(chunk!=0)begin
           header(8'h40,32'he0000100,12.5);
           for(j=0;j<chunk;j=j+1)begin bridge_data=ring_mem[ring_head][15+i+j];shift(bridge_data,8,4,12.5);stream_crc=core.crc_byte(stream_crc,bridge_data[7:0]);end
           end_transaction();
          end
         end
         received_bytes=received_bytes+payload_len;
         $display("FORWARD seq=%0d id=%0d offset=%0d bytes=%0d cycle=%0d",seq,fid,payload_offset,payload_len,cycles);
        end
       end
       8'h41:begin
        if(active!=1||fid!=active_id||received_bytes<=0||received_bytes>=n)$fatal(1,"bad abort");
        write_reg('h24,2);active=0;abort_count=abort_count+1;drop_count=drop_count+1;
        repeat(2)begin do @(negedge clk); while(!frame_boundary);end
        if(core.receiving||core.decoding||core.pending||core.complete_frames!=published||core.decoded_frames!=published||core.presented_frames!=published||pixels!=base_pixels||model.writes!=base_writes||lost!=0||cdc_overflow)$fatal(1,"abort state");
        if(published>0)begin
         if(!fvalid||front!=saved_front)$fatal(1,"prior front not selected");
         base=front ? 24'h080000:0;for(i=0;i<345600;i=i+1)if(model.mem[base+((i/480)+40)*480+(i%480)]!==saved_front_data[i])$fatal(1,"prior front corrupted");
        end
        $fclose(dump);$display("DROP id=%0d reason=guest_abort cycle=%0d prior_front=%0d",fid,cycles,published>0);
       end
       8'h43:begin
        if(active!=1||fid!=active_id||received_bytes!=n||~stream_crc!=header_crc)$fatal(1,"bad commit");
        read_reg('h028,readback);if(readback!==n)$fatal(1,"received count");write_reg('h24,4);active=0;
        while(core.presented_frames<published+1&&core.faults==0&&!tile_fault&&!protocol_fault)@(negedge clk);
        if(!fvalid||core.last_presented!=fid||core.presented_frames!=published+1||core.faults!=0||tile_fault||protocol_fault)$fatal(1,"publication");
        if(pixels-base_pixels!=345600||model.writes-base_writes!=345600||model.write_bursts-base_bursts!=43200)$fatal(1,"pixel count");
        base=front ? 24'h080000:0;
        for(i=0;i<345600;i=i+1)begin
         readback_i=base+((i/480)+40)*480+(i%480);
         if(!seen[i]||model.mem[readback_i]!==expected[i])$fatal(1,"new framebuffer");
         if(published>0 && model.mem[(saved_front?24'h080000:0)+((i/480)+40)*480+(i%480)]!==saved_front_data[i])$fatal(1,"prior framebuffer");
        end
        saved_front=front;for(i=0;i<345600;i=i+1)saved_front_data[i]=model.mem[base+((i/480)+40)*480+(i%480)];
        $fclose(dump);published=published+1;
        $display("PRESENT id=%0d seq=%0d cycle=%0d pixels=345600",fid,seq,cycles);
       end
       default:$fatal(1,"unsupported event");
      endcase
      // An overflowing in-service DATA is discarded at the next loop before freeing the ring.
      if(!overflow_pending)begin ring_bytes=ring_bytes-current_len;ring_head=(ring_head+1)%5;ring_count=ring_count-1;end
     end
    end
   end
  join
  if(active!=0||ring_count!=0||ring_bytes!=0||seen_events!=84||core.presented_frames!=published||core.drops!=abort_count||underruns!=baseline_underruns)$fatal(1,"final accounting");
  if((stall_cycles==0 && (published!=2||drop_count!=1||discard_frame!=-1)) || (stall_cycles>0 && (published!=1||drop_count!=2||discard_frame!=0)))$fatal(1,"scenario accounting");
  $display("SCHEDULE_RESULT stall=%0d events=%0d enqueued=%0d queue_high=%0d published=%0d dropped=%0d disc_frame=%0d epoch=%0d finish=%0d",stall_cycles,seen_events,enqueued,ring_high,published,drop_count,discard_frame,sim_epoch,cycles);
  $display("TEST_PASS_SCHEDULED_GUEST");$finish;
 end
 initial begin #1000000000;$fatal(1,"scheduled replay watchdog");end
endmodule
