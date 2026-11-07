#!/usr/bin/env python3
"""Verify lossless chunk order, complete raw stream hashes and terminal verdicts."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent

def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def main():
    alias=json.loads((ROOT/'fpga/experiments/cu66-v91l-overlap-live/results.json').read_text());p=ROOT/alias['selected_report'];report=json.loads(p.read_text())
    assert alias==dict(report,selected_report=str(p.relative_to(ROOT))) and len(report['modes'])==5
    modes=[]
    for mode in report['modes']:
        log='pins-seed'+str(mode['seed'])+'-tac'+str(mode['t_ac_ns'])+('-guard' if mode['guard_mode'] else '')+'.jsonl'
        receipt=report['compressed_artifacts'][log];chunks=receipt['chunks']
        assert mode['pin_logs']==[c['path'] for c in chunks]
        whole=hashlib.sha256();total=rows=0;verdicts=[];carry=b''
        for chunk in chunks:
            path=p.parent/chunk['path'];assert sha(path)==chunk['gzip_sha256']
            digest=hashlib.sha256();size=lines=0
            with gzip.open(path,'rb') as stream:
                for b in iter(lambda:stream.read(1<<20),b''):
                    whole.update(b);digest.update(b);size+=len(b);lines+=b.count(b'\n');raw=carry+b;at=raw.rfind(b'\n')
                    if at>=0:
                        for line in raw[:at+1].splitlines():
                            if b'"type":"verdict"' in line or b'"type": "verdict"' in line:verdicts.append(json.loads(line))
                        carry=raw[at+1:]
                    else:carry=raw
            assert digest.hexdigest()==chunk['raw_sha256'] and size==chunk['raw_bytes'] and lines==chunk['rows']
            assert not carry,'chunk boundary splits a JSONL record'
            total+=size;rows+=lines
        assert whole.hexdigest()==receipt['raw_sha256'] and total==receipt['raw_bytes'] and rows==receipt['rows']
        assert len(verdicts)==1 and verdicts[0]==mode['verdict'] and verdicts[0]['status']=='TEST_PASS'
        assert verdicts[0]['seed']==mode['seed'] and bool(verdicts[0]['guard_mode'])==mode['guard_mode']
        modes.append(dict(seed=mode['seed'],t_ac_ns=mode['t_ac_ns'],guard_mode=mode['guard_mode'],chunks=len(chunks),raw_sha256=whole.hexdigest(),raw_bytes=total,rows=rows,terminal_verdict=verdicts[0]))
    result=dict(status='PASS_LOSSLESS_CHUNKS_AND_RAW_TERMINAL_VERDICTS',report=str(p.relative_to(ROOT)),report_sha256=sha(p),verifier_sha256=sha(Path(__file__)),modes=modes)
    (HERE/'stream-audit.json').write_text(json.dumps(result,indent=2)+'\n');print(result['status'])
if __name__=='__main__':main()
