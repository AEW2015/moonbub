from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/staging-timing';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();comp=d/'comparison-ooc-v001.json';q=json.loads(comp.read_text());assert q['status']=='MATCHED_OOC_COMPLETE_NO_ROUTED_BOARD_QUALIFICATION'
for n,h in q['proofs_sha256'].items():assert sha(r/n)==h,n
functional=d/'safety-v002/qualification-v001.json';f=json.loads(functional.read_text())
for n,h in f['sources_sha256'].items():assert sha(r/n)==h,n
for n,h in f['proofs_sha256'].items():assert sha(r/n)==h,n
o=d/'safety-v002/qualification-ooc-v002.json';assert not o.exists();p={'status':'PASS_FINITE_FUNCTIONAL_AND_MATCHED_UNPLACED_SETUP_IMPROVEMENT_BOARD_GATES_OPEN','sources_sha256':f['sources_sha256'],'functional_qualification_sha256':sha(functional),'comparison_path':comp.relative_to(r).as_posix(),'comparison_sha256':sha(comp),'safe_metrics':q['results']['safe'],'old_held_CE_slack_ns':q['results']['old']['held_enable']['slack_ns'],'safe_held_CE_slack_ns':q['results']['safe']['held_enable']['slack_ns'],'clocks_IO_CDC_matched':True,'routed_board_signoff':False,'global_hold_unplaced_negative':True,'actual_safe_RTL_SDK_native_HUD_coSim':'PENDING','hardware':False,'BIT':False,'source_changes_after_functional_proof':False,'next_gates':['Actual safe RTL SDK/native HUD integration','Full-board constraints object/coverage audit, setup/hold/pulse/DRC/CDC/fit/route','Physical QSPI and bounded volatile hardware test under root-owned release gate']};o.write_text(json.dumps(p,indent=2)+'\n');print(sha(o))
