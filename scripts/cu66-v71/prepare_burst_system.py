"""Explicit RGB burst integration; selected map is an include-path experiment."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[2];d=r/'fpga/experiments/cu66-v71/system'
p=d/'cu71_system_bram.sv';f=d/'cu71_system_burst.sv';assert not f.exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
painter=r/'fpga/experiments/cu66-v71/display/cu71_painter_strip_burst.sv'
assert sha(painter)=='eb11803c4e40ade48b99cc9c240d54e8254ebd3e561242bd232cd03d2d6df7a4'
s=p.read_text();changes={'module cu71_system_bram #(':'module cu71_system_burst #(',
 '    cu71_memory_system #(':'    cu71_memory_system_burst #(',
 '    cu71_painter_strip_pipe painter(':'    cu71_painter_strip_burst painter(',
 '    cu71_scanout_prefetch #(.RGB_BASE(RGB0_BASE)) scanout(':'    cu71_scanout_banked #(.RGB_BASE(RGB0_BASE),.RGB1_BASE(RGB1_BASE)) scanout(',
 '        memory_drained=!memory_tile_busy&&!(arb_state!=ARB_IDLE&&arb_owner!=2);':'        memory_drained=!memory_tile_busy&&!rgb_busy&&!(arb_state!=ARB_IDLE&&arb_owner!=2);',
 '        painter_drained=!painter_busy;':'        painter_drained=!painter_busy&&!rgb_busy;'}
for a,b in changes.items():assert s.count(a)==1,a;s=s.replace(a,b)
anchor='    logic lcd_abort_i,lcd_busy,lcd_aborted;'
assert s.count(anchor)==1
s=s.replace(anchor,anchor+'''
    logic rgb_req_valid,rgb_req_ready,rgb_rsp_valid,rgb_rsp_ready,rgb_rsp_error;
    logic [23:0] rgb_req_addr;logic [127:0] rgb_req_data;logic [15:0] rgb_req_mask;
    logic rgb_abort_i,rgb_busy,rgb_aborted;''')
anchor='        .lcd_rsp_data,.lcd_rsp_error,.lcd_abort_i,.lcd_busy,.lcd_aborted,'
assert s.count(anchor)==2
# Add RGB port only at the memory instance, never the scanout instance.
s=s.replace(anchor,anchor+'''
        .rgb_req_valid,.rgb_req_ready,.rgb_req_addr,.rgb_req_data,.rgb_req_mask,
        .rgb_rsp_valid,.rgb_rsp_ready,.rgb_rsp_error,.rgb_abort_i,.rgb_busy,.rgb_aborted,''',1)
anchor='''        .aux_rsp_valid(p_rsp_valid),.aux_rsp_ready(p_rsp_ready),.aux_rsp_data(p_rsp_data),.aux_rsp_error(p_rsp_error),'''
assert s.count(anchor)==2
s=s.replace(anchor,anchor+'''
        .rgb_req_valid,.rgb_req_ready,.rgb_req_addr,.rgb_req_data,.rgb_req_mask,
        .rgb_rsp_valid,.rgb_rsp_ready,.rgb_rsp_error,.rgb_abort_i,.rgb_busy,.rgb_aborted,''',1)
f.write_text(s,newline='\n')
(d/'derivation-burst.json').write_text(json.dumps(dict(parent_sha256=sha(p),candidate_sha256=sha(f),painter_sha256=sha(painter),
 selected_map='Externally selected cu70_memory_map.svh include path; old map first control, crossbank separate A/B',
 scope='Explicit completed RGB bursts and joined drain, bank-aware scanout translation; exact full-system and timing pending'),indent=2)+'\n')
old=json.loads((r/'fpga/experiments/cu66-v70/system/sources.json').read_text())
v71='fpga/experiments/cu66-v71/';replacements={
 'fpga/experiments/cu66-v70/system/cu70_system.sv':v71+'system/cu71_system_burst.sv',
 'fpga/experiments/cu66-v70/receiver/cu70_receiver.sv':v71+'codec/cu71_receiver_bram.sv',
 'fpga/experiments/cu66-v69/integration/cu66_base_pipeline.sv':v71+'codec/cu71_base_pipeline_bram.sv',
 'fpga/experiments/cu66-v69/rows/cu66_rows_sha256.sv':v71+'codec/cu71_rows_sha256_bram.sv',
 'fpga/experiments/cu66-v69/rows/cu66_tile_rows.sv':v71+'rows/cu71_tile_rows.sv',
 'fpga/experiments/cu66-v70/memory/cu70_memory_system.sv':v71+'memory/cu71_memory_system_burst.sv',
 'fpga/experiments/cu66-v70/memory/cu70_word_bridge.sv':v71+'memory/cu71_word_bridge_burst.sv',
 'fpga/experiments/cu66-v70/memory/cu70_tile_memory.sv':v71+'memory/cu71_tile_memory.sv',
 'fpga/experiments/cu66-v70/memory/cu70_sdram_controller.sv':v71+'memory/moonshine_sdram_burst.sv',
 'fpga/experiments/cu66-v70/display/cu70_painter_strip.sv':v71+'display/cu71_painter_strip_burst.sv',
 'fpga/experiments/cu66-v70/display/cu70_scanout.sv':v71+'display/cu71_scanout_banked.sv',
 'fpga/experiments/cu66-v70/display/cu70_lcd_lines.sv':v71+'display/cu71_lcd_lines.sv'}
sources=[replacements.get(n,n) for n in old['rtl_sources'] if not n.endswith(('_sim.sv','_model.sv'))]
(d/'sources-burst.json').write_text(json.dumps(dict(top='cu71_system_burst',sources=sources,include_dirs=old['include_dirs'],SIMULATION=False,
 sources_sha256={n:sha(r/n) for n in sources},scope='Hardware RTL only; verification model wrapper must be added explicitly'),indent=2)+'\n')
print(f)
