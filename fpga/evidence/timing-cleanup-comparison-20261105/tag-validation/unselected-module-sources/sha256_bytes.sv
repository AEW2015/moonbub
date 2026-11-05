// Bounded byte-stream SHA-256. One64-byte register,16-word rolling schedule,
// one32-bit compression round/cycle. Hash certificate only, no bank publication.
module sha256_bytes #(parameter MAX_BYTES=1036804)(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,
 input wire [63:0] start_owner,input wire [31:0] start_epoch,
 input wire [63:0] start_length,
 input wire in_valid,output wire in_ready,input wire [7:0] in_byte,input wire in_last,
 output wire out_valid,input wire out_ready,output wire [255:0] out_digest,
 output wire [63:0] out_owner,output wire [31:0] out_epoch,
 output wire error_valid,input wire error_ready,output reg [1:0] error_code
);
 localparam IDLE=0,CHECK=1,LOAD=2,PAD_ONE=3,PAD_ZERO=4,PAD_LENGTH=5,
  COMP_INIT=6,ROUND=7,ADD_HASH=8,DIGEST=9,ERROR=10,COMP_FLUSH=11;
 reg [3:0] state,resume;
 reg [63:0] owner,length;
 reg [31:0] epoch,remaining;
 reg [5:0] byte_index,round_index;
 reg [2:0] length_index;
 reg [511:0] block;
 reg [31:0] hash[0:7],w[0:15];
 reg [31:0] a,b,c,d,e,f,g,h;
 wire [63:0] bit_length=length<<3;
 function automatic [31:0] rr(input [31:0] x,input integer n);rr=(x>>n)|(x<<(32-n));endfunction
 function automatic [31:0] big0(input [31:0] x);big0=rr(x,2)^rr(x,13)^rr(x,22);endfunction
 function automatic [31:0] big1(input [31:0] x);big1=rr(x,6)^rr(x,11)^rr(x,25);endfunction
 function automatic [31:0] small0(input [31:0] x);small0=rr(x,7)^rr(x,18)^(x>>3);endfunction
 function automatic [31:0] small1(input [31:0] x);small1=rr(x,17)^rr(x,19)^(x>>10);endfunction
 function automatic [31:0] carry(input [31:0] x,y,z);carry=((x&y)|(x&z)|(y&z))<<1;endfunction
 function automatic [31:0] k(input [5:0] t);
 begin case(t)
 0:k=32'h428a2f98;1:k=32'h71374491;2:k=32'hb5c0fbcf;3:k=32'he9b5dba5;
 4:k=32'h3956c25b;5:k=32'h59f111f1;6:k=32'h923f82a4;7:k=32'hab1c5ed5;
 8:k=32'hd807aa98;9:k=32'h12835b01;10:k=32'h243185be;11:k=32'h550c7dc3;
 12:k=32'h72be5d74;13:k=32'h80deb1fe;14:k=32'h9bdc06a7;15:k=32'hc19bf174;
 16:k=32'he49b69c1;17:k=32'hefbe4786;18:k=32'h0fc19dc6;19:k=32'h240ca1cc;
 20:k=32'h2de92c6f;21:k=32'h4a7484aa;22:k=32'h5cb0a9dc;23:k=32'h76f988da;
 24:k=32'h983e5152;25:k=32'ha831c66d;26:k=32'hb00327c8;27:k=32'hbf597fc7;
 28:k=32'hc6e00bf3;29:k=32'hd5a79147;30:k=32'h06ca6351;31:k=32'h14292967;
 32:k=32'h27b70a85;33:k=32'h2e1b2138;34:k=32'h4d2c6dfc;35:k=32'h53380d13;
 36:k=32'h650a7354;37:k=32'h766a0abb;38:k=32'h81c2c92e;39:k=32'h92722c85;
 40:k=32'ha2bfe8a1;41:k=32'ha81a664b;42:k=32'hc24b8b70;43:k=32'hc76c51a3;
 44:k=32'hd192e819;45:k=32'hd6990624;46:k=32'hf40e3585;47:k=32'h106aa070;
 48:k=32'h19a4c116;49:k=32'h1e376c08;50:k=32'h2748774c;51:k=32'h34b0bcb5;
 52:k=32'h391c0cb3;53:k=32'h4ed8aa4a;54:k=32'h5b9cca4f;55:k=32'h682e6ff3;
 56:k=32'h748f82ee;57:k=32'h78a5636f;58:k=32'h84c87814;59:k=32'h8cc70208;
 60:k=32'h90befffa;61:k=32'ha4506ceb;62:k=32'hbef9a3f7;63:k=32'hc67178f2;
 endcase end endfunction
 wire [31:0] choice=(e&f)^((~e)&g),majority=(a&b)^(a&c)^(b&c);
 // Carry-save trees keep the five-input T1 sum to a single carry propagation.
 wire [31:0] t10=h^big1(e)^choice,t11=carry(h,big1(e),choice);
 wire [31:0] t12=t10^t11^k(round_index),t13=carry(t10,t11,k(round_index));
 wire [31:0] t14=t12^t13^w[0],t15=carry(t12,t13,w[0]);
 wire [31:0] t1=t14+t15;
 wire [31:0] an=t1^big0(a)^majority,ac=carry(t1,big0(a),majority);
 wire [31:0] wn0=small1(w[14])^w[9]^small0(w[1]);
 wire [31:0] wn1=carry(small1(w[14]),w[9],small0(w[1]));
 wire [31:0] wn2=wn0^wn1^w[0],wn3=carry(wn0,wn1,w[0]);
 assign start_ready=state==IDLE && !block_write_valid && !reset && !abort;
 assign in_ready=state==LOAD && !reset && !abort;
 assign out_valid=state==DIGEST && !reset && !abort;
 assign out_digest={hash[0],hash[1],hash[2],hash[3],hash[4],hash[5],hash[6],hash[7]};
 assign out_owner=owner;assign out_epoch=epoch;
 assign error_valid=state==ERROR && !reset && !abort;
 // One private byte-write reservation separates remote stream/cancel
 // control from the512 block-register enables. A prior accepted write may
 // retire on cancellation; validity/owner reset masks all service outputs.
 // COMP_FLUSH retires the final byte before COMP_INIT reads the whole block.
 reg block_write_valid;reg[5:0]block_write_index;reg[7:0]block_write_byte;
 task reserve_byte(input[7:0]value);begin
  block_write_valid<=1;block_write_index<=byte_index;block_write_byte<=value;
 end endtask
 always @(posedge clk)begin
  if(reset||abort)block_write_valid<=0;
  else begin
   block_write_valid<=0;
   case(state)
    LOAD:if(in_valid&&in_last==(remaining==1))reserve_byte(in_byte);
    PAD_ONE:reserve_byte(8'h80);
    PAD_ZERO:if(byte_index!=56)reserve_byte(8'h00);
    PAD_LENGTH:reserve_byte(bit_length>>((7-length_index)*8));
   endcase
  end
 end
 always @(posedge clk)if(block_write_valid)block[511-block_write_index*8-:8]<=block_write_byte;
 integer lane;
 always @(posedge clk)begin
  if(reset||abort)begin
   state<=IDLE;owner<=0;epoch<=0;length<=0;remaining<=0;byte_index<=0;round_index<=0;length_index<=0;error_code<=0;
   for(lane=0;lane<8;lane=lane+1)hash[lane]<=0;
  end else case(state)
   IDLE:if(start_valid&&start_ready)begin owner<=start_owner;epoch<=start_epoch;length<=start_length;byte_index<=0;state<=CHECK;end
   CHECK:begin
    if(length>MAX_BYTES || length[63:61]!=0)begin error_code<=1;state<=ERROR;end
    else begin
     hash[0]<=32'h6a09e667;hash[1]<=32'hbb67ae85;hash[2]<=32'h3c6ef372;hash[3]<=32'ha54ff53a;
     hash[4]<=32'h510e527f;hash[5]<=32'h9b05688c;hash[6]<=32'h1f83d9ab;hash[7]<=32'h5be0cd19;
     remaining<=length[31:0];state<=length==0?PAD_ONE:LOAD;
    end
   end
   LOAD:if(in_valid)begin
    if(in_last!=(remaining==1))begin error_code<=2;state<=ERROR;end
    else begin
     remaining<=remaining-1;
     if(byte_index==63)begin byte_index<=0;resume<=remaining==1?PAD_ONE:LOAD;state<=COMP_FLUSH;end
     else begin byte_index<=byte_index+1'b1;if(remaining==1)state<=PAD_ONE;end
    end
   end
   PAD_ONE:begin
    
    if(byte_index==63)begin byte_index<=0;resume<=PAD_ZERO;state<=COMP_FLUSH;end
    else begin byte_index<=byte_index+1'b1;state<=PAD_ZERO;end
   end
   PAD_ZERO:begin
    if(byte_index==56)begin length_index<=0;state<=PAD_LENGTH;end
    else begin
     
     if(byte_index==63)begin byte_index<=0;resume<=PAD_ZERO;state<=COMP_FLUSH;end
     else byte_index<=byte_index+1'b1;
    end
   end
   PAD_LENGTH:begin
    
    if(length_index==7)begin byte_index<=0;resume<=DIGEST;state<=COMP_FLUSH;end
    else begin byte_index<=byte_index+1'b1;length_index<=length_index+1'b1;end
   end
   COMP_FLUSH:state<=COMP_INIT;
   COMP_INIT:begin
    a<=hash[0];b<=hash[1];c<=hash[2];d<=hash[3];e<=hash[4];f<=hash[5];g<=hash[6];h<=hash[7];
    for(lane=0;lane<16;lane=lane+1)w[lane]<=block[511-lane*32-:32];
    round_index<=0;state<=ROUND;
   end
   ROUND:begin
    h<=g;g<=f;f<=e;e<=d+t1;d<=c;c<=b;b<=a;a<=an+ac;
    // Shifted window provides constant taps, avoiding16-way read muxes. Compute
    // W[t+16] while consuming W[t]; after W63, shifted-in zeros are unused.
    for(lane=0;lane<15;lane=lane+1)w[lane]<=w[lane+1];
    w[15]<=round_index<48?wn2+wn3:32'd0;
    if(round_index==63)state<=ADD_HASH;else round_index<=round_index+1'b1;
   end
   ADD_HASH:begin
    hash[0]<=hash[0]+a;hash[1]<=hash[1]+b;hash[2]<=hash[2]+c;hash[3]<=hash[3]+d;
    hash[4]<=hash[4]+e;hash[5]<=hash[5]+f;hash[6]<=hash[6]+g;hash[7]<=hash[7]+h;state<=resume;
   end
   DIGEST:if(out_ready)state<=IDLE;
   ERROR:if(error_ready)state<=IDLE;
   default:state<=IDLE;
  endcase
 end
endmodule
