import hashlib,json,pathlib,shutil,subprocess,sys
P=pathlib.Path(__file__).resolve().parent
m=json.loads((P/'package-files.json').read_text())
for n,h in m.items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==h,n
print('SOURCE_PACKAGE_HASHES_PASS',len(m))
if len(sys.argv)>1 and sys.argv[1]=='build':
 out=pathlib.Path(sys.argv[2]).resolve();out.mkdir(parents=True,exist_ok=False)
 shutil.copytree(P/'inputs',out/'inputs')
 for n in ['key.cp23.hex','quantizers.hex']:shutil.copyfile(P/n,out/n)
 command=['vivado','-mode','batch','-source',str(out/'inputs/build_board.tcl'),'-log',str(out/'vivado.log'),'-journal',str(out/'vivado.jou'),'-tclargs',str(out)]
 raise SystemExit(subprocess.run(command,cwd=out).returncode)
