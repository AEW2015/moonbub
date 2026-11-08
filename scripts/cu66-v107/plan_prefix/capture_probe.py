#!/usr/bin/env python3
"""Generate full-production synchronous ingress pair with read-only observations."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v107-plan-prefix';OUT=SRC/'verification'
def main():
 old=(OUT/'ingress_original.sv').read_text();header=old.split(') (\n',1)[1].split('\n);',1)[0];ports=[];kind=prefix=None
 for item in header.split(','):
  item=item.strip();m=re.match(r'(input|output)\s+logic\s+(signed\s+)?(\[[^\]]+\]\s*)?(.*)',item,re.S)
  if m:kind=m[1];prefix='logic '+(m[2] or '')+(m[3] or '');item=m[4]
  m=re.match(r'(\w+)(.*)',item,re.S);assert m;ports.append(dict(direction=kind,prefix=prefix,name=m[1],tail=m[2]))
 body='module ingress_capture_probe (\n'+',\n'.join(' '+p['direction']+' '+p['prefix']+p['name']+p['tail'] for p in ports)+''',
 output logic mismatch,verify_capture,
 output logic [31:0] verify_a1,verify_a2,verify_a3,
 output logic [31:0] meta_prefix1,meta_prefix12,meta_prefix123
);
'''
 for p in ports:
  if p['direction']=='output':body+=' '+p['prefix']+'old_'+p['name']+p['tail']+';\n'
 for v,label in [('original','old_dut'),('candidate','new_dut')]:
  args=['.'+p['name']+'('+('old_' if v=='original' and p['direction']=='output' else '')+p['name']+')' for p in ports]
  if v=='candidate':args+=['.meta_prefix1(meta_prefix1)','.meta_prefix12(meta_prefix12)','.meta_prefix123(meta_prefix123)']
  body+=' ingress_'+v+' '+label+'('+','.join(args)+');\n'
 body+=' assign mismatch=!('+'&&'.join('(old_'+p['name']+'=='+p['name']+')' for p in ports if p['direction']=='output')+');\n'
 body+=' assign verify_capture=new_dut.prefix_header_capture;\n assign verify_a1=new_dut.plan_align1;\n assign verify_a2=new_dut.plan_align2;\n assign verify_a3=new_dut.plan_align3;\nendmodule\n';(OUT/'ingress_capture_probe.sv').write_text(body);print('FULL_PRODUCTION_CAPTURE_PROBE_PREPARED',len(ports))
if __name__=='__main__':main()
