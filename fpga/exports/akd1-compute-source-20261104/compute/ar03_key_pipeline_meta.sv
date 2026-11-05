// Private KEY pre-HUD YUV candidate path. No AF03/reference publication.
module ar03_key_pipeline_meta #(parameter [31:0] INITIAL_TOKEN=1)(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,input wire[63:0] start_owner,
 input wire[31:0] start_bytes,start_epoch,
 input wire in_valid,output wire in_ready,input wire[7:0] in_byte,input wire in_last,
 output wire candidate_valid,input wire candidate_ready,output wire[7:0] candidate_sample,
 output wire[63:0] candidate_owner,output wire[31:0] candidate_epoch,candidate_frame,candidate_block,
 output wire[1:0] candidate_plane,output wire[15:0] candidate_x,candidate_y,
 output wire meta_valid,input wire meta_ready,
 output wire[63:0] meta_owner,output wire[31:0] meta_epoch,meta_frame,
 output reg[15:0] meta_width,meta_height,output reg[127:0] meta_stored_tag,
 output wire completion_valid,input wire completion_ready,
 output wire[63:0] completion_owner,output wire[31:0] completion_epoch,completion_frame,
 output wire error_valid,input wire error_ready,output reg[3:0] error_stage,output reg[7:0] error_code,
 output wire[63:0] error_owner
);
 localparam IDLE=0,ENVELOPE=1,GM_START=2,GM_REPLAY=3,GM_CERT=4,
 PLANE_START=5,PLANE_REPLAY=6,PLANE_WAIT=7,RETIRE=8,COMPLETE=9,FAIL=10,META=11;
 reg[3:0] state;
 reg[63:0] owner;
 reg[31:0] epoch,frame,token,next_token,request_count,response_count;
 reg[1:0] plane;
 reg env_retired,map_retired;
 wire cancel=abort||state==FAIL;
 wire running=state==PLANE_START||state==PLANE_REPLAY||state==PLANE_WAIT;
 wire streaming=state==GM_REPLAY||state==PLANE_REPLAY;
 wire ev,er,eir,ee,eqr,ersv,erse,ert;
 wire[3:0] ecode;
 wire[63:0] eo,erso;
 wire[31:0] ep,ef,eref,eninner,ers_epoch,unused_expected;
 wire[7:0] eflags,unused_rb,unused_db;
 wire[127:0] unused_tag,unused_stored,unused_po,unused_pl;
 wire[31:0]unused_patch,unused_blob;wire[2:0]unused_count;wire unused_checked;
 wire[7:0]ers_data;
 wire env_start=start_valid&&state==IDLE&&next_token!=0&&next_token!=32'hffffffff;
 wire env_cert_ready=state==ENVELOPE&&ev&&eflags==1&&eo==owner;
 wire gm_start_ready,gm_in_ready,gv,ge,gqr,gbv,gbe,grt;
 wire[3:0]gcode;wire[63:0]go,geo,gbo;wire[31:0]gp,gf,gref,gnmap,gbep,gbindex;
 wire gkey;wire[15:0]gw,gh,gbx,gby;wire[95:0]g_offsets,g_lengths;wire[47:0]g_bws,g_bhs;
 wire[1:0]gbplane;wire[5:0]gbscale;
 wire[31:0]plane_offset=g_offsets[plane*32+:32],plane_length=g_lengths[plane*32+:32];
 wire[15:0]bw=g_bws[plane*16+:16],bh=g_bhs[plane*16+:16];
 // Capture all full-width products at the validated GM certificate. Plane
 // selection must not feed a multiplier on each map-request capture enable.
 reg[95:0]cached_block_counts;
 wire[31:0]nblocks=cached_block_counts[plane*32+:32];
 wire[15:0]pw=plane==0?gw:(gw>>1),ph=plane==0?gh:(gh>>1);
 wire[31:0]replay_length=state==GM_REPLAY?eninner:plane_length;
 wire[31:0]replay_base=state==GM_REPLAY?32'd61:32'd61+plane_offset;
 wire response_identity=erso==owner&&ers_epoch==epoch&&!erse;
 wire target_ready=state==GM_REPLAY?gm_in_ready:j_in_ready;
 wire replay_response_ready=streaming&&target_ready&&response_identity;
 wire replay_response_valid=streaming&&ersv&&response_identity;
 wire replay_last=response_count==replay_length-1;
 ar03_envelope envelope(
  .clk(clk),.reset(reset),.abort(cancel),.start_valid(env_start),.start_ready(er),
  .start_owner(start_owner),.start_bytes(start_bytes),.start_check_epoch(1'b1),.start_expected_epoch(start_epoch),
  .in_valid(in_valid&&state==ENVELOPE),.in_ready(eir),.in_data(in_byte),.in_last(in_last),
  .envelope_validated(ev),.envelope_ready(env_cert_ready),.desc_owner(eo),.desc_epoch(ep),.desc_frame(ef),
  .desc_expected_epoch(unused_expected),.desc_epoch_checked(unused_checked),.desc_flags(eflags),
  .desc_reference_bank(unused_rb),.desc_destination_bank(unused_db),.desc_reference_id(eref),.desc_inner_bytes(eninner),
  .desc_patch_bytes(unused_patch),.desc_reference_tag(unused_tag),.desc_stored_tag(unused_stored),
  .desc_patch_count(unused_count),.desc_patch_blob_offset(unused_blob),.desc_patch_offsets(unused_po),.desc_patch_lengths(unused_pl),
  .error_valid(ee),.error_ready(1'b0),.error_code(ecode),
  .rd_req_valid(streaming&&request_count<replay_length),.rd_req_ready(eqr),.rd_req_address(replay_base+request_count),
  .rd_req_owner(owner),.rd_req_epoch(epoch),.rd_rsp_valid(ersv),.rd_rsp_ready(replay_response_ready),
  .rd_rsp_data(ers_data),.rd_rsp_error(erse),.rd_rsp_owner(erso),.rd_rsp_epoch(ers_epoch),
  .retire_valid(state==RETIRE&&!env_retired),.retire_ready(ert),.retire_owner(owner),.retire_epoch(epoch));
 reg map_wait,prefetch_valid;
 reg[15:0]next_x,next_y,prefetch_x,prefetch_y,pending_x,pending_y;
 reg[31:0]next_block,prefetch_block,pending_block;
 reg[5:0]prefetch_scale,current_scale;
 wire map_req=running&&!map_wait&&!prefetch_valid&&next_block<nblocks;
 wire map_ready=running&&map_wait&&!prefetch_valid;
 wire map_identity=gbo==owner&&gbep==epoch&&gbplane==plane&&gbx==pending_x&&gby==pending_y&&gbindex==pending_block&&!gbe;
 gm01_sections sections(
  .clk(clk),.reset(reset),.abort(cancel),.start_valid(state==GM_START),.start_ready(gm_start_ready),
  .start_owner(owner),.start_bytes(eninner),.start_epoch(epoch),.start_frame(frame),.start_reference(eref),.start_key(1'b1),
  .in_valid(replay_response_valid&&state==GM_REPLAY),.in_ready(gm_in_ready),.in_data(ers_data),.in_last(replay_last),
  .inner_sections_validated(gv),.certificate_ready(state==GM_CERT),.desc_owner(go),.desc_epoch(gp),.desc_frame(gf),.desc_reference(gref),
  .desc_key(gkey),.desc_width(gw),.desc_height(gh),.desc_map_bytes(gnmap),.desc_plane_offsets(g_offsets),.desc_plane_lengths(g_lengths),.desc_blocks_w(g_bws),.desc_blocks_h(g_bhs),
  .error_valid(ge),.error_ready(1'b0),.error_code(gcode),.error_owner(geo),
  .block_req_valid(map_req),.block_req_ready(gqr),.block_req_owner(owner),.block_req_epoch(epoch),.block_req_plane(plane),.block_req_x(next_x),.block_req_y(next_y),
  .block_valid(gbv),.block_ready(map_ready),.block_error(gbe),.block_owner(gbo),.block_epoch(gbep),.block_plane(gbplane),.block_x(gbx),.block_y(gby),.block_index(gbindex),.block_scale(gbscale),
  .retire_valid(state==RETIRE&&!map_retired),.retire_ready(grt),.retire_owner(owner),.retire_epoch(epoch));
 wire j_start_ready,j_in_ready,j_tile_ready,j_valid,j_done,j_error,j_last;
 wire[4:0]j_error_code;
 wire[31:0]j_owner,j_epoch,j_block,j_coefficient_block;
 wire[1:0]j_plane;wire[15:0]j_x,j_y;
 wire[5:0]j_index,j_coefficient_index;wire[7:0]j_sample,j_bank;
 wire tile_identity=j_coefficient_block==prefetch_block;
 wire tile_valid=running&&prefetch_valid&&tile_identity;
 wire tile_accept=tile_valid&&j_tile_ready;
 wire[15:0]tile_x=prefetch_x<<3,tile_y=prefetch_y<<3;
 wire[3:0]tile_cols=pw-tile_x>=8?4'd8:pw-tile_x;
 wire[3:0]tile_rows=ph-tile_y>=8?4'd8:ph-tile_y;
 reg[7:0]quantizers[0:383];initial $readmemh("quantizers.hex",quantizers);
 wire[8:0]quantizer_base=(plane==0?9'd0:9'd192)+(current_scale==8?9'd0:current_scale==16?9'd64:9'd128);
 wire[7:0]quant_factor=quantizers[quantizer_base+{3'b0,j_coefficient_index}];
 wire sample_identity=j_owner==token&&j_epoch==epoch&&j_plane==plane;
 wire child_error=ee||ge||j_error;
 cp02_key_join #(.MAX_BYTES(65536),.MAX_BLOCKS(8192)) key_join(
  .clk(clk),.reset(reset),.abort(cancel),.start_valid(state==PLANE_START),.start_ready(j_start_ready),
  .start_owner(token),.start_epoch(epoch),.start_block_base(32'd0),.start_bytes(plane_length),.start_blocks(nblocks),.start_width(bw),.start_plane(plane),
  .in_valid(replay_response_valid&&state==PLANE_REPLAY),.in_ready(j_in_ready),.in_byte(ers_data),.in_last(replay_last),
  .tile_valid(tile_valid),.tile_ready(j_tile_ready),.tile_bank(8'd0),.tile_x(tile_x),.tile_y(tile_y),.tile_rows(tile_rows),.tile_cols(tile_cols),.quant_factor(quant_factor),
  .coefficient_block(j_coefficient_block),.coefficient_index(j_coefficient_index),
  .out_valid(j_valid),.out_ready(candidate_ready&&running&&sample_identity&&!child_error&&!reset&&!abort),
  .out_sample(j_sample),.out_owner(j_owner),.out_epoch(j_epoch),.out_block(j_block),.out_plane(j_plane),.out_bank(j_bank),.out_x(j_x),.out_y(j_y),.out_index(j_index),.out_last(j_last),
  .done_valid(j_done),.done_ready(state==PLANE_WAIT),.error_valid(j_error),.error_ready(1'b0),.error_code(j_error_code));
 assign start_ready=state==IDLE&&er&&!reset&&!abort;
 assign in_ready=state==ENVELOPE&&eir&&!reset&&!abort;
 assign candidate_valid=running&&j_valid&&sample_identity&&!child_error&&!reset&&!abort;
 assign candidate_sample=j_sample;assign candidate_owner=owner;assign candidate_epoch=epoch;assign candidate_frame=frame;
 assign candidate_plane=j_plane;assign candidate_block=j_block;
 assign candidate_x=j_x+{13'b0,j_index[2:0]};assign candidate_y=j_y+{13'b0,j_index[5:3]};
 assign meta_valid=state==META&&!reset&&!abort;
 assign meta_owner=owner;assign meta_epoch=epoch;assign meta_frame=frame;
 assign completion_valid=state==COMPLETE&&!reset&&!abort;
 assign completion_owner=owner;assign completion_epoch=epoch;assign completion_frame=frame;
 assign error_valid=state==FAIL&&!reset&&!abort;assign error_owner=owner;
 always @(posedge clk)begin
  if(reset)begin
   state<=IDLE;owner<=0;epoch<=0;frame<=0;token<=0;next_token<=INITIAL_TOKEN;
   request_count<=0;response_count<=0;plane<=0;env_retired<=0;map_retired<=0;
   map_wait<=0;prefetch_valid<=0;next_x<=0;next_y<=0;next_block<=0;current_scale<=8;
   error_stage<=0;error_code<=0;meta_width<=0;meta_height<=0;meta_stored_tag<=0;
   cached_block_counts<=0;
  end else if(abort)begin
   state<=IDLE;map_wait<=0;prefetch_valid<=0;request_count<=0;response_count<=0;
   cached_block_counts<=0;
  end else begin
   if(map_req&&gqr)begin map_wait<=1;pending_x<=next_x;pending_y<=next_y;pending_block<=next_block;end
   if(gbv&&map_ready)begin
    map_wait<=0;prefetch_valid<=1;prefetch_scale<=gbscale;prefetch_x<=gbx;prefetch_y<=gby;prefetch_block<=gbindex;
   end
   if(tile_accept)begin
    current_scale<=prefetch_scale;prefetch_valid<=0;next_block<=next_block+1;
    if(next_x==bw-1)begin next_x<=0;next_y<=next_y+1;end else next_x<=next_x+1;
   end
   if(streaming&&request_count<replay_length&&eqr)request_count<=request_count+1;
   if(ersv&&replay_response_ready)response_count<=response_count+1;
   if(state!=IDLE&&state!=FAIL&&state!=COMPLETE&&(child_error||(ersv&&streaming&&!response_identity)||
      (gbv&&map_ready&&!map_identity)||(j_valid&&running&&!sample_identity)||
      (running&&prefetch_valid&&j_tile_ready&&!tile_identity)))begin
    state<=FAIL;error_stage<=ee?2:ge?3:j_error?4:5;error_code<=ee?{4'b0,ecode}:ge?{4'b0,gcode}:j_error?{3'b0,j_error_code}:8'd1;
   end else case(state)
    IDLE:if(start_valid&&start_ready)begin
     owner<=start_owner;epoch<=start_epoch;request_count<=0;response_count<=0;map_wait<=0;prefetch_valid<=0;plane<=0;
     cached_block_counts<=0;
     if(next_token==0||next_token==32'hffffffff)begin state<=FAIL;error_stage<=1;error_code<=3;end
     else begin token<=next_token;next_token<=next_token+1;state<=ENVELOPE;end
    end
    ENVELOPE:if(ev)begin
     if(eflags!=1||eo!=owner||ep!=epoch)begin state<=FAIL;error_stage<=1;error_code<=1;end
     else begin frame<=ef;meta_stored_tag<=unused_stored;state<=GM_START;end
    end
    GM_START:if(gm_start_ready)begin state<=GM_REPLAY;request_count<=0;response_count<=0;end
    GM_REPLAY:if(ersv&&replay_response_ready&&replay_last)state<=GM_CERT;
    GM_CERT:if(gv)begin
     if(go!=owner||gp!=epoch||gf!=frame||!gkey)begin state<=FAIL;error_stage<=5;error_code<=2;end
     else begin
      cached_block_counts[0+:32]<={16'b0,g_bws[0+:16]}*{16'b0,g_bhs[0+:16]};
      cached_block_counts[32+:32]<={16'b0,g_bws[16+:16]}*{16'b0,g_bhs[16+:16]};
      cached_block_counts[64+:32]<={16'b0,g_bws[32+:16]}*{16'b0,g_bhs[32+:16]};
      state<=META;meta_width<=gw;meta_height<=gh;
     end
    end
    META:if(meta_ready)begin state<=PLANE_START;plane<=0;next_block<=0;next_x<=0;next_y<=0;map_wait<=0;prefetch_valid<=0;end
    PLANE_START:if(j_start_ready)begin state<=PLANE_REPLAY;request_count<=0;response_count<=0;end
    PLANE_REPLAY:if(ersv&&replay_response_ready&&replay_last)state<=PLANE_WAIT;
    PLANE_WAIT:if(j_done)begin
     if(plane==2)begin state<=RETIRE;env_retired<=0;map_retired<=0;end
     else begin plane<=plane+1;state<=PLANE_START;next_block<=0;next_x<=0;next_y<=0;map_wait<=0;prefetch_valid<=0;end
    end
    RETIRE:begin
     if(ert)env_retired<=1;if(grt)map_retired<=1;
     if((env_retired||ert)&&(map_retired||grt))state<=COMPLETE;
    end
    COMPLETE:if(completion_ready)state<=IDLE;
    FAIL:if(error_ready)begin state<=IDLE;map_wait<=0;prefetch_valid<=0;end
    default:state<=IDLE;
   endcase
  end
 end
endmodule
