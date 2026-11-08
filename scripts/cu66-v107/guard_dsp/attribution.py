#!/usr/bin/env python3
"""Read-only portable DSP binding extraction from existing zstd EDIF in DCP."""
import hashlib,json,re,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=ROOT/'experiments/python-gamebub-v107/guard-dsp/attribution';NATIVE=ROOT/'experiments/python-gamebub-v107/native/20261108T052651848340Z/receipt.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 AREA.mkdir(parents=True,exist_ok=True);parent=json.loads(NATIVE.read_text());entry=parent['artifacts']['synth.dcp'];checkpoint=Path(entry['external_path']);before=sha(checkpoint);assert before==entry['sha256']
 with zipfile.ZipFile(checkpoint) as archive:compressed=archive.read('cs88_pipeline_v91k.edf')
 data=subprocess.run(['zstd','-dc'],input=compressed,capture_output=True,check=True).stdout;s=data.decode();matches=list(re.finditer(r'\(instance error4 \(viewref netlist \(cellref DSP48E1 ',s));assert len(matches)==1;start=matches[0].start();end=s.index('\n         )',start)+len('\n         )');instance=s[start:end]
 ports={};nets={}
 for match in re.finditer(r'\(portref (?:\(member \w+ \d+\)|\w+) \(instanceref error4\)\)',s):
  start=s.rfind('\n         (net ',0,match.start())
  if start in nets:continue
  end=s.find('\n         (net ',match.end());block=s[start:end];name=block.splitlines()[1].strip();refs=re.findall(r'\(portref (.*?) \(instanceref error4\)\)',block);nets[start]=dict(name=name,error4_ports=refs)
  for ref in refs:assert ref not in ports;ports[ref]=name
 one=sum(1<<(17-bit) for bit in range(18) if '_const1_' in ports[f'(member B {bit})']);assert one==43
 assert all('_const0_' in ports[f'(member B {bit})'] or '_const1_' in ports[f'(member B {bit})'] for bit in range(18))
 assert all('_const0_' in ports[f'(member A {member})'] for member in range(13))
 for bit in range(17):assert f'"Q[{bit}]"' in ports[f'(member A {29-bit})']
 expected={'AREG':1,'BREG':0,'MREG':0,'PREG':0}
 for prop,value in expected.items():assert f'(property {prop} (integer {value}))' in instance
 rpt=Path(parent['artifacts']['place-setup-paths.rpt']['external_path']);assert sha(rpt)==parent['artifacts']['place-setup-paths.rpt']['sha256'];report=rpt.read_text();first=report[:report.index('\nSlack (VIOLATED)',report.index('Slack (VIOLATED)')+1)];assert 'scratch/error4/CLK' in first and 'scratch/error4/P[3]' in first and 'scratch/cursors_reg[1][2]/CE' in first
 (AREA/'error4-instance.edif.txt').write_text(instance+'\n');(AREA/'place-first-path.rpt').write_text(first);(AREA/'error4-net-binding.json').write_text(json.dumps(list(nets.values()),indent=2,sort_keys=True)+'\n')
 original=ROOT/'fpga/experiments/cu66-v106-scratch/packed_scratch_v91g2.sv';line=original.read_text().splitlines()[428];assert "begin_count3>32'(begin_blocks)*43" in line
 result=dict(schema='v107-existing-control-dsp-binding-v1',status='PASS_EXACT_MAPPED_CONSTANT43_ATTRIBUTION',parent_receipt=str(NATIVE.relative_to(ROOT)),parent_receipt_sha256=sha(NATIVE),checkpoint_sha256_before=before,checkpoint_sha256_after=sha(checkpoint),compressed_edif_sha256=hashlib.sha256(compressed).hexdigest(),expanded_edif_sha256=hashlib.sha256(data).hexdigest(),instance='coefficients/child/scratch/error4',primitive='DSP48E1',B_constant=one,A_nonconstant_bits=17,A_high_bits_grounded=13,registers=expected,source=str(original.relative_to(ROOT)),source_sha256=sha(original),guard_source_line=429,guard_source_text=line.strip(),placement_slack_ns=-2.639,placement_data_ns=12.350,placement_clock_to_P3_ns=4.009,placement_logic_levels=11,read_only=True,scope='Read-only synthesis DCP binding plus actual placement path; routed DSP timing is separately probed, and source alias attributes alone do not prove new mapping.')
 assert result['checkpoint_sha256_before']==result['checkpoint_sha256_after'];result['artifacts_sha256']={p.name:sha(p) for p in AREA.iterdir() if p.is_file() and p.name!='receipt.json'};(AREA/'receipt.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(result['status'])
if __name__=='__main__':main()
