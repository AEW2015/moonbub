"""Independent read-only static source graph and source-binding audit; no build."""
from pathlib import Path
import hashlib,json,re
r=Path(__file__).resolve().parents[2];d=r/'fpga/experiments/cu66-v71/direct-system'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
m=d/'final-integration-v008/sources.json';s=d/'syncsafe-math-v002/board-source-v008/selection.json'
assert sha(m)=='15cc325a837720ae4f54dbb98b30d457d76271f416b7ef1576c198a68fde4b69'
assert sha(s)=='3e5760ca6da2d593febe00655cb0a343d6d675f02db2ea8d1e9623df0fef6ba8'
manifest=json.loads(m.read_text());selection=json.loads(s.read_text());checked={}
for key in('sources_sha256','headers_sha256','constraints_sha256','native_guard_references'):
 for n,h in selection[key].items():
  assert sha(r/n)==h,(key,n);checked[n]=h
assert set(selection['sources'])==set(selection['sources_sha256'])
assert len(selection['sources'])==len(set(selection['sources']))
assert manifest['sources']==selection['sources'][:len(manifest['sources'])]
assert all(selection['sources_sha256'][n]==h for n,h in manifest['sources_sha256'].items())
assert selection['BUILD_ALLOWED']and not selection['BIT_ALLOWED']and not selection['PROGRAM_ALLOWED']and not selection['SIMULATION']
assert selection['UID_USR_ACCESS']==selection['CSR_magic']=='0x44593731'
assert selection['ABI']=='0x00010000'and selection['capabilities']=='0x0f'
parent=json.loads((d/'syncsafe-math-v002/board-source-v005/selection.json').read_text())
for k in('headers_sha256','constraints_sha256','constraint_entry','XDC_order','include_dirs','clock_IO_SDRAM_budget_changes'):
 assert selection[k]==parent[k],k
definitions={};texts={}
for n in selection['sources']:
 text=(r/n).read_text();text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S);texts[n]=text
 for name in re.findall(r'\bmodule\s+(\w+)',text):
  assert name not in definitions,('duplicate module',name,n);definitions[name]=n
graph={name:[]for name in definitions}
for name,n in definitions.items():
 text=texts[n]
 for child in definitions:
  if child==name:continue
  if re.search(r'\b'+child+r'\s+(?:#\s*\(.*?\)\s*)?\w+\s*\(',text,re.S):graph[name].append(child)
seen=set()
def visit(n):
 if n in seen:return
 seen.add(n)
 for c in graph[n]:visit(c)
visit(selection['top']);assert seen==set(definitions),('unreachable/extraneous',set(definitions)-seen)
assert len([x for x in definitions if x.startswith('cu71_base')])==1
assert 'cu71_base_core_v006'in definitions and 'cu71_packet_hudsum'in definitions and 'cu71_idct_validpipe'in definitions
assert not any(x in definitions for x in('cu66_packet_control','cu71_base_pipeline_math','cu71_receiver_core_v006','cu71_system_core_v006'))
# Independently reverse composition to exact frozen parents.
der=json.loads((d/'final-integration-v008/derivation.json').read_text())
receiver=(d/'final-integration-v008/cu71_receiver_final_v008.sv').read_text()
rev=receiver
for old,new in reversed(der['receiver_binding_swaps']):assert rev.count(new)==1;rev=rev.replace(new,old)
for old,new in reversed(der['event_swaps']):assert rev.count(new)==1;rev=rev.replace(new,old)
assert rev==(r/der['owner_source']).read_text()
system=(d/'final-integration-v008/cu71_system_final_v008.sv').read_text();rev=system
for old,new in reversed(der['system_binding_swaps']):assert rev.count(new)==1;rev=rev.replace(new,old)
assert rev==(d/'core-integration-v006/cu71_system_core_v006.sv').read_text()
top=(d/'syncsafe-math-v002/board-source-v008/moonshine_top_dy71.sv').read_text()
assert top.replace('cu71_system_final_v008 #(','cu71_system_direct_syncsafe #(')==(r/'fpga/experiments/cu66-v71/transport-nonzero/samecycle-v001/moonshine_top_dy71.sv').read_text()
def header(t):return re.search(r'\bmodule\s+\w+\b(.*?);',t,re.S).group(1)
assert header(system)==header((d/'core-integration-v006/cu71_system_core_v006.sv').read_text())
assert header(receiver)==header((r/der['owner_source']).read_text())
assert header(top)==header((r/'fpga/experiments/cu66-v71/transport-nonzero/samecycle-v001/moonshine_top_dy71.sv').read_text())
builder=(r/'scripts/cu66-v71/build_selected_board.py').read_text()
assert 'write_bitstream'not in builder and 'open_hw'not in builder and 'program_hw'not in builder
assert "and not result['native_error_lines']"in builder and "re.findall(r'^ERROR:.*$'"in builder
o=d/'final-integration-v008/review-static-v001.json';assert not o.exists()
o.write_text(json.dumps(dict(status='PASS_STATIC_COMPOSITION_REVIEW_NO_BUILD_OR_HARDWARE',manifest_sha256=sha(m),selection_sha256=sha(s),verified_bindings=checked,module_graph=graph,all_modules_reachable=True,duplicate_modules=False,exact_reverse_composition=True,headers_identical=True,constraints_headers_clock_numeric_unchanged=True,
 findings=['No static source/graph/port blocker to report-only build. All module sources reachable once; no old parser/base/IDCT duplicate.',
 'Whole final KEY/P/P and actual v36/native pairing remain pending; static review does not establish composed behavior or board timing.',
 'Builder rejects native ERROR lines in captured console and never writes BIT/programs. Placed checkpoint/setup/summary added; these are diagnostic and not included in required_reports list.',
 'Current builder TEMP/TMP uses output/tmp: root must use a short unique output path for this build (or a separately reviewed short private temp change), preserving the verified native workaround.',
 'Inherited metadata fields still say pending split/safe gates although earlier versions were proved; the new final composition pending status is conservative, not a release gate bypass.'],hardware=False),indent=2)+'\n')
print(o,sha(o));print('SOURCES',len(selection['sources']),'MODULES',len(definitions),'STATIC_PASS')
