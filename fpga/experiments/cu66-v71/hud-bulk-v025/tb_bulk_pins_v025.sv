`timescale 1ns/1ps
module tb_bulk_pins_v025 #(parameter realtime PHASE=0.0,parameter realtime HALF=31.25);
reg spi_clk=0,core_clk=0,reset=1;always #2.5 spi_clk=~spi_clk;initial begin #(PHASE);forever #5 core_clk=~core_clk;end
reg sck=0,cs=1;reg[3:0]host_dq=0;wire[3:0]dq,oe;wire spi_write,spi_read,new_write,new_overflow;wire[11:0]spi_address,new_address,new_read_address;wire[31:0]spi_wdata,spi_rdata,new_wdata;
moonshine_qspi_endpoint endpoint(.clk200(spi_clk),.rst_n(!reset),.qspi_sck(sck),.qspi_cs_n(cs),.qspi_dq_i(host_dq),.dq_o(dq),.dq_oe(oe),.buttons_native(12'd0),.vblank(1'b0),.core_write(spi_write),.core_read(spi_read),.core_address(spi_address),.core_wdata(spi_wdata),.core_rdata(spi_rdata));
cu71_bus_cdc_bulk_v025 bridge(.spi_clk,.spi_reset(reset),.spi_write,.spi_read,.spi_address,.spi_wdata,.spi_rdata,.overflow(new_overflow),.overflow_gray(),.core_clk,.core_reset(reset),.core_write(new_write),.core_address(new_address),.core_read_address(new_read_address),.core_wdata(new_wdata),.core_rdata(new_bus_rdata));
wire [31:0] old_bus_rdata,new_bus_rdata;
reg  in_transport_fault=0;
wire  old_start_valid,new_start_valid;
reg  in_start_ready=0;
wire [63:0] old_start_generation,new_start_generation;
wire [31:0] old_start_packet_bytes,new_start_packet_bytes;
wire  old_abort_i,new_abort_i;
wire  old_clear_fault,new_clear_fault;
reg  in_busy=0;
reg  in_done=0;
reg  in_error=0;
reg [7:0] in_stage=0;
reg [7:0] in_error_code=0;
reg  in_memory_tile_busy=0;
reg  in_memory_aux_busy=0;
reg [31:0] in_accepted_count=0;
reg [31:0] in_presented_count=0;
reg [31:0] in_rejected_count=0;
reg [31:0] in_lcd_underruns=0;
reg  in_packet_req_valid=0;
wire  old_packet_req_ready,new_packet_req_ready;
reg [15:0] in_packet_req_address=0;
reg [63:0] in_packet_req_generation=0;
reg [31:0] in_packet_req_sequence=0;
wire  old_packet_rsp_valid,new_packet_rsp_valid;
reg  in_packet_rsp_ready=0;
wire [15:0] old_packet_rsp_address,new_packet_rsp_address;
wire [63:0] old_packet_rsp_generation,new_packet_rsp_generation;
wire [31:0] old_packet_rsp_sequence,new_packet_rsp_sequence;
wire [7:0] old_packet_rsp_data,new_packet_rsp_data;
reg  in_hud_prepare_valid=0;
wire  old_hud_prepare_ready,new_hud_prepare_ready;
reg [63:0] in_active_generation=0;
reg [31:0] in_active_frame_id=0;
reg [31:0] in_active_reference_id=0;
reg  in_active_key=0;
reg [15:0] in_hud_address=0;
reg [15:0] in_hud_bytes=0;
reg [127:0] in_expected_hud_tag=0;
reg [1:0] in_candidate_bank=0;
wire  old_hud_result_valid,new_hud_result_valid;
reg  in_hud_result_ready=0;
wire [63:0] old_hud_result_generation,new_hud_result_generation;
wire [31:0] old_hud_result_frame_id,new_hud_result_frame_id;
wire [31:0] old_hud_result_reference_id,new_hud_result_reference_id;
wire [127:0] old_hud_result_tag,new_hud_result_tag;
wire [15:0] old_hud_result_words,new_hud_result_words;
wire  old_hud_result_success,new_hud_result_success;
wire  old_hud_drain_valid,new_hud_drain_valid;
reg  in_hud_drain_ready=0;
wire [63:0] old_hud_drain_generation,new_hud_drain_generation;
wire [31:0] old_hud_drain_frame_id,new_hud_drain_frame_id;
wire [1:0] old_hud_drain_bank,new_hud_drain_bank;
wire [127:0] old_hud_drain_tag,new_hud_drain_tag;
wire [15:0] old_hud_drain_words,new_hud_drain_words;
wire  old_hud_drain_success,new_hud_drain_success;
reg  in_software_command_valid=0;
wire  old_software_command_ready,new_software_command_ready;
reg [2:0] in_software_command_opcode=0;
wire  old_software_ack_valid,new_software_ack_valid;
reg  in_software_ack_ready=0;
wire [2:0] old_software_ack_opcode,new_software_ack_opcode;
wire [63:0] old_software_ack_generation,new_software_ack_generation;
wire [31:0] old_software_ack_frame_id,new_software_ack_frame_id;
wire  old_software_ack_success,new_software_ack_success;
wire  old_hud_aux_req_valid,new_hud_aux_req_valid;
reg  in_hud_aux_req_ready=0;
wire [63:0] old_hud_aux_generation,new_hud_aux_generation;
wire [31:0] old_hud_aux_frame_id,new_hud_aux_frame_id;
wire  old_hud_aux_req_write,new_hud_aux_req_write;
wire [23:0] old_hud_aux_req_addr,new_hud_aux_req_addr;
wire [15:0] old_hud_aux_req_data,new_hud_aux_req_data;
reg  in_hud_aux_rsp_valid=0;
wire  old_hud_aux_rsp_ready,new_hud_aux_rsp_ready;
reg [15:0] in_hud_aux_rsp_data=0;
reg  in_hud_aux_rsp_error=0;
wire [9:0] old_diag_address,new_diag_address;
reg [31:0] in_diag_data=0;
wire  old_quarantine,new_quarantine;
dy71_local_control_bulk_v025 new_csr(.clk(core_clk),.rst(reset),.bus_write(new_write),.bus_address(new_address),.bus_wdata(new_wdata),.bus_rdata(new_bus_rdata),.transport_fault(in_transport_fault),.start_valid(new_start_valid),.start_ready(in_start_ready),.start_generation(new_start_generation),.start_packet_bytes(new_start_packet_bytes),.abort_i(new_abort_i),.clear_fault(new_clear_fault),.busy(in_busy),.done(in_done),.error(in_error),.stage(in_stage),.error_code(in_error_code),.memory_tile_busy(in_memory_tile_busy),.memory_aux_busy(in_memory_aux_busy),.accepted_count(in_accepted_count),.presented_count(in_presented_count),.rejected_count(in_rejected_count),.lcd_underruns(in_lcd_underruns),.packet_req_valid(in_packet_req_valid),.packet_req_ready(new_packet_req_ready),.packet_req_address(in_packet_req_address),.packet_req_generation(in_packet_req_generation),.packet_req_sequence(in_packet_req_sequence),.packet_rsp_valid(new_packet_rsp_valid),.packet_rsp_ready(in_packet_rsp_ready),.packet_rsp_address(new_packet_rsp_address),.packet_rsp_generation(new_packet_rsp_generation),.packet_rsp_sequence(new_packet_rsp_sequence),.packet_rsp_data(new_packet_rsp_data),.hud_prepare_valid(in_hud_prepare_valid),.hud_prepare_ready(new_hud_prepare_ready),.active_generation(in_active_generation),.active_frame_id(in_active_frame_id),.active_reference_id(in_active_reference_id),.active_key(in_active_key),.hud_address(in_hud_address),.hud_bytes(in_hud_bytes),.expected_hud_tag(in_expected_hud_tag),.candidate_bank(in_candidate_bank),.hud_result_valid(new_hud_result_valid),.hud_result_ready(in_hud_result_ready),.hud_result_generation(new_hud_result_generation),.hud_result_frame_id(new_hud_result_frame_id),.hud_result_reference_id(new_hud_result_reference_id),.hud_result_tag(new_hud_result_tag),.hud_result_words(new_hud_result_words),.hud_result_success(new_hud_result_success),.hud_drain_valid(new_hud_drain_valid),.hud_drain_ready(in_hud_drain_ready),.hud_drain_generation(new_hud_drain_generation),.hud_drain_frame_id(new_hud_drain_frame_id),.hud_drain_bank(new_hud_drain_bank),.hud_drain_tag(new_hud_drain_tag),.hud_drain_words(new_hud_drain_words),.hud_drain_success(new_hud_drain_success),.software_command_valid(in_software_command_valid),.software_command_ready(new_software_command_ready),.software_command_opcode(in_software_command_opcode),.software_ack_valid(new_software_ack_valid),.software_ack_ready(in_software_ack_ready),.software_ack_opcode(new_software_ack_opcode),.software_ack_generation(new_software_ack_generation),.software_ack_frame_id(new_software_ack_frame_id),.software_ack_success(new_software_ack_success),.hud_aux_req_valid(new_hud_aux_req_valid),.hud_aux_req_ready(in_hud_aux_req_ready),.hud_aux_generation(new_hud_aux_generation),.hud_aux_frame_id(new_hud_aux_frame_id),.hud_aux_req_write(new_hud_aux_req_write),.hud_aux_req_addr(new_hud_aux_req_addr),.hud_aux_req_data(new_hud_aux_req_data),.hud_aux_rsp_valid(in_hud_aux_rsp_valid),.hud_aux_rsp_ready(new_hud_aux_rsp_ready),.hud_aux_rsp_data(in_hud_aux_rsp_data),.hud_aux_rsp_error(in_hud_aux_rsp_error),.diag_address(new_diag_address),.diag_data(in_diag_data),.quarantine(new_quarantine),.bus_read_address(new_read_address));

reg[15:0]memory[0:21119];reg pending=0;reg[23:0]saved_address;reg[15:0]saved_data;reg saved_write;integer delay_count=0,cycles=0,requests=0,responses=0,per_run=0,expected_offset=0;
always @(posedge core_clk)begin
 if(reset)begin pending<=0;in_hud_aux_req_ready<=0;in_hud_aux_rsp_valid<=0;cycles<=0;end
 else begin
 cycles<=cycles+1;in_hud_aux_req_ready<=!pending&&!in_hud_aux_rsp_valid&&(cycles%7!=0);
 if(new_hud_aux_req_valid&&in_hud_aux_req_ready)begin
  if(pending||in_hud_aux_rsp_valid)$fatal(1,"duplicate outstanding AUX");
  if(new_hud_aux_generation!==5||new_hud_aux_frame_id!==7||new_hud_aux_req_addr!==24'h500000+expected_offset+per_run)$fatal(1,"typed AUX context/offset%h",new_hud_aux_req_addr);
  pending<=1;saved_address<=new_hud_aux_req_addr;saved_data<=new_hud_aux_req_data;saved_write<=new_hud_aux_req_write;delay_count<=requests%13+1;requests<=requests+1;per_run<=per_run+1;in_hud_aux_req_ready<=0;
 end
 if(pending)begin if(delay_count>0)delay_count<=delay_count-1;else begin pending<=0;in_hud_aux_rsp_valid<=1;in_hud_aux_rsp_data<=memory[saved_address-24'h500000];if(saved_write)memory[saved_address-24'h500000]<=saved_data;end end
 if(in_hud_aux_rsp_valid&&new_hud_aux_rsp_ready)begin in_hud_aux_rsp_valid<=0;responses<=responses+1;end
 if(new_hud_drain_valid||new_software_ack_valid)$fatal(1,"bulk engine fabricated commit/drain");
 end
end
function automatic[15:0]pattern(input integer i);begin pattern=(i*173)^16'h5a3c;end endfunction
reg[31:0]values[0:127];integer seq=0;
task begin_transaction;begin sck=0;host_dq=0;cs=0;#100;end endtask
task end_transaction;begin sck=0;cs=1;#100;end endtask
task shift(input[31:0]value,input integer bits,input integer lanes);integer n;begin for(n=bits-lanes;n>=0;n=n-lanes)begin host_dq=(value>>n)&((1<<lanes)-1);#(HALF);sck=1;#(HALF);sck=0;end end endtask
task header(input[7:0]command,input[31:0]address);begin begin_transaction();shift(command,8,1);shift(address,32,4);end endtask
task read_burst(input[31:0]address,input integer count);integer w,n;begin header(8'h55,address);shift(0,32,4);shift(0,32,4);for(w=0;w<count;w=w+1)begin values[w]=0;for(n=0;n<8;n=n+1)begin #(HALF);sck=1;values[w]=(values[w]<<4)|dq;#(HALF);sck=0;end end end_transaction();end endtask
task command(input integer op,input integer off,input integer count,input integer mode);integer j,polls;begin
 if(op==23||op==17||op==18)begin per_run=0;expected_offset=off;end
 header(8'h54,32'he0000040);shift(5,32,4);shift(0,32,4);shift(7,32,4);shift(6,32,4);shift(off,32,4);shift(count,32,4);shift(mode,32,4);for(j=0;j<5;j=j+1)shift(0,32,4);end_transaction();
 seq=seq+1;header(8'h54,32'he0000020);shift(seq,32,4);shift(op,32,4);end_transaction();
 polls=0;read_burst(32'he0000028,3);while(values[0]!==seq)begin polls=polls+1;if(polls>100)$fatal(1,"mailbox timeout seq%0d",seq);read_burst(32'he0000028,3);end
 if(values[1]!==0)$fatal(1,"mailbox rejection seq%0d status%h",seq,values[1]);
 if(op==23&&values[2]!==count)$fatal(1,"bulk completion count");
end endtask
integer i,n,k,off;reg[31:0]v;
initial begin
 for(i=0;i<21120;i=i+1)memory[i]=16'hdead;
 #300;reset=0;#200;in_busy=1;in_active_generation=5;in_active_frame_id=7;in_active_reference_id=6;in_candidate_bank=1;in_hud_prepare_valid=1;repeat(3)@(negedge core_clk);in_hud_prepare_valid=0;
 read_burst(32'he0000000,3);if(values[0]!==32'h44593731||values[1]!==32'h00020000||values[2]!==31)$fatal(1,"strict ABI2 profile");
 read_burst(32'he0000600,2);if(values[0]!==32'h48425531||values[1]!==32'h10000)$fatal(1,"bulk signature");
 for(i=0;i<4;i=i+1)begin
  case(i)0:n=1;1:n=17;2:n=256;default:n=128;endcase off=i*512;
  command(22,off,n,0);
  header(8'h54,32'he0000400);for(k=0;k<(n+1)/2;k=k+1)begin v={pattern(off+k*2+1),pattern(off+k*2)};if(k*2+1==n)v[31:16]=0;shift(v,32,4);end end_transaction();
  command(23,off,n,0);read_burst(32'he0000610,1);if(values[0]!==n)$fatal(1,"actual completed writes");
  command(22,off,n,1);command(23,off,n,1);read_burst(32'he0000400,(n+1)/2);
  for(k=0;k<(n+1)/2;k=k+1)begin v={pattern(off+k*2+1),pattern(off+k*2)};if(k*2+1==n)v[31:16]=0;if(values[k]!==v)$fatal(1,"pin-level synchronous BRAM readback word%0d got%h wanted%h",k,values[k],v);end
 end
 command(17,42,32'habcd,0);command(18,42,0,0);if(values[2]!==32'habcd)$fatal(1,"legacy scalar AUX changed");
 if(new_overflow||requests!=806||responses!=806)$fatal(1,"counts or CDC overflow req%0d rsp%0d",requests,responses);
 $display("BULK_PINS_PASS selected_endpoint actual_new_CDC_control_bulk synthetic_owner_AUX requests806 responses806 words1_17_256_128 odd_pad legacy_RW phase%0f half%0f",PHASE,HALF);$finish;
end
initial begin #10000000;$fatal(1,"pin watchdog");end
endmodule
