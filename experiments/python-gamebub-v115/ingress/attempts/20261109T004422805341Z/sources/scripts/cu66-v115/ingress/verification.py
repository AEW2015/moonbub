"""Build reversible verification adapters without editing any historical checker."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[3];SRC=ROOT/'fpga/experiments/cu66-v115-ingress';V=SRC/'verification'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 records=[]
 def derive(source,dest,edits):
  p=ROOT/source;s=p.read_text();rows=[]
  for before,after in edits:
   assert s.count(before)==1,(source,before,s.count(before));s=s.replace(before,after,1);rows.append(dict(before=before,after=after))
  q=V/dest;q.write_text(s);records.append(dict(source=source,source_sha256=sha(p),path=str(q.relative_to(ROOT)),sha256=sha(q),edits=rows))
 for file,name in [('rice_original.sv','rice_original'),('rice_candidate.sv','rice_candidate')]:
  original='fpga/experiments/cu66-v110-prefix/br88_rice_elastic.sv' if name=='rice_original' else 'fpga/experiments/cu66-v115-ingress/br88_rice_elastic.sv'
  derive(original,file,[('module br88_rice_elastic (','module '+name+' (')])
 derive('fpga/experiments/cu66-v110-prefix/verification/rice_probe.sv','rice_probe.sv',[])
 derive('fpga/experiments/cu66-v110-prefix/verification/historical_rice.cpp','historical_rice.cpp',[])
 before='  d.reset=(guards&1)!=0;'
 after='''  // Complete the new private prepared-state tuple. No old check changes.
  NEW(prefix_window)=std::min(uint32_t(size-consumed),uint32_t(15));
  NEW(remaining_nonzero)=uint32_t(size-consumed)!=0;NEW(load_nonzero)=loaded<size;
  d.reset=(guards&1)!=0;'''
 derive('fpga/experiments/cu66-v110-prefix/verification/tb_rice.cpp','tb_rice.cpp',[(before,after)])
 original=ROOT/'fpga/experiments/cu66-v115-ingress/br88_packet_ingress_sync_v91h.sv';s=original.read_text();interface=s[:s.index('    localparam')];interface=interface.replace('module br88_packet_ingress_sync_v91h #(','module ingress_probe #(',1);interface=interface.replace('    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold\n','    output logic [63:0] count_stage_fetch_wait, count_stage_word_hold,\n    output logic [5:0] probe_fetch_index, output logic [31:0] probe_expected_addr,\n    output logic probe_selection_context\n')
 # Exact port names taken from the actual module interface.
 ports=re.findall(r'\b(?:input|output)\s+logic(?:\s+signed)?(?:\s+\[[^\]]+\])?\s+([^;\n]+)',s[:s.index('    localparam')]);names=[]
 for group in ports:
  for n in group.split(','):
   n=n.strip()
   if n and re.fullmatch(r'\w+',n):names.append(n)
 # A declaration can contain several names; regex above respects newline declarations.
 assert len(names)==len(set(names))
 body=interface+'    br88_packet_ingress_sync_v91h #(.MAX_PACKET_BYTES(MAX_PACKET_BYTES)) dut('+','.join('.'+n+'('+n+')'for n in names)+');\n'
 body+='    assign probe_fetch_index=dut.fetch_index;\n    assign probe_expected_addr=dut.expected_fetch_addr;\n    assign probe_selection_context=dut.selection_context;\nendmodule\n'
 (V/'ingress_probe.sv').write_text(body)
 (V/'adapters.json').write_text(json.dumps(dict(schema='v115-ingress-verification-adapters-v1',adapters=records,wrapper_source=str(original.relative_to(ROOT)),wrapper_source_sha256=sha(original),wrapper_sha256=sha(V/'ingress_probe.sv'),parser_original_check_sites_removed=0,parser_extra_prepared_tuple_sites=1,ingress_contract='new independent admitted-event dense golden/address-owner scoreboard; old exact-cycle checker remains byte-unchanged in frozen base'),indent=2)+'\n')
if __name__=='__main__':main()
