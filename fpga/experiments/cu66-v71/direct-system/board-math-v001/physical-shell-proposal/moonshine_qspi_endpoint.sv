`timescale 1ns/1ps
// Always-on, native-app subset of the production HandheldTop host interface.
// Pin protocol: mode 0, DQ0 command, 1/2/4-lane address/data, eight dummy
// BYTES on reads, MSB first, optional per-word byte reversal. clk200 must
// remain 200 MHz regardless of app/SDRAM settings. Validated digital rates:
// writes <=40 MHz, reads <=16 MHz; external pin margins require signoff.
// No external-memory or game-core emulation. Unknown reads return zero;
// unknown writes have no effect. Overlay memory is a separate consumer.
module moonshine_qspi_endpoint (
 input wire clk200, rst_n,
 input wire qspi_sck, qspi_cs_n,
 input wire [3:0] qspi_dq_i,
 output wire [3:0] dq_o, dq_oe,
 input wire [11:0] buttons_native,
 input wire vblank,
 output wire irq_request,
 output reg [3:0] control,
 output wire [11:0] force_buttons_native,
 output reg display_external, color_correct_enable,
 output reg [23:0] overlay_xctrl, overlay_yctrl,
 output reg ov_wr,
 output reg [17:0] ov_addr,
 output reg [15:0] ov_data,
 output reg core_write,core_read,
 output wire [11:0] core_address,
 output reg [31:0] core_wdata,
 input wire [31:0] core_rdata
);
 localparam IDLE=0, COMMAND=1, ADDRESS=2, WRITE=3, DUMMY=4, READ=5, INVALID=6;
 (* ASYNC_REG="TRUE" *) reg [1:0] sck_sync,cs_sync;
 (* ASYNC_REG="TRUE" *) reg [3:0] dq_meta,dq_sync;
 (* ASYNC_REG="TRUE" *) reg [11:0] buttons_meta,buttons_sync;
 (* ASYNC_REG="TRUE" *) reg [1:0] vblank_sync;
 reg prev_sck,prev_cs,prev_vblank;
 reg [11:0] prev_buttons;
 reg [2:0] warmup,state;
 reg seen_idle,tx_active;
 reg [7:0] command;
 reg [31:0] shift_in,address,shift_out;
 reg [11:0] write_address_q;
 assign core_address=core_write ? write_address_q : address[11:0];
 reg [6:0] bits_left,tx_left;
 reg [11:0] forced;
 reg [3:0] irq_enable,irq_flags;
 wire rise=sck_sync[1]&&!prev_sck;
 wire fall=!sck_sync[1]&&prev_sck;
 wire [2:0] lanes=(state==COMMAND) ? 3'd1:
                         command[6:5]==2'd2 ? 3'd4:command[6:5]==2'd1 ? 3'd2:3'd1;
 wire [5:0] word_bits=command[2:1]==2'd2 ? 6'd32:command[2:1]==2'd1 ? 6'd16:6'd8;
 wire [2:0] word_bytes=command[2:1]==2'd2 ? 3'd4:command[2:1]==2'd1 ? 3'd2:3'd1;
 wire [31:0] incoming=(shift_in<<lanes) |
                (lanes==4 ? {28'b0,dq_sync}:lanes==2 ? {30'b0,dq_sync[1:0]}:{31'b0,dq_sync[0]});
 // The native tester mapping is A,B,X,Y,Up,Down,Left,Right,L,R,Start,Select.
 wire [11:0] physical_host={buttons_sync[0],buttons_sync[1],buttons_sync[2],buttons_sync[3],
                           buttons_sync[4],buttons_sync[5],buttons_sync[6],buttons_sync[7],
                           buttons_sync[8],buttons_sync[9],buttons_sync[10],buttons_sync[11]};
 genvar k;
 generate for(k=0;k<12;k=k+1) begin: force_map
   assign force_buttons_native[k]=forced[11-k];
 end endgenerate
 assign irq_request=|(irq_enable&irq_flags);
 // Deassert ownership immediately on raw CS, including while synchronizers
 // still contain an old selected transaction. DQ1 is MISO in single mode.
 assign dq_oe=(!rst_n || qspi_cs_n || !tx_active) ? 4'b0:
               command[6:5]==2'd2 ? 4'b1111:command[6:5]==2'd1 ? 4'b0011:4'b0010;
 wire [31:0] aligned_out=command[2:1]==2'd2 ? shift_out:
                        command[2:1]==2'd1 ? {shift_out[15:0],16'b0}:{shift_out[7:0],24'b0};
 assign dq_o=command[6:5]==2'd2 ? aligned_out[31:28]:
             command[6:5]==2'd1 ? {2'b0,aligned_out[31:30]}:{2'b0,aligned_out[31],1'b0};
 function automatic [31:0] swap_word(input [31:0] d,input [1:0] size,input swap);
 begin
   case(size)
    0: swap_word={24'b0,d[7:0]};
    1: swap_word=swap ? {16'b0,d[7:0],d[15:8]}:{16'b0,d[15:0]};
    default:swap_word=swap ? {d[7:0],d[15:8],d[23:16],d[31:24]}:d;
   endcase
 end endfunction
 reg [15:0] read_address_q;
 reg read_framework_q,read_core_q;
 reg [31:0] read_data;
 reg [31:0] read_data_q;
 // Split address decode from byte swap/serializer selection at 200 MHz.
 // The existing eight dummy bytes leave ample time for this registered view.
 always @(posedge clk200)begin
  if(!rst_n) begin read_data_q<=0;read_address_q<=0;read_framework_q<=0;read_core_q<=0;end
  else begin
   read_address_q<=address[15:0];
   read_framework_q<=address[31:24]==8'h01;read_core_q<=address[31:28]==4'he;
   read_data_q<=read_data;
  end
 end
 always @* begin
   read_data=0;
   if(read_framework_q) case(read_address_q)
    16'h0000:read_data={28'b0,control[3],vblank_sync[1],control[1:0]};
    16'h0004:read_data={20'b0,forced};
    16'h0008:read_data={31'b0,display_external};
    16'h000c:read_data={28'b0,irq_enable};
    16'h0010:read_data={28'b0,irq_flags};
    16'h0014:read_data=0; // No cartridge support in the native tester.
    16'h0018:read_data={31'b0,color_correct_enable};
    16'h001c:read_data={20'b0,physical_host};
    16'h0100:read_data={8'b0,overlay_xctrl};
    16'h0104:read_data={8'b0,overlay_yctrl};
    // Dimensions of native application video, NOT the overlay dimensions.
    16'h0200:read_data={16'd800,16'd480};
    default:read_data=0;
   endcase
   else if(read_core_q)read_data=core_rdata;
 end
 wire [31:0] write_data=swap_word(incoming,command[2:1],command[3]);
 always @(posedge clk200) begin
  if(!rst_n) begin
   sck_sync<=0;cs_sync<=3;dq_meta<=0;dq_sync<=0;
   buttons_meta<=0;buttons_sync<=0;vblank_sync<=0;
   prev_sck<=0;prev_cs<=1;prev_vblank<=0;prev_buttons<=0;
   warmup<=0;seen_idle<=0;tx_active<=0;state<=IDLE;command<=0;
   shift_in<=0;shift_out<=0;address<=0;bits_left<=0;tx_left<=0;
   // JTAG image must start without an ESP32 core-load/enable transaction.
   control<=4'b0011;forced<=0;irq_enable<=4'b0010;irq_flags<=0;
   display_external<=0;color_correct_enable<=0;
   overlay_xctrl<=0;overlay_yctrl<=0;ov_wr<=0;ov_addr<=0;ov_data<=0;
   core_write<=0;core_read<=0;write_address_q<=0;core_wdata<=0;
  end else begin
   sck_sync<={sck_sync[0],qspi_sck};cs_sync<={cs_sync[0],qspi_cs_n};
   dq_meta<=qspi_dq_i;dq_sync<=dq_meta;
   buttons_meta<=buttons_native;buttons_sync<=buttons_meta;
   vblank_sync<={vblank_sync[0],vblank};
   prev_sck<=sck_sync[1];prev_cs<=cs_sync[1];
   prev_buttons<=buttons_sync;prev_vblank<=vblank_sync[1];
   ov_wr<=0;core_write<=0;core_read<=0;
   // Read events use the updated address; write events retain the old address
   // across auto-increment until the bridge samples the registered strobe.
   write_address_q<=address[11:0];
   // Overlay samples address and data only with ov_wr; free-running updates
   // avoid a high-fanout 200 MHz write-enable cone. Event values are unchanged.
   ov_addr<=address[17:0];ov_data<=write_data[15:0];
   if(warmup!=7) warmup<=warmup+1'b1;
   if(warmup==7 && cs_sync[1]) seen_idle<=1;
   if(cs_sync[1]) begin state<=IDLE;shift_out<=0;tx_active<=0;end
   else if(seen_idle && prev_cs) begin
    state<=COMMAND;bits_left<=8;shift_in<=0;shift_out<=0;command<=0;tx_active<=0;
   end else if(seen_idle) begin
    if(rise) begin
     case(state)
      COMMAND:begin
       shift_in<=incoming;bits_left<=bits_left-1'b1;
       if(bits_left==1) begin
        command<=incoming[7:0];shift_in<=0;bits_left<=32;
        state<=(incoming[7]||incoming[6:5]==3||incoming[2:1]==3) ? INVALID:ADDRESS;
       end
      end
      ADDRESS:begin
       shift_in<=incoming;bits_left<=bits_left-lanes;
       if(bits_left==lanes) begin
        address<=incoming;shift_in<=0;
        if(command[0] && incoming[31:28]==4'he)begin core_read<=1;end
        state<=command[0] ? DUMMY:WRITE;
        bits_left<=command[0] ? 7'd64:{1'b0,word_bits};
       end
      end
      DUMMY:begin
       bits_left<=bits_left-lanes;
       if(bits_left==lanes) begin state<=READ;tx_left<=0;end
      end
      WRITE:begin
       shift_in<=incoming;bits_left<=bits_left-lanes;
       if(bits_left==lanes) begin
        shift_in<=0;bits_left<={1'b0,word_bits};
        if(command[4]) address<=address+word_bytes;
        if(address[31:24]==8'h01) case(address[15:0])
         16'h0000:control<=write_data[3:0];
         16'h0004:forced<=write_data[11:0];
         16'h0008:display_external<=write_data[0];
         16'h000c:irq_enable<=write_data[3:0];
         16'h0010:irq_flags<=irq_flags&~write_data[3:0];
         16'h0018:color_correct_enable<=write_data[0];
         16'h0100:overlay_xctrl<=write_data[23:0];
         16'h0104:overlay_yctrl<=write_data[23:0];
         default:begin end
        endcase
        if(address[31:28]==4'he)begin
         core_write<=1;core_wdata<=write_data;
        end
        if(address[31:24]==8'h03 && address[23:18]==0) begin
         ov_wr<=1;ov_addr<=address[17:0];ov_data<=write_data[15:0];
        end
       end
      end
      default:begin end
     endcase
    end
    if(fall && (state==DUMMY || state==READ)) tx_active<=1;
    if(fall && state==READ) begin
     if(tx_left==0) begin
      shift_out<=swap_word(read_data_q,command[2:1],command[3]);
      tx_left<={1'b0,word_bits}-lanes;
      if(command[4])begin
       address<=address+word_bytes;
       // Pipeline the next core snapshot while the current word is shifted.
       if(address[31:28]==4'he)begin core_read<=1;end
      end
     end else begin shift_out<=shift_out<<lanes;tx_left<=tx_left-lanes;end
    end
   end
   // New events win over a simultaneous W1C acknowledgment, as upstream.
   if(buttons_sync!=prev_buttons) irq_flags[1]<=1;
   if(vblank_sync[1]&&!prev_vblank) irq_flags[0]<=1;
  end
 end
endmodule

