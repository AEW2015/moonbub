#!/usr/bin/env python3
"""Read retained matched unit synthesis reports without adding timing qualification."""
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];AREA=ROOT/'experiments/python-gamebub-v106/idct-area'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    reports=sorted((AREA/'native').glob('*/receipt.json'));assert reports
    rp=reports[-1];r=json.loads(rp.read_text());assert r['status']=='SYNTHESIS_ONLY_FINISHED_SIGNOFF_OPEN' and r['observed_exit_code']==0 and r['source_snapshot_unchanged']
    inputs=json.loads((rp.parent/'inputs.json').read_text());build=Path(r['build_external']);assert sha(rp.parent/'inputs.json')==r['source_manifest_sha256']
    for name,artifact in r['artifacts'].items():
        p=rp.parent/'reports'/name
        if p.is_file():assert sha(p)==artifact['sha256']
    for p,h in inputs['source_sha256'].items():assert sha(build/'snapshot'/p)==h
    for p,v in inputs['source_origins'].items():assert sha(ROOT/v['path'])==v['sha256']
    assert r['top']=='cu66_idct8x8' and r['part']=='xc7a100tcsg324-1' and r['clock_period_ns']==10 and r['max_threads']==2 and r['memory_limit_bytes']==8*1024**3
    assert r['tools_readonly'] and r['existing_legitimate_license_readonly'] and not r['hostid_or_MAC_changed'] and not r['bitstream_generated']
    variants={}
    for name in ('original','prefetch','shared'):
        p=rp.parent/'reports'/f'{name}-utilization.rpt';s=p.read_text();entries={}
        for line in s.splitlines():
            parts=[x.strip() for x in line.split('|')]
            if len(parts)>3 and parts[2].isdigit():entries[parts[1].rstrip('*')]=int(parts[2])
        setup=rp.parent/'reports'/f'{name}-setup-paths.rpt';t=setup.read_text();slack=re.search(r'Slack\s*\([^)]*\)\s*:\s*(-?[\d.]+)ns',t);assert slack
        variants[name]={'synthesis_slice_LUTs':entries['Slice LUTs'],'synthesis_LUT_as_Logic':entries['LUT as Logic'],'synthesis_LUT_as_Memory':entries['LUT as Memory'],'synthesis_slice_registers':entries['Slice Registers'],'synthesis_DSPs':entries['DSPs'],'synthesis_estimated_worst_slack_ns':float(slack.group(1)),'worst_source':re.search(r'Source:\s+([^\n]+)',t).group(1).strip(),'worst_destination':re.search(r'Destination:\s+([^\n]+)',t).group(1).strip(),'synthesis_data_path_delay_ns':float(re.search(r'Data Path Delay:\s+([\d.]+)ns',t).group(1)),'source':inputs['source_origins'][name+'/cu66_idct8x8.sv'],'reports':{str(x.relative_to(ROOT)):sha(x) for x in (p,setup,rp.parent/'reports'/f'{name}-dsp-registers.tsv')}}
    v=variants;out={'schema':'v106-idct-area-matched-unit-synthesis-comparison-v1','status':'UNIT_SYNTHESIS_EVIDENCE_COMPLETE','selected_receipt':{'path':str(rp.relative_to(ROOT)),'sha256':sha(rp)},'analyzer':{'path':str(Path(__file__).relative_to(ROOT)),'sha256':sha(Path(__file__))},'variants':v,'shared_minus_original_LUTs':v['shared']['synthesis_slice_LUTs']-v['original']['synthesis_slice_LUTs'],'shared_minus_prefetch_LUTs':v['shared']['synthesis_slice_LUTs']-v['prefetch']['synthesis_slice_LUTs'],'shared_to_original_LUT_ratio':v['shared']['synthesis_slice_LUTs']/v['original']['synthesis_slice_LUTs'],'clock_period_ns':10.0,'part':r['part'],'top':r['top'],'all_settings_matched':True,'limits':['Synthesis-only estimated timing and unit mapped cell attribution; not placement/routing or complete-top resource-fit proof.','External input/output arrival/required timing remains open.','Native fifth full candidate placement failed; no prior failed evidence is replaced by unit results.']}
    (AREA/'unit-synthesis-comparison.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('variants','limits')},indent=2));print(json.dumps(variants,indent=2))
if __name__=='__main__':main()
