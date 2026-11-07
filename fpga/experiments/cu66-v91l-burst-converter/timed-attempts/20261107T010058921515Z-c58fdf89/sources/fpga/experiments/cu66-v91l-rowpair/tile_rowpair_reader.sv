`timescale 1ns/1ps
`default_nettype none
// Sequential per-plane 16-byte consumer, one accepted physical BL8 owner.
// 180x64-bit row fragments +128-bit scratch+128-bit response =1472 data bytes.
module tile_rowpair_reader #(parameter bit RETAIN_ROWS=1)(
 input logic clk,power_on_reset,reset,cancel,
 input logic start,output logic start_ready,input logic [1:0] start_bank,
 input logic [31:0] start_epoch,start_generation,
 input logic finish,output logic active,busy,output logic [3:0] session_error,
 input logic req_valid,output logic req_ready,
 input logic [18:0] req_addr,input logic [1:0] req_bank,
 input logic [31:0] req_epoch,req_generation,req_token,
 output logic rsp_valid,input logic rsp_ready,output logic [127:0] rsp_data,
 output logic [18:0] rsp_addr,output logic [1:0] rsp_bank,
 output logic [31:0] rsp_epoch,rsp_generation,rsp_token,output logic [3:0] rsp_error,
 output logic mem_req_valid,input logic mem_req_ready,output logic [18:0] mem_req_addr,
 output logic [1:0] mem_req_bank,output logic [31:0] mem_req_epoch,mem_req_generation,
 input logic mem_rsp_valid,output logic mem_rsp_ready,input logic [127:0] mem_rsp_data,
 input logic [18:0] mem_rsp_addr,input logic [1:0] mem_rsp_bank,
 input logic [31:0] mem_rsp_epoch,mem_rsp_generation,input logic mem_rsp_error,
 output logic physical_pending,output logic [2:0] state,
 output logic [31:0] count_requests,count_responses,count_errors,
 output logic [31:0] count_physical_requests,count_physical_responses,
 output logic [31:0] count_row_hits,count_scratch_hits,
 output logic [7:0] valid_fragments
);
 localparam logic [2:0] IDLE=0,LOOKUP=1,OFFER=2,WAIT_BURST=3,RESPONSE=4;
 localparam logic [3:0] E_NONE=0,E_RANGE=1,E_ORDER=2,E_LEASE=3,E_CANCEL=4,E_MEMORY=5;
 logic [1:0] bank;
 logic [31:0] epoch,generation;
 logic [18:0] next_addr[0:2];
 logic [63:0] row_data[0:179];
 logic [89:0] valid_y;
 logic [44:0] valid_cb,valid_cr;
 logic [8:0] row_tag[0:2];
 logic [127:0] scratch;
 logic [18:0] scratch_addr,burst_addr;
 logic scratch_valid,pending,canceled,half;
 logic initialized=0;
 logic [18:0] logical_addr,plane_base,local_addr,physical_addr;
 logic [9:0] width,x;
 logic [8:0] y;
 logic [1:0] plane;
 logic [7:0] fragment;
 logic [6:0] column_fragment;
 logic fragment_valid,row_hit,scratch_hit,matching_response;
 integer nvalid;

 always_comb begin
  logical_addr=rsp_addr+(half?19'd8:19'd0);
  plane=logical_addr<345600?2'd0:logical_addr<432000?2'd1:2'd2;
  plane_base=plane==0?19'd0:plane==1?19'd345600:19'd432000;
  width=plane==0?10'd720:10'd360;
  local_addr=logical_addr-plane_base;
  if(plane==0)begin y=9'(local_addr/19'd720);x=10'(local_addr%19'd720);end
  else begin y=9'(local_addr/19'd360);x=10'(local_addr%19'd360);end
  physical_addr=plane_base+19'(((32'(y)>>3)*(32'(width)>>3)+(32'(x)>>3))*64+((32'(y)&7)*8)+(32'(x)&7));
  column_fragment=7'(x>>3);
  fragment=8'((plane==0?0:plane==1?90:135)+32'(column_fragment));
  case(plane)
   0:fragment_valid=valid_y[column_fragment];
   1:fragment_valid=valid_cb[column_fragment[5:0]];
   default:fragment_valid=valid_cr[column_fragment[5:0]];
  endcase
  row_hit=RETAIN_ROWS&&row_tag[plane]==y&&fragment_valid;
  scratch_hit=scratch_valid&&scratch_addr=={physical_addr[18:4],4'b0};
  nvalid=$countones(valid_y)+$countones(valid_cb)+$countones(valid_cr);
  valid_fragments=8'(nvalid);
 end
 assign busy=active||state!=IDLE||pending;
 assign start_ready=!active&&state==IDLE&&!pending&&!reset&&!cancel&&!power_on_reset;
 assign req_ready=active&&state==IDLE&&!pending&&!finish&&!reset&&!cancel&&!power_on_reset;
 assign rsp_valid=state==RESPONSE&&!power_on_reset;
 assign mem_req_valid=state==OFFER&&active&&!canceled&&!pending&&!reset&&!cancel&&!power_on_reset;
 assign mem_req_addr=burst_addr;
 assign mem_req_bank=bank;
 assign mem_req_epoch=epoch;
 assign mem_req_generation=generation;
 assign matching_response=mem_rsp_bank==bank&&mem_rsp_epoch==epoch&&mem_rsp_generation==generation&&mem_rsp_addr==burst_addr;
 assign mem_rsp_ready=pending&&matching_response&&!power_on_reset;
 assign physical_pending=pending;

 always_ff @(posedge clk)begin
  initialized<=1;
  if(power_on_reset)begin
   active<=0;state<=IDLE;bank<=0;epoch<=0;generation<=0;session_error<=0;
   valid_y<=0;valid_cb<=0;valid_cr<=0;
   for(integer i=0;i<3;i=i+1)begin row_tag[i]<=0;next_addr[i]<=0;end
   scratch<=0;scratch_addr<=0;scratch_valid<=0;burst_addr<=0;pending<=0;canceled<=0;half<=0;
   rsp_data<=0;rsp_addr<=0;rsp_bank<=0;rsp_epoch<=0;rsp_generation<=0;rsp_token<=0;rsp_error<=0;
   count_requests<=0;count_responses<=0;count_errors<=0;count_physical_requests<=0;count_physical_responses<=0;
   count_row_hits<=0;count_scratch_hits<=0;
  end else if(reset||cancel)begin
   // Warm kill invalidates cache but retains every accepted burst until its tagged return.
   active<=0;valid_y<=0;valid_cb<=0;valid_cr<=0;scratch_valid<=0;
   session_error<=E_CANCEL;canceled<=1;
   if(state==RESPONSE)begin
    // An already offered response is immutable, including its success/error value.
    if(rsp_ready)begin state<=IDLE;count_responses<=count_responses+1;end
   end else if(pending)begin
    state<=WAIT_BURST;
    if(mem_rsp_valid&&mem_rsp_ready)begin
     pending<=0;count_physical_responses<=count_physical_responses+1;
     rsp_data<=0;rsp_error<=E_CANCEL;state<=RESPONSE;count_errors<=count_errors+1;
    end
   end else if(state!=IDLE)begin
    rsp_data<=0;rsp_error<=E_CANCEL;state<=RESPONSE;count_errors<=count_errors+1;
   end
  end else begin
   if(start&&start_ready)begin
    bank<=start_bank;epoch<=start_epoch;generation<=start_generation;
    active<=start_bank<3&&start_epoch!=0&&start_generation!=0;
    session_error<=start_bank<3&&start_epoch!=0&&start_generation!=0?E_NONE:E_LEASE;
    valid_y<=0;valid_cb<=0;valid_cr<=0;scratch_valid<=0;canceled<=0;
    next_addr[0]<=0;next_addr[1]<=345600;next_addr[2]<=432000;
   end else if(finish&&state==IDLE&&!pending)begin
    active<=0;valid_y<=0;valid_cb<=0;valid_cr<=0;scratch_valid<=0;
   end
   case(state)
    IDLE:if(req_valid&&req_ready)begin
     rsp_addr<=req_addr;rsp_bank<=req_bank;rsp_epoch<=req_epoch;rsp_generation<=req_generation;rsp_token<=req_token;
     rsp_data<=0;rsp_error<=E_NONE;half<=0;canceled<=0;count_requests<=count_requests+1;
     if(!RETAIN_ROWS)scratch_valid<=0;
     if(req_addr>=518400||req_addr[3:0]!=0)begin
      rsp_error<=E_RANGE;session_error<=E_RANGE;state<=RESPONSE;active<=0;
      valid_y<=0;valid_cb<=0;valid_cr<=0;scratch_valid<=0;count_errors<=count_errors+1;
     end else if(req_bank!=bank||req_epoch!=epoch||req_generation!=generation)begin
      rsp_error<=E_LEASE;session_error<=E_LEASE;state<=RESPONSE;active<=0;
      valid_y<=0;valid_cb<=0;valid_cr<=0;scratch_valid<=0;count_errors<=count_errors+1;
     end else if(req_addr!=next_addr[req_addr<345600?0:req_addr<432000?1:2])begin
      rsp_error<=E_ORDER;session_error<=E_ORDER;state<=RESPONSE;active<=0;
      valid_y<=0;valid_cb<=0;valid_cr<=0;scratch_valid<=0;count_errors<=count_errors+1;
     end else begin
      next_addr[req_addr<345600?0:req_addr<432000?1:2]<=req_addr+19'd16;
      state<=LOOKUP;
     end
    end
    LOOKUP:begin
     if(row_hit)begin
      rsp_data[(half?64:0)+:64]<=row_data[fragment];count_row_hits<=count_row_hits+1;
      if(half)state<=RESPONSE;else half<=1;
     end else if(scratch_hit)begin
      rsp_data[(half?64:0)+:64]<=scratch[(physical_addr[3]?64:0)+:64];
      count_scratch_hits<=count_scratch_hits+1;
      if(half)state<=RESPONSE;else half<=1;
     end else begin burst_addr<={physical_addr[18:4],4'b0};state<=OFFER;end
    end
    OFFER:if(mem_req_valid&&mem_req_ready)begin
     pending<=1;state<=WAIT_BURST;count_physical_requests<=count_physical_requests+1;
    end
    WAIT_BURST:if(mem_rsp_valid&&mem_rsp_ready)begin
     pending<=0;count_physical_responses<=count_physical_responses+1;
     if(canceled||mem_rsp_error)begin
      rsp_data<=0;rsp_error<=canceled?E_CANCEL:E_MEMORY;session_error<=canceled?E_CANCEL:E_MEMORY;
      state<=RESPONSE;active<=0;valid_y<=0;valid_cb<=0;valid_cr<=0;scratch_valid<=0;
      count_errors<=count_errors+1;
     end else begin
      scratch<=mem_rsp_data;scratch_addr<=burst_addr;scratch_valid<=1;state<=LOOKUP;
      if(RETAIN_ROWS&&!y[0])begin
       row_data[fragment]<=mem_rsp_data[127:64];
       case(plane)
        0:begin
         if(row_tag[0]!=y+1'b1)valid_y<=90'b1<<column_fragment;else valid_y[column_fragment]<=1;
        end
        1:begin
         if(row_tag[1]!=y+1'b1)valid_cb<=45'b1<<column_fragment;else valid_cb[column_fragment[5:0]]<=1;
        end
        default:begin
         if(row_tag[2]!=y+1'b1)valid_cr<=45'b1<<column_fragment;else valid_cr[column_fragment[5:0]]<=1;
        end
       endcase
       row_tag[plane]<=y+1'b1;
      end
     end
    end
    RESPONSE:if(rsp_valid&&rsp_ready)begin state<=IDLE;count_responses<=count_responses+1;end
    default:state<=IDLE;
   endcase
  end
 end
 always_ff @(posedge clk)begin
  if(power_on_reset&&initialized)assert(!pending)else $fatal(1,"cold reset during accepted physical read");
  if(!power_on_reset)begin
   assert(state<=RESPONSE);
   assert(count_physical_requests>=count_physical_responses);
   assert(count_physical_requests-count_physical_responses<=1);
   assert(pending==(count_physical_requests!=count_physical_responses));
   assert(nvalid>=0&&nvalid<=180);
   if(mem_req_valid)assert(!pending&&burst_addr[3:0]==0&&burst_addr<518400);
   if(rsp_valid)assert(!pending);
   if(state==LOOKUP||state==WAIT_BURST)assert(fragment<180&&column_fragment<(plane==0?90:45)&&physical_addr[2:0]==0);
  end
 end
endmodule
`default_nettype wire
