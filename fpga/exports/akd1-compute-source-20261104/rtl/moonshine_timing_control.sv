`timescale 1ns/1ps
`default_nettype none
// Four-phase held-value mailbox. Either reset rebaselines the link before send.
// Pixel reset also resets the raster; core reset never changes margin midframe.
module moonshine_timing_control(
 input wire core_clk,core_reset,pixel_clk,pixel_reset,frame_origin,
 input wire bus_write,input wire[11:0]bus_address,input wire[31:0]bus_wdata,
 output reg[31:0]bus_rdata,
 output reg[9:0]pixel_hsync,pixel_vsync,pixel_hstart,pixel_vstart,pixel_htotal,pixel_vtotal
);
 localparam [2:0] LINK_ARM=0,LINK_ONLINE=1,WAIT_APPLY=2,WAIT_CLEAR=3,IDLE=4;
 reg[2:0]state;
 (* DONT_TOUCH="TRUE" *)reg[61:0]requested_value;
 // Intentionally not reset: retain old wire payload until remote cancellation is acknowledged.
 (* DONT_TOUCH="TRUE" *)reg[61:0]transport_payload;
 reg[61:0]applied_value;
 reg[29:0]shadow_h,shadow_v;
 localparam[29:0]H0=30'h02f02804,V0=30'h00a05004,H1=30'h0021dc04,V1=30'h00300804;
 reg applied_valid;
 reg[3:0]last_result;
 reg[7:0]applied_seq;
 reg core_online,request_level;
 reg[6:0]link_watchdog;
 reg pixel_online,pixel_armed,ack_level,pixel_pending;
 (* DONT_TOUCH="TRUE" *)reg[61:0]pending_timing;
 (* ASYNC_REG="TRUE" *)reg[1:0]ack_sync,online_sync,armed_sync;
 (* ASYNC_REG="TRUE" *)reg[1:0]core_online_sync,request_sync;
 function automatic valid_h(input[31:0]v);
 reg[9:0]a,b,c,xor_sum,majority;reg[11:0]sum;
 begin
  a=v[9:0];b=v[19:10];c=v[29:20];
  xor_sum=a^b^c;majority=(a&b)|(a&c)|(b&c);
  sum={2'd0,xor_sum}+{1'd0,majority,1'd0};
  // sum<=543 is exactly sum+480<=1023, without another carry comparator.
  valid_h=(v[31:30]==0 && (|a) && (|c[9:1]) && sum[11:10]==0 && (!sum[9] || sum[8:5]==0));
 end endfunction
 function automatic valid_v(input[31:0]v);
 reg[9:0]a,b,c,xor_sum,majority;reg[11:0]sum;
 begin
  a=v[9:0];b=v[19:10];c=v[29:20];
  xor_sum=a^b^c;majority=(a&b)|(a&c)|(b&c);
  sum={2'd0,xor_sum}+{1'd0,majority,1'd0};
  // sum<=223 is sum+800<=1023; with SYNC>=1, START>=2
  // rejects only SYNC=1,BACK=0. No arithmetic width can wrap.
  valid_v=(v[31:30]==0 && (|a) && (|c) && (a!=10'd1 || (|b)) && sum[11:8]==0 && !(&sum[7:5]));
 end endfunction
 wire write_ready=(state==IDLE && online_sync[1]);
 always @*begin
  bus_rdata=0;
  case(bus_address)
   'h090:bus_rdata=32'h54494d31;
   'h094:bus_rdata={2'd0,shadow_h};
   'h098:bus_rdata={2'd0,shadow_v};
   'h09c:bus_rdata=32'h00010003;
   'h0a0:bus_rdata={2'd0,applied_value[29:0]};
   'h0a4:bus_rdata={2'd0,applied_value[59:30]};
   'h0a8:bus_rdata={applied_seq,4'd0,last_result,5'd0,write_ready,online_sync[1],applied_valid,(state!=IDLE),5'd0,applied_value[61:60]};
   default:begin end
  endcase
 end
 always @(posedge core_clk)begin
  if(core_reset)begin
   state<=LINK_ARM;requested_value<={2'd0,V0,H0};applied_value<={2'd0,V0,H0};shadow_h<=H0;shadow_v<=V0;applied_valid<=0;
   last_result<=0;applied_seq<=0;core_online<=0;request_level<=0;
   ack_sync<=0;online_sync<=0;armed_sync<=0;link_watchdog<=0;
  end else begin
   ack_sync<={ack_sync[0],ack_level};online_sync<={online_sync[0],pixel_online};armed_sync<={armed_sync[0],pixel_armed};
   case(state)
    LINK_ARM:begin
     core_online<=0;request_level<=0;link_watchdog<=0;
     if(armed_sync[1] && !online_sync[1] && !ack_sync[1])begin transport_payload<=requested_value;core_online<=1;state<=LINK_ONLINE;end
    end
    LINK_ONLINE:begin
     if(online_sync[1])begin request_level<=1;state<=WAIT_APPLY;end
     else if(&link_watchdog)begin core_online<=0;request_level<=0;state<=LINK_ARM;applied_valid<=0;last_result<=5;end
     else link_watchdog<=link_watchdog+1'b1;
    end
    WAIT_APPLY:if(ack_sync[1])begin
     applied_value<=requested_value;applied_valid<=1;applied_seq<=applied_seq+1'b1;
     last_result<=2;request_level<=0;state<=WAIT_CLEAR;
    end
    WAIT_CLEAR:if(!ack_sync[1])state<=IDLE;
    IDLE:begin end
    default:begin core_online<=0;request_level<=0;state<=LINK_ARM;applied_valid<=0;last_result<=5;end
   endcase
   // Pixel reset holds its link offline until it has observed our low-online
   // phase; thus no reset pulse can be mistaken for an old completed request.
   if(state!=LINK_ARM && state!=LINK_ONLINE && !online_sync[1])begin
    core_online<=0;request_level<=0;state<=LINK_ARM;applied_valid<=0;last_result<=5;
   end
   if(bus_write)case(bus_address)
    'h094:begin
     if(!valid_h(bus_wdata))last_result<=3;
     else if(!write_ready)last_result<=4;
     else begin shadow_h<=bus_wdata[29:0];last_result<=6;end
    end
    'h098:begin
     if(!valid_v(bus_wdata))last_result<=3;
     else if(!write_ready)last_result<=4;
     else begin shadow_v<=bus_wdata[29:0];last_result<=6;end
    end
    'h09c:begin
     if(bus_wdata>2 || (bus_wdata==2 && (!valid_h({2'd0,shadow_h}) || !valid_v({2'd0,shadow_v}))))last_result<=3;
     else if(!write_ready)last_result<=4;
     else begin
      if(bus_wdata==0)begin requested_value<={2'd0,V0,H0};transport_payload<={2'd0,V0,H0};shadow_h<=H0;shadow_v<=V0;end
      else if(bus_wdata==1)begin requested_value<={2'd1,V1,H1};transport_payload<={2'd1,V1,H1};shadow_h<=H1;shadow_v<=V1;end
      else begin requested_value<={2'd2,shadow_v,shadow_h};transport_payload<={2'd2,shadow_v,shadow_h};end
      request_level<=1;state<=WAIT_APPLY;last_result<=1;
     end
    end
    default:begin end
   endcase
  end
 end
 always @(posedge pixel_clk)begin
  if(pixel_reset)begin
   pixel_hsync<=4;pixel_vsync<=4;pixel_hstart<=14;pixel_vstart<=24;pixel_htotal<=541;pixel_vtotal<=834;pending_timing<={2'd0,V0,H0};pixel_pending<=0;pixel_online<=0;pixel_armed<=0;ack_level<=0;
   core_online_sync<=2'b11;request_sync<=0;
  end else begin
   core_online_sync<={core_online_sync[0],core_online};request_sync<={request_sync[0],request_level};
   if(!core_online_sync[1])begin
    pixel_online<=0;pixel_armed<=1;pixel_pending<=0;ack_level<=0;
   end else if(pixel_armed)begin pixel_online<=1;pixel_armed<=0;ack_level<=0;pixel_pending<=0;end
   else if(pixel_online)begin
    if(!request_sync[1])begin ack_level<=0;pixel_pending<=0;end
    else if(!ack_level && !pixel_pending)begin pending_timing<=transport_payload;pixel_pending<=1;end
    else if(pixel_pending && frame_origin)begin pixel_hsync<=pending_timing[9:0];pixel_vsync<=pending_timing[39:30];
     pixel_hstart<={2'd0,pending_timing[9:0]}+{2'd0,pending_timing[19:10]};
     pixel_vstart<={2'd0,pending_timing[39:30]}+{2'd0,pending_timing[49:40]};
     pixel_htotal<={2'd0,pending_timing[9:0]}+{2'd0,pending_timing[19:10]}+{2'd0,pending_timing[29:20]}+12'd480;
     pixel_vtotal<={2'd0,pending_timing[39:30]}+{2'd0,pending_timing[49:40]}+{2'd0,pending_timing[59:50]}+12'd800;
     ack_level<=1;pixel_pending<=0;end
   end
  end
 end
endmodule
`default_nettype wire
