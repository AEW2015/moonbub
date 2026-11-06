"""Derive isolated DY71 integration; never alter selected RGB timing hierarchy."""
from pathlib import Path
import hashlib,json
r=Path(__file__).resolve().parents[3];d=r/'fpga/experiments/cu66-v71/direct-system';p=r/'fpga/experiments/cu66-v71/codec/timing-v001/cu71_system_timing.sv';s=p.read_text();sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
s=s.replace('module cu71_system_timing #(','module cu71_system_direct #(').replace('    parameter integer USE_STRIP=0,\n','')
old='''    output logic painter_busy,painter_error,output logic [7:0] painter_error_code,
    output logic [31:0] painter_reads,painter_writes,painter_pixels,painter_cycles,''';assert old in s
s=s.replace(old,'''    output wire [31:0] profile_magic,profile_abi,profile_capabilities,
    output wire cache_prepare_busy,cache_prepare_fault,
    output wire [31:0] cache_dma_reads,cache_line_misses,cache_generated_lines,cache_prepare_cycles,
    output wire [31:0] cache_accepted_prepares,cache_rejected_prepares,cache_rejected_descriptors,
    output wire [31:0] cache_unowned_responses,''')
s=s.replace('    cu71_receiver_timing #(','    cu71_receiver_direct #(').replace('    cu71_memory_system_burst #(','    cu71_memory_system_direct #(')
s=s.replace('front_rgb_slot','front_cache_slot').replace('paint_rgb_slot','paint_cache_slot').replace('presentation_rgb_slot','presentation_cache_slot').replace('presented_rgb_slot','presented_cache_slot')
s=s.replace('painter_drained','cache_worker_drained').replace('paint_','cache_prepare_')
# Unused scalar painter/LCD clients are held inactive. HUD retains the actual
# existing permission, completion-count and response/recycling state machine.
anchor="    assign l_req_valid=1'b0;assign l_req_write=1'b0;";assert anchor in s
s=s.replace(anchor,"    assign p_req_valid=1'b0;assign p_req_write=1'b0;assign p_req_addr=0;assign p_req_data=0;assign p_rsp_ready=1'b1;\n"+anchor)
s=s.replace('        cache_prepare_y=canonical_base(candidate_bank);cache_prepare_u=cache_prepare_y+24\'d172800;cache_prepare_v=cache_prepare_y+24\'d216000;\n','')
s=s.replace("        cache_prepare_hud=selected_hud_base;cache_prepare_rgb=cache_prepare_cache_slot?RGB1_BASE:RGB0_BASE;\n",'')
s=s.replace('        cache_worker_drained=!painter_busy&&!rgb_busy;','        cache_worker_drained=adapter_worker_drained;')
s=s.replace('        cache_prepare_result_valid=painter_native_valid||(painter_inflight&&!painter_busy&&painter_error);\n','').replace('        cache_prepare_result_success=painter_native_valid&&!painter_error;\n','')
s=s.replace('painter_inflight<=0;','')
s=s.replace('            if(cache_prepare_start_valid&&cache_prepare_start_ready)painter_inflight<=1;\n','')
s=s.replace('            if(cache_prepare_abort||(cache_prepare_result_valid&&cache_prepare_result_ready))\n','')
s=s.replace('.cache_prepare_result_success,.cache_worker_drained,','.cache_prepare_result_success,.cache_prepare_result_slot,.cache_worker_drained,')
# Replace renderer/scanout block completely. RGB backend ports remain tied off.
start=s.index('    generate if(USE_STRIP!=0)');s=s[:start]+'''
    assign profile_magic=32'h44593731;
    assign profile_abi=32'h00010000;
    assign profile_capabilities=32'h0000000f;
    assign rgb_req_valid=1'b0;assign rgb_req_addr=0;assign rgb_req_data=0;
    assign rgb_req_mask=16'hffff;assign rgb_rsp_ready=1'b1;assign rgb_abort_i=1'b0;
    logic adapter_worker_drained,cache_prepare_result_slot;
    logic owner_prepare_valid,owner_prepare_ready,owner_prepare_slot;
    logic[63:0]owner_prepare_generation;logic[31:0]owner_prepare_frame_id;
    logic[1:0]owner_prepare_canonical_bank,owner_prepare_hud_bank;
    logic owner_prepared_valid,owner_prepared_ready,owner_prepared_slot,owner_prepared_error;
    logic[63:0]owner_prepared_generation;logic[31:0]owner_prepared_frame_id;
    logic[7:0]owner_prepared_reason,cache_prepare_result_reason;
    logic owner_abort_valid,owner_abort_ready,owner_abort_slot,owner_abort_done,owner_abort_error;
    logic[63:0]owner_abort_generation;logic[31:0]owner_abort_frame_id;
    logic[7:0]direct_first_fault;logic[63:0]direct_first_fault_generation;logic[31:0]direct_first_fault_frame;
    cu71_direct_prepare_adapter prepare_adapter(
      .clk,.rst,.kill(cache_prepare_abort),.start_valid(cache_prepare_start_valid),.start_ready(cache_prepare_start_ready),
      .generation(active_generation),.frame_id(active_frame_id),.canonical_bank(candidate_bank),.hud_bank(candidate_bank),.cache_slot(cache_prepare_cache_slot),
      .result_valid(cache_prepare_result_valid),.result_ready(cache_prepare_result_ready),.result_generation(cache_prepare_result_generation),
      .result_frame_id(cache_prepare_result_frame_id),.result_slot(cache_prepare_result_slot),.result_success(cache_prepare_result_success),.result_reason(cache_prepare_result_reason),
      .worker_drained(adapter_worker_drained),.busy(cache_prepare_busy),.fault(cache_prepare_fault),
      .descriptor_accepted(presentation_valid&&presentation_ready),.descriptor_generation(presentation_generation),.descriptor_frame_id(presentation_frame_id),.descriptor_slot(presentation_cache_slot),
      .owner_prepare_valid,.owner_prepare_ready,.owner_prepare_generation,.owner_prepare_frame_id,.owner_prepare_canonical_bank,.owner_prepare_hud_bank,.owner_prepare_slot,
      .owner_prepared_valid,.owner_prepared_ready,.owner_prepared_generation,.owner_prepared_frame_id,.owner_prepared_slot,.owner_prepared_error,.owner_prepared_reason,
      .owner_abort_valid,.owner_abort_ready,.owner_abort_generation,.owner_abort_frame_id,.owner_abort_slot,.owner_abort_done,.owner_abort_error);
    cu71_direct_scanout scanout(
      .mem_clk(clk),.rst,.pixel_clk,.pixel_reset_n,
      .prepare_valid(owner_prepare_valid),.prepare_ready(owner_prepare_ready),.prepare_generation(owner_prepare_generation),.prepare_frame_id(owner_prepare_frame_id),
      .prepare_canonical_bank(owner_prepare_canonical_bank),.prepare_hud_bank(owner_prepare_hud_bank),.prepare_cache_slot(owner_prepare_slot),
      .prepared_valid(owner_prepared_valid),.prepared_ready(owner_prepared_ready),.prepared_generation(owner_prepared_generation),.prepared_frame_id(owner_prepared_frame_id),
      .prepared_cache_slot(owner_prepared_slot),.prepared_error(owner_prepared_error),.prepared_reason(owner_prepared_reason),
      .prepare_abort_valid(owner_abort_valid),.prepare_abort_ready(owner_abort_ready),.prepare_abort_generation(owner_abort_generation),.prepare_abort_frame_id(owner_abort_frame_id),
      .prepare_abort_cache_slot(owner_abort_slot),.abort_done(owner_abort_done),.abort_error(owner_abort_error),
      .descriptor_valid(presentation_valid),.descriptor_ready(presentation_ready),.descriptor_generation(presentation_generation),.descriptor_frame_id(presentation_frame_id),.descriptor_cache_slot(presentation_cache_slot),
      .presented(lcd_presented),.error(lcd_error),.front_valid(lcd_front_valid),.front_cache_slot(lcd_front_slot),.front_generation(lcd_front_generation),.front_frame_id(lcd_front_frame_id),
      .pending_valid(lcd_pending),.presented_count(lcd_presented_count),.frame_boundary(lcd_frame_boundary),.scanout_drained(lcd_scanout_drained),
      .lcd_req_valid,.lcd_req_ready,.lcd_req_addr,.lcd_rsp_valid,.lcd_rsp_ready,.lcd_rsp_data,.lcd_rsp_error,.lcd_abort_i,.lcd_busy,.lcd_aborted,
      .underruns(lcd_underruns),.dma_reads(cache_dma_reads),.unowned_dma_responses(cache_unowned_responses),
      .accepted_prepares(cache_accepted_prepares),.rejected_prepares(cache_rejected_prepares),.rejected_descriptors(cache_rejected_descriptors),
      .memory_errors(lcd_memory_errors),.line_cache_misses(cache_line_misses),.generated_lines(cache_generated_lines),.prepare_cycles(cache_prepare_cycles),
      .first_fault(direct_first_fault),.first_fault_generation(direct_first_fault_generation),.first_fault_frame_id(direct_first_fault_frame),
      .hsync,.vsync,.data_enable,.physical_x,.physical_y,.red,.green,.blue);
endmodule
'''
out=d/'cu71_system_direct.sv';assert not out.exists();out.write_text(s,newline='\n')
spec=json.loads((p.parent/'sources.json').read_text());drop=['cu70_painter','cu71_painter_strip_burst','cu71_scanout_banked','cu71_lcd_lines']
sources=[]
for n in spec['sources']:
 f=Path(n)
 if f.stem in drop:continue
 if f.stem=='cu71_system_timing':n=out.relative_to(r).as_posix()
 elif f.stem=='cu71_receiver_timing':n=(d/'cu71_receiver_direct.sv').relative_to(r).as_posix()
 elif f.stem in ['cu71_tile_memory','cu71_word_bridge_burst','cu71_memory_system_burst']:
  stem={'cu71_tile_memory':'cu71_tile_memory_direct','cu71_word_bridge_burst':'cu71_word_bridge_direct','cu71_memory_system_burst':'cu71_memory_system_direct'}[f.stem];n=(f.parent/(stem+'.sv')).as_posix()
 sources.append(n)
sources.append((d/'cu71_direct_prepare_adapter.sv').relative_to(r).as_posix())
for name in ['cu71_direct_scanout','cu71_cache_dma','cu71_direct_cache','cu71_yuv_pixel_pipe','cu71_lcd_lines_direct']:sources.append('fpga/experiments/cu66-v71/direct-display/'+name+'.sv')
(d/'sources.json').write_text(json.dumps({'top':'cu71_system_direct','sources':sources,'include_dirs':spec['include_dirs'],'sources_sha256':{n:sha(r/n)for n in sources},'profile_magic':'0x44593731','profile_abi':'0x00010000','capabilities':'0x0f','SIMULATION':False,'scope':'Experimental DY71 native integration, tile-major canonical and direct YUV cache contexts. NoRGBtraffic/noCSR/network compatibility. Complete tests and physical timing pending.'},indent=2)+'\n')
(d/'system-derivation.json').write_text(json.dumps({'parent':p.relative_to(r).as_posix(),'parent_sha256':sha(p),'candidate':out.relative_to(r).as_posix(),'candidate_sha256':sha(out),'profile':'DY71','hardware':False},indent=2)+'\n');print('PREPARED_DY71',sha(out))
