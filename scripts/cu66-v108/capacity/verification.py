#!/usr/bin/env python3
"""Prepare strict, lossless adapters and independent capacity proof benches."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT/'fpga/experiments/cu66-v108-capacity'
BASE = ROOT/'fpga/experiments/cu66-v107-count-threshold'
OUT = SRC/'verification'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ports(source):
    header = source.split(') (\n', 1)[1].split('\n);', 1)[0]
    found = []
    kind = prefix = None
    for item in header.split(','):
        item = item.strip()
        match = re.match(r'(input|output)\s+logic\s+(signed\s+)?(\[[^\]]+\]\s*)?(.*)', item, re.S)
        if match:
            kind = match[1]
            prefix = 'logic '+(match[2] or '')+(match[3] or '')
            item = match[4]
        match = re.match(r'(\w+)(.*)', item, re.S)
        assert match, (item, prefix)
        found.append(dict(direction=kind, prefix=prefix, name=match[1], tail=match[2]))
    return found


def paired_probe(module, param, original_ports, extra_ports, observations):
    text = 'module '+module+param+' (\n'+',\n'.join(
        ' '+p['direction']+' '+p['prefix']+p['name']+p['tail'] for p in original_ports)
    text += ',\n output logic mismatch,\n'+extra_ports+'\n);\n'
    for p in original_ports:
        if p['direction'] == 'output':
            text += ' '+p['prefix']+'old_'+p['name']+p['tail']+';\n'
    for variant in ('original', 'candidate'):
        kind = 'pipeline' if module == 'prefix_probe' else 'ingress'
        typ = kind+'_'+variant
        if param:
            typ += ' #(.SYNC_STAGING(SYNC_STAGING))'
        args = ['.'+p['name']+'('+('old_' if variant == 'original' and p['direction'] == 'output' else '')+p['name']+')' for p in original_ports]
        if kind == 'ingress' and variant == 'candidate':
            args += ['.meta_capacity_upper(verify_capacity_upper)', '.meta_capacity_lower(verify_capacity_lower)', '.meta_capacity_wrap(verify_capacity_wrap)']
        text += ' '+typ+' '+('old_dut' if variant == 'original' else 'new_dut')+'('+','.join(args)+');\n'
    text += ' assign mismatch=!('+'&&'.join('(old_'+p['name']+'=='+p['name']+')' for p in original_ports if p['direction'] == 'output')+');\n'
    return text+observations+'\nendmodule\n'


def main():
    OUT.mkdir(exist_ok=True)
    recipe = json.loads((SRC/'edit-recipe.json').read_text())
    kinds = {'br88_packet_ingress_sync_v91h.sv': 'ingress', 'br88_packet_ingress_v91h.sv': 'packet',
        'br88_pipeline_v91h.sv': 'pipeline', 'packed_scratch_v91g2.sv': 'scratch'}
    adapters = []
    for name, e in recipe['production'].items():
        module, kind = name[:-3], kinds[name]
        for variant, path in [('original', ROOT/e['original']), ('candidate', SRC/name)]:
            text = path.read_text()
            renames = [(f'module {module} ', f'module {kind}_{variant} ')]
            if kind == 'packet':
                renames += [('br88_packet_ingress_sync_v91h #(', f'ingress_{variant} #(')]
            if kind == 'pipeline':
                renames += [('br88_packet_ingress_v91h #(', f'packet_{variant} #('),
                    ('packed_scratch_v91g2 scratch (', f'scratch_{variant} scratch (')]
            for before, after in renames:
                assert text.count(before) == 1
                text = text.replace(before, after, 1)
            q = OUT/(kind+'_'+variant+'.sv')
            q.write_text(text)
            adapters.append(dict(path=str(q.relative_to(ROOT)), source=str(path.relative_to(ROOT)),
                source_sha256=sha(path), sha256=sha(q), renames=renames))
    pp = ports((BASE/'br88_pipeline_v91h.sv').read_text())
    obs = ''.join(' assign verify_'+n+'=new_dut.meta_'+n+';\n' for n in (
        'blocks', 'count1', 'count2', 'count3', 'prefix1', 'prefix12', 'prefix123',
        'threshold1', 'threshold2', 'threshold3', 'capacity_upper', 'capacity_lower', 'capacity_wrap'))
    obs += ' assign verify_capacity_bad=new_dut.scratch.capacity_bad;\n'
    extra = ''' output logic [16:0] verify_blocks,
 output logic [31:0] verify_count1,verify_count2,verify_count3,
 output logic [31:0] verify_prefix1,verify_prefix12,verify_prefix123,
 output logic [31:0] verify_threshold1,verify_threshold2,verify_threshold3,
 output logic [31:0] verify_capacity_upper,verify_capacity_lower,
 output logic verify_capacity_wrap,verify_capacity_bad'''
    (OUT/'prefix_probe.sv').write_text(paired_probe('prefix_probe', ' #(parameter integer SYNC_STAGING=1)', pp, extra, obs))
    body = (BASE/'verification/tb_prefix.cpp').read_text()
    needle = '  ++metadata_edges;metadata_held'
    check = '''  const uint32_t units_mask=0x0fffffffU;
  const uint32_t a_units=((d.verify_prefix123>>4)+2U)&units_mask;
  const uint32_t cap_upper=((16384U-a_units)&units_mask)<<3;
  const uint32_t cap_lower=((~a_units)&units_mask)<<3;
  require(d.verify_capacity_upper==cap_upper&&d.verify_capacity_lower==cap_lower&&bool(d.verify_capacity_wrap)==(a_units>16384U),"independent capacity bound owner");
  const uint32_t literal_plan=d.dbg_meta_raw?uint32_t(32U+128U*d.verify_blocks):uint32_t(32U+((2U*d.verify_blocks+15U)&0xfffffff0U)+d.verify_prefix123);
  require(bool(d.verify_capacity_bad)==(literal_plan>262144U),"independent original plan capacity predicate");
  ++metadata_edges;metadata_held'''
    assert body.count(needle) == 1
    body = body.replace(needle, check, 1)
    (OUT/'tb_prefix.cpp').write_text(body)
    ip = ports((BASE/'br88_packet_ingress_sync_v91h.sv').read_text())
    obs = ''' assign verify_capture=new_dut.prefix_header_capture;
 assign verify_a1=new_dut.plan_align1;assign verify_a2=new_dut.plan_align2;assign verify_a3=new_dut.plan_align3;
 assign verify_threshold_live=new_dut.threshold_live;
 assign verify_capacity_live=new_dut.capacity_live;
'''
    extra = ''' output logic verify_capture,
 output logic [31:0] verify_a1,verify_a2,verify_a3,
 output logic [2:0] verify_threshold_live,
 output logic [31:0] verify_capacity_upper,verify_capacity_lower,
 output logic verify_capacity_wrap,verify_capacity_live'''
    (OUT/'ingress_capture_probe.sv').write_text(paired_probe('ingress_capture_probe', '', ip, extra, obs))
    capture = (BASE/'verification/tb_capture.cpp').read_text()
    needle = ' uint64_t threshold_commits=0,threshold_flush_commits=0,commit_abort_retries=0;'
    after = needle+'''
 std::deque<std::pair<uint64_t,uint32_t>> capacity_queue;
 uint32_t capacity_upper=0,capacity_lower=0;bool capacity_wrap=false,capacity_live=false;
 uint64_t capacity_commits=0,capacity_flush_commits=0,capacity_abort_retries=0;
 static std::array<uint32_t,3> capacity_bounds(uint32_t prefix){const uint32_t a=((prefix>>4)+2U)&0x0fffffffU;return {((16384U-a)&0x0fffffffU)<<3,((~a)&0x0fffffffU)<<3,uint32_t(a>16384U)};}
'''
    assert capture.count(needle) == 1
    capture = capture.replace(needle, after, 1)
    needle = ' void check(){'
    after = needle+'''
  need(d.verify_capacity_upper==capacity_upper&&d.verify_capacity_lower==capacity_lower&&bool(d.verify_capacity_wrap)==capacity_wrap,"independent four-edge bound tuple arithmetic/hold");
  need(bool(d.verify_capacity_live)==capacity_live,"independent capacity validity/flush owner");
  if(d.meta_valid){const auto c=capacity_bounds(p123);need(capacity_live&&capacity_upper==c[0]&&capacity_lower==c[1]&&capacity_wrap==bool(c[2]),"actual owned metadata capacity bounds");}
'''
    assert capture.count(needle) == 1
    capture = capture.replace(needle, after, 1)
    needle = '  d.clk=1;d.eval();p12=next12;p123=next123;check();'
    after = '''  const bool cap_commit=!capacity_queue.empty()&&capacity_queue.front().first==edges;
  if(cap_commit){const auto c=capacity_bounds(capacity_queue.front().second);capacity_queue.pop_front();capacity_upper=c[0];capacity_lower=c[1];capacity_wrap=bool(c[2]);++capacity_commits;if(flush)++capacity_flush_commits;}
  if(flush){capacity_queue.clear();capacity_live=false;}else if(cap_commit)capacity_live=true;
  if(expected_capture&&capture_index==2&&!flush)capacity_queue.push_back({edges+4,uint32_t(p12+align_count(count))});
  need(capacity_queue.size()<=4,"capacity pipeline owner bound");
  d.clk=1;d.eval();p12=next12;p123=next123;check();'''
    assert capture.count(needle) == 1
    capture = capture.replace(needle, after, 1)
    needle = "<<unsigned(d.verify_threshold_live)<<','<<flush<<'\\n'"
    after = "<<unsigned(d.verify_threshold_live)<<','<<flush<<','<<d.verify_capacity_upper<<','<<d.verify_capacity_lower<<','<<unsigned(d.verify_capacity_wrap)<<','<<unsigned(d.verify_capacity_live)<<'\\n'"
    assert capture.count(needle) == 1
    capture = capture.replace(needle, after, 1)
    needle = ' void high_metadata('
    func = ''' void capacity_flush_commit_retry(){
  clean();prepare(41U,0xfffffffdU,0);tick(true,2,0xfffffffdU);
  auto&r=*d.rootp;BOTH(state,0U);BOTH(context_active,0U);BOTH(ram_valid,0U);
  for(unsigned quiet=0;quiet<3;++quiet)tick(false,-1,0);
  d.abort_packet=1;tick(false,-1,0);d.abort_packet=0;need(!capacity_live,"capacity commit/abort owner invalidated");
  raw(19001U,-1);++capacity_abort_retries;
 }
'''
    assert capture.count(needle) == 1
    capture = capture.replace(needle, func+needle, 1)
    # Prepared high-count contexts must model the real settled P12 before WAIT41.
    # They are not real received headers; actual RAW below retains exactly93 clocks.
    needle = 'for(unsigned slot=0;slot<3;++slot){prepare(33+4*slot,counts[slot],0);tick(true,int(slot),counts[slot]);}'
    after = '''for(unsigned slot=0;slot<3;++slot){prepare(33+4*slot,counts[slot],0);tick(true,int(slot),counts[slot]);
   auto&r=*d.rootp;BOTH(state,0U);BOTH(context_active,0U);BOTH(ram_valid,0U);
   for(unsigned quiet=0;quiet<2;++quiet)tick(false,-1,0);
  }'''
    assert capture.count(needle) == 1
    capture = capture.replace(needle, after, 1)
    needle = ' for(int index:{33,37,41})'
    assert capture.count(needle) == 1
    capture = capture.replace(needle, ' b.capacity_flush_commit_retry();\n'+needle, 1)
    needle = 'b.raw_packets==7&&b.restarts==3&&b.held==2295&&b.commit_abort_retries==3&&b.threshold_flush_commits>=3'
    after = 'b.raw_packets==8&&b.restarts==3&&b.held==2312&&b.commit_abort_retries==3&&b.threshold_flush_commits>=3&&b.capacity_abort_retries==1&&b.capacity_flush_commits>=1'
    assert capture.count(needle) == 1
    capture = capture.replace(needle, after, 1)
    needle = '<<b.edges<<",\\\"threshold_commits'
    after = '<<b.edges<<",\\\"capacity_commits\\\":"<<b.capacity_commits<<",\\\"capacity_flush_commits\\\":"<<b.capacity_flush_commits<<",\\\"capacity_abort_retries\\\":"<<b.capacity_abort_retries<<",\\\"threshold_commits'
    assert capture.count(needle) == 1
    capture = capture.replace(needle, after, 1)
    (OUT/'tb_capture.cpp').write_text(capture)
    (OUT/'adapters.json').write_text(json.dumps(dict(schema='v108-capacity-lossless-adapters-v1',
        adapters=adapters, original_pipeline_header_ports=pp, original_ingress_header_ports=ip,
        bench_sources={str((BASE/'verification'/n).relative_to(ROOT)): sha(BASE/'verification'/n) for n in ('tb_prefix.cpp', 'tb_capture.cpp')},
        complete_body_renames_only=True, original_public_comparison_kept=True,
        prepared_fixture_adjustment='Two quiet edges after each manually injected high-count word settle P12 before last-word capture; real received RAW path still exactly93clocks.',
        limits='Prepared only; no simulator execution or qualification claimed. All original public, invalid/debug/counter, golden and ownership checks remain.'), indent=2, sort_keys=True)+'\n')
    # Literal exact production block extraction, with checked synthetic inputs.
    sync = (SRC/'br88_packet_ingress_sync_v91h.sv').read_text()
    begin = sync.index('    // CAPACITY_BOUND_PIPELINE_BEGIN')
    end = sync.index('    // CAPACITY_BOUND_PIPELINE_END', begin)+len('    // CAPACITY_BOUND_PIPELINE_END')
    block = sync[begin:end]
    bad = (SRC/'packed_scratch_v91g2.sv').read_text()
    begin_bad = bad.index('    assign capacity_bad=')
    end_bad = bad.index(';', begin_bad)+1
    predicate = bad[begin_bad:end_bad]
    top = '''module capacity_math_probe (
 input logic clk,reset,take,
 input logic [27:0] prefix12_units,input logic [31:0] count3,
 input logic [16:0] blocks,input logic raw,
 output logic [31:0] meta_capacity_upper,meta_capacity_lower,
 output logic meta_capacity_wrap,output logic live,bad,
 output logic [31:0] plan_prefix12
);
 logic prefix_header_capture,cancelled,context_failure,context_active,ctx_done;
 logic [5:0] fetch_index;logic [7:0] ram_data,fetch_bytes[38:40];
 assign prefix_header_capture=take&&!reset;assign cancelled=reset;
 assign context_failure=0;assign context_active=0;assign ctx_done=0;
 assign fetch_index=6'd41;assign plan_prefix12={prefix12_units,4'd0};
 assign ram_data=count3[31:24];assign fetch_bytes[38]=count3[7:0];
 assign fetch_bytes[39]=count3[15:8];assign fetch_bytes[40]=count3[23:16];
 function automatic logic [31:0] count_aligned(input logic [31:0] n);
  return ((n<<2)+32'd15)&32'hfffffff0;
 endfunction
'''+block+'''
 logic capacity_bad;logic [16:0] begin_blocks;logic begin_raw;
 logic [31:0] begin_capacity_upper,begin_capacity_lower;logic begin_capacity_wrap;
 assign begin_blocks=blocks;assign begin_raw=raw;
 assign begin_capacity_upper=meta_capacity_upper;assign begin_capacity_lower=meta_capacity_lower;
 assign begin_capacity_wrap=meta_capacity_wrap;
'''+predicate+'''
 assign live=capacity_live;assign bad=capacity_bad;
endmodule
'''
    (OUT/'capacity_math_probe.sv').write_text(top)
    (OUT/'tb_math.cpp').write_bytes((Path(__file__).parent/'tb_math.cpp').read_bytes())
    (OUT/'math-block.json').write_text(json.dumps(dict(
        production=str((SRC/'br88_packet_ingress_sync_v91h.sv').relative_to(ROOT)),
        exact_production_pipeline=True, block_sha256=hashlib.sha256(block.encode()).hexdigest(),
        predicate_source=str((SRC/'packed_scratch_v91g2.sv').relative_to(ROOT)),
        predicate_sha256=hashlib.sha256(predicate.encode()).hexdigest(),
        limits='Exact block/predicate extraction with synthetic coherent units16 prefix/current-byte plumbing; full production capture and controller pairing separate.'), indent=2, sort_keys=True)+'\n')
    print('CAPACITY_VERIFICATION_PREPARED', len(adapters), len(pp), len(ip))


if __name__ == '__main__':
    main()
