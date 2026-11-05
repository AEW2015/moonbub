"""Isolated native-pad simulation; no hardware access or frozen-source changes."""
import argparse, hashlib, json, os, pathlib, shutil, subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', required=True)
parser.add_argument('--strict-hold', action='store_true')
parser.add_argument('--posedge-retime', action='store_true')
args = parser.parse_args()
out = pathlib.Path(args.output).resolve()
out.mkdir(parents=True, exist_ok=False)
package = ROOT / 'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
for src, name in [(package/'inputs/core/parents/moonshine_sdram_burst.sv', 'controller.sv'),
                  (package/'sim-inputs/core/parents/sdram_model_bounded.sv', 'model.sv'),
                  (package/'sim-inputs/sim/support-primitives.sv', 'primitives.sv')]:
    shutil.copyfile(src, out/name)
if args.strict_hold:
    # Isolated candidate knobs, not modifications to the sealed controller.
    p=out/'controller.sv'
    s=p.read_text().replace('REFRESH_CYCLES=750','REFRESH_CYCLES=750, READ_WAIT_CYCLES=5')
    assert 'else begin delay<=5;state<=READ_WAIT;' in s
    p.write_text(s.replace('else begin delay<=5;state<=READ_WAIT;',
                           'else begin delay<=READ_WAIT_CYCLES;state<=READ_WAIT;'))
    p=out/'model.sv'
    s=p.read_text().replace('T_AC_NS=2.0,','T_OH_NS=0.5, T_AC_NS=2.0,')
    # Do not stretch the previous beat through the device's access interval.
    assert 'else if(left>0)begin' in s
    s=s.replace('else if(left>0)begin','else if(left>0)begin outdata<=#(T_OH_NS) 16\'hxxxx;')
    s=s.replace('else drive<=#(T_AC_NS) 0;', 'else drive<=#(T_OH_NS) 0;')
    p.write_text(s)
if args.posedge_retime:
    p=out/'controller.sv'
    s=p.read_text()
    assert 'always @(negedge clk)dq_retime<=dq_capture;' in s
    p.write_text(s.replace('always @(negedge clk)dq_retime<=dq_capture;',
                           'always @(posedge clk)dq_retime<=dq_capture;'))
(out/'tb.sv').write_text(r'''
`timescale 1ns/1ps
module tb;
parameter real TAC=2.0;
parameter integer READ_DELAY=5;
reg clk=0; always #5 clk=~clk;
real flight=4.0, phase=7.75;
reg read_clk=0, device_clk=0;
always @(clk) read_clk <= #(phase) clk;
wire sclk;
always @(sclk) device_clk <= #(flight) sclk;
reg reset=1,valid=0,wr=1; reg[23:0]address=0;
reg[127:0]data=0; reg[15:0]mask=0;
wire ready,rv,idle; wire[15:0]rd,dq; wire[12:0]a;
wire[1:0]ba,cke,cs;wire ras,cas,we,lm,um;
moonshine_sdram_burst #(.POWERUP_CYCLES(0),.REFRESH_CYCLES(250)) dut(
 .clk(clk),.read_clk(read_clk),.reset(reset),.request_valid(valid),.request_ready(ready),
 .request_write(wr),.request_address(address),.request_burst_data(data),.request_burst_mask(mask),
 .response_valid(rv),.response_data(rd),.idle(idle),.sdram_a(a),.sdram_bs(ba),.sdram_dq(dq),
 .sdram_clk(sclk),.sdram_cke(cke),.sdram_cs_n(cs),.sdram_ras_n(ras),.sdram_cas_n(cas),
 .sdram_we_n(we),.sdram_ldqm(lm),.sdram_udqm(um));
sdram_model_burst #(.CLOCK_FLIGHT_NS(0.0),.T_AC_NS(TAC),.MEM_WORDS(2048)) model(
 .clk(device_clk),.a(a),.ba(ba),.cke(cke),.cs(cs),.ras(ras),.cas(cas),.we(we),
 .ldqm(lm),.udqm(um),.dq(dq));
integer i,j,k,n,errors=0,write_errors=0,read_errors=0,preload_errors=0;
integer base[0:5];reg[15:0]expected[0:2047];
task issue(input bit writing,input integer addr,input integer tag,input bit masked);
begin
 @(negedge clk);while(!ready)@(negedge clk);
 wr=writing;address=addr;mask=masked?16'h0924:0;
 for(j=0;j<8;j=j+1)data[j*16+:16]=tag+j*16'h101;
 valid=1;@(negedge clk);valid=0;
 if(writing)begin
  for(j=0;j<8;j=j+1)begin
   if(!mask[2*j])expected[addr+j][7:0]=data[j*16+:8];
   if(!mask[2*j+1])expected[addr+j][15:8]=data[j*16+8+:8];
  end
  while(!ready)@(negedge clk);
  for(j=0;j<8;j=j+1)if(model.mem[addr+j]!==expected[addr+j])begin
   write_errors=write_errors+1;
   $display("WRITE_MISMATCH addr=%0d actual=%04x expected=%04x",addr+j,model.mem[addr+j],expected[addr+j]);
  end
 end else begin
  n=0;
  while(n<8)begin
   @(negedge clk);
   if(rv)begin
    $display("READ addr=%0d beat=%0d actual=%04x expected=%04x t=%0t",addr,n,rd,expected[addr+n],$time);
    if(rd!==expected[addr+n])read_errors=read_errors+1;
    n=n+1;
   end
  end
 end
end endtask
initial begin
 if(!$value$plusargs("FLIGHT=%f",flight))flight=4.0;
 if(!$value$plusargs("PHASE=%f",phase))phase=7.75;
 base[0]=0;base[1]=8;base[2]=504;base[3]=512;base[4]=520;base[5]=1024;
 for(i=0;i<2048;i=i+1)begin expected[i]=16'hb000+i;model.mem[i]=expected[i];end
 repeat(5)@(negedge clk);reset=0;
 // Independent preloaded reads separate read-return alignment from writes.
 for(k=0;k<6;k=k+1)issue(0,base[k],0,0);
 preload_errors=read_errors;
 for(k=0;k<6;k=k+1)issue(1,base[k],16'h1000+k*16'h1000,0);
 for(k=0;k<6;k=k+1)issue(1,base[k],16'h7654+k*16'h0100,1);
 for(k=0;k<6;k=k+1)issue(0,base[k],0,0);
 $display("ALIGN_RESULT phase=%0f flight=%0f tac=%0f write_errors=%0d preload_errors=%0d read_errors=%0d writes=%0d refreshes=%0d",phase,flight,TAC,write_errors,preload_errors,read_errors,model.writes,model.refreshes);
 $finish;
end
initial begin #100000;$fatal(1,"bounded timeout");end
endmodule
''', newline='\n')
if args.strict_hold:
    p=out/'tb.sv'
    p.write_text(p.read_text().replace('.REFRESH_CYCLES(250)',
                                       '.REFRESH_CYCLES(250),.READ_WAIT_CYCLES(READ_DELAY)'))
