"""Source-bound CDC candidate handoff; deliberately not a board-release verdict."""
from pathlib import Path
import hashlib,json,re,shutil
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/direct-display';c=d/'cdc';o=c/'handoff02';o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
proofs=['protocol-frozen01','protocol-syncsafe01','protocol-actual01','guard-syncsafe01','error-bundle01','owner-syncsafe01','syncsafe-ooc02'];checks={};artifacts=[]
def artifact(p,role):
 assert p.is_file()and p.stat().st_size>0,p
 artifacts.append(dict(role=role,path=str(p.relative_to(r)).replace('\\','/'),sha256=sha(p)))
for proof in proofs:
 p=c/proof;q=json.loads((p/'result.json').read_text());assert q['status'].startswith('PASS'),(proof,q['status']);artifact(p/'result.json','component_result');artifact(p/'execution.json','execution')
 for f in p.iterdir():
  if f.is_file()and f.stat().st_size>0 and f.suffix in ['.log','.rpt','.tcl','.xdc','.dcp','.txt','.sv','.cpp','.json']:artifact(f,'native_leaf'if proof=='syncsafe-ooc02'else'protocol_evidence')
checks['protocol_and_payload_hold']=dict(status='pass',evidence=str((c/'protocol-actual01/phase9999.log').relative_to(r)).replace('\\','/'))
checks['fixed_window_skip_and_reset']=dict(status='pass',evidence=str((c/'guard-syncsafe01/phase1.log').relative_to(r)).replace('\\','/'))
checks['completion_error_pairing']=dict(status='pass',evidence=str((c/'error-bundle01/phase4999.log').relative_to(r)).replace('\\','/'))
checks['native_pixels_and_owner_abort_fences']=dict(status='pass',evidence=str((c/'owner-syncsafe01/seed7311.log').relative_to(r)).replace('\\','/'))
p=c/'syncsafe-ooc02';log=(p/'vivado.log').read_text();assert 'Path segmentation'not in log;skew=(p/'bus-skew.rpt').read_text();assert [int(n)for n in re.findall(r'Endpoints:\s+(\d+)',skew)]==[10,10,32]
fanout=(p/'first-stage-fanout.txt').read_text().splitlines();assert len(fanout)==6 and all(' ENDPOINTS 'in line and len(line.split(' ENDPOINTS ')[1].split())==1 for line in fanout)
cdc=(p/'cdc-after.rpt').read_text();assert re.search(r'CDC-1\s+Critical\s+2',cdc)and re.search(r'CDC-3\s+Info\s+6',cdc);assert 'request0_reg/C' in cdc and 'request_sync0_reg[0]/D'in cdc
checks['first_stage_only_syncchain']=dict(status='pass',evidence=str((p/'first-stage-fanout.txt').relative_to(r)).replace('\\','/'))
checks['native_exact_endpoint_coverage']=dict(status='pass',evidence=str((p/'exceptions.rpt').relative_to(r)).replace('\\','/'))
checks['native_bus_skew']=dict(status='pass',evidence=str((p/'bus-skew.rpt').relative_to(r)).replace('\\','/'))
timing=(p/'synthesized-timing.rpt').read_text();assert 'All user specified timing constraints are met.'in timing
checks['internal_synthesis_timing']=dict(status='pass',evidence=str((p/'synthesized-timing.rpt').relative_to(r)).replace('\\','/'))
for key in ['new_DY71_board_object_binding','routed_board_timing_and_IO','physical_CDC_MTBF','full_DY71_grouped_receiver_integration']:
 checks[key]=dict(status='incomplete',evidence=str((c/'PLAN.md').relative_to(r)).replace('\\','/'))
original=json.loads((c/'syncsafe-derivation.json').read_text())
for name,h in original['parent_sha256'].items():assert sha(r/name)==h
selected=[c/'cu71_lcd_lines_syncsafe.sv',c/'cu71_direct_scanout_syncsafe.sv',d/'cu71_cache_dma.sv',d/'cu71_direct_cache.sv',d/'cu71_yuv_pixel_pipe.sv'];src={p.name:sha(p)for p in selected}
for name,h in json.loads((c/'syncsafe-ooc02/source-freeze.json').read_text()).items():assert src[name]==h
assert sha(c/'direct_cdc_candidate.tcl')==sha(p/'executed-cdc-constraints.tcl')
extra=[c/'direct_cdc_candidate.tcl',c/'PLAN.md',c/'clock-protocol-derivation.json',c/'syncsafe-derivation.json',Path(__file__)]
for f in selected+extra:
 artifact(f,'rtl'if f.suffix=='.sv'else'constraints'if f.suffix=='.tcl'else'plan')
 target=o/'source-snapshot'/f.relative_to(r);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
for f in (r/'scripts/cu66-v71/direct-display/cdc').iterdir():
 if f.is_file()and f.suffix in ['.py','.tcl']:artifact(f,'rebuild');target=o/'source-snapshot'/f.relative_to(r);target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target)
manifest=dict(overall='INCOMPLETE',component_status='PASS_PROTOCOL_NATIVE_PIXELS_AND_TARGETED_CDC_LEAF_GATES',artifacts=artifacts,checks=checks,selected_candidate='cu71_direct_scanout_syncsafe',source_sha256=src,changes='Functional request stage0 fanout removed; stage1 idle+2quiet clocks; fixed4memclock qualified frame window, skipwhenbusy',ports_changed=False,panel_timing_changed=False,extra_frame_observation_memclocks=4,clock_reference='Existing RGB board/source-v007; exact panel period34.057649667ns, simulator/toolquantization34.058ns; noDY71 boardgenerated',synthesis_slack_ns={'setup':0.255,'hold':0.164,'pulse':4.020},resource=json.loads((p/'primitive-counts.json').read_text()),remaining_manual_CDC={'CDC1':2,'meaning':'Held completed_bad payloads; explicit protocol/latency proof plus targeted delay bounds; not a generic CDC waiver or MTBF result','request_bundles':'CDC15 CE structures','gray_counter':'CDC6 multi-bit recognized synchronizer, one-bit increment asserted'},rejected_timing_attempts={'constraint-report01':'Q-start path segmentation/emptybuscoverage; invalid timing/CDC evidence','syncsafe-ooc01':'Resource/source proof retained, timing/CDC constraints rejected for sameQ-start issue'},hardware_programmed=False,full_board_built=False,thirty_fps_qualified=False,MTBF_qualified=False,c_check_handoff='Unavailable in enabled tool catalog; manual nonempty/hash/content validation executed, not claimed tool PASS',cookie_limit='Inherited32-bit internal DMA cookie failsclosed beforeexhaustion; widen/prove or qualifiedcoordinatedreset beforelongrelease')
(o/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print('CDC_SYNCSAFE_COMPONENT_HANDOFF_INCOMPLETE_BOARD_GATES',o)
