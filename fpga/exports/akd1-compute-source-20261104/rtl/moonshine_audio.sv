`timescale 1ns/1ps
`default_nettype none
// Eight fixed512-frame slots. RAM is written only by the core and read only
// by pclk. COMMIT and last-frame consumption each advance ONE Gray slot token.
// No sample/descriptor multi-bit mailbox crosses clocks. A sidebit marks LAST.
module moonshine_audio(
 input wire core_clk,pixel_clk,arst,
 input wire bus_write,input wire[11:0]bus_address,input wire[31:0]bus_wdata,
 input wire transport_fault,
 output reg[31:0]bus_rdata,output wire dac_bclk,dac_wclk,dac_din
);
 (* ASYNC_REG="TRUE" *)reg[2:0]crst=7,prst=7;
 always @(posedge core_clk or posedge arst)if(arst)crst<=7;else crst<={crst[1:0],1'b0};
 always @(posedge pixel_clk or posedge arst)if(arst)prst<=7;else prst<={prst[1:0],1'b0};
 (* ram_style="block" *)reg[32:0]samples[0:4095];
 reg[32:0]sample_q;
 reg[3:0]wp=0,wgray=0,rp=0,rgray=0;
 (* ASYNC_REG="TRUE" *)reg[3:0]rg1=0,rg2=0,wg1=0,wg2=0;
 (* ASYNC_REG="TRUE" *)reg[1:0]online_sync=0,ack_sync=0,enable_sync=0,playing_sync=0,rebuffer_sync=0;
 reg core_online=0,pixel_online=0,enabled=0,playing=0,rebuffer=1;
 reg[2:0]link_state=0;reg[2:0]settle=0;
 reg[8:0]read_index=0;
 reg[9:0]frames=0,staged=0,stage_length=0;
 reg[31:0]sequence_number=0,expected_crc=0,session=0,stage_sequence=0,stage_session=0,stage_crc=0;
 reg staging=0,poisoned=0,sequence_valid=0;
 reg[31:0]published_epoch=0,consumed_epoch=0,consumed_gray=0;
 (* ASYNC_REG="TRUE" *)reg[31:0]consumed_meta=0,consumed_sync=0;
 reg[31:0]committed=0,last_sequence=0,last_session=0,rejected=0;
 reg[7:0]result=0;
 reg[31:0]played=0,underruns=0,played_gray=0,underrun_gray=0;
 (* ASYNC_REG="TRUE" *)reg[31:0]played_meta=0,played_sync=0,underrun_meta=0,underrun_sync=0;
 function automatic[3:0]ungray4(input[3:0]v);integer i;begin for(i=0;i<4;i=i+1)ungray4[i]=^(v>>i);end endfunction
 function automatic[31:0]ungray32(input[31:0]v);integer i;begin for(i=0;i<32;i=i+1)ungray32[i]=^(v>>i);end endfunction
 function automatic[31:0]crc_word(input[31:0]crc,input[31:0]word_value);
 reg[31:0]v;integer j,k;begin v=crc;for(j=0;j<4;j=j+1)begin v=v^{24'd0,word_value[j*8+:8]};for(k=0;k<8;k=k+1)v=v[0] ? (v>>1)^32'hedb88320:v>>1;end crc_word=v;end endfunction
 wire[31:0]sequence_delta=sequence_number-last_sequence;
 wire ready=link_state==4 && ack_sync[1];
 wire[3:0]queued=wp-ungray4(rg2);
 wire[3:0]credits=ready ? 4'd8-queued-{3'd0,staging}:0;
 wire[3:0]audio_queued=ungray4(wg2)-rp;
 wire available=rgray!=wg2;
 wire sample_tick;
 wire[31:0]output_pcm=(pixel_online && online_sync[1] && enable_sync[1] && playing && available)?sample_q[31:0]:32'd0;
 moonshine_audio_dsp transmitter(.clk(pixel_clk),.reset(prst[2]),.pcm(output_pcm),.sample_tick(sample_tick),.bclk(dac_bclk),.wclk(dac_wclk),.din(dac_din));
 // Always-enabled synchronous read infers a genuine dual-clock BRAM read port.
 always @(posedge pixel_clk)sample_q<=samples[{rp[2:0],read_index}];
 always @*begin
  bus_rdata=0;
  case(bus_address)
   'h300:bus_rdata=32'h41504331;'h304:bus_rdata=32'h00010001;
   'h30c:bus_rdata={16'd0,result,1'b0,sequence_valid,!ready,rebuffer_sync[1],playing_sync[1],enabled,staging,ready};
   'h310:bus_rdata={22'd0,frames};'h314:bus_rdata=sequence_number;'h318:bus_rdata=expected_crc;'h31c:bus_rdata=session;
   'h320:bus_rdata={6'd0,staged,4'd0,queued,4'd0,credits};
   'h324:bus_rdata=committed;'h328:bus_rdata=last_sequence;'h32c:bus_rdata=last_session;'h330:bus_rdata=rejected;
   'h334:bus_rdata=ungray32(played_sync);'h338:bus_rdata=ungray32(underrun_sync);
   'h348:bus_rdata=ready ? published_epoch-ungray32(consumed_sync):32'hffffffff;
   'h33c:bus_rdata=4096;'h340:bus_rdata=176171875;'h344:bus_rdata=3648;
   default:bus_rdata=0;
  endcase
 end
 // Flush: hold published pointer until pixel side observes offline and resets
 // its pointer, then reset producer and wait four cycles before rearming.
 always @(posedge core_clk)begin
  if(crst[2])begin
   wp<=0;wgray<=0;rg1<=0;rg2<=0;ack_sync<=0;core_online<=0;enabled<=0;link_state<=0;settle<=0;
   frames<=0;sequence_number<=0;expected_crc<=0;session<=0;stage_length<=0;stage_sequence<=0;stage_session<=0;stage_crc<=0;
   staging<=0;poisoned<=0;staged<=0;sequence_valid<=0;committed<=0;last_sequence<=0;last_session<=0;rejected<=0;result<=0;
   published_epoch<=0;consumed_meta<=0;consumed_sync<=0;
   playing_sync<=0;rebuffer_sync<=0;played_meta<=0;played_sync<=0;underrun_meta<=0;underrun_sync<=0;
  end else begin
   rg1<=rgray;rg2<=rg1;ack_sync<={ack_sync[0],pixel_online};
   playing_sync<={playing_sync[0],playing};rebuffer_sync<={rebuffer_sync[0],rebuffer};
   consumed_meta<=consumed_gray;consumed_sync<=consumed_meta;
   played_meta<=played_gray;played_sync<=played_meta;underrun_meta<=underrun_gray;underrun_sync<=underrun_meta;
   case(link_state)
    0:begin core_online<=0;if(!ack_sync[1])begin wp<=0;wgray<=0;published_epoch<=0;settle<=0;link_state<=1;end end
    1:if(settle==4)begin core_online<=1;link_state<=2;end else settle<=settle+1'b1;
    2:if(ack_sync[1])link_state<=4;
    default:;
   endcase
   if(transport_fault)begin enabled<=0;staging<=0;staged<=0;sequence_valid<=0;core_online<=0;link_state<=0;result<=5;end
   else if(bus_write)begin
    if(bus_address=='h308 && bus_wdata==0)begin enabled<=0;staging<=0;staged<=0;poisoned<=0;sequence_valid<=0;core_online<=0;link_state<=0;result<=5;end
    else if(bus_address=='h308)begin
     if(!ready)begin rejected<=rejected+1;result<=7;end
     else case(bus_wdata)
      1:begin enabled<=1;result<=1;end
      2:begin
       if(staging)begin rejected<=rejected+1;result<=7;end
       else if(frames==0 || frames>512)begin rejected<=rejected+1;result<=6;end
       else if(sequence_valid && (sequence_delta==0 || sequence_delta[31]))begin rejected<=rejected+1;result<=11;end
       else if(credits==0)begin rejected<=rejected+1;result<=8;end
       else begin staging<=1;staged<=0;poisoned<=0;stage_length<=frames;stage_sequence<=sequence_number;stage_session<=session;stage_crc<=32'hffffffff;result<=2;end
      end
      3:begin
       if(!staging || poisoned || staged!=stage_length)begin staging<=0;staged<=0;rejected<=rejected+1;result<=9;end
       else if((stage_crc^32'hffffffff)!=expected_crc)begin staging<=0;staged<=0;rejected<=rejected+1;result<=10;end
       else begin wp<=wp+1'b1;wgray<=((wp+1'b1)^((wp+1'b1)>>1));staging<=0;staged<=0;committed<=committed+1;published_epoch<=published_epoch+stage_length;last_sequence<=stage_sequence;last_session<=stage_session;sequence_valid<=1;result<=3;end
      end
      4:begin staging<=0;staged<=0;poisoned<=0;result<=4;end
      default:begin rejected<=rejected+1;result<=6;end
     endcase
    end else if(bus_address=='h380)begin
     if(!ready || !staging || staged>=stage_length)begin poisoned<=1;rejected<=rejected+1;result<=9;end
     else begin samples[{wp[2:0],staged[8:0]}]<={staged==stage_length-1'b1,bus_wdata};staged<=staged+1'b1;stage_crc<=crc_word(stage_crc,bus_wdata);end
    end else if(bus_address=='h310 || bus_address=='h314 || bus_address=='h318 || bus_address=='h31c)begin
     if(!ready || staging)begin rejected<=rejected+1;result<=7;end
     else case(bus_address)
      'h310:if(bus_wdata==0 || bus_wdata>512)begin rejected<=rejected+1;result<=6;end else frames<=bus_wdata[9:0];
      'h314:sequence_number<=bus_wdata;
      'h318:expected_crc<=bus_wdata;
      'h31c:if(queued!=0 || enabled)begin rejected<=rejected+1;result<=12;end else begin session<=bus_wdata;sequence_valid<=0;end
     endcase
    end
   end
  end
 end
 always @(posedge pixel_clk)begin
  if(prst[2])begin
   rp<=0;rgray<=0;wg1<=0;wg2<=0;online_sync<=0;enable_sync<=0;pixel_online<=0;
   consumed_epoch<=0;consumed_gray<=0;playing<=0;rebuffer<=1;read_index<=0;played<=0;underruns<=0;played_gray<=0;underrun_gray<=0;
  end else begin
   wg1<=wgray;wg2<=wg1;online_sync<={online_sync[0],core_online};enable_sync<={enable_sync[0],enabled};
   if(!online_sync[1])begin pixel_online<=0;rp<=0;rgray<=0;read_index<=0;consumed_epoch<=0;consumed_gray<=0;playing<=0;rebuffer<=1;end
   else begin
    pixel_online<=1;
    if(!enable_sync[1])begin playing<=0;rebuffer<=1;end
    else if(sample_tick)begin
     if(!playing)begin if(audio_queued>=2)begin playing<=1;rebuffer<=0;end end
     else if(!available)begin playing<=0;rebuffer<=1;underruns<=underruns+1'b1;underrun_gray<=(underruns+1'b1)^((underruns+1'b1)>>1);end
     else begin
      consumed_epoch<=consumed_epoch+1'b1;consumed_gray<=(consumed_epoch+1'b1)^((consumed_epoch+1'b1)>>1);
      played<=played+1'b1;played_gray<=(played+1'b1)^((played+1'b1)>>1);
      if(sample_q[32])begin rp<=rp+1'b1;rgray<=((rp+1'b1)^((rp+1'b1)>>1));read_index<=0;end
      else read_index<=read_index+1'b1;
     end
    end
   end
  end
 end
endmodule
`default_nettype wire
