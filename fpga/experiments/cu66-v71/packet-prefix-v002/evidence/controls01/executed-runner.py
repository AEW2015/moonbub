"""Bounded real byte-RAM native metadata/qmap controls; exact error-code A/B."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess
r=Path(__file__).resolve().parents[3];p=argparse.ArgumentParser();p.add_argument('--output',required=True);a=p.parse_args();o=r/a.output;o.mkdir(parents=True,exist_ok=False)
s=r/'fpga/experiments/cu66-v69/packet';d=r/'fpga/experiments/cu66-v71/packet-prefix-v002'
sha=lambda x:hashlib.sha256(x.read_bytes()).hexdigest()
lines=(s/'cases.tsv').read_text().splitlines();valid=[x for x in lines if x.split('\t')[2]=='1'][:12];neg=[x for x in lines if x.split('\t')[2]!='1'];chosen=valid+neg
assert len(neg)==28
shutil.copyfile(__file__,o/'executed-runner.py');shutil.copyfile(d/'cu71_packet_presum.sv',o/'candidate.sv');shutil.copyfile(s/'cu66_packet_control.sv',o/'parent.sv')
for label in ['baseline','candidate']:
 b=o/label;b.mkdir();(b/'fixtures').mkdir()
 for line in chosen:
  parts=line.split('\t')
  for name in [parts[1],parts[8]]:
   if name and (s/name).is_file():
    shutil.copyfile(s/name,b/name)
    if name.endswith('.meta'):
     # Metadata references a qmap oracle in its first record.
     for token in (s/name).read_text().split():
      if (s/token).is_file():shutil.copyfile(s/token,b/token)
 (b/'cases.tsv').write_text('\n'.join(chosen)+'\n',newline='\n')
 t=(s/'tb_packet.cpp').read_text().replace('cu66_packet_control','cu71_packet_presum')
 t=t.replace('need(mode == 0, "unexpected structural reject code" +','std::cout << "EXACT_REJECT " << active_case << " " << unsigned(d.error_code) << "\\n";\n        need(mode == 0, "unexpected structural reject code" +')
 t=t.replace('valid == 457 && rejected == 23 && deferred == 5','valid == 12 && rejected == 23 && deferred == 5')
 (b/'tb_packet.cpp').write_text(t,newline='\n')
 rtl=(o/('parent.sv' if label=='baseline' else 'candidate.sv')).read_text().replace('module cu66_packet_control (','module cu71_packet_presum (')
 (b/'cu71_packet_presum.sv').write_text(rtl,newline='\n');shutil.copyfile(s/'cu66_profile.svh',b/'cu66_profile.svh')
 w='/mnt/c/'+str(b.relative_to(Path('C:/'))).replace('\\','/')
 shell=f'''#!/bin/bash
set -euo pipefail
source /opt/gamebub-openxc7-20261021/oss-cad-suite/environment
cd '{w}'
verilator --cc --exe --build -j 2 -Wall --top-module cu71_packet_presum -I. --Mdir obj cu71_packet_presum.sv tb_packet.cpp -CFLAGS '-std=c++17 -O2' >build.log 2>&1
obj/Vcu71_packet_presum cases.tsv 6910 >seed6910.log
obj/Vcu71_packet_presum cases.tsv 6911 >seed6911.log
'''
 (b/'run.sh').write_text(shell,newline='\n')
 cmd=['wsl','-d','MRS-HDL-Research','--','bash',w+'/run.sh'];q=subprocess.run(cmd,capture_output=True)
 (b/'launcher.log').write_bytes(q.stdout+q.stderr);print(label,q.returncode,flush=True)
 assert q.returncode==0,(label,(b/'launcher.log').read_text())
for seed in [6910,6911]:
 logs=[(o/l/f'seed{seed}.log').read_text()for l in ['baseline','candidate']]
 assert all('TEST_PASS' in t for t in logs)
 rejects=[[x for x in t.splitlines()if x.startswith('EXACT_REJECT')]for t in logs]
 assert rejects[0]==rejects[1] and len(rejects[0])==23
sources={str(x.relative_to(o)):sha(x)for x in o.rglob('*')if x.is_file() and 'obj'not in x.parts and x.suffix in ['.sv','.svh','.cpp','.tsv','.sh','.meta','.cu66','.qmap','.py']}
(o/'source-freeze.json').write_text(json.dumps(sources,indent=2)+'\n')
(o/'result.json').write_text(json.dumps(dict(status='PASS_NATIVE_BYTE_RAM_METADATA_QMAP_AND_EXACT_REJECTION_CODES',valid_frames_per_seed=12,structural_rejects_per_seed=23,semantic_deferred_per_seed=5,seeds=[6910,6911],baseline_parser_sha256=sha(s/'cu66_packet_control.sv'),candidate_sha256=sha(d/'cu71_packet_presum.sv'),hardware=False,canonical_decoder=False,scope='Actual RAM parser plus native metadata/qmap oracle; full reconstructed canonical/HUD golden integration remains separate'),indent=2)+'\n')
print('PACKET_PREFIX_CONTROLS_PASS',o,flush=True)
