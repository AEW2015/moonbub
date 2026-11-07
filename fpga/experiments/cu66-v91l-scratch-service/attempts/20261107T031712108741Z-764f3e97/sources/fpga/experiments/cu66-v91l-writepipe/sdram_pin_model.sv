`timescale 1ns/1ps
`default_nettype none
// Functional, source-compatible pin model; finite timing checks, not vendor/PVT signoff.
module sdram_pin_model #(parameter real T_AC_NS=2.0,CLOCK_FLIGHT_NS=4.0)(
 input wire clk,input wire [12:0] a,input wire [1:0] ba,cke,cs,
 input wire ras,cas,we,ldqm,udqm,inout wire [15:0] dq,
 input wire [23:0] peek_addr,output wire [15:0] peek_data,
 output integer writes,readwords,refreshes,mrs,activates,precharges
);
 logic [15:0] mem [0:16777215];logic [12:0] rows[0:3];logic [3:0] opened=0;
 logic drive_request=0;logic[15:0]data_request=0;wire drive;wire[15:0]outdata;
 assign #(T_AC_NS)drive=drive_request;assign #(T_AC_NS)outdata=data_request;
 integer latency=0,left=0,readaddr=0,cycle=0,lastcolumn=-100;
 integer lastact[0:3],lastpre[0:3],lastwrite[0:3],lastref=-100;
 wire device_clock;assign #(CLOCK_FLIGHT_NS) device_clock=clk;
 assign dq=drive?outdata:16'bz;assign peek_data=mem[peek_addr];
 function automatic logic [15:0] initial_word(input logic [23:0] unused_addr);return unused_addr[15:0]^16'h5a3c;endfunction
 initial begin
  writes=0;readwords=0;refreshes=0;mrs=0;activates=0;precharges=0;
  for(integer i=0;i<16777216;i=i+1)mem[i]=initial_word(24'(i));
  for(integer b=0;b<4;b=b+1)begin rows[b]=0;lastact[b]=-100;lastpre[b]=-100;lastwrite[b]=-100;end
 end
 initial forever begin
  @(posedge device_clock);if(cke[0])begin
  assert(!cke[1]&&cs[1])else $fatal(1,"unexpected second SDRAM chip enabled");
  cycle=cycle+1;
  if(latency>0)begin
   latency=latency-1;
   if(latency==0)begin
    data_request=mem[readaddr];drive_request=1;readaddr=readaddr+1;left=7;readwords=readwords+1;
    $display("{\"type\":\"read\",\"cycle\":%0d,\"time_ps\":%0d,\"address\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),readaddr-1,mem[readaddr-1]);
   end
  end else if(left>0)begin
   data_request=mem[readaddr];readaddr=readaddr+1;left=left-1;readwords=readwords+1;
   $display("{\"type\":\"read\",\"cycle\":%0d,\"time_ps\":%0d,\"address\":%0d,\"data\":%0d}",cycle,longint'($realtime*1000.0),readaddr-1,mem[readaddr-1]);
  end else drive_request=0;
  if(!cs[0]&&{ras,cas,we}!=3'b111)begin
   $display("{\"type\":\"pin\",\"cycle\":%0d,\"time_ps\":%0d,\"command\":%0d,\"bank\":%0d,\"address\":%0d,\"row\":%0d,\"dq\":%0d}",cycle,longint'($realtime*1000.0),{ras,cas,we},ba,a,rows[ba],({ras,cas,we}==3'b100)?dq:16'd0);
   case({ras,cas,we})
    3'b011:begin
     assert(!opened[ba]&&cycle-lastpre[ba]>=2&&cycle-lastref>=8)else $fatal(1,"ACT timing/open bank");
     opened[ba]=1;rows[ba]=a;lastact[ba]=cycle;activates=activates+1;
    end
    3'b010:begin
     if(a[10])begin
      for(integer b=0;b<4;b=b+1)begin
       assert(!opened[b]||(cycle-lastact[b]>=5&&cycle-lastwrite[b]>=2))else $fatal(1,"all PRE timing");lastpre[b]=cycle;
      end
      opened=0;
     end else begin
      assert(!opened[ba]||(cycle-lastact[ba]>=5&&cycle-lastwrite[ba]>=2))else $fatal(1,"PRE timing");opened[ba]=0;lastpre[ba]=cycle;
     end
     precharges=precharges+1;
    end
    3'b100:begin
     assert(opened[ba]&&cycle-lastact[ba]>=2&&!drive&&!ldqm&&!udqm)else $fatal(1,"WRITE timing/mask/contention");
     assert(cycle-lastcolumn>=1)else $fatal(1,"WRITE tCCD below one clock");lastcolumn=cycle;
     mem[{ba,rows[ba],a[8:0]}]=dq;lastwrite[ba]=cycle;writes=writes+1;
    end
    3'b101:begin
     assert(opened[ba]&&cycle-lastact[ba]>=2&&a[2:0]==0)else $fatal(1,"READ timing/alignment");
     assert(cycle-lastcolumn>=1)else $fatal(1,"READ tCCD below one clock");lastcolumn=cycle;
     readaddr=int'({ba,rows[ba],a[8:0]});latency=3;
    end
    3'b001:begin assert(opened==0&&cycle-lastref>=8)else $fatal(1,"REF timing/open bank");lastref=cycle;refreshes=refreshes+1;end
    3'b000:begin assert(a==13'h233)else $fatal(1,"MRS mismatch");mrs=mrs+1;end
    default:$fatal(1,"unexpected SDRAM command");
   endcase
  end
 end
 end
endmodule
`default_nettype wire
