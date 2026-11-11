#!/usr/bin/env python3
"""Derive an opt-in instrumented live-guard bench; never modifies selected RTL."""
from pathlib import Path
import hashlib
import json

root = Path(__file__).resolve().parents[3]
base = root / 'fpga/experiments/cu66-v117-live-guard/tb_keyframe.cpp'
out = root / 'fpga/experiments/cu66-v129-observe/tb_keyframe.cpp'
source = base.read_text()
assert hashlib.sha256(source.encode()).hexdigest() == 'cad383becd5a9d20a8722a4ec78b0cb5ae86d7967abdbfac0a4857c6b1da4b18'

def once(old, new):
    global source
    assert source.count(old) == 1, old
    source = source.replace(old, new, 1)

once('#include "Vcs88_live_v91l.h"', '#include "Vcs88_live_v91l.h"\n#include "monitor.hpp"')
once('    void observe_fences(bool kill){', '    v129_observe::Monitor latency_monitor;\n    void observe_fences(bool kill){')
once('maximum_slots_owned=triple_phase_edges=triple_transfer_edges=0;instrument_started=false;',
     'maximum_slots_owned=triple_phase_edges=triple_transfer_edges=0;instrument_started=false;latency_monitor={};')
once('      if(!instrument_started||kill)return;', '''      if(!instrument_started||kill)return;
#if ELASTIC
      if(!commit_cycle) {
        const auto& m=*d.rootp;
        v129_observe::Sample s;
        s.coefficient={bool(d.coefficient_valid),bool(d.coefficient_ready)};
        s.inverse={bool(m.cs88_live_v91l__DOT__producer__DOT__staged_valid),bool(m.cs88_live_v91l__DOT__producer__DOT__staged_ready)};
        s.residual={bool(d.residual_valid),bool(d.residual_ready)};
        s.canonical={bool(d.out_valid),bool(d.out_ready)};
        s.hash={bool(d.join_output_valid),bool(d.join_output_ready)};
        s.request={bool(d.candidate_req_valid),bool(d.candidate_req_ready)};
        s.response={bool(d.candidate_rsp_valid),bool(d.candidate_rsp_ready)};
        s.pending_ack=bool(candidate_pending);
        latency_monitor.sample(s);
      }
#endif''')
once('    void report_fences(){', '''    void report_fences(){
#if ELASTIC
      latency_monitor.report(std::cout,seed,profile,frame_epoch);
#endif''')
out.write_text(source)
print(json.dumps({'baseline_sha256': hashlib.sha256(base.read_bytes()).hexdigest(),
                  'derived_sha256': hashlib.sha256(out.read_bytes()).hexdigest(),
                  'header_sha256': hashlib.sha256((out.parent/'monitor.hpp').read_bytes()).hexdigest(),
                  'output': str(out.relative_to(root))}, sort_keys=True))
