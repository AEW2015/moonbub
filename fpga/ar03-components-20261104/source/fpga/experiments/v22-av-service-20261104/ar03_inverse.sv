// Standalone AR03 inverse prototype; no prediction, clipping or hardware deployment.
module ar03_inverse (
 input wire clk, input wire reset, input wire abort,
 input wire start_valid, output wire start_ready,
 input wire [31:0] start_owner, input wire [31:0] start_block,
 input wire in_valid, output wire in_ready, input wire signed [31:0] in_data, input wire in_last,
 output wire out_valid, input wire out_ready, output wire signed [31:0] out_data,
 output wire [31:0] out_owner, output wire [31:0] out_block, output wire [5:0] out_index, output wire out_last,
 output wire error_valid, input wire error_ready, output reg [1:0] error_code,
 output reg [1:0] classification
);
 localparam IDLE=0, LOAD=1, CLASSIFY=2, FIRST=3, STORE_FIRST=4, SECOND=5, STORE_SECOND=6, OUTPUT=7, ERROR=8, DC_SECOND=9, DC_STORE=10, FIRST_PRODUCT=11, FIRST_ACC=12, SECOND_PRODUCT=13, SECOND_ACC=14;
 reg [3:0] state;
 reg [31:0] owner,block_id;
 reg [5:0] index;
 reg [2:0] group,k;
 reg invalid_range,has_ac;
 reg signed [31:0] coeff[0:63], middle[0:63], result[0:63];
 reg signed [39:0] acc[0:7];
 reg signed [31:0] dc,dc_middle;
 reg signed [31:0] operand;
 reg signed [15:0] basis_reg[0:7];
 reg signed [39:0] product_reg[0:7];
 integer lane;
 function automatic signed [15:0] basis(input [2:0] a,input [2:0] b);
 begin case ({a,b})
 6'd0: basis = 16'sd5793;
 6'd1: basis = 16'sd5793;
 6'd2: basis = 16'sd5793;
 6'd3: basis = 16'sd5793;
 6'd4: basis = 16'sd5793;
 6'd5: basis = 16'sd5793;
 6'd6: basis = 16'sd5793;
 6'd7: basis = 16'sd5793;
 6'd8: basis = 16'sd8035;
 6'd9: basis = 16'sd6811;
 6'd10: basis = 16'sd4551;
 6'd11: basis = 16'sd1598;
 6'd12: basis = -16'sd1598;
 6'd13: basis = -16'sd4551;
 6'd14: basis = -16'sd6811;
 6'd15: basis = -16'sd8035;
 6'd16: basis = 16'sd7568;
 6'd17: basis = 16'sd3135;
 6'd18: basis = -16'sd3135;
 6'd19: basis = -16'sd7568;
 6'd20: basis = -16'sd7568;
 6'd21: basis = -16'sd3135;
 6'd22: basis = 16'sd3135;
 6'd23: basis = 16'sd7568;
 6'd24: basis = 16'sd6811;
 6'd25: basis = -16'sd1598;
 6'd26: basis = -16'sd8035;
 6'd27: basis = -16'sd4551;
 6'd28: basis = 16'sd4551;
 6'd29: basis = 16'sd8035;
 6'd30: basis = 16'sd1598;
 6'd31: basis = -16'sd6811;
 6'd32: basis = 16'sd5793;
 6'd33: basis = -16'sd5793;
 6'd34: basis = -16'sd5793;
 6'd35: basis = 16'sd5793;
 6'd36: basis = 16'sd5793;
 6'd37: basis = -16'sd5793;
 6'd38: basis = -16'sd5793;
 6'd39: basis = 16'sd5793;
 6'd40: basis = 16'sd4551;
 6'd41: basis = -16'sd8035;
 6'd42: basis = 16'sd1598;
 6'd43: basis = 16'sd6811;
 6'd44: basis = -16'sd6811;
 6'd45: basis = -16'sd1598;
 6'd46: basis = 16'sd8035;
 6'd47: basis = -16'sd4551;
 6'd48: basis = 16'sd3135;
 6'd49: basis = -16'sd7568;
 6'd50: basis = 16'sd7568;
 6'd51: basis = -16'sd3135;
 6'd52: basis = -16'sd3135;
 6'd53: basis = 16'sd7568;
 6'd54: basis = -16'sd7568;
 6'd55: basis = 16'sd3135;
 6'd56: basis = 16'sd1598;
 6'd57: basis = -16'sd4551;
 6'd58: basis = 16'sd6811;
 6'd59: basis = -16'sd8035;
 6'd60: basis = 16'sd8035;
 6'd61: basis = -16'sd6811;
 6'd62: basis = 16'sd4551;
 6'd63: basis = -16'sd1598;
 default: basis=0;
 endcase end endfunction
 function automatic signed [31:0] round_q14(input signed [39:0] v);
 reg signed [39:0] biased;
 begin biased=v+40'sd8192; round_q14=biased >>> 14; end endfunction
 function automatic signed [39:0] product(input signed [31:0] a,input signed [15:0] b);
 reg signed [47:0] wide;
 begin wide=a*b; product=wide[39:0]; end endfunction
 assign start_ready=(state==IDLE) && !reset && !abort;
 assign in_ready=(state==LOAD) && !reset && !abort;
 assign out_valid=(state==OUTPUT) && !reset && !abort;
 assign out_data=result[index];
 assign out_owner=owner; assign out_block=block_id;
 assign out_index=index; assign out_last=(index==63);
 assign error_valid=(state==ERROR) && !reset && !abort;
 always @(posedge clk) begin
  if(reset || abort) begin state<=IDLE; index<=0; group<=0; k<=0; invalid_range<=0; has_ac<=0; error_code<=0; classification<=0; owner<=0; block_id<=0; end
  else case(state)
   IDLE: if(start_valid) begin owner<=start_owner;block_id<=start_block;index<=0;has_ac<=0;invalid_range<=0;state<=LOAD; end
   LOAD: if(in_valid) begin
    coeff[index]<=in_data;
    if(in_data < -32'sd522240 || in_data > 32'sd522240) invalid_range<=1;
    if(index!=0 && in_data!=0) has_ac<=1;
    if(in_last != (index==63)) begin error_code<=2; state<=ERROR; end
    else if(index==63) state<=CLASSIFY;
    else index<=index+1'b1;
   end
   CLASSIFY: begin
    if(invalid_range) begin error_code<=1;state<=ERROR; end
    else if(!has_ac) begin
     classification<=(coeff[0]==0)?0:1;
     if(coeff[0]==0) begin
      for(lane=0;lane<64;lane=lane+1) result[lane]<=0;
      index<=0;state<=OUTPUT;
     end else begin
      dc_middle<=round_q14(product(coeff[0],16'sd5793));
      state<=DC_SECOND;
     end
    end else begin
     classification<=2;group<=0;k<=0;
     for(lane=0;lane<8;lane=lane+1) acc[lane]<=0;
     state<=FIRST;
    end
   end
   FIRST: begin
    operand<=coeff[{group,k}];
    for(lane=0;lane<8;lane=lane+1) basis_reg[lane]<=basis(k,lane);
    state<=FIRST_PRODUCT;
   end
   FIRST_PRODUCT: begin
    for(lane=0;lane<8;lane=lane+1) product_reg[lane]<=product(operand,basis_reg[lane]);
    state<=FIRST_ACC;
   end
   FIRST_ACC: begin
    if(operand!=0) for(lane=0;lane<8;lane=lane+1) acc[lane]<=acc[lane]+product_reg[lane];
    if(k==7) state<=STORE_FIRST; else begin k<=k+1'b1;state<=FIRST;end
   end
   STORE_FIRST: begin
    for(lane=0;lane<8;lane=lane+1) begin middle[group*8+lane]<=round_q14(acc[lane]);acc[lane]<=0;end
    k<=0;
    if(group==7) begin group<=0;state<=SECOND;end else begin group<=group+1'b1;state<=FIRST;end
   end
   SECOND: begin
    operand<=middle[{k,group}];
    for(lane=0;lane<8;lane=lane+1) basis_reg[lane]<=basis(k,lane);
    state<=SECOND_PRODUCT;
   end
   SECOND_PRODUCT: begin
    for(lane=0;lane<8;lane=lane+1) product_reg[lane]<=product(operand,basis_reg[lane]);
    state<=SECOND_ACC;
   end
   SECOND_ACC: begin
    if(operand!=0) for(lane=0;lane<8;lane=lane+1) acc[lane]<=acc[lane]+product_reg[lane];
    if(k==7) state<=STORE_SECOND;else begin k<=k+1'b1;state<=SECOND;end
   end
   STORE_SECOND: begin
    for(lane=0;lane<8;lane=lane+1) begin result[lane*8+group]<=round_q14(acc[lane]);acc[lane]<=0;end
    k<=0;
    if(group==7) begin index<=0;state<=OUTPUT;end else begin group<=group+1'b1;state<=SECOND;end
   end
   DC_SECOND: begin
    dc<=round_q14(product(dc_middle,16'sd5793));
    state<=DC_STORE;
   end
   DC_STORE: begin
    for(lane=0;lane<64;lane=lane+1) result[lane]<=dc;
    index<=0;state<=OUTPUT;
   end
   OUTPUT: if(out_ready) begin if(index==63) state<=IDLE;else index<=index+1'b1;end
   ERROR: if(error_ready) state<=IDLE;
   default: state<=IDLE;
  endcase
 end
endmodule
