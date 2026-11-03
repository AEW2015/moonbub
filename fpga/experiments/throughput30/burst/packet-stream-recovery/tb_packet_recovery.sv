`timescale 1ns/1ps
// Integration test only: ten 720x480 real JPEGs -> decoder -> tile transpose -> BL8
// writer -> functional SDRAM, while LCD scans the other buffer.
module tb_packet_recovery;
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
 reg[7:0] jpeg0[0:262143],jpeg1[0:262143];
 reg[15:0] previous_front[0:345599];
 integer ev_id[0:127],ev_at[0:127],ev_off[0:127],ev_len[0:127],event_count=0;
 integer ring_id[0:4],discard_id=-1,frame_active=-1,n0,n1,frame_len,frame_bytes=0;
 integer preload_writes,preload_pixels,preload_front,aborts=0,recovery_commits=0,received_packets=0;
 integer drop_final=0,drop_start=-1,drop_count=1,frame0_events=0,no_sof=0,last_forward_cycle=0,abort_trigger_cycle=0;
 reg[31:0] crc0,crc1,receive_crc;
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
 task check_prior_front;
 integer check_index,check_base;
 begin
  if(!fvalid||front!=preload_front||core.presented_frames!=1||core.complete_frames!=1||core.decoded_frames!=1||pixels!=preload_pixels||model.writes!=preload_writes)$fatal(1,"front changed on abort");
  check_base=front ? 24'h080000:0;
  for(check_index=0;check_index<345600;check_index=check_index+1)
   if(model.mem[check_base+((check_index/480)+40)*480+(check_index%480)]!==previous_front[check_index])$fatal(1,"prior front changed on abort");
 end endtask
 task abort_partial(input integer timeout_reason);
 begin
  abort_trigger_cycle=cycles;discard_id=0;write_reg('h24,2);aborts=aborts+1;
  ring_count=0;ring_bytes=0;ring_head=ring_tail;frame_active=-1;
  check_prior_front();
  $display("FRAME_ABORT id=0 reason=%0d cycle=%0d trigger_cycle=%0d last_forward_cycle=%0d forwarded_bytes=%0d prior_front_intact=1",timeout_reason,cycles,abort_trigger_cycle,last_forward_cycle,frame_bytes);
 end endtask
 initial begin
  if(!$value$plusargs("DROP_FINAL=%d",drop_final))drop_final=0;
  if(drop_final!=0 && drop_final!=1)$fatal(1,"invalid loss mode");
  if(!$value$plusargs("DROP_START=%d",drop_start))drop_start=(drop_final ? 25:5);
  if(!$value$plusargs("DROP_COUNT=%d",drop_count))drop_count=1;
  if(!$value$plusargs("FIXTURE_DIR=%s",fixture_dir))$fatal(1,"need FIXTURE_DIR");
  if(!$value$plusargs("DUMP_DIR=%s",dump_dir))$fatal(1,"need DUMP_DIR");
  if(!$value$plusargs("TRACE_FILE=%s",trace_file))$fatal(1,"need TRACE_FILE");
  trace_fd=$fopen(trace_file,"r");if(!trace_fd)$fatal(1,"missing packet trace");
  trace_status=$fscanf(trace_fd,"%d\n",event_count);
  if(trace_status!=1||event_count<2||event_count>128)$fatal(1,"invalid count");
  for(trace_line=0;trace_line<event_count;trace_line=trace_line+1)begin
   trace_status=$fscanf(trace_fd,"%d %d %d %d\n",ev_id[trace_line],ev_at[trace_line],ev_off[trace_line],ev_len[trace_line]);
   if(trace_status!=4||ev_id[trace_line]<0||ev_id[trace_line]>1||ev_len[trace_line]<1||ev_len[trace_line]>1024)$fatal(1,"invalid packet row");
   if(ev_id[trace_line]==0)frame0_events=frame0_events+1;
   if(trace_line>0 && ev_at[trace_line]<ev_at[trace_line-1])$fatal(1,"arrival order");
  end
  if(drop_start<0||drop_count<1||drop_start+drop_count>frame0_events)$fatal(1,"invalid loss range");
  $fclose(trace_fd);
  jpeg_file=$sformatf("%s/0000.jpg",fixture_dir);fd=$fopen(jpeg_file,"rb");if(!fd)$fatal(1,"missing 0");n0=$fread(jpeg0,fd);$fclose(fd);
  jpeg_file=$sformatf("%s/0001.jpg",fixture_dir);fd=$fopen(jpeg_file,"rb");if(!fd)$fatal(1,"missing 1");n1=$fread(jpeg1,fd);$fclose(fd);
  jpeg_file=$sformatf("%s/0002.jpg",fixture_dir);fd=$fopen(jpeg_file,"rb");if(!fd)$fatal(1,"missing preload");n=$fread(jpeg,fd);$fclose(fd);
  if(n0<=0||n1<=0||n<=0)$fatal(1,"empty fixture");
  crc=32'hffffffff;for(i=0;i<n;i=i+1)crc=core.crc_byte(crc,jpeg[i]);crc=~crc;
  crc0=32'hffffffff;for(i=0;i<n0;i=i+1)crc0=core.crc_byte(crc0,jpeg0[i]);crc0=~crc0;
  crc1=32'hffffffff;for(i=0;i<n1;i=i+1)crc1=core.crc_byte(crc1,jpeg1[i]);crc1=~crc1;
  for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24'h080000+i]=0;end
  for(i=0;i<345600;i=i+1)seen[i]=0;
  dump_file=$sformatf("%s/preload-rgb565.txt",dump_dir);dump=$fopen(dump_file,"w");if(!dump)$fatal(1,"dump preload");
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);
  repeat(2000000)@(negedge clk);baseline_underruns=underruns;frame=2;
  // Prior front: whole-fixture preload, not claimed as network streaming.
  write_reg('h14,2);write_reg('h18,n);write_reg('h1c,{16'd720,16'd480});write_reg('h20,crc);write_reg('h24,1);
  for(i=0;i<n;i=i+chunk)begin
   read_reg('h00c,readback);if(readback!==n-i)$fatal(1,"preload remaining");
   read_reg('h054,readback);credit=readback;credit_reads=credit_reads+1;if(credit>63)$fatal(1,"preload credit");
   chunk=(n-i<credit)?n-i:credit;
   if(chunk!=0)begin header(8'h40,32'he0000100,12.5);for(j=0;j<chunk;j=j+1)shift(jpeg[i+j],8,4,12.5);end_transaction();end
  end
  read_reg('h028,readback);if(readback!==n)$fatal(1,"preload received");write_reg('h24,4);
  while(core.presented_frames<1&&core.faults==0&&!tile_fault&&!protocol_fault)@(negedge clk);
  if(!fvalid||core.last_presented!=2||core.presented_frames!=1||pixels!=345600||model.writes!=345600)$fatal(1,"preload not presented");
  preload_front=front;preload_writes=model.writes;preload_pixels=pixels;base=front ? 24'h080000:0;
  for(i=0;i<345600;i=i+1)begin previous_front[i]=model.mem[base+((i/480)+40)*480+(i%480)];seen[i]=0;end
  $fclose(dump);dump_file=$sformatf("%s/recovery-rgb565.txt",dump_dir);dump=$fopen(dump_file,"w");if(!dump)$fatal(1,"dump recovery");
  $display("PRELOAD_PRESENT id=2 cycle=%0d front=%0d writes=%0d",cycles,front,model.writes);
  // Simulated new session's zero epoch begins only after prior front exists.
  epoch=cycles;frame=0;
  fork
   begin : packet_producer
    integer k, omitted, ordinal;
    omitted=0;ordinal=0;
    for(k=0;k<event_count;k=k+1)begin
     while(cycles<epoch+ev_at[k])@(negedge clk);
     if(ev_id[k]==0 && ordinal>=drop_start && ordinal<drop_start+drop_count)begin
      omitted=omitted+1;$display("PACKET_EVENT id=0 offset=%0d bytes=%0d arrival_cycle=%0d action=omitted",ev_off[k],ev_len[k],cycles);
     end else if(ev_id[k]==discard_id)begin
      $display("PACKET_EVENT id=%0d offset=%0d bytes=%0d arrival_cycle=%0d action=discard_after_abort",ev_id[k],ev_off[k],ev_len[k],cycles);
     end else begin
      if(ring_count>=5||ring_bytes+ev_len[k]+40>5320)$fatal(1,"bounded queue overflow event=%0d",k);
      ring_id[ring_tail]=ev_id[k];ring_offset[ring_tail]=ev_off[k];ring_len[ring_tail]=ev_len[k];ring_tail=(ring_tail+1)%5;
      ring_count=ring_count+1;ring_bytes=ring_bytes+ev_len[k]+40;if(ring_bytes>ring_high)ring_high=ring_bytes;
      $display("PACKET_EVENT id=%0d offset=%0d bytes=%0d arrival_cycle=%0d action=enqueue",ev_id[k],ev_off[k],ev_len[k],cycles);
     end
     if(ev_id[k]==0)ordinal=ordinal+1;
    end
    if(omitted!=drop_count)$fatal(1,"injected loss count");packet_done=1;
   end
   begin : packet_consumer
    integer fid,off,plen;
    while(!packet_done||ring_count!=0)begin
     @(posedge clk);#0.001;
     while(ring_count==0&&!packet_done)begin
      @(posedge clk);#0.001;
      // Hypothetical testbench inactivity timer, not the production receiver.
      if(frame_active==0 && last_forward_cycle!=0 && cycles-last_forward_cycle>=200000)abort_partial(1);
     end
     if(ring_count!=0)begin
      fid=ring_id[ring_head];off=ring_offset[ring_head];plen=ring_len[ring_head];
      if(frame_active<0)begin
       if(fid==0 && off!=0)begin
        if(drop_start!=0)$fatal(1,"unexpected missing SOF");
        discard_id=0;no_sof=1;ring_count=0;ring_bytes=0;ring_head=ring_tail;
        if(core.receiving || core.decoding || core.pending)$fatal(1,"unstarted frame is active");
        check_prior_front();
        $display("FRAME_NO_SOF id=0 cycle=%0d first_offset=%0d prior_front_intact=1",cycles,off);
        continue;
       end
       if(off!=0||!core.ready_state)$fatal(1,"SOF or busy fid=%0d off=%0d",fid,off);
       if(fid==1 && aborts+no_sof!=1)$fatal(1,"recovery before loss handling");
       frame_active=fid;frame=fid;frame_len=(fid==0)?n0:n1;frame_bytes=0;receive_crc=32'hffffffff;
       write_reg('h14,fid);write_reg('h18,frame_len);write_reg('h1c,{16'd720,16'd480});write_reg('h20,(fid==0)?crc0:crc1);write_reg('h24,1);
       $display("FRAME_BEGIN id=%0d cycle=%0d",fid,cycles);
      end
      if(fid!=frame_active)$fatal(1,"interleaved frame");
      if(off!=frame_bytes)begin
       if(fid!=0||off<=frame_bytes)$fatal(1,"unexpected offset gap");
       abort_partial(0);
      end else begin
       for(i=off;i<off+plen;i=i+chunk)begin
        read_reg('h00c,readback);if(readback!==frame_len-i)$fatal(1,"remaining fid=%0d i=%0d",fid,i);
        read_reg('h054,readback);credit=readback;credit_reads=credit_reads+1;if(credit>63)$fatal(1,"credit");
        chunk=(off+plen-i<credit)?off+plen-i:credit;
        if(chunk!=0)begin
         header(8'h40,32'he0000100,12.5);
         for(j=0;j<chunk;j=j+1)begin tx_byte=(fid==0)?jpeg0[i+j]:jpeg1[i+j];shift(tx_byte,8,4,12.5);receive_crc=core.crc_byte(receive_crc,tx_byte[7:0]);end
         end_transaction();
        end
       end
       frame_bytes=frame_bytes+plen;received_packets=received_packets+1;last_forward_cycle=cycles;
       $display("PACKET_FORWARD id=%0d offset=%0d bytes=%0d cycle=%0d",fid,off,plen,cycles);
       ring_head=(ring_head+1)%5;ring_count=ring_count-1;ring_bytes=ring_bytes-plen-40;
       if(frame_bytes==frame_len)begin
        if(fid!=1||~receive_crc!=crc1)$fatal(1,"wrong frame/CRC commit");
        read_reg('h028,readback);if(readback!==frame_len)$fatal(1,"recovery received");
        write_reg('h24,4);recovery_commits=recovery_commits+1;frame_active=-1;
        $display("FRAME_COMMIT id=1 cycle=%0d bytes=%0d",cycles,frame_bytes);
       end
      end
     end
    end
   end
  join
  while(core.presented_frames<2&&core.faults==0&&!tile_fault&&!protocol_fault)@(negedge clk);
  if(!fvalid||core.last_presented!=1||core.presented_frames!=2||aborts+no_sof!=1||recovery_commits!=1||front==preload_front)$fatal(1,"recovery publication");
  if(pixels-preload_pixels!=345600||model.writes-preload_writes!=345600||underruns!=baseline_underruns||lost!=0||cdc_overflow)$fatal(1,"recovery pixel accounting");
  base=front ? 24'h080000:0;
  for(i=0;i<345600;i=i+1)begin
   if(!seen[i]||model.mem[base+((i/480)+40)*480+(i%480)]!==expected[i])$fatal(1,"recovery backbuffer mismatch");
   if(model.mem[(preload_front ? 24'h080000:0)+((i/480)+40)*480+(i%480)]!==previous_front[i])$fatal(1,"prior front changed during recovery");
  end
  $fclose(dump);
  $display("PACKET_RECOVERY_RESULT events=%0d forwarded_packets=%0d aborts=%0d no_sof=%0d commits=%0d presented=%0d prior_front_preserved=1 queue_high_bytes=%0d epoch=%0d finish_cycle=%0d",event_count,received_packets,aborts,no_sof,recovery_commits,core.presented_frames,ring_high,epoch,cycles);
  $display("TEST_PASS_PACKET_RECOVERY");$finish;
 end
 initial begin #600000000;$fatal(1,"recovery watchdog frame=%0d cycle=%0d",frame,cycles);end
endmodule
