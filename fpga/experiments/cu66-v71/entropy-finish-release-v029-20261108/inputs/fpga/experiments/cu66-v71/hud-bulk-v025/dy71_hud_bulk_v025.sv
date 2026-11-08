`timescale 1ns/1ps
`default_nettype none
// Bounded payload staging + sequential, completed AUX requests. No owner/commit authority.
module dy71_hud_bulk_v025(
 input wire clk,rst,bus_write,input wire[11:0]bus_address,bus_read_address,input wire[31:0]bus_wdata,
 output wire bus_selected,output reg[31:0]bus_rdata,
 input wire setup_valid,output wire setup_ready,output wire setup_error,
 input wire identity_valid,input wire[63:0]command_generation,input wire[31:0]command_frame,command_reference,
 input wire[1:0]command_bank,input wire[31:0]command_ticket,word_offset,word_count,read_mode,
 input wire run_valid,output wire run_ready,output reg done,error,
 input wire hud_live,input wire[63:0]live_generation,input wire[31:0]live_frame,live_reference,live_ticket,input wire[1:0]live_bank,
 output wire req_valid,input wire req_ready,output wire[63:0]req_generation,output wire[31:0]req_frame,
 output wire req_write,output wire[23:0]req_address,output wire[15:0]req_data,
 input wire rsp_valid,output wire rsp_ready,input wire[15:0]rsp_data,input wire rsp_error,
 output wire active,output reg[8:0]completed_words
);
 `include "cu70_memory_map.svh"
 localparam[1:0]IDLE=0,FETCH=1,ISSUE=2,DRAIN=3;
 reg[1:0]state=IDLE;
 reg configured=0,mode_read=0,result_ready=0,fault=0;
 reg[63:0]generation=0;reg[31:0]frame=0,reference=0,ticket=0;
 reg[1:0]bank=0;reg[14:0]offset=0;reg[8:0]count=0,index=0;
 reg[7:0]packed_loaded=0;
 wire[8:0]packed_count=(count+9'd1)>>1;
 wire[32:0]end_word={1'b0,word_offset}+{1'b0,word_count};
 wire setup_legal=!run_valid&&identity_valid&&command_generation!=0&&command_bank<3&&word_count!=0&&word_count<=256&&word_offset<21120&&end_word<=21120&&read_mode<=1;
 assign active=state!=IDLE;assign setup_ready=!active;assign setup_error=!setup_legal;
 assign run_ready=!active;
 wire command_matches=identity_valid&&command_generation==generation&&command_frame==frame&&command_reference==reference&&command_bank==bank&&command_ticket==ticket&&word_offset=={17'd0,offset}&&word_count=={23'd0,count}&&read_mode=={31'd0,mode_read};
 wire live_matches=hud_live&&live_generation==generation&&live_frame==frame&&live_reference==reference&&live_bank==bank&&live_ticket==ticket;
 wire scratch=bus_write&&bus_address>=12'h400&&bus_address<12'h600;
 wire load_ok=!rst&&scratch&&bus_address[1:0]==0&&configured&&!mode_read&&!active&&!fault&&packed_loaded<packed_count&&{1'b0,bus_address[8:2]}==packed_loaded;
 wire bad_access=scratch&&!load_ok;
 wire failed=fault||bad_access||!live_matches;
 // Explicit RAM primitives preserve the CPU write-address mux. Vivado2025.2
 // inferred the previous shared-port template with the read address on writes;
 // post-synthesis XSim caught that mismatch before any implementation/programming.
 wire[15:0]cpu_low,cpu_high,engine_low,engine_high;
 wire[6:0]cpu_address=load_ok?bus_address[8:2]:bus_read_address[8:2];
 wire read_completion=!rst&&state==DRAIN&&rsp_valid&&mode_read&&!rsp_error&&!failed;
 wire low_write=read_completion&&!index[0];
 wire high_write=read_completion&&(index[0]||index+1==count);
 wire[15:0]high_data=index[0]?rsp_data:16'd0;
 RAMB18E1 #(.RAM_MODE("TDP"),.READ_WIDTH_A(18),.READ_WIDTH_B(18),.WRITE_WIDTH_A(18),.WRITE_WIDTH_B(18),
  .DOA_REG(0),.DOB_REG(0),.WRITE_MODE_A("READ_FIRST"),.WRITE_MODE_B("READ_FIRST"),.SIM_DEVICE("7SERIES"),.SIM_COLLISION_CHECK("ALL"))
 payload_low(.CLKARDCLK(clk),.CLKBWRCLK(clk),.ENARDEN(1'b1),.ENBWREN(1'b1),
  .ADDRARDADDR({3'b111,index[7:1],4'b1111}),.ADDRBWRADDR({3'b111,cpu_address,4'b1111}),
  .DIADI(rsp_data),.DIBDI(bus_wdata[15:0]),.DIPADIP(2'd0),.DIPBDIP(2'd0),.DOADO(engine_low),.DOBDO(cpu_low),.DOPADOP(),.DOPBDOP(),
  .WEA({2{low_write}}),.WEBWE({2'b00,{2{load_ok}}}),.REGCEAREGCE(1'b0),.REGCEB(1'b0),
  .RSTRAMARSTRAM(1'b0),.RSTRAMB(1'b0),.RSTREGARSTREG(1'b0),.RSTREGB(1'b0));
 RAMB18E1 #(.RAM_MODE("TDP"),.READ_WIDTH_A(18),.READ_WIDTH_B(18),.WRITE_WIDTH_A(18),.WRITE_WIDTH_B(18),
  .DOA_REG(0),.DOB_REG(0),.WRITE_MODE_A("READ_FIRST"),.WRITE_MODE_B("READ_FIRST"),.SIM_DEVICE("7SERIES"),.SIM_COLLISION_CHECK("ALL"))
 payload_high(.CLKARDCLK(clk),.CLKBWRCLK(clk),.ENARDEN(1'b1),.ENBWREN(1'b1),
  .ADDRARDADDR({3'b111,index[7:1],4'b1111}),.ADDRBWRADDR({3'b111,cpu_address,4'b1111}),
  .DIADI(high_data),.DIBDI(bus_wdata[31:16]),.DIPADIP(2'd0),.DIPBDIP(2'd0),.DOADO(engine_high),.DOBDO(cpu_high),.DOPADOP(),.DOPBDOP(),
  .WEA({2{high_write}}),.WEBWE({2'b00,{2{load_ok}}}),.REGCEAREGCE(1'b0),.REGCEB(1'b0),
  .RSTRAMARSTRAM(1'b0),.RSTRAMB(1'b0),.RSTREGARSTREG(1'b0),.RSTREGB(1'b0));
 assign req_valid=!rst&&state==ISSUE;
 assign req_generation=generation;assign req_frame=frame;assign req_write=!mode_read;
 wire[23:0]base=bank==0?HUD0_BASE:bank==1?HUD1_BASE:HUD2_BASE;
 reg[23:0]request_address=0;
 always @(posedge clk)if(state==FETCH)request_address<=base+{9'd0,offset}+{15'd0,index};
 assign req_address=request_address;
 assign req_data=mode_read?16'd0:(index[0]?engine_high:engine_low);
 assign rsp_ready=!rst&&state==DRAIN;
 always @(posedge clk)begin
  if(rst)begin
   state<=IDLE;configured<=0;mode_read<=0;result_ready<=0;fault<=0;generation<=0;frame<=0;reference<=0;ticket<=0;bank<=0;offset<=0;count<=0;index<=0;packed_loaded<=0;completed_words<=0;done<=0;error<=0;
  end else begin
   done<=0;
   if(bad_access)begin fault<=1;result_ready<=0;end
   if(load_ok)packed_loaded<=packed_loaded+1'b1;
   if(setup_valid&&setup_ready)begin
    result_ready<=0;packed_loaded<=0;completed_words<=0;index<=0;configured<=setup_legal&&!bad_access;fault<=!setup_legal||bad_access;error<=0;
    if(setup_legal)begin generation<=command_generation;frame<=command_frame;reference<=command_reference;bank<=command_bank;ticket<=command_ticket;offset<=word_offset[14:0];count<=word_count[8:0];mode_read<=read_mode[0];end
   end
   if(run_valid&&run_ready)begin
    configured<=0;result_ready<=0;completed_words<=0;index<=0;error<=0;
    if(setup_valid||!configured||!command_matches||failed||(!mode_read&&packed_loaded!=packed_count))begin done<=1;error<=1;fault<=1;end
    else state<=FETCH;
   end
   case(state)
    FETCH:if(failed)begin state<=IDLE;done<=1;error<=1;fault<=1;end else state<=ISSUE;
    // Once asserted, keep a request stable until accepted, including on abort.
    // Its response must drain before an error can complete the block.
    ISSUE:begin if(failed)fault<=1;if(req_ready)state<=DRAIN;end
    DRAIN:if(rsp_valid)begin
     if(rsp_error||failed)begin state<=IDLE;done<=1;error<=1;fault<=1;end
     else begin
      completed_words<=completed_words+1'b1;
      if(index+1==count)begin state<=IDLE;done<=1;error<=0;result_ready<=mode_read;end
      else begin index<=index+1'b1;state<=FETCH;end
     end
    end
    default:begin end
   endcase
  end
 end
 assign bus_selected=(bus_read_address>=12'h600&&bus_read_address<=12'h618)||(bus_read_address>=12'h400&&bus_read_address<12'h600);
 always @*begin
  bus_rdata=0;
  case(bus_read_address)
   12'h600:bus_rdata=32'h48425531;
   12'h604:bus_rdata=32'h00010000;
   12'h608:bus_rdata={27'd0,fault,result_ready,(!mode_read&&packed_loaded==packed_count&&count!=0),active,configured};
   12'h60c:bus_rdata={24'd0,packed_loaded};
   12'h610:bus_rdata={23'd0,completed_words};
   12'h614:bus_rdata={7'd0,count,1'b0,offset};
   12'h618:bus_rdata=ticket;
   default:if(bus_read_address>=12'h400&&bus_read_address<12'h600&&bus_read_address[1:0]==0&&result_ready&&{2'd0,bus_read_address[8:2]}<packed_count)bus_rdata={cpu_high,cpu_low};
  endcase
 end
endmodule
`default_nettype wire
