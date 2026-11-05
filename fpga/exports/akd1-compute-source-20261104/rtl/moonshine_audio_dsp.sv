`timescale 1ns/1ps
`default_nettype none
// Same DSP offset-zero framing as the existing AudioDspTransmitter:
// 608 MCLK/frame, BCLK=MCLK/8, left then right MSB-first, sampled falling BCLK.
module moonshine_audio_dsp(
 input wire clk,reset,input wire[31:0]pcm,
 output wire sample_tick,output reg bclk=1,output reg wclk=0,output wire din
);
 reg[9:0]frame_counter=0;reg[1:0]bit_counter=0;reg[31:0]shift=0;
 assign sample_tick=frame_counter==607;
 assign din=shift[31];
 always @(posedge clk)begin
  if(reset)begin frame_counter<=0;bit_counter<=0;shift<=0;bclk<=1;wclk<=0;end
  else begin
   frame_counter<=sample_tick ? 0:frame_counter+1'b1;
   bit_counter<=bit_counter+1'b1;
   if(bit_counter==3)begin
    bclk<=!bclk;
    if(!bclk)begin shift<={shift[30:0],1'b0};wclk<=0;end
   end
   if(sample_tick)begin shift<={pcm[15:0],pcm[31:16]};wclk<=1;end
  end
 end
endmodule
`default_nettype wire
