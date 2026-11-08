#!/usr/bin/env python3
"""Independent full32 geometry replay and byte/correction-table provenance audit."""
import gzip,hashlib,itertools,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v106/context';FPGA=ROOT/'fpga/experiments/cu66-v106-context'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def expected_records():
    edges=(0,1,4,5,14,15,42,43,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff)
    for b,d in ((1,5),(2,15),(3,43)):
        for n in range(65536*d+1):yield b,n,0,'valid'
        for n in edges:yield b,n,n^0xffffffff,'edge'
    for b,d in ((1,5),(2,15),(3,43)):
        for target in (d-1,d,2*d-1,2*d,3*d-1,3*d,4*(d-1)):
            n=0;remaining=target
            for i in range(4):
                residue=min(remaining,d-1);remaining-=residue
                v=next(v for v in range(256) if (v<<(8*i))%d==residue)
                n|=v<<(8*i)
            assert remaining==0
            yield b,n,0,'edge'
    rng=1068001;mask=(1<<64)-1
    for i in range(131072):
        rng=(rng^(rng<<13))&mask;rng^=rng>>7;rng=(rng^(rng<<17))&mask;n=rng&0xffffffff
        rng=(rng^(rng<<13))&mask;rng^=rng>>7;rng=(rng^(rng<<17))&mask;e=rng&0xffffffff
        yield i%3+1,n,e,'random'
    for b in (0,*range(4,256)):
        for n in (0,1,0x80000000,0xffffffff):yield b,n,n^0xffffffff,'default'

