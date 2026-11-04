#!/usr/bin/env python3
"""Export selected vectors to 32-bit two's-complement readmemh files for RTL."""
import argparse,json
from pathlib import Path
from acceptance import load_array
HERE=Path(__file__).resolve().parent

def export(dataset,start,count,outdir):
    index=json.loads((HERE/'golden-index.json').read_text());row=next(r for r in index['datasets'] if r['name']==dataset)
    if type(start)is not int or type(count)is not int or start<0 or not 1<=count<=256 or start+count>row['blocks']:raise ValueError('bounded vector slice')
    outdir=Path(outdir);outdir.mkdir(parents=True,exist_ok=True)
    for kind in ('dequantized','residual'):
        a=load_array(row['arrays'][kind])[start:start+count]
        (outdir/(kind+'.mem')).write_text(''.join(f'{int(v)&0xffffffff:08x}\n' for v in a.flat))
    meta=dict(dataset=dataset,start_block=start,blocks=count,words_per_block=64,word_bits=32,order='block then row then column',signed=True,encoding='two-complement hexadecimal',source_index_sha256=__import__('hashlib').sha256((HERE/'golden-index.json').read_bytes()).hexdigest())
    (outdir/'slice.json').write_text(json.dumps(meta,indent=2)+'\n');return meta

def main():
    p=argparse.ArgumentParser();p.add_argument('--dataset',default='actual-ar03');p.add_argument('--start',type=int,default=0);p.add_argument('--count',type=int,default=8);p.add_argument('--outdir',type=Path,required=True);a=p.parse_args()
    print(json.dumps(export(a.dataset,a.start,a.count,a.outdir)))
if __name__=='__main__':main()
