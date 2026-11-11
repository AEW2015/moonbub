// Standalone V129 ownership-boundary prototype. Not wired into the producer.
// Reset/kill invalidate control, not the 204-bit payload storage.
module v129_dense_owned_queue (
    input logic clk, reset, kill,
    input logic arm_valid, output logic arm_ready,
    input logic [31:0] arm_frame_epoch, arm_child_epoch,
    input logic [15:0] arm_first_block,
    input logic child_quiescent, memory_debt_empty,
    input logic finish_valid, output logic finish_ready,
    input logic in_valid, output logic in_ready,
    input logic [31:0] in_frame_epoch, in_child_epoch,
    input logic [15:0] in_block,
    input logic [5:0] in_index,
    input logic signed [15:0] in_value,
    input logic publication_context_ready,
    output logic out_valid, input logic out_ready,
    output logic [31:0] out_frame_epoch, out_child_epoch,
    output logic [15:0] out_block,
    output logic [5:0] out_index,
    output logic signed [15:0] out_value,
    output logic owner_fault, output logic active,
    output logic [1:0] occupancy,
    output logic [15:0] acquisition_block
);
    typedef struct packed {
        logic [31:0] frame_epoch, child_epoch;
        logic [15:0] block_id;
        logic [5:0] index;
        logic signed [15:0] value;
    } tuple_t;
    tuple_t payload [0:1];
    logic head, tail;
    logic [31:0] owner_frame, owner_child;
    logic bad_offer, push, pop;

    // No dependence on downstream-ready or on the wide owner comparison.
    assign arm_ready=!active && !owner_fault && occupancy==2'd0 &&
        child_quiescent && memory_debt_empty && !reset && !kill;
    assign in_ready=active && !owner_fault && occupancy<2'd2 && !reset && !kill;
    assign out_valid=active && !owner_fault && occupancy!=2'd0 &&
        publication_context_ready && !reset && !kill;
    assign finish_ready=active && !owner_fault && occupancy==2'd0 && !in_valid &&
        child_quiescent && memory_debt_empty && !reset && !kill;
    assign {out_frame_epoch,out_child_epoch,out_block,out_index,out_value}=payload[head];
    assign bad_offer=active && in_valid &&
        (in_frame_epoch!=owner_frame || in_child_epoch!=owner_child || in_block!=acquisition_block);
    assign push=in_valid && in_ready;
    assign pop=out_valid && out_ready;

    // Even an accepted bad offer may refresh a payload bank, but that bank is
    // not owned after the fault edge and cannot become an output transaction.
    always_ff @(posedge clk)if(push)
        payload[tail]<='{frame_epoch:in_frame_epoch,child_epoch:in_child_epoch,
                         block_id:in_block,index:in_index,value:in_value};
    always_ff @(posedge clk)begin
        if(reset || kill)begin
            active<=0;owner_fault<=0;occupancy<=0;head<=0;tail<=0;
        end else if(arm_valid && arm_ready)begin
            owner_frame<=arm_frame_epoch;owner_child<=arm_child_epoch;
            acquisition_block<=arm_first_block;active<=1;owner_fault<=0;
            occupancy<=0;head<=0;tail<=0;
        end else if(active && bad_offer)begin
            // Previously offered good head may be accepted on this edge;
            // all remaining queued/provisional entries are then invalidated.
            owner_fault<=1;active<=0;occupancy<=0;head<=0;tail<=0;
        end else if(finish_valid && finish_ready)begin
            active<=0;occupancy<=0;head<=0;tail<=0;
        end else if(active)begin
            if(push)begin
                tail<=!tail;
                if(in_index==6'd63)acquisition_block<=acquisition_block+16'd1;
            end
            if(pop)head<=!head;
            case({push,pop})
                2'b10:occupancy<=occupancy+2'd1;
                2'b01:occupancy<=occupancy-2'd1;
                default:begin end
            endcase
        end
    end
`ifndef SYNTHESIS
    always_ff @(posedge clk)begin
        if(!reset && !kill)begin
            assert(occupancy<=2'd2)else $fatal(1,"dense queue occupancy overflow");
            assert(!out_valid || (active && occupancy!=2'd0 && !owner_fault))
                else $fatal(1,"unowned queue publication");
            if(out_valid)assert(out_frame_epoch==owner_frame && out_child_epoch==owner_child)
                else $fatal(1,"queue head owner mismatch");
        end
    end
    assert property(@(posedge clk) out_valid && !out_ready |=>
        (out_valid && $stable({out_frame_epoch,out_child_epoch,out_block,out_index,out_value})) ||
        reset || kill || owner_fault || !publication_context_ready)
        else $fatal(1,"held dense tuple changed without kill/fault/context fence");
`endif
endmodule
