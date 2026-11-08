`timescale 1ns/1ps
`default_nettype none
// STB1 isolated ABI3 prototype: fixed credit reservation, native stage commits remain authoritative.
module cu71_staging_burst_v1 # (parameter integer DEPTH=256)(
 input wire clk,rst,bus_write,input wire[11:0]bus_address,bus_read_address,input wire[31:0]bus_wdata,
 input wire transport_fault,begin_packet,input wire[63:0]staged_generation,
 input wire[31:0]packet_bytes,written_bytes,actual_crc,
 input wire scalar_valid,input wire[31:0]scalar_word,input wire[2:0]native_capacity,
 output wire upload_valid,output wire[31:0]upload_word,output wire[2:0]upload_count,input wire upload_ready,
 output wire fence_ready,output wire blocked,output reg fault=0,
 output wire selected,output reg[31:0]rdata,
 output wire[31:0]accepted_prefix,output wire[8:0]queued_words
);
 localparam AW=$clog2(DEPTH);
 (* ram_style="block" *) reg[34:0]fifo[0:DEPTH-1];
 reg[34:0]fifo_q;
 reg[AW-1:0]wp=0,rp=0;reg[AW:0]used=0;reg fetched=0;
 reg[63:0]shadow_generation=0,held_generation=0;
 reg[31:0]shadow_offset=0,shadow_bytes=0,ticket=0;
 reg[31:0]accepted=0,received=0,chunk_bytes=0,rejected_words=0;
 reg armed=0;
 wire alias_write=bus_write&&bus_address>=12'hc00;
 wire scalar_conflict=scalar_valid&&(armed||used!=0);
 wire fifo_identity=held_generation==staged_generation&&staged_generation!=0;
 assign upload_valid=!rst&&((fetched&&fifo_identity&&upload_ready)||(scalar_valid&&!armed&&used==0&&!fault));
 assign upload_word=used!=0?fifo_q[31:0]:scalar_word;
 assign upload_count=used!=0?fifo_q[34:32]:native_capacity;
 wire pop=upload_valid&&upload_ready&&used!=0;
 wire scalar_accept=upload_valid&&upload_ready&&used==0;
 wire[31:0]remaining=chunk_bytes-received;
 wire[2:0]nbytes=remaining>=4?3'd4:remaining[2:0];
 wire alias_legal=armed&&!fault&&!transport_fault&&fifo_identity&&received<chunk_bytes&&
  bus_address[1:0]==0&&{22'd0,bus_address[9:0]}==(received&32'hfffffffc)&&used<DEPTH;
 wire push=alias_write&&alias_legal;
 assign fence_ready=used==0&&written_bytes==accepted;
 assign blocked=armed||used!=0||!fence_ready;
 assign accepted_prefix=accepted;assign queued_words=used;
 wire[32:0]end_offset={1'b0,shadow_offset}+{1'b0,shadow_bytes};
 wire setup_legal=!blocked&&!fault&&!transport_fault&&upload_ready&&staged_generation!=0&&
  shadow_generation==staged_generation&&shadow_offset==written_bytes&&shadow_offset[1:0]==0&&
  shadow_bytes!=0&&shadow_bytes<=DEPTH*4&&end_offset<={1'b0,packet_bytes}&&
  (shadow_bytes[1:0]==0||end_offset=={1'b0,packet_bytes})&&bus_wdata>ticket;
 always @(posedge clk)fifo_q<=fifo[rp];
 always @(posedge clk)begin
  if(rst)begin
   wp<=0;rp<=0;used<=0;fetched<=0;shadow_generation<=0;held_generation<=0;shadow_offset<=0;shadow_bytes<=0;
   ticket<=0;accepted<=0;received<=0;chunk_bytes<=0;rejected_words<=0;armed<=0;fault<=0;
  end else begin
   if(transport_fault)fault<=1;
   if(begin_packet)begin
    // The owner only admits begin from EMPTY, with all accepted writes drained.
    if(blocked)fault<=1;
    else begin accepted<=0;armed<=0;received<=0;chunk_bytes<=0;end
   end
   if(scalar_conflict)begin fault<=1;rejected_words<=rejected_words+1;end
   if(scalar_accept)accepted<=written_bytes+{29'd0,native_capacity};
   if(used!=0&&!fifo_identity)fault<=1;
   if(!fetched&&used!=0)fetched<=1;
   if(pop)begin rp<=rp+1'b1;fetched<=0;end
   if(alias_write)begin
    if(push)begin fifo[wp]<={nbytes,bus_wdata};wp<=wp+1'b1;received<=received+{29'd0,nbytes};accepted<=accepted+{29'd0,nbytes};end
    else begin fault<=1;rejected_words<=rejected_words+1;end
   end
   case({push,pop})2'b10:used<=used+1'b1;2'b01:used<=used-1'b1;default:begin end endcase
   if(armed&&received==chunk_bytes&&fence_ready)armed<=0;
   if(bus_write)case(bus_address)
    12'h720:shadow_generation[31:0]<=bus_wdata;
    12'h724:shadow_generation[63:32]<=bus_wdata;
    12'h728:shadow_offset<=bus_wdata;
    12'h72c:shadow_bytes<=bus_wdata;
    12'h730:if(setup_legal)begin held_generation<=shadow_generation;received<=0;chunk_bytes<=shadow_bytes;ticket<=bus_wdata;armed<=1;end else fault<=1;
    default:begin end
   endcase
  end
 end
 assign selected=bus_read_address>=12'h700&&bus_read_address<=12'h730;
 always @*begin
  rdata=0;
  case(bus_read_address)
   12'h700:rdata=32'h53544231;
   12'h704:rdata=32'h00010000;
   12'h708:rdata={27'd0,transport_fault,blocked,fence_ready,armed,fault};
   12'h70c:rdata=fence_ready&&!armed&&!fault&&!transport_fault?DEPTH:0;
   12'h710:rdata=fence_ready?written_bytes:0;
   12'h714:rdata=fence_ready?actual_crc:0;
   12'h718:rdata=ticket;
   12'h71c:rdata=rejected_words;
   12'h720:rdata=shadow_generation[31:0];12'h724:rdata=shadow_generation[63:32];12'h728:rdata=shadow_offset;12'h72c:rdata=shadow_bytes;
   12'h730:rdata={23'd0,queued_words};
   default:begin end
  endcase
 end
endmodule
`default_nettype wire
