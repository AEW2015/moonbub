`timescale 1ns/1ps
`default_nettype none
// Restricted exact CP23 fixture composition, offline diagnostic only.
// One immutable first front; no live protocol/ACK, arbitrary payload or reference path.
module cp23_key_composite_scanout #(
 parameter[23:0]FIRST_BASE=24'h100000,
 parameter[63:0]FIRST_OWNER=64'h123456789abcdef0
)(
 input wire clk,read_clk,pixel_clk,reset,pixel_reset_n,
 input wire start_valid,output wire start_ready,
 input wire payload_valid,output wire payload_ready,input wire[7:0]payload_byte,input wire payload_last,
 input wire sample_enable,abort_job,
 output reg base_qualified,front_valid,output reg[31:0]promotion_count,
 output reg qualified_pulse,promoted_pulse,released_pulse,
 output wire job_active_out,output wire[31:0]lcd_underruns,output wire frame_boundary,
 output wire[7:0]red,green,blue,output wire hsync,vsync,data_enable,output wire[9:0]physical_x,physical_y,
 output wire[12:0]sdram_a,output wire[1:0]sdram_bs,inout wire[15:0]sdram_dq,
 output wire sdram_clk,output wire[1:0]sdram_cke,sdram_cs_n,
 output wire sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm
);
 localparam WORDS=259200;
 reg job_active,ever_started,release_pending,release_success;reg[31:0]cycles,hud_stored;
 wire js,sr,ts,sv,store_ready,cv,checked,jq,jabort_rejected;
 wire[7:0]sample,join_code;wire[1:0]sample_plane,hud_rect;
 wire[15:0]sample_x,sample_y,hud_word,hud_index,hud_x,hud_y;
 wire sample_last,hud_valid,hud_ready;
 wire[63:0]sample_owner,completion_owner;wire[31:0]sample_epoch,sample_frame,sample_gen,completion_epoch,completion_frame,completion_gen;
 wire[127:0]completion_tag,hud_tag;wire[3:0]key_stage;wire[31:0]staged_bytes,join_yuv,join_hud;
 wire ack,pub,cap;
 wire failed,aborted,done,tdone,tfailed,taborted,raw_idle,joined_idle;
 wire[63:0]store_owner,transpose_owner;wire[3:0]store_error,store_state,transpose_error,transpose_state;
 wire[31:0]accepted_bytes,accepted_words,fifo_enqueued,fifo_dequeued,fifo_occupancy,fifo_high_water;
 wire[31:0]transpose_inputs,transpose_processed,transpose_outputs,transpose_high_water;
 wire old_pixel_valid,old_pixel_ready,old_flush,old_discard;wire[23:0]old_pixel_address;wire[15:0]old_pixel_data;
 wire pixel_valid,pixel_ready,flush,discard;wire[23:0]pixel_address;wire[15:0]pixel_data;
 wire join_failed=cv&&!checked;
 wire stop_job=job_active&&abort_job;
 wire boundary_fault=word_stage_fault||hud_stage_fault;
 reg boundary_abort_sent,join_result_seen;
 wire boundary_abort_request=job_active&&!join_result_seen&&!boundary_abort_sent&&(boundary_fault||word_discard_q);
 always @(posedge clk)begin
  if(reset||go||retire||!job_active)begin boundary_abort_sent<=0;join_result_seen<=0;end
  else begin
   if(cv)join_result_seen<=1;
   if(stop_job||boundary_abort_request)boundary_abort_sent<=1;
  end
 end
 wire matching_completion=cv&&checked&&completion_owner==FIRST_OWNER&&completion_epoch==1&&completion_frame==0&&completion_gen==1&&
  completion_tag==128'hb74b12e10009cfccbcb5363d13edc4ee&&hud_tag==128'h1026aab8b7df606614f560a966806641;
 wire all_counts=accepted_bytes==518400&&accepted_words==WORDS&&transpose_inputs==WORDS&&transpose_processed==518400&&transpose_outputs==WORDS&&hud_stored==21120&&!yuv_stage_valid&&!word_stage_valid&&!hud_stage_valid&&!word_discard_q&&!boundary_fault;
 wire good_done=job_active&&done&&tdone&&matching_completion&&all_counts&&joined_idle;
 wire failed_done=job_active&&cv&&(join_failed||failed||aborted)&&(done||failed||aborted)&&(tdone||tfailed||taborted)&&joined_idle&&!word_stage_valid&&!hud_stage_valid&&(word_discard_q||!old_discard);
 wire retire=good_done||failed_done;
 assign job_active_out=job_active;
 assign start_ready=!ever_started&&!job_active&&js&&sr&&ts&&!reset&&!abort_job;
 // Offer to the decoder independently of its own READY, avoiding a
 // combinational READY->VALID->incoming-cancel->READY feedback path.
 wire key_offer=start_valid&&!ever_started&&!job_active&&sr&&ts&&!reset&&!abort_job;
 wire go=key_offer&&js;
 // One bounded canonical-byte ownership stage, breaking decoder metadata/valid
 // from the private store/transpose/controller combinational acceptance path.
 wire raw_sv,raw_last;wire[7:0]raw_sample;wire[1:0]raw_plane;
 wire[15:0]raw_x,raw_y;wire[63:0]raw_owner;wire[31:0]raw_epoch,raw_frame,raw_gen;
 reg yuv_stage_valid;reg[202:0]yuv_stage_tuple;
 wire yuv_stage_ready=!yuv_stage_valid||(store_ready&&sample_enable);
 assign sv=yuv_stage_valid;
 assign {sample_owner,sample_epoch,sample_frame,sample_gen,sample,sample_plane,sample_x,sample_y,sample_last}=yuv_stage_tuple;
 always @(posedge clk)begin
  if(reset||go||stop_job||join_failed||failed||aborted||tfailed||taborted||boundary_fault||word_discard_q)yuv_stage_valid<=0;
  else if(yuv_stage_ready)begin
   yuv_stage_valid<=raw_sv;
   if(raw_sv)yuv_stage_tuple<={raw_owner,raw_epoch,raw_frame,raw_gen,raw_sample,raw_plane,raw_x,raw_y,raw_last};
  end
 end
 cp23_key_private_join key(.clk(clk),.reset(reset),.start_valid(key_offer),.start_ready(js),.start_owner(FIRST_OWNER),.start_epoch(32'd1),.start_frame(32'd0),.start_generation(32'd1),.start_bytes(32'd17412),
  .in_valid(payload_valid&&job_active),.in_ready(payload_ready),.in_byte(payload_byte),.in_last(payload_last),
  .abort_valid(stop_job||boundary_abort_request),.abort_owner(FIRST_OWNER),.abort_epoch(32'd1),.abort_frame(32'd0),.abort_rejected(jabort_rejected),
  .yuv_valid(raw_sv),.yuv_ready(yuv_stage_ready),.yuv_sample(raw_sample),.yuv_plane(raw_plane),.yuv_x(raw_x),.yuv_y(raw_y),.yuv_last(raw_last),
  .hud_valid(hud_valid),.hud_ready(hud_ready),.hud_word(hud_word),.hud_index(hud_index),.hud_x(hud_x),.hud_y(hud_y),.hud_rect(hud_rect),
  .output_owner(raw_owner),.output_epoch(raw_epoch),.output_frame(raw_frame),.output_generation(raw_gen),
  .result_valid(cv),.result_ready(retire),.result_owner(completion_owner),.result_epoch(completion_epoch),.result_frame(completion_frame),.result_generation(completion_gen),
  .candidate_checked(checked),.result_stage(key_stage),.result_code(join_code),.base_tag(completion_tag),.hud_tag(hud_tag),.stored_bytes(staged_bytes),.yuv_words(join_yuv),.hud_words(join_hud),
  .ack_valid(ack),.publication_valid(pub),.profile_advertised(cap),.child_quiescent(jq));
 ar03_yuv_elastic #(.DEPTH(512),.APERTURE_WORDS(524288)) store(.clk(clk),.reset(reset),.start_valid(go),.start_ready(sr),
  .start_owner(FIRST_OWNER),.start_epoch(32'd1),.start_frame(32'd0),.start_base(FIRST_BASE),
  .in_valid(sv&&sample_enable),.in_ready(store_ready),.in_byte(sample),.in_owner(sample_owner),.in_epoch(sample_epoch),.in_frame(sample_frame),.in_last(sample_last),
  .abort(stop_job),.fault(join_failed||tfailed||boundary_fault),.completion_valid(cv&&checked),.completion_owner(completion_owner),.completion_epoch(completion_epoch),.completion_frame(completion_frame),
  .release_valid(retire),.release_owner(FIRST_OWNER),.release_epoch(32'd1),.release_frame(32'd0),
  .pixel_valid(old_pixel_valid),.pixel_ready(old_pixel_ready),.pixel_address(old_pixel_address),.pixel_data(old_pixel_data),.force_flush(old_flush),.discard(old_discard),.memory_idle(joined_idle),
  .busy(),.done(done),.failed(failed),.aborted(aborted),.owner(store_owner),.accepted_bytes(accepted_bytes),.accepted_words(accepted_words),.error_code(store_error),.state(store_state),
  .enqueued(fifo_enqueued),.dequeued(fifo_dequeued),.occupancy(fifo_occupancy),.high_water(fifo_high_water));
 // One complete private word reservation. Private upstream discard is
 // observed one clock later; at most one already-valid staged word can drain
 // on that observation edge. Incoming errored/invalid words never handshake.
 reg word_stage_valid,word_discard_q,word_stage_fault;
 reg[167:0]word_stage_tuple;reg[31:0]word_captured;
 wire[63:0]word_owner;wire[31:0]word_epoch,word_frame;
 wire[23:0]word_address;wire[15:0]word_data;
 assign {word_owner,word_epoch,word_frame,word_address,word_data}=word_stage_tuple;
 wire word_forward_ready;
 wire word_forward_valid=word_stage_valid&&!reset&&!stop_job&&!word_discard_q&&!word_stage_fault;
 wire word_stage_ready=!word_stage_valid||word_forward_ready;
 wire word_offer_ok=store_owner==FIRST_OWNER&&old_pixel_address==FIRST_BASE+word_captured&&word_captured<WORDS;
 assign old_pixel_ready=word_stage_ready&&word_offer_ok&&job_active&&!reset&&!stop_job&&!old_discard&&!word_discard_q&&!boundary_fault;
 wire word_capture=old_pixel_valid&&old_pixel_ready;
 wire word_forward=word_forward_valid&&word_forward_ready;
 wire word_flush=old_flush&&(!word_stage_valid||word_forward)&&!word_discard_q&&!word_stage_fault;
 always @(posedge clk)begin
  if(reset||go||retire||release_pending||!job_active)begin
   word_stage_valid<=0;word_discard_q<=0;word_stage_fault<=0;word_captured<=0;
  end else begin
   word_discard_q<=old_discard;
   if(old_pixel_valid&&word_stage_ready&&!old_discard&&!stop_job&&!word_offer_ok)word_stage_fault<=1;
   if(stop_job||old_discard||join_failed||failed||aborted||tfailed||taborted||boundary_fault)word_stage_valid<=0;
   else if(word_stage_ready)begin
    word_stage_valid<=word_capture;
    if(word_capture)begin word_stage_tuple<={store_owner,32'd1,32'd0,old_pixel_address,old_pixel_data};word_captured<=word_captured+1;end
   end
  end
 end
 ar03_yuv_transpose #(.BANKS(2),.APERTURE_WORDS(524288)) transpose(.clk(clk),.reset(reset),.start_valid(go),.start_ready(ts),
  .start_owner(FIRST_OWNER),.start_epoch(32'd1),.start_frame(32'd0),.start_width(16'd720),.start_height(16'd480),.start_base(FIRST_BASE),
  .in_valid(word_forward_valid),.in_ready(word_forward_ready),.in_address(word_address),.in_data(word_data),.in_owner(word_owner),.in_epoch(word_epoch),.in_frame(word_frame),
  .upstream_flush(word_flush),.upstream_discard(word_discard_q||word_stage_fault),.abort(stop_job),.fault(join_failed||hud_stage_fault),
  .pixel_valid(pixel_valid),.pixel_ready(pixel_ready),.pixel_address(pixel_address),.pixel_data(pixel_data),.force_flush(flush),.discard(discard),.memory_idle(raw_idle),
  .store_idle(joined_idle),.done(tdone),.failed(tfailed),.aborted(taborted),.release_valid(retire),.release_owner(FIRST_OWNER),.release_epoch(32'd1),.release_frame(32'd0),
  .owner(transpose_owner),.input_words(transpose_inputs),.processed_bytes(transpose_processed),.output_words(transpose_outputs),.stripe_high_water(transpose_high_water),.error_code(transpose_error),.state(transpose_state));
 // Fixed exact-fixture rectangle layout; only freshly written candidate words
 // become visible after the complete joint integrity and physical drain gate.
 (* ram_style="block" *)reg[15:0]hud_ram[0:21119];
 // Producer READY has no tuple/identity/index dependence and no bypass.
 // The RAM consumer applies the original freshness gate to the captured tuple.
 reg hud_stage_valid,hud_stage_fault;reg[225:0]hud_stage_tuple;
 wire[63:0]hs_owner;wire[31:0]hs_epoch,hs_frame,hs_gen;
 wire[15:0]hs_word,hs_index,hs_x,hs_y;wire[1:0]hs_rect;
 assign {hs_owner,hs_epoch,hs_frame,hs_gen,hs_word,hs_index,hs_x,hs_y,hs_rect}=hud_stage_tuple;
 wire[15:0]hud_base=hs_rect==0?16'd0:hs_rect==1?16'd3840:hs_rect==2?16'd7680:16'd15360;
 wire[15:0]hud_limit=hs_rect<2?16'd3840:hs_rect==2?16'd7680:16'd5760;
 wire hud_identity=hs_owner==FIRST_OWNER&&hs_epoch==1&&hs_frame==0&&hs_gen==1;
 wire hud_tuple_ok=hud_identity&&hs_index<hud_limit&&hud_base+hs_index==hud_stored;
 assign hud_ready=!hud_stage_valid&&job_active&&!reset&&!stop_job&&!join_failed&&!boundary_fault;
 wire hud_capture=hud_valid&&hud_ready;
 wire hud_consume=hud_stage_valid&&job_active&&!reset&&!stop_job&&!join_failed&&!boundary_fault&&hud_tuple_ok;
 always @(posedge clk)begin
  if(reset||go||retire||release_pending||!job_active)begin hud_stage_valid<=0;hud_stage_fault<=0;end
  else begin
   if(hud_stage_valid&&!hud_tuple_ok&&!stop_job&&!join_failed)hud_stage_fault<=1;
   if(stop_job||join_failed||failed||aborted||tfailed||taborted||boundary_fault)hud_stage_valid<=0;
   else if(hud_consume)hud_stage_valid<=0;
   else if(hud_capture)begin hud_stage_valid<=1;hud_stage_tuple<={raw_owner,raw_epoch,raw_frame,raw_gen,hud_word,hud_index,hud_x,hud_y,hud_rect};end
  end
 end
 always @(posedge clk)if(hud_consume)hud_ram[hud_base+hs_index]<=hs_word;
 wire base_line_valid;wire[15:0]base_line_data;wire[9:0]base_x;wire[8:0]base_y;
 wire h0=base_x>=22&&base_x<182&&base_y>=54&&base_y<78;
 wire h1=base_x>=22&&base_x<182&&base_y>=82&&base_y<106;
 wire h2=base_x>=168&&base_x<488&&base_y>=360&&base_y<384;
 wire h3=base_x>=168&&base_x<408&&base_y>=390&&base_y<414;
 wire hud_hit=h0||h1||h2||h3;
 wire[15:0]hud_address=h0?(base_y-54)*160+base_x-22:h1?3840+(base_y-82)*160+base_x-22:h2?7680+(base_y-360)*320+base_x-168:15360+(base_y-390)*240+base_x-168;
 reg overlay_valid,overlay_hit;reg[15:0]overlay_base,overlay_hud;
 wire line_data_valid=overlay_valid;wire[15:0]line_data=overlay_hit?overlay_hud:overlay_base;
 always @(posedge clk)begin
  if(reset||!base_qualified)begin overlay_valid<=0;overlay_hit<=0;end
  else begin
   overlay_valid<=base_line_valid;
   if(base_line_valid)begin overlay_base<=base_line_data;overlay_hit<=hud_hit;if(hud_hit)overlay_hud<=hud_ram[hud_address];end
  end
 end
 wire gather_reset=reset||!base_qualified;
 wire primed,display_valid;
 wire[63:0]display_owner;wire[31:0]display_epoch,display_frame,display_token;
 wire line_req_valid,line_req_ready;wire[23:0]line_req_address;
 wire request_valid,request_ready,request_rejected,response_valid,response_ready;
 wire[63:0]request_owner,response_owner;wire[31:0]request_epoch,request_frame,request_sequence,response_epoch,response_frame,response_sequence;
 wire[23:0]request_address;wire[127:0]response_data;wire[1:0]response_status;wire[3:0]response_words;
 wire[31:0]gather_requests,gather_responses,gather_faults,gather_lines;
 ar03_yuv_line_gather #(.Y_BASE(FIRST_BASE),.OWNER(FIRST_OWNER),.EPOCH(1),.FRAME(0)) gather(.clk(clk),.reset(gather_reset),
  .display_valid(display_valid),.display_owner(display_owner),.display_epoch(display_epoch),.display_frame(display_frame),.display_token(display_token),
  .line_req_valid(line_req_valid),.line_req_ready(line_req_ready),.line_req_address(line_req_address),.line_data_valid(base_line_valid),.line_data(base_line_data),.pixel_x(base_x),.pixel_y(base_y),.primed(primed),
  .request_valid(request_valid),.request_ready(request_ready),.request_rejected(request_rejected),.request_owner(request_owner),.request_epoch(request_epoch),.request_frame(request_frame),.request_sequence(request_sequence),.request_address(request_address),
  .response_valid(response_valid),.response_ready(response_ready),.response_data(response_data),.response_owner(response_owner),.response_epoch(response_epoch),.response_frame(response_frame),.response_sequence(response_sequence),.response_status(response_status),.response_words(response_words),
  .requests(gather_requests),.responses(gather_responses),.protocol_faults(gather_faults),.completed_lines(gather_lines));
 wire owned_quiescent;
 ar03_memory_owned #(.YUV_WORDS(524288)) memory(.clk(clk),.read_clk(read_clk),.reset(reset),
  .display_valid(display_valid),.display_owner(display_owner),.display_epoch(display_epoch),.display_frame(display_frame),.display_token(display_token),
  .pixel_valid(pixel_valid),.pixel_ready(pixel_ready),.pixel_address(pixel_address),.pixel_data(pixel_data),.force_flush(flush),.discard(discard),
  .line_req_valid(1'b0),.line_req_address(24'd0),
  .request_valid(request_valid),.request_ready(request_ready),.request_rejected(request_rejected),.request_owner(request_owner),.request_epoch(request_epoch),.request_frame(request_frame),.request_sequence(request_sequence),.request_address(request_address),
  .cancel_valid(1'b0),.cancel_owner(64'd0),.cancel_epoch(32'd0),.cancel_frame(32'd0),.cancel_sequence(32'd0),.client_fault(1'b0),
  .response_valid(response_valid),.response_ready(response_ready),.response_data(response_data),.response_owner(response_owner),.response_epoch(response_epoch),.response_frame(response_frame),.response_sequence(response_sequence),.response_status(response_status),.response_words(response_words),
  .owned_quiescent(owned_quiescent),.physical_idle(raw_idle),
  .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),.sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),.sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),.sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));
 wire frame_origin;
 moonshine_lcd_720p lcd(.pixel_clk(pixel_clk),.reset_n(pixel_reset_n),.mem_clk(clk),.mem_reset(reset),
  .front_valid(front_valid),.front_buffer(1'b0),.pattern_enable(1'b0),.front_720p(1'b0),.display_margin(7'd13),.frame_origin(frame_origin),
  .timing_hsync(10'd4),.timing_vsync(10'd4),.timing_hstart(10'd14),.timing_vstart(10'd24),.timing_htotal(10'd541),.timing_vtotal(10'd834),
  .line_req_valid(line_req_valid),.line_req_ready(line_req_ready),.line_req_address(line_req_address),.line_data_valid(line_data_valid),.line_data(line_data),
  .frame_boundary(frame_boundary),.underruns(lcd_underruns),.hsync(hsync),.vsync(vsync),.data_enable(data_enable),.physical_x(physical_x),.physical_y(physical_y),.red(red),.green(green),.blue(blue));

 always @(posedge clk)begin
  if(reset)begin job_active<=0;ever_started<=0;release_pending<=0;release_success<=0;cycles<=0;hud_stored<=0;base_qualified<=0;front_valid<=0;promotion_count<=0;qualified_pulse<=0;promoted_pulse<=0;released_pulse<=0;end
  else begin
   cycles<=cycles+1;qualified_pulse<=0;promoted_pulse<=0;released_pulse<=0;
   if(go)begin job_active<=1;ever_started<=1;hud_stored<=0;end
   if(hud_consume)hud_stored<=hud_stored+1;
   if(retire)begin release_pending<=1;release_success<=good_done;end
   if(release_pending&&abort_job)release_success<=0;
   // A release request is not release completion. Wait for all real writer
   // components to acknowledge idle/readiness and discard their held result.
   if(release_pending&&sr&&ts&&js&&!cv&&jq&&store_owner==0&&transpose_owner==0&&joined_idle&&raw_idle&&!word_stage_valid&&!hud_stage_valid&&!word_discard_q)begin
    release_pending<=0;job_active<=0;released_pulse<=1;
    if(release_success&&!abort_job)begin base_qualified<=1;qualified_pulse<=1;end
   end
   if(frame_boundary&&base_qualified&&primed&&!front_valid)begin front_valid<=1;promotion_count<=promotion_count+1;promoted_pulse<=1;end
  end
 end
endmodule
`default_nettype wire
