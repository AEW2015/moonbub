module event_new(input logic clk,rst,input logic[7:0]event_code,stage,fatal_code,
 input logic[23:0]last_address,input logic[31:0]event_fid,input logic[63:0]event_generation,clock_count,
 input logic[9:0]diag_address,output logic[31:0]diag_data,event_sequence,event_overwrites);
    logic [255:0] events[0:7];
    // Physical payload writes lag the logical event edge; diagnostic bypass
    // preserves the original immediate ring contents. Payload needs no reset.
    logic [255:0] event_record_pending;
    logic [2:0] event_write_index;
    logic event_pending_valid;
    logic [7:0] event_slot_valid;
    always_ff @(posedge clk)begin
        // No event-derived CE or bulk reset on the computed 256-bit record.
        event_record_pending<={8'd0,last_address,stage,event_code,fatal_code,8'd0,
                event_fid,event_generation[63:32],event_generation[31:0],clock_count[63:32],clock_count[31:0],event_sequence};
        event_write_index<=event_sequence[2:0];
        if(rst)begin
            event_sequence<=0;event_overwrites<=0;
            event_pending_valid<=0;event_slot_valid<=0;
        end else begin
            // Procedural-if X semantics match the original event predicate.
            event_pending_valid<=0;
            if(event_code!=0)begin
                event_pending_valid<=1;
                event_slot_valid[event_sequence[2:0]]<=1;
                event_sequence<=event_sequence+1;
                if(event_sequence>=8)event_overwrites<=event_overwrites+1;
            end
            if(event_pending_valid)events[event_write_index]<=event_record_pending;
        end
    end
always_comb begin
 diag_data=0;
 if(diag_address==10'h058)diag_data=event_sequence;
 else if(diag_address==10'h05c)diag_data=event_overwrites;
 else if(diag_address>=10'h100&&diag_address<10'h200&&diag_address[1:0]==0)
                    begin
                        if(event_pending_valid&&diag_address[7:5]==event_write_index)
                            diag_data=event_record_pending[int'(diag_address[4:2])*32+:32];
                        else if(event_slot_valid[diag_address[7:5]])
                            diag_data=events[diag_address[7:5]][int'(diag_address[4:2])*32+:32];
                    end
end
endmodule
