module miter(input [31:0]gray,output mismatch);
wire[31:0]binary;
for(genvar i=0;i<32;i=i+1)assign binary[i]=^(gray>>i);
assign mismatch=(|binary)^(|gray);
endmodule
