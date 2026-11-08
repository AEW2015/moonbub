`timescale 1ns/1ps
`default_nettype none
// Shared async assertion, domain-local synchronized release is REQUIRED.
// The RAM has DEPTH words; the registered output adds one elastic slot.
module v107_async_fifo #(
    parameter integer WIDTH=44, parameter integer AW=3
)(
    input wire wclk,wrst,input wire wvalid,output wire wready,
    input wire [WIDTH-1:0] wdata,
    input wire rclk,rrst,output reg rvalid,input wire rready,
    output reg [WIDTH-1:0] rdata
);
    localparam integer DEPTH=1<<AW;
    (* ram_style="block" *) reg [WIDTH-1:0] storage [0:DEPTH-1];
    reg [AW:0] wbin,wgray,rbin,rgray;
    (* ASYNC_REG="TRUE" *) reg [AW:0] rgray_meta,rgray_sync,wgray_meta,wgray_sync;
    (* ASYNC_REG="TRUE" *) reg [1:0] rup_sync,wup_sync;
    reg full,wup,rup;
    reg stalled_previous;reg [WIDTH-1:0] previous_data;
    wire take=wvalid&&wready;
    wire [AW:0] wnext=wbin+{{AW{1'b0}},take};
    wire [AW:0] wgnext=(wnext>>1)^wnext;
    wire empty=rgray==wgray_sync;
    wire fetch=!rrst&&wup_sync[1]&&(!rvalid||rready)&&!empty;
    wire [AW:0] rnext=rbin+1'b1;
    assign wready=!wrst&&rup_sync[1]&&!full;
    // Independent clocked read/write ports. Reset never touches RAM contents.
    always @(posedge wclk) if(take) storage[wbin[AW-1:0]]<=wdata;
    always @(posedge rclk) if(fetch) rdata<=storage[rbin[AW-1:0]];
    always @(posedge wclk or posedge wrst) begin
        if(wrst) begin
            wbin<=0;wgray<=0;rgray_meta<=0;rgray_sync<=0;rup_sync<=0;full<=0;wup<=0;
        end else begin
            rgray_meta<=rgray;rgray_sync<=rgray_meta;rup_sync<={rup_sync[0],rup};wup<=1;
            assert($onehot0(wgray^wgnext));
            wbin<=wnext;wgray<=wgnext;
            full<=wgnext=={~rgray_sync[AW:AW-1],rgray_sync[AW-2:0]};
        end
    end
    always @(posedge rclk or posedge rrst) begin
        if(rrst) begin
            rbin<=0;rgray<=0;wgray_meta<=0;wgray_sync<=0;wup_sync<=0;rvalid<=0;rup<=0;stalled_previous<=0;previous_data<=0;
        end else begin
            wgray_meta<=wgray;wgray_sync<=wgray_meta;wup_sync<={wup_sync[0],wup};rup<=1;
            if(stalled_previous) assert(rvalid && rdata==previous_data);
            stalled_previous<=rvalid&&!rready;previous_data<=rdata;
            if(fetch) assert($onehot0(rgray^((rnext>>1)^rnext)));
            if(!wup_sync[1]) rvalid<=0;
            else if(!rvalid||rready) rvalid<=fetch;
            if(fetch)begin rbin<=rnext;rgray<=(rnext>>1)^rnext;end
        end
    end
endmodule
`default_nettype wire
