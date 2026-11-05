#!/usr/bin/env python3
"""Finite, source-pinned functional presentation/scanout RTL qualification."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
CONTAINER=os.environ.get('TASK_CONTAINER','gamebub-cu66-v69-build')


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    native=ROOT/'experiments/cu66-native-v69'
    source=[*HERE.glob('*.sv'),*HERE.glob('*.cpp'),Path(__file__).resolve(),
            *native.glob('*.hpp'),native/'index.tsv',*sorted((native/'fixtures').glob('*.cu66')),
            ROOT/'fpga/rtl/moonshine_lcd.sv']
    before={str(p.relative_to(ROOT)):sha(p)for p in source}
    commands=[]
    def run(argv,name,timeout=300):
        log=HERE/name
        with log.open('w')as f:proc=subprocess.run(argv,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
        commands.append({'argv':argv,'exit_code':proc.returncode,'log':str(log.relative_to(ROOT)),'sha256':sha(log)})
        if proc.returncode:raise RuntimeError(f'{name}: exit {proc.returncode}; inspect retained log')
        return log.read_text()
    for top,files,tb in [('cu70_painter',['cu70_painter.sv'],'tb_painter.cpp'),
                         ('cu70_scanout',['cu70_scanout.sv','cu70_lcd_lines.sv'],'tb_scanout.cpp')]:
        run(['docker','exec',CONTAINER,'verilator','--cc','--exe','--build','-j','2','--Wall',
             '--top-module',top,'--Mdir',f'/build/v70-display-{top}','-CFLAGS','-O2 -std=c++17',
             *[str(HERE/f)for f in files],str(HERE/tb)],f'build-final-{top}.log',600)
    painter=[]
    for seed in [0,7001,7002]:
        log=run(['docker','exec',CONTAINER,'/build/v70-display-cu70_painter/Vcu70_painter',str(native/'index.tsv'),str(seed)],f'painter-final-seed{seed}.log',600)
        assert re.search(rf'^PASS actual_frames=8 patterns=4 recovery=1 fault_probes={5 if seed else 0} seed={seed}$',log,re.M)and'FAIL'not in log
        rows=[dict((k,int(v))for k,v in re.findall(r'(\w+)=(\d+)',line))for line in log.splitlines()if line.startswith('CASE_PASS')]
        good=[x for x in rows if x['mode']==0]
        assert len(good)==13 and all(x['read_words']==280320 and x['write_words']==384000 and x['painted']==345600 and x['error']==0 for x in good)
        painter.append({'seed':seed,'actual_key_P_frames':8,'patterns':4,'recovery':1,'fault_probes':5 if seed else 0,'full_physical_rasters':13,'full_raster_words':384000,'min_cycles':min(x['cycles']for x in good),'max_cycles':max(x['cycles']for x in good),'mean_cycles':sum(x['cycles']for x in good)/len(good)})
    scanout=[]
    for seed,starve in [(0,False),(7003,False),(7004,False),(7003,True)]:
        log=run(['docker','exec',CONTAINER,'/build/v70-display-cu70_scanout/Vcu70_scanout',str(seed),*(['--starve']if starve else[])],f'scanout-final-seed{seed}{"-starve"if starve else""}.log')
        assert f'PASS seed={seed} asynchronous_clocks_ns=10,36' in log and 'TEST_PASS_SCANOUT'in log and 'FAIL'not in log
        line=next(s for s in log.splitlines()if s.startswith('TEST_PASS_SCANOUT'))
        counts={k:int(v)for k,v in re.findall(r'(\w+)=(\d+)',line)}
        assert counts['compared_pixels']==768000 and counts['complete_frames']==2 and counts['descriptors_presented']==2 and counts['stale_rejections']==1
        assert (counts['underruns']==counts['black_lines']>0)if starve else(counts['underruns']==counts['black_lines']==0)
        scanout.append({'seed':seed,'starvation':starve,**counts})
    control=[str(HERE/'cu70_painter.sv'),str(HERE/'tb_painter_control.sv')]
    run(['docker','exec',CONTAINER,'iverilog','-g2012','-s','tb_painter_control','-o','/build/v70-display-control-final.vvp',*control],'control-iverilog-build.log')
    ilog=run(['docker','exec',CONTAINER,'vvp','/build/v70-display-control-final.vvp'],'control-iverilog.log')
    run(['docker','exec',CONTAINER,'verilator','--binary','--timing','--build','-j','2','--Wall','-Wno-BLKSEQ','--top-module','tb_painter_control','--Mdir','/build/v70-display-control-final',*control],'control-verilator-build.log',600)
    vlog=run(['docker','exec',CONTAINER,'/build/v70-display-control-final/Vtb_painter_control'],'control-verilator.log')
    marker='TEST_PASS_PAINTER_CONTROL topbars=19200 coded_pixels=720 reads=1080 invalid_generation_rejected=1 abort_drained=1'
    assert marker in ilog and marker in vlog and 'FATAL'not in ilog and 'FAIL'not in vlog
    assert before=={str(p.relative_to(ROOT)):sha(p)for p in source},'source mutation during run'
    result={'status':'PASS','source_sha256':before,'commands':commands,'painter':painter,'scanout':scanout,
            'control_backends':['Icarus12','Verilator5.020'],'testbench_style_waiver':'BLKSEQ only for procedural clock/oracle temporaries in tb_painter_control; DUT lint otherwise Wall fatal','storage_bytes':{'Y_row':720,'two_chroma_rows_each_plane':1440,'HUD_cache':16,'total_logical_data':2176},
            'painter_traffic_per_frame':{'canonical_read_words':259200,'HUD_read_words':21120,'RGB_write_words':384000,'total_logical_bytes':1328640},
            'not_proven':['physical performance or30fps','BRAM/DSP fit orFmax','command-accurate SDRAM service inthese scalarbenches','fullreceiver/globalHUDcommit integration','formalCDCsignoff'],
            'scope':'identityfilter;color/HUD/padding/portraitpainter and asynchronousLCDdescriptor/line path, independentcomponenttests'}
    (HERE/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    print('DISPLAY_FUNCTIONAL_PASS painter_full_rasters=39 painter_words=14976000 scanout_complete_frames=8 scanout_pixels=3072000 seeded_fault_probes=10 starvation_lines='+str(scanout[-1]['black_lines']))


if __name__=='__main__':main()
