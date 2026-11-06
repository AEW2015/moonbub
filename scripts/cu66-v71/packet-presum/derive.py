from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];s=r/'fpga/experiments/cu66-v71/packet-prefix-v001/cu71_packet_prefix.sv';d=r/'fpga/experiments/cu66-v71/packet-prefix-v002'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(s)=='b4c8dcb002adf8c3522a73a73f06bd928acb5bf83c953883647577486a9a8b1d'
t=s.read_text().replace('module cu71_packet_prefix (','module cu71_packet_presum (')
t=t.replace('DRAIN, PREFIX_STARTS, PREFIX_ADDRESSES','DRAIN, PREFIX_STARTS, PREFIX_ADDRESSES, INNER_SUM_PAIRS, INNER_SUM_MERGE, INNER_SUM_TOTAL')
t=t.replace('logic [15:0] prefix0, prefix_yu, prefix_y;','logic [15:0] prefix0, prefix_yu, prefix_y;\n    logic [31:0] inner_sum0,inner_sum1,inner_sum2,inner_sum01,inner_length_total;')
t=t.replace('prefix0<=0;prefix_yu<=0;prefix_y<=0;','prefix0<=0;prefix_yu<=0;prefix_y<=0;\n            inner_sum0<=0;inner_sum1<=0;inner_sum2<=0;inner_sum01<=0;inner_length_total<=0;')
t=t.replace("else if(scan_addr==16'd135) state<=CHECK_INNER;","else if(scan_addr==16'd135) state<=INNER_SUM_PAIRS;")
t=t.replace("inner32(40)+inner32(44)+inner32(48)+inner32(52)+inner32(56)+32'd64!=32'(inner_bytes)","inner_length_total!=32'(inner_bytes)")
t=t.replace('                CHECK_INNER: begin','''                // All 60 header bytes have been captured; no byte read is outstanding.
                // Every register/addition retains original unsigned modulo-32 semantics.
                INNER_SUM_PAIRS: begin
                    inner_sum0<=inner32(40)+inner32(44);
                    inner_sum1<=inner32(48)+inner32(52);
                    inner_sum2<=inner32(56)+32'd64;
                    state<=INNER_SUM_MERGE;
                end
                INNER_SUM_MERGE: begin
                    inner_sum01<=inner_sum0+inner_sum1;
                    state<=INNER_SUM_TOTAL;
                end
                INNER_SUM_TOTAL: begin
                    inner_length_total<=inner_sum01+inner_sum2;
                    state<=CHECK_INNER;
                end
                CHECK_INNER: begin''')
p=d/'cu71_packet_presum.sv';p.write_text(t,newline='\n');(d/'derivation.json').write_text(json.dumps(dict(parent=str(s.relative_to(r)),parent_sha256=sha(s),output_sha256=sha(p),change='Three pre-CHECK_INNER unsigned32 modular sum stages; same validation priority, two prefix stages, ports and byte sequence; +5 successful clocks versusv69'),indent=2)+'\n')
tb=(s.parent/'tb_prefix.sv').read_text().replace('cu71_packet_prefix','cu71_packet_presum')
tb=tb.replace('dut.state=dut.CHECK_INNER;','''dut.state=dut.INNER_SUM_PAIRS;
  tick();check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready,"sum pair stage private");
  tick();check(!rd_req_valid&&!metadata_valid&&!commit_ready&&!qmap_req_ready,"sum merge stage private");
  tick();check(dut.inner_length_total===32'(338+m+y+u+v+64),"full-width modulo32 length sum");''')
tb=tb.replace('  $display("PACKET_PREFIX_FOCUSED_PASS checks=%0d",checks);', '''  for(integer stage=0;stage<3;stage++)begin
   setup(1,0,47,47,47);@(negedge clk);dut.state=dut.INNER_SUM_PAIRS;
   for(integer k=0;k<stage;k++)tick();@(negedge clk);abort_i=1;tick();check(done&&aborted&&!busy&&!metadata_valid&&!rd_req_valid,"sum state abort");@(negedge clk);abort_i=0;legal(1,0,47,47,47);
   setup(1,0,47,47,47);@(negedge clk);dut.state=dut.INNER_SUM_PAIRS;
   for(integer k=0;k<stage;k++)tick();@(negedge clk);rst=1;tick();check(!busy&&!error&&!aborted&&!dut.inner_validated&&dut.inner_length_total===0,"sum state reset");@(negedge clk);rst=0;legal(0,3,47,47,47);
  end
  for(integer n=0;n<1000;n++)begin
   seed=seed*1664525+1013904223;setup(1,seed,seed^32'hfedcba98,seed+32'h12345678,seed-32'hc0000000);tick();check(error&&error_code==7,"wide malformed operand rejection after exact modular sum");
  end
  $display("PACKET_PRESUM_FOCUSED_PASS checks=%0d",checks);''')
(d/'tb_prefix.sv').write_text(tb,newline='\n');print(p)
