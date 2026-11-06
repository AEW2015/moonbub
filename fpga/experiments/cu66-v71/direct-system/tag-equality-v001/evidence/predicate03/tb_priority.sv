`timescale 1ns/1ps
module tb_priority;
reg  clk=0;
reg  rst=0;
reg  abort_i=0;
reg  start_valid=0;
wire  start_ready;
reg [31:0] frame_id=0;
reg  key=0;
reg [127:0] expected_tag=0;
reg  plane_cfg_valid=0;
wire  plane_cfg_ready;
reg [1:0] plane_cfg_plane=0;
reg [2:0] plane_cfg_dispatch=0;
reg [15:0] plane_cfg_bytes=0;
reg [16:0] plane_cfg_blocks=0;
wire  rd_req_valid;
reg  rd_req_ready=0;
wire [1:0] rd_req_plane;
wire [15:0] rd_req_addr;
reg  rd_rsp_valid=0;
wire  rd_rsp_ready;
reg [7:0] rd_rsp_data=0;
wire  q_req_valid;
reg  q_req_ready=0;
wire [10:0] q_req_index;
reg  q_rsp_valid=0;
reg [1:0] q_rsp_code=0;
wire  ref_req_valid;
reg  ref_req_ready=0;
wire [31:0] ref_req_tile;
reg  ref_rsp_valid=0;
wire  ref_rsp_ready;
reg [31:0] ref_rsp_tile=0;
reg [511:0] ref_rsp_pixels=0;
wire  tile_valid;
reg  tile_ready=0;
reg  write_done=0;
reg  write_error=0;
wire [31:0] tile_frame_id;
wire [1:0] tile_plane;
wire [16:0] tile_index;
wire [511:0] tile_pixels;
wire  tile_last;
wire  tag_valid;
reg  tag_ready=0;
wire [255:0] digest;
wire  busy;
wire  error;
wire  aborted;
wire [7:0] error_code;
wire [31:0] accepted_tiles;
wire [31:0] cycle_count;
wire  old_start_ready;
wire  old_plane_cfg_ready;
wire  old_rd_req_valid;
wire [1:0] old_rd_req_plane;
wire [15:0] old_rd_req_addr;
wire  old_rd_rsp_ready;
wire  old_q_req_valid;
wire [10:0] old_q_req_index;
wire  old_ref_req_valid;
wire [31:0] old_ref_req_tile;
wire  old_ref_rsp_ready;
wire  old_tile_valid;
wire [31:0] old_tile_frame_id;
wire [1:0] old_tile_plane;
wire [16:0] old_tile_index;
wire [511:0] old_tile_pixels;
wire  old_tile_last;
wire  old_tag_valid;
wire [255:0] old_digest;
wire  old_busy;
wire  old_error;
wire  old_aborted;
wire [7:0] old_error_code;
wire [31:0] old_accepted_tiles;
wire [31:0] old_cycle_count;

always #5 clk=~clk;
cu71_base_pipeline_math dut(.clk(clk),.rst(rst),.abort_i(abort_i),.start_valid(start_valid),.start_ready(start_ready),.frame_id(frame_id),.key(key),.expected_tag(expected_tag),.plane_cfg_valid(plane_cfg_valid),.plane_cfg_ready(plane_cfg_ready),.plane_cfg_plane(plane_cfg_plane),.plane_cfg_dispatch(plane_cfg_dispatch),.plane_cfg_bytes(plane_cfg_bytes),.plane_cfg_blocks(plane_cfg_blocks),.rd_req_valid(rd_req_valid),.rd_req_ready(rd_req_ready),.rd_req_plane(rd_req_plane),.rd_req_addr(rd_req_addr),.rd_rsp_valid(rd_rsp_valid),.rd_rsp_ready(rd_rsp_ready),.rd_rsp_data(rd_rsp_data),.q_req_valid(q_req_valid),.q_req_ready(q_req_ready),.q_req_index(q_req_index),.q_rsp_valid(q_rsp_valid),.q_rsp_code(q_rsp_code),.ref_req_valid(ref_req_valid),.ref_req_ready(ref_req_ready),.ref_req_tile(ref_req_tile),.ref_rsp_valid(ref_rsp_valid),.ref_rsp_ready(ref_rsp_ready),.ref_rsp_tile(ref_rsp_tile),.ref_rsp_pixels(ref_rsp_pixels),.tile_valid(tile_valid),.tile_ready(tile_ready),.write_done(write_done),.write_error(write_error),.tile_frame_id(tile_frame_id),.tile_plane(tile_plane),.tile_index(tile_index),.tile_pixels(tile_pixels),.tile_last(tile_last),.tag_valid(tag_valid),.tag_ready(tag_ready),.digest(digest),.busy(busy),.error(error),.aborted(aborted),.error_code(error_code),.accepted_tiles(accepted_tiles),.cycle_count(cycle_count));
cu71_base_pipeline_reference reference(.clk(clk),.rst(rst),.abort_i(abort_i),.start_valid(start_valid),.start_ready(old_start_ready),.frame_id(frame_id),.key(key),.expected_tag(expected_tag),.plane_cfg_valid(plane_cfg_valid),.plane_cfg_ready(old_plane_cfg_ready),.plane_cfg_plane(plane_cfg_plane),.plane_cfg_dispatch(plane_cfg_dispatch),.plane_cfg_bytes(plane_cfg_bytes),.plane_cfg_blocks(plane_cfg_blocks),.rd_req_valid(old_rd_req_valid),.rd_req_ready(rd_req_ready),.rd_req_plane(old_rd_req_plane),.rd_req_addr(old_rd_req_addr),.rd_rsp_valid(rd_rsp_valid),.rd_rsp_ready(old_rd_rsp_ready),.rd_rsp_data(rd_rsp_data),.q_req_valid(old_q_req_valid),.q_req_ready(q_req_ready),.q_req_index(old_q_req_index),.q_rsp_valid(q_rsp_valid),.q_rsp_code(q_rsp_code),.ref_req_valid(old_ref_req_valid),.ref_req_ready(ref_req_ready),.ref_req_tile(old_ref_req_tile),.ref_rsp_valid(ref_rsp_valid),.ref_rsp_ready(old_ref_rsp_ready),.ref_rsp_tile(ref_rsp_tile),.ref_rsp_pixels(ref_rsp_pixels),.tile_valid(old_tile_valid),.tile_ready(tile_ready),.write_done(write_done),.write_error(write_error),.tile_frame_id(old_tile_frame_id),.tile_plane(old_tile_plane),.tile_index(old_tile_index),.tile_pixels(old_tile_pixels),.tile_last(old_tile_last),.tag_valid(old_tag_valid),.tag_ready(tag_ready),.digest(old_digest),.busy(old_busy),.error(old_error),.aborted(old_aborted),.error_code(old_error_code),.accepted_tiles(old_accepted_tiles),.cycle_count(old_cycle_count));
reg[255:0]H=0;reg[127:0]T=0;reg[7:0]flags=0;integer checks=0,n,which;
task bind_state;begin
force dut.fs=4'd4;force dut.hash_value=H;force dut.wanted_tag=T;force dut.rows_result_valid=1;force dut.write_pending=flags[0];
force dut.s_error=flags[1];
force dut.dq_valid=flags[2];
force dut.dq_error=flags[2];
force dut.idct_valid=flags[3];
force dut.idct_error=flags[3];
force dut.recon_valid=flags[4];
force dut.recon_error=flags[4];
force dut.rows_error=flags[5];
force dut.e_error=0;force dut.s_code=8'h03;force dut.rows_code=8'h04;force dut.recon_id=0;force dut.tid=0;
force reference.fs=4'd4;force reference.hash_value=H;force reference.wanted_tag=T;force reference.rows_result_valid=1;force reference.write_pending=flags[0];
force reference.s_error=flags[1];
force reference.dq_valid=flags[2];
force reference.dq_error=flags[2];
force reference.idct_valid=flags[3];
force reference.idct_error=flags[3];
force reference.recon_valid=flags[4];
force reference.recon_error=flags[4];
force reference.rows_error=flags[5];
force reference.e_error=0;force reference.s_code=8'h03;force reference.rows_code=8'h04;force reference.recon_id=0;force reference.tid=0;
end endtask
task compare;begin bind_state();#1;if(dut.fail_now!==reference.fail_now||dut.fail_code!==reference.fail_code||tag_valid!==old_tag_valid)$fatal(1,"actual base failpriority mismatch");checks++;end endtask
initial begin
 rst=1;repeat(3)begin @(posedge clk);#1;end @(negedge clk);rst=0;
 // Actual fail_now and error publication from the complete elaborated bases.
 for(n=0;n<64;n++)begin
  flags=n;H=0;T=1;write_done=flags[0];write_error=flags[0];compare();
  if(dut.fail_code!== (flags[0]?8'h61:flags[1]?8'h23:flags[2]?8'h31:flags[3]?8'h32:flags[4]?8'h33:flags[5]?8'h44:8'h50))$fatal(1,"documented priority changed");
 end
 flags=0;write_done=0;write_error=0;
 for(which=0;which<128;which++)begin H=0;T=0;H[128+which]=1'bx;compare();T[(which+32)%128]=1;compare();end
 flags=0;H=0;T=0;compare();if(dut.fail_now!==0)$fatal(1,"equal tag failed");
 T=1;abort_i=1;compare();@(posedge clk);#1;if(!error||error_code!==8'h50||error!==old_error||error_code!==old_error_code)$fatal(1,"abort plus tag priority");
 $display("TAG_EQ_ACTUAL_BASE_PRIORITY_PASS checks=%0d",checks);$finish;
end
initial begin #100000;$fatal(1,"watchdog");end
endmodule
