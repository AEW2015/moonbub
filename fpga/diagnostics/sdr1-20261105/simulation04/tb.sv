`timescale 1ns/1ps
module tb;
reg clk=0;always #5 clk=~clk;wire read_clk;assign #2.625 read_clk=~clk;
reg reset=1,go=0;wire req,ready,wr,rv,idle,wb,ri;
wire[23:0]addr,first_address;wire[127:0]data,first_response;wire[15:0]rd,raw,response_mask;
wire[31:0]status,counts,first_values,run_id;wire[255:0]raw_trace;
wire[12:0]a;wire[1:0]ba,cke,cs;wire[15:0]dq;wire sk,ras,cas,we,lm,um;
sdr1_engine engine(.clk(clk),.reset(reset),.go(go),.request_valid(req),.request_ready(ready),.request_write(wr),
 .request_address(addr),.request_data(data),.response_valid(rv),.response_data(rd),.observe_write_beat(wb),
 .observe_read_issue(ri),.raw_read(raw),.status(status),.counts(counts),.first_address(first_address),
 .first_values(first_values),.raw_trace(raw_trace),.first_response(first_response),.response_mask(response_mask),.run_id(run_id));
moonshine_sdram_burst controller(.clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(req),.request_ready(ready),
 .request_write(wr),.request_address(addr),.request_burst_data(data),.request_burst_mask(16'd0),
 .observe_write_beat(wb),.observe_read_issue(ri),.observe_raw_read(raw),.response_valid(rv),.response_data(rd),.idle(idle),
 .sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),.sdram_clk(sk),.sdram_cke(cke),.sdram_cs_n(cs),
 .sdram_ras_n(ras),.sdram_cas_n(cas),.sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
sdram_model_burst #(.MEM_WORDS(1572865),.CLOCK_FLIGHT_NS(0.757),.T_AC_NS(2.223),.T_OH_NS(2.223))model(
 .clk(sk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),.ldqm(lm),.udqm(um),.dq(dq));
localparam[127:0]EXPECTED=128'h17071606150514041303120211011000;
reg[651:0]held;integer i,found=0,cycles=0;
always @(posedge clk)begin cycles=cycles+1;if(cycles>200000)$fatal(1,"bounded diagnostic timeout");end
initial begin
 repeat(5)@(negedge clk);reset=0;repeat(3)@(negedge clk);
 // Start while initialization is pending: one owned pending request.
 go=1;repeat(2)@(negedge clk);go=0;
 wait(engine.state==2&&ready);@(negedge clk);go=1;
 repeat(2)@(negedge clk);go=0;
 wait(status[1]);@(negedge clk);
 if(status[0]||status[23:16]!=0||status[15:8]!=32||!status[2]||counts[23:16]!=32||counts[31:24]!=1||counts[3]||run_id!=1)$fatal(1,"diagnostic counters status=%h counts=%h gen=%0d",status,counts,run_id);
 if(first_response!==EXPECTED||model.writes!=32)$fatal(1,"literal independent memory readback resp=%h",first_response);
 if($countones(response_mask)!=8)$fatal(1,"read-valid trace mask");
 for(i=0;i<=8;i=i+1)if(raw_trace[i*16+:128]===EXPECTED)found=1;
 if(!found)$fatal(1,"raw trace omitted the expected contiguous burst");
 held={status,counts&32'hfffffffd,raw_trace,first_response,first_address,first_values,response_mask,run_id};
 repeat(100)begin @(negedge clk);if({status,counts&32'hfffffffd,raw_trace,first_response,first_address,first_values,response_mask,run_id}!==held)$fatal(1,"retained result changed");end
 $display("SDR1_NATIVE_READBACK_PASS reads=32 writes=32 busy_rejection=1 raw_trace=16 literal_words=8 mask=%h raw=%h",response_mask,raw_trace);
 reset=1;go=1;repeat(5)@(negedge clk);reset=0;repeat(50)@(negedge clk);
 if(status[0]||status[1]||run_id!=0)$fatal(1,"held GO fabricated a restart after reset");
 $display("SDR1_RESET_ADMISSION_PASS held_GO_no_restart=1");$finish;
end
endmodule
