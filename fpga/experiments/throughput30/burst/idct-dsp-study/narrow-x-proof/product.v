module product(input signed [15:0] a,input signed [16:0] w,input signed [12:0] c);
 wire signed [31:0] a32={{16{a[15]}},a};
 wire signed [31:0] w32={{15{w[16]}},w};
 wire signed [31:0] c32={{19{c[12]}},c};
 wire signed [31:0] x=a*c, xr=a32*c32;
 wire signed [31:0] y=w*c, yr=w32*c32;
 always @* begin assert(x==xr);assert(y==yr);end
endmodule
