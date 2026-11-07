#!/usr/bin/env python3
"""Replay live wrapper/bench generators with output writes intercepted."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import runpy
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]
AREA=ROOT/'fpga/experiments/cu66-v91l-reference-live'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    captured={}
    def capture(path,text,*args,**kwargs):
        path=path.resolve();assert path not in captured
        captured[path]=text.encode('utf-8');return len(text)
    scripts=[AREA/'make_wrapper.py',AREA/'make_bench.py']
    with patch.object(Path,'write_text',new=capture),contextlib.redirect_stdout(io.StringIO()):
        for script in scripts:runpy.run_path(str(script),run_name='__main__')
    assert set(captured)=={AREA/'reference_live.sv',AREA/'tb_reference_live.cpp'}
    for path,raw in captured.items():assert path.read_bytes()==raw,str(path)
    inputs=[*scripts,AREA/'bench_extension.inc',ROOT/'fpga/experiments/cu66-v91l-rows/tb_compare.cpp',
            ROOT/'fpga/experiments/cu66-v91l-rows/cs88_rows_v91l.sv',
            ROOT/'fpga/experiments/cu66-v91l-burst-converter/canonical_rgb565_tiled.sv',
            ROOT/'fpga/experiments/cu66-v91l-reference-reader/reference_shared_timed.sv']
    result=dict(schema='cu66-v91l-reference-generation-v1',status='PASS_CAPTURE_ONLY_BYTE_IDENTICAL_GENERATION',
                verifier_sha256=sha(Path(__file__)),source_sha256={str(p.relative_to(ROOT)):sha(p) for p in inputs},
                outputs_sha256={str(p.relative_to(ROOT)):sha(p) for p in captured},
                scope='Only Path.write_text calls intercepted. Both trusted local generators reproduced exact current outputs without rewriting qualified sources; no functional equivalence or physical timing claim.')
    Path(__file__).with_name('generation-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['status'])
if __name__=='__main__':main()
