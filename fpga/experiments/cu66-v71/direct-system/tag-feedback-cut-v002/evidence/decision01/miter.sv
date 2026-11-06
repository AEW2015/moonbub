module logic_old(input [3:0] fs,input  abort_i,input  write_done,input  write_pending,input  write_error,input  e_error,input [7:0] e_code,input  s_error,input [7:0] s_code,input  dq_valid,input  dq_error,input  idct_valid,input  idct_error,input  recon_valid,input  recon_error,input [31:0] recon_id,input [31:0] tid,input  rows_error,input [7:0] rows_code,input  rows_result_valid,input [255:0] hash_value,input [127:0] wanted_tag,output tag_valid,output reg fail_now,output reg[7:0]fail_code,output reg kill);
localparam[3:0] IDLE=0,RUN_PLANE=3,HASH_WAIT=4,RESULT_HOLD=5,DRAIN=6;
assign tag_valid=fs==RESULT_HOLD&&!kill&&!fail_now;
    always_comb begin
        fail_now=0;fail_code=0;
        if(fs!=IDLE&&fs!=DRAIN)begin
            if(write_done&&write_pending&&write_error)begin fail_now=1;fail_code=8'h61;end
            else if(fs==RUN_PLANE&&e_error)begin fail_now=1;fail_code=8'h10|(e_code&8'h0f);end
            else if(s_error)begin fail_now=1;fail_code=8'h20|(s_code&8'h0f);end
            else if(dq_valid&&dq_error)begin fail_now=1;fail_code=8'h31;end
            else if(idct_valid&&idct_error)begin fail_now=1;fail_code=8'h32;end
            else if(recon_valid&&(recon_error||recon_id!=tid))begin fail_now=1;fail_code=8'h33;end
            else if(rows_error)begin fail_now=1;fail_code=8'h40|(rows_code&8'h0f);end
            else if(fs==HASH_WAIT&&rows_result_valid&&hash_value[255:128]!=wanted_tag)
                begin fail_now=1;fail_code=8'h50;end
        end
        kill=abort_i||fs==DRAIN;
    end

endmodule
module logic_new(input [3:0] fs,input  abort_i,input  write_done,input  write_pending,input  write_error,input  e_error,input [7:0] e_code,input  s_error,input [7:0] s_code,input  dq_valid,input  dq_error,input  idct_valid,input  idct_error,input  recon_valid,input  recon_error,input [31:0] recon_id,input [31:0] tid,input  rows_error,input [7:0] rows_code,input  rows_result_valid,input [255:0] hash_value,input [127:0] wanted_tag,output tag_valid,output reg fail_now,output reg[7:0]fail_code,output reg kill);
localparam[3:0] IDLE=0,RUN_PLANE=3,HASH_WAIT=4,RESULT_HOLD=5,DRAIN=6;
reg fail_without_tag;
assign tag_valid=fs==RESULT_HOLD&&!kill&&!fail_without_tag;
    always_comb begin
        fail_now=0;fail_code=0;fail_without_tag=0;
        if(fs!=IDLE&&fs!=DRAIN)begin
            if(write_done&&write_pending&&write_error)begin fail_now=1;fail_without_tag=1;fail_code=8'h61;end
            else if(fs==RUN_PLANE&&e_error)begin fail_now=1;fail_without_tag=1;fail_code=8'h10|(e_code&8'h0f);end
            else if(s_error)begin fail_now=1;fail_without_tag=1;fail_code=8'h20|(s_code&8'h0f);end
            else if(dq_valid&&dq_error)begin fail_now=1;fail_without_tag=1;fail_code=8'h31;end
            else if(idct_valid&&idct_error)begin fail_now=1;fail_without_tag=1;fail_code=8'h32;end
            else if(recon_valid&&(recon_error||recon_id!=tid))begin fail_now=1;fail_without_tag=1;fail_code=8'h33;end
            else if(rows_error)begin fail_now=1;fail_without_tag=1;fail_code=8'h40|(rows_code&8'h0f);end
            else if(fs==HASH_WAIT&&rows_result_valid&&hash_value[255:128]!=wanted_tag)
                begin fail_now=1;fail_code=8'h50;end
        end
        kill=abort_i||fs==DRAIN;
    end

endmodule
module tagcut_miter(input [3:0] fs,input  abort_i,input  write_done,input  write_pending,input  write_error,input  e_error,input [7:0] e_code,input  s_error,input [7:0] s_code,input  dq_valid,input  dq_error,input  idct_valid,input  idct_error,input  recon_valid,input  recon_error,input [31:0] recon_id,input [31:0] tid,input  rows_error,input [7:0] rows_code,input  rows_result_valid,input [255:0] hash_value,input [127:0] wanted_tag,output same);
wire old_tag,new_tag,old_fail,new_fail,old_kill,new_kill;wire[7:0]old_code,new_code;
logic_old old_logic(.fs(fs),.abort_i(abort_i),.write_done(write_done),.write_pending(write_pending),.write_error(write_error),.e_error(e_error),.e_code(e_code),.s_error(s_error),.s_code(s_code),.dq_valid(dq_valid),.dq_error(dq_error),.idct_valid(idct_valid),.idct_error(idct_error),.recon_valid(recon_valid),.recon_error(recon_error),.recon_id(recon_id),.tid(tid),.rows_error(rows_error),.rows_code(rows_code),.rows_result_valid(rows_result_valid),.hash_value(hash_value),.wanted_tag(wanted_tag),.tag_valid(old_tag),.fail_now(old_fail),.fail_code(old_code),.kill(old_kill));
logic_new new_logic(.fs(fs),.abort_i(abort_i),.write_done(write_done),.write_pending(write_pending),.write_error(write_error),.e_error(e_error),.e_code(e_code),.s_error(s_error),.s_code(s_code),.dq_valid(dq_valid),.dq_error(dq_error),.idct_valid(idct_valid),.idct_error(idct_error),.recon_valid(recon_valid),.recon_error(recon_error),.recon_id(recon_id),.tid(tid),.rows_error(rows_error),.rows_code(rows_code),.rows_result_valid(rows_result_valid),.hash_value(hash_value),.wanted_tag(wanted_tag),.tag_valid(new_tag),.fail_now(new_fail),.fail_code(new_code),.kill(new_kill));
assign same=(old_tag==new_tag)&&(old_fail==new_fail)&&(old_code==new_code)&&(old_kill==new_kill);
endmodule
