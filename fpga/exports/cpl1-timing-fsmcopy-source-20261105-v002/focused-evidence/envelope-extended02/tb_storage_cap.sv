`timescale 1ns/1ps
module tb_storage_cap;
 reg clk=0;always #5 clk=~clk;reg reset=1,abort=0,error_ready=0,start_large=0,start_small=0;reg[31:0]bytes_large=0,bytes_small=0;
 wire ready_large,ready_small,input_large,input_small,error_large,error_small;wire[3:0]code_large,code_small;
ar03_envelope #(.MAX_BYTES(65536)) large_storage(.clk(clk),.reset(reset),.abort(abort),.start_owner(64'hdead00000000beef),.start_check_epoch(1'b1),.start_expected_epoch(32'd1),.in_valid(1'b0),.in_data(8'b0),.in_last(1'b0),.envelope_ready(1'b0),.error_ready(error_ready),.rd_req_valid(1'b0),.rd_req_address(32'b0),.rd_req_owner(64'b0),.rd_req_epoch(32'b0),.rd_rsp_ready(1'b0),.retire_valid(1'b0),.retire_owner(64'b0),.retire_epoch(32'b0),.start_valid(start_large),.start_bytes(bytes_large),.start_ready(ready_large),.in_ready(input_large),.error_valid(error_large),.error_code(code_large));
ar03_envelope #(.MAX_BYTES(115)) small_storage(.clk(clk),.reset(reset),.abort(abort),.start_owner(64'hdead00000000beef),.start_check_epoch(1'b1),.start_expected_epoch(32'd1),.in_valid(1'b0),.in_data(8'b0),.in_last(1'b0),.envelope_ready(1'b0),.error_ready(error_ready),.rd_req_valid(1'b0),.rd_req_address(32'b0),.rd_req_owner(64'b0),.rd_req_epoch(32'b0),.rd_rsp_ready(1'b0),.retire_valid(1'b0),.retire_owner(64'b0),.retire_epoch(32'b0),.start_valid(start_small),.start_bytes(bytes_small),.start_ready(ready_small),.in_ready(input_small),.error_valid(error_small),.error_code(code_small));
integer checks=0;
 task probe(input integer is_small,input integer size,input integer reject);
 begin @(negedge clk);if(is_small)begin start_small=1;bytes_small=size;end else begin start_large=1;bytes_large=size;end
 @(negedge clk);start_small=0;start_large=0;#1;
 if(is_small)begin if(error_small!==reject[0]||input_small===reject[0])$fatal(1,"small parameter mismatch size%0d",size);end
 else begin if(error_large!==reject[0]||input_large===reject[0])$fatal(1,"large parameter mismatch size%0d",size);end
 if(reject)begin error_ready=1;@(negedge clk);error_ready=0;end else begin abort=1;@(negedge clk);abort=0;end
 #1;if(!ready_large||!ready_small)$fatal(1,"parameter probe cleanup");checks=checks+1;
 end endtask
 initial begin repeat(3)@(negedge clk);reset=0;
 probe(0,49152,0);probe(0,49153,1);probe(0,65536,1);probe(0,114,1);probe(0,115,0);
 probe(1,115,0);probe(1,116,1);probe(1,49152,1);probe(1,114,1);
 $display("STORAGE_PARAMETER_CAP_PASS checks=%0d protocol_cap=49152 large_storage=65536 small_storage=115",checks);$finish;end
endmodule
