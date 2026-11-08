module prefix_math_probe (
 input logic clk,prefix_header_capture,
 input logic [5:0] fetch_index,
 input logic [7:0] ram_data,
 input logic [95:0] prior_header,
 input logic [31:0] begin_count1,begin_count2,begin_count3,
 input logic [16:0] begin_blocks,
 output logic [31:0] meta_prefix1,meta_prefix12,meta_prefix123,
 output logic [23:0] verify_ignored_high,
 output logic [31:0] old_plan2,old_plan3,old_used,new_plan2,new_plan3,new_used
);
 logic [7:0] fetch_bytes[0:45];
 logic [31:0] plan_align1,plan_align2,plan_align3,plan_prefix12,plan_prefix123;
 always_comb begin
  for(integer i=0;i<46;i=i+1)fetch_bytes[i]=0;
  for(integer i=0;i<12;i=i+1)fetch_bytes[30+i]=prior_header[8*i+:8];
 end
 assign verify_ignored_high={fetch_bytes[41],fetch_bytes[37],fetch_bytes[33]};
 assign meta_prefix1=plan_align1;
 assign meta_prefix12=plan_prefix12;
 assign meta_prefix123=plan_prefix123;
    function automatic logic [31:0] count_aligned(input logic [31:0] n);
        return ((n<<2)+32'd15)&32'hfffffff0;
    endfunction
    function automatic logic [31:0] aligned(input logic [31:0] n);
        aligned=(n+15)&32'hfffffff0;
    endfunction
    function automatic logic [31:0] sum3(input logic [31:0] a,b,c);
        return (a^b^c)+(((a&b)|(a&c)|(b&c))<<1);
    endfunction
    function automatic logic [31:0] sum4(input logic [31:0] a,b,c,d);
        logic [31:0] s,carry;
        begin
            s=a^b^c;carry=((a&b)|(a&c)|(b&c))<<1;
            return sum3(s,carry,d);
        end
    endfunction
    function automatic logic [31:0] sum5(input logic [31:0] a,b,c,d,e);
        logic [31:0] s0,c0,s1,c1;
        begin
            s0=a^b^c;c0=((a&b)|(a&c)|(b&c))<<1;
            s1=s0^d^e;c1=((s0&d)|(s0&e)|(d&e))<<1;
            return sum3(s1,c1,c0);
        end
    endfunction
    always_ff @(posedge clk)begin
        if(prefix_header_capture)begin
            if(fetch_index==6'd33)plan_align1<=count_aligned({ram_data,fetch_bytes[32],fetch_bytes[31],fetch_bytes[30]});
            if(fetch_index==6'd37)plan_align2<=count_aligned({ram_data,fetch_bytes[36],fetch_bytes[35],fetch_bytes[34]});
            if(fetch_index==6'd41)plan_align3<=count_aligned({ram_data,fetch_bytes[40],fetch_bytes[39],fetch_bytes[38]});
        end
        plan_prefix12<=plan_align1+plan_align2;
        plan_prefix123<=plan_prefix12+plan_align3;
    end
 assign old_plan2=sum3(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4));
 assign old_plan3=sum4(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4),aligned(begin_count2*4));
 assign old_used=sum5(32,aligned(32'(begin_blocks)*2),aligned(begin_count1*4),aligned(begin_count2*4),aligned(begin_count3*4));
 assign new_plan2=(32+aligned(32'(begin_blocks)*2))+meta_prefix1;
 assign new_plan3=(32+aligned(32'(begin_blocks)*2))+meta_prefix12;
 assign new_used=(32+aligned(32'(begin_blocks)*2))+meta_prefix123;
endmodule
