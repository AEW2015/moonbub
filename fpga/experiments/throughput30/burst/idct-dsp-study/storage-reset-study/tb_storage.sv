`timescale 1ns/1ps
module tb_storage;
 reg clk=0,tready=1;always #5 clk=~clk;
 reg rst=1,start=0,iv=0,eob=0,tv=0,fp=0,fpop=0;reg [5:0] ii=0,ti=0;reg [15:0] idata=0;reg [31:0] tdata=0,fdata=0;
 wire ia,ib,iva,ivb;wire [15:0] ia0,ia1,ia2,ia3,ib0,ib1,ib2,ib3;wire [2:0] ixa,ixb;
 wire ta,tb,tva,tvb;wire [31:0] ta0,ta1,ta2,ta3,tb0,tb1,tb2,tb3;wire [2:0] txa,txb;
 wire fva,fvb;wire [31:0] fa,fb;
 jpeg_idct_ram uia(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(1'b0),.inport_valid_i(iv),.inport_data_i(idata),.inport_idx_i(ii),.inport_eob_i(eob),.outport_ready_i(1'b1),.inport_accept_o(ia),.outport_valid_o(iva),.outport_data0_o(ia0),.outport_data1_o(ia1),.outport_data2_o(ia2),.outport_data3_o(ia3),.outport_idx_o(ixa));
 jpeg_idct_ram uib(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(1'b0),.inport_valid_i(iv),.inport_data_i(idata),.inport_idx_i(ii),.inport_eob_i(eob),.outport_ready_i(1'b1),.inport_accept_o(ib),.outport_valid_o(ivb),.outport_data0_o(ib0),.outport_data1_o(ib1),.outport_data2_o(ib2),.outport_data3_o(ib3),.outport_idx_o(ixb));
 jpeg_idct_transpose uta(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(1'b0),.inport_valid_i(tv),.inport_data_i(tdata),.inport_idx_i(ti),.outport_ready_i(tready),.inport_accept_o(ta),.outport_valid_o(tva),.outport_data0_o(ta0),.outport_data1_o(ta1),.outport_data2_o(ta2),.outport_data3_o(ta3),.outport_idx_o(txa));
 jpeg_idct_transpose utb(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(1'b0),.inport_valid_i(tv),.inport_data_i(tdata),.inport_idx_i(ti),.outport_ready_i(tready),.inport_accept_o(tb),.outport_valid_o(tvb),.outport_data0_o(tb0),.outport_data1_o(tb1),.outport_data2_o(tb2),.outport_data3_o(tb3),.outport_idx_o(txb));
 jpeg_idct_fifo #(.WIDTH(32),.DEPTH(8),.ADDR_W(3)) ufa(.clk_i(clk),.rst_i(rst),.flush_i(start),.data_in_i(fdata),.push_i(fp),.pop_i(fpop),.data_out_o(fa),.accept_o(),.valid_o(fva));
 jpeg_idct_fifo #(.WIDTH(32),.DEPTH(8),.ADDR_W(3)) ufb(.clk_i(clk),.rst_i(rst),.flush_i(start),.data_in_i(fdata),.push_i(fp),.pop_i(fpop),.data_out_o(fb),.accept_o(),.valid_o(fvb));
 integer j,k,n,tdiff,icount,nonzero,drop=0,separate=0,busy=0;
 initial begin
  if(!$value$plusargs("DROP=%d",drop))drop=0;
  if(!$value$plusargs("SEPARATE=%d",separate))separate=0;
  if(!$value$plusargs("BUSY=%d",busy))busy=0;
  for(j=0;j<64;j=j+1)begin
   uia.u_ram0.ram[j]=16'h1234;uia.u_ram1.ram[j]=16'h1234;uia.u_ram2.ram[j]=16'h1234;uia.u_ram3.ram[j]=16'h1234;
   uib.u_ram0.ram[j]=16'hfedc;uib.u_ram1.ram[j]=16'hfedc;uib.u_ram2.ram[j]=16'hfedc;uib.u_ram3.ram[j]=16'hfedc;
  end
  for(j=0;j<32;j=j+1)begin
   uta.u_ram0.ram[j]=32'h12345678;uta.u_ram1.ram[j]=32'h12345678;uta.u_ram2.ram[j]=32'h12345678;uta.u_ram3.ram[j]=32'h12345678;
   utb.u_ram0.ram[j]=32'hfedcba98;utb.u_ram1.ram[j]=32'hfedcba98;utb.u_ram2.ram[j]=32'hfedcba98;utb.u_ram3.ram[j]=32'hfedcba98;
  end
  for(j=0;j<8;j=j+1)begin ufa.ram_q[j]=32'h12345678;ufb.ram_q[j]=32'hfedcba98;end
  repeat(3)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;
  if(fva||fvb||fa===fb)$fatal(1,"fifo invalid stale control");
  $display("EMPTY_FIFO_RAW_STALE_DIFFER valid=0");
  fp=1;fdata=32'hb0123456;@(negedge clk);fp=0;
  if(!fva||!fvb||fa!==fdata||fb!==fdata)$fatal(1,"fifo accepted ID mismatch");
  fpop=1;@(negedge clk);fpop=0;if(fva||fvb)$fatal(1,"fifo did not empty");
  $display("FIFO_VALID_ID_PASS");
  if(!ia||!ib)$fatal(1,"input not ready");iv=1;ii=0;idata=16'h0025;eob=!separate;@(negedge clk);iv=0;eob=separate;if(separate)@(negedge clk);eob=0;
  icount=0;nonzero=0;
  for(n=0;n<100;n=n+1)begin @(negedge clk);
   if(iva!==ivb)$fatal(1,"input valid mismatch");
   if(iva)begin
    if({ixa,ia0,ia1,ia2,ia3}!=={ixb,ib0,ib1,ib2,ib3})$fatal(1,"input valid stale leak n=%0d",n);
    if((ia0|ia1|ia2|ia3)!=0)nonzero=nonzero+1;icount=icount+1;
   end
  end
  if(icount!=64||nonzero==0)$fatal(1,"input incomplete count=%0d nonzero=%0d",icount,nonzero);
  $display("INPUT_SPARSE_MASK_PASS valid_cycles=%0d",icount);
  if(busy)begin
   // Deliberately hold consumer not ready; parent IDCT ties this input high.
   tready=0;
   for(k=0;k<128;k=k+1)begin
    if(!ta||!tb)$fatal(1,"early busy at %0d",k);
    ti=k%64;tdata=32'h88770000+k;tv=1;@(negedge clk);
   end
   if(ta||tb)$fatal(1,"both banks not busy");
   ti=0;tdata=32'h99999999;tv=1;@(negedge clk);
   if(ta||tb)$fatal(1,"busy cleared unexpectedly");
   tv=0;$display("TRANSPOSE_FORCED_BUSY_PASS accepted=128 rejected_offer=1");$finish;
  end else begin
  for(k=0;k<64;k=k+1)begin
   if(!ta||!tb)$fatal(1,"transpose not ready idx=%0d",k);
   ti=k;tdata=32'h55660000+k;tv=!(drop && k==5);@(negedge clk);
  end
  tv=0;tdiff=0;icount=0;
  for(n=0;n<110;n=n+1)begin @(negedge clk);
   if(tva!==tvb)$fatal(1,"transpose valid mismatch");
   if(tva)begin
    if({txa,ta0,ta1,ta2,ta3}!=={txb,tb0,tb1,tb2,tb3})tdiff=tdiff+1;
    icount=icount+1;
   end
  end
  if(icount!=64)$fatal(1,"transpose incomplete count=%0d",icount);
  if(!drop && tdiff!=0)$fatal(1,"complete block stale leak differences=%0d",tdiff);
  if(drop && tdiff==0)$fatal(1,"missing-index negative control failed");
  if(drop)$display("TRANSPOSE_MISSING_INDEX_DETECTED valid_cycles=%0d differing_cycles=%0d",icount,tdiff);
  else $display("TRANSPOSE_COMPLETE_BLOCK_PASS valid_cycles=%0d differing_cycles=%0d",icount,tdiff);
  $display("STORAGE_RESET_TEST_PASS drop=%0d",drop);$finish;
  end
 end
endmodule
