// Clocked-memory CP02 with bounded registered admission and arithmetic stages.
// Validate packet + entropy fully before emitting coefficients, then replay AC.
module cp02_decoder #(parameter MAX_BYTES=65536, MAX_BLOCKS=8192)(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,
 input wire [31:0] start_owner,start_epoch,start_block_base,start_bytes,start_blocks,
 input wire [15:0] start_width,input wire [1:0] start_plane,
 input wire in_valid,output wire in_ready,input wire [7:0] in_byte,input wire in_last,
 output wire out_valid,input wire out_ready,output wire signed [15:0] out_coefficient,
 output wire [31:0] out_owner,out_epoch,out_block,output wire [1:0] out_plane,
 output wire [5:0] out_index,output wire out_last,out_plane_last,packet_validated,
 output wire done_valid,input wire done_ready,
 output wire error_valid,input wire error_ready,output reg [3:0] error_code
);
 localparam IDLE=0,LOAD=1,HEADER=2,CRC=3,CRC_CHECK=4,RAW_CHECK=5,RAW_OUT=6,
 DC_START=7,RICE_PREFIX=8,GET=9,RICE_SUFFIX=10,RICE_ESCAPE=11,DC_VALUE=12,
 PAD=13,AC_INIT=14,AC_TOKEN=15,AC_SECOND=16,AC_RUN=17,AC_VALUE=18,
 BLOCK_END=19,OUT=20,DONE=21,ERROR=22,AC_NEXT=23,CRC_PRIME=24,
 RAW_FETCH_LO=25,RAW_CAPTURE_LO=26,RAW_FETCH_HI=27,RAW_CAPTURE_HI=28,
 BIT_FETCH=29,BIT_CAPTURE=30,AC_DC_WAIT=31,ADMIT_BOUNDS=32,ADMIT_MOD=33,
 DC_UNMAP=34,DC_ADD=35,DC_CHECK=36,AC_MAP=37,AC_UNMAP=38,AC_CHECK=39;
 localparam PAW=$clog2(MAX_BYTES),DAW=MAX_BLOCKS>1?$clog2(MAX_BLOCKS):1;
 reg [5:0] state,return_get,return_rice,return_pad,return_bit,return_raw;
 (* ram_style="block" *) reg [7:0] packet[0:MAX_BYTES-1];
 (* ram_style="block" *) reg signed [15:0] dc_table[0:MAX_BLOCKS-1];
 reg signed [15:0] block_data[0:63],dc_q;
 reg [7:0] packet_q,raw_low,bit_cache,raw_kd,raw_k0,raw_k1,raw_k2;
 reg signed [15:0] raw_word;
 reg [175:0] header_bytes;
 reg [31:0] received_crc,bit_cache_address;
 reg bit_cache_valid;
 reg [13:0] divide_bits;
 reg [9:0] remainder;
 reg [3:0] divide_left;
 wire [9:0] shifted_remainder={remainder[8:0],divide_bits[13]};
 wire [9:0] next_remainder=shifted_remainder>={1'b0,width[8:0]} ? shifted_remainder-{1'b0,width[8:0]} : shifted_remainder;
 reg signed [31:0] mapped_signed,sample_value;
 reg [31:0] mapped_value;
 reg sample_good;
 reg [31:0] owner,epoch,block_base,total,blocks,block_id,offset,ndc,nac,acbase;
 reg [15:0] width,column;
 reg [1:0] plane;
 reg mode,replay,validated;
 reg [31:0] crc,bitpos,bitend,get_value,rice_value;
 reg [5:0] get_left,index;
 reg [4:0] quotient;
 reg [3:0] rice_k,kd,k0,k1,k2;
 reg [4:0] escape_bits;
 reg [6:0] position,target;
 reg signed [31:0] previous;
 wire bit_hit=bit_cache_valid && bit_cache_address==(bitpos>>3);
 wire bit_value=bit_cache[7-bitpos[2:0]];
 wire [31:0] get_next=(get_value<<1)|bit_value;
 wire signed [31:0] unmapped=rice_value[0] ? -$signed((rice_value>>1)+1) : $signed(rice_value>>1);
 wire signed [31:0] dc_value=previous+unmapped;
 wire [31:0] ac_mapped=rice_value+1;
 wire signed [31:0] ac_value=ac_mapped[0] ? -$signed((ac_mapped>>1)+1) : $signed(ac_mapped>>1);
 wire [31:0] raw_address=22+((block_id*64+index)<<1);
 wire signed [15:0] raw_value=raw_word;
 wire [31:0] packet_address=(state==CRC_PRIME)?0:(state==CRC)?offset+1:
   (state==RAW_FETCH_LO)?raw_address:(state==RAW_FETCH_HI)?raw_address+1:(bitpos>>3);
 // These are the ONLY packet/DC read ports. Cache/header accesses below are
 // small registers; the large arrays have synchronous reads and no RAM reset.
 always @(posedge clk)begin
  packet_q<=packet[packet_address[PAW-1:0]];
  dc_q<=dc_table[block_id[DAW-1:0]];
 end
 function automatic [7:0] hdr8(input integer a);hdr8=header_bytes[a*8+:8];endfunction
 function automatic [31:0] le32(input integer a);
  le32=header_bytes[a*8+:32];
 endfunction
 function automatic [31:0] crc_byte(input [31:0] c,input [7:0] b);
  reg [31:0] v;integer j;
  begin v=c^{24'b0,b};for(j=0;j<8;j=j+1)v=v[0]?(v>>1)^32'hedb88320:v>>1;crc_byte=v;end
 endfunction
 function automatic [5:0] zigzag(input [5:0] p);
  begin case(p)
  0:zigzag=0;1:zigzag=1;2:zigzag=8;3:zigzag=16;4:zigzag=9;5:zigzag=2;6:zigzag=3;7:zigzag=10;
  8:zigzag=17;9:zigzag=24;10:zigzag=32;11:zigzag=25;12:zigzag=18;13:zigzag=11;14:zigzag=4;15:zigzag=5;
  16:zigzag=12;17:zigzag=19;18:zigzag=26;19:zigzag=33;20:zigzag=40;21:zigzag=48;22:zigzag=41;23:zigzag=34;
  24:zigzag=27;25:zigzag=20;26:zigzag=13;27:zigzag=6;28:zigzag=7;29:zigzag=14;30:zigzag=21;31:zigzag=28;
  32:zigzag=35;33:zigzag=42;34:zigzag=49;35:zigzag=56;36:zigzag=57;37:zigzag=50;38:zigzag=43;39:zigzag=36;
  40:zigzag=29;41:zigzag=22;42:zigzag=15;43:zigzag=23;44:zigzag=30;45:zigzag=37;46:zigzag=44;47:zigzag=51;
  48:zigzag=58;49:zigzag=59;50:zigzag=52;51:zigzag=45;52:zigzag=38;53:zigzag=31;54:zigzag=39;55:zigzag=46;
  56:zigzag=53;57:zigzag=60;58:zigzag=61;59:zigzag=54;60:zigzag=47;61:zigzag=55;62:zigzag=62;63:zigzag=63;
  endcase end
 endfunction
 assign start_ready=state==IDLE && !reset && !abort;
 assign in_ready=state==LOAD && !reset && !abort;
 assign out_valid=(state==OUT || state==RAW_OUT) && !reset && !abort;
 assign out_coefficient=state==RAW_OUT?raw_value:block_data[index];
 assign out_owner=owner;assign out_epoch=epoch;assign out_block=block_base+block_id;assign out_plane=plane;
 assign out_index=index;assign out_last=index==63;assign out_plane_last=index==63 && block_id==blocks-1;
 assign done_valid=state==DONE && !reset && !abort;
 assign packet_validated=validated && !reset && !abort;
 assign error_valid=state==ERROR && !reset && !abort;
 task fail(input [3:0] code);begin error_code<=code;state<=ERROR;validated<=0;end endtask
 task begin_rice(input [3:0] k,input [4:0] esc,input [5:0] dest);
 begin rice_k<=k;escape_bits<=esc;return_rice<=dest;quotient<=0;state<=RICE_PREFIX;end endtask
 integer lane;
 always @(posedge clk)begin
  if(reset || abort)begin
   state<=IDLE;owner<=0;epoch<=0;block_base<=0;total<=0;blocks<=0;block_id<=0;offset<=0;index<=0;
   width<=0;column<=0;plane<=0;error_code<=0;bitpos<=0;bitend<=0;previous<=0;replay<=0;validated<=0;bit_cache_valid<=0;
   divide_bits<=0;remainder<=0;divide_left<=0;sample_good<=0;
  end else case(state)
   IDLE:if(start_valid)begin
    owner<=start_owner;epoch<=start_epoch;block_base<=start_block_base;total<=start_bytes;blocks<=start_blocks;
    width<=start_width;plane<=start_plane;offset<=0;block_id<=0;index<=0;replay<=0;validated<=0;bit_cache_valid<=0;
    state<=ADMIT_BOUNDS;
   end
   ADMIT_BOUNDS:begin
    // Reject full-width invalid values BEFORE narrowing for bounded remainder.
    if(blocks<1 || blocks>MAX_BLOCKS || blocks>8192 || width<1 || width>256 ||
       total<26 || total>MAX_BYTES || {1'b0,total}>({1'b0,blocks}*128+26) || plane>2 ||
       ({1'b0,block_base}+{1'b0,blocks}-1)>33'hffffffff)fail(1);
    else begin divide_bits<=blocks[13:0];remainder<=0;divide_left<=14;state<=ADMIT_MOD;end
   end
   ADMIT_MOD:begin
    divide_bits<={divide_bits[12:0],1'b0};remainder<=next_remainder;divide_left<=divide_left-1'b1;
    if(divide_left==1)begin if(next_remainder!=0)fail(1);else state<=LOAD;end
   end
   LOAD:if(in_valid)begin
    packet[offset[PAW-1:0]]<=in_byte;
    if(offset<22)header_bytes[offset*8+:8]<=in_byte;
    if(offset>=total-4)received_crc[(offset-(total-4))*8+:8]<=in_byte;
    if(offset>=22)begin
     if(offset==22)raw_kd<=in_byte;
     if(offset==22+le32(14))raw_k0<=in_byte;
     if(offset==23+le32(14))raw_k1<=in_byte;
     if(offset==24+le32(14))raw_k2<=in_byte;
    end
    if(in_last!=(offset==total-1))fail(2);
    else if(offset==total-1)state<=HEADER;
    else offset<=offset+1;
   end
   HEADER:begin
    ndc<=le32(14);nac<=le32(18);acbase<=22+le32(14);mode<=hdr8(5)&1;
    if(le32(0)!=32'h32305043 || hdr8(4)!=1 || hdr8(5)>1 || le32(6)!=blocks ||
       {hdr8(11),hdr8(10)}!=width || {hdr8(13),hdr8(12)}!=0 ||
       ({1'b0,le32(14)}+{1'b0,le32(18)}+26)!={1'b0,total})fail(3);
    else if(hdr8(5)==0 && (le32(14)!=blocks*128 || le32(18)!=0))fail(3);
    else if(hdr8(5)==1 && (le32(14)<1 || le32(18)<3))fail(3);
    else begin crc<=32'hffffffff;offset<=0;state<=CRC_PRIME;end
   end
   CRC_PRIME:state<=CRC;
   CRC:begin crc<=crc_byte(crc,packet_q);if(offset==total-5)state<=CRC_CHECK;else offset<=offset+1;end
   CRC_CHECK:begin
    if((~crc)!=received_crc)fail(4);
    else if(!mode)begin block_id<=0;index<=0;return_raw<=RAW_CHECK;state<=RAW_FETCH_LO;end
    else if(raw_kd>13 || raw_k0>11 || raw_k1>11 || raw_k2>11)fail(5);
    else begin kd<=raw_kd;k0<=raw_k0;k1<=raw_k1;k2<=raw_k2;
     block_id<=0;column<=0;previous<=0;bitpos<=23*8;bitend<=acbase*8;state<=DC_START;end
   end
   RAW_CHECK:begin
    if(raw_value < -2048 || raw_value > 2048)fail(6);
    else begin
     state<=RAW_FETCH_LO;
     if(index==63)begin index<=0;if(block_id==blocks-1)begin block_id<=0;validated<=1;return_raw<=RAW_OUT;end else block_id<=block_id+1;end
     else index<=index+1'b1;
    end
   end
   RAW_FETCH_LO:state<=RAW_CAPTURE_LO;
   RAW_CAPTURE_LO:begin raw_low<=packet_q;state<=RAW_FETCH_HI;end
   RAW_FETCH_HI:state<=RAW_CAPTURE_HI;
   RAW_CAPTURE_HI:begin raw_word<={packet_q,raw_low};state<=return_raw;end
   RAW_OUT,OUT:if(out_ready)begin
    if(index==63)begin
     index<=0;
     if(block_id==blocks-1)state<=DONE;
     else begin block_id<=block_id+1;state<=state==OUT?AC_DC_WAIT:RAW_FETCH_LO;end
    end else begin index<=index+1'b1;if(state==RAW_OUT)state<=RAW_FETCH_LO;end
   end
   DC_START:begin_rice(kd,14,DC_UNMAP);
   RICE_PREFIX:begin
    if(bitpos>=bitend)fail(7);
    else if(!bit_hit)begin return_bit<=RICE_PREFIX;state<=BIT_FETCH;end
    else begin
     bitpos<=bitpos+1;
     if(bit_value)begin
      if(rice_k==0)begin rice_value<=quotient;state<=return_rice;end
      else begin get_left<=rice_k;get_value<=0;return_get<=RICE_SUFFIX;state<=GET;end
     end else if(quotient==14)begin get_left<=escape_bits;get_value<=0;return_get<=RICE_ESCAPE;state<=GET;end
     else quotient<=quotient+1'b1;
    end
   end
   GET:begin
    if(bitpos>=bitend)fail(7);
    else if(!bit_hit)begin return_bit<=GET;state<=BIT_FETCH;end
    else begin bitpos<=bitpos+1;get_value<=get_next;get_left<=get_left-1'b1;if(get_left==1)state<=return_get;end
   end
   RICE_SUFFIX:begin rice_value<=(quotient<<rice_k)|get_value;state<=return_rice;end
   RICE_ESCAPE:begin if((get_value>>rice_k)<15)fail(8);else begin rice_value<=get_value;state<=return_rice;end end
   DC_UNMAP:begin mapped_signed<=unmapped;state<=DC_ADD;end
   DC_ADD:begin sample_value<=previous+mapped_signed;state<=DC_CHECK;end
   DC_CHECK:begin sample_good<=sample_value>=-2048 && sample_value<=2048;state<=DC_VALUE;end
   DC_VALUE:begin
    if(!sample_good)fail(6);
    else begin
     dc_table[block_id[DAW-1:0]]<=sample_value;block_id<=block_id+1;
     if(column==width-1)begin column<=0;previous<=0;end else begin column<=column+1;previous<=sample_value;end
     if(block_id==blocks-1)begin return_pad<=AC_NEXT;state<=PAD;end else state<=DC_START;
    end
   end
   PAD:begin
    if(bitpos>bitend || bitend-bitpos>=8)fail(9);
    else if(bitpos==bitend)begin if(return_pad==AC_NEXT && replay)validated<=1;state<=return_pad;end
    else if(!bit_hit)begin return_bit<=PAD;state<=BIT_FETCH;end
    else if(bit_value)fail(9);else bitpos<=bitpos+1;
   end
   AC_NEXT:begin
    // Enter AC validation, or replay after successful final AC padding.
    block_id<=0;bitpos<=(acbase+3)*8;bitend<=(total-4)*8;state<=AC_DC_WAIT;
   end
   AC_DC_WAIT:state<=AC_INIT;
   AC_INIT:begin
    if(replay)begin for(lane=0;lane<64;lane=lane+1)block_data[lane]<=0;block_data[0]<=dc_q;end
    position<=1;state<=AC_TOKEN;
   end
   AC_TOKEN:begin
    if(position>=64)state<=BLOCK_END;
    else if(bitpos>=bitend)fail(7);
    else if(!bit_hit)begin return_bit<=AC_TOKEN;state<=BIT_FETCH;end
    else begin bitpos<=bitpos+1;if(!bit_value)state<=AC_SECOND;
     else begin get_left<=4;get_value<=0;return_get<=AC_RUN;state<=GET;end
    end
   end
   AC_SECOND:begin
    if(bitpos>=bitend)fail(7);
    else if(!bit_hit)begin return_bit<=AC_SECOND;state<=BIT_FETCH;end
    else begin bitpos<=bitpos+1;
     if(!bit_value)state<=BLOCK_END;
     else if(position+16>64)fail(10);
     else begin position<=position+16;state<=AC_TOKEN;end
    end
   end
   AC_RUN:begin
    if(position+get_value>=64)fail(10);
    else begin target<=position+get_value;
     begin_rice(position+get_value<=5?k0:position+get_value<=20?k1:k2,12,AC_MAP);
    end
   end
   AC_MAP:begin mapped_value<=rice_value+1;state<=AC_UNMAP;end
   AC_UNMAP:begin sample_value<=mapped_value[0] ? -$signed((mapped_value>>1)+1) : $signed(mapped_value>>1);state<=AC_CHECK;end
   AC_CHECK:begin sample_good<=sample_value!=0 && sample_value>=-2048 && sample_value<=2048;state<=AC_VALUE;end
   AC_VALUE:begin
    if(!sample_good)fail(6);
    else begin if(replay)block_data[zigzag(target[5:0])]<=sample_value;position<=target+1;state<=AC_TOKEN;end
   end
   BLOCK_END:begin
    if(replay)begin index<=0;state<=OUT;end
    else if(block_id==blocks-1)begin replay<=1;return_pad<=AC_NEXT;state<=PAD;end
    else begin block_id<=block_id+1;state<=AC_DC_WAIT;end
   end
   BIT_FETCH:state<=BIT_CAPTURE;
   BIT_CAPTURE:begin bit_cache<=packet_q;bit_cache_address<=bitpos>>3;bit_cache_valid<=1;state<=return_bit;end
   DONE:if(done_ready)begin state<=IDLE;validated<=0;end
   ERROR:if(error_ready)state<=IDLE;
   default:state<=IDLE;
  endcase
 end
endmodule
