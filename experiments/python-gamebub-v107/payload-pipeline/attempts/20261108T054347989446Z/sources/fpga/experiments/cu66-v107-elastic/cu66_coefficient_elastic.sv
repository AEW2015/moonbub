// V107: one registered coefficient token, with an ordered end-of-input fence.
module cu66_coefficient_elastic (
    input logic clk, reset, start, cancel,
    input logic input_done,
    input logic in_valid,
    output logic in_ready,
    input logic [31:0] in_epoch, in_child_epoch,
    input logic [1:0] in_plane, in_qscale,
    input logic [15:0] in_block,
    input logic [12:0] in_tile,
    input logic [10:0] in_qcell,
    input logic [5:0] in_index,
    input logic signed [15:0] in_value,
    output logic out_valid,
    input logic out_ready,
    output logic [31:0] out_epoch, out_child_epoch,
    output logic [1:0] out_plane, out_qscale,
    output logic [15:0] out_block,
    output logic [12:0] out_tile,
    output logic [10:0] out_qcell,
    output logic [5:0] out_index,
    output logic signed [15:0] out_value,
    output logic output_done, occupied
);
    logic active, full, done_pending, final_wait;
    logic [129:0] payload;
    logic kill, closed;
    assign kill=reset||start||cancel;
    // A simultaneous done plus stalled final offer retains that offer's owner.
    // Later tokens are excluded once this final offer has been accepted.
    assign closed=done_pending&&!final_wait;
    assign in_ready=active&&!kill&&!closed&&(!full||out_ready);
    assign out_valid=active&&!kill&&full;
    assign output_done=active&&!kill&&done_pending&&!final_wait&&!full;
    assign occupied=full||final_wait;
    assign {out_epoch,out_child_epoch,out_plane,out_qscale,out_block,
            out_tile,out_qcell,out_index,out_value}=payload;
    always_ff @(posedge clk)begin
        if(reset||start||cancel)begin
            active<=start&&!reset&&!cancel;full<=0;done_pending<=0;final_wait<=0;
        end else if(active)begin
            if(out_valid&&out_ready)full<=0;
            if(in_valid&&in_ready)begin
                payload<={in_epoch,in_child_epoch,in_plane,in_qscale,in_block,
                          in_tile,in_qcell,in_index,in_value};
                full<=1;
                if(final_wait)final_wait<=0;
            end
            if(input_done&&!done_pending)begin
                done_pending<=1;
                final_wait<=in_valid&&!in_ready;
            end
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!kill)begin
        assert(!output_done||(!out_valid&&!in_ready&&!occupied))
            else $fatal(1,"coefficient fence overtook token");
        assert(!final_wait||done_pending)
            else $fatal(1,"coefficient final-offer owner without fence");
    end
    assert property (@(posedge clk) disable iff(kill)
        out_valid&&!out_ready |=> kill || (out_valid&&$stable(payload)))
        else $fatal(1,"coefficient held token changed");
`endif
endmodule
