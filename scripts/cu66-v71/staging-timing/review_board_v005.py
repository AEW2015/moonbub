from pathlib import Path
import hashlib,json,tkinter
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002';f=d/'board-source-v005/selection.json';sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert sha(f)=='84cc0f1e93f03f870207c68df2c33aac6a4a7a3cee8da87deab7900ec69daf76';n=json.loads(f.read_text());p=json.loads((d/'board-source-v004/selection.json').read_text())
for key in['sources_sha256','headers_sha256','constraints_sha256','native_guard_references']:
 for name,h in n[key].items():assert sha(r/name)==h,(key,name)
assert n['constraints_sha256']==p['constraints_sha256'] and n['constraint_entry']==p['constraint_entry']
assert n['system_ports']==p['system_ports'] and n['CSR_ports']==p['CSR_ports']
for key in['UID_USR_ACCESS','CSR_magic','ABI','capabilities','part','watchdog_clocks','clock_IO_SDRAM_budget_changes']:assert n[key]==p[key],key
assert not n['BIT_ALLOWED']and not n['PROGRAM_ALLOWED'] and not n['SIMULATION']
replacements=json.loads((d/'board-source-v005/derivation.json').read_text())['source_replacements'];assert len(replacements)==2
assert [replacements.get(path,path)for path in p['sources']]==n['sources']
parent=r/'fpga/experiments/cu66-v71/codec/math-v004/cu71_base_pipeline_math.sv';base=r/'fpga/experiments/cu66-v71/direct-system/validpipe-v003/cu71_base_pipeline_math.sv';assert base.read_text().replace('cu71_idct_validpipe inverse(','cu71_idct_indexed inverse(')==parent.read_text()
interpreter=tkinter.Tcl()
for path in n['constraints_sha256']:
 if path.endswith('.tcl'):assert int(interpreter.call('info','complete',(r/path).read_text()))==1,path
helper=r/next(path for path in n['constraints_sha256']if path.endswith('bundle-registers-exact.tcl'));text=helper.read_text();assert 'dy71_bundle_exact_regs bridge/response_reg 32'in text and 'dy71_bundle_pins $response C 10.0'in text and 'dy71_bundle_pins $spi_rdata D 5.0'in text
q={'status':'PASS_STATIC_PROSPECTIVE_DY71_REPORT_ONLY_SOURCE_REVIEW','selection_sha256':sha(f),'exact_two_source_replacements':replacements,'base_change_exact_module_substitution':True,'safe_stager_CSR_and_bridge_unchanged':True,'top_ports_identity_clocks_PHY_map_constraints_unchanged_from_v004':True,'legacy_bundles':'Exact numbered FD source C/destination D, same10ns; native object/timing audit still pending','validpipe_review_sha256':sha(r/'fpga/experiments/cu66-v71/staging-timing/inverse-validpipe-review-v002.json'),'constraints_Tcl_balanced':True,'full_system_proof':'PENDING_IN_PARALLEL_NOT_A_BUILD_SUCCESS','BUILD_scope':'Root may launch report-only synthesis/implementation; no BIT eligibility or hardware','hardware':False};o=r/'fpga/experiments/cu66-v71/staging-timing/board-v005-review-v001.json';assert not o.exists();o.write_text(json.dumps(q,indent=2)+'\n');print(sha(o))
