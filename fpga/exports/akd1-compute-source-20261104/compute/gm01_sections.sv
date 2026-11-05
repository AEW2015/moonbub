// AR03 GM01 section/map certificate only; CP02 and publication remain downstream.
module gm01_sections(
 input wire clk,reset,abort,
 input wire start_valid,output wire start_ready,
 input wire[63:0] start_owner,input wire[31:0] start_bytes,
 input wire[31:0] start_epoch,start_frame,start_reference,input wire start_key,
 input wire in_valid,output wire in_ready,input wire[7:0] in_data,input wire in_last,
 output wire inner_sections_validated,input wire certificate_ready,
 output wire[63:0] desc_owner,output wire[31:0] desc_epoch,desc_frame,desc_reference,
 output wire desc_key,output wire[15:0] desc_width,desc_height,
 output wire[31:0] desc_map_bytes,output wire[95:0] desc_plane_offsets,desc_plane_lengths,
 output wire[47:0] desc_blocks_w,desc_blocks_h,
 output wire error_valid,input wire error_ready,output reg[3:0] error_code,
 output wire[63:0] error_owner,
 input wire block_req_valid,output wire block_req_ready,
 input wire[63:0] block_req_owner,input wire[31:0] block_req_epoch,
 input wire[1:0] block_req_plane,input wire[15:0] block_req_x,block_req_y,
 output wire block_valid,input wire block_ready,output reg block_error,
 output reg[63:0] block_owner,output reg[31:0] block_epoch,
 output reg[1:0] block_plane,output reg[15:0] block_x,block_y,
 output reg[31:0] block_index,output reg[5:0] block_scale,
 input wire retire_valid,output wire retire_ready,
 input wire[63:0] retire_owner,input wire[31:0] retire_epoch
);
 localparam IDLE=0,LOAD=1,CHECK=2,CERTIFICATE=3,QUERY=4,ERROR=5,
  PRODUCTS=6,LIMITS=7,FLAGS=8,DECIDE=9;
 reg[3:0] state;
 reg[63:0] owner;
 reg[31:0] total,expected_epoch,expected_frame,expected_reference;
 reg expected_key;
 reg[31:0] cursor,crc_state,trailer,magic,epoch,frame,reference_id,nmap;
 reg[7:0] version,flags;
 reg[15:0] width,height,dx,dy,mw,mh;
 reg[31:0] plane_length[0:2];
 // Conservative fixed bound: ceil(2048/16)^2 / 4 = 4096 packed bytes.
 // The pixel-area restriction lowers actual use; no coefficient payload is stored.
 (* ram_style="block" *) reg[7:0] map_memory[0:4095];
 reg[7:0] map_q;
 reg map_bad,read_pending,pending_error,response_valid;
 reg[1:0] pending_code;
 reg[63:0] pending_owner;
 reg[31:0] pending_epoch,pending_index;
 reg[1:0] pending_plane;
 reg[15:0] pending_x,pending_y;
 localparam Q_IDLE=0,Q_SELECT=1,Q_MULTIPLY=2,Q_ADD=3,Q_READ=4,Q_RETURN=5;
 reg[2:0] query_phase;
 reg[15:0] request_bw,request_bh,map_x,map_y;
 reg request_identity;
 reg[31:0] map_row,index_row,request_cell;
 wire[31:0] expected_mw=({16'b0,width}+15)>>4;
 wire[31:0] expected_mh=({16'b0,height}+15)>>4;
 wire[31:0] cells={16'b0,mw}*{16'b0,mh};
 wire[31:0] pixels={16'b0,width}*{16'b0,height};
 wire[31:0] expected_map=(cells+3)>>2;
 wire[15:0] luma_bw=({16'b0,width}+7)>>3;
 wire[15:0] luma_bh=({16'b0,height}+7)>>3;
 wire[15:0] chroma_bw=({16'b0,(width>>1)}+7)>>3;
 wire[15:0] chroma_bh=({16'b0,(height>>1)}+7)>>3;
 wire[31:0] luma_blocks={16'b0,luma_bw}*{16'b0,luma_bh};
 wire[31:0] chroma_blocks={16'b0,chroma_bw}*{16'b0,chroma_bh};
 wire[33:0] exact_total=34'd50+{2'b0,nmap}+{2'b0,plane_length[0]}+{2'b0,plane_length[1]}+{2'b0,plane_length[2]};
 wire geometry_ok=width>=2&&width<=2048&&height>=2&&height<=2048&&!width[0]&&!height[0]&&pixels<=345600;
 wire header_ok=magic==32'h31304d47&&version==1&&(flags==0||flags==1)&&epoch!=32'hffffffff&&frame!=32'hffffffff&&
  epoch==expected_epoch&&frame==expected_frame&&reference_id==expected_reference&&flags[0]==expected_key&&dx==0&&dy==0&&
  ((flags==1)?reference_id==32'hffffffff:reference_id<frame);
 wire map_geometry_ok=mw==expected_mw&&mh==expected_mh&&nmap==expected_map&&nmap<=4096;
 wire plane_bounds_ok=plane_length[0]>=26&&plane_length[0]<=128*luma_blocks+26&&
  plane_length[1]>=26&&plane_length[1]<=128*chroma_blocks+26&&plane_length[2]>=26&&plane_length[2]<=128*chroma_blocks+26;
 // Registered arithmetic preserves the original 16/32/34-bit domains, including
 // malformed headers. Never narrow dimensions on the assumption they are valid.
 reg[15:0] lbw_q,lbh_q,cbw_q,cbh_q;
 reg[31:0] pixels_q,cells_q,mw_q,mh_q,map_q_expected;
 reg[31:0] lblocks_q,cblocks_q,llimit_q,climit_q;
 reg[31:0] offset0_q,offset1_q,offset2_q;
 reg[33:0] total_left_q,total_right_q,total_q;
 reg header_q,sr_q,dimensions_q,geometry_q,map_geometry_q,planes_q,total_ok_q,crc_q,map_bad_q;
 wire matching_retire=state==QUERY&&retire_valid&&retire_owner==owner&&retire_epoch==epoch;
 wire drained_retire=matching_retire&&!read_pending&&!response_valid;
 // Rounded dimensions are captured before certificate validation. They remain
 // stable for the complete lease, including held descriptors and query stalls.
 wire map_read_enable=state==QUERY&&read_pending&&query_phase==Q_READ&&!pending_error&&!reset&&!abort;
 wire[31:0] map_position=cursor-46;
 integer i,j;
 assign start_ready=state==IDLE&&!reset&&!abort;
 assign in_ready=state==LOAD&&!reset&&!abort;
 assign inner_sections_validated=state==CERTIFICATE&&!reset&&!abort;
 assign desc_owner=owner;assign desc_epoch=epoch;assign desc_frame=frame;assign desc_reference=reference_id;
 assign desc_key=flags[0];assign desc_width=width;assign desc_height=height;assign desc_map_bytes=nmap;
 assign desc_plane_offsets={offset2_q,offset1_q,offset0_q};
 assign desc_plane_lengths={plane_length[2],plane_length[1],plane_length[0]};
 assign desc_blocks_w={cbw_q,cbw_q,lbw_q};assign desc_blocks_h={cbh_q,cbh_q,lbh_q};
 assign error_valid=state==ERROR&&!reset&&!abort;assign error_owner=owner;
 assign block_req_ready=state==QUERY&&!read_pending&&(!response_valid||block_ready)&&!matching_retire&&!reset&&!abort;
 assign block_valid=state==QUERY&&response_valid&&!reset&&!abort;
 assign retire_ready=state==QUERY&&retire_owner==owner&&retire_epoch==epoch&&!read_pending&&!response_valid&&!reset&&!abort;
 function automatic[31:0] crc_byte(input[31:0] old,input[7:0] value);
 reg[31:0] c;integer b;
 begin c=old^{24'b0,value};for(b=0;b<8;b=b+1)c=(c>>1)^(c[0]?32'hedb88320:0);crc_byte=c;end endfunction
 // All map reads and writes are clocked; abort/reset invalidate leases, not RAM.
 always @(posedge clk)if(!reset&&!abort)begin
  if(in_ready&&in_valid&&cursor>=46&&cursor<total-4&&map_position<nmap&&map_position<4096)map_memory[map_position]<=in_data;
  if(map_read_enable)map_q<=map_memory[request_cell>>2];
 end
 always @(posedge clk)begin
  if(reset||abort)begin
   state<=IDLE;owner<=0;read_pending<=0;query_phase<=Q_IDLE;response_valid<=0;error_code<=0;
   block_error<=0;block_owner<=0;block_epoch<=0;block_plane<=0;block_x<=0;block_y<=0;block_index<=0;block_scale<=0;
  end else begin
   if(block_valid&&block_ready)response_valid<=0;
   // All request identity is opaque and captured before arithmetic begins.
   // read_pending owns this complete pipeline and fences matching retire.
   if(read_pending)case(query_phase)
    Q_SELECT:begin
     request_bw<=pending_plane==0?lbw_q:cbw_q;
     request_bh<=pending_plane==0?lbh_q:cbh_q;
     map_x<=pending_plane==0?(pending_x>>1):pending_x;
     map_y<=pending_plane==0?(pending_y>>1):pending_y;
     request_identity<=pending_owner==owner&&pending_epoch==epoch&&pending_plane<3;
     query_phase<=Q_MULTIPLY;
    end
    Q_MULTIPLY:begin
     map_row<={16'b0,map_y}*{16'b0,mw};
     index_row<={16'b0,pending_y}*{16'b0,request_bw};
     pending_error<=!request_identity||pending_x>=request_bw||pending_y>=request_bh;
     query_phase<=Q_ADD;
    end
    Q_ADD:begin
     request_cell<=map_row+{16'b0,map_x};
     pending_index<=index_row+{16'b0,pending_x};
     query_phase<=Q_READ;
    end
    Q_READ:begin pending_code<=request_cell[1:0];query_phase<=Q_RETURN;end
    Q_RETURN:begin
    block_error<=pending_error;block_owner<=pending_owner;block_epoch<=pending_epoch;block_plane<=pending_plane;
    block_x<=pending_x;block_y<=pending_y;block_index<=pending_error?0:pending_index;
    block_scale<=pending_error?0:(6'd8<<((map_q>>(6-2*pending_code))&3));
    response_valid<=1;read_pending<=0;query_phase<=Q_IDLE;
    end
    default:begin read_pending<=0;query_phase<=Q_IDLE;end
   endcase
   if(block_req_ready&&block_req_valid)begin
    read_pending<=1;query_phase<=Q_SELECT;pending_owner<=block_req_owner;
    pending_epoch<=block_req_epoch;pending_plane<=block_req_plane;pending_x<=block_req_x;pending_y<=block_req_y;
   end
   case(state)
    IDLE:if(start_valid)begin
     owner<=start_owner;total<=start_bytes;expected_epoch<=start_epoch;expected_frame<=start_frame;expected_reference<=start_reference;expected_key<=start_key;
     cursor<=0;crc_state<=32'hffffffff;trailer<=0;magic<=0;version<=0;flags<=0;epoch<=0;frame<=0;reference_id<=0;
     width<=0;height<=0;dx<=0;dy<=0;mw<=0;mh<=0;nmap<=0;map_bad<=0;read_pending<=0;query_phase<=Q_IDLE;response_valid<=0;
     for(i=0;i<3;i=i+1)plane_length[i]<=0;
     if(start_bytes<50||start_bytes>49152)begin error_code<=1;state<=ERROR;end else state<=LOAD;
    end
    LOAD:if(in_valid)begin
     if(cursor<total-4)crc_state<=crc_byte(crc_state,in_data);else trailer[(cursor-(total-4))*8+:8]<=in_data;
     if(cursor<4)magic[cursor*8+:8]<=in_data;
     if(cursor==4)version<=in_data;if(cursor==5)flags<=in_data;
     if(cursor>=6&&cursor<10)epoch[(cursor-6)*8+:8]<=in_data;
     if(cursor>=10&&cursor<14)frame[(cursor-10)*8+:8]<=in_data;
     if(cursor>=14&&cursor<18)reference_id[(cursor-14)*8+:8]<=in_data;
     if(cursor>=18&&cursor<20)width[(cursor-18)*8+:8]<=in_data;
     if(cursor>=20&&cursor<22)height[(cursor-20)*8+:8]<=in_data;
     if(cursor>=22&&cursor<24)dx[(cursor-22)*8+:8]<=in_data;
     if(cursor>=24&&cursor<26)dy[(cursor-24)*8+:8]<=in_data;
     if(cursor>=26&&cursor<28)mw[(cursor-26)*8+:8]<=in_data;
     if(cursor>=28&&cursor<30)mh[(cursor-28)*8+:8]<=in_data;
     if(cursor>=30&&cursor<34)nmap[(cursor-30)*8+:8]<=in_data;
     for(i=0;i<3;i=i+1)if(cursor>=34+4*i&&cursor<38+4*i)plane_length[i][(cursor-(34+4*i))*8+:8]<=in_data;
     if(cursor>=46&&cursor<total-4&&map_position<nmap)begin
      if(map_position>=4096)map_bad<=1;
      for(j=0;j<4;j=j+1)begin
       if(map_position*4+j<cells)begin if(((in_data>>(6-2*j))&3)>2)map_bad<=1;end
       else if(((in_data>>(6-2*j))&3)!=0)map_bad<=1;
      end
     end
     if(in_last!=(cursor==total-1))begin state<=ERROR;error_code<=2;end
     else if(cursor==total-1)state<=CHECK;
     cursor<=cursor+1;
    end
    CHECK:begin
     offset0_q<=32'd46+nmap;
     lbw_q<=luma_bw;lbh_q<=luma_bh;cbw_q<=chroma_bw;cbh_q<=chroma_bh;
     pixels_q<=pixels;cells_q<=cells;mw_q<=expected_mw;mh_q<=expected_mh;
     total_left_q<=34'd50+{2'b0,nmap}+{2'b0,plane_length[0]};
     total_right_q<={2'b0,plane_length[1]}+{2'b0,plane_length[2]};
     header_q<=header_ok;sr_q<=magic==32'h31305253;
     dimensions_q<=width>=2&&width<=2048&&height>=2&&height<=2048&&!width[0]&&!height[0];
     crc_q<=(crc_state^32'hffffffff)==trailer;map_bad_q<=map_bad;
     state<=PRODUCTS;
    end
    PRODUCTS:begin
     offset1_q<=offset0_q+plane_length[0];
     lblocks_q<={16'b0,lbw_q}*{16'b0,lbh_q};
     cblocks_q<={16'b0,cbw_q}*{16'b0,cbh_q};
     map_q_expected<=(cells_q+32'd3)>>2;
     total_q<=total_left_q+total_right_q;
     geometry_q<=dimensions_q&&pixels_q<=345600;
     state<=LIMITS;
    end
    LIMITS:begin
     offset2_q<=offset1_q+plane_length[1];
     llimit_q<=32'd128*lblocks_q+32'd26;
     climit_q<=32'd128*cblocks_q+32'd26;
     map_geometry_q<=mw==mw_q&&mh==mh_q&&nmap==map_q_expected&&nmap<=4096;
     total_ok_q<=total_q=={2'b0,total};
     state<=FLAGS;
    end
    FLAGS:begin
     planes_q<=plane_length[0]>=26&&plane_length[0]<=llimit_q&&
      plane_length[1]>=26&&plane_length[1]<=climit_q&&plane_length[2]>=26&&plane_length[2]<=climit_q;
     state<=DECIDE;
    end
    DECIDE:begin
     if(sr_q)begin state<=ERROR;error_code<=3;end // SR01 unsupported.
     else if(!header_q)begin state<=ERROR;error_code<=4;end
     else if(!geometry_q||!map_geometry_q)begin state<=ERROR;error_code<=5;end
     else if(!planes_q||!total_ok_q)begin state<=ERROR;error_code<=6;end
     else if(!crc_q)begin state<=ERROR;error_code<=7;end
     else if(map_bad_q)begin state<=ERROR;error_code<=8;end
     else state<=CERTIFICATE;
    end
    CERTIFICATE:if(certificate_ready)state<=QUERY;
    QUERY:if(drained_retire)state<=IDLE;
    ERROR:if(error_ready)state<=IDLE;
    default:state<=IDLE;
   endcase
  end
 end
endmodule
