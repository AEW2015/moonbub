`timescale 1ns/1ps
`default_nettype none
// Sequential private diagnostic composition with real bounded staging RAM.
// No ACK, publication, advertised codec capability or external-memory lease.
module cp23_key_private_join(
 input wire clk,reset,start_valid,output wire start_ready,input wire[63:0]start_owner,
 input wire[31:0]start_epoch,start_frame,start_generation,start_bytes,
 input wire in_valid,output wire in_ready,input wire[7:0]in_byte,input wire in_last,
 input wire abort_valid,input wire[63:0]abort_owner,input wire[31:0]abort_epoch,abort_frame,output wire abort_rejected,
 output wire yuv_valid,input wire yuv_ready,output wire[7:0]yuv_sample,output wire[1:0]yuv_plane,output wire[15:0]yuv_x,yuv_y,output wire yuv_last,
 output wire hud_valid,input wire hud_ready,output wire[15:0]hud_word,hud_index,hud_x,hud_y,output wire[1:0]hud_rect,
 output wire[63:0]output_owner,output wire[31:0]output_epoch,output_frame,output_generation,
 output wire result_valid,input wire result_ready,output wire[63:0]result_owner,output wire[31:0]result_epoch,result_frame,result_generation,
 output reg candidate_checked,output reg[3:0]result_stage,output reg[7:0]result_code,
 output reg[127:0]base_tag,hud_tag,output wire[31:0]stored_bytes,yuv_words,hud_words,
 output wire ack_valid,publication_valid,profile_advertised,output wire child_quiescent
);
 localparam IDLE=0,LOAD=1,OSTART=2,OFEED=3,OWAIT=4,BSTART=5,BFEED=6,BWAIT=7,HSTART=8,HFEED=9,HWAIT=10,CANCEL=11,DRAIN=12,RESULT=13;
 reg[3:0]state=IDLE;reg[63:0]owner;reg[31:0]epoch,frame,generation,total,wcount,ycount,hcount,nb,nh;
 reg complete_store,outer_ok,base_ok,hud_ok,last_yuv;
 reg[7:0]packet_ram[0:49151];reg[7:0]ram_data,byte_data;reg byte_valid,read_pending;reg[15:0]read_addr,range_end;
 wire cancel_live=abort_valid&&state!=IDLE&&abort_owner==owner&&abort_epoch==epoch&&abort_frame==frame;
 wire cancel_incoming=abort_valid&&state==IDLE&&start_valid&&abort_owner==start_owner&&abort_epoch==start_epoch&&abort_frame==start_frame;
 wire blocked=reset||cancel_live||state==CANCEL||state==DRAIN||state==RESULT;
 assign abort_rejected=abort_valid&&!cancel_live&&!cancel_incoming;
 assign start_ready=state==IDLE&&!reset&&!cancel_incoming&&child_quiescent;
 assign in_ready=state==LOAD&&!reset&&!cancel_live&&wcount<total&&wcount<49152;
 assign result_valid=state==RESULT&&!reset&&!cancel_live;
 assign result_owner=owner;assign result_epoch=epoch;assign result_frame=frame;assign result_generation=generation;
 assign output_owner=owner;assign output_epoch=epoch;assign output_frame=frame;assign output_generation=generation;
 assign stored_bytes=wcount;assign yuv_words=ycount;assign hud_words=hcount;
 assign ack_valid=0;assign publication_valid=0;assign profile_advertised=0;
 wire feed_state=state==OFEED||state==BFEED||state==HFEED;
 wire read_enable=feed_state&&complete_store&&!byte_valid&&!read_pending&&read_addr<range_end&&!reset&&!cancel_live;
 // RAM read-data is not reset. Validity and complete fresh-write-before-read gate visibility.
 always @(posedge clk)begin
  if(in_valid&&in_ready)packet_ram[wcount[15:0]]<=in_byte;
  if(read_enable)ram_data<=packet_ram[read_addr];
 end
 wire os,oi,ov,oa,ocheck,osupported,oknown;wire[3:0]ocode;wire[63:0]oo;wire[31:0]oe,ofr,onb,onh,ocount;
 wire bs,bi,bsv,bcv,bev;wire[63:0]bso,bco,beo;wire[31:0]bse,bsf,bce,bcf;wire[127:0]btag;wire[3:0]bestage;wire[7:0]becode;
 wire hs,hi,hv,hwv,ha,hchecked;wire[3:0]hcode;wire[63:0]hwo,hro;wire[31:0]hwe,hwf,hwg,hre,hrf,hrg,hdwords,hreceived;wire[127:0]htag;
 wire bphase=state==BFEED||state==BWAIT,hphase=state==HFEED||state==HWAIT;
 wire bid=bso==owner&&bse==epoch&&bsf==frame;
 wire hid=hwo==owner&&hwe==epoch&&hwf==frame&&hwg==generation;
 wire oid=oo==owner&&oe==epoch&&ofr==frame;
 wire bcid=bco==owner&&bce==epoch&&bcf==frame;
 wire hrid=hro==owner&&hre==epoch&&hrf==frame&&hrg==generation;
 wire child_abort=state==CANCEL||cancel_live;
 wire oready=(state==OWAIT||state==DRAIN)&&ov&&oid&&!reset&&!cancel_live;
 wire bready=state==BWAIT&&bcv&&bcid&&!reset&&!cancel_live;
 wire hready=(state==HWAIT||state==DRAIN)&&hv&&hrid&&!reset&&!cancel_live;
 cp23_envelope outer(.clk(clk),.reset(reset),.start_valid(state==OSTART&&!blocked),.start_ready(os),.start_owner(owner),.start_epoch(epoch),.start_frame(frame),.start_bytes(total),.in_valid(state==OFEED&&byte_valid&&!blocked),.in_ready(oi),.in_byte(byte_data),.in_last(read_addr==range_end-1),.abort_valid(child_abort),.abort_owner(owner),.abort_epoch(epoch),.abort_frame(frame),.abort_rejected(oa),.result_valid(ov),.result_ready(oready),.result_code(ocode),.envelope_checked(ocheck),.payload_supported(osupported),.component_magic_known(oknown),.result_owner(oo),.result_epoch(oe),.result_frame(ofr),.base_bytes(onb),.hud_bytes(onh),.received_bytes(ocount));
 ar03_key_tagged base(.clk(clk),.reset(reset),.abort(child_abort),.start_valid(state==BSTART&&!blocked),.start_ready(bs),.start_owner(owner),.start_bytes(nb),.start_epoch(epoch),.in_valid(state==BFEED&&byte_valid&&!blocked),.in_ready(bi),.in_byte(byte_data),.in_last(read_addr==range_end-1),.sample_valid(bsv),.sample_ready(yuv_ready&&bphase&&bid&&!blocked),.sample(yuv_sample),.sample_owner(bso),.sample_epoch(bse),.sample_frame(bsf),.sample_plane(yuv_plane),.sample_x(yuv_x),.sample_y(yuv_y),.sample_last(yuv_last),.completion_valid(bcv),.completion_ready(bready),.completion_owner(bco),.completion_epoch(bce),.completion_frame(bcf),.completion_tag(btag),.error_valid(bev),.error_ready(1'b0),.error_stage(bestage),.error_code(becode),.error_owner(beo));
 hc22_key_hud hud(.clk(clk),.reset(reset),.start_valid(state==HSTART&&!blocked),.start_ready(hs),.start_owner(owner),.start_epoch(epoch),.start_frame(frame),.start_generation(generation),.start_bytes(nh),.in_valid(state==HFEED&&byte_valid&&!blocked),.in_ready(hi),.in_byte(byte_data),.in_last(read_addr==range_end-1),.abort_valid(child_abort),.abort_owner(owner),.abort_epoch(epoch),.abort_frame(frame),.abort_rejected(ha),.word_valid(hwv),.word_ready(hud_ready&&hphase&&hid&&!blocked),.word_data(hud_word),.word_index(hud_index),.word_x(hud_x),.word_y(hud_y),.word_rect(hud_rect),.word_owner(hwo),.word_epoch(hwe),.word_frame(hwf),.word_generation(hwg),.result_valid(hv),.result_ready(hready),.result_code(hcode),.candidate_checked(hchecked),.result_owner(hro),.result_epoch(hre),.result_frame(hrf),.result_generation(hrg),.decoded_words(hdwords),.received_bytes(hreceived),.result_tag(htag));
 assign yuv_valid=bsv&&bphase&&bid&&!blocked;assign hud_valid=hwv&&hphase&&hid&&!blocked;
 assign child_quiescent=os&&bs&&hs&&!ov&&!bcv&&!bev&&!bsv&&!hv&&!hwv;
 wire byte_ready=state==OFEED?oi:state==BFEED?bi:state==HFEED?hi:1'b0;
 task failure(input[3:0]s,input[7:0]c);begin state<=CANCEL;result_stage<=s;result_code<=c;candidate_checked<=0;base_tag<=0;hud_tag<=0;outer_ok<=0;base_ok<=0;hud_ok<=0;byte_valid<=0;read_pending<=0;end endtask
 task begin_range(input[15:0]first,last,input[3:0]nextstate);begin read_addr<=first;range_end<=last;byte_valid<=0;read_pending<=0;state<=nextstate;end endtask
 always @(posedge clk)begin
  if(reset)begin state<=IDLE;owner<=0;epoch<=0;frame<=0;generation<=0;total<=0;wcount<=0;ycount<=0;hcount<=0;nb<=0;nh<=0;complete_store<=0;outer_ok<=0;base_ok<=0;hud_ok<=0;last_yuv<=0;byte_valid<=0;read_pending<=0;read_addr<=0;range_end<=0;candidate_checked<=0;result_stage<=0;result_code<=0;base_tag<=0;hud_tag<=0;end
  else if(cancel_live)failure(0,8);
  else begin
   read_pending<=read_enable;
   if(read_pending)begin byte_data<=ram_data;byte_valid<=1;end
   if(feed_state&&byte_valid&&byte_ready)begin
    byte_valid<=0;read_addr<=read_addr+1;
    if(read_addr==range_end-1)state<=state==OFEED?OWAIT:state==BFEED?BWAIT:HWAIT;
   end
   if(yuv_valid&&yuv_ready)begin ycount<=ycount+1;if(yuv_last)last_yuv<=1;end
   if(hud_valid&&hud_ready)hcount<=hcount+1;
   case(state)
    IDLE:if(start_valid&&start_ready)begin
     owner<=start_owner;epoch<=start_epoch;frame<=start_frame;generation<=start_generation;total<=start_bytes;wcount<=0;ycount<=0;hcount<=0;nb<=0;nh<=0;complete_store<=0;outer_ok<=0;base_ok<=0;hud_ok<=0;last_yuv<=0;byte_valid<=0;read_pending<=0;candidate_checked<=0;result_stage<=0;result_code<=0;base_tag<=0;hud_tag<=0;
     if(start_owner==0||start_epoch==0||start_epoch==32'hffffffff||start_frame==32'hffffffff||start_generation==32'hffffffff||start_bytes<57||start_bytes>49152)failure(1,1);else state<=LOAD;
    end
    LOAD:if(in_valid&&in_ready)begin
     wcount<=wcount+1;
     if(in_last!=(wcount==total-1))failure(1,7);
     else if(wcount==total-1)begin complete_store<=1;state<=OSTART;end
    end
    OSTART:if(os)begin_range(0,total[15:0],OFEED);
    OWAIT:if(ov)begin
     if(!oid||ocode!=9||!ocheck||osupported||!oknown||ocount!=total||onb+onh+57!=total)failure(2,{4'd0,ocode});
     else begin outer_ok<=1;nb<=onb;nh<=onh;state<=BSTART;end
    end
    BSTART:if(bs)begin_range(16'd53,16'd53+nb[15:0],BFEED);
    BWAIT:if(bcv)begin
     if(!bcid||ycount!=518400||!last_yuv)failure(3,8'd255);
     else begin base_ok<=1;base_tag<=btag;state<=HSTART;end
    end
    HSTART:if(hs)begin_range(16'd53+nb[15:0],16'd53+nb[15:0]+nh[15:0],HFEED);
    HWAIT:if(hv)begin
     if(!hrid||hcode!=0||!hchecked||hdwords!=21120||hcount!=21120||hreceived!=nh)failure(4,{4'd0,hcode});
     else begin hud_ok<=1;hud_tag<=htag;state<=DRAIN;end
    end
    CANCEL:begin state<=DRAIN;byte_valid<=0;read_pending<=0;end
    DRAIN:if(child_quiescent&&!byte_valid&&!read_pending)begin
     candidate_checked<=outer_ok&&base_ok&&hud_ok;
     state<=RESULT;
    end
    RESULT:if(result_valid&&result_ready)begin state<=IDLE;complete_store<=0;end
   endcase
   // Rejected children may terminate before consuming their entire replay range.
   // Capture that reason now; waiting for end-of-range would deadlock on !ready.
   if(state==OFEED&&ov)failure(2,ocode==9?8'd254:{4'd0,ocode});
   if(state==HFEED&&hv)failure(4,hcode==0?8'd254:{4'd0,hcode});
   if(bphase&&bev)failure(3,becode);
   if(bphase&&bsv&&!bid)failure(3,8'd254);
   if(hphase&&hwv&&!hid)failure(4,8'd254);
   if(read_enable&&(!complete_store||read_addr>=total||read_addr>=49152))failure(5,1);
  end
 end
endmodule
`default_nettype wire
