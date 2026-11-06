`timescale 1ns/1ps
module tb;reg[255:0]hash_value=0;reg[127:0]wanted_tag=0;

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

wire old_bad=hash_value[255:128]!=wanted_tag;wire new_bad=!tag_equal_balanced;
reg[3:0]small_a,small_b;reg[1:0]lane_a,lane_b;integer checks=0,i,j,k,v;
function automatic bit4(input integer n);case(n)0:bit4=0;1:bit4=1;2:bit4=1'bx;3:bit4=1'bz;endcase endfunction
task check;begin #1;if(old_bad!==new_bad)$fatal(1,"full1284state mismatch");checks++;end endtask
initial begin
 // Exhaustive four-state four-bit comparison versus two grouped two-bit limbs.
 for(v=0;v<65536;v++)begin
  for(k=0;k<4;k++)begin small_a[k]=bit4((v>>(k*2))&3);small_b[k]=bit4((v>>(8+k*2))&3);end
  #1;if((small_a!=small_b)!==!((small_a[1:0]==small_b[1:0])&&(small_a[3:2]==small_b[3:2])))$fatal(1,"compositional4state mismatch");checks++;
 end
 for(i=0;i<128;i++)for(j=2;j<4;j++)begin
  hash_value=0;wanted_tag=0;hash_value[128+i]=bit4(j);check();
  wanted_tag[(i+17)%128]=1;check();
  wanted_tag=0;wanted_tag[i]=bit4(j);hash_value=0;check();
  hash_value[128+(i+1)%128]=1;check();
 end
 for(i=0;i<10000;i++)begin hash_value={$random,$random,$random,$random,$random,$random,$random,$random};wanted_tag=hash_value[255:128];check();wanted_tag[i%128]=~wanted_tag[i%128];check();end
 $display("TAG_EQ_FOURSTATE_PASS checks=%0d",checks);$finish;
end endmodule
