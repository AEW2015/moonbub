module cu66_mode_store_v107 (
    input wire clk,write_enable,input wire [12:0] write_address,input wire [1:0] write_data,
    input wire read_enable,input wire [12:0] read_address,output reg [1:0] q
);
    (* ram_style="block" *) reg [1:0] words [0:8099];
    // Parser writes and FINISHED reads are mutually exclusive in the caller.
    // Preserve the last registered lookup value across every parser write.
    always @(posedge clk)begin
        if(write_enable)words[write_address]<=write_data;
        else if(read_enable)q<=words[read_address];
    end
endmodule
