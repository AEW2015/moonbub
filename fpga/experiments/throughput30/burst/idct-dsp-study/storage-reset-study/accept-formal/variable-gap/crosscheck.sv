`timescale 1ns/1ps
module crosscheck;
reg clk=0,valid=0;reg [5:0] idx=0;
miter m(.clk(clk),.valid(valid),.idx(idx));
integer fd,n,r;integer f,w,d,ri,st,v,i,ef,ew,ed,er,es;
reg [1023:0] path;
initial begin
 if(!$value$plusargs("VECTORS=%s",path))$fatal(1,"missing vectors");
 fd=$fopen(path,"r");if(!fd)$fatal(1,"open vectors"); n=0;
 while(!$feof(fd))begin
 r=$fscanf(fd,"%h %h %h %h %h %h %h %h %h %h %h %h\n",f,w,d,ri,st,v,i,ef,ew,ed,er,es);
 if(r==12)begin
  clk=0;m.ready=f;m.wr=w;m.rd=d;m.ri=ri;m.st=st;valid=v;idx=i;#1;clk=1;#1;
  if({m.ready,m.wr,m.rd,m.ri,m.st}!={ef[1:0],ew[0],ed[0],er[5:0],es[1:0]})$fatal(1,"transition mismatch vector=%0d",n);
  n=n+1;
 end else if(r!=-1)$fatal(1,"bad vector %0d",r);
 end
 if(n!=16384)$fatal(1,"bad count %0d",n);
 $display("MODEL_CROSSCHECK_PASS transitions=%0d",n);$finish;
end
endmodule
