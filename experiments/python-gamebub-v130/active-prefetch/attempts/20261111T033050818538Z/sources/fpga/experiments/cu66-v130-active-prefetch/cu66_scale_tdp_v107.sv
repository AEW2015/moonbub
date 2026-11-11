module cu66_scale_tdp_v107 (
    input wire clk,input wire a_write,input wire [10:0] a_addr,input wire [1:0] a_data,
    input wire b_write,b_read,input wire [10:0] b_addr,input wire [1:0] b_data,
    output reg [1:0] b_q
);
    (* ram_style="block" *) reg [1:0] words [0:1349];
    // Suppress only same-address simultaneous A writes: original Q_FILL wins.
    wire a_commit=a_write && !(b_write && a_addr==b_addr);
    always @(posedge clk)if(a_commit) words[a_addr]<=a_data;
    // A B-write must hold the previous lookup output (NO_CHANGE semantics).
    always @(posedge clk)begin
        if(b_write) words[b_addr]<=b_data;
        else if(b_read) b_q<=words[b_addr];
    end
endmodule
