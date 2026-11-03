#!/usr/bin/env python3
"""Verify RTL entropy bytes vs a marker/byte-stuffing oracle, across stalls."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


def entropy_bytes(jpeg):
    if jpeg[:2] != b'\xff\xd8': raise ValueError('missing SOI')
    pos=2
    while pos<len(jpeg):
        if jpeg[pos]!=0xff: raise ValueError('bad marker prefix')
        while pos<len(jpeg) and jpeg[pos]==0xff: pos+=1
        if pos>=len(jpeg): raise ValueError('truncated marker')
        marker=jpeg[pos];pos+=1
        if marker in (0xd8,0xd9) or 0xd0<=marker<=0xd7: raise ValueError('unexpected standalone marker')
        if pos+2>len(jpeg): raise ValueError('truncated marker length')
        length=int.from_bytes(jpeg[pos:pos+2],'big')
        if length<2 or pos+length>len(jpeg): raise ValueError('invalid segment length')
        pos+=length
        if marker==0xda: break
    else: raise ValueError('missing SOS')
    out=bytearray()
    while pos<len(jpeg):
        b=jpeg[pos];pos+=1
        if b!=0xff: out.append(b);continue
        if pos==len(jpeg): raise ValueError('truncated scan marker')
        tag=jpeg[pos];pos+=1
        if tag==0x00: out.append(0xff)
        elif tag==0xd9:
            if pos!=len(jpeg): raise ValueError('bytes after EOI')
            return bytes(out)
        else: raise ValueError(f'unsupported marker in scan: ff{tag:02x}')
    raise ValueError('missing EOI')


def main():
    a=argparse.ArgumentParser(description=__doc__)
    a.add_argument('--sim',type=Path,required=True)
    a.add_argument('--fixtures',type=Path,required=True)
    a.add_argument('--frames',type=int,default=10)
    a.add_argument('--seeds',type=int,default=30)
    a.add_argument('--output',type=Path,required=True)
    ns=a.parse_args(); sim=ns.sim.resolve(); fixtures=ns.fixtures.resolve()
    if ns.frames<1 or ns.seeds<1: a.error('positive frames and seeds required')
    summary={'scope':'jpeg_input entropy output only; deterministic invalid-source marker noise and xorshift output stalls; not full JPEG decode/FPS',
             'simulator_binary_sha256':hashlib.sha256(sim.read_bytes()).hexdigest(),
             'seeds':ns.seeds,'fixtures':[],'checks':0}
    with tempfile.TemporaryDirectory(prefix='jpeg-entropy-stress-') as td:
        result=Path(td)/'entropy.bin'
        for frame in range(ns.frames):
            fixture=fixtures/f'{frame:04d}.jpg';data=fixture.read_bytes();expected=entropy_bytes(data)
            for seed in range(1,ns.seeds+1):
                run=subprocess.run([str(sim),f'+JPEG_FILE={fixture}',f'+OUT_FILE={result}','+RANDOM=1','+NOISE_GAPS=1',f'+SEED={seed}'],
                                   capture_output=True,text=True,timeout=30)
                if run.returncode or 'TEST_PASS_ENTROPY' not in run.stdout:
                    raise RuntimeError(f'RTL failure frame={frame} seed={seed} return={run.returncode}\n{run.stdout}\n{run.stderr}')
                actual=result.read_bytes()
                if actual!=expected:
                    raise ValueError(f'entropy mismatch frame={frame} seed={seed} expected={len(expected)} actual={len(actual)}')
                summary['checks']+=1
            summary['fixtures'].append({'frame':frame,'jpeg_sha256':hashlib.sha256(data).hexdigest(),
                'entropy_bytes':len(expected),'entropy_sha256':hashlib.sha256(expected).hexdigest()})
            print(f'frame {frame}: {ns.seeds} seeded byte-identical entropy streams',flush=True)
    ns.output.write_text(json.dumps(summary,indent=2)+'\n')
    print(f"TEST_PASS_ENTROPY_ORACLE checks={summary['checks']}")
if __name__=='__main__': main()
