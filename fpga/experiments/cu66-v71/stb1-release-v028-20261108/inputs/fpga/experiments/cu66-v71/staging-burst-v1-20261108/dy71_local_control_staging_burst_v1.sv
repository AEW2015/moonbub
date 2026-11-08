// Lab-only typed control link for real ESP32 HUD service and CU66 packet upload.
// No network capability is advertised. Accepted memory operations always drain.
`timescale 1ns/1ps
`default_nettype none
module dy71_local_control_bulk_v025(
 input wire clk,rst,bus_write,input wire [11:0] bus_address,input wire [11:0] bus_read_address,input wire [31:0] bus_wdata,
 output reg [31:0] bus_rdata,input wire transport_fault,
 output wire start_valid,input wire start_ready,output wire [63:0] start_generation,
 output wire [31:0] start_packet_bytes,output wire abort_i,clear_fault,
 input wire busy,done,error,input wire [7:0] stage,error_code,
 input wire memory_tile_busy,memory_aux_busy,
 input wire [31:0] accepted_count,presented_count,rejected_count,lcd_underruns,
 input wire packet_req_valid,output wire packet_req_ready,input wire [15:0] packet_req_address,
 input wire [63:0] packet_req_generation,input wire [31:0] packet_req_sequence,
 output wire packet_rsp_valid,input wire packet_rsp_ready,output wire [15:0] packet_rsp_address,
 output wire [63:0] packet_rsp_generation,output wire [31:0] packet_rsp_sequence,output wire [7:0] packet_rsp_data,
 input wire hud_prepare_valid,output wire hud_prepare_ready,
 input wire [63:0] active_generation,input wire [31:0] active_frame_id,active_reference_id,
 input wire active_key,input wire [15:0] hud_address,hud_bytes,input wire [127:0] expected_hud_tag,
 input wire [1:0] candidate_bank,
 output wire hud_result_valid,input wire hud_result_ready,
 output wire [63:0] hud_result_generation,output wire [31:0] hud_result_frame_id,hud_result_reference_id,
 output wire [127:0] hud_result_tag,output wire [15:0] hud_result_words,output wire hud_result_success,
 output wire hud_drain_valid,input wire hud_drain_ready,
 output wire [63:0] hud_drain_generation,output wire [31:0] hud_drain_frame_id,output wire [1:0] hud_drain_bank,
 output wire [127:0] hud_drain_tag,output wire [15:0] hud_drain_words,output wire hud_drain_success,
 input wire software_command_valid,output wire software_command_ready,input wire [2:0] software_command_opcode,
 output wire software_ack_valid,input wire software_ack_ready,output wire [2:0] software_ack_opcode,
 output wire [63:0] software_ack_generation,output wire [31:0] software_ack_frame_id,output wire software_ack_success,
 output wire hud_aux_req_valid,input wire hud_aux_req_ready,
 output wire [63:0] hud_aux_generation,output wire [31:0] hud_aux_frame_id,
 output wire hud_aux_req_write,output wire [23:0] hud_aux_req_addr,output wire [15:0] hud_aux_req_data,
 input wire hud_aux_rsp_valid,output wire hud_aux_rsp_ready,input wire [15:0] hud_aux_rsp_data,input wire hud_aux_rsp_error,
 output reg [9:0] diag_address,input wire [31:0] diag_data,
 output wire quarantine
);
 `include "cu70_memory_map.svh"
 localparam [4:0] IDLE=0,BEGIN_PACKET=1,SEAL_PACKET=2,START_FRAME=3,DISCARD_PACKET=4,
  ABORT_FRAME=5,CLEAR_FAULT=6,HUD_RESULT=7,AUX_ISSUE=8,AUX_DRAIN=9,HUD_DRAIN=10,
  SOFT_ACK=11,PACKET_ISSUE=12,PACKET_DRAIN=13,BULK_SETUP=14,BULK_RUN=15,BULK_WAIT=16;
 (* MAX_FANOUT = 64 *) reg [4:0] command_state=IDLE;
 reg [31:0] fields[0:11],command_fields[0:11];
 reg [32:0] command_word_end;
 reg [31:0] submitted_sequence=0,pending_sequence=0,ack_sequence=0,ack_status=0,ack_data=0,rejected_commands=0;
 reg [7:0] operation=0;reg [63:0] last_started_generation=0;
 reg frame_active=0,seen_busy=0;
 reg hud_pending=0,soft_pending=0;reg [31:0] hud_ticket=0,soft_ticket=0;
 reg [63:0] hud_gen=0,soft_gen=0;reg [31:0] hud_fid=0,hud_ref=0,soft_fid=0,soft_ref=0;
 reg [31:0] expected_packet_crc=0;
 reg [15:0] hud_offset=0,hud_length=0;reg [1:0] hud_bank=0;reg hud_key=0;
 reg [127:0] hud_tag=0;reg [2:0] soft_opcode=0;
 wire [63:0] cmd_gen={command_fields[1],command_fields[0]};
 wire [31:0] cmd_fid=command_fields[2],cmd_ref=command_fields[3];
 wire [127:0] cmd_tag={command_fields[8],command_fields[9],command_fields[10],command_fields[11]};
 wire hud_identity_match;
 cu71_balanced_identity_v019 #(.WIDTH(130))hud_match(
  .a({cmd_gen,cmd_fid,cmd_ref,candidate_bank}),.b({hud_gen,hud_fid,hud_ref,hud_bank}),.match(hud_identity_match));
 wire hud_identity=hud_pending&&busy&&hud_identity_match;
 wire command_idle=command_state==IDLE;
 wire staging_begin_ready,upload_ready,sealed_valid,staging_active;
 wire [63:0] staged_generation;wire [31:0] packet_bytes,written_bytes,actual_crc,staging_faults;
 wire staged_req_valid,staged_req_ready,staged_rsp_valid,staged_rsp_ready;
 wire [15:0] staged_req_address,staged_rsp_address;
 wire [63:0] staged_req_generation,staged_rsp_generation;
 wire [31:0] staged_req_sequence,staged_rsp_sequence;wire [7:0] staged_rsp_data;
 wire packet_bridge_busy,packet_identity_fault;
 reg [1:0] cpu_byte=0;reg [31:0] cpu_word=0;
 wire cpu_req_valid=command_state==PACKET_ISSUE&&can_packet;
 wire cpu_req_ready,cpu_rsp_valid;wire [15:0] cpu_rsp_address;wire [63:0] cpu_rsp_generation;
 wire [31:0] cpu_rsp_sequence;wire [7:0] cpu_rsp_data;
 wire [15:0] cpu_address=command_fields[4][15:0]+{14'd0,cpu_byte};
 wire release_packet=frame_active&&seen_busy&&!busy&&!memory_tile_busy&&!memory_aux_busy&&!packet_bridge_busy&&!staged_rsp_valid;
 assign quarantine=transport_fault||packet_identity_fault||burst_fault;
 wire can_begin=!burst_blocked&&staging_begin_ready&&cmd_gen!=0&&cmd_gen>last_started_generation&&command_fields[4]!=0&&command_fields[4]<=49152&&!quarantine;
 wire can_seal=!burst_blocked&&!burst_fault&&upload_ready&&written_bytes==packet_bytes&&actual_crc==expected_packet_crc&&command_fields[5]==expected_packet_crc&&cmd_gen==staged_generation;
 wire can_start=sealed_valid&&cmd_gen==staged_generation&&cmd_gen>last_started_generation&&!quarantine&&!frame_active;
 wire can_discard=!burst_blocked&&!upload_pulse&&!frame_active&&!staging_active&&(upload_ready||sealed_valid)&&cmd_gen==staged_generation;
 wire can_aux=hud_identity&&command_fields[4]<21120;
 wire can_soft=soft_pending&&cmd_gen==soft_gen&&cmd_fid==soft_fid&&cmd_ref==soft_ref&&command_fields[4][2:0]==soft_opcode;
 wire can_packet=staging_active&&cmd_gen==staged_generation&&command_word_end<={1'b0,packet_bytes};
 wire begin_packet=command_state==BEGIN_PACKET&&can_begin;
 wire activate_packet=start_valid&&start_ready;
 wire scalar_upload=bus_write&&bus_address==12'h100;
 wire burst_fault,burst_fence,burst_blocked,burst_selected;wire[31:0]burst_rdata,burst_prefix;
 wire[8:0]burst_queued;wire upload_pulse;wire[31:0]upload_word;wire[2:0]upload_count;
 cu71_staging_burst_v1 burst(.clk,.rst,.bus_write,.bus_address,.bus_read_address,.bus_wdata,.transport_fault,
  .begin_packet,.staged_generation,.packet_bytes,.written_bytes,.actual_crc,.scalar_valid(scalar_upload),.scalar_word(bus_wdata),.native_capacity(upload_bytes),
  .upload_valid(upload_pulse),.upload_word,.upload_count,.upload_ready,.fence_ready(burst_fence),.blocked(burst_blocked),.fault(burst_fault),
  .selected(burst_selected),.rdata(burst_rdata),.accepted_prefix(burst_prefix),.queued_words(burst_queued));
 wire [2:0] upload_bytes;
 cu71_packet_staging_safe staging(.clk,.rst,.begin_valid(begin_packet),.begin_ready(staging_begin_ready),
  .begin_generation(cmd_gen),.begin_bytes(command_fields[4]),.begin_crc(command_fields[5]),
  .upload_valid(upload_pulse),.upload_ready,.upload_word(upload_word),.upload_count(upload_count),.upload_capacity(upload_bytes),
  .seal_valid(command_state==SEAL_PACKET&&can_seal),.activate_valid(activate_packet),.release_valid(release_packet),
  .discard_valid(command_state==DISCARD_PACKET&&can_discard),.sealed_valid,.active(staging_active),.generation(staged_generation),
  .packet_bytes,.written_bytes,.actual_crc,.faults(staging_faults),
  .packet_req_valid(staged_req_valid),.packet_req_ready(staged_req_ready),.packet_req_address(staged_req_address),
  .packet_req_generation(staged_req_generation),.packet_req_sequence(staged_req_sequence),
  .packet_rsp_valid(staged_rsp_valid),.packet_rsp_ready(staged_rsp_ready),.packet_rsp_address(staged_rsp_address),
  .packet_rsp_generation(staged_rsp_generation),.packet_rsp_sequence(staged_rsp_sequence),.packet_rsp_data(staged_rsp_data));
 cu71_packet_arbiter_cut_v001 packet_arbiter(.clk,.rst,
  .p0_valid(packet_req_valid),.p0_ready(packet_req_ready),.p0_address(packet_req_address),.p0_generation(packet_req_generation),.p0_sequence(packet_req_sequence),
  .p0_rsp_valid(packet_rsp_valid),.p0_rsp_ready(packet_rsp_ready),.p0_rsp_address(packet_rsp_address),.p0_rsp_generation(packet_rsp_generation),.p0_rsp_sequence(packet_rsp_sequence),.p0_rsp_data(packet_rsp_data),
  .p1_valid(cpu_req_valid),.p1_ready(cpu_req_ready),.p1_address(cpu_address),.p1_generation(cmd_gen),.p1_sequence(pending_sequence),
  .p1_rsp_valid(cpu_rsp_valid),.p1_rsp_ready(command_state==PACKET_DRAIN),.p1_rsp_address(cpu_rsp_address),.p1_rsp_generation(cpu_rsp_generation),.p1_rsp_sequence(cpu_rsp_sequence),.p1_rsp_data(cpu_rsp_data),
  .req_valid(staged_req_valid),.req_ready(staged_req_ready),.req_address(staged_req_address),.req_generation(staged_req_generation),.req_sequence(staged_req_sequence),
  .rsp_valid(staged_rsp_valid),.rsp_ready(staged_rsp_ready),.rsp_address(staged_rsp_address),.rsp_generation(staged_rsp_generation),.rsp_sequence(staged_rsp_sequence),.rsp_data(staged_rsp_data),
  .busy(packet_bridge_busy),.identity_fault(packet_identity_fault));
 assign start_valid=command_state==START_FRAME&&can_start;
 assign start_generation=staged_generation;assign start_packet_bytes=packet_bytes;
 assign abort_i=command_state==ABORT_FRAME&&busy&&stage<9;
 assign clear_fault=command_state==CLEAR_FAULT;
 assign hud_prepare_ready=!hud_pending;
 assign hud_result_valid=command_state==HUD_RESULT&&hud_identity;
 assign hud_result_generation=cmd_gen;assign hud_result_frame_id=cmd_fid;assign hud_result_reference_id=cmd_ref;
 assign hud_result_tag=cmd_tag;assign hud_result_words=command_fields[5][15:0];assign hud_result_success=command_fields[4][0];
 assign hud_drain_valid=command_state==HUD_DRAIN&&hud_identity;
 assign hud_drain_generation=cmd_gen;assign hud_drain_frame_id=cmd_fid;assign hud_drain_bank=command_fields[6][1:0];
 assign hud_drain_tag=cmd_tag;assign hud_drain_words=command_fields[5][15:0];assign hud_drain_success=command_fields[4][0];
 assign software_command_ready=!soft_pending;
 assign software_ack_valid=command_state==SOFT_ACK&&can_soft;
 assign software_ack_generation=cmd_gen;assign software_ack_frame_id=cmd_fid;
 assign software_ack_opcode=command_fields[4][2:0];assign software_ack_success=command_fields[5][0];
 assign hud_aux_req_valid=bulk_route?bulk_req_valid:(command_state==AUX_ISSUE&&can_aux);
 assign hud_aux_generation=bulk_route?bulk_req_generation:cmd_gen;assign hud_aux_frame_id=bulk_route?bulk_req_frame:cmd_fid;assign hud_aux_req_write=bulk_route?bulk_req_write:(operation==17);
 assign hud_aux_req_addr=bulk_route?bulk_req_address:((hud_bank==0?HUD0_BASE:hud_bank==1?HUD1_BASE:HUD2_BASE)+command_fields[4][23:0]);
 assign hud_aux_req_data=bulk_route?bulk_req_data:command_fields[5][15:0];assign hud_aux_rsp_ready=bulk_route?bulk_rsp_ready:(command_state==AUX_DRAIN);
 task automatic finish(input [31:0] status,input [31:0] data);
 begin ack_sequence<=pending_sequence;ack_status<=status;ack_data<=data;command_state<=IDLE;end endtask
 wire bulk_selected,bulk_setup_ready,bulk_setup_error,bulk_run_ready,bulk_done,bulk_error,bulk_active;
 wire[31:0]bulk_rdata;wire[8:0]bulk_completed;
 wire bulk_req_valid,bulk_req_write,bulk_rsp_ready;wire[63:0]bulk_req_generation;wire[31:0]bulk_req_frame;wire[23:0]bulk_req_address;wire[15:0]bulk_req_data;
 wire bulk_route=command_state==BULK_RUN||command_state==BULK_WAIT;
 // Preserve this protocol boundary for exact full-design post-synthesis tests.
 // Do not freeze placement/route or apply a broad DONT_TOUCH to the system.
 (* KEEP_HIERARCHY="TRUE" *) dy71_hud_bulk_v025 bulk(.clk,.rst,.bus_write,.bus_address,.bus_read_address,.bus_wdata,.bus_selected(bulk_selected),.bus_rdata(bulk_rdata),
  .setup_valid(command_state==BULK_SETUP),.setup_ready(bulk_setup_ready),.setup_error(bulk_setup_error),
  .identity_valid(hud_identity&&!quarantine),.command_generation(cmd_gen),.command_frame(cmd_fid),.command_reference(cmd_ref),.command_bank(hud_bank),.command_ticket(hud_ticket),
  .word_offset(command_fields[4]),.word_count(command_fields[5]),.read_mode(command_fields[6]),
  .run_valid(command_state==BULK_RUN),.run_ready(bulk_run_ready),.done(bulk_done),.error(bulk_error),
  .hud_live(hud_pending&&busy&&!quarantine),.live_generation(active_generation),.live_frame(active_frame_id),.live_reference(active_reference_id),.live_ticket(hud_ticket),.live_bank(candidate_bank),
  .req_valid(bulk_req_valid),.req_ready(hud_aux_req_ready&&bulk_route),.req_generation(bulk_req_generation),.req_frame(bulk_req_frame),.req_write(bulk_req_write),.req_address(bulk_req_address),.req_data(bulk_req_data),
  .rsp_valid(hud_aux_rsp_valid&&bulk_route),.rsp_ready(bulk_rsp_ready),.rsp_data(hud_aux_rsp_data),.rsp_error(hud_aux_rsp_error),.active(bulk_active),.completed_words(bulk_completed));
 integer i;
 always @(posedge clk)begin
  if(rst)begin
   command_state<=IDLE;submitted_sequence<=0;pending_sequence<=0;ack_sequence<=0;ack_status<=0;ack_data<=0;rejected_commands<=0;
   operation<=0;last_started_generation<=0;frame_active<=0;seen_busy<=0;diag_address<=0;
   hud_pending<=0;soft_pending<=0;hud_ticket<=0;soft_ticket<=0;hud_gen<=0;soft_gen<=0;
   hud_fid<=0;hud_ref<=0;soft_fid<=0;soft_ref<=0;expected_packet_crc<=0;hud_offset<=0;hud_length<=0;hud_bank<=0;hud_key<=0;hud_tag<=0;soft_opcode<=0;cpu_byte<=0;cpu_word<=0;
   command_word_end<=33'd4;
   for(i=0;i<12;i=i+1)begin fields[i]<=0;command_fields[i]<=0;end
  end else begin
   if(frame_active&&busy)seen_busy<=1;
   if(begin_packet)expected_packet_crc<=command_fields[5];
   if(release_packet)begin frame_active<=0;seen_busy<=0;end
   if(hud_prepare_valid&&hud_prepare_ready)begin
    hud_pending<=1;hud_ticket<=hud_ticket+1'b1;hud_gen<=active_generation;hud_fid<=active_frame_id;hud_ref<=active_reference_id;
    hud_offset<=hud_address;hud_length<=hud_bytes;hud_tag<=expected_hud_tag;hud_key<=active_key;hud_bank<=candidate_bank;
   end
   if(!busy&&!frame_active)hud_pending<=0;
   if(software_command_valid&&software_command_ready)begin
    soft_pending<=1;soft_ticket<=soft_ticket+1'b1;soft_gen<=active_generation;soft_fid<=active_frame_id;soft_ref<=active_reference_id;soft_opcode<=software_command_opcode;
   end
   if(bus_write)begin
    if(bus_address==12'h020)submitted_sequence<=bus_wdata;
    if(bus_address>=12'h040&&bus_address<=12'h06c&&bus_address[1:0]==0)fields[(bus_address-12'h040)>>2]<=bus_wdata;
    if(bus_address==12'h200)diag_address<=bus_wdata[9:0];
    if(bus_address==12'h024)begin
     if(command_idle&&submitted_sequence>ack_sequence)begin
      pending_sequence<=submitted_sequence;operation<=bus_wdata[7:0];ack_status<=32'd1;
      for(i=0;i<12;i=i+1)command_fields[i]<=fields[i];
      command_word_end<={1'b0,fields[4]}+33'd4;
      case(bus_wdata[7:0])
       1:command_state<=BEGIN_PACKET;2:command_state<=SEAL_PACKET;3:command_state<=START_FRAME;
       4:command_state<=DISCARD_PACKET;5:command_state<=ABORT_FRAME;6:command_state<=CLEAR_FAULT;
       16:command_state<=HUD_RESULT;17,18:command_state<=AUX_ISSUE;19:command_state<=HUD_DRAIN;
       20:command_state<=SOFT_ACK;22:command_state<=BULK_SETUP;23:command_state<=BULK_RUN;21:begin command_state<=PACKET_ISSUE;cpu_byte<=0;cpu_word<=0;end
       default:begin ack_sequence<=submitted_sequence;ack_status<=32'h80000001;rejected_commands<=rejected_commands+1'b1;end
      endcase
     end else if(submitted_sequence!=ack_sequence&&submitted_sequence!=pending_sequence)rejected_commands<=rejected_commands+1'b1;
    end
   end
   case(command_state)
    BEGIN_PACKET:begin
     if(!can_begin)finish(32'h80000002,0);
     else finish(0,0);
    end
    SEAL_PACKET:begin
     if(!can_seal)finish(32'h80000003,actual_crc);
     else finish(0,actual_crc);
    end
    START_FRAME:begin
     if(!can_start)finish(32'h80000004,0);
     else if(start_ready)begin frame_active<=1;seen_busy<=0;last_started_generation<=staged_generation;finish(0,0);end
    end
    DISCARD_PACKET:if(!can_discard)finish(32'h80000005,0);else finish(0,0);
    ABORT_FRAME:if(!busy||stage>=9)finish(32'h80000006,0);else finish(0,0);
    CLEAR_FAULT:finish(0,0);
    HUD_RESULT,HUD_DRAIN:begin
     if(!hud_identity)finish(32'h80000007,0);
     else if(command_state==HUD_RESULT&&hud_result_ready)finish(0,0);
     else if(command_state==HUD_DRAIN&&hud_drain_ready)finish(0,0);
    end
    BULK_SETUP:if(bulk_setup_ready)finish(bulk_setup_error?32'h8000000d:0,0);
    BULK_RUN:if(bulk_run_ready)command_state<=BULK_WAIT;
    BULK_WAIT:if(bulk_done)finish(bulk_error?32'h8000000e:0,{23'd0,bulk_completed});
    AUX_ISSUE:begin
     if(!can_aux)finish(32'h80000008,0);
     else if(hud_aux_req_ready)command_state<=AUX_DRAIN;
    end
    AUX_DRAIN:if(hud_aux_rsp_valid)finish(hud_aux_rsp_error?32'h80000009:0,{16'd0,hud_aux_rsp_data});
    SOFT_ACK:begin
     if(!can_soft)finish(32'h8000000a,0);
     else if(software_ack_ready)begin soft_pending<=0;finish(0,0);end
    end
    PACKET_ISSUE:begin
     if(!can_packet)finish(32'h8000000b,0);
     else if(cpu_req_ready)command_state<=PACKET_DRAIN;
    end
    PACKET_DRAIN:if(cpu_rsp_valid)begin
     if(cpu_rsp_address!=cpu_address||cpu_rsp_generation!=cmd_gen||cpu_rsp_sequence!=pending_sequence)finish(32'h8000000c,0);
     else begin
      cpu_word[cpu_byte*8+:8]<=cpu_rsp_data;
      if(cpu_byte==3)finish(0,{cpu_rsp_data,cpu_word[23:0]});
      else begin cpu_byte<=cpu_byte+1'b1;command_state<=PACKET_ISSUE;end
     end
    end
    default:begin end
   endcase
  end
 end
 always @*begin
  bus_rdata=0;
  case(bus_read_address)
   12'h000:bus_rdata=32'h44593731;12'h004:bus_rdata=32'h00030000;
   12'h008:bus_rdata=32'h0000003f; // local staging, CU66 owner, typed HUD; no UDP/30fps capability
   12'h00c:bus_rdata={24'd0,quarantine,soft_pending,hud_pending,frame_active,staging_active,sealed_valid,upload_ready,command_idle};
   12'h020:bus_rdata=submitted_sequence;12'h028:bus_rdata=ack_sequence;12'h02c:bus_rdata=ack_status;12'h030:bus_rdata=ack_data;12'h034:bus_rdata=rejected_commands;
   12'h104:bus_rdata=written_bytes;12'h108:bus_rdata=packet_bytes;12'h10c:bus_rdata=actual_crc;12'h110:bus_rdata=staging_faults;
   12'h114:bus_rdata=staged_generation[31:0];12'h118:bus_rdata=staged_generation[63:32];
   12'h204:bus_rdata=diag_data;
   12'h300:bus_rdata=hud_ticket;12'h304:bus_rdata=hud_gen[31:0];12'h308:bus_rdata=hud_gen[63:32];
   12'h30c:bus_rdata=hud_fid;12'h310:bus_rdata=hud_ref;12'h314:bus_rdata={hud_length,hud_offset};
   12'h318:bus_rdata={29'd0,hud_key,hud_bank};12'h31c:bus_rdata=hud_tag[127:96];12'h320:bus_rdata=hud_tag[95:64];12'h324:bus_rdata=hud_tag[63:32];12'h328:bus_rdata=hud_tag[31:0];
   12'h330:bus_rdata=soft_ticket;12'h334:bus_rdata={29'd0,soft_opcode};12'h338:bus_rdata=soft_gen[31:0];12'h33c:bus_rdata=soft_gen[63:32];12'h340:bus_rdata=soft_fid;12'h344:bus_rdata=soft_ref;
   12'h350:bus_rdata={15'd0,error_code,stage,busy};12'h354:bus_rdata=accepted_count;12'h358:bus_rdata=presented_count;12'h35c:bus_rdata=rejected_count;12'h360:bus_rdata=lcd_underruns;
   default:if(burst_selected)bus_rdata=burst_rdata;else if(bulk_selected)bus_rdata=bulk_rdata;
  endcase
 end
endmodule
`default_nettype wire
