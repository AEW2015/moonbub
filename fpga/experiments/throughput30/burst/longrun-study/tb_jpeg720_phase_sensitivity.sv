`timescale 1ns/1ps
// Integration test only: 60 distinct 720x480 synthetic JPEGs -> decoder -> tile transpose -> BL8
// writer -> functional SDRAM, while LCD scans the other buffer.
module tb_jpeg720_phase_sensitivity;
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
 string fixture_dir,dump_dir,jpeg_file,dump_file;
 integer fd,dump,n,i,x,y,pixels=0,readback_i,baseline_underruns,base;
 longint unsigned cycles=0,cycle_origin=0;
 integer frame,frame_start_pixels,frame_start_writes,frame_start_bursts;
 longint unsigned arrival,commit_cycle,target,service_start;
 longint unsigned first_present,last_present,epoch,max_latency=0,window_end;
 integer frame_count=10;integer strict_window=1;integer phase_cycles=0;
 integer q_frame=0,enqueued=0,q_highwater=0,q_overflows=0;longint unsigned q_arrival=0;reg q_valid=0;
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
 task write_reg(input[11:0]a0,input[31:0]d0);begin @(negedge clk);addr=a0;data=d0;wr=1;@(negedge clk);wr=0;end endtask
 initial begin
  if($value$plusargs("FRAMES=%d",frame_count))begin end
  if($value$plusargs("CYCLE_ORIGIN=%d",cycle_origin))begin end
  if($value$plusargs("STRICT_WINDOW=%d",strict_window))begin end
  if($value$plusargs("PHASE_CYCLES=%d",phase_cycles))begin end
  if(phase_cycles<0||phase_cycles>1536677)$fatal(1,"invalid phase");
  cycles=cycle_origin;
  if(frame_count<1 || frame_count>1800)$fatal(1,"FRAMES must be in range 1..1800");
  if(!$value$plusargs("FIXTURE_DIR=%s",fixture_dir))fixture_dir="fixtures";
  if(!$value$plusargs("DUMP_DIR=%s",dump_dir))dump_dir=".";
  for(i=0;i<384000;i=i+1)begin model.mem[i]=0;model.mem[24'h080000+i]=0;end
  repeat(8)@(negedge clk);reset=0;while(!mem_idle)@(negedge clk);
  repeat(2000000)@(negedge clk);baseline_underruns=underruns;
  repeat(phase_cycles)@(negedge clk);
  $display("PHASE_RESULT delay_cycles=%0d",phase_cycles);$fflush();
  // Exact rational 100MHz/30Hz schedule, with integer-cycle rounding.
  epoch=cycles;
  fork
   begin : producer
    integer f;longint unsigned next_cycle;
    for(f=0;f<frame_count;f=f+1)begin
     next_cycle=epoch+(64'(f)*64'd10000000)/64'd3;
     while(cycles<next_cycle)@(negedge clk);
     if(q_valid)begin q_overflows=q_overflows+1;$fatal(1,"external queue overflow frame=%0d",f);end
     q_frame=f;q_arrival=cycles;q_valid=1;enqueued=enqueued+1;q_highwater=1;
    end
   end
   begin : consumer
  for(frame=0;frame<frame_count;frame=frame+1)begin
   // Consumer samples after a posedge, producer changes queue on negedge.
   @(posedge clk);#0.001;
   while(!q_valid||!core.ready_state)begin @(posedge clk);#0.001;end
   if(q_frame!=frame)$fatal(1,"external queue order");
   arrival=q_arrival;service_start=cycles;q_valid=0;
   // Conceptual external queue stores one complete compressed JPEG; the
   // bench loads fixture bytes here without modeling receiver memory/RF.
   jpeg_file=$sformatf("%s/%04d.jpg",fixture_dir,frame);fd=$fopen(jpeg_file,"rb");
   if(!fd)$fatal(1,"missing fixture frame=%0d",frame);n=$fread(jpeg,fd);$fclose(fd);
   if(n<=0||n>262144)$fatal(1,"bad fixture length frame=%0d n=%0d",frame,n);
   crc=32'hffffffff;for(i=0;i<n;i=i+1)crc=core.crc_byte(crc,jpeg[i]);crc=~crc;
   base=front ? 0:24'h080000;
   for(i=0;i<345600;i=i+1)begin seen[i]=0;model.mem[base+((i/480)+40)*480+(i%480)]=16'hdead;end
   dump_file=$sformatf("%s/%04d-rgb565.txt",dump_dir,frame);dump=$fopen(dump_file,"w");if(!dump)$fatal(1,"dump open");
   frame_start_pixels=pixels;frame_start_writes=model.writes;frame_start_bursts=model.write_bursts;
   write_reg('h14,frame+1);write_reg('h18,n);write_reg('h1c,{16'd720,16'd480});write_reg('h20,crc);write_reg('h24,1);
   for(i=0;i<n;i=i+1)write_reg('h100,jpeg[i]);
   write_reg('h24,4);commit_cycle=cycles;
   while(core.presented_frames<frame+1&&core.faults==0&&!tile_fault&&!protocol_fault)@(negedge clk);
   if(core.faults!=0||tile_fault||protocol_fault)$fatal(1,"decode/staging fault frame=%0d core=%0d tile=%0d stage=%0d",frame,core.faults,tile_fault,protocol_fault);
   if(!fvalid||core.last_presented!=frame+1||core.presented_frames!=frame+1)$fatal(1,"publication frame %0d",frame);
   if(pixels-frame_start_pixels!=345600||model.writes-frame_start_writes!=345600||model.write_bursts-frame_start_bursts!=43200)
    $fatal(1,"frame %0d pixel conservation",frame);
   base=front ? 24'h080000:0;
   for(i=0;i<345600;i=i+1)begin
    readback_i=base+((i/480)+40)*480+(i%480);
    if(!seen[i]||model.mem[readback_i]!==expected[i])$fatal(1,"frame %0d mismatch i=%0d",frame,i);
   end
   if(underruns!=baseline_underruns)$fatal(1,"frame %0d LCD underrun",frame);
   if(core.drops!=0||core.overflows!=0)$fatal(1,"frame %0d drop/overflow",frame);
   if(cycles-arrival>max_latency)max_latency=cycles-arrival;
   if(frame==0)first_present=cycles;last_present=cycles;
   $fclose(dump);
   $display("FRAME_RESULT id=%0d arrival_cycle=%0d commit_cycle=%0d present_cycle=%0d queue_wait_cycles=%0d upload_cycles=%0d arrival_to_present_cycles=%0d writes=%0d bursts=%0d underruns=%0d",frame+1,arrival,commit_cycle,cycles,service_start-arrival,commit_cycle-service_start,cycles-arrival,model.writes-frame_start_writes,model.write_bursts-frame_start_bursts,underruns-baseline_underruns);$fflush();
  end
   end
  join
  if(enqueued!=frame_count||q_valid||q_overflows)$fatal(1,"queue final state");
  window_end=epoch+(64'(frame_count)*64'd10000000)/64'd3;
  if(strict_window && cycles>window_end)$fatal(1,"presentation deadline missed cycle=%0d window_end=%0d",cycles,window_end);
  while(strict_window && cycles<window_end)@(negedge clk);
  if(core.drops || core.overflows || underruns!=baseline_underruns)$fatal(1,"error after presentation window");
  $display("WINDOW_RESULT epoch=%0d end=%0d elapsed_cycles=%0d strict=%0d",epoch,cycles,cycles-epoch,strict_window);
  $display("TEST_PASS_JPEG720_PHASE_QUEUE1 frames=%0d queued=%0d queue_highwater=%0d queue_overflows=%0d presented=%0d",frame,enqueued,q_highwater,q_overflows,core.presented_frames);
  $display("TEST_PASS_JPEG720_PHASE frames=%0d distinct_presented=%0d pixels=%0d writes=%0d drops=%0d overflows=%0d underruns=%0d first_present_cycle=%0d last_present_cycle=%0d max_arrival_to_present_cycles=%0d",frame,core.presented_frames,pixels,model.writes,core.drops,core.overflows,underruns-baseline_underruns,first_present,last_present,max_latency);$finish;
 end
 initial begin #(64'd90000000000);$fatal(1,"multiframe watchdog frame=%0d cycle=%0d",frame,cycles);end
endmodule
