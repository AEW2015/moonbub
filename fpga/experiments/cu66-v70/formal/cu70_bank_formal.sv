// Bounded safety harness for frozen v69 three-bank control only.
// All transaction/control inputs are symbolic. The runner constrains rst=1
// at step1 and rst=0 afterward; no fairness or legal-traffic assumptions.
module cu70_bank_formal (
    input wire clk,rst,abort_i,drain_done,
    input wire begin_valid,begin_key,commit_valid,commit_ok,vblank,scanout_drained,
    input wire [31:0] begin_id,begin_reference_id,
    output wire cover_active,cover_read,cover_pending,cover_front,
    output wire cover_abort_and_present
);
    wire begin_ready,commit_ready,active,aborting,read_bank_valid,ref_valid,front_valid,pending_valid;
    wire [1:0] write_bank,read_bank,ref_bank,front_bank,pending_bank;
    wire [31:0] ref_id,front_id,pending_id,accepted_count,presented_count;
    wire begin_accepted,frame_committed,frame_presented,aborted,error;
    wire [7:0] error_code;
    reg past_valid=0;
    cu66_frame_bank_control dut(.*);
    assign cover_active=active;
    assign cover_read=read_bank_valid;
    assign cover_pending=pending_valid;
    assign cover_front=front_valid;
    assign cover_abort_and_present=aborted&&frame_presented;
    always @(posedge clk)begin
        past_valid<=1;
        if(past_valid&&!rst)begin
            // P01..P05: all live bank identifiers are in the implemented range.
            assert(!active||write_bank<=2);
            assert(!ref_valid||ref_bank<=2);
            assert(!front_valid||front_bank<=2);
            assert(!pending_valid||pending_bank<=2);
            assert(!read_bank_valid||read_bank<=2);
            // P06..P09: candidate writer excludes every published/read bank.
            assert(!active||!ref_valid||write_bank!=ref_bank);
            assert(!active||!front_valid||write_bank!=front_bank);
            assert(!active||!pending_valid||write_bank!=pending_bank);
            assert(!read_bank_valid||active);
            // P10..P12: presentation separation and retained abort/read leases.
            assert(!pending_valid||!front_valid||pending_bank!=front_bank);
            assert(!read_bank_valid||read_bank!=write_bank);
            assert(!aborting||active);
            // P13..P16: abort cannot advance accepted canonical history. A
            // previous pending presentation is deliberately allowed to advance.
            if(!$past(rst)&&$past(abort_i))begin
                assert(accepted_count==$past(accepted_count));
                assert(ref_valid==$past(ref_valid));
                assert(ref_bank==$past(ref_bank));
                assert(ref_id==$past(ref_id));
            end
        end
    end
endmodule
