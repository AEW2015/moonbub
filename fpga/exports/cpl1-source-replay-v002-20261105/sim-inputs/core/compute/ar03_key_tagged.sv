// Private pre-HUD KEY decode + raster ordering + exact canonical hash.
// Completion is NOT frame acceptance, bank publication, AF03 or presentation.
module ar03_key_tagged(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,input wire[63:0] start_owner,
 input wire[31:0] start_bytes,start_epoch,
 input wire in_valid,output wire in_ready,input wire[7:0] in_byte,input wire in_last,
 output wire sample_valid,input wire sample_ready,output wire[7:0] sample,
 output wire[63:0] sample_owner,output wire[31:0] sample_epoch,sample_frame,
 output wire[1:0] sample_plane,output wire[15:0] sample_x,sample_y,output wire sample_last,
 output wire completion_valid,input wire completion_ready,
 output wire[63:0] completion_owner,output wire[31:0] completion_epoch,completion_frame,
 output wire[127:0] completion_tag,
 output wire error_valid,input wire error_ready,output wire[3:0] error_stage,output wire[7:0] error_code,
 output wire[63:0] error_owner
);
 localparam IDLE=0,RUN=1,DONE=2,FAIL=3;
 reg[1:0] state;reg[63:0] owner;reg[31:0] epoch,frame;
 reg[15:0] width,height;reg[127:0] expected_tag,tag;
 reg metadata_seen,key_done,raster_done,tag_done,cancel_pending;
 reg[3:0] held_stage;reg[7:0] held_code;
 // Only registered state cancels children, avoiding error->abort->error loops.
 wire cancel=abort||state==FAIL||cancel_pending;
 wire ks,ki,kv,kc,ke,mv,mr;
 wire[7:0] ksample,kcode;wire[3:0] kstage;
 wire[63:0] ko,kco,keo,mo;wire[31:0] kep,kfr,kblock,kcep,kcfr,mep,mfr;
 wire[1:0] kp;wire[15:0] kx,ky,mw,mh;wire[127:0] mt;
 wire rs,ri,rv,rd,re,hs,hi,hv,he;
 wire[2:0] rcode,hcode;wire[7:0] r_sample;wire[63:0] ro,ho;
 wire[31:0] rep,rfr,hep;wire[1:0] rp;wire[15:0] rx,ry;wire rl;
 wire[127:0] ht;
 wire meta_good=mo==owner&&mep==epoch&&mw>=2&&mh>=2&&mw<=720&&mh<=480&&!mw[0]&&!mh[0];
 wire sample_identity=ro==owner&&rep==epoch&&rfr==frame;
 wire child_error=ke||re||he;
 wire bad_sample=rv&&metadata_seen&&!sample_identity;
 wire bad_meta=mv&&!meta_good;
 wire bad_completion=kc&&(kco!=owner||kcep!=epoch||kcfr!=frame);
 wire bad_tag=hv&&(ho!=owner||hep!=epoch||ht!=expected_tag);
 wire fail_now=state==RUN&&(child_error||bad_sample||bad_meta||bad_completion||bad_tag);
 wire[3:0] live_stage=ke?kstage:re?4'd6:he?4'd7:4'd8;
 wire[7:0] live_code=ke?kcode:re?{5'b0,rcode}:he?{5'b0,hcode}:bad_sample?8'd2:bad_meta?8'd1:bad_completion?8'd2:8'd3;
 // Error, reason and identity are visible in the same cycle that any child
 // withdraws its stream on failure. Every transfer is masked by that event.
 wire active=state==RUN&&!fail_now&&!reset&&!abort;
 wire launch_meta=active&&mv&&meta_good&&rs&&hs;
 assign mr=launch_meta;
 ar03_key_pipeline_meta key_path(
  .clk(clk),.reset(reset),.abort(cancel),.start_valid(start_valid&&state==IDLE),.start_ready(ks),
  .start_owner(start_owner),.start_bytes(start_bytes),.start_epoch(start_epoch),
  .in_valid(in_valid&&state==RUN),.in_ready(ki),.in_byte(in_byte),.in_last(in_last),
  .candidate_valid(kv),.candidate_ready(ri&&active&&metadata_seen),.candidate_sample(ksample),
  .candidate_owner(ko),.candidate_epoch(kep),.candidate_frame(kfr),.candidate_block(kblock),
  .candidate_plane(kp),.candidate_x(kx),.candidate_y(ky),
  .meta_valid(mv),.meta_ready(mr),.meta_owner(mo),.meta_epoch(mep),.meta_frame(mfr),
  .meta_width(mw),.meta_height(mh),.meta_stored_tag(mt),
  .completion_valid(kc),.completion_ready(active),.completion_owner(kco),.completion_epoch(kcep),.completion_frame(kcfr),
  .error_valid(ke),.error_ready(1'b0),.error_stage(kstage),.error_code(kcode),.error_owner(keo));
 wire klast=kp==2&&kx==(width>>1)-1&&ky==(height>>1)-1;
 ar03_raster_stripes raster(
  .clk(clk),.reset(reset),.abort(cancel),.start_valid(launch_meta),.start_ready(rs),
  .start_owner(mo),.start_epoch(mep),.start_frame(mfr),.start_width(mw),.start_height(mh),
  .in_valid(kv&&active&&metadata_seen),.in_ready(ri),.in_sample(ksample),.in_owner(ko),.in_epoch(kep),.in_frame(kfr),
  .in_block(kblock),.in_plane(kp),.in_x(kx),.in_y(ky),.in_last(klast),
  .out_valid(rv),.out_ready(sample_ready&&hi&&active&&sample_identity),.out_sample(r_sample),
  .out_owner(ro),.out_epoch(rep),.out_frame(rfr),.out_plane(rp),.out_x(rx),.out_y(ry),.out_last(rl),
  .done_valid(rd),.done_ready(active),.error_valid(re),.error_ready(1'b0),.error_code(rcode));
 canonical_tag hash_path(
  .clk(clk),.reset(reset),.abort(cancel),.start_valid(launch_meta),.start_ready(hs),
  .start_owner(mo),.start_epoch(mep),.start_width(mw),.start_height(mh),
  .in_valid(rv&&sample_ready&&active&&sample_identity),.in_ready(hi),.in_sample({8'b0,r_sample}),
  .in_plane(rp),.in_x(rx),.in_y(ry),.in_last(rl),
  .out_valid(hv),.out_ready(active),.out_tag(ht),.out_owner(ho),.out_epoch(hep),
  .error_valid(he),.error_ready(1'b0),.error_code(hcode));
 assign start_ready=state==IDLE&&ks&&!cancel_pending&&!reset&&!abort;
 assign in_ready=state==RUN&&ki&&!reset&&!abort;
 // A sample transfer is simultaneously accepted by the hash path and observer.
 // hi remains asserted while a valid sample is held behind sample_ready=0.
 assign sample_valid=rv&&hi&&active&&sample_identity;
 assign sample=r_sample;assign sample_owner=ro;assign sample_epoch=rep;assign sample_frame=rfr;
 assign sample_plane=rp;assign sample_x=rx;assign sample_y=ry;assign sample_last=rl;
 assign completion_valid=state==DONE&&!reset&&!abort;
 assign completion_owner=owner;assign completion_epoch=epoch;assign completion_frame=frame;assign completion_tag=tag;
 assign error_valid=(state==FAIL||fail_now)&&!reset&&!abort;assign error_owner=owner;
 assign error_stage=state==FAIL?held_stage:live_stage;
 assign error_code=state==FAIL?held_code:live_code;
 always @(posedge clk)begin
  if(reset)begin state<=IDLE;owner<=0;epoch<=0;frame<=0;width<=0;height<=0;expected_tag<=0;tag<=0;
   metadata_seen<=0;key_done<=0;raster_done<=0;tag_done<=0;held_stage<=0;held_code<=0;cancel_pending<=0;end
  else if(abort)begin state<=IDLE;metadata_seen<=0;key_done<=0;raster_done<=0;tag_done<=0;cancel_pending<=0;end
  else begin
   cancel_pending<=0;
   case(state)
   IDLE:if(start_valid&&start_ready)begin state<=RUN;owner<=start_owner;epoch<=start_epoch;
    metadata_seen<=0;key_done<=0;raster_done<=0;tag_done<=0;end
   RUN:begin
    if(fail_now)begin state<=error_ready?IDLE:FAIL;held_stage<=live_stage;held_code<=live_code;cancel_pending<=1;end
    else begin
     if(launch_meta)begin metadata_seen<=1;frame<=mfr;width<=mw;height<=mh;expected_tag<=mt;end
     if(kc)key_done<=1;if(rd)raster_done<=1;
     if(hv)begin tag_done<=1;tag<=ht;end
     if(key_done&&raster_done&&tag_done)state<=DONE;
    end
   end
   DONE:if(completion_ready)state<=IDLE;
   FAIL:if(error_ready)state<=IDLE;
   default:state<=IDLE;
   endcase
  end
 end
endmodule
