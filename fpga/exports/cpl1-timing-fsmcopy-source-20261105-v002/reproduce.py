import hashlib,json,pathlib,shutil,subprocess,sys,os,re
P=pathlib.Path(__file__).resolve().parent
for n,h in json.loads((P/'package-files.json').read_text()).items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
print('SOURCE_PACKAGE_HASHES_PASS')
if len(sys.argv)>1 and sys.argv[1]=='build':
 out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
 shutil.copytree(P/'inputs',out/'inputs')
 for n in ['key.cp23.hex','quantizers.hex']:shutil.copy2(P/n,out/n)
 tool=os.environ.get('VIVADO')or shutil.which('vivado')or 'C:/Xilinx/2025.2/Vivado/bin/vivado.bat'
 def run(tcl,dest,args):
  dest.mkdir(exist_ok=True)
  q=subprocess.run([tool,'-mode','batch','-source',str(tcl),'-log',str(dest/'vivado.log'),'-journal',str(dest/'vivado.jou'),'-tclargs',*map(str,args)],cwd=dest)
  if q.returncode:raise SystemExit(q.returncode)
 run(out/'inputs/build_board.tcl',out,[out])
 final=out
 if(P/'implementation-repair.tcl').exists():
  repair=out/'repair';repair.mkdir();shutil.copytree(out/'inputs',repair/'inputs')
  run(P/'implementation-repair.tcl',repair,[out/'placed.dcp',repair])
  final=repair
 if(P/'implementation-chain.json').exists():
  for i,step in enumerate(json.loads((P/'implementation-chain.json').read_text())):
   post=out/('postroute-'+str(i));post.mkdir();shutil.copytree(out/'inputs',post/'inputs')
   run(P/step['script'],post,[final/'routed.dcp',post,step['directive']])
   final=post
 lines=(final/'timing-summary.rpt').read_text().splitlines();i=next(i for i,l in enumerate(lines)if l.strip().startswith('WNS(ns)'));v=lines[i+2].split();assert len(v)==12,v
 assert all(float(v[i])>0 for i in [0,4,8])and all(int(v[i])==0 for i in [2,6,10]),v
 route=(final/'route-status.rpt').read_text()
 def count(label):
  m=re.search(label+r'\.*\s*:\s*(\d+)',route,re.I);assert m,label;return int(m[1])
 assert count(r'# of routable nets')==count(r'# of fully routed nets')>0 and count(r'# of nets with routing errors')==0
 bus=re.findall(r'Slack \((MET|VIOLATED)\)\s*:\s*(-?[0-9.]+)ns',(final/'bus-skew.rpt').read_text());assert len(bus)==4 and all(s=='MET'and float(v)>0 for s,v in bus),bus
 print('PASS_REBUILT_ROUTED_TIMING_ONLY_NOT_HARDWARE_SIGNOFF',final)
 if len(sys.argv)>3 and sys.argv[3]=='image':
  image=out/'image';image.mkdir();run(P/'image/write-image.tcl',image,[final/'routed.dcp',image])
