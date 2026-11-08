#!/usr/bin/env python3
"""Prepare four-file packet-count ceilings, preserving existing public cycles."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];BASE=ROOT/'fpga/experiments/cu66-v107-plan-prefix';OUT=ROOT/'fpga/experiments/cu66-v107-count-threshold'
HASHES={'br88_packet_ingress_sync_v91h.sv':'f7e05105dc7b00f7ed6ef493a188ede0252ae12c7a344854729848813d00327f','br88_packet_ingress_v91h.sv':'83577ff7278102040bc0315457be9c7bd8c1e4dd5467a425b8c58eb1bcf31164','br88_pipeline_v91h.sv':'d00f774fd8c4900ad98c40f5ac1e3b17be40b07ea62ebe71ef2c33efff156947','packed_scratch_v91g2.sv':'4d06f2c15b85091640e181a83e27d6072ec680f4ec8fe62245ee9398337ae622'}
def sha(s):return hashlib.sha256(s.encode()).hexdigest()
def pipeline():return r'''
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
'''
def main():
 OUT.mkdir(exist_ok=True);texts={n:(BASE/n).read_text() for n in HASHES};edits={n:[] for n in HASHES}
 for n,h in HASHES.items():assert sha(texts[n])==h,n
 def add(n,a,b):assert texts[n].count(a)==1,(n,a);texts[n]=texts[n].replace(a,b,1);edits[n].append(dict(before=a,after=b,expected_occurrences=1))
 sync='br88_packet_ingress_sync_v91h.sv';wrapper='br88_packet_ingress_v91h.sv';child='br88_pipeline_v91h.sv';scratch='packed_scratch_v91g2.sv'
 for n in (sync,wrapper):
  add(n,'    output logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123,','    output logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123,\n    output logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3,')
 add(sync,'    function automatic logic [31:0] cached32(input integer at);',pipeline()+'\n    function automatic logic [31:0] cached32(input integer at);')
 add(sync,'fetch_bytes[0]>19 || fetch_bytes[1]>11 || counts[band]>descriptor_limit','fetch_bytes[0]>19 || fetch_bytes[1]>11 || descriptor_count_bad')
 invariants=r'''    always_ff @(posedge clk)if(meta_valid)begin
        assert(&threshold_live)else $fatal(1,"count threshold not live before metadata");
        assert(meta_threshold1==meta_count1/32'd5+32'(meta_count1%32'd5!=0))else $fatal(1,"count threshold1 stale owner");
        assert(meta_threshold2==meta_count2/32'd15+32'(meta_count2%32'd15!=0))else $fatal(1,"count threshold2 stale owner");
        assert(meta_threshold3==meta_count3/32'd43+32'(meta_count3%32'd43!=0))else $fatal(1,"count threshold3 stale owner");
    end
    always_ff @(posedge clk)if(!cancelled&&!context_failure&&!(context_active&&ctx_done)&&state==DESCRIPTOR&&band!=0)begin
        assert(threshold_live[band-1'b1])else $fatal(1,"descriptor count threshold not live");
        assert(descriptor_count_bad==(counts[band]>descriptor_limit))else $fatal(1,"descriptor count threshold mismatch");
    end
    assert property (@(posedge clk) disable iff(cancelled)
        meta_valid&&!meta_ready |=> cancelled || (meta_valid&&$stable({meta_threshold1,meta_threshold2,meta_threshold3})))
        else $fatal(1,"held count threshold changed");
'''
 add(sync,'`ifndef SYNTHESIS\n    always_ff @(posedge clk)if(meta_valid)begin','`ifndef SYNTHESIS\n'+invariants+'    always_ff @(posedge clk)if(meta_valid)begin')
 add(wrapper,'        // Legacy branch has no header-fetch cache; preserve exact count algebra.','''        // Exact legacy fallback has no timing claim and avoids n+d-1 overflow.
        assign meta_threshold1=meta_count1/32'd5+32'(meta_count1%32'd5!=0);
        assign meta_threshold2=meta_count2/32'd15+32'(meta_count2%32'd15!=0);
        assign meta_threshold3=meta_count3/32'd43+32'(meta_count3%32'd43!=0);
        // Legacy branch has no header-fetch cache; preserve exact count algebra.''')
 add(wrapper,'            .meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),','            .meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),\n            .meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),')
 add(child,'    logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123;','    logic [31:0] meta_prefix1, meta_prefix12, meta_prefix123;\n    logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3;')
 add(child,'        .meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),','        .meta_prefix1(meta_prefix1),.meta_prefix12(meta_prefix12),.meta_prefix123(meta_prefix123),\n        .meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),')
 add(child,'        .begin_prefix1(meta_prefix1),.begin_prefix12(meta_prefix12),.begin_prefix123(meta_prefix123),','        .begin_prefix1(meta_prefix1),.begin_prefix12(meta_prefix12),.begin_prefix123(meta_prefix123),\n        .begin_threshold1(meta_threshold1),.begin_threshold2(meta_threshold2),.begin_threshold3(meta_threshold3),')
 add(scratch,'    input logic [31:0] begin_prefix1, begin_prefix12, begin_prefix123,','    input logic [31:0] begin_prefix1, begin_prefix12, begin_prefix123,\n    input logic [31:0] begin_threshold1, begin_threshold2, begin_threshold3,')
 add(scratch,"begin_count1>32'(begin_blocks)*5 || begin_count2>32'(begin_blocks)*15 ||\n                        begin_count3>begin_limit43", "32'(begin_blocks)<begin_threshold1 || 32'(begin_blocks)<begin_threshold2 ||\n                        32'(begin_blocks)<begin_threshold3")
 add(scratch,'    always_ff @(posedge clk)if(begin_valid&&begin_ready)begin','''    always_ff @(posedge clk)if(begin_valid&&begin_ready)begin
        assert(begin_threshold1==begin_count1/32'd5+32'(begin_count1%32'd5!=0))else $fatal(1,"scratch threshold1 ownership mismatch");
        assert(begin_threshold2==begin_count2/32'd15+32'(begin_count2%32'd15!=0))else $fatal(1,"scratch threshold2 ownership mismatch");
        assert(begin_threshold3==begin_count3/32'd43+32'(begin_count3%32'd43!=0))else $fatal(1,"scratch threshold3 ownership mismatch");
        assert((32'(begin_blocks)<begin_threshold3)==(begin_count3>begin_limit43))else $fatal(1,"scratch43 threshold predicate mismatch");''')
 recipe=dict(schema='v107-count-threshold-exact-four-source-v1',status='PREPARED_NOT_RTL_QUALIFIED',public_added_cycles=0,registered_positions=9,post_capture_edges=8,latest_capture='F_HEADER WAIT41',latest_commit='F_HEADER WAIT45',production={})
 for n,s in texts.items():
  (OUT/n).write_text(s);recipe['production'][n]=dict(original=str((BASE/n).relative_to(ROOT)),original_sha256=HASHES[n],candidate_sha256=sha(s),edits=edits[n])
 (OUT/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n');print(json.dumps({n:x['candidate_sha256'] for n,x in recipe['production'].items()},indent=2))
if __name__=='__main__':main()
