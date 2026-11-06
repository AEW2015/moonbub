module header_math_miter(input wire[31:0] l0,l1,l2,l3,input wire[15:0]packet_bytes,output wire mismatch);
wire[31:0]header_pair01=l0+l1;
wire[31:0]header_pair23=l2+l3;
wire[31:0]old_total=32'd46+l0+l1+l2+l3;
wire[31:0]new_total=32'd46+header_pair01+header_pair23;
wire[31:0]old_prefix1=42+l0;
wire[31:0]new_prefix1=32'd42+l0;
wire[31:0]old_prefix2=42+l0+l1;
wire[31:0]new_prefix2=32'd42+header_pair01;
wire[31:0]old_prefix3=42+l0+l1+l2;
wire[31:0]new_prefix3=32'd42+header_pair01+l2;
assign mismatch=(old_total!=new_total)||(old_prefix1!=new_prefix1)||(old_prefix2!=new_prefix2)||(old_prefix3!=new_prefix3)||((old_total!={16'd0,packet_bytes})!=(new_total!={16'd0,packet_bytes}));
endmodule
