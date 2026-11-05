// AR03 outer-envelope certificate only. Not inner decode, AF03 or publication.
module ar03_envelope #(
 parameter integer MAX_BYTES=49152
)(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,
 input wire [63:0] start_owner,input wire [31:0] start_bytes,
 input wire start_check_epoch,input wire [31:0] start_expected_epoch,
 input wire in_valid,output wire in_ready,input wire [7:0] in_data,input wire in_last,
 output wire envelope_validated,input wire envelope_ready,
 output wire [63:0] desc_owner,output wire [31:0] desc_epoch,desc_frame,
 output wire [31:0] desc_expected_epoch,output wire desc_epoch_checked,
 output wire [7:0] desc_flags,desc_reference_bank,desc_destination_bank,
 output wire [31:0] desc_reference_id,desc_inner_bytes,desc_patch_bytes,
 output wire [127:0] desc_reference_tag,desc_stored_tag,
 output wire [2:0] desc_patch_count,output wire [31:0] desc_patch_blob_offset,
 output wire [127:0] desc_patch_offsets,desc_patch_lengths,
 output wire error_valid,input wire error_ready,output reg [3:0] error_code,
 input wire rd_req_valid,output wire rd_req_ready,input wire [31:0] rd_req_address,
 input wire [63:0] rd_req_owner,input wire [31:0] rd_req_epoch,
 output wire rd_rsp_valid,input wire rd_rsp_ready,output reg [7:0] rd_rsp_data,
 output reg rd_rsp_error,output reg [63:0] rd_rsp_owner,output reg [31:0] rd_rsp_epoch,
 input wire retire_valid,output wire retire_ready,
 input wire [63:0] retire_owner,input wire [31:0] retire_epoch
);
 initial begin if(MAX_BYTES<115)$fatal(1,"MAX_BYTES must store the minimum115-byte envelope");end
 localparam IDLE=0,LOAD=1,CHECK=2,CERTIFICATE=3,REPLAY=4,ERROR=5;
 reg [2:0] state;
 (* ram_style="block" *) reg [7:0] memory[0:MAX_BYTES-1];
 reg [7:0] ram_q;
 reg [63:0] owner;
 reg [31:0] total,expected_epoch;
 reg check_epoch;
 reg [31:0] cursor,crc_state,trailer,magic,epoch,frame,reference_id,inner_bytes,patch_bytes;
 reg [7:0] version,flags,reference_bank,destination_bank,patch_count;
 reg [127:0] reference_tag,stored_tag;
 reg [31:0] inner_magic,inner_epoch,inner_frame,inner_reference;
 reg [7:0] inner_version,inner_flags;
 reg [31:0] patch_offset[0:3],patch_length[0:3];
 reg [2:0] completed_patches;
 reg [1:0] prefix_index;
 reg [31:0] prefix_value,remaining_patch;
 reg patch_error;
 reg read_pending,pending_error,response_valid;
 reg [63:0] pending_owner;
 reg [31:0] pending_epoch;
 integer i;
 // Normal retirement drains already accepted reads; abort is explicit cancel.
 wire retire_requested=state==REPLAY&&retire_valid&&retire_owner==owner&&retire_epoch==epoch;
 wire retire_match=retire_requested&&!read_pending&&!response_valid;
 wire [33:0] blob_start=34'd61+{2'b0,inner_bytes};
 wire [33:0] blob_end=blob_start+{2'b0,patch_bytes};
 wire [33:0] length_sum=34'd65+{2'b0,inner_bytes}+{2'b0,patch_bytes};
 wire [31:0] prefix_complete={in_data,prefix_value[23:0]};
 wire rd_identity=rd_req_owner==owner&&rd_req_epoch==epoch&&rd_req_address<total;
 assign start_ready=state==IDLE&&!reset&&!abort;
 assign in_ready=state==LOAD&&!reset&&!abort;
 assign envelope_validated=state==CERTIFICATE&&!reset&&!abort;
 assign error_valid=state==ERROR&&!reset&&!abort;
 assign desc_owner=owner;assign desc_epoch=epoch;assign desc_frame=frame;
 assign desc_expected_epoch=expected_epoch;assign desc_epoch_checked=check_epoch;
 assign desc_flags=flags;assign desc_reference_bank=reference_bank;assign desc_destination_bank=destination_bank;
 assign desc_reference_id=reference_id;assign desc_reference_tag=reference_tag;assign desc_stored_tag=stored_tag;
 assign desc_inner_bytes=inner_bytes;assign desc_patch_bytes=patch_bytes;assign desc_patch_count=patch_count[2:0];
 assign desc_patch_blob_offset=61+inner_bytes;
 generate genvar g;for(g=0;g<4;g=g+1)begin
  assign desc_patch_offsets[g*32+:32]=patch_offset[g];
  assign desc_patch_lengths[g*32+:32]=patch_length[g];
 end endgenerate
 assign rd_req_ready=state==REPLAY&&!read_pending&&(!response_valid||rd_rsp_ready)&&!reset&&!abort&&!retire_requested;
 assign rd_rsp_valid=state==REPLAY&&response_valid&&!reset&&!abort&&!retire_match;
 assign retire_ready=state==REPLAY&&retire_owner==owner&&retire_epoch==epoch&&!read_pending&&!response_valid&&!reset&&!abort;
 function automatic [31:0] crc_byte(input[31:0] old,input[7:0] value);
 reg[31:0] c;integer b;
 begin c=old^{24'b0,value};for(b=0;b<8;b=b+1)c=(c>>1)^((c[0])?32'hedb88320:0);crc_byte=c;end endfunction
 wire outer_header_ok=magic==32'h33305241&&version==3&&(flags==0||flags==1||flags==2)&&epoch!=32'hffffffff&&frame!=32'hffffffff&&(!check_epoch||epoch==expected_epoch)&&patch_count<=4;
 wire reference_profile_ok=(flags==1)?(reference_bank==255&&reference_id==32'hffffffff&&reference_tag==0&&destination_bank==0&&stored_tag!=0):
  ((reference_bank==0||reference_bank==1)&&reference_id<frame&&reference_tag!=0&&((flags==2)?(destination_bank==1&&stored_tag!=0):(destination_bank==255&&stored_tag==0)));
 wire inner_is_sr=inner_magic==32'h31305253;
 wire minimal_inner_ok=(inner_magic==32'h31304d47||inner_is_sr)&&inner_version==1&&inner_epoch==epoch&&inner_frame==frame&&inner_reference==reference_id&&inner_flags[0]==(flags==1)&&
  ((inner_is_sr)?(inner_flags==0||inner_flags==1||inner_flags==2||inner_flags==4):(inner_flags==0||inner_flags==1));
 // Byte RAM has synchronous writes and synchronous replay reads. It is never
 // cleared on abort; identity/valid/bounds gates invalidate all old contents.
 always @(posedge clk)begin
  if(!reset&&!abort)begin
   if(in_ready&&in_valid)memory[cursor]<=in_data;
   if(rd_req_ready&&rd_req_valid&&rd_identity)ram_q<=memory[rd_req_address];
  end
 end
 always @(posedge clk)begin
  if(reset||abort)begin
   state<=IDLE;owner<=0;read_pending<=0;response_valid<=0;error_code<=0;
   rd_rsp_data<=0;rd_rsp_error<=0;rd_rsp_owner<=0;rd_rsp_epoch<=0;
  end else begin
   if(rd_rsp_valid&&rd_rsp_ready)response_valid<=0;
   if(read_pending)begin
    rd_rsp_data<=pending_error?0:ram_q;rd_rsp_error<=pending_error;rd_rsp_owner<=pending_owner;rd_rsp_epoch<=pending_epoch;
    response_valid<=1;read_pending<=0;
   end
   if(rd_req_ready&&rd_req_valid)begin
    read_pending<=1;pending_error<=!rd_identity;pending_owner<=rd_req_owner;pending_epoch<=rd_req_epoch;
   end
   case(state)
    IDLE:if(start_valid)begin
     owner<=start_owner;total<=start_bytes;expected_epoch<=start_expected_epoch;check_epoch<=start_check_epoch;
     cursor<=0;crc_state<=32'hffffffff;trailer<=0;magic<=0;epoch<=0;frame<=0;reference_id<=0;inner_bytes<=0;patch_bytes<=0;
     version<=0;flags<=0;reference_bank<=0;destination_bank<=0;patch_count<=0;reference_tag<=0;stored_tag<=0;
     inner_magic<=0;inner_epoch<=0;inner_frame<=0;inner_reference<=0;inner_version<=0;inner_flags<=0;
     completed_patches<=0;prefix_index<=0;prefix_value<=0;remaining_patch<=0;patch_error<=0;read_pending<=0;response_valid<=0;
     for(i=0;i<4;i=i+1)begin patch_offset[i]<=0;patch_length[i]<=0;end
     if(start_bytes<115||start_bytes>MAX_BYTES||start_bytes>49152)begin error_code<=1;state<=ERROR;end else state<=LOAD;
    end
    LOAD:if(in_valid)begin
     if(cursor<total-4)crc_state<=crc_byte(crc_state,in_data);
     else trailer[(cursor-(total-4))*8+:8]<=in_data;
     if(cursor<4)magic[cursor*8+:8]<=in_data;
     if(cursor==4)version<=in_data;if(cursor==5)flags<=in_data;
     if(cursor>=6&&cursor<10)epoch[(cursor-6)*8+:8]<=in_data;
     if(cursor>=10&&cursor<14)frame[(cursor-10)*8+:8]<=in_data;
     if(cursor==14)reference_bank<=in_data;if(cursor==15)destination_bank<=in_data;
     if(cursor>=16&&cursor<20)reference_id[(cursor-16)*8+:8]<=in_data;
     if(cursor>=20&&cursor<36)reference_tag[(cursor-20)*8+:8]<=in_data;
     if(cursor>=36&&cursor<52)stored_tag[(cursor-36)*8+:8]<=in_data;
     if(cursor>=52&&cursor<56)inner_bytes[(cursor-52)*8+:8]<=in_data;
     if(cursor==56)patch_count<=in_data;
     if(cursor>=57&&cursor<61)patch_bytes[(cursor-57)*8+:8]<=in_data;
     if(cursor>=61&&cursor<65)inner_magic[(cursor-61)*8+:8]<=in_data;
     if(cursor==65)inner_version<=in_data;if(cursor==66)inner_flags<=in_data;
     if(cursor>=67&&cursor<71)inner_epoch[(cursor-67)*8+:8]<=in_data;
     if(cursor>=71&&cursor<75)inner_frame[(cursor-71)*8+:8]<=in_data;
     if(cursor>=75&&cursor<79)inner_reference[(cursor-75)*8+:8]<=in_data;
     if({2'b0,cursor}>=blob_start&&{2'b0,cursor}<blob_end&&cursor<total-4)begin
      if(remaining_patch!=0)begin
       remaining_patch<=remaining_patch-1;
       if(remaining_patch==1)begin if(completed_patches<4)completed_patches<=completed_patches+1'b1;else patch_error<=1;end
      end else begin
       if(completed_patches>=patch_count||completed_patches>=4)patch_error<=1;
       prefix_value[prefix_index*8+:8]<=in_data;
       if(prefix_index==3)begin
        prefix_index<=0;remaining_patch<=prefix_complete;
        if(prefix_complete==0||({2'b0,cursor}+{2'b0,prefix_complete}+1)>blob_end)patch_error<=1;
        if(completed_patches<4)begin patch_offset[completed_patches]<=cursor+1;patch_length[completed_patches]<=prefix_complete;end
       end else prefix_index<=prefix_index+1'b1;
      end
     end
     if(in_last!=(cursor==total-1))begin error_code<=2;state<=ERROR;end
     else if(cursor==total-1)state<=CHECK;
     else cursor<=cursor+1;
    end
    CHECK:begin
     if(!outer_header_ok)begin error_code<=3;state<=ERROR;end
     else if(!reference_profile_ok)begin error_code<=4;state<=ERROR;end
     else if(inner_bytes<50||length_sum!={2'b0,total})begin error_code<=5;state<=ERROR;end
     else if((~crc_state)!=trailer)begin error_code<=6;state<=ERROR;end
     else if(!minimal_inner_ok)begin error_code<=7;state<=ERROR;end
     else if(patch_error||remaining_patch!=0||prefix_index!=0||completed_patches!=patch_count)begin error_code<=8;state<=ERROR;end
     else state<=CERTIFICATE;
    end
    CERTIFICATE:if(envelope_ready)state<=REPLAY;
    REPLAY:if(retire_match)begin state<=IDLE;read_pending<=0;response_valid<=0;end
    ERROR:if(error_ready)begin state<=IDLE;read_pending<=0;response_valid<=0;end
    default:begin state<=IDLE;read_pending<=0;response_valid<=0;end
   endcase
  end
 end
endmodule
