module threshold_math_probe (
 input logic clk,reset,take,input logic [1:0] selected,
 input logic [31:0] numerator,input logic [16:0] blocks,
 output logic [31:0] meta_threshold1,meta_threshold2,meta_threshold3,
 output logic [2:0] live,output logic [2:0] bad,output logic selected_bad
);
 logic [7:0] ram_data,fetch_bytes[0:45];logic [5:0] fetch_index;
 logic prefix_header_capture,cancelled,context_failure,context_active,ctx_done;
 logic [1:0] band;logic [16:0] context_blocks;logic [31:0] counts[0:3];
 assign ram_data=numerator[31:24];assign fetch_index=6'(33+4*32'(selected));
 assign prefix_header_capture=take&&!reset;assign cancelled=reset;
 assign context_failure=0;assign context_active=0;assign ctx_done=0;
 assign band=selected+2'd1;assign context_blocks=blocks;
 for(genvar g=0;g<46;g=g+1)begin:bytes_in
  if(g==30||g==34||g==38)begin: low assign fetch_bytes[g]=numerator[7:0];end
  else if(g==31||g==35||g==39)begin: middle assign fetch_bytes[g]=numerator[15:8];end
  else if(g==32||g==36||g==40)begin: high assign fetch_bytes[g]=numerator[23:16];end
  else begin: unused_byte assign fetch_bytes[g]=0;end
 end
 for(genvar g=0;g<4;g=g+1)begin: counts_in assign counts[g]=numerator;end
    // COUNT_THRESHOLD_PIPELINE_BEGIN: nine registered positions E0..E8.
    // Capture at WAIT33/37/41; latest commit WAIT45, before HEADER.
    // Private payload has no reset or global CE; validity owns each packet.
    logic [31:0] count_threshold[0:2];
    logic [2:0] threshold_live;
    logic descriptor_count_bad;
    assign meta_threshold1=count_threshold[0];
    assign meta_threshold2=count_threshold[1];
    assign meta_threshold3=count_threshold[2];
    for(genvar tb=0;tb<3;tb=tb+1)begin: threshold_pipes
        localparam integer DIVISOR=tb==0?5:tb==1?15:43;
        localparam integer LAST=33+4*tb;
        localparam logic [31:0] RECIP=32'(64'h100000000/64'(DIVISOR));
        logic [31:0] forwarded_count;
        logic [7:0] valid_pipe;
        logic [31:0] captured_count;
        logic flush, capture;
        function automatic logic [32:0] partial_product(input logic [15:0] a,input logic [16:0] b);
            return a*b;
        endfunction
        (* use_dsp = "yes" *) logic [15:0] mul00_hi;
        (* use_dsp = "yes" *) logic [31:0] mul01, mul10, mul11, check_lo;
        (* use_dsp = "yes" *) logic [15:0] check_hi;
        logic [32:0] cross_s1;
        logic [16:0] cross_carry_s2;
        logic [15:0] low_carry_s1;
        logic [31:0] high_s1, high_s2;
        logic [31:0] n_delay[0:5];
        logic [31:0] q_s3, q_s4, q_s5, q_s6;
        logic [31:0] product_s5, remainder_s6;
        logic [1:0] correction;
        assign forwarded_count={ram_data,fetch_bytes[LAST-1],fetch_bytes[LAST-2],fetch_bytes[LAST-3]};
        assign capture=prefix_header_capture&&fetch_index==6'(LAST);
        assign flush=cancelled||context_failure||(context_active&&ctx_done);
        assign correction=remainder_s6==0?2'd0:(remainder_s6>32'(DIVISOR)?2'd2:2'd1);
        always_ff @(posedge clk)begin
            if(flush)begin valid_pipe<=0;threshold_live[tb]<=0;end
            else begin
                valid_pipe<={valid_pipe[6:0],capture};
                if(valid_pipe[7])threshold_live[tb]<=1;
            end
        end
        always_ff @(posedge clk)begin
            // E0: register the forwarded word before any multiplication.
            captured_count<=forwarded_count;
            // E1: exact unsigned16 x unsigned17 reciprocal products.
            mul00_hi<=16'(partial_product(captured_count[15:0],{1'b0,RECIP[15:0]})>>16);
            mul01<=32'(partial_product(captured_count[15:0],{1'b0,RECIP[31:16]}));
            mul10<=32'(partial_product(captured_count[31:16],{1'b0,RECIP[15:0]}));
            mul11<=32'(partial_product(captured_count[31:16],{1'b0,RECIP[31:16]}));
            n_delay[0]<=captured_count;
            for(integer j=1;j<6;j=j+1)n_delay[j]<=n_delay[j-1];
            // E2/E3: split the three-term cross sum across two edges.
            cross_s1<={1'b0,mul01}+{1'b0,mul10};
            low_carry_s1<=mul00_hi;high_s1<=mul11;
            cross_carry_s2<=17'((cross_s1+{17'd0,low_carry_s1})>>16);high_s2<=high_s1;
            // E4: high32 of n*M, q0 is floor(n/d) or one less.
            q_s3<=high_s2+{15'd0,cross_carry_s2};
            // E5: bounded q0*d, again using16 x17 registered products.
            check_lo<=32'(partial_product(q_s3[15:0],17'(DIVISOR)));
            check_hi<=16'(partial_product(q_s3[31:16],17'(DIVISOR)));q_s4<=q_s3;
            // E6/E7: full product is <=n, so its low32 are exact.
            product_s5<=check_lo+{check_hi,16'd0};q_s5<=q_s4;
            remainder_s6<=n_delay[5]-product_s5;q_s6<=q_s5;
            // E8: one carry chain, with a bounded0/1/2 correction.
            if(valid_pipe[7])count_threshold[tb]<=q_s6+{30'd0,correction};
        end
`ifndef SYNTHESIS
        always_ff @(posedge clk)if(!flush&&valid_pipe[7])begin
            assert(remainder_s6<32'(2*DIVISOR))else $fatal(1,"count reciprocal remainder bound");
        end
`endif
    end
    always_comb begin
        case(band)
            1:descriptor_count_bad=32'(context_blocks)<count_threshold[0];
            2:descriptor_count_bad=32'(context_blocks)<count_threshold[1];
            3:descriptor_count_bad=32'(context_blocks)<count_threshold[2];
            default:descriptor_count_bad=counts[0]>32'(context_blocks);
        endcase
    end
    // COUNT_THRESHOLD_PIPELINE_END
 assign selected_bad=descriptor_count_bad;
 assign live=threshold_live;
 assign bad={32'(blocks)<meta_threshold3,32'(blocks)<meta_threshold2,32'(blocks)<meta_threshold1};
endmodule
