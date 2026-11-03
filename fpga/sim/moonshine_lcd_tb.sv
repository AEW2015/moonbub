`timescale 1ns/1ps
module moonshine_lcd_tb;
    reg pixel_clk=0,mem_clk=0;
    always #17.029 pixel_clk=~pixel_clk;
    always #5 mem_clk=~mem_clk;
    reg reset_n=0,mem_reset=1,front_valid=0,front_buffer=0,pattern_enable=1;
    wire req;wire [23:0] address;reg ready=0,data_valid=0;reg [15:0] data=0;
    wire boundary;wire [31:0] underruns;wire hs,vs,de;wire[7:0]r,g,b;
    moonshine_lcd dut(.pixel_clk(pixel_clk),.reset_n(reset_n),.mem_clk(mem_clk),.mem_reset(mem_reset),
      .front_valid(front_valid),.front_buffer(front_buffer),.pattern_enable(pattern_enable),
      .line_req_valid(req),.line_req_ready(ready),.line_req_address(address),
      .line_data_valid(data_valid),.line_data(data),.frame_boundary(boundary),.underruns(underruns),
      .hsync(hs),.vsync(vs),.data_enable(de),.red(r),.green(g),.blue(b));
    integer frame=0,requests=0,responses=0,beat=0,delay_count=0,ticks=0;
    integer pixels=0,pattern_pixels=0,image_pixels=0,black_fault_pixels=0;
    reg inflight=0;reg [23:0] base=0;reg injected=0;
    reg stalled=0;reg [23:0] stalled_address;
    function automatic [15:0] value(input [23:0] addr);
        integer row,col;reg bufid;
        begin
            bufid=addr>=24'h080000;row=(addr & 24'h07ffff)/480;col=(addr & 24'h07ffff)%480;
            value={row[4:0],col[5:0],(row[4:0]^col[4:0]^{5{bufid}})};
        end
    endfunction
    // A variable-latency, backpressured external line transport. It is not an
    // SDRAM model; the separate controller tests own SDRAM command timing.
    always @(negedge mem_clk)begin
        ticks=ticks+1;ready=0;data_valid=0;
        if(!mem_reset)begin
            if(req && !inflight && ticks%11==0)ready=1;
            if(inflight)begin
                if(delay_count>0)delay_count=delay_count-1;
                else if(ticks%7!=0)begin data_valid=1;data=value(base+beat);end
            end
        end
    end
    always @(posedge mem_clk)begin
        if(!mem_reset)begin
            if(stalled && (!req || address!==stalled_address))$fatal(1,"request changed while stalled");
            stalled=req && !ready;stalled_address=address;
            if(boundary)begin
                frame=frame+1;
                if(frame==2)begin pattern_enable<=0;front_valid<=1;end
                if(frame==3)front_buffer<=1;
                if(frame==6)begin
                    if(underruns==0 || !injected || black_fault_pixels==0)$fatal(1,"underrun not exercised");
                    if(pattern_pixels<345600 || image_pixels<691200)$fatal(1,"coverage incomplete");
                    $display("LCD_PASS requests=%0d responses=%0d pattern=%0d image=%0d underruns=%0d black_fault=%0d",requests,responses,pattern_pixels,image_pixels,underruns,black_fault_pixels);
                    $finish;
                end
            end
            if(req && ready)begin
                if(inflight)$fatal(1,"overlapping line requests");
                if(address%480!=0 && (address-24'h080000)%480!=0)$fatal(1,"unaligned line");
                if((address & 24'h07ffff)<40*480 || (address & 24'h07ffff)>=760*480)$fatal(1,"read outside canvas");
                base=address;beat=0;inflight=1;requests=requests+1;
                if(frame==4 && !injected && (address & 24'h07ffff)==42*480)begin delay_count=6500;injected=1;end
            end
            if(data_valid && inflight)begin
                beat=beat+1;responses=responses+1;
                if(beat==480)inflight=0;
            end
        end
    end
    integer sx=0,sy=0;integer landscape_x,landscape_y;reg fault_line_black=0;
    reg[15:0]expected;reg[23:0]expected_rgb;
    // Independent raster model starts from reset and checks every output cycle.
    always @(posedge pixel_clk)begin
        if(!reset_n)begin sx=0;sy=0;end
        else begin
            landscape_x=sy-24;landscape_y=sx-14;
            expected=0;
            if(sx>=14 && sx<494 && sy>=24 && sy<824 && landscape_x>=40 && landscape_x<760)begin
                if(frame<=1)begin
                    case((landscape_x-40)/90)
                        0:expected=16'hffff;1:expected=16'hffe0;2:expected=16'h07ff;3:expected=16'h07e0;
                        4:expected=16'hf81f;5:expected=16'hf800;6:expected=16'h001f;default:expected=0;
                    endcase
                    pattern_pixels=pattern_pixels+1;
                end else begin
                    expected=value((frame>=3?24'h080000:0)+landscape_x*480+landscape_y);
                    image_pixels=image_pixels+1;
                end
            end
            expected_rgb={{expected[15:11],expected[15:13]},{expected[10:5],expected[10:9]},{expected[4:0],expected[4:2]}};
            #1;
            if(de!==(sx>=14 && sx<494 && sy>=24 && sy<824) || hs!==(sx<4) || vs!==(sy<4))$fatal(1,"native raster mismatch %0d,%0d",sx,sy);
            if(frame==4 && sx==14)fault_line_black=({r,g,b}==0 && expected_rgb!=0);
            if(frame==4 && de && landscape_x>=40 && landscape_x<760 && fault_line_black && {r,g,b}!=0)$fatal(1,"late line switched visible midway");
            if(frame>=1 && {r,g,b}!==expected_rgb)begin
                if(frame==4 && fault_line_black && {r,g,b}==0)black_fault_pixels=black_fault_pixels+1;
                else $fatal(1,"pixel mismatch frame%0d at%0d,%0d actual%h expected%h",frame,sx,sy,{r,g,b},expected_rgb);
            end
            pixels=pixels+de;
            if(sx==540)begin sx=0;if(sy==833)sy=0;else sy=sy+1;end else sx=sx+1;
        end
    end
    initial begin #101;mem_reset=0;reset_n=1;end
    initial begin #100000000;$fatal(1,"watchdog");end
endmodule
