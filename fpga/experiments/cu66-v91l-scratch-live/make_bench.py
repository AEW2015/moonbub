"""Derive the frozen native reference bench, removing its last external-memory actor."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];AREA=Path(__file__).resolve().parent
s=(ROOT/'fpga/experiments/cu66-v91l-reference-live/tb_reference_live.cpp').read_text()
def replace(before,after):
 global s
 assert before in s,before[:100]
 s=s.replace(before,after)
replace('Vreference_live','Vscratch_live')
replace('        d.mem_req_ready=0;d.mem_rsp_valid=0;d.mem_rsp_epoch=0;d.mem_rsp_error=0;\n        for(unsigned k=0;k<4;++k)d.mem_rsp_data[k]=0;\n','')
a=s.index('        d.mem_req_ready=!pending',s.index('    void tick()'))
b=s.index('        d.eval();live_observe();',a)
s=s[:a]+s[b:]
replace('rgb_observe();reference_lines_observe();','rgb_observe();reference_lines_observe();scratch_observe();')
replace('if(response){need(pending.has_value(),"response without accepted owner");const auto &q=pending->req;', 'if(response){need(pending.has_value(),"response without accepted owner");const auto &q=pending->req;physical_scratch_response(q);')
replace('pending=Pending{q,cycle+(profile==0?1:(q.write?16:18)+unsigned(((q.addr>>4)^seed)&3))};++requests;', 'pending=Pending{q,cycle};physical_scratch_request(q);++requests;')
replace('      rgb_checking=false;', '      scratch_frame();rgb_checking=false;')
replace('&&d.fabric_mux_owner==0,"RGB began before actual candidate closure"', '&&d.fabric_mux_owner==0&&!d.fabric_scratch_busy&&!d.fabric_scratch_pending&&d.fabric_memory_owner==0,"RGB began before actual candidate/scratch closure"')
replace('        inputs=0;coefficients=0;requests=0;acks=0;', '        scratch_read_requests=scratch_write_requests=scratch_read_responses=scratch_write_responses=0;scratch_first=scratch_last=scratch_wait_cycles=scratch_pending_cycles=scratch_max_address=0;held_scratch_response.reset();\n        inputs=0;coefficients=0;requests=0;acks=0;')
replace('    static uint32_t be32(', (AREA/'bench_extension.inc').read_text()+'\n    static uint32_t be32(')
replace('cycle<80000000','cycle<160000000')
replace('watchdog<12000000','watchdog<50000000')
replace('n<20000000&&!commit_cycle','n<50000000&&!commit_cycle')
replace('&&!b.d.fabric_ref_pending&&b.d.fabric_mux_owner==0', '&&!b.d.fabric_ref_pending&&!b.d.fabric_scratch_busy&&!b.d.fabric_scratch_pending&&b.d.fabric_mux_owner==0&&b.d.fabric_memory_owner==0')
replace('actual_live_writes_physical_reference_validated_then_rgb_same_timed_memory','actual_live_writes_physical_scratch_and_reference_validated_then_rgb_same_timed_memory')
replace('scratch_rtl\\\":false','scratch_rtl\\\":true')
replace('REFERENCE_LIVE_TEST_FAIL','SCRATCH_LIVE_TEST_FAIL')
# Preserve source bytes except the one frozen whitespace-only line emptied here.
s=s.replace('        \n\n','\n')
(AREA/'tb_scratch_live.cpp').write_text('// Physical scratch endpoint; all C++ memory actors removed.\n'+s)
print('SCRATCH_LIVE_BENCH_GENERATED')
