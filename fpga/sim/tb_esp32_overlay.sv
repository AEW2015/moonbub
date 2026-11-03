`timescale 1ns/1ps
module tb_esp32_overlay;
    reg sys_clk=0,pixel_clk=0;
    always #2.5 sys_clk=~sys_clk;
    always #17 pixel_clk=~pixel_clk;
    reg sys_rst_n=0,pixel_rst_n=0,ov_wr=0;
    reg [17:0] ov_addr=0;
    reg [15:0] ov_data=0;
    reg [9:0] in_x=0,in_y=0;
    reg in_hs=0,in_vs=0,in_de=0;
    reg [23:0] in_rgb=0;
    wire out_hs,out_vs,out_de,overlay_visible;
    wire [23:0] out_rgb;
    esp32_overlay dut(.*);
    wire [23:0] theme_rgb;
    esp32_overlay #(.TESTER_THEME(1)) themed(
        .sys_clk(sys_clk),.sys_rst_n(sys_rst_n),.ov_wr(ov_wr),.ov_addr(ov_addr),.ov_data(ov_data),
        .pixel_clk(pixel_clk),.pixel_rst_n(pixel_rst_n),.in_x(in_x),.in_y(in_y),
        .in_hs(in_hs),.in_vs(in_vs),.in_de(in_de),.in_rgb(in_rgb),.out_rgb(theme_rgb));
    reg [15:0] model[0:86399];
    reg [26:0] expected[0:2];
    reg [23:0] expected_theme[0:2];
    integer checks=0,j,a,gray,cr,cg,cb;
    reg [15:0] p;
    reg [23:0] color,themed_color;
    function automatic [23:0] expand(input [14:0] c);
        expand={c[14:10],c[14:12],c[9:5],c[9:7],c[4:0],c[4:2]};
    endfunction
    always @(posedge pixel_clk) begin
        if(!pixel_rst_n) begin
            for(j=0;j<3;j=j+1) begin expected[j]=0;expected_theme[j]=0;end
        end else begin
            expected[2]=expected[1];expected[1]=expected[0];
            expected_theme[2]=expected_theme[1];expected_theme[1]=expected_theme[0];
            p=0;
            if(in_x<480 && in_y>=12 && in_y<732) begin
                a=(in_x/2)*360+(in_y-12)/2;
                p=model[a];
            end
            color=in_de ? (p[15] ? expand(p[14:0]) : in_rgb) : 0;
            themed_color=color;
            if(in_de && p[15] && p[14:10]==p[9:5] && p[9:5]==p[4:0]) begin
                gray=p[14:10];
                cr=(233*(31-gray)+12*gray+15)/31;
                cg=(242*(31-gray)+27*gray+15)/31;
                cb=(250*(31-gray)+39*gray+15)/31;
                themed_color={cr[7:0],cg[7:0],cb[7:0]};
            end
            expected[0]={in_hs,in_vs,in_de,color};expected_theme[0]=themed_color;
        end
        #1;
        if({out_hs,out_vs,out_de,out_rgb}!==expected[2])
            $fatal(1,"overlay alignment/pixel mismatch check=%0d got=%h expected=%h",checks,{out_hs,out_vs,out_de,out_rgb},expected[2]);
        if(theme_rgb!==expected_theme[2]) $fatal(1,"theme mismatch");
        checks=checks+1;
    end
    task automatic write_pixel(input integer byte_addr,input [15:0] data);
        begin
            @(negedge sys_clk);ov_addr=byte_addr;ov_data=data;ov_wr=1;
            @(posedge sys_clk);
            if(sys_rst_n && (byte_addr%2)==0 && byte_addr/2<86400) model[byte_addr/2]=data;
            @(negedge sys_clk);ov_wr=0;
        end
    endtask
    task automatic sample(input integer x,y,input bit de,hs,vs,input [23:0] rgb);
        begin @(negedge pixel_clk);in_x=x;in_y=y;in_de=de;in_hs=hs;in_vs=vs;in_rgb=rgb;end
    endtask
    task automatic blank_frame;
        begin sample(0,0,0,0,1,0);sample(0,0,0,0,0,0);repeat(5) @(negedge pixel_clk);end
    endtask
    integer x,y,k;
    initial begin
        for(k=0;k<86400;k=k+1) model[k]=0;
        repeat(5) @(negedge pixel_clk);sys_rst_n=1;pixel_rst_n=1;
        // Power-up transparent, arbitrary underlying tester colors and syncs.
        sample(0,12,1,0,0,24'h123456);sample(479,731,1,1,0,24'h654321);
        sample(240,372,1,0,0,24'habcdef);blank_frame();
        if(overlay_visible) $fatal(1,"transparent initialization owns app");
        // Distinct 2x2 corners and a row/column marker catch transpose/mirror.
        write_pixel(0,16'hfc00);write_pixel(718,16'h83e0);
        write_pixel(172080,16'h801f);write_pixel(172798,16'hffff);
        write_pixel((7*360+9)*2,16'h94a5);
        write_pixel((10*360+10)*2,16'h8000);
        write_pixel((10*360+11)*2,16'hffff & 16'h7fff);
        // Odd/out-of-range writes must not alias the first or final pixel.
        write_pixel(1,16'h8000);write_pixel(172800,16'h8000);write_pixel(262142,16'h8000);
        for(x=0;x<2;x=x+1) for(y=12;y<14;y=y+1) sample(x,y,1,0,0,24'h010203);
        sample(0,730,1,0,0,24'h010203);sample(1,731,1,0,0,24'h010203);
        sample(478,12,1,0,0,24'h010203);sample(479,13,1,0,0,24'h010203);
        sample(478,730,1,0,0,24'h010203);sample(479,731,1,0,0,24'h010203);
        sample(14,30,1,0,0,24'h010203);sample(20,32,1,0,0,24'h010203);
        sample(20,34,1,0,0,24'h010203);
        sample(0,11,1,0,0,24'hfedcba);sample(0,732,1,0,0,24'hfedcba);
        sample(480,12,1,0,0,24'hfedcba);sample(1023,1023,1,0,0,24'hfedcba);
        blank_frame();if(!overlay_visible) $fatal(1,"opaque overlay not detected");
        // Complete panel verifies every border and repeated source coordinate.
        for(y=0;y<800;y=y+1) for(x=0;x<480;x=x+1)
            sample(x,y,1,(x%13)==0,0,{y[7:0],x[7:0],8'h5a});
        blank_frame();if(!overlay_visible) $fatal(1,"visible frame lost");
        // Remove all opaque markers; normal framebuffer update, not CPU clear.
        write_pixel(0,0);write_pixel(718,0);write_pixel(172080,0);write_pixel(172798,0);
        write_pixel((7*360+9)*2,0);write_pixel((10*360+10)*2,0);
        for(y=0;y<800;y=y+1) for(x=0;x<480;x=x+1) sample(x,y,1,0,0,24'h556677);
        blank_frame();if(overlay_visible) $fatal(1,"transparent frame does not release app");
        // Reset must suppress pipeline output without erasing ESP32 content.
        write_pixel(0,16'hfc00);sample(0,12,1,0,0,24'h222222);
        repeat(5) @(negedge pixel_clk);
        pixel_rst_n=0;sys_rst_n=0;repeat(5) @(negedge pixel_clk);
        write_pixel(0,16'h801f); // writes while system reset ignored
        pixel_rst_n=1;sys_rst_n=1;sample(0,12,1,0,0,24'h222222);
        repeat(5) @(negedge pixel_clk);
        sample(0,0,0,0,0,0);repeat(5) @(negedge pixel_clk);
        for(k=0;k<32;k=k+1) write_pixel(200+k*2,16'h8000|(k<<10)|(k<<5)|k);
        for(k=0;k<32;k=k+1) sample(0,212+k*2,1,0,0,24'h222222);
        repeat(5) @(negedge pixel_clk);
        $display("ESP32_OVERLAY_PASS checks=%0d full_frames=2 alpha_edges_orientation_init_reset_palette=PASS",checks);
        $finish;
    end
    initial begin #100000000;$fatal(1,"timeout");end
endmodule
