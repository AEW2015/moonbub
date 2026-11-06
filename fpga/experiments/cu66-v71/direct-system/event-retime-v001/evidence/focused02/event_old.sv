module event_old(input logic clk,rst,input logic[7:0]event_code,stage,fatal_code,
 input logic[23:0]last_address,input logic[31:0]event_fid,input logic[63:0]event_generation,clock_count,
 input logic[9:0]diag_address,output logic[31:0]diag_data,event_sequence,event_overwrites);
    logic [255:0] events[0:7];
    always_ff @(posedge clk)begin
        if(rst)begin
            event_sequence<=0;event_overwrites<=0;
            for(integer i=0;i<8;i=i+1)events[i]<=0;
        end else if(event_code!=0)begin
            events[event_sequence[2:0]]<={8'd0,last_address,stage,event_code,fatal_code,8'd0,
                event_fid,event_generation[63:32],event_generation[31:0],clock_count[63:32],clock_count[31:0],event_sequence};
            event_sequence<=event_sequence+1;
            if(event_sequence>=8)event_overwrites<=event_overwrites+1;
        end
    end
always_comb begin
 diag_data=0;
 if(diag_address==10'h058)diag_data=event_sequence;
 else if(diag_address==10'h05c)diag_data=event_overwrites;
 else if(diag_address>=10'h100&&diag_address<10'h200&&diag_address[1:0]==0)
                    diag_data=events[diag_address[7:5]][int'(diag_address[4:2])*32+:32];
end
endmodule
