`timescale 1ns/1ps
`default_nettype none
module v107_reset_release (
    input wire clk, input wire async_reset, output wire reset
);
    (* ASYNC_REG="TRUE" *) reg [2:0] release_pipe = 3'b111;
    always @(posedge clk or posedge async_reset)
        if (async_reset) release_pipe <= 3'b111;
        else release_pipe <= {release_pipe[1:0],1'b0};
    assign reset = release_pipe[2];
endmodule
`default_nettype wire
