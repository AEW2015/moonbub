module geometry_probe (input logic [1:0] geometry_plane,input logic [31:0] geometry_tile,input logic [15:0] raw_mask,output logic [15:0] mask,output logic [4:0] count,raw_count,output logic [31:0] original_count);
    function automatic logic hidden(input logic [1:0] p, input logic [31:0] t);
        if(p!=0)return t>=1046&&t<=1064;
        return (t>=633&&t<=651)||(t>=723&&t<=741)||
            (t>=993&&t<=1011)||(t>=1083&&t<=1101)||
            (t>=4071&&t<=4110)||(t>=4161&&t<=4200)||
            (t>=4251&&t<=4290)||(t>=4431&&t<=4460)||
            (t>=4521&&t<=4550);
    endfunction
    function automatic logic [31:0] tile_count(input logic [1:0] p);
        return p==0?32'd5400:32'd1350;
    endfunction
    function automatic logic [31:0] visible_group(input logic [1:0] p, input logic [31:0] t);
        logic [31:0] n;
        begin
            n=0;
            for(integer k=0;k<16;k=k+1)
                if(t+32'(k)<tile_count(p)&&!hidden(p,t+32'(k)))n=n+1;
            return n;
        end
    endfunction
    function automatic logic [15:0] visibility_mask(input logic [1:0] p,input logic [31:0] t);
        logic [15:0] m;
        begin
            for(integer k=0;k<16;k=k+1)
                m[k]=t+32'(k)<tile_count(p)&&!hidden(p,t+32'(k));
            return m;
        end
    endfunction
    function automatic logic [4:0] visibility_count(input logic [15:0] m);
        logic [1:0] pair_count [0:7];
        logic [2:0] quad_count [0:3];
        logic [3:0] oct_count [0:1];
        begin
            for(integer k=0;k<8;k=k+1)
                pair_count[k]={1'b0,m[2*k]}+{1'b0,m[2*k+1]};
            for(integer k=0;k<4;k=k+1)
                quad_count[k]={1'b0,pair_count[2*k]}+{1'b0,pair_count[2*k+1]};
            for(integer k=0;k<2;k=k+1)
                oct_count[k]={1'b0,quad_count[2*k]}+{1'b0,quad_count[2*k+1]};
            return {1'b0,oct_count[0]}+{1'b0,oct_count[1]};
        end
    endfunction
    assign mask=visibility_mask(geometry_plane,geometry_tile);
    assign count=visibility_count(mask);
    assign raw_count=visibility_count(raw_mask);
    assign original_count=visible_group(geometry_plane,geometry_tile);
endmodule
