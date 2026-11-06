`timescale 1ns/1ps
// Successor: synchronous 128-bit RAM caches with explicit read-port replication.
// No store/transpose, publication, HUD, runtime reset/rekey, or bank map.
module ar03_yuv_line_gather #(
 parameter [23:0] Y_BASE=24'h100000,
 parameter [63:0] OWNER=64'hfedcba9876543210,
 parameter [31:0] EPOCH=32'h10203040, FRAME=32'h50607080
)(
 input wire clk,reset,
 output wire display_valid,output wire[63:0]display_owner,
 output wire[31:0]display_epoch,display_frame,display_token,
 input wire line_req_valid,output wire line_req_ready,input wire[23:0]line_req_address,
 output wire line_data_valid,output wire[15:0]line_data,output wire[9:0]pixel_x,output wire[8:0]pixel_y,
 output reg primed,
 output wire request_valid,input wire request_ready,input wire request_rejected,
 output wire[63:0]request_owner,output wire[31:0]request_epoch,request_frame,request_sequence,
 output wire[23:0]request_address,
 input wire response_valid,output wire response_ready,input wire[127:0]response_data,
 input wire[63:0]response_owner,input wire[31:0]response_epoch,response_frame,response_sequence,
 input wire[1:0]response_status,input wire[3:0]response_words,
 output reg[31:0]requests,responses,rejected_response_cycles,unsolicited_response_cycles,
 output reg[31:0]cache_misses,completed_lines,protocol_faults
);
 localparam CB_BASE=Y_BASE+24'd172800,CR_BASE=Y_BASE+24'd216000;
 localparam REQ=0,WAIT_RSP=1,IDLE=2,CHECK=3,RENDER=4;
 reg[2:0]state;
 reg[1:0]kind; // 0Y,1Cb,2Cr
 reg[9:0]column;
 reg[8:0]load_column;
 reg slot,initial_prime;
 reg[4:0]block_index;
 reg[31:0]read_sequence,line_operation,line_next;
 reg[9:0]in_index,out_index;
 reg stage_valid;
 reg[9:0]stage_index;
 wire stage_advance=!stage_valid||kir;
 wire fetch=state==RENDER&&in_index<480&&stage_advance&&!reset;
 wire cache_write=response_valid&&response_ready;
 wire[4:0]write_word=kind==0?block_index:((slot?5'd15:5'd0)+block_index);
 wire[4:0]addr_l=(left_slot?5'd15:5'd0)+(cy>>4);
 wire[4:0]addr_r=(right_slot?5'd15:5'd0)+(cy>>4);
 wire[4:0]addr_lb=(left_slot?5'd15:5'd0)+(below_cy>>4);
 wire[4:0]addr_rb=(right_slot?5'd15:5'd0)+(below_cy>>4);
 wire[127:0]yword,cb00w,cb10w,cb01w,cb11w,cr00w,cr10w,cr01w,cr11w;
 ar03_gather_cache_ram yr(.clk(clk),.we(cache_write&&kind==0),.wa(write_word),.wd(response_data),.re(fetch),.a(in_index[8:4]),.b(5'd0),.qa(yword),.qb());
 ar03_gather_cache_ram cbtop(.clk(clk),.we(cache_write&&kind==1),.wa(write_word),.wd(response_data),.re(fetch),.a(addr_l),.b(addr_r),.qa(cb00w),.qb(cb10w));
 ar03_gather_cache_ram cbbottom(.clk(clk),.we(cache_write&&kind==1),.wa(write_word),.wd(response_data),.re(fetch),.a(addr_lb),.b(addr_rb),.qa(cb01w),.qb(cb11w));
 ar03_gather_cache_ram crtop(.clk(clk),.we(cache_write&&kind==2),.wa(write_word),.wd(response_data),.re(fetch),.a(addr_l),.b(addr_r),.qa(cr00w),.qb(cr10w));
 ar03_gather_cache_ram crbottom(.clk(clk),.we(cache_write&&kind==2),.wa(write_word),.wd(response_data),.re(fetch),.a(addr_lb),.b(addr_rb),.qa(cr01w),.qb(cr11w));
 wire[8:0]stage_cy=stage_index>>1;
 wire[8:0]stage_below=stage_cy==239?9'd239:stage_cy+1'b1;
 reg[1:0]cache_valid;
 reg[8:0]cache_column[0:1];
 reg[127:0]cache_identity[0:1];
 wire[127:0]identity={OWNER,EPOCH,FRAME};
 assign display_valid=primed&&!reset&&(state==CHECK||state==REQ||state==WAIT_RSP);
 assign display_owner=OWNER;assign display_epoch=EPOCH;assign display_frame=FRAME;assign display_token=line_operation;
 wire[8:0]cx=column>>1;
 wire[8:0]right_cx=cx==359?9'd359:cx+1'b1;
 wire left_slot=cx[0],right_slot=right_cx[0];
 wire left_hit=cache_valid[left_slot]&&cache_column[left_slot]==cx&&cache_identity[left_slot]==identity;
 wire right_hit=cache_valid[right_slot]&&cache_column[right_slot]==right_cx&&cache_identity[right_slot]==identity;
 wire response_identity_match=response_owner==OWNER&&response_epoch==EPOCH&&response_frame==FRAME&&response_sequence==read_sequence;
 wire good_response=response_identity_match&&response_status==0&&response_words==8;
 assign request_valid=state==REQ&&!reset;
 assign request_owner=OWNER;assign request_epoch=EPOCH;assign request_frame=FRAME;assign request_sequence=read_sequence;
 // Compute address on the existing preparation edge, not through memory
 // arbitration. REQ handshakes and all response/service cycles are unchanged.
 // Modulo-2^24 unsigned constant strides; explicit operand width prevents shift truncation.
 function automatic [23:0] stride120(input [23:0] value);
  stride120=(value<<7)-(value<<3);
 endfunction
 function automatic [23:0] stride240(input [23:0] value);
  stride240=(value<<8)-(value<<4);
 endfunction
 reg[23:0]held_request_address;
 assign request_address=held_request_address;
 // Copy all128bits into reserved local arrays on the same edge that frees slot.
 // No response is held waiting for some other request/chroma dependency.
 assign response_ready=state==WAIT_RSP&&good_response&&!reset;
 assign line_req_ready=state==IDLE&&primed&&!reset;
 wire[8:0]cy=in_index>>1;
 wire[8:0]below_cy=cy==239?9'd239:cy+1'b1;
 wire[8:0]lbase=left_slot?9'd240:9'd0,rbase=right_slot?9'd240:9'd0;
 wire kiv=state==RENDER&&stage_valid;
 wire kir,kov,koerr;
 wire[15:0]krgb;
 wire[159:0]ktag;
 wire[11:0]kx,ky,kw,kh;
 wire[159:0]expected_tag={OWNER,EPOCH,FRAME,line_operation};
 wire kernel_identity=ktag==expected_tag&&kx==column&&ky==out_index&&kw==720&&kh==480&&!koerr;
 assign line_data_valid=state==RENDER&&kov&&kernel_identity&&!reset;
 assign line_data=krgb;assign pixel_x=kx[9:0];assign pixel_y=ky[8:0];
 ar03_rgb565_kernel #(.TAG_WIDTH(160)) rgb(.clk(clk),.rst(reset),.abort(1'b0),
  .in_valid(kiv),.in_ready(kir),.in_y(yword[stage_index[3:0]*8+:8]),
  .cb00(cb00w[stage_cy[3:0]*8+:8]),.cb10(cb10w[stage_cy[3:0]*8+:8]),.cb01(cb01w[stage_below[3:0]*8+:8]),.cb11(cb11w[stage_below[3:0]*8+:8]),
  .cr00(cr00w[stage_cy[3:0]*8+:8]),.cr10(cr10w[stage_cy[3:0]*8+:8]),.cr01(cr01w[stage_below[3:0]*8+:8]),.cr11(cr11w[stage_below[3:0]*8+:8]),
  .in_x({2'd0,column}),.in_row({2'd0,stage_index}),.in_width(12'd720),.in_height(12'd480),.in_tag(expected_tag),
  .out_valid(kov),.out_ready(state==RENDER&&kernel_identity),.out_rgb565(krgb),
  .out_x(kx),.out_row(ky),.out_width(kw),.out_height(kh),.out_tag(ktag),.out_error(koerr));
 integer i;
 task begin_chroma(input[8:0]col);
  begin
   load_column<=col;slot<=col[0];cache_valid[col[0]]<=0;held_request_address<=CB_BASE+stride120({15'd0,col});
   kind<=1;block_index<=0;state<=REQ;cache_misses<=cache_misses+1;
  end
 endtask
 always @(posedge clk)begin
  if(reset)begin
   state<=REQ;held_request_address<=CB_BASE;kind<=1;column<=0;load_column<=0;slot<=0;initial_prime<=1;primed<=0;
   block_index<=0;read_sequence<=32'h90000000;line_operation<=0;line_next<=0;
   in_index<=0;out_index<=0;stage_valid<=0;stage_index<=0;cache_valid<=0;cache_column[0]<=0;cache_column[1]<=0;
   cache_identity[0]<=0;cache_identity[1]<=0;
   requests<=0;responses<=0;rejected_response_cycles<=0;unsolicited_response_cycles<=0;
   cache_misses<=0;completed_lines<=0;protocol_faults<=0;
  end else begin
   if(stage_advance)begin
    stage_valid<=fetch;
    if(fetch)stage_index<=in_index;
   end
   if(response_valid&&!response_ready)begin
    if(state==WAIT_RSP)rejected_response_cycles<=rejected_response_cycles+1;
    else unsolicited_response_cycles<=unsolicited_response_cycles+1;
   end
   case(state)
    REQ:if(request_valid&&request_ready)begin
     requests<=requests+1;state<=WAIT_RSP;
     if(request_rejected)protocol_faults<=protocol_faults+1;
    end
    WAIT_RSP:if(response_valid&&response_ready)begin
     responses<=responses+1;read_sequence<=read_sequence+1;
     if(kind==0&&block_index==29)begin in_index<=0;out_index<=0;state<=RENDER;end
     else if(kind!=0&&block_index==14)begin
      block_index<=0;
      if(kind==1)begin kind<=2;held_request_address<=CR_BASE+stride120({15'd0,load_column});state<=REQ;end
      else begin
       cache_valid[slot]<=1;cache_column[slot]<=load_column;cache_identity[slot]<=identity;
       if(initial_prime&&load_column==0)begin
        kind<=1;load_column<=1;slot<=1;cache_valid[1]<=0;held_request_address<=CB_BASE+24'd120;state<=REQ;
       end else if(initial_prime)begin initial_prime<=0;primed<=1;state<=IDLE;end
       else state<=CHECK;
      end
     end else begin block_index<=block_index+1;held_request_address<=held_request_address+24'd8;state<=REQ;end
    end
    IDLE:if(line_req_valid&&line_req_ready)begin
     if(line_req_address%480!=0||line_req_address>=345600)protocol_faults<=protocol_faults+1;
     column<=line_req_address/480;line_operation<=line_next;line_next<=line_next+1;state<=CHECK;
    end
    CHECK:begin
     if(!left_hit)begin_chroma(cx);
     else if(column[0]&&!right_hit)begin_chroma(right_cx);
     else begin kind<=0;block_index<=0;held_request_address<=Y_BASE+stride240({14'd0,column});state<=REQ;end
    end
    RENDER:begin
     if(fetch)in_index<=in_index+1;
     if(kov&&!kernel_identity)protocol_faults<=protocol_faults+1;
     if(line_data_valid)begin
      out_index<=out_index+1;
      if(out_index==479)begin completed_lines<=completed_lines+1;state<=IDLE;end
     end
    end
    default:protocol_faults<=protocol_faults+1;
   endcase
  end
 end
endmodule

// Port A writes only during cache loading, reads only during rendering.
// Port B is read-only. Two chroma replicas supply four independent word reads.
// Data RAM intentionally has no reset; validity/identity and stage_valid fence it.
module ar03_gather_cache_ram(
 input wire clk,we,re,input wire[4:0]wa,a,b,input wire[127:0]wd,
 output reg[127:0]qa,qb
);
 (* ram_style="block" *)reg[127:0]mem[0:31];
 always @(posedge clk)begin
  if(we)mem[wa]<=wd;
  else if(re)qa<=mem[a];
 end
 always @(posedge clk)if(re)qb<=mem[b];
endmodule
