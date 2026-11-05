`timescale 1ns/1ps
`default_nettype none
// Private independent HC22 KEY candidate. This bounded stage supports only
// legacy mode0 bodies encoded HR01 INDEX_RUNS(2). No ACK or publication.
module hc22_key_hud(
 input wire clk,reset,start_valid,output wire start_ready,
 input wire[63:0]start_owner,input wire[31:0]start_epoch,start_frame,start_generation,start_bytes,
 input wire in_valid,output wire in_ready,input wire[7:0]in_byte,input wire in_last,
 input wire abort_valid,input wire[63:0]abort_owner,input wire[31:0]abort_epoch,abort_frame,output wire abort_rejected,
 output wire word_valid,input wire word_ready,output wire[15:0]word_data,word_index,word_x,word_y,
 output wire[1:0]word_rect,output wire[63:0]word_owner,output wire[31:0]word_epoch,word_frame,word_generation,
 output wire result_valid,input wire result_ready,output reg[3:0]result_code,output reg candidate_checked,
 output wire[63:0]result_owner,output wire[31:0]result_epoch,result_frame,result_generation,
 output wire[31:0]decoded_words,received_bytes,output reg[127:0]result_tag
);
 localparam IDLE=0,HC_HDR=1,HC_CHECK=2,HSTART=3,P_HDR=4,P_CHECK=5,HRECT=6,PAL_LO=7,PAL_HI=8,
 ROW_LO=9,ROW_HI=10,TOKEN=11,SYMBOL=12,EMIT=13,P_CRC=14,HC_CRC=15,WAIT_HASH=16,RESULT=17,HC_SUM=18,HC_VALIDATE=19;
 reg[4:0]state=IDLE;reg[63:0]owner;reg[31:0]epoch,frame,generation,words;
 // Admission validates the original32-bit start_bytes before LOAD can run.
 reg[15:0]total,count,frame_crc_start,frame_last_index;
 reg[32:0]size_pair_lo,size_pair_hi;reg[33:0]header_total;
 reg[31:0]hmagic,hepoch,hframe,hgen,href_frame,href_gen,sizes[0:3];reg[7:0]version,dest,refslot,modes[0:3];reg[127:0]reftag,newtag;
 reg[31:0]crc,pcrc,pwire,hwire,pmagic,ppixels,plen;reg[7:0]pversion,pmode,lo;
 // Total accepted input is bounded to49152 bytes; per-patch pc cannot wrap16 bits.
 reg[15:0]pc,patch_bytes,patch_data_end,row_room;reg row_room_valid;
 reg[15:0]px,py,pw,ph,colors,palette[0:255],prev_palette,pal_index;
 // Only indices below validated colors can enter seen; cardinality proves all-used.
 reg[8:0]seen_count;reg[255:0]seen;reg[1:0]rect;reg[4:0]row;reg[8:0]col;reg[15:0]row_left,run_left,pending_word;reg repeat_token,hash_phase;reg[2:0]prefix_index,crc_index;
 wire alive=state!=IDLE&&state!=RESULT;
 wire cancel=abort_valid&&state!=IDLE&&abort_owner==owner&&abort_epoch==epoch&&abort_frame==frame;
 wire incoming_cancel=abort_valid&&state==IDLE&&start_valid&&abort_owner==start_owner&&abort_epoch==start_epoch&&abort_frame==start_frame;
 assign abort_rejected=abort_valid&&!cancel&&!incoming_cancel;
 assign start_ready=state==IDLE&&!reset&&!incoming_cancel;
 assign result_valid=state==RESULT&&!reset&&!cancel;
 assign result_owner=owner;assign result_epoch=epoch;assign result_frame=frame;assign result_generation=generation;
 assign word_owner=owner;assign word_epoch=epoch;assign word_frame=frame;assign word_generation=generation;
 assign decoded_words=words;assign received_bytes=count;assign word_rect=rect;assign word_data=pending_word;
 function automatic[15:0]rx(input[1:0]r);rx=r<2?16'd22:16'd168;endfunction
 function automatic[15:0]ry(input[1:0]r);case(r)0:ry=54;1:ry=82;2:ry=360;3:ry=390;endcase endfunction
 function automatic[15:0]rw(input[1:0]r);case(r)0,1:rw=160;2:rw=320;3:rw=240;endcase endfunction
 // Exact selected rectangle bounds: no runtime multiply/DSP in validation.
 function automatic[15:0]row_byte_limit(input[1:0]r);
  case(r)0,1:row_byte_limit=16'd480;2:row_byte_limit=16'd960;3:row_byte_limit=16'd720;endcase
 endfunction
 function automatic[15:0]pixel_count(input[1:0]r);
  case(r)0,1:pixel_count=16'd3840;2:pixel_count=16'd7680;3:pixel_count=16'd5760;endcase
 endfunction
 function automatic[15:0]payload_limit(input[1:0]r);
  case(r)0,1:payload_limit=16'd11568;2:payload_limit=16'd23088;3:payload_limit=16'd17328;endcase
 endfunction
 // P_CHECK validates all raw geometry before row/token/output states.
 // Use the accepted fixed rectangle geometry thereafter, never a raw width
 // multiplication on the output/row-bound path.
 function automatic[15:0]fixed_index(input[1:0]r,input[4:0]y,input[8:0]x);
  reg[15:0]yy;begin yy={11'd0,y};case(r)
   0,1:fixed_index=(yy<<7)+(yy<<5)+x;
   2:fixed_index=(yy<<8)+(yy<<6)+x;
   3:fixed_index=(yy<<8)-(yy<<4)+x;
  endcase end
 endfunction
 assign word_index=fixed_index(rect,row,col);assign word_x=rx(rect)+col;assign word_y=ry(rect)+row;
 wire hs,hi,hv,he;wire[255:0]digest;wire[63:0]ho;wire[31:0]hep;wire[1:0]hcode;
 wire launch=state==HSTART&&hs&&!reset&&!cancel;
 wire hash_valid=!reset&&!cancel&&(state==HRECT||(state==EMIT&&(!hash_phase||word_ready)));
 wire[63:0]rect_bytes={16'd24,rw(rect),ry(rect),rx(rect)};
 wire[7:0]hash_byte=state==HRECT?rect_bytes[prefix_index*8+:8]:(hash_phase?pending_word[15:8]:pending_word[7:0]);
 wire hash_last=state==EMIT&&hash_phase&&rect==3&&row==23&&col==239;
 sha256_bytes #(.MAX_BYTES(42272))tagger(.clk(clk),.reset(reset),.abort(cancel||state==RESULT),.start_valid(launch),.start_ready(hs),.start_owner(owner),.start_epoch(epoch),.start_length(64'd42272),.in_valid(hash_valid),.in_ready(hi),.in_byte(hash_byte),.in_last(hash_last),.out_valid(hv),.out_ready(1'b0),.out_digest(digest),.out_owner(ho),.out_epoch(hep),.error_valid(he),.error_ready(1'b0),.error_code(hcode));
 assign word_valid=state==EMIT&&hash_phase&&hi&&!reset&&!cancel;
 assign in_ready=!reset&&!cancel&&(state==HC_HDR||state==P_HDR||state==PAL_LO||state==PAL_HI||state==ROW_LO||state==ROW_HI||state==TOKEN||state==SYMBOL||state==P_CRC||state==HC_CRC);
 function automatic[31:0]crc_byte(input[31:0]old,input[7:0]b);reg[31:0]v;integer k;begin v=old^b;for(k=0;k<8;k=k+1)v=v[0]?(v>>1)^32'hedb88320:v>>1;crc_byte=v;end endfunction
 task fail(input[3:0]c);begin state<=RESULT;result_code<=c;candidate_checked<=0;result_tag<=0;end endtask
 task next_patch(input[1:0]selected_rect);begin pc<=0;patch_bytes<=sizes[selected_rect][15:0];patch_data_end<=sizes[selected_rect][15:0]-16'd4;row_room<=0;row_room_valid<=0;pcrc<=32'hffffffff;pwire<=0;pmagic<=0;pversion<=0;pmode<=0;px<=0;py<=0;pw<=0;ph<=0;colors<=0;ppixels<=0;plen<=0;seen<=0;seen_count<=0;pal_index<=0;prev_palette<=0;row<=0;col<=0;state<=P_HDR;end endtask
 integer k;
 always @(posedge clk)begin
  if(reset)begin
   seen_count<=0;pc<=0;patch_bytes<=0;patch_data_end<=0;row_room<=0;row_room_valid<=0;size_pair_lo<=0;size_pair_hi<=0;header_total<=0;state<=IDLE;owner<=0;epoch<=0;frame<=0;generation<=0;total<=0;count<=0;frame_crc_start<=0;frame_last_index<=0;words<=0;result_code<=0;candidate_checked<=0;result_tag<=0;crc<=32'hffffffff;rect<=0;hash_phase<=0;
   hmagic<=0;hepoch<=0;hframe<=0;hgen<=0;href_frame<=0;href_gen<=0;version<=0;dest<=0;refslot<=0;reftag<=0;newtag<=0;hwire<=0;
   for(k=0;k<4;k=k+1)begin sizes[k]<=0;modes[k]<=0;end
   // Palette RAM/data is intentionally not reset; all entries in range must be freshly written before use.
  end else if(cancel)fail(8);
  else begin
   if(state==IDLE&&start_valid&&start_ready)begin
    owner<=start_owner;epoch<=start_epoch;frame<=start_frame;generation<=start_generation;total<=start_bytes[15:0];frame_crc_start<=start_bytes[15:0]-16'd4;frame_last_index<=start_bytes[15:0]-16'd1;count<=0;words<=0;result_code<=0;candidate_checked<=0;result_tag<=0;crc<=32'hffffffff;rect<=0;hash_phase<=0;
    hmagic<=0;hepoch<=0;hframe<=0;hgen<=0;href_frame<=0;href_gen<=0;version<=0;dest<=0;refslot<=0;reftag<=0;newtag<=0;hwire<=0;
    for(k=0;k<4;k=k+1)begin sizes[k]<=0;modes[k]<=0;end
    if(start_owner==0||start_epoch==0||start_epoch==32'hffffffff||start_frame==32'hffffffff||start_generation==32'hffffffff||start_bytes<83||start_bytes>49152)fail(1);else state<=HC_HDR;
   end
   if(in_valid&&in_ready)begin
    count<=count+1;
    if(in_last!=(count==frame_last_index))fail(7);
    else begin
     if(count<frame_crc_start)crc<=crc_byte(crc,in_byte);
     if(state!=HC_HDR&&state!=HC_CRC)begin pc<=pc+1;if(pc<patch_data_end)pcrc<=crc_byte(pcrc,in_byte);end
     case(state)
      HC_HDR:begin
       if(count<4)hmagic[count*8+:8]<=in_byte;if(count==4)version<=in_byte;
       if(count>=5&&count<9)hepoch[(count-5)*8+:8]<=in_byte;if(count>=9&&count<13)hframe[(count-9)*8+:8]<=in_byte;
       if(count>=13&&count<17)hgen[(count-13)*8+:8]<=in_byte;if(count==17)dest<=in_byte;if(count==18)refslot<=in_byte;
       if(count>=19&&count<23)href_frame[(count-19)*8+:8]<=in_byte;if(count>=23&&count<27)href_gen[(count-23)*8+:8]<=in_byte;
       if(count>=27&&count<43)reftag[127-(count-27)*8-:8]<=in_byte;if(count>=43&&count<59)newtag[127-(count-43)*8-:8]<=in_byte;
       if(count>=59&&count<75)sizes[(count-59)/4][((count-59)%4)*8+:8]<=in_byte;if(count>=75)modes[count-75]<=in_byte;
       if(count==78)state<=HC_CHECK;
      end
      P_HDR:begin
       if(pc<4)pmagic[pc*8+:8]<=in_byte;if(pc==4)pversion<=in_byte;if(pc==5)pmode<=in_byte;
       if(pc>=6&&pc<8)px[(pc-6)*8+:8]<=in_byte;if(pc>=8&&pc<10)py[(pc-8)*8+:8]<=in_byte;
       if(pc>=10&&pc<12)pw[(pc-10)*8+:8]<=in_byte;if(pc>=12&&pc<14)ph[(pc-12)*8+:8]<=in_byte;
       if(pc>=14&&pc<16)colors[(pc-14)*8+:8]<=in_byte;if(pc>=16&&pc<20)ppixels[(pc-16)*8+:8]<=in_byte;
       if(pc>=20&&pc<24)plen[(pc-20)*8+:8]<=in_byte;if(pc==23)state<=P_CHECK;
      end
      PAL_LO:begin lo<=in_byte;state<=PAL_HI;end
      PAL_HI:begin
       if(pal_index!=0&&{in_byte,lo}<=prev_palette)fail(4);
       else begin palette[pal_index]<={in_byte,lo};prev_palette<={in_byte,lo};pal_index<=pal_index+1;if(pal_index+1==colors)state<=ROW_LO;else state<=PAL_LO;end
      end
      ROW_LO:begin
       lo<=in_byte;
       // Reserve the two length bytes before comparing the incoming length.
       // Both values refer to the current immutable, validated patch extent.
       row_room<=patch_data_end-pc-16'd2;
       row_room_valid<=({1'b0,pc}+17'd2)<={1'b0,patch_data_end};
       state<=ROW_HI;
      end
      ROW_HI:begin
       if({in_byte,lo}==0||{in_byte,lo}>row_byte_limit(rect)||!row_room_valid||{in_byte,lo}>row_room)fail(4);
       else begin row_left<={in_byte,lo};col<=0;state<=TOKEN;end
      end
      TOKEN:begin
       if({9'd0,in_byte[6:0]}+1>rw(rect)-col||row_left<1+(in_byte[7]?1:({9'd0,in_byte[6:0]}+1)))fail(4);
       else begin repeat_token<=in_byte[7];run_left<={9'd0,in_byte[6:0]}+1;row_left<=row_left-1;state<=SYMBOL;end
      end
      SYMBOL:begin
       if(in_byte>=colors||row_left==0||pc>=patch_data_end)fail(4);
       else begin pending_word<=palette[in_byte];if(!seen[in_byte])seen_count<=seen_count+9'd1;seen[in_byte]<=1;row_left<=row_left-1;hash_phase<=0;state<=EMIT;end
      end
      P_CRC:begin
       pwire[crc_index*8+:8]<=in_byte;
       if({1'b0,pc}!={1'b0,patch_data_end}+{14'd0,crc_index})fail(4);
       else if(crc_index==3)begin
        if({in_byte,pwire[23:0]}!=~pcrc)fail(5);
        else if(rect==3)begin state<=HC_CRC;crc_index<=0;end
        else begin rect<=rect+1;next_patch(rect+2'd1);end
       end else crc_index<=crc_index+1;
      end
      HC_CRC:begin
       hwire[crc_index*8+:8]<=in_byte;
       if({1'b0,count}!={1'b0,frame_crc_start}+{14'd0,crc_index})fail(2);
       else if(crc_index==3)begin if({in_byte,hwire[23:0]}!=~crc)fail(5);else state<=WAIT_HASH;end
       else crc_index<=crc_index+1;
      end
     endcase
    end
   end
   // Header fields are immutable while admission is stalled. Keep the
   // four-size addition off result/abort and streaming control in one cycle.
   if(state==HC_CHECK)begin
    size_pair_lo<={1'b0,sizes[0]}+{1'b0,sizes[1]};
    size_pair_hi<={1'b0,sizes[2]}+{1'b0,sizes[3]};
    state<=HC_SUM;
   end
   if(state==HC_SUM)begin
    header_total<={1'b0,size_pair_lo}+{1'b0,size_pair_hi}+34'd83;
    state<=HC_VALIDATE;
   end
   if(state==HC_VALIDATE)begin
    if(hmagic!=32'h32324348||version!=1||hepoch!=epoch||hframe!=frame||hgen!=generation||newtag==0||header_total!={18'd0,total}||sizes[0]<28||sizes[1]<28||sizes[2]<28||sizes[3]<28||sizes[0]>49152||sizes[1]>49152||sizes[2]>49152||sizes[3]>49152)fail(2);
    else if(dest!=0||refslot!=255||href_frame!=32'hffffffff||href_gen!=32'hffffffff||reftag!=0||modes[0]!=0||modes[1]!=0||modes[2]!=0||modes[3]!=0)fail(3);
    else state<=HSTART;
   end
   if(launch)next_patch(rect);
   if(state==P_CHECK)begin
    if(pmagic!=32'h31305248||pversion!=1||pmode!=2)fail(3);
    else if(px!=rx(rect)||py!=ry(rect)||pw!=rw(rect)||ph!=24||ppixels!=pixel_count(rect)||colors==0||colors>256||colors>ppixels||plen>payload_limit(rect)||({2'b0,plen}+34'd28+{18'd0,colors,1'b0})!={18'd0,patch_bytes})fail(4);
    else begin prefix_index<=0;state<=HRECT;end
   end
   if(state==HRECT&&hi)begin if(prefix_index==7)state<=PAL_LO;else prefix_index<=prefix_index+1;end
   if(state==EMIT&&hi)begin
    if(!hash_phase)hash_phase<=1;
    else if(word_ready)begin
     hash_phase<=0;words<=words+1;col<=col+1;run_left<=run_left-1;
     if(run_left>1)begin if(!repeat_token)state<=SYMBOL;end
     else if(col+1==rw(rect))begin
      if(row_left!=0)fail(4);
      else if(row==23)begin
       if(pc!=patch_data_end||{7'd0,seen_count}!=colors)fail(4);else begin state<=P_CRC;crc_index<=0;end
      end else begin row<=row+1;state<=ROW_LO;end
     end else if(row_left==0)fail(4);else state<=TOKEN;
    end
   end
   if(alive&&he)fail(9);
   if(state==WAIT_HASH&&hv)begin
    if(ho!=owner||hep!=epoch||digest[255:128]!=newtag||words!=21120)fail(6);
    else begin state<=RESULT;result_code<=0;candidate_checked<=1;result_tag<=digest[255:128];end
   end
   if(state==RESULT&&result_valid&&result_ready)state<=IDLE;
  end
 end
endmodule
`default_nettype wire
