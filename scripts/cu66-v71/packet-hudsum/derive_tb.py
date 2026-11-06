from pathlib import Path
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/packet-prefix-v003'
t=(r/'fpga/experiments/cu66-v71/packet-prefix-v002/tb_prefix.sv').read_text().replace('cu71_packet_presum','cu71_packet_hudsum')
tasks='''
 reg[7:0]hh[0:105];
 task hput32(input integer at,input reg[31:0]v);begin for(integer i=0;i<4;i++)dut.hud_header[at+i]=v[8*i+:8];end endtask
 task setuphud(input bit key,input reg[31:0]a,b,c,d);begin
  @(negedge clk);rst=1;tick();@(negedge clk);rst=0;abort_i=0;
  for(integer i=0;i<106;i++)dut.hud_header[i]=hh[i];
  dut.metadata_key=key;if(!key)dut.hud_header[22]=1;
  dut.metadata_frame_id={hh[13],hh[12],hh[11],hh[10]};dut.metadata_reference_id={hh[17],hh[16],hh[15],hh[14]};
  dut.packet_bytes=49152;dut.metadata_hud_bytes=(a+b+c+d+110>49152)?16'd49152:16'(a+b+c+d+110);
  hput32(54,a);hput32(58,b);hput32(62,c);hput32(66,d);dut.state=dut.HUD_SUM_PAIRS;
  tick();check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready,"HUD pairs private");
  tick();check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready,"HUD merge private");
  tick();check(dut.hud_length_total===32'(a+b+c+d+110),"HUD exact modulo32 staged sum");
 end endtask
 task legalhud(input bit key,input reg[31:0]a,b,c,d);begin
  setuphud(key,a,b,c,d);tick();check(debug_state==1&&!error&&!metadata_valid,"legal HUD header resumes exact scan");
  for(integer i=0;i<16;i++)begin
   check(dut.metadata_hud_output_tag[127-8*i-:8]===hh[38+i],"HUD output tag packing");
   check(dut.metadata_hud_reference_tag[127-8*i-:8]===((!key&&i==0)?8'd1:hh[22+i]),"HUD reference tag packing");
  end
 end endtask
 task rejecthud(input reg[31:0]a,b,c,d,input bit bad_header,input bit bad_rect,input bit bad_type,input reg[7:0]wanted);begin
  setuphud(1,a,b,c,d);if(bad_header)dut.hud_header[0]=0;if(bad_rect)dut.hud_header[74]=dut.hud_header[74]^8'd1;if(bad_type)dut.hud_header[70]=0;
  tick();check(done&&error&&error_code==wanted&&!busy&&!metadata_valid,"exact HUD11-before12 priority and grammar");
 end endtask
'''
t=t.replace(' initial begin',tasks+'\n initial begin',1).replace('$readmemh("header.hex",header);','$readmemh("header.hex",header);$readmemh("hud.hex",hh);')
t=t.replace('  $display("PACKET_PRESUM_FOCUSED_PASS checks=%0d",checks);','''  legalhud(1,1,1,1,1);legalhud(0,1,1,1,1);
  for(integer n=0;n<1000;n++)begin
   seed=seed*1664525+1013904223;a=1+(seed%10000);seed=seed*1664525+1013904223;b=1+(seed%10000);seed=seed*1664525+1013904223;c=1+(seed%10000);legalhud(n[0],a,b,c,1);
  end
  for(integer n=0;n<10;n++)begin
   rejecthud(bounds[n],1,1,1,1,0,0,11);
   if(n==0||n>=3)rejecthud(bounds[n],1,1,1,0,0,0,12);
   rejecthud(1,1,1,1,0,1,0,12);rejecthud(1,1,1,1,0,0,1,12);
   rejecthud(0,1,1,1,1,1,1,11);
  end
  setuphud(1,1,1,1,1);dut.metadata_hud_bytes=115;tick();check(error&&error_code==12,"HUD total mismatch");
  for(integer n=0;n<1000;n++)begin
   seed=seed*1664525+1013904223;setuphud(1,seed,seed^32'hfedcba98,seed+32'h12345678,seed-32'hc0000000);tick();check(error&&error_code==12,"HUD wide malformed rejection and sum wrap");
  end
  for(integer stage=0;stage<3;stage++)begin
   setuphud(1,1,1,1,1);@(negedge clk);dut.state=dut.HUD_SUM_PAIRS;
   for(integer k=0;k<stage;k++)tick();@(negedge clk);abort_i=1;tick();check(done&&aborted&&!busy&&!metadata_valid&&!rd_req_valid,"HUD sum state abort");@(negedge clk);abort_i=0;legalhud(1,1,1,1,1);
   setuphud(1,1,1,1,1);@(negedge clk);dut.state=dut.HUD_SUM_PAIRS;
   for(integer k=0;k<stage;k++)tick();@(negedge clk);rst=1;tick();check(!busy&&!error&&!aborted&&!dut.inner_validated&&dut.hud_length_total===0,"HUD sum state reset");@(negedge clk);rst=0;legalhud(0,1,1,1,1);
  end
  $display("PACKET_HUDSUM_FOCUSED_PASS checks=%0d",checks);''')
(d/'tb_prefix.sv').write_text(t,newline='\n')
