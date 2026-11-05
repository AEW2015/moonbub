"""Validate executed result matrices, including required failing controls."""
from pathlib import Path
import json,re
root=Path(__file__).resolve().parents[1]
cases=[]
for version,count in [('v001',45),('v002',225),('v003',225)]:
    path=root/f'evidence/cpl1-sdram-alignment-20261105-{version}/results.json'
    if not path.exists():path=root/f'evidence/cpl1-sdram-alignment-public-20261105/{version}-results.json'
    result=json.loads(path.read_text())
    rows=result['cases'];assert len(rows)==count
    assert all(x['write_errors']==0 and x['writes']==96 and x['refreshes']>=3 for x in rows)
    if version=='v003':
        selected=[x for x in rows if x['phase']==3.75 and x['read_delay']==5]
        assert len(selected)==15 and all(x['read_errors']==0 for x in selected)
    negative=[x for x in rows if x['phase']==7.75 and x.get('read_delay',5)==5 and x['tac']==2 and x['flight']==0]
    assert len(negative)==1 and negative[0]['preload_errors']==48
    cases.extend(rows)
# Match the tested retiming behavior to actual isolated product RTL.
package=root/'fpga/exports/cpl1-timing-fsmcopy-source-20261105-v002'
candidate=root/'fpga/candidates/cp23-sdram-capture135-20261105-v001'
strip=lambda s:re.sub(r'\s+','',re.sub(r'//[^\n]*','',s))
name='core/parents/moonshine_sdram_burst.sv'
parent=(package/'inputs'/name).read_text()
changed=(candidate/'inputs'/name).read_text()
assert strip(changed)==strip(parent.replace('always @(negedge clk)dq_retime<=dq_capture;',
                                           'always @(posedge clk)dq_retime<=dq_capture;'))
name='rtl/moonshine_top_cpl1.sv'
assert strip((candidate/'inputs'/name).read_text())==strip((package/'inputs'/name).read_text().replace('.CLKOUT2_PHASE(279.0)','.CLKOUT2_PHASE(135.0)'))
print('ALIGNMENT_EVIDENCE_PASS cases=495 zero_write_errors=1 required_bad_phase_detected=1 candidate_pairs=15/15 product_delta_checked=1')
