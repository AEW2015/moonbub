module cast_probe(input logic signed [7:0] a, input logic [39:0] b, output logic signed [31:0] x,y); assign x=$signed(32'(a)); assign y=$signed(32'(b)); endmodule
