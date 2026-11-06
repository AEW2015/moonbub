module tag_miter(input[255:0]hash_value,input[127:0]wanted_tag,output same);

    // Exact same128-bit logical equality, kept limb boundaries and balanced tree.
    (* KEEP="TRUE" *) wire [7:0] tag_limb_equal;
    (* KEEP="TRUE" *) wire [3:0] tag_pair_equal;
    (* KEEP="TRUE" *) wire [1:0] tag_quad_equal;
    wire tag_equal_balanced;
    for(genvar tag_limb=0;tag_limb<8;tag_limb=tag_limb+1)begin:g_tag_equal
        assign tag_limb_equal[tag_limb]=hash_value[128+tag_limb*16+:16]==wanted_tag[tag_limb*16+:16];
    end
    assign tag_pair_equal={tag_limb_equal[7]&tag_limb_equal[6],tag_limb_equal[5]&tag_limb_equal[4],tag_limb_equal[3]&tag_limb_equal[2],tag_limb_equal[1]&tag_limb_equal[0]};
    assign tag_quad_equal={tag_pair_equal[3]&tag_pair_equal[2],tag_pair_equal[1]&tag_pair_equal[0]};
    assign tag_equal_balanced=tag_quad_equal[1]&tag_quad_equal[0];

assign same=(hash_value[255:128]!=wanted_tag)==(!tag_equal_balanced);endmodule
