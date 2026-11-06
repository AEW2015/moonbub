module dc_math(input [8:0] dc_column,input signed [31:0] previous_dc,input [31:0] rice_value,output same);
    function automatic signed [31:0] unzigzag(input [31:0] value);
        unzigzag = value[0] ? -$signed(value >> 1)-32'sd1 : $signed(value >> 1);
    endfunction
wire signed [31:0] captured=(dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value);
wire old_fail=((dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value))<-2048 || ((dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value))>2048;
wire new_fail=captured<-2048 || captured>2048;
wire signed [31:0] old_previous=(dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value);
wire [15:0] old_tile=16'((dc_column==0?32'sd0:previous_dc)+unzigzag(rice_value));
assign same=(old_fail==new_fail) && (old_previous==captured) && (old_tile==16'(captured));
endmodule
