`timescale 1ns/1ps
module tb_bus_pair;
 parameter realtime PHASE=0.0;
 parameter integer DY=0;
 reg spi_clk=0,core_clk=0,core_run=1,reset=1;
 always #2.5 spi_clk=~spi_clk;
 initial begin #(PHASE);forever begin #5;if(core_run)core_clk=~core_clk;end end
 reg spi_write=0,spi_read=0;reg[11:0]spi_address=0;reg[31:0]spi_wdata=0;
 wire[31:0]old_spi_rdata,new_spi_rdata,old_gray,new_gray;wire old_overflow,new_overflow;
 wire old_write,new_write;wire[11:0]old_address,new_address,new_read_address;
 wire[31:0]old_wdata,new_wdata;
 moonshine_bus_cdc old_bridge(.spi_clk,.spi_reset(reset),.spi_write,.spi_read,.spi_address,.spi_wdata,
 .spi_rdata(old_spi_rdata),.overflow(old_overflow),.overflow_gray(old_gray),.core_clk,.core_reset(reset),
 .core_write(old_write),.core_address(old_address),.core_wdata(old_wdata),.core_rdata(old_bus_rdata));
 cu71_bus_cdc_split new_bridge(.spi_clk,.spi_reset(reset),.spi_write,.spi_read,.spi_address,.spi_wdata,
 .spi_rdata(new_spi_rdata),.overflow(new_overflow),.overflow_gray(new_gray),.core_clk,.core_reset(reset),
 .core_write(new_write),.core_address(new_address),.core_read_address(new_read_address),.core_wdata(new_wdata),.core_rdata(new_bus_rdata));
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
generate if(DY==0)begin:cu
cu71_local_control old_csr(.clk(core_clk),.rst(reset),.bus_write(old_write),.bus_address(old_address),.bus_wdata(old_wdata),.bus_rdata(old_bus_rdata),.transport_fault(in_transport_fault),.start_valid(old_start_valid),.start_ready(in_start_ready),.start_generation(old_start_generation),.start_packet_bytes(old_start_packet_bytes),.abort_i(old_abort_i),.clear_fault(old_clear_fault),.busy(in_busy),.done(in_done),.error(in_error),.stage(in_stage),.error_code(in_error_code),.memory_tile_busy(in_memory_tile_busy),.memory_aux_busy(in_memory_aux_busy),.accepted_count(in_accepted_count),.presented_count(in_presented_count),.rejected_count(in_rejected_count),.lcd_underruns(in_lcd_underruns),.packet_req_valid(in_packet_req_valid),.packet_req_ready(old_packet_req_ready),.packet_req_address(in_packet_req_address),.packet_req_generation(in_packet_req_generation),.packet_req_sequence(in_packet_req_sequence),.packet_rsp_valid(old_packet_rsp_valid),.packet_rsp_ready(in_packet_rsp_ready),.packet_rsp_address(old_packet_rsp_address),.packet_rsp_generation(old_packet_rsp_generation),.packet_rsp_sequence(old_packet_rsp_sequence),.packet_rsp_data(old_packet_rsp_data),.hud_prepare_valid(in_hud_prepare_valid),.hud_prepare_ready(old_hud_prepare_ready),.active_generation(in_active_generation),.active_frame_id(in_active_frame_id),.active_reference_id(in_active_reference_id),.active_key(in_active_key),.hud_address(in_hud_address),.hud_bytes(in_hud_bytes),.expected_hud_tag(in_expected_hud_tag),.candidate_bank(in_candidate_bank),.hud_result_valid(old_hud_result_valid),.hud_result_ready(in_hud_result_ready),.hud_result_generation(old_hud_result_generation),.hud_result_frame_id(old_hud_result_frame_id),.hud_result_reference_id(old_hud_result_reference_id),.hud_result_tag(old_hud_result_tag),.hud_result_words(old_hud_result_words),.hud_result_success(old_hud_result_success),.hud_drain_valid(old_hud_drain_valid),.hud_drain_ready(in_hud_drain_ready),.hud_drain_generation(old_hud_drain_generation),.hud_drain_frame_id(old_hud_drain_frame_id),.hud_drain_bank(old_hud_drain_bank),.hud_drain_tag(old_hud_drain_tag),.hud_drain_words(old_hud_drain_words),.hud_drain_success(old_hud_drain_success),.software_command_valid(in_software_command_valid),.software_command_ready(old_software_command_ready),.software_command_opcode(in_software_command_opcode),.software_ack_valid(old_software_ack_valid),.software_ack_ready(in_software_ack_ready),.software_ack_opcode(old_software_ack_opcode),.software_ack_generation(old_software_ack_generation),.software_ack_frame_id(old_software_ack_frame_id),.software_ack_success(old_software_ack_success),.hud_aux_req_valid(old_hud_aux_req_valid),.hud_aux_req_ready(in_hud_aux_req_ready),.hud_aux_generation(old_hud_aux_generation),.hud_aux_frame_id(old_hud_aux_frame_id),.hud_aux_req_write(old_hud_aux_req_write),.hud_aux_req_addr(old_hud_aux_req_addr),.hud_aux_req_data(old_hud_aux_req_data),.hud_aux_rsp_valid(in_hud_aux_rsp_valid),.hud_aux_rsp_ready(old_hud_aux_rsp_ready),.hud_aux_rsp_data(in_hud_aux_rsp_data),.hud_aux_rsp_error(in_hud_aux_rsp_error),.diag_address(old_diag_address),.diag_data(in_diag_data),.quarantine(old_quarantine));
cu71_local_control_safe new_csr(.clk(core_clk),.rst(reset),.bus_write(new_write),.bus_address(new_address),.bus_wdata(new_wdata),.bus_rdata(new_bus_rdata),.transport_fault(in_transport_fault),.start_valid(new_start_valid),.start_ready(in_start_ready),.start_generation(new_start_generation),.start_packet_bytes(new_start_packet_bytes),.abort_i(new_abort_i),.clear_fault(new_clear_fault),.busy(in_busy),.done(in_done),.error(in_error),.stage(in_stage),.error_code(in_error_code),.memory_tile_busy(in_memory_tile_busy),.memory_aux_busy(in_memory_aux_busy),.accepted_count(in_accepted_count),.presented_count(in_presented_count),.rejected_count(in_rejected_count),.lcd_underruns(in_lcd_underruns),.packet_req_valid(in_packet_req_valid),.packet_req_ready(new_packet_req_ready),.packet_req_address(in_packet_req_address),.packet_req_generation(in_packet_req_generation),.packet_req_sequence(in_packet_req_sequence),.packet_rsp_valid(new_packet_rsp_valid),.packet_rsp_ready(in_packet_rsp_ready),.packet_rsp_address(new_packet_rsp_address),.packet_rsp_generation(new_packet_rsp_generation),.packet_rsp_sequence(new_packet_rsp_sequence),.packet_rsp_data(new_packet_rsp_data),.hud_prepare_valid(in_hud_prepare_valid),.hud_prepare_ready(new_hud_prepare_ready),.active_generation(in_active_generation),.active_frame_id(in_active_frame_id),.active_reference_id(in_active_reference_id),.active_key(in_active_key),.hud_address(in_hud_address),.hud_bytes(in_hud_bytes),.expected_hud_tag(in_expected_hud_tag),.candidate_bank(in_candidate_bank),.hud_result_valid(new_hud_result_valid),.hud_result_ready(in_hud_result_ready),.hud_result_generation(new_hud_result_generation),.hud_result_frame_id(new_hud_result_frame_id),.hud_result_reference_id(new_hud_result_reference_id),.hud_result_tag(new_hud_result_tag),.hud_result_words(new_hud_result_words),.hud_result_success(new_hud_result_success),.hud_drain_valid(new_hud_drain_valid),.hud_drain_ready(in_hud_drain_ready),.hud_drain_generation(new_hud_drain_generation),.hud_drain_frame_id(new_hud_drain_frame_id),.hud_drain_bank(new_hud_drain_bank),.hud_drain_tag(new_hud_drain_tag),.hud_drain_words(new_hud_drain_words),.hud_drain_success(new_hud_drain_success),.software_command_valid(in_software_command_valid),.software_command_ready(new_software_command_ready),.software_command_opcode(in_software_command_opcode),.software_ack_valid(new_software_ack_valid),.software_ack_ready(in_software_ack_ready),.software_ack_opcode(new_software_ack_opcode),.software_ack_generation(new_software_ack_generation),.software_ack_frame_id(new_software_ack_frame_id),.software_ack_success(new_software_ack_success),.hud_aux_req_valid(new_hud_aux_req_valid),.hud_aux_req_ready(in_hud_aux_req_ready),.hud_aux_generation(new_hud_aux_generation),.hud_aux_frame_id(new_hud_aux_frame_id),.hud_aux_req_write(new_hud_aux_req_write),.hud_aux_req_addr(new_hud_aux_req_addr),.hud_aux_req_data(new_hud_aux_req_data),.hud_aux_rsp_valid(in_hud_aux_rsp_valid),.hud_aux_rsp_ready(new_hud_aux_rsp_ready),.hud_aux_rsp_data(in_hud_aux_rsp_data),.hud_aux_rsp_error(in_hud_aux_rsp_error),.diag_address(new_diag_address),.diag_data(in_diag_data),.quarantine(new_quarantine),.bus_read_address(new_read_address));
end else begin:dy
dy71_local_control old_csr(.clk(core_clk),.rst(reset),.bus_write(old_write),.bus_address(old_address),.bus_wdata(old_wdata),.bus_rdata(old_bus_rdata),.transport_fault(in_transport_fault),.start_valid(old_start_valid),.start_ready(in_start_ready),.start_generation(old_start_generation),.start_packet_bytes(old_start_packet_bytes),.abort_i(old_abort_i),.clear_fault(old_clear_fault),.busy(in_busy),.done(in_done),.error(in_error),.stage(in_stage),.error_code(in_error_code),.memory_tile_busy(in_memory_tile_busy),.memory_aux_busy(in_memory_aux_busy),.accepted_count(in_accepted_count),.presented_count(in_presented_count),.rejected_count(in_rejected_count),.lcd_underruns(in_lcd_underruns),.packet_req_valid(in_packet_req_valid),.packet_req_ready(old_packet_req_ready),.packet_req_address(in_packet_req_address),.packet_req_generation(in_packet_req_generation),.packet_req_sequence(in_packet_req_sequence),.packet_rsp_valid(old_packet_rsp_valid),.packet_rsp_ready(in_packet_rsp_ready),.packet_rsp_address(old_packet_rsp_address),.packet_rsp_generation(old_packet_rsp_generation),.packet_rsp_sequence(old_packet_rsp_sequence),.packet_rsp_data(old_packet_rsp_data),.hud_prepare_valid(in_hud_prepare_valid),.hud_prepare_ready(old_hud_prepare_ready),.active_generation(in_active_generation),.active_frame_id(in_active_frame_id),.active_reference_id(in_active_reference_id),.active_key(in_active_key),.hud_address(in_hud_address),.hud_bytes(in_hud_bytes),.expected_hud_tag(in_expected_hud_tag),.candidate_bank(in_candidate_bank),.hud_result_valid(old_hud_result_valid),.hud_result_ready(in_hud_result_ready),.hud_result_generation(old_hud_result_generation),.hud_result_frame_id(old_hud_result_frame_id),.hud_result_reference_id(old_hud_result_reference_id),.hud_result_tag(old_hud_result_tag),.hud_result_words(old_hud_result_words),.hud_result_success(old_hud_result_success),.hud_drain_valid(old_hud_drain_valid),.hud_drain_ready(in_hud_drain_ready),.hud_drain_generation(old_hud_drain_generation),.hud_drain_frame_id(old_hud_drain_frame_id),.hud_drain_bank(old_hud_drain_bank),.hud_drain_tag(old_hud_drain_tag),.hud_drain_words(old_hud_drain_words),.hud_drain_success(old_hud_drain_success),.software_command_valid(in_software_command_valid),.software_command_ready(old_software_command_ready),.software_command_opcode(in_software_command_opcode),.software_ack_valid(old_software_ack_valid),.software_ack_ready(in_software_ack_ready),.software_ack_opcode(old_software_ack_opcode),.software_ack_generation(old_software_ack_generation),.software_ack_frame_id(old_software_ack_frame_id),.software_ack_success(old_software_ack_success),.hud_aux_req_valid(old_hud_aux_req_valid),.hud_aux_req_ready(in_hud_aux_req_ready),.hud_aux_generation(old_hud_aux_generation),.hud_aux_frame_id(old_hud_aux_frame_id),.hud_aux_req_write(old_hud_aux_req_write),.hud_aux_req_addr(old_hud_aux_req_addr),.hud_aux_req_data(old_hud_aux_req_data),.hud_aux_rsp_valid(in_hud_aux_rsp_valid),.hud_aux_rsp_ready(old_hud_aux_rsp_ready),.hud_aux_rsp_data(in_hud_aux_rsp_data),.hud_aux_rsp_error(in_hud_aux_rsp_error),.diag_address(old_diag_address),.diag_data(in_diag_data),.quarantine(old_quarantine));
dy71_local_control_safe new_csr(.clk(core_clk),.rst(reset),.bus_write(new_write),.bus_address(new_address),.bus_wdata(new_wdata),.bus_rdata(new_bus_rdata),.transport_fault(in_transport_fault),.start_valid(new_start_valid),.start_ready(in_start_ready),.start_generation(new_start_generation),.start_packet_bytes(new_start_packet_bytes),.abort_i(new_abort_i),.clear_fault(new_clear_fault),.busy(in_busy),.done(in_done),.error(in_error),.stage(in_stage),.error_code(in_error_code),.memory_tile_busy(in_memory_tile_busy),.memory_aux_busy(in_memory_aux_busy),.accepted_count(in_accepted_count),.presented_count(in_presented_count),.rejected_count(in_rejected_count),.lcd_underruns(in_lcd_underruns),.packet_req_valid(in_packet_req_valid),.packet_req_ready(new_packet_req_ready),.packet_req_address(in_packet_req_address),.packet_req_generation(in_packet_req_generation),.packet_req_sequence(in_packet_req_sequence),.packet_rsp_valid(new_packet_rsp_valid),.packet_rsp_ready(in_packet_rsp_ready),.packet_rsp_address(new_packet_rsp_address),.packet_rsp_generation(new_packet_rsp_generation),.packet_rsp_sequence(new_packet_rsp_sequence),.packet_rsp_data(new_packet_rsp_data),.hud_prepare_valid(in_hud_prepare_valid),.hud_prepare_ready(new_hud_prepare_ready),.active_generation(in_active_generation),.active_frame_id(in_active_frame_id),.active_reference_id(in_active_reference_id),.active_key(in_active_key),.hud_address(in_hud_address),.hud_bytes(in_hud_bytes),.expected_hud_tag(in_expected_hud_tag),.candidate_bank(in_candidate_bank),.hud_result_valid(new_hud_result_valid),.hud_result_ready(in_hud_result_ready),.hud_result_generation(new_hud_result_generation),.hud_result_frame_id(new_hud_result_frame_id),.hud_result_reference_id(new_hud_result_reference_id),.hud_result_tag(new_hud_result_tag),.hud_result_words(new_hud_result_words),.hud_result_success(new_hud_result_success),.hud_drain_valid(new_hud_drain_valid),.hud_drain_ready(in_hud_drain_ready),.hud_drain_generation(new_hud_drain_generation),.hud_drain_frame_id(new_hud_drain_frame_id),.hud_drain_bank(new_hud_drain_bank),.hud_drain_tag(new_hud_drain_tag),.hud_drain_words(new_hud_drain_words),.hud_drain_success(new_hud_drain_success),.software_command_valid(in_software_command_valid),.software_command_ready(new_software_command_ready),.software_command_opcode(in_software_command_opcode),.software_ack_valid(new_software_ack_valid),.software_ack_ready(in_software_ack_ready),.software_ack_opcode(new_software_ack_opcode),.software_ack_generation(new_software_ack_generation),.software_ack_frame_id(new_software_ack_frame_id),.software_ack_success(new_software_ack_success),.hud_aux_req_valid(new_hud_aux_req_valid),.hud_aux_req_ready(in_hud_aux_req_ready),.hud_aux_generation(new_hud_aux_generation),.hud_aux_frame_id(new_hud_aux_frame_id),.hud_aux_req_write(new_hud_aux_req_write),.hud_aux_req_addr(new_hud_aux_req_addr),.hud_aux_req_data(new_hud_aux_req_data),.hud_aux_rsp_valid(in_hud_aux_rsp_valid),.hud_aux_rsp_ready(new_hud_aux_rsp_ready),.hud_aux_rsp_data(in_hud_aux_rsp_data),.hud_aux_rsp_error(in_hud_aux_rsp_error),.diag_address(new_diag_address),.diag_data(in_diag_data),.quarantine(new_quarantine),.bus_read_address(new_read_address));
end endgenerate
integer core_cycles=0,write_count=0,read_count=0,phase_checks=0;reg[31:0]rng=32'h71713579;
 always @(negedge core_clk)if(!reset)begin
 core_cycles=core_cycles+1;
 if(old_write!==new_write)$fatal(1,"write pulse mismatch");
 if(old_write && {old_address,old_wdata}!=={new_address,new_wdata})$fatal(1,"ordered write data/address mismatch");
 if(old_write)write_count=write_count+1;
 if(old_bridge.read_state!==new_bridge.read_state||old_bridge.fetched!==new_bridge.fetched||old_bridge.rp!==new_bridge.rp||old_bridge.rgray!==new_bridge.rgray||old_bridge.wg1!==new_bridge.wg1||old_bridge.wg2!==new_bridge.wg2||old_bridge.read_sync!==new_bridge.read_sync||old_bridge.ack!==new_bridge.ack||old_bridge.read_seen!==new_bridge.read_seen)$fatal(1,"FSM/Gray mismatch");
 if(old_bridge.read_state!=0 && old_address!==new_read_address)$fatal(1,"held mailbox address mismatch");
 if(old_bridge.read_state==1 && old_bus_rdata!==new_bus_rdata)$fatal(1,"actual CSR snapshot read mismatch addr%h old%h new%h",old_address,old_bus_rdata,new_bus_rdata);
if(old_start_valid!==new_start_valid)$fatal(1,"actual CSR output mismatch start_valid");
if(old_start_generation!==new_start_generation)$fatal(1,"actual CSR output mismatch start_generation");
if(old_start_packet_bytes!==new_start_packet_bytes)$fatal(1,"actual CSR output mismatch start_packet_bytes");
if(old_abort_i!==new_abort_i)$fatal(1,"actual CSR output mismatch abort_i");
if(old_clear_fault!==new_clear_fault)$fatal(1,"actual CSR output mismatch clear_fault");
if(old_packet_req_ready!==new_packet_req_ready)$fatal(1,"actual CSR output mismatch packet_req_ready");
if(old_packet_rsp_valid!==new_packet_rsp_valid)$fatal(1,"actual CSR output mismatch packet_rsp_valid");
if(old_packet_rsp_address!==new_packet_rsp_address)$fatal(1,"actual CSR output mismatch packet_rsp_address");
if(old_packet_rsp_generation!==new_packet_rsp_generation)$fatal(1,"actual CSR output mismatch packet_rsp_generation");
if(old_packet_rsp_sequence!==new_packet_rsp_sequence)$fatal(1,"actual CSR output mismatch packet_rsp_sequence");
if(old_packet_rsp_data!==new_packet_rsp_data)$fatal(1,"actual CSR output mismatch packet_rsp_data");
if(old_hud_prepare_ready!==new_hud_prepare_ready)$fatal(1,"actual CSR output mismatch hud_prepare_ready");
if(old_hud_result_valid!==new_hud_result_valid)$fatal(1,"actual CSR output mismatch hud_result_valid");
if(old_hud_result_generation!==new_hud_result_generation)$fatal(1,"actual CSR output mismatch hud_result_generation");
if(old_hud_result_frame_id!==new_hud_result_frame_id)$fatal(1,"actual CSR output mismatch hud_result_frame_id");
if(old_hud_result_reference_id!==new_hud_result_reference_id)$fatal(1,"actual CSR output mismatch hud_result_reference_id");
if(old_hud_result_tag!==new_hud_result_tag)$fatal(1,"actual CSR output mismatch hud_result_tag");
if(old_hud_result_words!==new_hud_result_words)$fatal(1,"actual CSR output mismatch hud_result_words");
if(old_hud_result_success!==new_hud_result_success)$fatal(1,"actual CSR output mismatch hud_result_success");
if(old_hud_drain_valid!==new_hud_drain_valid)$fatal(1,"actual CSR output mismatch hud_drain_valid");
if(old_hud_drain_generation!==new_hud_drain_generation)$fatal(1,"actual CSR output mismatch hud_drain_generation");
if(old_hud_drain_frame_id!==new_hud_drain_frame_id)$fatal(1,"actual CSR output mismatch hud_drain_frame_id");
if(old_hud_drain_bank!==new_hud_drain_bank)$fatal(1,"actual CSR output mismatch hud_drain_bank");
if(old_hud_drain_tag!==new_hud_drain_tag)$fatal(1,"actual CSR output mismatch hud_drain_tag");
if(old_hud_drain_words!==new_hud_drain_words)$fatal(1,"actual CSR output mismatch hud_drain_words");
if(old_hud_drain_success!==new_hud_drain_success)$fatal(1,"actual CSR output mismatch hud_drain_success");
if(old_software_command_ready!==new_software_command_ready)$fatal(1,"actual CSR output mismatch software_command_ready");
if(old_software_ack_valid!==new_software_ack_valid)$fatal(1,"actual CSR output mismatch software_ack_valid");
if(old_software_ack_opcode!==new_software_ack_opcode)$fatal(1,"actual CSR output mismatch software_ack_opcode");
if(old_software_ack_generation!==new_software_ack_generation)$fatal(1,"actual CSR output mismatch software_ack_generation");
if(old_software_ack_frame_id!==new_software_ack_frame_id)$fatal(1,"actual CSR output mismatch software_ack_frame_id");
if(old_software_ack_success!==new_software_ack_success)$fatal(1,"actual CSR output mismatch software_ack_success");
if(old_hud_aux_req_valid!==new_hud_aux_req_valid)$fatal(1,"actual CSR output mismatch hud_aux_req_valid");
if(old_hud_aux_generation!==new_hud_aux_generation)$fatal(1,"actual CSR output mismatch hud_aux_generation");
if(old_hud_aux_frame_id!==new_hud_aux_frame_id)$fatal(1,"actual CSR output mismatch hud_aux_frame_id");
if(old_hud_aux_req_write!==new_hud_aux_req_write)$fatal(1,"actual CSR output mismatch hud_aux_req_write");
if(old_hud_aux_req_addr!==new_hud_aux_req_addr)$fatal(1,"actual CSR output mismatch hud_aux_req_addr");
if(old_hud_aux_req_data!==new_hud_aux_req_data)$fatal(1,"actual CSR output mismatch hud_aux_req_data");
if(old_hud_aux_rsp_ready!==new_hud_aux_rsp_ready)$fatal(1,"actual CSR output mismatch hud_aux_rsp_ready");
if(old_diag_address!==new_diag_address)$fatal(1,"actual CSR output mismatch diag_address");
if(old_quarantine!==new_quarantine)$fatal(1,"actual CSR output mismatch quarantine");
phase_checks=phase_checks+1;
 end
 always @(negedge spi_clk)if(!reset)begin
 if({old_spi_rdata,old_overflow,old_gray}!=={new_spi_rdata,new_overflow,new_gray})$fatal(1,"SPI result/overflow mismatch");
 if(old_bridge.wp!==new_bridge.wp||old_bridge.wgray!==new_bridge.wgray||old_bridge.rg1!==new_bridge.rg1||old_bridge.rg2!==new_bridge.rg2||old_bridge.ack_sync!==new_bridge.ack_sync)$fatal(1,"SPI Gray/pointer mismatch");
 end
 task put(input[11:0]address,input[31:0]value);begin
 @(negedge spi_clk);spi_address=address;spi_wdata=value;spi_write=1;
 @(negedge spi_clk);spi_write=0;end endtask
 task get(input[11:0]address);reg ack_before;integer timeout;begin
 @(negedge spi_clk);ack_before=old_bridge.ack;spi_address=address;spi_read=1;
 @(negedge spi_clk);spi_read=0;timeout=0;
 while(old_bridge.ack_sync[2]==ack_before)begin @(negedge spi_clk);timeout=timeout+1;if(timeout>10000)$fatal(1,"mailbox timeout");end
 repeat(3)@(negedge spi_clk);
 if(old_spi_rdata!==new_spi_rdata)$fatal(1,"mailbox data differs");read_count=read_count+1;
 end endtask
 task reset_both;begin
 @(negedge spi_clk);reset=1;spi_read=0;spi_write=0;core_run=1;repeat(12)@(negedge spi_clk);
 reset=0;repeat(12)@(negedge spi_clk);end endtask
 integer i,j;reg[31:0]gray_binary;
 initial begin
 in_start_ready=1;in_hud_result_ready=1;in_hud_drain_ready=1;in_software_ack_ready=1;in_hud_aux_req_ready=1;
 in_diag_data=32'hfedcba98;in_accepted_count=123;in_presented_count=122;in_rejected_count=4;in_lcd_underruns=7;
 reset_both();get(0);
 if(old_spi_rdata!==(DY?32'h44593731:32'h43553731))$fatal(1,"wrong profile");
 // Real typed CSR metadata and BEGIN/upload/SEAL/discard; no software or HUD ACK invented.
 put('h040,1);put('h044,0);put('h050,8);put('h054,32'h12345678);put('h020,1);put('h024,1);get('h02c);
 put('h100,32'h04030201);put('h100,32'h08070605);get('h104);get('h10c);
 put('h020,2);put('h024,2);get('h02c);put('h020,3);put('h024,4);get('h02c);
 // All byte addresses through actual read mux; queued writes precede snapshots.
 for(i=0;i<4096;i=i+1)begin
 if(i%29==0)begin put('h200,i);put('h040,i^32'h1234);end
 get(i[11:0]);end
 // Queue saturation while core is stopped, then ordered drain before mailbox read.
 @(negedge core_clk);core_run=0;
 for(i=0;i<140;i=i+1)put('h200,i);
 if(!old_overflow||old_gray==0)$fatal(1,"queue full not exercised");
 core_run=1;get('h204);
 // Held bundled address remains stable until response, even when later writes queue.
 for(j=0;j<100;j=j+1)begin
 put('h200,j);put('h040,j^32'habcdef00);get('h204);get('h040);
 end
 reset_both();get(0);if(old_overflow||old_gray!=0)$fatal(1,"reset did not clear overflow");
 // Reset with both pending read and queued writes; joint reset cancels both sides.
 put('h040,32'hffffffff);@(negedge spi_clk);spi_read=1;spi_address='h020;
 @(negedge spi_clk);spi_read=0;reset_both();get('h020);
 if(old_spi_rdata!=0)$fatal(1,"reset state not cleared");
 $display("ACTUAL_CSR_BRIDGE_PAIR_PASS profile=%0d phase=%0.3f reads=%0d writes=%0d comparisons=%0d fifo_full=1 ordered_drains=1 gray=1 reset=1 unchanged_capture_cycles=1",DY,PHASE,read_count,write_count,phase_checks);$finish;
 end
 initial begin #20000000;$fatal(1,"watchdog");end
endmodule
