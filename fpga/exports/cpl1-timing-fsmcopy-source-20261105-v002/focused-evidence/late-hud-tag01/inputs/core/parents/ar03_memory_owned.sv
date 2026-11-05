`timescale 1ns/1ps
`default_nettype none
// Synthetic-aperture service: retained LCD line reads and packed writes plus
// one reserved, owner-tagged arbitrary BL8 response. No production bank map.
module ar03_memory_owned #(
 parameter [23:0] YUV_BASE=24'h100000,
 parameter integer YUV_WORDS=262144,
 parameter [23:0] LCD_BASE=24'h000000,
 parameter integer LCD_WORDS=1048576,
 parameter integer DISPLAY_READ_QUOTA=12,
 parameter integer WRITE_WAIT_MAX=256,
 parameter integer DISPLAY_MAX_CYCLES=2000
)(
 input wire clk,read_clk,reset,
 input wire display_valid,input wire[63:0]display_owner,
 input wire[31:0]display_epoch,display_frame,display_token,
 output wire display_active,
 output reg[31:0]display_expirations,display_rejections,quota_write_grants,age_write_grants,
 input wire pixel_valid,output wire pixel_ready,input wire[23:0]pixel_address,input wire[15:0]pixel_data,
 input wire force_flush,discard,output wire write_rejected,
 input wire line_req_valid,output wire line_req_ready,input wire[23:0]line_req_address,
 output wire line_data_valid,output wire[15:0]line_data,output wire line_rejected,
 input wire request_valid,output wire request_ready,output wire request_rejected,output wire[2:0]request_reject_reason,
 input wire[63:0]request_owner,input wire[31:0]request_epoch,request_frame,request_sequence,input wire[23:0]request_address,
 input wire cancel_valid,input wire[63:0]cancel_owner,input wire[31:0]cancel_epoch,cancel_frame,cancel_sequence,
 input wire client_fault,output wire cancel_rejected,
 output wire response_valid,input wire response_ready,output wire[127:0]response_data,
 output wire[63:0]response_owner,output wire[31:0]response_epoch,response_frame,response_sequence,
 output reg[1:0]response_status,output reg[3:0]response_words,
 output wire owned_quiescent,output wire physical_idle,/*CPL_OBS_BEGIN*/output wire observe_write_beat,/*CPL_OBS_END*/
 output reg owned_issue,owned_physical_done,owned_delivered,
 output wire[2:0]owned_state,
 output wire[12:0]sdram_a,output wire[1:0]sdram_bs,inout wire[15:0]sdram_dq,
 output wire sdram_clk,output wire[1:0]sdram_cke,sdram_cs_n,
 output wire sdram_ras_n,sdram_cas_n,sdram_we_n,sdram_ldqm,sdram_udqm
);
 localparam O_IDLE=0,O_QUEUED=1,O_READING=2,O_DRAIN=3,O_HOLD=4;
 localparam GOOD=0,ABORTED=1,FAULT=2;
 localparam B_NONE=0,B_LCD=1,B_OWNED=2;
 reg[2:0]ostate;
 reg[63:0]owner;reg[31:0]epoch,frame,held_sequence;reg[23:0]owned_address;
 reg[127:0]slot_data;
 reg cancel_pending,fault_pending;
 reg line_busy;reg[23:0]lcd_address;reg[8:0]lcd_received;
 reg bus_pending;reg[1:0]bus_kind;reg[2:0]beat;
 reg prefer_owned;
 reg display_seen,reservation_active;
 reg[63:0]reserved_owner;
 reg[31:0]reserved_epoch,reserved_frame,reserved_token,display_age;
 // Global debt counters: lease creation/change/release never clears them.
 reg[31:0]owned_read_streak,write_wait;
 wire controller_ready,controller_idle,rsp_valid;wire[15:0]rsp_data;
 wire packed_valid,packed_ready,packed_empty;wire[23:0]packed_address;
 wire[127:0]packed_data;wire[15:0]packed_mask;wire packer_pixel_ready;
 wire[24:0]yuv_end={1'b0,YUV_BASE}+YUV_WORDS;
 wire[24:0]lcd_end={1'b0,LCD_BASE}+LCD_WORDS;
 initial begin
  if(DISPLAY_READ_QUOTA<1||WRITE_WAIT_MAX<1||DISPLAY_MAX_CYCLES<1)
   $fatal(1,"invalid bounded reservation parameter");
  if(YUV_WORDS<8||LCD_WORDS<480||YUV_BASE[2:0]!=0||LCD_BASE[2:0]!=0||
   (YUV_WORDS%8)!=0||(LCD_WORDS%8)!=0||
   ({1'b0,YUV_BASE}+YUV_WORDS)>25'h1000000||({1'b0,LCD_BASE}+LCD_WORDS)>25'h1000000)
   $fatal(1,"invalid synthetic memory aperture");
  if(!(({1'b0,YUV_BASE}+YUV_WORDS)<={1'b0,LCD_BASE}||({1'b0,LCD_BASE}+LCD_WORDS)<={1'b0,YUV_BASE}))
   $fatal(1,"synthetic LCD/YUV apertures overlap");
 end
 wire write_bounds=pixel_address>=YUV_BASE&&{1'b0,pixel_address}<yuv_end;
 wire lcd_bounds=line_req_address>=LCD_BASE&&line_req_address[2:0]==0&&
  ({1'b0,line_req_address}+25'd480)<=lcd_end;
 wire request_identity=request_owner!=0&&request_epoch!=32'hffffffff&&request_frame!=32'hffffffff;
 wire request_aligned=request_address[2:0]==0;
 wire request_bounds=request_address>=YUV_BASE&&({1'b0,request_address}+25'd8)<=yuv_end;
 wire request_ok=request_identity&&request_aligned&&request_bounds;
 wire cancel_live=cancel_valid&&ostate!=O_IDLE&&cancel_owner==owner&&cancel_epoch==epoch&&cancel_frame==frame&&cancel_sequence==held_sequence;
 wire cancel_incoming=cancel_valid&&ostate==O_IDLE&&request_valid&&request_identity&&
  cancel_owner==request_owner&&cancel_epoch==request_epoch&&cancel_frame==request_frame&&cancel_sequence==request_sequence;
 assign cancel_rejected=cancel_valid&&!cancel_live&&!cancel_incoming;
 assign request_ready=ostate==O_IDLE&&!reset&&!client_fault&&!cancel_incoming;
 assign request_rejected=request_valid&&request_ready&&!request_ok;
 assign request_reject_reason=!request_identity?3'd1:!request_aligned?3'd2:!request_bounds?3'd3:3'd0;
 wire request_accept=request_valid&&request_ready&&request_ok;
 assign pixel_ready=packer_pixel_ready&&write_bounds&&!reset;
 assign write_rejected=pixel_valid&&!write_bounds&&!reset;
 assign line_req_ready=!line_busy&&lcd_bounds&&!reset;
 assign line_rejected=line_req_valid&&!lcd_bounds&&!reset;
 wire lcd_offer=line_req_valid&&lcd_bounds;
 // Whole LCD lines retain priority. Between lines only, arbitrate fairly
 // between an owned read and a packed write. Continuous LCD offers can starve
 // both; this module promises no unconditional deadline or starvation bound.
 wire can_command=!reset&&!bus_pending&&ostate!=O_DRAIN;
 wire want_lcd=line_busy;
 wire want_owned=ostate==O_QUEUED&&!cancel_live&&!client_fault;
 wire want_write=packed_valid;
 wire choose_lcd=can_command&&want_lcd;
 wire eligible_gap=can_command&&!line_busy&&!lcd_offer;
 wire display_tuple_same=display_valid&&display_owner==reserved_owner&&display_epoch==reserved_epoch&&display_frame==reserved_frame&&display_token==reserved_token;
 wire incoming_in_window=request_owner==reserved_owner&&request_epoch==reserved_epoch&&request_frame==reserved_frame;
 wire current_in_window=ostate==O_IDLE||(owner==reserved_owner&&epoch==reserved_epoch&&frame==reserved_frame);
 wire reservation_running=reservation_active&&display_tuple_same&&current_in_window&&(!request_accept||incoming_in_window);
 assign display_active=reservation_running;
 wire pending_write_due=packed_valid&&(owned_read_streak>=DISPLAY_READ_QUOTA||write_wait>=WRITE_WAIT_MAX);
 wire choose_owned=eligible_gap&&want_owned&&
  (reservation_running?!pending_write_due:(!want_write||prefer_owned));
 wire choose_write=eligible_gap&&want_write&&
  (reservation_running?pending_write_due:(!want_owned||!prefer_owned));
 wire command_valid=(choose_lcd||choose_owned||choose_write)&&controller_ready;
 wire command_write=choose_write;
 wire[23:0]command_address=choose_lcd?lcd_address:choose_owned?owned_address:packed_address;
 assign packed_ready=choose_write&&controller_ready;
 assign line_data_valid=rsp_valid&&bus_pending&&bus_kind==B_LCD;
 assign line_data=rsp_data;
 assign owned_state=ostate;
 assign owned_quiescent=ostate==O_IDLE;
 // A held response is physically drained but still owns its client slot.
 // This is not the same proof as owned_quiescent or client delivery.
 assign physical_idle=controller_idle&&!bus_pending&&!line_busy&&!lcd_offer&&packed_empty&&
  (ostate==O_IDLE||ostate==O_HOLD);
 assign response_valid=ostate==O_HOLD&&!reset&&!cancel_live&&!client_fault;
 assign response_data=response_words==8?slot_data:128'd0;
 assign response_owner=owner;assign response_epoch=epoch;
 assign response_frame=frame;assign response_sequence=held_sequence;
 moonshine_burst_packer packer(.clk(clk),.reset(reset),.pixel_valid(pixel_valid&&write_bounds&&!reset),.pixel_ready(packer_pixel_ready),
  .pixel_address(pixel_address),.pixel_data(pixel_data),.force_flush(force_flush),.discard(discard),.empty(packed_empty),
  .burst_valid(packed_valid),.burst_ready(packed_ready),.burst_address(packed_address),.burst_data(packed_data),.burst_mask(packed_mask));
 moonshine_sdram_burst controller(/*CPL_OBS_BEGIN*/.observe_write_beat(observe_write_beat),/*CPL_OBS_END*/.clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(command_valid),.request_ready(controller_ready),
  .request_write(command_write),.request_address(command_address),.request_burst_data(packed_data),.request_burst_mask(packed_mask),
  .response_valid(rsp_valid),.response_data(rsp_data),.idle(controller_idle),
  .sdram_a(sdram_a),.sdram_bs(sdram_bs),.sdram_dq(sdram_dq),.sdram_clk(sdram_clk),.sdram_cke(sdram_cke),.sdram_cs_n(sdram_cs_n),
  .sdram_ras_n(sdram_ras_n),.sdram_cas_n(sdram_cas_n),.sdram_we_n(sdram_we_n),.sdram_ldqm(sdram_ldqm),.sdram_udqm(sdram_udqm));
 // Scheduling-only sidecar. Original admission/cancel/data/drain process below
 // is unchanged. Accepted physical bursts remain indivisible.
 always @(posedge clk)begin
  if(reset)begin
   display_seen<=0;reservation_active<=0;display_age<=0;
   reserved_owner<=0;reserved_epoch<=0;reserved_frame<=0;reserved_token<=0;
   owned_read_streak<=0;write_wait<=0;
   display_expirations<=0;display_rejections<=0;quota_write_grants<=0;age_write_grants<=0;
  end else begin
   if(!packed_valid)write_wait<=0;
   else if(write_wait<WRITE_WAIT_MAX)write_wait<=write_wait+1;
   if(choose_owned&&controller_ready&&owned_read_streak<DISPLAY_READ_QUOTA)
    owned_read_streak<=owned_read_streak+1;
   if(choose_write&&controller_ready)begin
    if(reservation_running&&owned_read_streak>=DISPLAY_READ_QUOTA)quota_write_grants<=quota_write_grants+1;
    if(reservation_running&&write_wait>=WRITE_WAIT_MAX)age_write_grants<=age_write_grants+1;
    owned_read_streak<=0;write_wait<=0;
   end
   if(!display_valid)begin reservation_active<=0;display_seen<=0;end
   else if(reservation_active&&!reservation_running)begin
    reservation_active<=0;display_rejections<=display_rejections+1;
   end else if(reservation_active)begin
    if(display_age>=DISPLAY_MAX_CYCLES-1)begin
     reservation_active<=0;display_expirations<=display_expirations+1;
    end else display_age<=display_age+1;
   end
   // Admission, not an untrusted level alone, creates a lease. Suppressed
   // same-edge request/cancel/fault admission cannot create or renew one.
   if(display_valid&&!display_seen&&request_accept)begin
    display_seen<=1;
    if(display_owner!=0&&display_epoch!=32'hffffffff&&display_frame!=32'hffffffff&&
       display_owner==request_owner&&display_epoch==request_epoch&&display_frame==request_frame)begin
     reservation_active<=1;display_age<=0;
     reserved_owner<=display_owner;reserved_epoch<=display_epoch;reserved_frame<=display_frame;reserved_token<=display_token;
    end else begin reservation_active<=0;display_rejections<=display_rejections+1;end
   end
  end
 end
 always @(posedge clk)begin
  if(reset)begin
   line_busy<=0;lcd_address<=0;lcd_received<=0;bus_pending<=0;bus_kind<=B_NONE;beat<=0;prefer_owned<=1;
   ostate<=O_IDLE;owner<=0;epoch<=0;frame<=0;held_sequence<=0;owned_address<=0;
   cancel_pending<=0;fault_pending<=0;response_status<=GOOD;response_words<=0;
   owned_issue<=0;owned_physical_done<=0;owned_delivered<=0;
  end else begin
   owned_issue<=0;owned_physical_done<=0;owned_delivered<=0;
   if(line_req_valid&&line_req_ready)begin line_busy<=1;lcd_address<=line_req_address;lcd_received<=0;end
   if(command_valid&&controller_ready)begin
    if(choose_write)prefer_owned<=1;
    else begin
     bus_pending<=1;beat<=0;bus_kind<=choose_lcd?B_LCD:B_OWNED;
     if(choose_owned)begin ostate<=O_READING;owned_issue<=1;prefer_owned<=0;end
    end
   end
   if(rsp_valid&&bus_pending)begin
    beat<=beat+1'b1;
    if(bus_kind==B_LCD)begin
     lcd_received<=lcd_received+1'b1;
     if(beat==7)lcd_address<=lcd_address+8;
     if(lcd_received==479)line_busy<=0;
    end else if(bus_kind==B_OWNED)begin
     slot_data[beat*16+:16]<=rsp_data;response_words<=response_words+1'b1;
     if(beat==7)ostate<=O_DRAIN;
    end
    if(beat==7)begin bus_pending<=0;bus_kind<=B_NONE;end
   end
   if(request_accept)begin
    owner<=request_owner;epoch<=request_epoch;frame<=request_frame;held_sequence<=request_sequence;owned_address<=request_address;
    response_words<=0;response_status<=GOOD;cancel_pending<=0;fault_pending<=0;ostate<=O_QUEUED;
   end
   if(ostate==O_DRAIN&&controller_idle&&!bus_pending)begin
    ostate<=O_HOLD;owned_physical_done<=1;
    response_status<=(cancel_pending||cancel_live)?ABORTED:(fault_pending||client_fault)?FAULT:GOOD;
   end
   if(response_valid&&response_ready)begin
    ostate<=O_IDLE;owner<=0;owned_delivered<=1;
   end
   if(client_fault&&ostate!=O_IDLE)begin
    fault_pending<=1;
    if(ostate==O_QUEUED)begin ostate<=O_HOLD;response_status<=FAULT;response_words<=0;end
    else if(ostate==O_HOLD)response_status<=cancel_pending?ABORTED:FAULT;
   end
   if(cancel_live)begin
    cancel_pending<=1;
    if(ostate==O_QUEUED)begin ostate<=O_HOLD;response_status<=ABORTED;response_words<=0;end
    else if(ostate==O_HOLD)response_status<=ABORTED;
   end
  end
 end
endmodule
`default_nettype wire
