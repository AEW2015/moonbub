module product(input signed [31:0] a,input signed [12:0] c);
 wire signed [31:0] c32={{19{c[12]}},c};
 wire signed [31:0] x=a*c, y=a*c32;
 always @* assert(x==y);
endmodule
