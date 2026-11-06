// Three-bank ownership controller. All inputs are in one control clock domain.
// Validation and memory drain are explicit upstream contracts, not inferred.
module cu66_frame_bank_control (
    input logic clk, rst, abort_i, drain_done,
    input logic begin_valid,
    output logic begin_ready,
    input logic [31:0] begin_id,
    input logic begin_key,
    input logic [31:0] begin_reference_id,
    input logic commit_valid,
    output logic commit_ready,
    input logic commit_ok,
    input logic vblank, scanout_drained,
    output logic active, aborting,
    output logic [1:0] write_bank,
    output logic read_bank_valid,
    output logic [1:0] read_bank,
    output logic ref_valid,
    output logic [1:0] ref_bank,
    output logic [31:0] ref_id,
    output logic front_valid,
    output logic [1:0] front_bank,
    output logic [31:0] front_id,
    output logic pending_valid,
    output logic [1:0] pending_bank,
    output logic [31:0] pending_id,
    output logic begin_accepted, frame_committed, frame_presented, aborted,
    output logic error,
    output logic [7:0] error_code,
    output logic [31:0] accepted_count, presented_count
);
    logic [31:0] candidate_id;
    logic free_valid, safe_swap;
    logic [1:0] free_bank;
    always_comb begin
        free_valid=1'b0;
        free_bank=0;
        for (integer b=0; b<3; b=b+1) begin
            if (!free_valid && !(ref_valid && ref_bank==2'(b)) &&
                !(front_valid && front_bank==2'(b)) &&
                !(pending_valid && pending_bank==2'(b)) &&
                !(active && write_bank==2'(b))) begin
                free_valid=1'b1;
                free_bank=2'(b);
            end
        end
        safe_swap=vblank && scanout_drained && pending_valid;
        begin_ready=!rst && !abort_i && !active && free_valid;
        commit_ready=!rst && !abort_i && active && !aborting &&
                     (!commit_ok || !pending_valid || safe_swap);
    end

    always_ff @(posedge clk) begin
        if (rst) begin
            active<=0;
            aborting<=0;
            write_bank<=0;
            read_bank_valid<=0;
            read_bank<=0;
            ref_valid<=0;
            ref_bank<=0;
            ref_id<=32'hffffffff;
            front_valid<=0;
            front_bank<=0;
            front_id<=32'hffffffff;
            pending_valid<=0;
            pending_bank<=0;
            pending_id<=32'hffffffff;
            candidate_id<=32'hffffffff;
            begin_accepted<=0;
            frame_committed<=0;
            frame_presented<=0;
            aborted<=0;
            error<=0;
            error_code<=0;
            accepted_count<=0;
            presented_count<=0;
        end else begin
            begin_accepted<=0;
            frame_committed<=0;
            frame_presented<=0;
            aborted<=0;
            error<=0;
            error_code<=0;
            // A good pending frame may present even while a different writer
            // aborts. Retire old scanout readers before releasing the old front.
            if (safe_swap) begin
                front_valid<=1;
                front_bank<=pending_bank;
                front_id<=pending_id;
                pending_valid<=0;
                pending_id<=32'hffffffff;
                frame_presented<=1;
                presented_count<=presented_count+1;
            end
            if (active && aborting) begin
                if (drain_done) begin
                    active<=0;
                    aborting<=0;
                    read_bank_valid<=0;
                    candidate_id<=32'hffffffff;
                    aborted<=1;
                end
            end else if (active && abort_i) begin
                aborting<=1;
            end else if (commit_valid && commit_ready) begin
                if (!commit_ok) begin
                    aborting<=1;
                    error<=1;
                    error_code<=8'd4;
                end else begin
                    ref_valid<=1;
                    ref_bank<=write_bank;
                    ref_id<=candidate_id;
                    pending_valid<=1;
                    pending_bank<=write_bank;
                    pending_id<=candidate_id;
                    active<=0;
                    read_bank_valid<=0;
                    candidate_id<=32'hffffffff;
                    frame_committed<=1;
                    accepted_count<=accepted_count+1;
                end
            end else if (begin_valid && begin_ready) begin
                if (begin_id==32'hffffffff || (ref_valid && begin_id<=ref_id) ||
                    (begin_key && begin_reference_id!=32'hffffffff)) begin
                    error<=1;
                    error_code<=8'd1;
                end else if (!begin_key && (!ref_valid || begin_reference_id!=ref_id)) begin
                    error<=1;
                    error_code<=8'd2;
                end else begin
                    active<=1;
                    aborting<=0;
                    write_bank<=free_bank;
                    candidate_id<=begin_id;
                    read_bank_valid<=!begin_key;
                    read_bank<=ref_bank;
                    begin_accepted<=1;
                end
            end
        end
    end
endmodule
