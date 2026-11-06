from pathlib import Path
import argparse,json,hashlib,shutil,subprocess,shlex,time
r=Path(__file__).resolve().parents[4];d=r/'fpga/experiments/cu66-v71/owner-timing/meta-payload-v002';p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=Path(a.output).resolve();o.mkdir(parents=True,exist_ok=False);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();lin=lambda p:'/mnt/'+p.resolve().drive[0].lower()+p.resolve().as_posix()[2:];pins={};reports={};steps=[]
for label,file,top in[('parent','owner_invariant_abstract.sv','owner_invariant_abstract'),('candidate','owner_tag_structural.sv','owner_tag_structural')]:
 f=d/file;shutil.copy2(f,o/file);pins[str(f)]=sha(f);cmd='read_verilog -sv '+lin(o/file)+'; prep -top '+top+'; memory_map; opt; opt_dff; opt_clean; write_json '+lin(o/(label+'.json'));args=['wsl.exe','-d','MRS-HDL-Research','--','bash','-lc','source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment && yosys -Q -T -p '+shlex.quote(cmd)];start=time.monotonic()
 with(o/(label+'.log')).open('wb')as out:q=subprocess.run(args,stdout=out,stderr=subprocess.STDOUT,timeout=300)
 steps.append(dict(label=label,command=args,returncode=q.returncode,seconds=time.monotonic()-start));(o/'execution.json').write_text(json.dumps(steps,indent=2)+'\n');assert q.returncode==0,label
 m=json.loads((o/(label+'.json')).read_text())['modules'][top];bits=set(m['netnames']['hud_expected']['bits']);driver={};cells=m['cells']
 for name,c in cells.items():
  for port,bb in c['connections'].items():
   if c['port_directions'][port]=='output':
    for bit in bb:
     if isinstance(bit,int):driver[bit]=(name,port)
 holders=[(name,c)for name,c in cells.items()if set(c['connections'].get('Q',[]))&bits];assert holders,(label,'no tag register')
 def leaves(bit,seen):
  if not isinstance(bit,int)or bit in seen:return set()
  if bit not in driver:return{bit}
  name,_=driver[bit];c=cells[name];t=c['type']
  if any(x in t.lower()for x in('dff','latch','mem')):return{bit}
  out=set()
  for port,bb in c['connections'].items():
   if c['port_directions'][port]=='input':
    for b in bb:out|=leaves(b,seen|{bit})
  return out
 ce={};all_leaves=set()
 for name,c in holders:
  enables=[p for p in('EN','E')if p in c['connections']];assert enables,(label,c['type'],'enable not inferred')
  ls=set()
  for en in enables:
   for b in c['connections'][en]:ls|=leaves(b,set())
  ce[name]=dict(cell_type=c['type'],Q_bits=len(c['connections']['Q']),enable_leaves=len(ls),own_tag_bits_in_enable=len(ls&bits));all_leaves|=ls
 reports[label]=dict(tag_bits=len(bits),cells=ce,own_tag_enable_leaf_bits=len(all_leaves&bits),scope='Generic optimizedFF CE cone with all childoutputs as independentinputs. StopsatFFQ; not deviceLUT/timing orfullchildimplementation.')
assert reports['parent']['own_tag_enable_leaf_bits']>0 and reports['candidate']['own_tag_enable_leaf_bits']==0,reports
pins[str(Path(__file__))]=sha(Path(__file__));assert all(sha(Path(p))==h for p,h in pins.items());(o/'result.json').write_text(json.dumps(dict(status='PASS_STRUCTURAL_HUD_EXPECTED_SELF_CE_DEPENDENCY_REMOVED_WITHOUT_EXCEPTION',reports=reports,sources=pins,hardware=False,timing=False),indent=2)+'\n');print(json.dumps(dict(result_sha256=sha(o/'result.json'),reports=reports),indent=2))
