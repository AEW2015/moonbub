// Canonical SHA256[:16] for already clipped, plane/raster-ordered samples.
// NO block-to-raster reorder, reference bank/lease or publication controller.
module canonical_tag #(parameter MAX_DIM=2048,MAX_PIXELS=345600)(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,
 input wire [63:0] start_owner,input wire [31:0] start_epoch,
 input wire [15:0] start_width,start_height,
 input wire in_valid,output wire in_ready,input wire [15:0] in_sample,
 input wire [1:0] in_plane,input wire [15:0] in_x,in_y,input wire in_last,
 output wire out_valid,input wire out_ready,output wire [127:0] out_tag,
 output wire [63:0] out_owner,output wire [31:0] out_epoch,
 output wire error_valid,input wire error_ready,output reg [2:0] error_code
);
 localparam IDLE=0,AREA=1,GEOMETRY=2,START_HASH=3,HEADER=4,LOW=5,HIGH=6,WAIT_TAG=7,ERROR=8;
 reg [3:0] state;
 reg [63:0] owner;
 reg [31:0] epoch,area,samples,seen,bytes;
 reg [15:0] width,height,plane_width,plane_height,x,y;
 reg [1:0] plane,header_index;
 reg final_sample,cancel_hash;
 wire sr,br,hv,he;
 wire [255:0] digest;
 wire [63:0] hash_owner;wire [31:0] hash_epoch;wire [1:0] hash_error;
 wire identity_matches=hash_owner==owner && hash_epoch==epoch;
 wire correct_order=in_plane==plane && in_x==x && in_y==y;
 wire correct_last=in_last==(seen==samples-1);
 wire correct_sample=in_sample[15:8]==0;
 wire [7:0] header_byte=header_index==0?width[7:0]:header_index==1?width[15:8]:header_index==2?height[7:0]:height[15:8];
 wire byte_valid=state==HEADER || state==HIGH || (state==LOW && in_valid && correct_order && correct_last && correct_sample);
 wire [7:0] byte_data=state==HEADER?header_byte:state==HIGH?8'd0:in_sample[7:0];
 assign start_ready=state==IDLE && sr && !reset && !abort && !cancel_hash;
 assign in_ready=state==LOW && br && !reset && !abort;
 assign out_valid=state==WAIT_TAG && hv && identity_matches && !reset && !abort;
 // Opaque wire bytes: first SHA digest byte goes in bits[7:0], matching AR03
 // envelope capture. This is byte packing, not a numeric SHA word conversion.
 genvar tag_byte;
 generate for(tag_byte=0;tag_byte<16;tag_byte=tag_byte+1)begin: tag_pack
  assign out_tag[tag_byte*8+:8]=digest[255-tag_byte*8-:8];
 end endgenerate
 assign out_owner=owner;assign out_epoch=epoch;
 assign error_valid=state==ERROR && !reset && !abort;
 sha256_bytes #(.MAX_BYTES(3*MAX_PIXELS+4)) hash_engine(
  .clk(clk),.reset(reset),.abort(abort||cancel_hash),
  .start_valid(state==START_HASH),.start_ready(sr),.start_owner(owner),.start_epoch(epoch),.start_length({32'd0,bytes}),
  .in_valid(byte_valid),.in_ready(br),.in_byte(byte_data),.in_last(state==HIGH && final_sample),
  .out_valid(hv),.out_ready(state==WAIT_TAG && out_ready && identity_matches),.out_digest(digest),.out_owner(hash_owner),.out_epoch(hash_epoch),
  .error_valid(he),.error_ready(1'b0),.error_code(hash_error));
 task fail(input [2:0] code);begin error_code<=code;state<=ERROR;cancel_hash<=1;end endtask
 always @(posedge clk)begin
  if(reset||abort)begin
   state<=IDLE;owner<=0;epoch<=0;width<=0;height<=0;area<=0;samples<=0;seen<=0;bytes<=0;
   plane<=0;x<=0;y<=0;plane_width<=0;plane_height<=0;header_index<=0;final_sample<=0;cancel_hash<=0;error_code<=0;
  end else begin
   cancel_hash<=0;
   if((he && state!=IDLE && state!=ERROR) || (state==WAIT_TAG && hv && !identity_matches))fail(5);
   else case(state)
    IDLE:if(start_valid && sr)begin owner<=start_owner;epoch<=start_epoch;width<=start_width;height<=start_height;state<=AREA;end
    AREA:begin area<=width*height;state<=GEOMETRY;end
    GEOMETRY:begin
     if(width<2 || height<2 || width>MAX_DIM || height>MAX_DIM || width[0] || height[0] || area>MAX_PIXELS)fail(1);
     else begin
      samples<=area+(area>>1);bytes<=3*area+4;seen<=0;plane<=0;x<=0;y<=0;
      plane_width<=width;plane_height<=height;header_index<=0;state<=START_HASH;
     end
    end
    START_HASH:if(sr)state<=HEADER;
    HEADER:if(br)begin if(header_index==3)state<=LOW;else header_index<=header_index+1'b1;end
    LOW:if(in_valid && br)begin
     if(!correct_sample)fail(2);
     else if(!correct_order)fail(3);
     else if(!correct_last)fail(4);
     else begin
      seen<=seen+1;final_sample<=seen==samples-1;state<=HIGH;
      if(x==plane_width-1)begin
       x<=0;
       if(y==plane_height-1)begin y<=0;plane<=plane+1'b1;plane_width<=width>>1;plane_height<=height>>1;end
       else y<=y+1'b1;
      end else x<=x+1'b1;
     end
    end
    HIGH:if(br)state<=final_sample?WAIT_TAG:LOW;
    WAIT_TAG:if(hv && out_ready)state<=IDLE;
    ERROR:if(error_ready)state<=IDLE;
    default:state<=IDLE;
   endcase
  end
 end
endmodule
