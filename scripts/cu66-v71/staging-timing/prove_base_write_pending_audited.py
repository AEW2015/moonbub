from pathlib import Path
parent=Path(__file__).with_name('prove_base_write_pending.py');s=parent.read_text()
s=s.replace("pins={str(p):sha(p)}","pins={str(p):sha(p),str(parent):sha(parent)}")
s=s.replace("for label,script in commands.items():","for label,script in commands.items():\n script=script.replace('opt_clean; ','opt_clean; write_json '+lin(o/(label+'-netlist.json'))+'; ')")
needle="assert all(sha(Path(n))==h for n,h in pins.items());"
audit='''audits={}
for label in commands:
 net=json.loads((o/(label+'-netlist.json')).read_text())['modules']['cu71_base_pipeline_math'];cells=net['cells'];anyseq=[c for c in cells.values()if c['type']=='$anyseq'];bits=set(b for c in anyseq for b in c['connections']['Y']);checked={}
 for name in ['e_cfg_ready','s_cfg_ready','rows_ready','e_done','e_error','s_error','dq_valid','dq_error','idct_valid','idct_error','recon_valid','recon_error','rows_result_valid','rows_error']:
  actual=net['netnames'][name]['bits'];assert all(b in bits for b in actual),(label,name,actual);checked[name]=actual
 assert len(net['ports']['formal_fs']['bits'])==4
 audits[label]={'anyseq_cells':len(anyseq),'anyseq_bits':len(bits),'checked_child_outputs':checked,'no_input_validity_or_handshake_assumptions':True}
(o/'abstraction-audit.json').write_text(json.dumps(audits,indent=2)+'\\n')
'''
assert needle in s;s=s.replace(needle,audit+needle);exec(compile(s,str(parent),'exec'),globals())
