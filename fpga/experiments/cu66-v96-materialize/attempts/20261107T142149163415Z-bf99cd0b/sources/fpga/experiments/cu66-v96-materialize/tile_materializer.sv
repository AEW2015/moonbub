`timescale 1ns/1ps
`default_nettype none
// Standalone bounded materialization. Warm reset is cancellation, never a
// physical reset. The 64B tile is the only sample storage. One request in flight.
module tile_materializer #(parameter integer GEN_LANES=4)(
 input logic clk,power_on_reset,reset,cancel,
 input logic accepted_valid,input logic [1:0] accepted_bank,input logic [63:0] accepted_id,
 input logic [2:0] protected_mask,
 input logic req_valid,output logic req_ready,input logic [1:0] req_mode,
 input logic [31:0] req_epoch,input logic [63:0] req_src_id,req_dst_id,
 input logic [1:0] req_src_bank,req_dst_bank,input logic [18:0] req_src_addr,req_dst_addr,
 input logic literal_valid,output logic literal_ready,input logic [7:0] literal_data,
 output logic rsp_valid,input logic rsp_ready,output logic rsp_error,candidate_valid,
 output logic [31:0] rsp_epoch,output logic [63:0] rsp_src_id,rsp_dst_id,
 output logic busy,physical_pending,output logic [3:0] state,
 output logic [2:0] lease_mask,
 output logic rd_req_valid,input logic rd_req_ready,output logic [31:0] rd_req_epoch,rd_req_generation,
 output logic [1:0] rd_req_bank,output logic [18:0] rd_req_addr,
 input logic rd_rsp_valid,output logic rd_rsp_ready,input logic rd_rsp_error,
 input logic [31:0] rd_rsp_epoch,rd_rsp_generation,input logic [1:0] rd_rsp_bank,
 input logic [18:0] rd_rsp_addr,input logic [127:0] rd_rsp_data,
 output logic wr_req_valid,input logic wr_req_ready,output logic [31:0] wr_req_epoch,wr_req_token,
 output logic [1:0] wr_req_bank,output logic [19:0] wr_req_addr,output logic [63:0] wr_req_data,
 input logic wr_rsp_valid,output logic wr_rsp_ready,input logic wr_rsp_error,
 input logic [31:0] wr_rsp_epoch,wr_rsp_token,input logic [1:0] wr_rsp_bank,input logic [19:0] wr_rsp_addr
);
 localparam logic [3:0] IDLE=0,GENERATE=1,LITERAL=2,READ_OFFER=3,READ_WAIT=4,WRITE_OFFER=5,WRITE_WAIT=6,RESPONSE=7;
 logic [511:0] tile;
 logic [18:0] source_base,destination_base;
 logic [1:0] source_bank,destination_bank,line_index;
 logic [2:0] row_index;
 logic [6:0] sample_index;
 logic canceled,owns_lease,copy_mode;
 logic [31:0] ticket;
 wire kill=reset||cancel;
 wire legal=req_epoch!=0&&req_dst_id!=0&&req_mode<3&&req_dst_bank<3&&
  req_dst_addr[5:0]==0&&req_dst_addr<=19'd518336&&!protected_mask[req_dst_bank]&&
  (!accepted_valid||(req_dst_bank!=accepted_bank&&req_dst_id!=accepted_id))&&
  (req_mode!=0||(accepted_valid&&accepted_bank<3&&accepted_id!=0&&req_src_id==accepted_id&&
   req_src_bank==accepted_bank&&req_src_bank!=req_dst_bank&&req_src_id!=req_dst_id&&
   req_src_addr[5:0]==0&&req_src_addr<=19'd518336));
 wire lease_changed=owns_lease&&(protected_mask[destination_bank]||
  (accepted_valid&&accepted_bank==destination_bank)||
  (copy_mode&&(!accepted_valid||accepted_bank!=source_bank||accepted_id!=rsp_src_id)));
 wire stop=kill||canceled||lease_changed;
 // The retained writer expects canonical raster row addresses and maps to the
 // existing tile-major aperture. Invert only that mapping, without widening it.
 function automatic logic [19:0] raster_row(input logic [18:0] base_addr,input logic [2:0] row);
  integer unsigned plane_base,tile_no,width;
  plane_base=base_addr<345600?0:base_addr<432000?345600:432000;
  width=base_addr<345600?720:360;
  tile_no=(32'(base_addr)-plane_base)/64;
  return 20'(plane_base+((tile_no/(width/8))*8+32'(row))*width+(tile_no%(width/8))*8);
 endfunction
 assign busy=state!=IDLE;
 assign req_ready=state==IDLE&&!kill&&!power_on_reset;
 assign rsp_valid=state==RESPONSE&&!power_on_reset;
 assign lease_mask=owns_lease?((3'b001<<destination_bank)|(copy_mode?(3'b001<<source_bank):3'b000)):3'b000;
 assign literal_ready=state==LITERAL&&!stop&&!power_on_reset;
 assign rd_req_valid=state==READ_OFFER&&!stop&&!power_on_reset;
 assign rd_req_epoch=rsp_epoch;assign rd_req_generation=ticket;assign rd_req_bank=source_bank;
 assign rd_req_addr=source_base+{13'd0,line_index,4'd0};
 assign rd_rsp_ready=state==READ_WAIT&&physical_pending&&!power_on_reset&&
  rd_rsp_epoch==rsp_epoch&&rd_rsp_generation==ticket&&rd_rsp_bank==source_bank&&rd_rsp_addr==rd_req_addr;
 assign wr_req_valid=state==WRITE_OFFER&&!stop&&!power_on_reset;
 assign wr_req_epoch=rsp_epoch;assign wr_req_token=ticket;assign wr_req_bank=destination_bank;
 assign wr_req_addr=raster_row(destination_base,row_index);
 assign wr_req_data=tile[32'(row_index)*64+:64];
 assign wr_rsp_ready=state==WRITE_WAIT&&physical_pending&&!power_on_reset&&
  wr_rsp_epoch==rsp_epoch&&wr_rsp_token==ticket&&wr_rsp_bank==destination_bank&&wr_rsp_addr==wr_req_addr;
 always_ff @(posedge clk)begin
  if(power_on_reset)begin
   state<=IDLE;tile<=0;source_base<=0;destination_base<=0;source_bank<=0;destination_bank<=0;
   line_index<=0;row_index<=0;sample_index<=0;canceled<=0;owns_lease<=0;copy_mode<=0;ticket<=1;
   physical_pending<=0;rsp_error<=0;candidate_valid<=0;rsp_epoch<=0;rsp_src_id<=0;rsp_dst_id<=0;
  end else begin
   if(state!=IDLE&&state!=RESPONSE&&stop)begin canceled<=1;candidate_valid<=0;end
   case(state)
    IDLE:if(req_valid&&req_ready)begin
     rsp_epoch<=req_epoch;rsp_src_id<=req_src_id;rsp_dst_id<=req_dst_id;
     source_bank<=req_src_bank;destination_bank<=req_dst_bank;source_base<=req_src_addr;destination_base<=req_dst_addr;
     line_index<=0;row_index<=0;sample_index<=0;canceled<=0;copy_mode<=req_mode==0;
     rsp_error<=!legal;candidate_valid<=0;owns_lease<=legal;
     state<=!legal?RESPONSE:req_mode==0?READ_OFFER:req_mode==1?GENERATE:LITERAL;
    end
    GENERATE:if(stop)begin rsp_error<=1;state<=RESPONSE;end else begin
     for(integer n=0;n<GEN_LANES;n++)tile[(32'(sample_index)+n)*8+:8]<=8'd128;
     if(sample_index==7'(64-GEN_LANES))begin sample_index<=0;state<=WRITE_OFFER;end
     else sample_index<=sample_index+7'(GEN_LANES);
    end
    LITERAL:if(stop)begin rsp_error<=1;state<=RESPONSE;end else if(literal_valid&&literal_ready)begin
     tile[32'(sample_index)*8+:8]<=literal_data;
     if(sample_index==63)begin sample_index<=0;state<=WRITE_OFFER;end else sample_index<=sample_index+1;
    end
    READ_OFFER:if(stop)begin rsp_error<=1;state<=RESPONSE;end
     else if(rd_req_valid&&rd_req_ready)begin physical_pending<=1;state<=READ_WAIT;end
    READ_WAIT:if(rd_rsp_valid&&rd_rsp_ready)begin
     physical_pending<=0;ticket<=ticket==32'hffffffff?32'd1:ticket+1;
     if(stop||rd_rsp_error)begin rsp_error<=1;state<=RESPONSE;end else begin
      tile[32'(line_index)*128+:128]<=rd_rsp_data;
      if(line_index==3)state<=WRITE_OFFER;else begin line_index<=line_index+1;state<=READ_OFFER;end
     end
    end
    WRITE_OFFER:if(stop)begin rsp_error<=1;state<=RESPONSE;end
     else if(wr_req_valid&&wr_req_ready)begin physical_pending<=1;state<=WRITE_WAIT;end
    WRITE_WAIT:if(wr_rsp_valid&&wr_rsp_ready)begin
     physical_pending<=0;ticket<=ticket==32'hffffffff?32'd1:ticket+1;
     if(stop||wr_rsp_error)begin rsp_error<=1;state<=RESPONSE;end
     else if(row_index==7)begin candidate_valid<=1;state<=RESPONSE;end
     else begin row_index<=row_index+1;state<=WRITE_OFFER;end
    end
    // Offered completion and lease remain immutable until acknowledged.
    RESPONSE:if(rsp_valid&&rsp_ready)begin state<=IDLE;owns_lease<=0;candidate_valid<=0;end
    default:state<=IDLE;
   endcase
  end
 end
 initial assert(GEN_LANES==1||GEN_LANES==4)else $fatal(1,"generator lanes must be 1 or 4");
 always_ff @(posedge clk)if(!power_on_reset)begin
  assert(state<=RESPONSE);
  assert(!(rd_req_valid&&wr_req_valid));
  if(rd_req_valid||wr_req_valid)assert(owns_lease&&!physical_pending&&ticket!=0);
  if(rsp_valid)assert(!physical_pending&&candidate_valid==!rsp_error);
  if(physical_pending)assert(state==READ_WAIT||state==WRITE_WAIT);
 end
endmodule
`default_nettype wire
