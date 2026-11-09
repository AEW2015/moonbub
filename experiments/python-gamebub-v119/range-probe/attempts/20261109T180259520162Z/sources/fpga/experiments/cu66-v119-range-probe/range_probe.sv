// Standalone combinational prototype for the signed16 range predicate.
// This is not production RTL and has no clock or surrounding qualifiers.
module range_probe (
    input  logic [15:0] raw,
    output logic        in_range
);
    always_comb begin
        in_range = (raw[15:11] == 5'b00000)
                || (raw[15:11] == 5'b11111)
                || (raw == 16'h0800);
    end
endmodule
