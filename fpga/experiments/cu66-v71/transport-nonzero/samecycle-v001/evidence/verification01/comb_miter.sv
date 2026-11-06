module transport_comb_miter(input wire[31:0]gray,output wire mismatch);
 function automatic[31:0]ungray_transport(input[31:0]value);
 integer i;begin for(i=0;i<32;i=i+1)ungray_transport[i]=^(value>>i);end endfunction
assign mismatch=(ungray_transport(gray)!=0)!=(|gray);
endmodule