def main():
    sp=AREA/'results.json';summary=json.loads(sp.read_text());rp=ROOT/summary['selected_report'];r=json.loads(rp.read_text())
    assert summary['status']==r['status']=='PASS' and {k:v for k,v in summary.items() if k!='selected_report'}==r
    assert r['actual_RTL_run'] and r['strict_warnings'] and not r['assertions_disabled_or_downgraded'] and r['frozen_after_focused_PASS']
    for path,pin in r['source_sha256'].items():assert sha(ROOT/path)==pin
    for path,pin in r['artifacts_sha256'].items():assert sha(rp.parent/path)==pin
    recipe_path=FPGA/'edit-recipe.json';recipe=json.loads(recipe_path.read_text());original=ROOT/recipe['original_path'];candidate=ROOT/recipe['candidate_path']
    assert recipe['schema']=='v106-edit-recipe-v1' and len(recipe['edits'])==2 and sha(original)==recipe['original_sha256']
    text=original.read_text()
    for e in recipe['edits']:
        assert text.count(e['before'])==e['expected_occurrences']==1;text=text.replace(e['before'],e['after'],1)
    assert text==candidate.read_text() and sha(candidate)==recipe['candidate_sha256']==r['candidate']['sha256']
    assert sha(recipe_path)==r['candidate']['recipe_sha256']
    adapter=json.loads((FPGA/'adapter.json').read_text())
    for name,source in [('original',original),('candidate',candidate)]:
        text=(FPGA/('context_'+name+'.sv')).read_text().replace('module context_'+name+' (','module br88_context (',1)
        assert text.replace(adapter['extra_ports'],'\n);',1).replace(adapter['assignments'],'',1)==source.read_text()
    h=json.loads((FPGA/'helpers.json').read_text());helper=h['helpers'];assert helper in candidate.read_text() and helper in (FPGA/'context_probe.sv').read_text()
    assert h['ZIGZAG'] in original.read_text() and h['ZIGZAG'] in candidate.read_text()
    zz=list(map(int,re.findall(r"6'd(\d+)",h['ZIGZAG'])));assert len(zz)==64 and sorted(zz)==list(range(64))
    byte_tables={}
    for key,body in re.findall(r"4'd(\d+):begin(.*?)endcase",helper,re.S):
        b,i=divmod(int(key),4);values={int(v):int(pair,16) for v,pair in re.findall(r"8'd(\d+):return 22'h([0-9a-f]{6});",body)}
        assert b in (1,2,3) and (b,i) not in byte_tables and set(values)==set(range(256))
        divisor=(5,15,43)[b-1]
        for value,pair in values.items():
            q,rem=divmod(value<<(8*i),divisor);assert pair==((q%65536)<<6)|rem
        byte_tables[b,i]=values
    assert len(byte_tables)==12
    correction={}
    for band,body in re.findall(r"2'd(\d+):begin(.*?)endcase",helper,re.S):
        values={int(total):(int(q)<<6)|zz[int(index)] for total,q,index in re.findall(r"8'd(\d+):return \{2'd(\d+),ZIGZAG\[6'd(\d+)\]\};",body)}
        if not values:continue
        b=int(band);divisor=(5,15,43)[b-1];offset=(1,6,21)[b-1]
        assert set(values)==set(range(256)) and b not in correction
        for total,pair in values.items():assert pair==(((total//divisor)%4)<<6)|zz[offset+total%divisor]
        correction[b]=values
    assert len(correction)==3
    # Closed local identity used in the fixed-width carry-save quotient/remainder sums.
    for a,b,c in itertools.product((0,1),repeat=3):assert a+b+c==(a^b^c)+2*((a&b)|(a&c)|(b&c))
    digest=hashlib.sha256();trace=rp.parent/'geometry.tsv.gz';rows=0;bands=set();coverage=dict(valid=0,edge=0,random=0,default=0);expected_stream=iter(expected_records())
    # Direct integer division and the original raster permutation, independent of lookup machinery.
    with gzip.open(trace,'rb') as f:
        for line in f:
            b,n,e,old,new=map(int,line.split());assert b in range(256) and 0<=n<2**32 and 0<=e<2**32
            eb,en,ee,kind=next(expected_stream);assert (b,n,e)==(eb,en,ee);coverage[kind]+=1
            if b in (1,2,3):
                divisor=(5,15,43)[b-1];offset=(1,6,21)[b-1];q,rem=divmod(n,divisor)
                expected=((q%65536)<<6)|zz[offset+rem]
            else:expected=(e%65536)<<6
            assert old==new==expected
            digest.update(line);rows+=1;bands.add(b)
    assert next(expected_stream,None) is None
    assert coverage==dict(valid=4128771,edge=63,random=131072,default=1012)
    assert rows==r['model']['rows']==r['trace_replay']['rows']==4260918 and bands==set(range(256))
    assert digest.hexdigest()==r['raw_trace_sha256']==r['trace_replay']['raw_sha256']==r['model']['raw_geometry_trace_sha256']
    assert r['geometry_verdict']==dict(type='geometry_verdict',status='TEST_PASS',cases=4260918,valid_domain_cases=4128771,random_full32_cases=131072)
    assert r['terminal_verdict']==dict(type='verdict',status='TEST_PASS',cases=55,outputs_per_configuration=84265,configurations=8,directed_checks=172,seed=1068001)
    assert r['model']['coverage']==dict(valid=4128771,edge=63,random=131072,default=1012)
    assert r['model']['byte_constants_checked']==3072 and r['model']['correction_index_constants_checked']==768
    assert r['model']['max_remainder_sum']==r['model']['theoretical_remainder_sum_bound']==168
    cmd=next(c['argv'] for c in r['commands'] if '--cc' in c['argv'])
    assert '--assert' in cmd and '-Wall' in cmd and '-std=c++17 -O2 -Wall -Wextra -Werror' in cmd and '300s' in cmd and '--kill-after=5s' in cmd and cmd[cmd.index('-j')+1]=='2'
    assert 'Verilator 5.020' in (rp.parent/'verilator.log').read_text() and '%Warning-' not in (rp.parent/'compile.log').read_text()
    result=dict(schema='v106-context-independent-trace-audit-v1',status='PASS',
        auditor=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=sha(Path(__file__))),
        selected_receipt=dict(path=str(rp.relative_to(ROOT)),sha256=sha(rp)),selected_summary=dict(path=str(sp.relative_to(ROOT)),sha256=sha(sp)),
        trace_sha256=sha(trace),raw_trace_sha256=digest.hexdigest(),candidate=r['candidate'],rows=rows,coverage=coverage,
        byte_constants_checked=3072,correction_index_constants_checked=768,all_band_values_covered=len(bands),
        valid_domain_cases=4128771,random_full32_cases=131072,edge_cases=63,default_cases=1012,
        contexts=55,profiles=8,outputs_per_profile=84265,directed_checks=172,
        limits=['Universal algebra and exhaustive byte/correction constants; deterministic full32 tests are not exhaustive over2^32 positions or four-state values.',
            'Combined correction-table high addresses are unreachable from the proved byte-remainder sum bound; no unrestricted helper-domain claim.',
            'No routed timing closure, hardware FPS or complete decode latency qualification.'])
    (AREA/'trace-audit.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print('V106_CONTEXT_TRACE_AUDIT PASS',rows)
if __name__=='__main__':main()
