// Experimental direct tile-major YUV/HUD display owner. No RGB framebuffer.
// InternalPREPARE does not attest canonical/HUD integrity: the root owner must
// already have validated those tags and retain the supplied memory leases.
`timescale 1ns/1ps
`default_nettype none
module cu71_direct_scanout_fullword_v018(
 input wire mem_clk,rst,pixel_clk,pixel_reset_n,
 input wire prepare_valid,output wire prepare_ready,
 input wire[63:0]prepare_generation,input wire[31:0]prepare_frame_id,
 input wire[1:0]prepare_canonical_bank,prepare_hud_bank,input wire prepare_cache_slot,
 output wire prepared_valid,input wire prepared_ready,
 output reg[63:0]prepared_generation,output reg[31:0]prepared_frame_id,
 output reg prepared_cache_slot,prepared_error,output reg[7:0]prepared_reason,
 input wire prepare_abort_valid,output wire prepare_abort_ready,
 input wire[63:0]prepare_abort_generation,input wire[31:0]prepare_abort_frame_id,
 input wire prepare_abort_cache_slot,output reg abort_done,abort_error,
 input wire descriptor_valid,output wire descriptor_ready,
 input wire[63:0]descriptor_generation,input wire[31:0]descriptor_frame_id,input wire descriptor_cache_slot,
 output reg presented,error,output reg front_valid,front_cache_slot,
 output reg[63:0]front_generation,output reg[31:0]front_frame_id,
 output reg pending_valid,output reg[31:0]presented_count,
 output wire frame_boundary,scanout_drained,
 output wire lcd_req_valid,input wire lcd_req_ready,output wire[23:0]lcd_req_addr,
 input wire lcd_rsp_valid,output wire lcd_rsp_ready,input wire[127:0]lcd_rsp_data,input wire lcd_rsp_error,
 output wire lcd_abort_i,input wire lcd_busy,lcd_aborted,
 output wire[31:0]underruns,dma_reads,unowned_dma_responses,
 output reg[31:0]accepted_prepares,rejected_prepares,rejected_descriptors,
 output reg[31:0]memory_errors,line_cache_misses,generated_lines,prepare_cycles,
 output reg[7:0]first_fault,output reg[63:0]first_fault_generation,
 output reg[31:0]first_fault_frame_id,
 output wire hsync,vsync,data_enable,output wire[9:0]physical_x,physical_y,
 output wire[7:0]red,green,blue
);
 `include "cu70_memory_map.svh"
 localparam[2:0]C_FREE=0,C_FILL=1,C_READY=2,C_PENDING=3,C_FRONT=4;
 reg[2:0]context_state[0:1];
 reg[63:0]context_generation[0:1];reg[31:0]context_frame[0:1];
 reg[1:0]context_canonical[0:1],context_hud[0:1];
 reg[1:0]y_valid[0:1],c_valid[0:1];reg hud_valid[0:1],front_fault[0:1];
 reg[6:0]y_tag[0:1][0:1];reg[5:0]c_tag[0:1][0:1];
 reg[63:0]latest_generation;
 reg result_held,p_active,p_slot,p_fail;
 reg[7:0]p_fail_reason;
 reg[2:0]p_phase;reg[5:0]p_tile_y;reg[1:0]p_chunk;
 reg[14:0]p_hud_offset;reg[23:0]p_tile_base;
 reg abort_pending,abort_slot;reg[63:0]abort_generation;reg[31:0]abort_frame;
 reg pending_slot;reg[63:0]pending_generation;reg[31:0]pending_frame;
 reg fatal_dma;
 reg f_active,f_slot,f_address_pending;reg[9:0]wanted_u_stage;reg[1:0]f_kind;reg[6:0]f_group;reg[5:0]f_tile_y;reg[1:0]f_chunk;reg[23:0]f_tile_base;
 reg[9:0]front_next_u;
 reg inflight,inflight_front,inflight_slot,dma_abort_sent;reg[31:0]next_cookie,inflight_cookie;reg[63:0]inflight_generation;reg[31:0]inflight_frame;
 function automatic[23:0]hud_base_for(input[1:0]bank);
  case(bank)0:hud_base_for=HUD0_BASE;1:hud_base_for=HUD1_BASE;2:hud_base_for=HUD2_BASE;default:hud_base_for=0;endcase
 endfunction
 function automatic[1:0]phase_kind(input[2:0]phase);
  if(phase==0)phase_kind=3;else if(phase<=2)phase_kind=0;else if(phase==3||phase==5)phase_kind=1;else phase_kind=2;
 endfunction
 function automatic phase_group(input[2:0]phase);
  phase_group=phase==2||phase==5||phase==6;
 endfunction
 function automatic[23:0]page_start(input[1:0]kind,input[6:0]group,input[1:0]bank);
  page_start=canonical_base(bank)+(kind==0?24'd0:kind==1?24'd172800:24'd216000)+{12'd0,group,5'd0};
 endfunction
 wire abort_target=prepare_abort_generation!=0&&context_generation[prepare_abort_cache_slot]==prepare_abort_generation&&
  context_frame[prepare_abort_cache_slot]==prepare_abort_frame_id&&
  (context_state[prepare_abort_cache_slot]==C_FILL||context_state[prepare_abort_cache_slot]==C_READY);
 assign prepare_abort_ready=!abort_pending&&!rst;
 wire incoming_abort=prepare_abort_valid&&prepare_abort_ready&&abort_target;
 assign prepare_ready=!p_active&&!p_fail&&!result_held&&!abort_pending&&!rst&&!fatal_dma&&!prepare_abort_valid;
 assign prepared_valid=result_held&&!rst&&!(incoming_abort&&prepared_cache_slot==prepare_abort_cache_slot)&&
  !(abort_pending&&prepared_cache_slot==abort_slot);
 assign descriptor_ready=!pending_valid&&!rst&&!fatal_dma&&!abort_pending&&!prepare_abort_valid;
 wire line_req_valid,line_req_ready,line_data_valid,line_data_error,requests_idle;
 wire[9:0]line_req_line;wire line_req_context;wire[23:0]unused_line_address;
 wire[15:0]line_data;
 reg render_active,render_black,render_fault,render_slot;
 reg[9:0]render_u,issue_count,emit_count;
 reg[14:0]hud_ab_index,hud_c_index,hud_d_index;
 wire[9:0]requested_u=line_req_line-10'd40;
 wire invalid_line=line_req_line<40||line_req_line>=760||line_req_context!=front_cache_slot;
 wire[6:0]request_yg=requested_u[9:3];wire[5:0]request_cg=requested_u[9:4];
 wire request_halo=requested_u[0]&&requested_u[3:1]==7&&requested_u!=719;
 wire request_y_ready=y_valid[front_cache_slot][request_yg[0]]&&y_tag[front_cache_slot][request_yg[0]]==request_yg;
 wire request_c_ready=c_valid[front_cache_slot][request_cg[0]]&&c_tag[front_cache_slot][request_cg[0]]==request_cg;
 wire request_next_c_ready=!request_halo||(c_valid[front_cache_slot][!request_cg[0]]&&c_tag[front_cache_slot][!request_cg[0]]==request_cg+6'd1);
 wire cache_ready=request_y_ready&&request_c_ready&&request_next_c_ready&&hud_valid[front_cache_slot];
 wire pixel_busy,cache_valid,cache_error,pixel_valid,cache_read_busy;wire[31:0]cache_tag_value,pixel_tag;
 wire[15:0]pixel_rgb;reg[4:0]pixel_fault;
 assign line_req_ready=!render_active&&!pixel_busy&&!cache_read_busy&&front_valid&&!rst&&
  (invalid_line||front_fault[front_cache_slot]||cache_ready);
 wire cache_rd_valid=render_active&&!render_black&&issue_count<480&&!rst;
 reg hud_hit;reg[14:0]hud_read_index;
 always @*begin
  hud_hit=0;hud_read_index=0;
  if(render_u>=22&&render_u<182&&((issue_count>=54&&issue_count<78)||(issue_count>=82&&issue_count<106)))begin hud_hit=1;hud_read_index=hud_ab_index;end
  else if(render_u>=168&&render_u<488&&issue_count>=360&&issue_count<384)begin hud_hit=1;hud_read_index=hud_c_index;end
  else if(render_u>=168&&render_u<408&&issue_count>=390&&issue_count<414)begin hud_hit=1;hud_read_index=hud_d_index;end
 end
 wire[7:0]Y,cb_t0,cb_t1,cb_b0,cb_b1,cr_t0,cr_t1,cr_b0,cr_b1;
 wire x_odd,y_odd,cached_hud_hit;wire[15:0]cached_hud;
 wire cache_wr_valid,cache_wr_context,cache_wr_bank;wire[1:0]cache_wr_kind;wire[8:0]cache_wr_row;
 wire[63:0]cache_wr_data;wire[14:0]cache_wr_hud_index;wire[15:0]cache_wr_hud_word;wire cache_wr_error;
 wire cache_wr_allow=context_state[cache_wr_context]==C_FILL||context_state[cache_wr_context]==C_FRONT;
 cu71_direct_cache_fullword_v018 cache(.clk(mem_clk),.rst,.wr_valid(cache_wr_valid),.wr_allow(cache_wr_allow),.wr_context(cache_wr_context),.wr_bank(cache_wr_bank),.wr_kind(cache_wr_kind),.wr_row(cache_wr_row),.wr_data(cache_wr_data),.wr_hud_index(cache_wr_hud_index),.wr_hud_word(cache_wr_hud_word),.wr_error(cache_wr_error),
  .front_valid,.front_context(front_cache_slot),.render_live(render_active&&!render_black),.render_context(render_slot),.render_u,
  .rd_valid(cache_rd_valid),.rd_context(render_slot),.rd_u(render_u),.rd_v(issue_count[8:0]),.rd_hud_hit(hud_hit),.rd_hud_index(hud_read_index),.rd_tag({13'd0,render_u,issue_count[8:0]}),
  .out_valid(cache_valid),.out_error(cache_error),.out_tag(cache_tag_value),.out_y(Y),.out_cb_t0(cb_t0),.out_cb_t1(cb_t1),.out_cb_b0(cb_b0),.out_cb_b1(cb_b1),
  .out_cr_t0(cr_t0),.out_cr_t1(cr_t1),.out_cr_b0(cr_b0),.out_cr_b1(cr_b1),.out_x_odd(x_odd),.out_y_odd(y_odd),.out_hud_word(cached_hud),.out_hud_hit(cached_hud_hit),.read_busy(cache_read_busy));
 cu71_yuv_pixel_pipe pixel(.clk(mem_clk),.rst,.in_valid(cache_valid),.in_tag(cache_tag_value),.in_y(Y),.in_cb_t0(cb_t0),.in_cb_t1(cb_t1),.in_cb_b0(cb_b0),.in_cb_b1(cb_b1),
  .in_cr_t0(cr_t0),.in_cr_t1(cr_t1),.in_cr_b0(cr_b0),.in_cr_b1(cr_b1),.in_x_odd(x_odd),.in_y_odd(y_odd),
  .in_hud_hit(cached_hud_hit||cache_error),.in_hud_word(cache_error?16'd0:cached_hud),.out_valid(pixel_valid),.out_tag(pixel_tag),.out_rgb(pixel_rgb),.busy(pixel_busy));
 wire bad_pixel_tag=pixel_valid&&pixel_tag!={13'd0,render_u,emit_count[8:0]};
 assign line_data_valid=render_active&&(render_black||pixel_valid);
 assign line_data=render_black?16'd0:pixel_rgb;
 assign line_data_error=render_black||render_fault||pixel_fault[4]||bad_pixel_tag;
 cu71_lcd_lines_syncsafe lcd(.pixel_clk,.reset_n(pixel_reset_n),.mem_clk,.mem_reset(rst),.front_valid,.front_buffer(front_cache_slot),.pattern_enable(1'b0),
  .line_req_valid,.line_req_ready,.line_req_address(unused_line_address),.line_req_line,.line_req_context,.line_data_valid,.line_data,.line_data_error,
  .frame_boundary,.underruns,.requests_idle,.hsync,.vsync,.data_enable,.physical_x,.physical_y,.red,.green,.blue);
 wire dma_busy,dma_cmd_ready,dma_result_valid,dma_abort_ready,dma_abort_rejected;
 wire[63:0]dma_result_generation;wire[31:0]dma_result_frame,dma_result_cookie;
 wire dma_result_slot,dma_result_error,dma_result_aborted;wire[7:0]dma_result_reason;
 wire[31:0]unused_dma_commands,unused_dma_completed,unused_dma_aborted;
 wire[7:0]unused_dma_first_fault;wire[63:0]unused_dma_fault_generation;
 wire[31:0]unused_dma_fault_frame,unused_dma_fault_cookie;wire[23:0]unused_dma_fault_source;
 assign scanout_drained=requests_idle&&!render_active&&!pixel_busy&&!cache_read_busy&&!inflight&&!dma_busy&&!lcd_busy;
 wire switch_now=frame_boundary&&scanout_drained&&pending_valid&&!abort_pending&&!fatal_dma;
 wire choose_front=f_active;
 wire command_slot=choose_front?f_slot:p_slot;
 wire[1:0]command_kind=choose_front?f_kind:phase_kind(p_phase);
 wire command_bank=choose_front?f_group[0]:phase_group(p_phase);
 wire[23:0]command_source=choose_front?(f_tile_base+24'({f_chunk,3'd0})):
  (p_phase==0?hud_base_for(context_hud[p_slot])+24'(p_hud_offset):p_tile_base+24'({p_chunk,3'd0}));
 wire[8:0]command_row=choose_front?{f_tile_y,f_chunk,1'b0}:{p_tile_y,p_chunk,1'b0};
 wire dma_cmd_valid=(f_active||p_active)&&!(choose_front&&f_address_pending)&&!inflight&&!dma_busy&&!abort_pending&&!p_fail&&!fatal_dma&&!switch_now&&!prepare_abort_valid&&!rst&&next_cookie!=32'hffffffff;
 wire dma_abort_valid=abort_pending&&!dma_abort_sent&&inflight&&inflight_slot==abort_slot&&inflight_generation==abort_generation&&inflight_frame==abort_frame;
 cu71_cache_dma dma(.clk(mem_clk),.rst,.cmd_valid(dma_cmd_valid),.cmd_ready(dma_cmd_ready),.cmd_generation(context_generation[command_slot]),.cmd_frame_id(context_frame[command_slot]),.cmd_cookie(next_cookie),.cmd_context(command_slot),.cmd_bank(command_bank),.cmd_kind(command_kind),.cmd_source(command_source),.cmd_row(command_row),.cmd_hud_index(p_hud_offset),
  .result_valid(dma_result_valid),.result_ready(1'b1),.result_generation(dma_result_generation),.result_frame_id(dma_result_frame),.result_cookie(dma_result_cookie),.result_context(dma_result_slot),.result_error(dma_result_error),.result_aborted(dma_result_aborted),.result_reason(dma_result_reason),
  .abort_valid(dma_abort_valid),.abort_ready(dma_abort_ready),.abort_generation,.abort_frame_id(abort_frame),.abort_context(abort_slot),.abort_rejected(dma_abort_rejected),
  .lcd_req_valid,.lcd_req_ready,.lcd_req_addr,.lcd_rsp_valid,.lcd_rsp_ready,.lcd_rsp_data,.lcd_rsp_error,.lcd_abort_i,.lcd_busy,.lcd_aborted,
  .cache_wr_valid,.cache_wr_context,.cache_wr_bank,.cache_wr_kind,.cache_wr_row,.cache_wr_data,.cache_wr_hud_index,.cache_wr_hud_word,.cache_wr_error,
  .accepted_commands(unused_dma_commands),.accepted_reads(dma_reads),.completed_commands(unused_dma_completed),.aborted_commands(unused_dma_aborted),.unowned_responses(unowned_dma_responses),
  .first_fault(unused_dma_first_fault),.fault_generation(unused_dma_fault_generation),.fault_frame_id(unused_dma_fault_frame),.fault_cookie(unused_dma_fault_cookie),.fault_source(unused_dma_fault_source),.busy(dma_busy));
 // Desired current/next pages advance after a line has completely drained.
 // An urgent queued line can jump over missed rows; never serve a wrong tag.
 wire[9:0]wanted_u_input=line_req_valid&&!invalid_line&&!render_active?requested_u:front_next_u;
 wire[9:0]wanted_u=wanted_u_stage;
 wire[6:0]wanted_y=wanted_u[9:3];wire[5:0]wanted_c=wanted_u[9:4];
 wire wanted_halo=wanted_u[0]&&wanted_u[3:1]==7&&wanted_u!=719;
 reg refill_needed;reg[1:0]refill_kind;reg[6:0]refill_group;
 always @*begin
  refill_needed=0;refill_kind=0;refill_group=0;
  if(front_valid&&!front_fault[front_cache_slot])begin
   if(!y_valid[front_cache_slot][wanted_y[0]]||y_tag[front_cache_slot][wanted_y[0]]!=wanted_y)begin refill_needed=1;refill_kind=0;refill_group=wanted_y;end
   else if(!c_valid[front_cache_slot][wanted_c[0]]||c_tag[front_cache_slot][wanted_c[0]]!=wanted_c)begin refill_needed=1;refill_kind=1;refill_group={1'b0,wanted_c};end
   else if(wanted_halo&&(!c_valid[front_cache_slot][!wanted_c[0]]||c_tag[front_cache_slot][!wanted_c[0]]!=wanted_c+6'd1))begin refill_needed=1;refill_kind=1;refill_group={1'b0,wanted_c}+7'd1;end
   else if(wanted_y<89&&(!y_valid[front_cache_slot][!wanted_y[0]]||y_tag[front_cache_slot][!wanted_y[0]]!=wanted_y+7'd1))begin refill_needed=1;refill_kind=0;refill_group=wanted_y+7'd1;end
   else if(wanted_c<44&&(!c_valid[front_cache_slot][!wanted_c[0]]||c_tag[front_cache_slot][!wanted_c[0]]!=wanted_c+6'd1))begin refill_needed=1;refill_kind=1;refill_group={1'b0,wanted_c}+7'd1;end
  end
 end
 wire refill_hazard=render_active&&!render_black&&render_slot==front_cache_slot&&
  (refill_kind==0?refill_group[0]==render_u[3]:(refill_group[0]==render_u[4]||(render_u[0]&&render_u[3:1]==7&&render_u!=719)));
 reg miss_seen;reg[9:0]miss_line;
 task automatic note_fault(input[7:0]reason,input[63:0]generation,input[31:0]frame);
  begin error<=1;if(first_fault==0)begin first_fault<=reason;first_fault_generation<=generation;first_fault_frame_id<=frame;end end
 endtask
 always @(posedge mem_clk)begin
  if(rst)begin
   latest_generation<=0;result_held<=0;p_active<=0;p_slot<=0;p_fail<=0;p_fail_reason<=0;p_phase<=0;p_tile_y<=0;p_chunk<=0;p_hud_offset<=0;p_tile_base<=0;
   prepared_generation<=0;prepared_frame_id<=0;prepared_cache_slot<=0;prepared_error<=0;prepared_reason<=0;
   abort_pending<=0;abort_slot<=0;abort_generation<=0;abort_frame<=0;abort_done<=0;abort_error<=0;
   front_valid<=0;front_cache_slot<=0;front_generation<=0;front_frame_id<=32'hffffffff;front_next_u<=0;
   pending_valid<=0;pending_slot<=0;pending_generation<=0;pending_frame<=0;presented<=0;error<=0;presented_count<=0;fatal_dma<=0;
   f_active<=0;f_address_pending<=0;wanted_u_stage<=0;f_slot<=0;f_kind<=0;f_group<=0;f_tile_y<=0;f_chunk<=0;f_tile_base<=0;
   inflight<=0;inflight_front<=0;inflight_slot<=0;dma_abort_sent<=0;next_cookie<=1;inflight_cookie<=0;inflight_generation<=0;inflight_frame<=0;
   render_active<=0;render_black<=0;render_fault<=0;render_slot<=0;render_u<=0;issue_count<=0;emit_count<=0;hud_ab_index<=0;hud_c_index<=0;hud_d_index<=0;pixel_fault<=0;
   accepted_prepares<=0;rejected_prepares<=0;rejected_descriptors<=0;memory_errors<=0;line_cache_misses<=0;generated_lines<=0;prepare_cycles<=0;
   first_fault<=0;first_fault_generation<=0;first_fault_frame_id<=0;miss_seen<=0;miss_line<=0;
   for(integer i=0;i<2;i=i+1)begin
    context_state[i]<=C_FREE;context_generation[i]<=0;context_frame[i]<=0;context_canonical[i]<=0;context_hud[i]<=0;y_valid[i]<=0;c_valid[i]<=0;hud_valid[i]<=0;front_fault[i]<=0;
    for(integer j=0;j<2;j=j+1)begin y_tag[i][j]<=0;c_tag[i][j]<=0;end
   end
  end else begin
   presented<=0;error<=0;abort_done<=0;abort_error<=0;
   wanted_u_stage<=wanted_u_input;
   if(f_address_pending)begin f_tile_base<=page_start(f_kind,f_group,context_canonical[f_slot]);f_address_pending<=0;end
   pixel_fault<={pixel_fault[3:0],cache_valid&&cache_error};
   if(prepared_valid&&prepared_ready)result_held<=0;
   if(p_active&&!result_held)prepare_cycles<=prepare_cycles+1;
   if(prepare_valid&&prepare_ready)begin
    prepared_generation<=prepare_generation;prepared_frame_id<=prepare_frame_id;prepared_cache_slot<=prepare_cache_slot;prepared_error<=0;prepared_reason<=0;
    if(prepare_generation==0||prepare_generation<=latest_generation||prepare_frame_id==32'hffffffff||prepare_canonical_bank==3||prepare_hud_bank==3||context_state[prepare_cache_slot]!=C_FREE)begin
     result_held<=1;prepared_error<=1;prepared_reason<=1;rejected_prepares<=rejected_prepares+1;note_fault(8'h01,prepare_generation,prepare_frame_id);
    end else begin
     accepted_prepares<=accepted_prepares+1;latest_generation<=prepare_generation;p_active<=1;p_slot<=prepare_cache_slot;p_phase<=0;p_tile_y<=0;p_chunk<=0;p_hud_offset<=0;p_tile_base<=0;prepare_cycles<=0;
     context_state[prepare_cache_slot]<=C_FILL;context_generation[prepare_cache_slot]<=prepare_generation;context_frame[prepare_cache_slot]<=prepare_frame_id;context_canonical[prepare_cache_slot]<=prepare_canonical_bank;context_hud[prepare_cache_slot]<=prepare_hud_bank;
     y_valid[prepare_cache_slot]<=0;c_valid[prepare_cache_slot]<=0;hud_valid[prepare_cache_slot]<=0;front_fault[prepare_cache_slot]<=0;
    end
   end
   if(prepare_abort_valid&&prepare_abort_ready)begin
    if(!abort_target)begin abort_done<=1;abort_error<=1;note_fault(8'h02,prepare_abort_generation,prepare_abort_frame_id);end
    else begin
     abort_pending<=1;abort_slot<=prepare_abort_cache_slot;abort_generation<=prepare_abort_generation;abort_frame<=prepare_abort_frame_id;
     if(result_held&&prepared_cache_slot==prepare_abort_cache_slot)result_held<=0;
    end
   end
   if(abort_pending&&!inflight&&!dma_busy&&!lcd_busy)begin
    abort_pending<=0;abort_done<=1;p_active<=0;p_fail<=0;
    context_state[abort_slot]<=C_FREE;y_valid[abort_slot]<=0;c_valid[abort_slot]<=0;hud_valid[abort_slot]<=0;
    if(result_held&&prepared_cache_slot==abort_slot)result_held<=0;
   end
   if(descriptor_valid&&descriptor_ready)begin
    if(descriptor_generation==0||context_state[descriptor_cache_slot]!=C_READY||context_generation[descriptor_cache_slot]!=descriptor_generation||context_frame[descriptor_cache_slot]!=descriptor_frame_id||
       !hud_valid[descriptor_cache_slot]||(front_valid&&(descriptor_generation<=front_generation||descriptor_frame_id<=front_frame_id)))begin
     rejected_descriptors<=rejected_descriptors+1;note_fault(8'h20,descriptor_generation,descriptor_frame_id);
    end else begin pending_valid<=1;pending_slot<=descriptor_cache_slot;pending_generation<=descriptor_generation;pending_frame<=descriptor_frame_id;context_state[descriptor_cache_slot]<=C_PENDING;end
   end
   if(switch_now)begin
    if(front_valid)context_state[front_cache_slot]<=C_FREE;
    front_valid<=1;front_cache_slot<=pending_slot;front_generation<=pending_generation;front_frame_id<=pending_frame;front_next_u<=0;pending_valid<=0;
    context_state[pending_slot]<=C_FRONT;presented<=1;presented_count<=presented_count+1;f_active<=0;f_address_pending<=0;wanted_u_stage<=0;miss_seen<=0;
   end
   if(line_req_valid&&!line_req_ready&&front_valid&&(!miss_seen||miss_line!=line_req_line))begin line_cache_misses<=line_cache_misses+1;miss_seen<=1;miss_line<=line_req_line;end
   if(!line_req_valid)miss_seen<=0;
   if(line_req_valid&&line_req_ready)begin
    render_active<=1;render_black<=invalid_line||front_fault[front_cache_slot];render_fault<=0;render_slot<=front_cache_slot;render_u<=invalid_line?10'd0:requested_u;issue_count<=0;emit_count<=0;
    hud_ab_index<=15'(requested_u)-15'd22;hud_c_index<=15'd7680+15'(requested_u)-15'd168;hud_d_index<=15'd15360+15'(requested_u)-15'd168;
    if(invalid_line)begin front_fault[front_cache_slot]<=1;note_fault(8'h90,front_generation,front_frame_id);end
   end
   if(cache_rd_valid)begin
    issue_count<=issue_count+1;
    if(hud_hit)begin
     if(issue_count<106)hud_ab_index<=hud_ab_index+15'd160;
     else if(issue_count<384)hud_c_index<=hud_c_index+15'd320;
     else hud_d_index<=hud_d_index+15'd240;
    end
   end
   if(cache_valid&&cache_error)begin render_fault<=1;front_fault[render_slot]<=1;note_fault(8'h92,context_generation[render_slot],context_frame[render_slot]);end
   if(pixel_valid&&render_active&&bad_pixel_tag)begin render_fault<=1;front_fault[render_slot]<=1;note_fault(8'h93,context_generation[render_slot],context_frame[render_slot]);end
   if(line_data_valid)begin
    if(emit_count==479)begin render_active<=0;generated_lines<=generated_lines+1;front_next_u<=render_u==719?10'd0:render_u+10'd1;end
    else emit_count<=emit_count+1;
   end
   if(front_valid&&!f_active&&!fatal_dma&&!front_fault[front_cache_slot]&&refill_needed&&!refill_hazard&&!switch_now)begin
    f_active<=1;f_slot<=front_cache_slot;f_kind<=refill_kind;f_group<=refill_group;f_tile_y<=0;f_chunk<=0;f_address_pending<=1;
    if(refill_kind==0)y_valid[front_cache_slot][refill_group[0]]<=0;else c_valid[front_cache_slot][refill_group[0]]<=0;
   end
   if(dma_cmd_valid&&dma_cmd_ready)begin
    inflight<=1;dma_abort_sent<=0;inflight_front<=choose_front;inflight_slot<=command_slot;inflight_generation<=context_generation[command_slot];inflight_frame<=context_frame[command_slot];inflight_cookie<=next_cookie;next_cookie<=next_cookie+1;
   end
   if(next_cookie==32'hffffffff&&!fatal_dma)begin fatal_dma<=1;note_fault(8'h82,front_generation,front_frame_id);if(front_valid)front_fault[front_cache_slot]<=1;end
   if(dma_abort_valid&&dma_abort_ready)dma_abort_sent<=1;
   if(dma_abort_rejected)begin fatal_dma<=1;note_fault(8'h83,inflight_generation,inflight_frame);end
   if(dma_result_valid)begin
    inflight<=0;
    if(!inflight||dma_result_slot!=inflight_slot||dma_result_generation!=inflight_generation||dma_result_frame!=inflight_frame||dma_result_cookie!=inflight_cookie)begin
     fatal_dma<=1;memory_errors<=memory_errors+1;note_fault(8'h81,dma_result_generation,dma_result_frame);if(front_valid)front_fault[front_cache_slot]<=1;if(p_active)begin p_fail<=1;p_fail_reason<=8'h81;end
    end else if((abort_pending||incoming_abort)&&!inflight_front)begin
     // Identity-bound cancellation owns this provisional command; wait for
     // the common idle fence, then discard its entire cache context.
    end else if(dma_result_error||dma_result_aborted)begin
     memory_errors<=memory_errors+1;note_fault(8'h40|dma_result_reason,dma_result_generation,dma_result_frame);
     if(inflight_front)begin front_fault[inflight_slot]<=1;f_active<=0;if(render_active&&render_slot==inflight_slot)render_fault<=1;end
     else begin p_fail<=1;p_fail_reason<=8'h40|dma_result_reason;end
    end else if(inflight_front)begin
     if(f_chunk==3&&f_tile_y==(f_kind==0?59:29))begin
      if(f_kind==0)begin y_valid[f_slot][f_group[0]]<=1;y_tag[f_slot][f_group[0]]<=f_group;f_active<=0;end
      else if(f_kind==1)begin f_kind<=2;f_tile_y<=0;f_chunk<=0;f_tile_base<=page_start(2,f_group,context_canonical[f_slot]);end
      else begin c_valid[f_slot][f_group[0]]<=1;c_tag[f_slot][f_group[0]]<=f_group[5:0];f_active<=0;end
     end else if(f_chunk==3)begin f_chunk<=0;f_tile_y<=f_tile_y+1;f_tile_base<=f_tile_base+(f_kind==0?24'd2880:24'd1440);end
     else f_chunk<=f_chunk+1;
    end else begin
     if((p_phase==0&&p_hud_offset==21112)||(p_phase!=0&&p_chunk==3&&p_tile_y==(phase_kind(p_phase)==0?59:29)))begin
      if(p_phase==0)hud_valid[p_slot]<=1;
      if(p_phase==1||p_phase==2)begin y_valid[p_slot][phase_group(p_phase)]<=1;y_tag[p_slot][phase_group(p_phase)]<={6'd0,phase_group(p_phase)};end
      if(p_phase==4||p_phase==6)begin c_valid[p_slot][phase_group(p_phase)]<=1;c_tag[p_slot][phase_group(p_phase)]<={5'd0,phase_group(p_phase)};end
      if(p_phase==6)begin p_active<=0;context_state[p_slot]<=C_READY;result_held<=1;prepared_generation<=context_generation[p_slot];prepared_frame_id<=context_frame[p_slot];prepared_cache_slot<=p_slot;prepared_error<=0;prepared_reason<=0;end
      else begin p_phase<=p_phase+1;p_tile_y<=0;p_chunk<=0;p_hud_offset<=0;p_tile_base<=page_start(phase_kind(p_phase+3'd1),{6'd0,phase_group(p_phase+3'd1)},context_canonical[p_slot]);end
     end else if(p_phase==0)p_hud_offset<=p_hud_offset+15'd8;
     else if(p_chunk==3)begin p_chunk<=0;p_tile_y<=p_tile_y+1;p_tile_base<=p_tile_base+(phase_kind(p_phase)==0?24'd2880:24'd1440);end
     else p_chunk<=p_chunk+1;
    end
   end
   if(p_fail&&!inflight&&!dma_busy&&!lcd_busy&&!abort_pending)begin
    p_fail<=0;p_active<=0;context_state[p_slot]<=C_FREE;y_valid[p_slot]<=0;c_valid[p_slot]<=0;hud_valid[p_slot]<=0;
    result_held<=1;prepared_generation<=context_generation[p_slot];prepared_frame_id<=context_frame[p_slot];prepared_cache_slot<=p_slot;prepared_error<=1;prepared_reason<=p_fail_reason;
   end
  end
 end
endmodule
`default_nettype wire
