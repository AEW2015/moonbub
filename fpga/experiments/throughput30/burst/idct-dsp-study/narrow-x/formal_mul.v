// Combinational arithmetic obligation only; not full sequential equivalence.
module formal_mul(input signed [15:0] x, y, input [12:0] coeff);
 wire signed [31:0] x32={{16{x[15]}},x};
 wire signed [31:0] y32={{16{y[15]}},y};
 wire signed [31:0] c32={19'd0,coeff};
 wire signed [12:0] c13=coeff;
 wire signed [16:0] sum17=x32+y32;
 wire signed [16:0] diff17=x32-y32;
 wire signed [31:0] sum32=x32+y32;
 wire signed [31:0] diff32=x32-y32;
 wire signed [31:0] orig_x=x32*c32, narrow_x=x*c13;
 wire signed [31:0] orig_sum=sum32*c32, narrow_sum=sum17*c13;
 wire signed [31:0] orig_diff=diff32*c32, narrow_diff=diff17*c13;
 always @* begin
  assume(!coeff[12]);
  assert(orig_x==narrow_x);
  assert(orig_sum==narrow_sum);
  assert(orig_diff==narrow_diff);
 end
endmodule
