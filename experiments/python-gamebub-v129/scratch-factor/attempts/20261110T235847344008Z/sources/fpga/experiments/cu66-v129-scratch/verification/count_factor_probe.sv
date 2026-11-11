module count_factor_probe (
    input logic [31:0] written,
    input logic [31:0] counts [0:3],
    input logic [2:0] phase,
    output logic old_equal, new_equal
);
    // V129: evaluate each full-width count comparison before phase selection.
    // No stored payload, reset, enable, interface, or cycle is added.
    wire [3:0] band_count_matches;
    for(genvar count_lane=0;count_lane<4;count_lane=count_lane+1)begin: band_count_lanes
        assign band_count_matches[count_lane]=written==counts[count_lane];
    end
    wire selected_band_count_match=band_count_matches[phase[1:0]];
    assign old_equal=written==counts[phase[1:0]];
    assign new_equal=selected_band_count_match;
endmodule
