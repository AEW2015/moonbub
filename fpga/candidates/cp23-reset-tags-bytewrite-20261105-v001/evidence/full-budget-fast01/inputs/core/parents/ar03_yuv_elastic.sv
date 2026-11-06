`timescale 1ns/1ps
`default_nettype none
// One owner-scoped canonical-byte FIFO in front of the sealed owned sink.
// Occupancy includes the synchronous RAM output and elastic prefetch stage.
module ar03_yuv_elastic #(
 parameter integer TOTAL_BYTES=518400,DEPTH=512,
 parameter [23:0] APERTURE_BASE=24'h100000,
 parameter integer APERTURE_WORDS=262144
)(
 input wire clk,reset,
 input wire start_valid,output wire start_ready,
 input wire[63:0]start_owner,input wire[31:0]start_epoch,start_frame,input wire[23:0]start_base,
 input wire in_valid,output wire in_ready,input wire[7:0]in_byte,
 input wire[63:0]in_owner,input wire[31:0]in_epoch,in_frame,input wire in_last,
 input wire abort,input wire fault,
 input wire completion_valid,input wire[63:0]completion_owner,input wire[31:0]completion_epoch,completion_frame,
 input wire release_valid,input wire[63:0]release_owner,input wire[31:0]release_epoch,release_frame,
 output wire completion_rejected,release_rejected,
 output wire pixel_valid,input wire pixel_ready,output wire[23:0]pixel_address,output wire[15:0]pixel_data,
 output wire force_flush,discard,input wire memory_idle,
 output wire busy,done,failed,aborted,output wire[63:0]owner,
 output wire[31:0]accepted_bytes,accepted_words,output wire[3:0]error_code,state,
 output reg[31:0]enqueued,dequeued,occupancy,high_water
);
 localparam AW=$clog2(DEPTH);
 initial if(DEPTH<4||(DEPTH&(DEPTH-1))!=0)$fatal(1,"FIFO depth must be power of two >=4");
 (* ram_style="block" *)reg[7:0]ram[0:DEPTH-1];
 reg[AW-1:0]wp,rp;
 reg[31:0]ram_count;
 reg read_pending,prefetch_valid;
 reg[7:0]ram_q,prefetch_data;
 reg job_live,cancelled,cancel_was_abort;
 reg[31:0]held_epoch,held_frame;
 wire core_start_ready,core_in_ready,core_busy,core_done,core_failed,core_aborted;
 wire core_completion_rejected,core_release_rejected;
 wire metadata_ok=in_owner==owner&&in_epoch==held_epoch&&in_frame==held_frame&&in_last==(enqueued==TOTAL_BYTES-1);
 wire input_error=in_valid&&job_live&&!cancelled&&state==1&&enqueued<TOTAL_BYTES&&!metadata_ok;
 wire invalidate=reset||(job_live&&(abort||fault||input_error))||core_failed||core_aborted;
 wire all_empty=occupancy==0&&ram_count==0&&!read_pending&&!prefetch_valid;
 assign start_ready=core_start_ready&&!job_live&&!cancelled&&all_empty&&!reset&&!abort&&!fault;
 assign in_ready=job_live&&!cancelled&&state==1&&enqueued<TOTAL_BYTES&&occupancy<DEPTH&&metadata_ok&&!abort&&!fault&&!reset;
 wire enqueue=in_valid&&in_ready;
 wire core_valid=prefetch_valid&&job_live&&!cancelled&&!abort&&!fault&&!input_error&&!reset;
 wire dequeue=core_valid&&core_in_ready;
 wire prefetch_can=!prefetch_valid||dequeue;
 wire issue_read=job_live&&!cancelled&&!invalidate&&ram_count!=0&&(!read_pending||prefetch_can);
 // No reset on RAM data or RAM read output. Validity/pointers control exposure.
 always @(posedge clk)begin
  if(enqueue)ram[wp]<=in_byte;
  if(issue_read)ram_q<=ram[rp];
 end
 always @(posedge clk)begin
  if(reset)begin
   wp<=0;rp<=0;ram_count<=0;read_pending<=0;prefetch_valid<=0;
   job_live<=0;cancelled<=0;cancel_was_abort<=0;held_epoch<=0;held_frame<=0;
   enqueued<=0;dequeued<=0;occupancy<=0;high_water<=0;
  end else if(start_valid&&start_ready)begin
   wp<=0;rp<=0;ram_count<=0;read_pending<=0;prefetch_valid<=0;
   job_live<=1;cancelled<=0;cancel_was_abort<=0;held_epoch<=start_epoch;held_frame<=start_frame;
   enqueued<=0;dequeued<=0;occupancy<=0;high_water<=0;
  end else if(invalidate)begin
   wp<=0;rp<=0;ram_count<=0;read_pending<=0;prefetch_valid<=0;occupancy<=0;
   if(job_live&&!cancelled)begin cancelled<=1;cancel_was_abort<=abort;end
  end else begin
   if(job_live&&owner==0)begin job_live<=0;cancelled<=0;end
   if(enqueue)begin wp<=wp+1'b1;enqueued<=enqueued+1'b1;end
   if(issue_read)rp<=rp+1'b1;
   case({enqueue,issue_read})
    2'b10:ram_count<=ram_count+1'b1;
    2'b01:ram_count<=ram_count-1'b1;
   endcase
   case({enqueue,dequeue})
    2'b10:begin occupancy<=occupancy+1'b1;if(occupancy+1'b1>high_water)high_water<=occupancy+1'b1;end
    2'b01:occupancy<=occupancy-1'b1;
   endcase
   if(dequeue)dequeued<=dequeued+1'b1;
   if(prefetch_can)begin
    prefetch_valid<=read_pending;
    if(read_pending)prefetch_data<=ram_q;
   end
   if(issue_read)read_pending<=1;
   else if(prefetch_can)read_pending<=0;
  end
 end
 assign accepted_bytes=enqueued;
 assign busy=core_busy||occupancy!=0;
 assign done=core_done&&all_empty;
 assign failed=core_failed;
 assign aborted=core_aborted;
 assign completion_rejected=core_completion_rejected;
 assign release_rejected=release_valid&&(!all_empty||core_release_rejected);
 ar03_yuv_store_owned #(.TOTAL_BYTES(TOTAL_BYTES),.APERTURE_BASE(APERTURE_BASE),.APERTURE_WORDS(APERTURE_WORDS)) sink(
  .clk(clk),.reset(reset),.start_valid(start_valid&&!job_live&&!cancelled&&all_empty&&!reset&&!abort&&!fault),.start_ready(core_start_ready),
  .start_owner(start_owner),.start_epoch(start_epoch),.start_frame(start_frame),.start_base(start_base),
  .in_valid(core_valid),.in_ready(core_in_ready),.in_byte(prefetch_data),.in_owner(owner),.in_epoch(held_epoch),.in_frame(held_frame),.in_last(dequeued==TOTAL_BYTES-1),
  .abort(abort||(cancelled&&cancel_was_abort)),.fault(fault||input_error||(cancelled&&!cancel_was_abort)),
  .completion_valid(completion_valid),.completion_owner(completion_owner),.completion_epoch(completion_epoch),.completion_frame(completion_frame),
  .release_valid(release_valid&&all_empty),.release_owner(release_owner),.release_epoch(release_epoch),.release_frame(release_frame),
  .completion_rejected(core_completion_rejected),.release_rejected(core_release_rejected),
  .pixel_valid(pixel_valid),.pixel_ready(pixel_ready),.pixel_address(pixel_address),.pixel_data(pixel_data),
  .force_flush(force_flush),.discard(discard),.memory_idle(memory_idle),
  .busy(core_busy),.done(core_done),.failed(core_failed),.aborted(core_aborted),.owner(owner),
  .accepted_bytes(),.accepted_words(accepted_words),.error_code(error_code),.state(state));
endmodule
`default_nettype wire
