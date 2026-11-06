// V72 masked BL8 read/write controller; caller validates aligned physical bursts.
`timescale 1ns/1ps
`default_nettype none
// Conservative100MHz SDR SDRAM controller. Burst8 reads and masked writes,
// four independently tracked open rows, bounded refresh and explicit recovery.
// Mode register BL8/CAS3/programmed write burst. Addresses are16-bit WORD addresses.
module cu72_sdram_controller #(
 parameter integer POWERUP_CYCLES=20000, REFRESH_CYCLES=750
)(
 input wire clk,read_clk,reset,input wire request_valid,output wire request_ready,
 input wire request_write,input wire[23:0]request_address,input wire[127:0]request_burst_data,input wire[15:0]request_byte_enable,
 output reg response_valid,output reg[15:0]response_data,output wire idle,
 output reg[12:0]sdram_a,output reg[1:0]sdram_bs,inout wire[15:0]sdram_dq,
 output wire sdram_clk,output wire[1:0]sdram_cke,sdram_cs_n,
 output reg sdram_ras_n,sdram_cas_n,sdram_we_n,output reg sdram_ldqm,sdram_udqm
);
 localparam INIT_WAIT=0,INIT_PRE=1,INIT_REF=2,INIT_MRS=3,WAITING=4,
  IDLE=5,PRECHARGE=6,ACTIVATE=7,RW_CMD=8,READ_WAIT=9,READ_BURST=10,
  WRITE_BURST=11,REFRESH_PRE=12,REFRESH=13;
 reg[3:0]state,next_state;reg[15:0]delay,refresh_count;reg[1:0]init_refs;
 reg[3:0]open;reg[12:0]rows[0:3];reg[23:0]address;reg[127:0]write_buffer;reg[15:0]byte_enable;
 reg is_write;reg[2:0]beat;
 wire[15:0]dq_input;
 wire write_cycle=((state==RW_CMD && is_write)||state==WRITE_BURST) && !reset;
 wire[15:0]write_word=write_buffer[beat*16 +:16];
 wire[1:0]write_dqm=~byte_enable[beat*2 +:2];
 // The routed round-trip window requires a279-degree read clock (7.75ns
 // after the command rising edge), between the original negedge's setup
 // failure and the next posedge's hold failure. Retiming uses the following
 // command negedge, then posedge. External budgets and frequencies are fixed.
 (* IOB="TRUE" *)reg[15:0]dq_capture;
 reg[15:0]dq_retime;
 always @(posedge read_clk)dq_capture<=dq_input;
 always @(negedge clk)dq_retime<=dq_capture;
 `ifdef SIMULATION
 reg drive;reg[15:0]dq_out;
 always @(posedge clk)begin drive<=write_cycle;dq_out<=write_word;end
 assign sdram_dq=drive ? dq_out:16'bz;
 assign dq_input=sdram_dq;
 `else
 // Separate data and T ODDRs occupy each pad's OLOGIC. D1=D2 makes them
 // posedge-only SDR registers; no inverted shared fabric OE fanout remains.
 genvar d;generate for(d=0;d<16;d=d+1)begin:dq_io
  wire out,t;
  (* DONT_TOUCH="TRUE" *) ODDR #(.DDR_CLK_EDGE("SAME_EDGE"),.INIT(1'b0)) data_out(.C(clk),.CE(1'b1),.D1(reset?1'b0:write_word[d]),.D2(reset?1'b0:write_word[d]),.R(1'b0),.S(1'b0),.Q(out));
  (* DONT_TOUCH="TRUE" *) ODDR #(.DDR_CLK_EDGE("SAME_EDGE"),.INIT(1'b1)) tri_out(.C(clk),.CE(1'b1),.D1(!write_cycle),.D2(!write_cycle),.R(1'b0),.S(1'b0),.Q(t));
  IOBUF pad(.IO(sdram_dq[d]),.I(out),.T(t),.O(dq_input[d]));
 end endgenerate
 `endif
 assign sdram_cke=reset ? 2'b00:2'b01;
 assign sdram_cs_n=2'b10;
 assign request_ready=!reset && state==IDLE && refresh_count<16'(REFRESH_CYCLES);
 assign idle=!reset && state==IDLE;
 `ifdef SIMULATION
 assign sdram_clk=~clk;
 `else
 ODDR #(.DDR_CLK_EDGE("SAME_EDGE")) forward_clock(.C(clk),.CE(1'b1),.D1(1'b0),.D2(1'b1),.R(1'b0),.S(1'b0),.Q(sdram_clk));
 `endif
 task wait_cycles(input[15:0]n,input[3:0]after_state);
 begin delay<=n;next_state<=after_state;state<=WAITING;end endtask
 always @(posedge clk)begin
  if(reset)begin
   state<=INIT_WAIT;next_state<=INIT_PRE;delay<=16'(POWERUP_CYCLES);refresh_count<=0;init_refs<=0;
   open<=0;address<=0;write_buffer<=0;byte_enable<=0;is_write<=0;beat<=0;
   response_valid<=0;response_data<=0;sdram_a<=0;sdram_bs<=0;
   sdram_ras_n<=1;sdram_cas_n<=1;sdram_we_n<=1;sdram_ldqm<=0;sdram_udqm<=0;
  end else begin
   sdram_ras_n<=1;sdram_cas_n<=1;sdram_we_n<=1;
   response_valid<=0;sdram_ldqm<=0;sdram_udqm<=0;
   if(refresh_count!=65535)refresh_count<=refresh_count+1;
   case(state)
    INIT_WAIT:if(delay==0)state<=INIT_PRE;else delay<=delay-1'b1;
    INIT_PRE:begin sdram_ras_n<=0;sdram_we_n<=0;sdram_a<=13'h400;wait_cycles(2,INIT_REF);end
    INIT_REF:begin
     sdram_ras_n<=0;sdram_cas_n<=0;init_refs<=init_refs+1;
     if(init_refs==1)wait_cycles(8,INIT_MRS);else wait_cycles(8,INIT_REF);
    end
    INIT_MRS:begin sdram_ras_n<=0;sdram_cas_n<=0;sdram_we_n<=0;sdram_a<=13'h033;sdram_bs<=0;
     refresh_count<=0;wait_cycles(2,IDLE);end
    WAITING:if(delay==0)state<=next_state;else delay<=delay-1'b1;
    IDLE:begin
     if(refresh_count>=16'(REFRESH_CYCLES))state<=REFRESH_PRE;
     else if(request_valid)begin
      address<=request_address;write_buffer<=request_burst_data;byte_enable<=request_byte_enable;is_write<=request_write;beat<=0;
      `ifdef SIMULATION
      if(request_address[2:0]!=0)$fatal(1,"unaligned controller request");
      `endif
      if(open[request_address[23:22]])begin
       if(rows[request_address[23:22]]==request_address[21:9])state<=RW_CMD;
       else state<=PRECHARGE;
      end else state<=ACTIVATE;
     end
    end
    PRECHARGE:begin
     sdram_ras_n<=0;sdram_we_n<=0;sdram_a<=0;sdram_bs<=address[23:22];open[address[23:22]]<=0;
     wait_cycles(2,ACTIVATE);
    end
    ACTIVATE:begin
     sdram_ras_n<=0;sdram_a<=address[21:9];sdram_bs<=address[23:22];
     open[address[23:22]]<=1;rows[address[23:22]]<=address[21:9];wait_cycles(2,RW_CMD);
    end
    RW_CMD:begin
     sdram_a<={4'b0000,address[8:0]};sdram_bs<=address[23:22];sdram_cas_n<=0;
     if(is_write)begin sdram_we_n<=0;sdram_ldqm<=write_dqm[0];sdram_udqm<=write_dqm[1];beat<=1;state<=WRITE_BURST;end
     else begin delay<=5;state<=READ_WAIT;beat<=0;end
    end
    WRITE_BURST:begin
     sdram_ldqm<=write_dqm[0];sdram_udqm<=write_dqm[1];
     if(beat==7)wait_cycles(3,IDLE);else beat<=beat+1'b1;
    end
    READ_WAIT:if(delay==0)begin
     response_valid<=1;response_data<=dq_retime;beat<=1;state<=READ_BURST;
    end else delay<=delay-1'b1;
    READ_BURST:begin
     response_valid<=1;response_data<=dq_retime;beat<=beat+1'b1;
     if(beat==7)state<=IDLE;
    end
    REFRESH_PRE:begin
     sdram_ras_n<=0;sdram_we_n<=0;sdram_a<=13'h400;open<=0;wait_cycles(2,REFRESH);
    end
    REFRESH:begin sdram_ras_n<=0;sdram_cas_n<=0;refresh_count<=0;wait_cycles(8,IDLE);end
    default:state<=INIT_WAIT;
   endcase
  end
 end
endmodule
`default_nettype wire
