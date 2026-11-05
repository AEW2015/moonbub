#!/usr/bin/env python3
"""Finite Yosys SAT safety and reachable-state checks, never unbounded proof."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')
DUT=ROOT/'fpga/experiments/cu66-v69/banks/cu66_frame_bank_control.sv'
HARNESS=HERE/'cu70_bank_formal.sv'
AS_LIMIT=1610612736


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    began=time.monotonic();commands=[];runs=[]
    source={str(p.relative_to(ROOT)):sha(p)for p in [DUT,HARNESS,Path(__file__).resolve()]}
    with (HERE/'tool-version.log').open('w')as out:
        subprocess.run(['docker','exec',CONTAINER,'yosys','-V'],stdout=out,stderr=subprocess.STDOUT,check=True,timeout=5)
    tool=(HERE/'tool-version.log').read_text().strip()
    preamble=f'read_verilog -formal -sv {DUT} {HARNESS}\nprep -top cu70_bank_formal -flatten\ncheck\n'
    status='PASS_BOUNDED'
    try:
        jobs=[('proof',n,None)for n in (8,16,24)]
        jobs += [('reachability',16,signal)for signal in ('cover_active','cover_read','cover_pending','cover_front','cover_abort_and_present')]
        for kind,bound,cover in jobs:
            remaining=115-(time.monotonic()-began)
            if remaining<5:raise TimeoutError('total115secondbudget')
            wall=min(28,int(remaining)-2);solver=max(1,wall-4)
            name=f'{kind}-{cover or "all"}-{bound}'
            constraints=f'-seq {bound} -set-def-inputs -set-init-def -set rst 0 -set-at 1 rst 1'
            goal='-prove-asserts -verify'if kind=='proof'else f'-set-at {bound} {cover} 1 -show-ports'
            wave=HERE/(name+'.vcd')
            script=HERE/(name+'.ys')
            script.write_text(preamble+f'sat {constraints} {goal} -timeout {solver} -dump_vcd {wave}\n')
            argv=['docker','exec',CONTAINER,'timeout','--signal=TERM','--kill-after=2s',f'{wall}s','prlimit',f'--as={AS_LIMIT}','yosys','-Q','-s',str(script)]
            log=HERE/(name+'.log');started=time.monotonic()
            with log.open('w')as out:r=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=subprocess.STDOUT,timeout=wall+3)
            elapsed=time.monotonic()-started;text=log.read_text()
            command={'argv':argv,'exit_code':r.returncode,'elapsed_seconds':elapsed,'script':str(script.relative_to(ROOT)),'script_sha256':sha(script),'log':str(log.relative_to(ROOT)),'log_sha256':sha(log)}
            commands.append(command)
            if r.returncode or 'ERROR:'in text:raise RuntimeError(f'{name}: exit{r.returncode}')
            if not re.search(r'^\s+\$assert\s+16\s*$',text,re.M):raise RuntimeError('all16assertionsmustremainelaborated')
            marker='SAT proof finished - no model found: SUCCESS!'if kind=='proof'else'SAT solving finished - model found:'
            if marker not in text:raise RuntimeError(f'{name}: missing explicit required marker')
            if kind=='reachability'and not wave.is_file():raise RuntimeError('missing actual SAT witness waveform')
            peak=re.search(r'MEM: ([0-9.]+) MB peak',text)
            row={'kind':kind,'solver_steps':bound,'assertions_elaborated':16,'cover_signal':cover,'status':'PASS_BOUNDED'if kind=='proof'else'REACHABLE','elapsed_seconds':elapsed,'peak_memory_MB':float(peak[1])if peak else None}
            if kind=='reachability':row.update(witness=str(wave.relative_to(ROOT)),witness_sha256=sha(wave))
            runs.append(row)
            print(json.dumps(row),flush=True)
    except (RuntimeError,TimeoutError,subprocess.TimeoutExpired)as exc:
        status='INCONCLUSIVE_OR_FAILED'
        print(f'FORMAL_NOT_PASS {exc}',flush=True)
    if source!={str(p.relative_to(ROOT)):sha(p)for p in [DUT,HARNESS,Path(__file__).resolve()]}:
        status='INCONCLUSIVE_OR_FAILED'
    result={'status':status,'backend':tool,'source_sha256':source,'runs':runs,'commands':commands,
            'assumptions':['rst=1 at solverstep1,rst=0 at allsubsequentsteps','allmoduleinputbitsdefined but otherwise symbolic','past_validinitialized0 todisableclockedchecks beforefirstresetedge','otherinitialregistersdefinedsymbolic,notassumedzero'],
            'bounds_interpretation':'8/16/24SATsolverstates. Clockedassertionshaveonestepobserverlatency: safetychecksforDUTstatesbeforelastsamplingedge; resetstateandallpriorunrolledtransitionschecked. Notaninductiveorunboundedproof.',
            'assertion_groups':{'P01-P05':'livebankranges0..2','P06-P08':'activewritebankexcludesreference/front/pending','P09':'readleaserequiresactivewriter','P10':'pending/frontdifferwhenbothvalid','P11':'readbanknotactivewritebank','P12':'abortingrequiresactivelease','P13-P16':'previousabortmustpreserveacceptedcount/refvalid/refbank/refid;independentpresentationallowed'},
            'resource_limits':{'total_runner_seconds':115,'per_process_wall_seconds_max':28,'per_process_address_space_bytes':AS_LIMIT},
            'elapsed_seconds':time.monotonic()-began,
            'not_proven':['unboundedbankcorrectness','livenessorfairness','receiver/HUD/memorydatapathintegration','CDC/resetdomaincrossings','physicaltiming/performance']}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    if status!='PASS_BOUNDED':raise SystemExit(1)
    assert len(runs)==8
    print('BOUNDED_BANK_SAFETY_PASS bounds=8,16,24 assertions=16 reachable_witnesses=5 no_unbounded_or_liveness_claim',flush=True)


if __name__=='__main__':main()
