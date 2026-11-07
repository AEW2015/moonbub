from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'run-xsim-vendor-v004.py').read_text(encoding='utf-8-sig')
s=s.replace("e=p/'xsim-vendor04'", "e=p/'xsim-boundary01'").replace("p/'mapping04/funcsim.v'", "p/'boundary01/bulk-funcsim.v'")
s=s.replace('Actual synthesized standalone bulk engine / AMD unisims_ver;', 'Actual kept bulk cell exported from control-plane synthesis / AMD unisims_ver;')
(p/'run-xsim-kept-executed.py').write_text(s)
exec(compile(s,str(p/'run-xsim-kept-executed.py'),'exec'))
