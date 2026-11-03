`timescale 1ns/1ps
`default_nettype none
// Dualclock async write queue plus bundled-data read mailbox. Read address
// remains held until the next command, well beyond the eight dummy-byte period.
module moonshine_bus_cdc_credit_large(
 input wire spi_clk,spi_reset,input wire spi_write,spi_read,
 input wire[11:0]spi_address,input wire[31:0]spi_wdata,
 output reg[31:0]spi_rdata,output reg overflow,output reg[31:0]overflow_gray,output wire[11:0]spi_free,
 input wire core_clk,core_reset,output wire core_write,
 output wire[11:0]core_address,output wire[31:0]core_wdata,input wire[31:0]core_rdata
);
 localparam AW=11;
 (* ram_style="block" *)reg[43:0]queue[0:2047];
 reg[43:0]queue_read;
 // A separate unconditional synchronous read infers a core-clock block-RAM
 // port. Selecting the LUTRAM output directly made write-clock-to-core paths.
 always @(posedge core_clk)queue_read<=queue[rp[AW-1:0]];
 reg[AW:0]wp,wgray,rp,rgray;
 (* ASYNC_REG="TRUE" *)reg[AW:0]rg1,rg2,wg1,wg2;
 // Research-only conservative source-domain credit. The synchronized read
 // pointer lags the consumer, never intentionally grants space in advance.
 function automatic [AW:0] ungray(input [AW:0] value);
 integer k;begin for(k=0;k<=AW;k=k+1)ungray[k]=^(value>>k);end
 endfunction
 wire [AW:0] synced_read=ungray(rg2);
 wire [AW:0] used_conservative=wp-synced_read;
 // Existing full rule intentionally leaves one slot unused.
 assign spi_free=(used_conservative<=12'd2047)?(12'd2047-used_conservative):12'd0;
 wire[AW:0]wnext=wp+1'b1;
 wire full=((wnext^(wnext>>1))=={~rg2[AW:AW-1],rg2[AW-2:0]});
 wire empty=rgray==wg2;
 reg read_toggle;reg[11:0]read_address;reg[31:0]overflow_count;
 (* ASYNC_REG="TRUE" *)reg[2:0]read_sync,ack_sync;
 reg read_seen,ack;reg[31:0]response;
 reg[1:0]read_state;
 reg[11:0]latched_address;
 reg fetched;
 wire fetch=!empty && read_state==0 && !fetched;
 wire consume=fetched && read_state==0;
 assign core_write=consume;
 wire[43:0]q=queue_read;
 assign core_address=read_state!=0 ? latched_address:q[43:32];
 assign core_wdata=q[31:0];
 always @(posedge spi_clk)begin
  if(spi_reset)begin
   wp<=0;wgray<=0;rg1<=0;rg2<=0;read_toggle<=0;read_address<=0;
   ack_sync<=0;spi_rdata<=0;overflow<=0;overflow_count<=0;overflow_gray<=0;
  end else begin
   rg1<=rgray;rg2<=rg1;ack_sync<={ack_sync[1:0],ack};
   if(spi_write)begin
    if(full)begin overflow<=1;overflow_count<=overflow_count+1'b1;
     overflow_gray<=(overflow_count+1'b1)^((overflow_count+1'b1)>>1);end
    else begin queue[wp[AW-1:0]]<={spi_address,spi_wdata};wp<=wnext;wgray<=wnext^(wnext>>1);end
   end
   if(spi_read)begin read_address<=spi_address;read_toggle<=!read_toggle;end
   if(ack_sync[2]!=ack_sync[1])spi_rdata<=response;
  end
 end
 always @(posedge core_clk)begin
  if(core_reset)begin rp<=0;rgray<=0;wg1<=0;wg2<=0;read_sync<=0;read_seen<=0;ack<=0;
   response<=0;read_state<=0;latched_address<=0;fetched<=0;
  end else begin
   wg1<=wgray;wg2<=wg1;read_sync<={read_sync[1:0],read_toggle};
   if(consume)begin rp<=rp+1'b1;rgray<=((rp+1'b1)^((rp+1'b1)>>1));end
   if(fetch)fetched<=1;
   if(consume)fetched<=0;
   // Drain earlier writes before taking the snapshot. Firmware metadata+START
   // is therefore visible before its following credit/status read.
   case(read_state)
    0:if(read_sync[2]!=read_seen && empty && !fetched)begin read_state<=1;latched_address<=read_address;end
    1:begin response<=core_rdata;read_state<=2;end
    2:begin ack<=!ack;read_seen<=read_sync[2];read_state<=0;end
    default:read_state<=0;
   endcase
  end
 end
endmodule
`default_nettype wire
