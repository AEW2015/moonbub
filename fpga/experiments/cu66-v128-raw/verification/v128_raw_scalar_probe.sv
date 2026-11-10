module v128_raw_scalar_probe (
    input logic coef_select_raw,
    input logic [31:0] coef_raw_epoch,
    input logic [15:0] coef_raw_block,
    input logic [5:0] coef_raw_index,
    input logic signed [15:0] coef_raw_value,
    input logic [1:0] coef_raw_band,
    input logic [31:0] coef_context_epoch,
    input logic [15:0] coef_context_block,
    input logic [5:0] coef_context_index,
    input logic signed [15:0] coef_context_value,
    input logic [1:0] coef_context_band,
    input logic  raw_mode,
    input logic [31:0] active_epoch,
    input logic [16:0] blocks,
    input logic [31:0] written,
    input logic [31:0] previous_position,
    input logic  previous_valid,
    input logic [63:0] rank_threshold_mask,
    input logic [2:0] phase,
    input logic [31:0] counts [0:3],
    output logic [7:0] reference_phase_bad,
    output logic [7:0] candidate_phase_bad,
    output logic [7:0] literal_phase_bad,
    output logic  reference_epoch_bad,
    output logic  candidate_epoch_bad,
    output logic  reference_selected_bad,
    output logic  candidate_selected_bad,
    output logic  block_limit_high
);
    function automatic logic [5:0] zigzag(input logic [5:0] raster);
        integer rank;
        integer sum;
        integer row;
        begin
            rank=0; zigzag=0;
            for(integer diagonal=0;diagonal<15;diagonal=diagonal+1)
                for(integer step=0;step<8;step=step+1) begin
                    row=(diagonal%2==1) ? step : 7-step;
                    sum=diagonal-row;
                    if(sum>=0 && sum<8) begin
                        if(row*8+sum==integer'(raster)) zigzag=6'(rank);
                        rank=rank+1;
                    end
                end
        end
    endfunction
    function automatic logic band_matches(input logic [1:0] band, input logic [5:0] index);
        logic [5:0] z;
        begin
            z=zigzag(index);
            case(band)
                1: band_matches=z>=1 && z<6;
                2: band_matches=z>=6 && z<21;
                3: band_matches=z>=21;
                default: band_matches=index==0;
            endcase
        end
    endfunction
    logic [31:0] coef_epoch;
    assign coef_epoch=coef_select_raw ? coef_raw_epoch : coef_context_epoch;
    logic [15:0] coef_block;
    assign coef_block=coef_select_raw ? coef_raw_block : coef_context_block;
    logic [5:0] coef_index;
    assign coef_index=coef_select_raw ? coef_raw_index : coef_context_index;
    logic signed [15:0] coef_value;
    assign coef_value=coef_select_raw ? coef_raw_value : coef_context_value;
    logic [1:0] coef_band;
    assign coef_band=coef_select_raw ? coef_raw_band : coef_context_band;
    wire [5:0] input_zigzag=zigzag(coef_index);
    logic [31:0] input_raster_position;
    logic input_raster_bad,input_dc_bad,input_ac_bad,input_sparse_order_bad;
    assign input_sparse_order_bad=(previous_position[31:22]!=0) ||
        (coef_block<previous_position[21:6]) ||
        ((coef_block==previous_position[21:6]) && rank_threshold_mask[coef_index]);
    assign input_raster_position={10'd0,coef_block,coef_index};
    assign input_raster_bad=input_raster_position!=written;
    assign input_dc_bad=coef_index!=0 || 32'(coef_block)!=written;
    assign input_ac_bad=!band_matches(coef_band,coef_index) || coef_value==0 ||
        (previous_valid && input_sparse_order_bad);
    // V128_RAW_VALIDATION_BEGIN: compare full direct tuples before ingress
    // mode selects Boolean decisions. Stored scratch raw_mode remains a
    // separate format selector, including invalid/unready/transitional views.
    logic [1:0] ingress_epoch_bad;
    logic [7:0] ingress_phase_bad [0:1];
    logic input_epoch_bad;
    for(genvar validation_lane=0;validation_lane<2;validation_lane=validation_lane+1)begin: ingress_validation
        wire [31:0] lane_epoch=validation_lane==0 ? coef_raw_epoch : coef_context_epoch;
        wire [15:0] lane_block=validation_lane==0 ? coef_raw_block : coef_context_block;
        wire [5:0] lane_index=validation_lane==0 ? coef_raw_index : coef_context_index;
        wire signed [15:0] lane_value=validation_lane==0 ? coef_raw_value : coef_context_value;
        wire [1:0] lane_band=validation_lane==0 ? coef_raw_band : coef_context_band;
        wire [31:0] lane_raster_position={10'd0,lane_block,lane_index};
        wire lane_raster_bad=lane_raster_position!=written;
        wire lane_dc_bad=lane_index!=0 || 32'(lane_block)!=written;
        // Preserve the implemented full32 high/block + arbitrary64 rank-mask
        // contract. Literal-position equivalence needs its original owner.
        wire lane_sparse_order_bad=(previous_position[31:22]!=0) ||
            (lane_block<previous_position[21:6]) ||
            ((lane_block==previous_position[21:6]) && rank_threshold_mask[lane_index]);
        wire lane_ac_bad=!band_matches(lane_band,lane_index) || lane_value==0 ||
            (previous_valid && lane_sparse_order_bad);
        assign ingress_epoch_bad[validation_lane]=lane_epoch!=active_epoch;
        for(genvar lane_phase=0;lane_phase<8;lane_phase=lane_phase+1)begin: phase_lane
            assign ingress_phase_bad[validation_lane][lane_phase]=
                ingress_epoch_bad[validation_lane] || lane_band!=2'(lane_phase) ||
                lane_block>=16'(blocks) || lane_value < -2048 || lane_value > 2048 ||
                written>=counts[lane_phase & 3] ||
                (raw_mode ? lane_raster_bad : lane_phase==0 ? lane_dc_bad : lane_ac_bad);
        end
    end
    assign input_epoch_bad=coef_select_raw ? ingress_epoch_bad[0] : ingress_epoch_bad[1];
    // V128_RAW_VALIDATION_END
    for(genvar checking_phase=0;checking_phase<8;checking_phase=checking_phase+1)begin: phase_validation
        wire [31:0] phase_position=raw_mode ? (32'(coef_block)*64+32'(coef_index)) :
            (checking_phase==0 ? 32'(coef_block) : (32'(coef_block)*64+32'(input_zigzag)));
        assign reference_phase_bad[checking_phase]=coef_epoch!=active_epoch || coef_band!=2'(checking_phase) ||
            coef_block>=16'(blocks) || coef_value < -2048 || coef_value > 2048 ||
            written>=counts[checking_phase & 3] ||
            (raw_mode ? input_raster_bad : checking_phase==0 ? input_dc_bad : input_ac_bad);
        assign literal_phase_bad[checking_phase]=(coef_epoch!=active_epoch || coef_band!=2'(checking_phase) ||
                coef_block>=16'(blocks) || coef_value < -2048 || coef_value > 2048 ||
                written>=counts[checking_phase & 3] ||
                (raw_mode ? phase_position!=written : checking_phase==0 ?
                 (coef_index!=0 || 32'(coef_block)!=written) :
                 (!band_matches(coef_band,coef_index) || coef_value==0 ||
                  (previous_valid && phase_position<=previous_position))));
    end
    for(genvar checking_phase=0;checking_phase<8;checking_phase=checking_phase+1)begin: selected_lane
        assign candidate_phase_bad[checking_phase]=coef_select_raw ?
            ingress_phase_bad[0][checking_phase] : ingress_phase_bad[1][checking_phase];
    end
    assign block_limit_high=blocks[16];
    assign reference_epoch_bad=coef_epoch!=active_epoch;
    assign candidate_epoch_bad=input_epoch_bad;
    assign reference_selected_bad=reference_phase_bad[phase];
    assign candidate_selected_bad=candidate_phase_bad[phase];
endmodule
