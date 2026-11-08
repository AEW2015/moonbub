// Local mapping candidate: no state, latency, clock or reset.
module cu71_balanced_identity_v019 #(parameter integer WIDTH=64)(
 input wire[WIDTH-1:0]a,b,output wire match
);
 localparam integer N3=(WIDTH+2)/3,N18=(N3+5)/6,N108=(N18+5)/6;
 // Preserve local reduction boundaries, rather than a wide carry-chain match.
 (* keep="true" *)wire[N3-1:0]eq3;
 (* keep="true" *)wire[N18-1:0]eq18;
 (* keep="true" *)wire[N108-1:0]eq108;
 genvar i,j;
 generate
  for(i=0;i<N3;i=i+1)begin:g3
   wire[2:0]bits_match;
   for(j=0;j<3;j=j+1)begin:gb
    if(i*3+j<WIDTH)assign bits_match[j]=~(a[i*3+j]^b[i*3+j]);
    else assign bits_match[j]=1'b1;
   end
   assign eq3[i]=&bits_match;
  end
  for(i=0;i<N18;i=i+1)begin:g18
   wire[5:0]bits_match;
   for(j=0;j<6;j=j+1)begin:gb
    if(i*6+j<N3)assign bits_match[j]=eq3[i*6+j];
    else assign bits_match[j]=1'b1;
   end
   assign eq18[i]=&bits_match;
  end
  for(i=0;i<N108;i=i+1)begin:g108
   wire[5:0]bits_match;
   for(j=0;j<6;j=j+1)begin:gb
    if(i*6+j<N18)assign bits_match[j]=eq18[i*6+j];
    else assign bits_match[j]=1'b1;
   end
   assign eq108[i]=&bits_match;
  end
 endgenerate
 assign match=&eq108;
endmodule
