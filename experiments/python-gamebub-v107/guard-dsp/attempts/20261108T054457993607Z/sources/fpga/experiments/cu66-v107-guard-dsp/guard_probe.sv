module guard_probe (
 input logic [16:0] begin_blocks,context_blocks,
 input logic [31:0] scratch_count,ingress_count,
 output logic [31:0] scratch_original,scratch_candidate,ingress_original,ingress_candidate,
 output logic scratch_old_reject,scratch_new_reject,ingress_old_reject,ingress_new_reject
);
    assign scratch_original=32'(begin_blocks)*43;
    (* use_dsp = "no" *) logic [31:0] begin_limit43;
    assign begin_limit43=32'(begin_blocks)*43;
    assign scratch_candidate=begin_limit43;
    assign scratch_old_reject=scratch_count>scratch_original;
    assign scratch_new_reject=scratch_count>begin_limit43;
    assign ingress_original=32'(context_blocks)*43;
    (* use_dsp = "no" *) logic [31:0] context_limit43;
    assign context_limit43=32'(context_blocks)*43;
    assign ingress_candidate=context_limit43;
    assign ingress_old_reject=ingress_count>ingress_original;
    assign ingress_new_reject=ingress_count>context_limit43;
endmodule
