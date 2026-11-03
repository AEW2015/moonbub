`timescale 1ns/1ps
module tb_idct_reset;
 reg clk=0;always #5 clk=~clk;
 reg rst=1,start=0,valid=0,eob=0;reg [15:0] data=0;reg [5:0] idx=0;reg [31:0] id=32'hb0123456;
 wire aa,ab,va,vb;wire [31:0] da,db,ida,idb;wire [5:0] xa,xb;
 jpeg_idct a(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(1'b0),.inport_valid_i(valid),.inport_data_i(data),.inport_idx_i(idx),.inport_eob_i(eob),.inport_id_i(id),.outport_accept_i(1'b1),.inport_accept_o(aa),.outport_valid_o(va),.outport_data_o(da),.outport_idx_o(xa),.outport_id_o(ida));
 jpeg_idct b(.clk_i(clk),.rst_i(rst),.img_start_i(start),.img_end_i(1'b0),.inport_valid_i(valid),.inport_data_i(data),.inport_idx_i(idx),.inport_eob_i(eob),.inport_id_i(id),.outport_accept_i(1'b1),.inport_accept_o(ab),.outport_valid_o(vb),.outport_data_o(db),.outport_idx_o(xb),.outport_id_o(idb));
 integer j,n,count,xcount,tcount,separate=0;
 reg [63:0] seen;
 initial begin
  if(!$value$plusargs("SEPARATE=%d",separate))separate=0;
  for(j=0;j<64;j=j+1)begin
   a.u_input.u_ram0.ram[j]=16'h1234;a.u_input.u_ram1.ram[j]=16'h1234;a.u_input.u_ram2.ram[j]=16'h1234;a.u_input.u_ram3.ram[j]=16'h1234;
   b.u_input.u_ram0.ram[j]=16'hfedc;b.u_input.u_ram1.ram[j]=16'hfedc;b.u_input.u_ram2.ram[j]=16'hfedc;b.u_input.u_ram3.ram[j]=16'hfedc;
  end
  for(j=0;j<32;j=j+1)begin
   a.u_transpose.u_ram0.ram[j]=32'h12345678;a.u_transpose.u_ram1.ram[j]=32'h12345678;a.u_transpose.u_ram2.ram[j]=32'h12345678;a.u_transpose.u_ram3.ram[j]=32'h12345678;
   b.u_transpose.u_ram0.ram[j]=32'hfedcba98;b.u_transpose.u_ram1.ram[j]=32'hfedcba98;b.u_transpose.u_ram2.ram[j]=32'hfedcba98;b.u_transpose.u_ram3.ram[j]=32'hfedcba98;
  end
  for(j=0;j<8;j=j+1)begin a.u_id_fifo.ram_q[j]=32'h12345678;b.u_id_fifo.ram_q[j]=32'hfedcba98;end
  // Force distinct pre-reset X outputs and a write during the first reset edge.
  a.u_idct_x.valid_q=8'h40;b.u_idct_x.valid_q=8'h40;a.u_idct_x.ptr_q=0;b.u_idct_x.ptr_q=0;
  a.u_idct_x.block_out[0]=32'h11223344;b.u_idct_x.block_out[0]=32'haabbccdd;
  a.u_transpose.block_ready_q=0;b.u_transpose.block_ready_q=0;a.u_transpose.block_wr_q=0;b.u_transpose.block_wr_q=0;
  @(negedge clk);
  if(a.u_transpose.u_ram0.ram[0]!==32'h11223344||b.u_transpose.u_ram0.ram[0]!==32'haabbccdd)$fatal(1,"first reset edge did not exercise different writes");
  $display("RESET_EDGE_POISON_WRITE_OBSERVED");
  repeat(2)@(negedge clk);rst=0;start=1;@(negedge clk);start=0;
  if(!aa||!ab)$fatal(1,"not ready");valid=1;eob=!separate;idx=0;data=16'h0025;@(negedge clk);valid=0;eob=separate;if(separate)@(negedge clk);eob=0;
  count=0;xcount=0;tcount=0;seen=0;
  for(n=0;n<3000;n=n+1)begin @(negedge clk);
   if(a.u_idct_x.outport_valid_o)begin
    if(!a.idct_x_accept_w || !b.idct_x_accept_w)$fatal(1,"X beat not accepted");
    seen[a.u_idct_x.outport_idx_o]=1; xcount=xcount+1;
   end
   if(a.u_transpose.outport_valid_o)begin if(seen!==64'hffffffffffffffff)$fatal(1,"transpose read before complete overwrite");tcount=tcount+1;end
   if(aa!==ab || va!==vb)$fatal(1,"handshake differs cycle=%0d",n);
   if(va)begin
    if({da,xa,ida}!=={db,xb,idb})$fatal(1,"post-reset valid output differs cycle=%0d",n);
    if(ida!==id||idb!==id)$fatal(1,"wrong output ID");
    if(xa!=={count[2:0],count[5:3]}||xb!=={count[2:0],count[5:3]})$fatal(1,"output index/order count=%0d xa=%0d xb=%0d",count,xa,xb);
    count=count+1;
   end
  end
  if(count!=64||xcount!=64||tcount!=64)$fatal(1,"bad counts output=%0d x=%0d transpose=%0d",count,xcount,tcount);
  $display("CONNECTED_X_ACCEPT_AND_COMPLETE_PASS x=%0d transpose=%0d",xcount,tcount);
  $display("IDCT_RESET_SPARSE_FRAME_PASS valid_outputs=%0d",count);$finish;
 end
endmodule
