`timescale 1ns/1ps
// Standalone synchronous byte/DMA boundary. Not connected to production QSPI.
module v97_forward (
 input logic clk, rst_n, abort_frame, core_change,
 input logic [31:0] new_generation, start_generation, req_generation, data_generation, commit_generation,
 output logic [31:0] generation, ack_generation,
 input logic start_valid, input logic [31:0] start_epoch, start_fid, start_total, start_crc,
 output logic start_ready,
 input logic req_valid, input logic [31:0] req_epoch, input logic [10:0] req_len,
 output logic req_ready, output logic [31:0] req_token,
 input logic data_valid, input logic [31:0] data_epoch, data_token,
 input logic [7:0] data_byte, output logic data_ready,
 output logic ack_valid, input logic ack_ready, output logic [31:0] ack_epoch, ack_token,
 output logic sink_valid, input logic sink_ready, output logic [7:0] sink_byte,
 input logic commit_valid, input logic [31:0] commit_epoch, commit_fid,
 output logic commit_pulse, output logic [31:0] committed_fid,
 output logic active, reject_pulse, crc_error,
 output logic [11:0] fifo_used, reserved_bytes, free_bytes,
 output logic [1:0] queued_slots,
 output logic [31:0] received_bytes, drained_bytes,
 output wire [31:0] capability, version, capacity, max_dma, dma_alignment
);
 assign capability=32'h56393743; // V97C; old 0x0c remaining-frame count is NOT credit.
 assign version=32'd1;
 assign capacity=32'd2048;
 assign max_dma=32'd1400;
 assign dma_alignment=32'd4;
 logic [7:0] fifo[0:2047];
 logic [10:0] write_ptr,read_ptr;
 logic [31:0] epoch,fid,total,expected_crc,crc,issued_bytes,next_token;
 logic [1:0] slot_state[0:1]; // 0 free, 1 receiving, 2 complete ACK held
 logic [10:0] slot_left[0:1];
 logic [31:0] slot_token[0:1];
 logic request_slot,data_slot,ack_slot;
 wire push=data_valid&&data_ready;
 wire pop=sink_valid&&sink_ready;
 wire reserve=req_valid&&req_ready;
 wire acknowledge=ack_valid&&ack_ready;
 assign free_bytes=12'd2048-fifo_used-reserved_bytes;
 assign req_token=next_token;
 assign start_ready=!active&&fifo_used==0&&queued_slots==0;
 assign req_ready=active && !crc_error && req_generation==generation && next_token!=32'hffffffff && req_epoch==epoch && req_len!=0 && req_len<=11'd1400
                   && {1'b0,req_len}<=free_bytes && queued_slots<2
                   && issued_bytes<=total && {21'd0,req_len}<=total-issued_bytes;
 assign data_ready=active && !crc_error && slot_state[data_slot]==1
                   && data_generation==generation && data_epoch==epoch && data_token==slot_token[data_slot]
                   && fifo_used<12'd2048;
 assign ack_valid=active&&slot_state[ack_slot]==2;
 assign ack_epoch=epoch;
 assign ack_generation=generation;
 assign ack_token=slot_token[ack_slot];
 assign sink_valid=active&&fifo_used!=0;
 assign sink_byte=fifo[read_ptr];
 function automatic [31:0] crc_byte(input [31:0] old_crc,input [7:0] value);
  reg [31:0] c;
  begin
   c=old_crc^{24'd0,value};
   for(integer b=0;b<8;b=b+1)c=c[0] ? (c>>1)^32'hedb88320:c>>1;
   crc_byte=c;
  end
 endfunction
 always_ff @(posedge clk) begin
  if(!rst_n || abort_frame || core_change)begin
   active<=0;epoch<=0;fid<=0;total<=0;expected_crc<=0;crc<=32'hffffffff;
   fifo_used<=0;reserved_bytes<=0;queued_slots<=0;write_ptr<=0;read_ptr<=0;
   received_bytes<=0;drained_bytes<=0;issued_bytes<=0;
   request_slot<=0;data_slot<=0;ack_slot<=0;
   if(!rst_n)begin generation<=0;next_token<=1;end
   else if(core_change)begin generation<=new_generation;next_token<=1;end
   slot_state[0]<=0;slot_state[1]<=0;slot_left[0]<=0;slot_left[1]<=0;
   slot_token[0]<=0;slot_token[1]<=0;
   commit_pulse<=0;committed_fid<=0;reject_pulse<=0;crc_error<=0;
  end else begin
   commit_pulse<=0;reject_pulse<=0;
   if(start_valid)begin
    if(start_ready && start_generation==generation && start_epoch!=0 && start_total!=0 && start_total<=32'd262144)begin
     active<=1;epoch<=start_epoch;fid<=start_fid;total<=start_total;
     expected_crc<=start_crc;crc<=32'hffffffff;crc_error<=0;
     received_bytes<=0;drained_bytes<=0;issued_bytes<=0;
    end else reject_pulse<=1;
   end
   if(req_valid&&!req_ready)reject_pulse<=1;
   if(data_valid&&!data_ready)reject_pulse<=1;
   case({reserve,push})
    2'b10:reserved_bytes<=reserved_bytes+{1'b0,req_len};
    2'b01:reserved_bytes<=reserved_bytes-1'b1;
    2'b11:reserved_bytes<=reserved_bytes+{1'b0,req_len}-1'b1;
    default:begin end
   endcase
   case({push,pop})
    2'b10:fifo_used<=fifo_used+1'b1;
    2'b01:fifo_used<=fifo_used-1'b1;
    default:begin end
   endcase
   case({reserve,acknowledge})
    2'b10:queued_slots<=queued_slots+1'b1;
    2'b01:queued_slots<=queued_slots-1'b1;
    default:begin end
   endcase
   if(reserve)begin
    slot_state[request_slot]<=1;slot_left[request_slot]<=req_len;
    slot_token[request_slot]<=next_token;next_token<=next_token+1'b1;
    request_slot<=~request_slot;issued_bytes<=issued_bytes+{21'd0,req_len};
   end
   if(push)begin
    fifo[write_ptr]<=data_byte;write_ptr<=write_ptr+1'b1;
    received_bytes<=received_bytes+1'b1;crc<=crc_byte(crc,data_byte);
    slot_left[data_slot]<=slot_left[data_slot]-1'b1;
    if(slot_left[data_slot]==1)begin slot_state[data_slot]<=2;data_slot<=~data_slot;end
   end
   if(pop)begin read_ptr<=read_ptr+1'b1;drained_bytes<=drained_bytes+1'b1;end
   if(acknowledge)begin slot_state[ack_slot]<=0;ack_slot<=~ack_slot;end
   if(commit_valid)begin
    if(active && commit_generation==generation && commit_epoch==epoch && commit_fid==fid && !crc_error
       && received_bytes==total && drained_bytes==total && queued_slots==0 && fifo_used==0)begin
     if((crc^32'hffffffff)==expected_crc)begin
      commit_pulse<=1;committed_fid<=fid;active<=0;
     end else begin crc_error<=1;reject_pulse<=1;end
    end else reject_pulse<=1;
   end
   assert(fifo_used+reserved_bytes<=12'd2048) else $fatal(1,"credit capacity");
   assert(queued_slots<=2) else $fatal(1,"descriptor capacity");
   assert(drained_bytes<=received_bytes && received_bytes<=issued_bytes && issued_bytes<=total)
      else $fatal(1,"byte accounting");
  end
 end
endmodule
