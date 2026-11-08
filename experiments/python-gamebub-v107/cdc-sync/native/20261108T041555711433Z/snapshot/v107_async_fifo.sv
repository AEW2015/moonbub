`timescale 1ns/1ps
`default_nettype none
// Separate V107 prototype: shared async assertion / >=3 local reset edges.
// RAM address/enable cones use synchronous local state ONLY. Public transfer
// qualifiers gate immediately on local reset; private RAM may complete one
// discarded access on the first reset edge. New reads require committed data.
module v107_async_fifo #(
    parameter integer WIDTH=44, parameter integer AW=3
)(
    input wire async_reset,
    input wire wclk,wrst,input wire wvalid,output wire wready,
    input wire [WIDTH-1:0] wdata,
    input wire rclk,rrst,output wire rvalid,input wire rready,
    output reg [WIDTH-1:0] rdata
);
    localparam integer DEPTH=1<<AW;
    (* ram_style="block" *) reg [WIDTH-1:0] storage [0:DEPTH-1];
    // wreserve includes the one outstanding staged write; wbin/wgray publish
    // only completed physical writes. Read ownership advances after capture.
    reg [AW:0] wreserve,wbin,wgray,rbin,rgray;
    (* ASYNC_REG="TRUE" *) reg [AW:0] rgray_meta,rgray_sync,wgray_meta,wgray_sync;
    (* ASYNC_REG="TRUE" *) reg [1:0] rup_sync,wup_sync;
    reg full,rvalid_owned,write_pending,read_pending;
    reg [AW-1:0] write_address,read_address;
    reg [WIDTH-1:0] write_payload;
    // These notification-only flops MUST clear even with a stopped clock.
    // Their only crossing destinations are first synchronizer D pins; they
    // never directly drive a BRAM address/control. Preserve independent flags.
    (* DONT_TOUCH="TRUE" *) reg wup,rup;
    wire take=wvalid&&wready;
    wire [AW:0] reserve_next=wreserve+{{AW{1'b0}},take};
    wire [AW:0] reserve_gray_next=(reserve_next>>1)^reserve_next;
    wire [AW:0] commit_next=wbin+{{AW{1'b0}},write_pending};
    wire [AW:0] commit_gray_next=(commit_next>>1)^commit_next;
    wire [AW:0] read_next=rbin+1'b1;
    wire empty=rgray==wgray_sync;
    assign wready=!wrst&&rup_sync[1]&&!full;
    assign rvalid=!rrst&&rvalid_owned;
    // Pure synchronous RAM control: no wrst/rrst/ready/valid input appears in
    // either physical enable or address. Never reset the memory/output data.
    always @(posedge wclk)
        if(write_pending) storage[write_address]<=write_payload;
    always @(posedge rclk)
        if(read_pending) rdata<=storage[read_address];
    always @(posedge wclk or posedge async_reset)
        if(async_reset) wup<=0;else if(wrst) wup<=0;else wup<=1;
    always @(posedge rclk or posedge async_reset)
        if(async_reset) rup<=0;else if(rrst) rup<=0;else rup<=1;
    always @(posedge wclk) begin
        if(wrst)begin
            wreserve<=0;wbin<=0;wgray<=0;rgray_meta<=0;rgray_sync<=0;
            rup_sync<=0;full<=0;write_pending<=0;write_address<=0;
        end else begin
            rgray_meta<=rgray;rgray_sync<=rgray_meta;rup_sync<={rup_sync[0],rup};
            wreserve<=reserve_next;wbin<=commit_next;wgray<=commit_gray_next;
            full<=reserve_gray_next=={~rgray_sync[AW:AW-1],rgray_sync[AW-2:0]};
            write_pending<=take;
            if(take)begin write_address<=wreserve[AW-1:0];write_payload<=wdata;end
        end
    end
    always @(posedge rclk) begin
        if(rrst)begin
            rbin<=0;rgray<=0;wgray_meta<=0;wgray_sync<=0;wup_sync<=0;
            rvalid_owned<=0;read_pending<=0;read_address<=0;
        end else begin
            wgray_meta<=wgray;wgray_sync<=wgray_meta;wup_sync<={wup_sync[0],wup};
            if(rvalid_owned&&rready) rvalid_owned<=0;
            if(read_pending)begin
                rvalid_owned<=1;read_pending<=0;rbin<=read_next;rgray<=(read_next>>1)^read_next;
            end else if(wup_sync[1]&&(!rvalid_owned||rready)&&!empty)begin
                read_pending<=1;read_address<=rbin[AW-1:0];
            end
        end
    end
`ifndef SYNTHESIS
    reg stalled_previous;reg [WIDTH-1:0] previous_data;
    always @(posedge wclk)if(!wrst)begin
        assert($onehot0(wgray^commit_gray_next));
        assert(wreserve-wbin=={{AW{1'b0}},write_pending});
        if(write_pending) assert(write_address==wbin[AW-1:0]);
    end
    always @(posedge rclk)begin
        if(rrst)begin stalled_previous<=0;previous_data<=0;end
        else begin
            if(stalled_previous) assert(rvalid&&rdata==previous_data);
            stalled_previous<=rvalid&&!rready;previous_data<=rdata;
            if(read_pending)begin
                assert(read_address==rbin[AW-1:0]);
                assert(!rvalid_owned);
                assert($onehot0(rgray^((read_next>>1)^read_next)));
            end
        end
    end
`endif
endmodule
`default_nettype wire
