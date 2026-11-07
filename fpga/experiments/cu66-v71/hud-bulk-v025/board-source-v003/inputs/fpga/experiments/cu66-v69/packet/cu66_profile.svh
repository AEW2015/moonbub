// Fixed CU66 source profile. Wire digest byte0 occupies bits[127:120].
localparam logic [127:0] CU66_PROFILE = 128'h16c998527276c7c5249e96c75931494b;
function automatic [15:0] expected_rect(input integer index);
  case(index)
    0: expected_rect=16'd22;
    1: expected_rect=16'd54;
    2: expected_rect=16'd160;
    3: expected_rect=16'd24;
    4: expected_rect=16'd22;
    5: expected_rect=16'd82;
    6: expected_rect=16'd160;
    7: expected_rect=16'd24;
    8: expected_rect=16'd168;
    9: expected_rect=16'd360;
    10: expected_rect=16'd320;
    11: expected_rect=16'd24;
    12: expected_rect=16'd168;
    13: expected_rect=16'd390;
    14: expected_rect=16'd240;
    15: expected_rect=16'd24;
    default: expected_rect=16'd0;
  endcase
endfunction
