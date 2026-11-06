`timescale 1ns/1ps
// Three-live-strip direct-YUV cache; one streamed BL8 outstanding.
module cu77_direct_cache (
 input logic clk,rst,abort_i,
 input logic desc_valid,output logic desc_ready,
 input logic [63:0] desc_generation,input logic [31:0] desc_frame_id,input logic [1:0] desc_bank,
 input logic finish_valid,output logic finish_ready,
 output logic active,aborted,error,output logic [7:0] error_code,
 output logic [63:0] active_generation,output logic [31:0] active_frame_id,
 input logic prefetch_valid,output logic prefetch_ready,input logic [6:0] prefetch_index,
 output logic prefetch_done_valid,input logic prefetch_done_ready,output logic [6:0] prefetch_done_index,
 input logic consume_valid,output logic consume_ready,input logic [6:0] consume_index,
 output logic [6:0] prefetched_count,consumed_count,
 output logic mem_req_valid,input logic mem_req_ready,output logic [23:0] mem_req_addr,
 input logic mem_rsp_valid,output logic mem_rsp_ready,input logic [15:0] mem_rsp_data,
 input logic mem_rsp_last,mem_rsp_error,
 input logic pixel_req_valid,output logic pixel_req_ready,input logic [9:0] pixel_u,input logic [8:0] pixel_v,
 output logic pixel_rsp_valid,input logic pixel_rsp_ready,
 output logic [9:0] pixel_rsp_u,output logic [8:0] pixel_rsp_v,
 output logic [7:0] pixel_y,cb00,cb10,cb01,cb11,cr00,cr10,cr01,cr11,
 output logic pixel_hud_hit,output logic [15:0] pixel_hud,output logic pixel_rsp_error,
 output logic [31:0] read_commands,read_words,pixel_queries,cache_misses
);
 typedef enum logic[2:0] {IDLE,SCAN,ISSUE,FILL,DONE} state_t;
 state_t state;
 logic [1:0] bank;
 logic aborting,failed;
 logic [6:0] strip;
 logic [2:0] phase;
 logic [5:0] column,tile_row;
 logic [1:0] block_no;
 logic [2:0] beat;
 logic [2:0] yvalid,cvalid0,cvalid1;
 logic [6:0] ytag[0:2];logic [5:0] ctag0[0:2],ctag1[0:2];
 logic [15:0] hvalid;logic [5:0] htag[0:15];
 logic [15:0] ymemory[0:5759];logic [15:0] hmemory[0:3071];
 logic [15:0] cbmem0[0:719],cbmem1[0:719],cbmem2[0:719],cbmem3[0:719];
 logic [15:0] crmem0[0:719],crmem1[0:719],crmem2[0:719],crmem3[0:719];
 logic [15:0] yword,hword,cbword[0:3],crword[0:3];
 logic pixel_pending,ylane,clane0,clane1;
 logic [1:0] mb00,mb10,mb01,mb11;
 logic [12:0] yraddr;logic [11:0] hraddr;logic [9:0] craddr[0:3];
 logic query_ok,qhud;logic [1:0] qb00,qb10,qb01,qb11;
 integer qu,qv,qcx,qcx1,qcy,qcy1,qys,qcs0,qcs1,qcw0,qcw1,qs;
 integer hrect,hx,hw,hoff,hlo,hhi,hlast;
 integer target_col,target_slot,last_row,fill_row,fill_word,write_bank;logic[12:0]write_addr;
 logic scan_hit,scan_empty,last_column;
 function automatic integer rect_x(input integer n);
  case(n)0,1:rect_x=22;default:rect_x=168;endcase
 endfunction
 function automatic integer rect_y(input integer n);
  case(n)0:rect_y=54;1:rect_y=82;2:rect_y=360;default:rect_y=390;endcase
 endfunction
 function automatic integer rect_w(input integer n);
  case(n)0,1:rect_w=160;2:rect_w=320;default:rect_w=240;endcase
 endfunction
 function automatic integer rect_off(input integer n);
  case(n)0:rect_off=0;1:rect_off=3840;2:rect_off=7680;default:rect_off=15360;endcase
 endfunction
 function automatic logic[23:0] canonical(input logic[1:0] b);
  case(b)0:canonical=24'h080000;1:canonical=24'h480000;default:canonical=24'h880000;endcase
 endfunction
 function automatic logic[23:0] hudbase(input logic[1:0] b);
  case(b)0:hudbase=24'h100000;1:hudbase=24'h500000;default:hudbase=24'h900000;endcase
 endfunction
 function automatic integer caddr(input integer slot,cy,cw);
  caddr=slot*240+(cy/2)*2+cw/2;
 endfunction
 always_comb begin
  hrect=int'(phase)-3;hx=rect_x(hrect);hw=rect_w(hrect);hoff=rect_off(hrect);
  hlo=int'(strip)*8>hx?int'(strip)*8:hx;
  hhi=int'(strip)*8+8<hx+hw?int'(strip)*8+8:hx+hw;
  hlast=(hhi-1-hx)/8;
  target_col=phase==0?int'(strip):int'(column);
  target_slot=target_col%3;scan_hit=0;scan_empty=0;last_column=1;
  last_row=phase==0?59:phase<3?29:23;
  if(phase==0)scan_hit=yvalid[target_slot]&&ytag[target_slot]==strip;
  else if(phase==1)begin scan_hit=cvalid0[target_slot]&&ctag0[target_slot]==column;last_column=int'(column)==((int'(strip)*4+4>359?359:int'(strip)*4+4)/8);end
  else if(phase==2)begin scan_hit=cvalid1[target_slot]&&ctag1[target_slot]==column;last_column=int'(column)==((int'(strip)*4+4>359?359:int'(strip)*4+4)/8);end
  else if(phase<=6)begin
   target_slot=int'(column)%4;scan_empty=hlo>=hhi;
   scan_hit=hvalid[hrect*4+target_slot]&&htag[hrect*4+target_slot]==column;
   last_column=int'(column)==hlast;
  end
  mem_req_addr=canonical(bank);
  if(phase==0)mem_req_addr=canonical(bank)+24'((int'(tile_row)*90+int'(strip))*32+int'(block_no)*8);
  else if(phase==1||phase==2)mem_req_addr=canonical(bank)+(phase==1?24'd172800:24'd216000)+24'((int'(tile_row)*45+int'(column))*32+int'(block_no)*8);
  else if(phase<=6)mem_req_addr=hudbase(bank)+24'(hoff+int'(tile_row)*hw+int'(column)*8);
  fill_word=int'(block_no)*8+int'(beat);fill_row=int'(tile_row)*8+fill_word/4;
  write_addr=13'(phase==0?(int'(strip)%3)*1920+fill_row*4+fill_word%4:phase<3?caddr(int'(column)%3,fill_row,fill_word%4):hrect*768+(int'(column)%4)*192+int'(tile_row)*8+int'(beat));
  write_bank=(fill_row%2)*2+(fill_word%2);
  desc_ready=!active&&state==IDLE&&!pixel_pending&&!mem_rsp_valid&&!rst&&!abort_i;
  finish_ready=active&&!error&&state==IDLE&&prefetched_count==90&&consumed_count==90&&!pixel_pending&&!pixel_req_valid&&!abort_i&&!rst;
  prefetch_ready=active&&!error&&state==IDLE&&!abort_i&&!rst&&prefetch_index==prefetched_count&&prefetched_count<90&&int'(prefetch_index)<int'(consumed_count)+3;
  prefetch_done_valid=state==DONE&&active&&!error&&!aborting&&!abort_i&&!rst;
  prefetch_done_index=strip;
  consume_ready=active&&!error&&!abort_i&&!rst&&!pixel_pending&&!pixel_req_valid&&consume_index==consumed_count&&consumed_count<prefetched_count;
  mem_req_valid=state==ISSUE&&active&&!failed&&!aborting&&!abort_i&&!rst;
  mem_rsp_ready=state==FILL&&!rst;
  qu=int'(pixel_u);qv=int'(pixel_v);qs=qu/8;qcx=qu/2;qcx1=qcx+1<360?qcx+1:359;qcy=qv/2;qcy1=qcy+1<240?qcy+1:239;
  qys=qs%3;qcs0=(qcx/8)%3;qcs1=(qcx1/8)%3;qcw0=(qcx%8)/2;qcw1=(qcx1%8)/2;
  query_ok=active&&!error&&qu<720&&qv<480&&qs>=int'(consumed_count)&&qs<int'(prefetched_count);
  if(!yvalid[qys]||ytag[qys]!=7'(qs)||!cvalid0[qcs0]||!cvalid0[qcs1]||!cvalid1[qcs0]||!cvalid1[qcs1]||ctag0[qcs0]!=6'(qcx/8)||ctag0[qcs1]!=6'(qcx1/8)||ctag1[qcs0]!=6'(qcx/8)||ctag1[qcs1]!=6'(qcx1/8))query_ok=0;
  yraddr=13'(qys*1920+qv*4+(qu%8)/2);hraddr=0;qhud=0;
  for(integer i=0;i<4;i=i+1)begin
   if(qu>=rect_x(i)&&qu<rect_x(i)+rect_w(i)&&qv>=rect_y(i)&&qv<rect_y(i)+24)begin
    qhud=1;hraddr=12'(i*768+(((qu-rect_x(i))/8)%4)*192+(qv-rect_y(i))*8+(qu-rect_x(i))%8);
    if(!hvalid[i*4+(((qu-rect_x(i))/8)%4)]||htag[i*4+(((qu-rect_x(i))/8)%4)]!=6'((qu-rect_x(i))/8))query_ok=0;
   end
  end
  qb00=2'((qcy%2)*2+qcw0%2);qb10=2'((qcy%2)*2+qcw1%2);qb01=2'((qcy1%2)*2+qcw0%2);qb11=2'((qcy1%2)*2+qcw1%2);
  for(integer i=0;i<4;i=i+1)craddr[i]=0;
  craddr[qb00]=10'(caddr(qcs0,qcy,qcw0));craddr[qb10]=10'(caddr(qcs1,qcy,qcw1));craddr[qb01]=10'(caddr(qcs0,qcy1,qcw0));craddr[qb11]=10'(caddr(qcs1,qcy1,qcw1));
  if(!query_ok)for(integer i=0;i<4;i=i+1)craddr[i]=0;
  pixel_req_ready=active&&!error&&!abort_i&&!rst&&(!pixel_pending||pixel_rsp_ready);
  pixel_rsp_valid=pixel_pending&&!abort_i&&!rst;
  pixel_y=pixel_rsp_error?8'd0:8'(yword>>(ylane?8:0));
  cb00=pixel_rsp_error?8'd0:8'(cbword[mb00]>>(clane0?8:0));cb10=pixel_rsp_error?8'd0:8'(cbword[mb10]>>(clane1?8:0));
  cb01=pixel_rsp_error?8'd0:8'(cbword[mb01]>>(clane0?8:0));cb11=pixel_rsp_error?8'd0:8'(cbword[mb11]>>(clane1?8:0));
  cr00=pixel_rsp_error?8'd0:8'(crword[mb00]>>(clane0?8:0));cr10=pixel_rsp_error?8'd0:8'(crword[mb10]>>(clane1?8:0));
  cr01=pixel_rsp_error?8'd0:8'(crword[mb01]>>(clane0?8:0));cr11=pixel_rsp_error?8'd0:8'(crword[mb11]>>(clane1?8:0));
  pixel_hud=pixel_rsp_error?16'd0:hword;
 end
 // Two independent ports per bank: streamed fill write and synchronous full-word read.
 always_ff @(posedge clk)begin
  if(mem_rsp_valid&&mem_rsp_ready&&!aborting&&!abort_i&&!failed&&!mem_rsp_error&&mem_rsp_last==(beat==7))begin
   if(phase==0)ymemory[write_addr]<=mem_rsp_data;
   else if(phase==1)case(write_bank)0:cbmem0[write_addr[9:0]]<=mem_rsp_data;1:cbmem1[write_addr[9:0]]<=mem_rsp_data;2:cbmem2[write_addr[9:0]]<=mem_rsp_data;default:cbmem3[write_addr[9:0]]<=mem_rsp_data;endcase
   else if(phase==2)case(write_bank)0:crmem0[write_addr[9:0]]<=mem_rsp_data;1:crmem1[write_addr[9:0]]<=mem_rsp_data;2:crmem2[write_addr[9:0]]<=mem_rsp_data;default:crmem3[write_addr[9:0]]<=mem_rsp_data;endcase
   else hmemory[write_addr[11:0]]<=mem_rsp_data;
  end
  if(pixel_req_valid&&pixel_req_ready)begin
   yword<=ymemory[query_ok?yraddr:13'd0];hword<=hmemory[query_ok?hraddr:12'd0];
   cbword[0]<=cbmem0[craddr[0]];cbword[1]<=cbmem1[craddr[1]];cbword[2]<=cbmem2[craddr[2]];cbword[3]<=cbmem3[craddr[3]];
   crword[0]<=crmem0[craddr[0]];crword[1]<=crmem1[craddr[1]];crword[2]<=crmem2[craddr[2]];crword[3]<=crmem3[craddr[3]];
  end
 end
 task automatic next_phase;
 begin
  tile_row<=0;block_no<=0;
  if(phase==0)begin phase<=1;column<=6'((int'(strip)*4)/8);end
  else if(phase==1)begin phase<=2;column<=6'((int'(strip)*4)/8);end
  else if(phase==2)begin phase<=3;column<=6'((int'(strip)*8>22?int'(strip)*8-22:0)/8);end
  else if(phase<6)begin phase<=phase+1'b1;column<=6'((int'(strip)*8>rect_x(int'(phase)-2)?int'(strip)*8-rect_x(int'(phase)-2):0)/8);end
  else begin prefetched_count<=strip+1'b1;state<=DONE;end
 end endtask
 always_ff @(posedge clk)begin
  if(rst)begin
   state<=IDLE;active<=0;bank<=0;aborting<=0;failed<=0;aborted<=0;error<=0;error_code<=0;active_generation<=0;active_frame_id<=0;
   strip<=0;phase<=0;column<=0;tile_row<=0;block_no<=0;beat<=0;prefetched_count<=0;consumed_count<=0;yvalid<=0;cvalid0<=0;cvalid1<=0;hvalid<=0;
   pixel_pending<=0;pixel_rsp_u<=0;pixel_rsp_v<=0;pixel_rsp_error<=0;pixel_hud_hit<=0;ylane<=0;clane0<=0;clane1<=0;mb00<=0;mb10<=0;mb01<=0;mb11<=0;
   read_commands<=0;read_words<=0;pixel_queries<=0;cache_misses<=0;
   for(integer i=0;i<3;i=i+1)begin ytag[i]<=0;ctag0[i]<=0;ctag1[i]<=0;end
   for(integer i=0;i<16;i=i+1)htag[i]<=0;
  end else begin
   aborted<=0;
   if(pixel_rsp_valid&&pixel_rsp_ready)pixel_pending<=0;
   if(pixel_req_valid&&pixel_req_ready)begin
    pixel_pending<=1;pixel_rsp_u<=pixel_u;pixel_rsp_v<=pixel_v;pixel_rsp_error<=!query_ok;pixel_hud_hit<=query_ok&&qhud;
    ylane<=pixel_u[0];clane0<=1'(qcx%2);clane1<=1'(qcx1%2);mb00<=qb00;mb10<=qb10;mb01<=qb01;mb11<=qb11;
    pixel_queries<=pixel_queries+1;if(!query_ok)cache_misses<=cache_misses+1;
   end
   if(desc_valid&&desc_ready)begin
    error<=desc_generation==0||desc_frame_id==32'hffffffff||desc_bank>2;error_code<=desc_generation==0||desc_frame_id==32'hffffffff||desc_bank>2?8'h01:8'd0;
    active<=desc_generation!=0&&desc_frame_id!=32'hffffffff&&desc_bank<3;active_generation<=desc_generation;active_frame_id<=desc_frame_id;bank<=desc_bank;
    prefetched_count<=0;consumed_count<=0;yvalid<=0;cvalid0<=0;cvalid1<=0;hvalid<=0;aborting<=0;failed<=0;
    read_commands<=0;read_words<=0;pixel_queries<=0;cache_misses<=0;
   end
   if(finish_valid&&finish_ready)begin active<=0;yvalid<=0;cvalid0<=0;cvalid1<=0;hvalid<=0;end
   if(consume_valid&&consume_ready)consumed_count<=consumed_count+1'b1;
   if(abort_i&&active)begin
    pixel_pending<=0;aborting<=1;yvalid<=0;cvalid0<=0;cvalid1<=0;hvalid<=0;
    if(state!=FILL)begin active<=0;state<=IDLE;aborting<=0;aborted<=1;end
   end else if(!aborting)case(state)
    IDLE:if(prefetch_valid&&prefetch_ready)begin strip<=prefetch_index;phase<=0;column<=0;tile_row<=0;block_no<=0;beat<=0;failed<=0;state<=SCAN;end
    SCAN:begin
     if(scan_empty||scan_hit)begin if(last_column||scan_empty)next_phase();else column<=column+1'b1;end
     else begin
      if(phase==0)yvalid[target_slot]<=0;
      else if(phase==1)cvalid0[target_slot]<=0;
      else if(phase==2)cvalid1[target_slot]<=0;
      else hvalid[hrect*4+target_slot]<=0;
      tile_row<=0;block_no<=0;beat<=0;state<=ISSUE;
     end
    end
    ISSUE:if(mem_req_valid&&mem_req_ready)begin read_commands<=read_commands+1;beat<=0;state<=FILL;end
    FILL:begin end
    DONE:if(prefetch_done_valid&&prefetch_done_ready)state<=IDLE;
    default:state<=IDLE;
   endcase
   if(state==FILL&&mem_rsp_valid&&mem_rsp_ready)begin
    read_words<=read_words+1;
    if(mem_rsp_error||mem_rsp_last!=(beat==7))begin failed<=1;error<=1;error_code<=8'h02;end
    if(beat==7)begin
     beat<=0;
     if(aborting||abort_i||failed||mem_rsp_error||!mem_rsp_last)begin active<=0;state<=IDLE;aborting<=0;aborted<=1;pixel_pending<=0;yvalid<=0;cvalid0<=0;cvalid1<=0;hvalid<=0;end
     else if(int'(tile_row)==last_row&&(phase>=3||block_no==3))begin
      if(phase==0)begin yvalid[target_slot]<=1;ytag[target_slot]<=strip;end
      else if(phase==1)begin cvalid0[target_slot]<=1;ctag0[target_slot]<=column;end
      else if(phase==2)begin cvalid1[target_slot]<=1;ctag1[target_slot]<=column;end
      else begin hvalid[hrect*4+target_slot]<=1;htag[hrect*4+target_slot]<=column;end
      tile_row<=0;block_no<=0;state<=SCAN;
      if(last_column)next_phase();else column<=column+1'b1;
     end else begin
      if(phase>=3||block_no==3)begin block_no<=0;tile_row<=tile_row+1'b1;end
      else block_no<=block_no+1'b1;
      state<=ISSUE;
     end
    end else beat<=beat+1'b1;
   end
  end
 end
endmodule
