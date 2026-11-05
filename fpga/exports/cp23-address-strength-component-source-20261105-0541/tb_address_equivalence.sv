module tb;
 reg[9:0]base_x;reg[8:0]base_y;
 wire h0=base_x>=22&&base_x<182&&base_y>=54&&base_y<78;
 wire h1=base_x>=22&&base_x<182&&base_y>=82&&base_y<106;
 wire h2=base_x>=168&&base_x<488&&base_y>=360&&base_y<384;
 wire h3=base_x>=168&&base_x<408&&base_y>=390&&base_y<414;
 // Explicit modulo-2^16 unsigned row strides; only low16 address bits are consumed.
 wire[15:0]hud_y0={7'd0,base_y}-16'd54,hud_y1={7'd0,base_y}-16'd82;
 wire[15:0]hud_y2={7'd0,base_y}-16'd360,hud_y3={7'd0,base_y}-16'd390;
 wire[15:0]hud_stride0=(hud_y0<<7)+(hud_y0<<5);
 wire[15:0]hud_stride1=(hud_y1<<7)+(hud_y1<<5);
 wire[15:0]hud_stride2=(hud_y2<<8)+(hud_y2<<6);
 wire[15:0]hud_stride3=(hud_y3<<8)-(hud_y3<<4);
 wire[15:0]hud_address=h0?hud_stride0+{6'd0,base_x}-16'd22:h1?16'd3840+hud_stride1+{6'd0,base_x}-16'd22:h2?16'd7680+hud_stride2+{6'd0,base_x}-16'd168:16'd15360+hud_stride3+{6'd0,base_x}-16'd168;
 wire[15:0]original_address=h0?(base_y-54)*160+base_x-22:h1?3840+(base_y-82)*160+base_x-22:h2?7680+(base_y-360)*320+base_x-168:15360+(base_y-390)*240+base_x-168;
 // Modulo-2^24 unsigned constant strides; explicit operand width prevents shift truncation.
 function automatic [23:0] stride120(input [23:0] value);
  stride120=(value<<7)-(value<<3);
 endfunction
 function automatic [23:0] stride240(input [23:0] value);
  stride240=(value<<8)-(value<<4);
 endfunction

 reg[23:0]v,b;reg[23:0]old120,old240,new120,new240;integer x,y,i,j,n;
 initial begin
 n=0;
 for(y=0;y<512;y=y+1)for(x=0;x<1024;x=x+1)begin
 base_x=x;base_y=y;#1;if(hud_address!==original_address)$fatal(1,"HUD x%0d y%0d old%0h new%0h",x,y,original_address,hud_address);n=n+1;
 end
 for(i=0;i<1024;i=i+1)for(j=0;j<8;j=j+1)begin
 v=i;case(j)0:b=0;1:b=24'hffffff;2:b=24'hffff00;3:b=24'h100000;4:b=24'h800000;5:b=24'h7fffff;6:b=24'h2a3000;7:b=24'hfc0000;endcase
 old120=b+v*24'd120;old240=b+v*24'd240;new120=b+stride120(v);new240=b+stride240(v);#1;
 if(old120!==new120||old240!==new240)$fatal(1,"gather stride mismatch");n=n+2;
 end
 for(i=0;i<100000;i=i+1)begin
 v=$random;b=$random;old120=b+v*24'd120;old240=b+v*24'd240;new120=b+stride120(v);new240=b+stride240(v);#1;
 if(old120!==new120||old240!==new240)$fatal(1,"modulo mismatch");n=n+2;
 end
 $display("ADDRESS_STRENGTH_COMPILED_EQUIVALENCE_PASS checks=%0d all_hud_x=1024 all_hud_y=512",n);$finish;
 end
endmodule