env = dict(os.environ)
env['PATH'] = 'C:/msys64/ucrt64/bin' + os.pathsep + env.get('PATH', '')
rows=[]
for tac, read_delay in [(t,d) for t in [1.0,2.0,4.0]
                       for d in ([4,5,6] if args.strict_hold else [5])]:
    image=out/f'tac{tac}-delay{read_delay}.vvp'
    cmd=['C:/msys64/ucrt64/bin/iverilog.exe','-g2012','-s','tb',f'-Ptb.TAC={tac}',
         f'-Ptb.READ_DELAY={read_delay}', '-o',str(image),*[str(out/n) for n in ['controller.sv','model.sv','primitives.sv','tb.sv']]]
    q=subprocess.run(cmd,env=env,capture_output=True,text=True)
    (out/f'compile-{tac}-delay{read_delay}.log').write_text(q.stdout+q.stderr)
    assert q.returncode==0,q.stderr
    for phase in ([3.75,4.25,5.5,6.25,7.75] if args.strict_hold else [5.5,6.25,7.75]):
        for flight in [0.0,0.5,1.0,2.0,4.0]:
            q=subprocess.run(['C:/msys64/ucrt64/bin/vvp.exe',str(image),f'+PHASE={phase}',f'+FLIGHT={flight}'],
                             env=env,capture_output=True,text=True,timeout=15)
            log=q.stdout+q.stderr
            name=f'tac{tac}-delay{read_delay}-phase{phase}-flight{flight}.log'
            (out/name).write_text(log)
            result=next((s for s in log.splitlines() if s.startswith('ALIGN_RESULT ')),None)
            assert q.returncode==0 and result,log
            row=dict(tac=tac,read_delay=read_delay,phase=phase,flight=flight,log=name)
            for token in result.split()[1:]:
                key,value=token.split('=')
                if key.endswith('errors') or key in ['writes','refreshes']:row[key]=int(value)
            rows.append(row)
    print('TIMING_CASES_COMPLETE tac',tac,flush=True)
summary=dict(scope='Native-pad functional timing sensitivity, not measured board timing or routed qualification',
             strict_hold=args.strict_hold, hold_ns=0.5 if args.strict_hold else None,
             posedge_retime=args.posedge_retime,
             SIMULATION_define=False,hardware_modified=False,
             sources={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['controller.sv','model.sv','primitives.sv','tb.sv']},
             cases=rows)
(out/'results.json').write_text(json.dumps(summary,indent=2)+'\n')
print('ALIGNMENT_SWEEP_COMPLETE',len(rows),'cases',flush=True)
