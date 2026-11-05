#!/usr/bin/env python3
"""Reconcile retained display evidence without changing producer pins."""
import hashlib
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    checked=0
    for f,h in json.loads((HERE/'baseline-files.json').read_text())['files_sha256'].items():
        assert sha(ROOT/f)==h,('baselinechanged',f)
        checked+=1
    result={}
    for name in ['results.json','strip-results.json','strip-control-results.json']:
        p=HERE/name;d=json.loads(p.read_text());assert d['status']=='PASS'
        for f,h in d['source_sha256'].items():
            assert sha(ROOT/f)==h,('stalesource',f)
            checked+=1
        for c in d['commands']:
            assert c['exit_code']==0 and sha(ROOT/c['log'])==c['sha256'],('staleorfailedcommand',c)
            checked+=1
        result[name]=d
    base=result['results.json'];assert len(base['painter'])==3 and sum(r['full_physical_rasters']for r in base['painter'])==39
    assert all(r['actual_key_P_frames']==8 and r['patterns']==4 and r['recovery']==1 and r['full_raster_words']==384000 for r in base['painter'])
    assert len(base['scanout'])==4 and sum(r['compared_pixels']for r in base['scanout'])==3072000
    for r in base['scanout']:
        assert r['complete_frames']==r['descriptors_presented']==2 and r['stale_rejections']==1
        assert r['underruns']==r['black_lines']
        assert (r['black_lines']>0)==r['starvation']
    strip=result['strip-results.json'];assert len(strip['runs'])==4
    for r in strip['runs']:
        assert len(r['per_frame'])==r['full_rasters']==13
        for f in r['per_frame']:
            assert f['painted']==345600 and f['write_words']==384000 and f['read_words']==280320 and f['error']==0
            assert f['canvas_runs']==(43200 if r['variant']=='strip'else 345600)
            assert f['aligned8_runs']==(43200 if r['variant']=='strip'else 0)
    # Independently check directed faults and terminal markers in final logs.
    for c in base['commands']+strip['commands']:
        if '/Vcu70_painter'in ' '.join(c['argv']):
            text=(ROOT/c['log']).read_text();rows=[dict((k,int(v))for k,v in re.findall(r'(\w+)=(\d+)',s))for s in text.splitlines()if s.startswith('CASE_PASS')]
            assert 'PASS actual_frames=8 patterns=4 recovery=1'in text and'FAIL'not in text
            mode={r['mode']:r for r in rows if r['mode']}
            if mode:
                assert set(mode)=={1,2,3,4,5}
                assert all(mode[m]['error']==(2 if m in (3,4)else 0)for m in mode)
    for c in result['strip-control-results.json']['commands']:
        if c['log'].endswith(('final-iverilog.log','final-verilator.log')):
            assert 'TEST_PASS_STRIP_CONTROL'in (ROOT/c['log']).read_text()
    report={'status':'PASS','declared_hash_checks':checked,'baseline_rasters':39,'comparison_rasters':52,
            'total_painter_words_compared':34944000,'scanout_frames':8,'scanout_pixels_compared':3072000,
            'intentional_starvation_black_lines':sum(r['black_lines']for r in base['scanout']),
            'dirty_strip_control_backends':2,'verifier_sha256':sha(Path(__file__).resolve()),
            'scope':'functionalcomponents+addresslocality; notfullcontrollerintegration,targetfit,CDCsignofforphysicalfps'}
    (HERE/'display-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
