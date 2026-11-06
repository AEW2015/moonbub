// Integrated receiver, canonical memory, painter and native LCD descriptor path.
`timescale 1ns/1ps
module cu75_system #(
    parameter integer WATCHDOG_CYCLES=64000000,
    parameter integer COMMIT_RETRY_CYCLES=64,
    parameter integer USE_STRIP=1,
    parameter integer P0_CACHE_LINES=8,
    parameter integer POWERUP_CYCLES=20000,REFRESH_CYCLES=750
)(
    input logic clk,read_clk,pixel_clk,pixel_reset_n,rst,abort_i,clear_fault,
    input logic start_valid,output logic start_ready,
    input logic [63:0] start_generation,
    input logic [31:0] start_packet_bytes,
    output logic packet_req_valid,input logic packet_req_ready,
    output logic [15:0] packet_req_address,
    output logic [63:0] packet_req_generation,
    output logic [31:0] packet_req_sequence,
    input logic packet_rsp_valid,output logic packet_rsp_ready,
    input logic [63:0] packet_rsp_generation,
    input logic [31:0] packet_rsp_sequence,input logic [15:0] packet_rsp_address,
    input logic [7:0] packet_rsp_data,
    output logic hud_prepare_valid,input logic hud_prepare_ready,
    output logic [63:0] active_generation,
    output logic [31:0] active_frame_id,active_reference_id,
    output logic active_key,
    output logic [15:0] hud_address,hud_bytes,
    output logic [127:0] expected_hud_tag,
    output logic [1:0] candidate_bank,
    input logic hud_result_valid,output logic hud_result_ready,
    input logic [63:0] hud_result_generation,
    input logic [31:0] hud_result_frame_id,hud_result_reference_id,
    input logic [127:0] hud_result_tag,
    input logic [15:0] hud_result_words,input logic hud_result_success,
    input logic hud_drain_valid,output logic hud_drain_ready,
    input logic [63:0] hud_drain_generation,
    input logic [31:0] hud_drain_frame_id,
    input logic [1:0] hud_drain_bank,
    input logic [127:0] hud_drain_tag,
    input logic [15:0] hud_drain_words,input logic hud_drain_success,
    output logic software_command_valid,input logic software_command_ready,
    output logic [2:0] software_command_opcode,
    input logic software_ack_valid,output logic software_ack_ready,
    input logic [2:0] software_ack_opcode,
    input logic [63:0] software_ack_generation,
    input logic [31:0] software_ack_frame_id,input logic software_ack_success,
    output logic front_valid,front_rgb_slot,
    output logic [1:0] front_bank,
    output logic [63:0] front_generation,
    output logic [31:0] front_frame_id,
    output logic reference_valid,
    output logic [1:0] reference_bank,
    output logic [31:0] reference_frame_id,
    output logic [127:0] reference_tag,
    output logic busy,done,aborted,error,
    output logic [7:0] error_code,stage,
    output logic [31:0] accepted_count,presented_count,rejected_count,stale_completions,
    input logic [9:0] diag_address,output logic [31:0] diag_data,
    input logic hud_aux_req_valid,output logic hud_aux_req_ready,
    input logic [63:0] hud_aux_generation,input logic [31:0] hud_aux_frame_id,
    input logic hud_aux_req_write,input logic [23:0] hud_aux_req_addr,input logic [15:0] hud_aux_req_data,
    input logic hud_aux_req_burst,hud_aux_req_read_burst,
    input logic [127:0] hud_aux_req_burst_data,input logic [15:0] hud_aux_req_byte_enable,
    output logic [127:0] hud_aux_rsp_burst_data,
    output logic hud_aux_rsp_valid,input logic hud_aux_rsp_ready,
    output logic [15:0] hud_aux_rsp_data,output logic hud_aux_rsp_error,
    output logic lcd_front_valid,lcd_front_slot,lcd_presented,lcd_pending,lcd_frame_boundary,lcd_scanout_drained,lcd_error,
    output logic [63:0] lcd_front_generation,output logic [31:0] lcd_front_frame_id,lcd_presented_count,
    output logic [31:0] lcd_underruns,lcd_memory_errors,
    output logic hsync,vsync,data_enable,output logic [9:0] physical_x,physical_y,
    output logic [7:0] red,green,blue,
    output logic painter_busy,painter_error,output logic [7:0] painter_error_code,
    output logic [31:0] painter_reads,painter_read_words,painter_writes,painter_write_words,painter_pixels,painter_cycles,
    output logic memory_tile_busy,memory_aux_busy,memory_idle,
    output logic [31:0] memory_cache_hits,memory_cache_misses,memory_reads,memory_writes,
    output logic [31:0] p0_cache_hits,p0_cache_misses,p0_row_reads,p0_wait_cycles,p0_service_cycles,p1_cache_hits,p1_cache_misses,p0_read_wait_cycles,p0_read_service_cycles,
    output wire [12:0] sdram_a,output wire [1:0] sdram_bs,sdram_cke,sdram_cs_n,
    inout wire [15:0] sdram_dq,output wire sdram_clk,sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm
);
    `include "cu70_memory_map.svh"
    logic ref_req_valid,ref_req_ready,ref_rsp_valid,ref_rsp_ready,ref_rsp_error;
    logic [63:0] ref_req_generation,ref_rsp_generation;
    logic [1:0] ref_req_bank,ref_req_plane,ref_rsp_bank,ref_rsp_plane;
    logic [16:0] ref_req_index,ref_rsp_index;
    logic [511:0] ref_rsp_pixels;
    logic write_valid,write_ready,write_done_valid,write_done_ready,write_done_error;
    logic [63:0] write_generation,write_done_generation;
    logic [1:0] write_bank,write_plane,write_done_bank,write_done_plane;
    logic [16:0] write_index,write_done_index;
    logic [511:0] write_pixels;
    logic memory_drained,painter_drained;
    logic paint_start_valid,paint_start_ready,paint_rgb_slot,paint_result_valid,paint_result_ready,paint_result_success,paint_abort;
    logic [63:0] paint_result_generation;
    logic [31:0] paint_result_frame_id;
    logic presentation_valid,presentation_ready,presentation_rgb_slot;
    logic [63:0] presentation_generation;
    logic [31:0] presentation_frame_id;
    logic painter_native_valid,painter_inflight;
    logic [23:0] paint_y,paint_u,paint_v,paint_hud,paint_rgb;
    logic p_req_valid,p_req_ready,p_req_write,p_rsp_valid,p_rsp_ready,p_rsp_error;
    logic [23:0] p_req_addr;logic [15:0] p_req_data,p_rsp_data;
    logic p_req_read_burst;logic [127:0] p_rsp_burst_data;
    logic p_req_burst;logic [127:0] p_req_burst_data;logic [15:0] p_req_byte_enable;
    logic l_req_valid,l_req_ready,l_rsp_valid,l_rsp_ready,l_rsp_error,l_rsp_last;
    logic [23:0] l_req_addr;logic [15:0] l_rsp_data;
    logic m_req_valid,m_req_ready,m_req_write,m_rsp_valid,m_rsp_ready,m_rsp_error;
    logic [23:0] m_req_addr;logic [15:0] m_req_data,m_rsp_data;
    logic hud_access_allowed,hud_permission,hud_drain_checked,hud_transfer_fault;
    logic hud_request_shape_valid,hud_request_wide;logic [15:0] hud_request_words;
    logic[15:0] hud_completed_words;
    typedef enum logic[1:0] {ARB_IDLE,ARB_ISSUE,ARB_RESPONSE,ARB_LOCAL_ERROR} arb_state_t;
    arb_state_t arb_state;
    logic [1:0] arb_owner,arb_next,arb_choice;
    logic arb_choice_valid,arb_response_ready;
    logic [23:0] arb_address;
    logic [15:0] arb_data;
    logic arb_write,arb_burst,arb_read_burst;logic [127:0] m_rsp_burst_data;
    logic [127:0] arb_burst_data;logic [15:0] arb_byte_enable;
    logic [23:0] selected_hud_base;
    always_comb begin
        case(candidate_bank)
            0:selected_hud_base=HUD0_BASE;
            1:selected_hud_base=HUD1_BASE;
            2:selected_hud_base=HUD2_BASE;
            default:selected_hud_base=0;
        endcase
        paint_y=canonical_base(candidate_bank);paint_u=paint_y+24'd172800;paint_v=paint_y+24'd216000;
        paint_hud=selected_hud_base;paint_rgb=paint_rgb_slot?RGB1_BASE:RGB0_BASE;
        // A request has exactly one legal scalar, full-write or full-read shape.
        // Burst bounds cover every word before any physical request is issued.
        hud_request_wide=hud_aux_req_burst||hud_aux_req_read_burst;
        hud_request_words=hud_request_wide?16'd8:16'd1;
        hud_request_shape_valid=(!hud_aux_req_burst&&!hud_aux_req_read_burst&&hud_aux_req_byte_enable==0)||
            (hud_aux_req_write&&hud_aux_req_burst&&!hud_aux_req_read_burst&&hud_aux_req_byte_enable==16'hffff)||
            (!hud_aux_req_write&&!hud_aux_req_burst&&hud_aux_req_read_burst&&hud_aux_req_byte_enable==0);
        hud_permission=hud_access_allowed&&busy&&!paint_abort&&hud_request_shape_valid&&
            hud_aux_generation==active_generation&&hud_aux_frame_id==active_frame_id&&
            (!hud_request_wide||hud_aux_req_addr[2:0]==0)&&
            (!hud_aux_req_write||(hud_aux_req_addr==selected_hud_base+24'(hud_completed_words)&&
             {1'b0,hud_completed_words}+{1'b0,hud_request_words}<=17'd21120))&&
            hud_completed_words<=21120&&hud_aux_req_addr>=selected_hud_base&&
            {1'b0,hud_aux_req_addr}+25'(hud_request_words)<={1'b0,selected_hud_base}+25'd21120&&
            !(hud_drain_valid&&hud_drain_ready&&hud_drain_generation==active_generation&&hud_drain_frame_id==active_frame_id);
        arb_choice_valid=0;arb_choice=0;
        for(integer n=0;n<2;n=n+1)begin
            if(!arb_choice_valid)case((int'(arb_next)+n)%2)
                0:if(hud_aux_req_valid)begin arb_choice_valid=1;arb_choice=0;end
                1:if(p_req_valid)begin arb_choice_valid=1;arb_choice=1;end
                default:begin end
            endcase
        end
        hud_aux_req_ready=arb_state==ARB_IDLE&&arb_choice_valid&&arb_choice==0&&!rst;
        p_req_ready=arb_state==ARB_IDLE&&arb_choice_valid&&arb_choice==1&&!rst;
        hud_aux_rsp_valid=!rst&&((arb_state==ARB_RESPONSE&&m_rsp_valid&&arb_owner==0)||arb_state==ARB_LOCAL_ERROR);
        p_rsp_valid=!rst&&arb_state==ARB_RESPONSE&&m_rsp_valid&&arb_owner==1;
        hud_aux_rsp_data=arb_state==ARB_LOCAL_ERROR?16'd0:m_rsp_data;
        hud_aux_rsp_burst_data=arb_state==ARB_LOCAL_ERROR?128'd0:m_rsp_burst_data;
        hud_aux_rsp_error=arb_state==ARB_LOCAL_ERROR||m_rsp_error;
        p_rsp_burst_data=m_rsp_burst_data;p_rsp_data=m_rsp_data;p_rsp_error=m_rsp_error;
        case(arb_owner)
            0:arb_response_ready=hud_aux_rsp_ready;
            1:arb_response_ready=p_rsp_ready;
            default:arb_response_ready=0;
        endcase
        m_req_valid=arb_state==ARB_ISSUE&&!rst;m_req_write=arb_write;m_req_addr=arb_address;m_req_data=arb_data;
        m_rsp_ready=arb_state==ARB_RESPONSE&&arb_response_ready&&!rst;
        // Front scanout has its own lease and must not block every frame commit.
        memory_drained=!memory_tile_busy&&arb_state==ARB_IDLE;
        painter_drained=!painter_busy;
        hud_drain_checked=hud_drain_success&&hud_completed_words==21120&&!hud_transfer_fault&&
                          !(arb_state!=ARB_IDLE&&arb_owner==0);
        paint_result_valid=painter_native_valid||(painter_inflight&&!painter_busy&&painter_error);
        paint_result_success=painter_native_valid&&!painter_error;
    end
    always_ff @(posedge clk)begin
        if(rst)begin
            arb_state<=ARB_IDLE;arb_owner<=0;arb_next<=0;arb_address<=0;arb_data<=0;arb_write<=0;arb_read_burst<=0;arb_burst<=0;arb_burst_data<=0;arb_byte_enable<=0;
            hud_access_allowed<=0;painter_inflight<=0;hud_completed_words<=0;hud_transfer_fault<=0;
        end else begin
            if(hud_prepare_valid&&hud_prepare_ready)begin hud_access_allowed<=1;hud_completed_words<=0;hud_transfer_fault<=0;end
            if(arb_state==ARB_RESPONSE&&arb_owner==0&&arb_write&&m_rsp_valid&&m_rsp_ready)begin
                if(m_rsp_error)hud_transfer_fault<=1;
                else hud_completed_words<=hud_completed_words+(arb_burst?16'd8:16'd1);
            end
            if(!busy||paint_abort||(hud_drain_valid&&hud_drain_ready&&hud_drain_generation==active_generation&&hud_drain_frame_id==active_frame_id))hud_access_allowed<=0;
            if(paint_start_valid&&paint_start_ready)painter_inflight<=1;
            if(paint_abort||(paint_result_valid&&paint_result_ready))painter_inflight<=0;
            case(arb_state)
                ARB_IDLE:if(arb_choice_valid)begin
                    arb_owner<=arb_choice;arb_next<=arb_choice==1?2'd0:2'd1;
                    if(arb_choice==0)begin
                        arb_address<=hud_aux_req_addr;arb_data<=hud_aux_req_data;arb_write<=hud_aux_req_write;
                        arb_read_burst<=hud_aux_req_read_burst;arb_burst<=hud_aux_req_burst;
                        arb_burst_data<=hud_aux_req_burst_data;arb_byte_enable<=hud_aux_req_byte_enable;
                        arb_state<=hud_permission?ARB_ISSUE:ARB_LOCAL_ERROR;
                    end else begin
                        arb_address<=p_req_addr;arb_data<=p_req_data;arb_write<=p_req_write;arb_state<=ARB_ISSUE;
                        arb_read_burst<=p_req_read_burst;arb_burst<=p_req_burst;arb_burst_data<=p_req_burst_data;arb_byte_enable<=p_req_byte_enable;
                    end
                end
                ARB_ISSUE:if(m_req_valid&&m_req_ready)arb_state<=ARB_RESPONSE;
                ARB_RESPONSE:if(m_rsp_valid&&m_rsp_ready)arb_state<=ARB_IDLE;
                ARB_LOCAL_ERROR:if(hud_aux_rsp_ready)arb_state<=ARB_IDLE;
                default:arb_state<=ARB_IDLE;
            endcase
        end
    end
    cu70_receiver #(.WATCHDOG_CYCLES(WATCHDOG_CYCLES),.COMMIT_RETRY_CYCLES(COMMIT_RETRY_CYCLES)) receiver(
        .clk,.rst,.abort_i,.clear_fault,.start_valid,.start_ready,.start_generation,.start_packet_bytes,
        .packet_req_valid,.packet_req_ready,.packet_req_address,.packet_req_generation,.packet_req_sequence,
        .packet_rsp_valid,.packet_rsp_ready,.packet_rsp_generation,.packet_rsp_sequence,.packet_rsp_address,.packet_rsp_data,
        .ref_req_valid,.ref_req_ready,.ref_req_generation,.ref_req_bank,.ref_req_plane,.ref_req_index,
        .ref_rsp_valid,.ref_rsp_ready,.ref_rsp_generation,.ref_rsp_bank,.ref_rsp_plane,.ref_rsp_index,.ref_rsp_pixels,.ref_rsp_error,
        .write_valid,.write_ready,.write_generation,.write_bank,.write_plane,.write_index,.write_pixels,
        .write_done_valid,.write_done_ready,.write_done_generation,.write_done_bank,.write_done_plane,.write_done_index,.write_done_error,.memory_drained,
        .hud_prepare_valid,.hud_prepare_ready,.active_generation,.active_frame_id,.active_reference_id,.active_key,.hud_address,.hud_bytes,.expected_hud_tag,.candidate_bank,
        .hud_result_valid,.hud_result_ready,.hud_result_generation,.hud_result_frame_id,.hud_result_reference_id,.hud_result_tag,.hud_result_words,.hud_result_success,
        .hud_drain_valid,.hud_drain_ready,.hud_drain_generation,.hud_drain_frame_id,.hud_drain_bank,.hud_drain_tag,.hud_drain_words,.hud_drain_success(hud_drain_checked),
        .software_command_valid,.software_command_ready,.software_command_opcode,.software_ack_valid,.software_ack_ready,.software_ack_opcode,
        .software_ack_generation,.software_ack_frame_id,.software_ack_success,
        .paint_start_valid,.paint_start_ready,.paint_rgb_slot,.paint_result_valid,.paint_result_ready,.paint_result_generation,.paint_result_frame_id,.paint_result_success,.painter_drained,.paint_abort,
        .presentation_valid,.presentation_ready,.presentation_generation,.presentation_frame_id,.presentation_rgb_slot,
        .vblank(lcd_presented),.scanout_drained(lcd_presented),.presented_generation(lcd_front_generation),.presented_frame_id(lcd_front_frame_id),.presented_rgb_slot(lcd_front_slot),
        .front_valid,.front_rgb_slot,.front_bank,.front_generation,.front_frame_id,.reference_valid,.reference_bank,.reference_frame_id,.reference_tag,
        .busy,.done,.aborted,.error,.error_code,.stage,.accepted_count,.presented_count,.rejected_count,.stale_completions,.diag_address,.diag_data);
    cu74_memory_system #(.P0_CACHE_LINES(P0_CACHE_LINES),.POWERUP_CYCLES(POWERUP_CYCLES),.REFRESH_CYCLES(REFRESH_CYCLES)) memory(
        .clk,.read_clk,.rst,.abort_i(1'b0),.aux_abort_i(1'b0),
        .read_valid(ref_req_valid),.read_ready(ref_req_ready),.read_generation(ref_req_generation),.read_bank(ref_req_bank),.read_plane(ref_req_plane),.read_index(ref_req_index),
        .read_rsp_valid(ref_rsp_valid),.read_rsp_ready(ref_rsp_ready),.read_rsp_generation(ref_rsp_generation),.read_rsp_bank(ref_rsp_bank),.read_rsp_plane(ref_rsp_plane),.read_rsp_index(ref_rsp_index),.read_rsp_pixels(ref_rsp_pixels),.read_rsp_error(ref_rsp_error),
        .write_valid,.write_ready,.write_generation,.write_bank,.write_plane,.write_index,.write_pixels,
        .write_done_valid,.write_done_ready,.write_done_generation,.write_done_bank,.write_done_plane,.write_done_index,.write_done_error,
        .tile_busy(memory_tile_busy),.tile_aborted(),
        .aux_req_valid(m_req_valid),.aux_req_ready(m_req_ready),.aux_req_write(m_req_write),.aux_req_addr(m_req_addr),.aux_req_data(m_req_data),
        .aux_req_read_burst(arb_read_burst),.aux_rsp_burst_data(m_rsp_burst_data),
        .aux_req_burst(arb_burst),.aux_req_burst_data(arb_burst_data),.aux_req_byte_enable(arb_byte_enable),
        .aux_rsp_valid(m_rsp_valid),.aux_rsp_ready(m_rsp_ready),.aux_rsp_data(m_rsp_data),.aux_rsp_error(m_rsp_error),.aux_busy(memory_aux_busy),.aux_aborted(),
        .lcd_req_valid(l_req_valid),.lcd_req_ready(l_req_ready),.lcd_req_addr(l_req_addr),
        .lcd_rsp_valid(l_rsp_valid),.lcd_rsp_ready(l_rsp_ready),.lcd_rsp_data(l_rsp_data),.lcd_rsp_last(l_rsp_last),.lcd_rsp_error(l_rsp_error),
        .lcd_busy(),
        .p0_cache_hits,.p0_cache_misses,.p0_row_reads,.p0_wait_cycles,.p0_service_cycles,.p1_cache_hits,.p1_cache_misses,.p0_read_wait_cycles,.p0_read_service_cycles,
        .cache_hits(memory_cache_hits),.cache_misses(memory_cache_misses),.completed_reads(memory_reads),.completed_writes(memory_writes),
        .sdram_a,.sdram_bs,.sdram_cke,.sdram_cs_n,.sdram_dq,.sdram_clk,.sdram_ras_n,.sdram_cas_n,.sdram_we_n,.sdram_ldqm,.sdram_udqm,.idle(memory_idle));
    initial if(USE_STRIP!=1)$fatal(1,"V75 requires tile-aware painter");
    cu75_painter_burst painter(
        .clk,.rst,.abort_i(paint_abort),.start_valid(paint_start_valid),.start_ready(paint_start_ready),.generation(active_generation),.frame_id(active_frame_id),
        .y_base(paint_y),.u_base(paint_u),.v_base(paint_v),.hud_base(paint_hud),.rgb_base(paint_rgb),
        .aux_req_valid(p_req_valid),.aux_req_ready(p_req_ready),.aux_req_write(p_req_write),.aux_req_addr(p_req_addr),.aux_req_data(p_req_data),
        .aux_req_read_burst(p_req_read_burst),.aux_rsp_burst_data(p_rsp_burst_data),
        .aux_req_burst(p_req_burst),.aux_req_burst_data(p_req_burst_data),.aux_req_byte_enable(p_req_byte_enable),
        .aux_rsp_valid(p_rsp_valid),.aux_rsp_ready(p_rsp_ready),.aux_rsp_data(p_rsp_data),.aux_rsp_error(p_rsp_error),
        .result_valid(painter_native_valid),.result_ready(paint_result_ready),.result_generation(paint_result_generation),.result_frame_id(paint_result_frame_id),
        .busy(painter_busy),.done(),.aborted(),.error(painter_error),.error_code(painter_error_code),.memory_reads(painter_reads),.memory_read_words(painter_read_words),.memory_writes(painter_writes),.memory_write_words(painter_write_words),.painted_pixels(painter_pixels),.cycle_count(painter_cycles));
    cu71_scanout #(.RGB_BASE(RGB0_BASE)) scanout(
        .mem_clk(clk),.mem_rst(rst),.pixel_clk,.pixel_reset_n,
        .descriptor_valid(presentation_valid),.descriptor_ready(presentation_ready),.descriptor_generation(presentation_generation),.descriptor_frame_id(presentation_frame_id),.descriptor_slot(presentation_rgb_slot),
        .presented(lcd_presented),.error(lcd_error),.front_valid(lcd_front_valid),.front_slot(lcd_front_slot),.front_generation(lcd_front_generation),.front_frame_id(lcd_front_frame_id),.pending_valid(lcd_pending),.presented_count(lcd_presented_count),
        .frame_boundary(lcd_frame_boundary),.scanout_drained(lcd_scanout_drained),
        .lcd_req_valid(l_req_valid),.lcd_req_ready(l_req_ready),.lcd_req_addr(l_req_addr),
        .lcd_rsp_valid(l_rsp_valid),.lcd_rsp_ready(l_rsp_ready),.lcd_rsp_data(l_rsp_data),.lcd_rsp_last(l_rsp_last),.lcd_rsp_error(l_rsp_error),
        .underruns(lcd_underruns),.memory_errors(lcd_memory_errors),.hsync,.vsync,.data_enable,.physical_x,.physical_y,.red,.green,.blue);
endmodule
