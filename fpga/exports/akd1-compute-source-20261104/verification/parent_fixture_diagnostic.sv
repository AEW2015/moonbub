// Private compute/hash diagnostic, proposed local CSR window 0x400..0x44c.
// No HUD, reference publication, AF03, framebuffer write or network endpoint.
module parent_fixture_diagnostic #(
 parameter integer FIXTURE_BYTES=48203,
 parameter FIXTURE_FILE="fixture.hex",
 parameter integer WATCHDOG_CYCLES=10000000
)(input wire clk,reset,input wire bus_write,input wire[11:0]bus_address,
 input wire[31:0]bus_wdata,output reg[31:0]bus_rdata);
 localparam IDLE=0,START=1,RUN=2,DONE=3,FAIL=4,CANCEL=5,ABORTED=6;
 reg[2:0]state;reg[63:0]owner,next_owner;
 reg[31:0]elapsed,samples,bytes_sent,command_rejects,result_sequence;
 reg[31:0]result_epoch,result_frame;reg[127:0]result_tag;
 reg[3:0]fault_stage;reg[7:0]fault_code;
 (* rom_style="block" *)reg[7:0]rom[0:FIXTURE_BYTES-1];
 initial $readmemh(FIXTURE_FILE,rom);
 reg byte_valid;reg[7:0]byte_data;
 wire ks,ki,sv,cv,ev;wire[63:0]co,eo;
 wire[31:0]ce,cf;wire[127:0]ct;wire[3:0]es;wire[7:0]ec;
 wire command=bus_write&&bus_address==12'h408;
 wire abort_command=command&&bus_wdata==2;
 wire busy=state==START||state==RUN||state==CANCEL;
 wire cancel=state==CANCEL;
 // A fetched byte belongs to this run until the downstream transfer. No
 // asynchronous ROM output, overwrite while stalled, or implied DMA owner.
 always @(posedge clk)begin
  if(reset||cancel)begin byte_valid<=0;byte_data<=0;end
  else if(state==RUN)begin
   if(!byte_valid&&bytes_sent<FIXTURE_BYTES)begin
    byte_data<=rom[bytes_sent];byte_valid<=1;
   end else if(byte_valid&&ki)byte_valid<=0;
  end else byte_valid<=0;
 end
 ar03_key_tagged compute(.clk(clk),.reset(reset),.abort(cancel||state==FAIL),
  .start_valid(state==START),.start_ready(ks),.start_owner(owner),
  .start_bytes(FIXTURE_BYTES),.start_epoch(32'd1),
  .in_valid(state==RUN&&byte_valid),.in_ready(ki),.in_byte(byte_data),
  .in_last(bytes_sent==FIXTURE_BYTES-1),.sample_valid(sv),.sample_ready(1'b1),
  .sample(),.sample_owner(),.sample_epoch(),.sample_frame(),.sample_plane(),
  .sample_x(),.sample_y(),.sample_last(),
  .completion_valid(cv),.completion_ready(state==RUN),
  .completion_owner(co),.completion_epoch(ce),.completion_frame(cf),.completion_tag(ct),
  .error_valid(ev),.error_ready(1'b0),.error_stage(es),.error_code(ec),.error_owner(eo));
 always @*begin
  bus_rdata=0;
  case(bus_address)
   12'h400:bus_rdata=32'h31444b41; // AKD1, little-endian opaque magic
   12'h404:bus_rdata=32'h00010000;
   12'h40c:bus_rdata={25'b0,state==ABORTED,state==FAIL,state==DONE,busy,state};
   12'h410:bus_rdata=elapsed;
   12'h414:bus_rdata=samples;
   12'h418:bus_rdata=bytes_sent;
   12'h41c:bus_rdata={20'b0,fault_stage,fault_code};
   12'h420:bus_rdata=owner[31:0];
   12'h424:bus_rdata=owner[63:32];
   12'h428:bus_rdata=result_epoch;
   12'h42c:bus_rdata=result_frame;
   12'h430:bus_rdata=result_tag[31:0];
   12'h434:bus_rdata=result_tag[63:32];
   12'h438:bus_rdata=result_tag[95:64];
   12'h43c:bus_rdata=result_tag[127:96];
   12'h440:bus_rdata=command_rejects;
   12'h444:bus_rdata=result_sequence;
   12'h448:bus_rdata=FIXTURE_BYTES;
   12'h44c:bus_rdata=WATCHDOG_CYCLES;
  endcase
 end
 always @(posedge clk)begin
  if(reset)begin
   state<=IDLE;owner<=0;next_owner<=1;elapsed<=0;samples<=0;bytes_sent<=0;
   command_rejects<=0;result_sequence<=0;result_epoch<=0;result_frame<=0;
   result_tag<=0;fault_stage<=0;fault_code<=0;
  end else if(abort_command)begin
   state<=CANCEL;fault_stage<=0;fault_code<=0;result_tag<=0;
  end else begin
   if(command)begin
    if(bus_wdata==1&&!busy&&next_owner!=64'hffffffffffffffff)begin
     owner<=next_owner;next_owner<=next_owner+1'b1;state<=START;
     elapsed<=0;samples<=0;bytes_sent<=0;result_tag<=0;result_epoch<=0;
     result_frame<=0;fault_stage<=0;fault_code<=0;
    end else if(bus_wdata==4&&!busy)state<=IDLE;
    else command_rejects<=command_rejects+1'b1;
   end
   case(state)
    START:begin
     elapsed<=elapsed+1'b1;
     if(ks)begin state<=RUN;elapsed<=0;end
     else if(elapsed==WATCHDOG_CYCLES-1)begin
      state<=FAIL;fault_stage<=15;fault_code<=3;result_sequence<=result_sequence+1'b1;
     end
    end
    RUN:begin
     elapsed<=elapsed+1'b1;
     if(byte_valid&&ki)bytes_sent<=bytes_sent+1'b1;
     if(sv)samples<=samples+1'b1;
     if(ev)begin state<=FAIL;fault_stage<=es;fault_code<=ec;result_sequence<=result_sequence+1'b1;end
     else if(cv)begin
      if(co!=owner||ce!=1)begin state<=FAIL;fault_stage<=15;fault_code<=1;end
      else begin state<=DONE;result_epoch<=ce;result_frame<=cf;result_tag<=ct;end
      result_sequence<=result_sequence+1'b1;
     end else if(elapsed==WATCHDOG_CYCLES-1)begin
      state<=FAIL;fault_stage<=15;fault_code<=2;result_sequence<=result_sequence+1'b1;
     end
    end
    CANCEL:state<=ABORTED;
   endcase
  end
 end
endmodule
