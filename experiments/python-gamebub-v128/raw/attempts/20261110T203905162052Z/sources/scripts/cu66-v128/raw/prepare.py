#!/usr/bin/env python3
"""Deterministic V128 complete sparse-validation factor; default is read-only."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
DEST = ROOT / 'fpga/experiments/cu66-v128-raw'
PARENT = ROOT / 'experiments/python-gamebub-v127/integration/results.json'
SOURCES = {
    'sync': ('fpga/experiments/cu66-v91h/br88_packet_ingress_sync_v91h.sv', 'fpga/experiments/cu66-v120-range/br88_packet_ingress_sync_v91h.sv'),
    'wrapper': ('fpga/experiments/cu66-v91h/br88_packet_ingress_v91h.sv', 'fpga/experiments/cu66-v108-capacity/br88_packet_ingress_v91h.sv'),
    'child': ('fpga/experiments/cu66-v91h/br88_pipeline_v91h.sv', 'fpga/experiments/cu66-v127-owner/br88_pipeline_v91h.sv'),
    'scratch': ('fpga/experiments/cu66-v91g2/packed_scratch_v91g2.sv', 'fpga/experiments/cu66-v127-owner/packed_scratch_v91g2.sv'),
}
FIELDS = (('epoch', '[31:0]'), ('block', '[15:0]'), ('index', '[5:0]'), ('value', 'signed [15:0]'), ('band', '[1:0]'))

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def pin(path: Path):
    return {'path': str(path.relative_to(ROOT)), 'sha256': digest(path.read_bytes())}

def port_declarations(direction: str, prefix: str) -> str:
    lines = [f'    {direction} logic {prefix}_select_raw,']
    for lane in ('raw', 'context'):
        for field, width in FIELDS:
            lines.append(f'    {direction} logic {width} {prefix}_{lane}_{field},')
    return '\n'.join(lines) + '\n'

def connections(output_prefix: str, signal_prefix: str, indent: str) -> str:
    lines = [f'{indent}.{output_prefix}_select_raw({signal_prefix}_select_raw),']
    for lane in ('raw', 'context'):
        for field, _ in FIELDS:
            lines.append(f'{indent}.{output_prefix}_{lane}_{field}({signal_prefix}_{lane}_{field}),')
    return '\n'.join(lines) + '\n'

LANES = '''    // V128_RAW_VALIDATION_BEGIN: compare full direct tuples before ingress
    // mode selects Boolean decisions. Stored scratch raw_mode remains a
    // separate format selector, including invalid/unready/transitional views.
    logic [1:0] ingress_epoch_bad;
    logic [7:0] ingress_phase_bad [0:1];
    logic input_epoch_bad;
    for(genvar validation_lane=0;validation_lane<2;validation_lane=validation_lane+1)begin: ingress_validation
        wire [31:0] lane_epoch=validation_lane==0 ? coef_raw_epoch : coef_context_epoch;
        wire [15:0] lane_block=validation_lane==0 ? coef_raw_block : coef_context_block;
        wire [5:0] lane_index=validation_lane==0 ? coef_raw_index : coef_context_index;
        wire signed [15:0] lane_value=validation_lane==0 ? coef_raw_value : coef_context_value;
        wire [1:0] lane_band=validation_lane==0 ? coef_raw_band : coef_context_band;
        wire [31:0] lane_raster_position={10'd0,lane_block,lane_index};
        wire lane_raster_bad=lane_raster_position!=written;
        wire lane_dc_bad=lane_index!=0 || 32'(lane_block)!=written;
        // Preserve the implemented full32 high/block + arbitrary64 rank-mask
        // contract. Literal-position equivalence needs its original owner.
        wire lane_sparse_order_bad=(previous_position[31:22]!=0) ||
            (lane_block<previous_position[21:6]) ||
            ((lane_block==previous_position[21:6]) && rank_threshold_mask[lane_index]);
        wire lane_ac_bad=!band_matches(lane_band,lane_index) || lane_value==0 ||
            (previous_valid && lane_sparse_order_bad);
        assign ingress_epoch_bad[validation_lane]=lane_epoch!=active_epoch;
        for(genvar lane_phase=0;lane_phase<8;lane_phase=lane_phase+1)begin: phase_lane
            assign ingress_phase_bad[validation_lane][lane_phase]=
                ingress_epoch_bad[validation_lane] || lane_band!=2'(lane_phase) ||
                lane_block>=16'(blocks) || lane_value < -2048 || lane_value > 2048 ||
                written>=counts[lane_phase & 3] ||
                (raw_mode ? lane_raster_bad : lane_phase==0 ? lane_dc_bad : lane_ac_bad);
        end
    end
    assign input_epoch_bad=coef_select_raw ? ingress_epoch_bad[0] : ingress_epoch_bad[1];
    // V128_RAW_VALIDATION_END
'''
ASSERTIONS = '''`ifndef SYNTHESIS
    // V128_SELECTED_INPUT_IDENTITIES_BEGIN: valid offers include unready ones.
    // The all-cycle two-state prepared probe independently covers unowned views.
    always_ff @(posedge clk)if(!cancel && !response_failure && state==INGEST && coef_valid)begin
        assert({coef_epoch,coef_block,coef_index,coef_value,coef_band}==
            (coef_select_raw ?
             {coef_raw_epoch,coef_raw_block,coef_raw_index,coef_raw_value,coef_raw_band} :
             {coef_context_epoch,coef_context_block,coef_context_index,coef_context_value,coef_context_band}))
            else $fatal(1,"V128 selected full sparse tuple differs from ingress views");
        assert(input_epoch_bad==(coef_epoch!=active_epoch))
            else $fatal(1,"V128 selected full epoch error class differs");
        assert((coef_select_raw ? ingress_validation[0].lane_raster_bad : ingress_validation[1].lane_raster_bad)==input_raster_bad)
            else $fatal(1,"V128 selected raster format decision differs");
        assert((coef_select_raw ? ingress_validation[0].lane_dc_bad : ingress_validation[1].lane_dc_bad)==input_dc_bad)
            else $fatal(1,"V128 selected DC format decision differs");
        assert((coef_select_raw ? ingress_validation[0].lane_ac_bad : ingress_validation[1].lane_ac_bad)==input_ac_bad)
            else $fatal(1,"V128 selected AC format decision differs");
        assert((coef_select_raw ? ingress_validation[0].lane_sparse_order_bad : ingress_validation[1].lane_sparse_order_bad)==input_sparse_order_bad)
            else $fatal(1,"V128 selected implemented rank-mask decision differs");
    end
    // V128_SELECTED_INPUT_IDENTITIES_END
`endif
'''

def transform(role: str, original: str):
    text = original
    edits = []
    def change(tag: str, old: str, new: str):
        nonlocal text
        assert text.count(old) == 1, (role, tag, text.count(old))
        text = text.replace(old, new)
        edits.append({'tag': tag, 'old': old, 'new': new, 'occurrences': 1})
    if role in ('sync', 'wrapper'):
        anchor = '    output logic [31:0] out_epoch,\n'
        change('direct-view-output-ports', anchor, anchor + port_declarations('output', 'view'))
    if role == 'sync':
        anchor = '        out_epoch=raw_mode ? context_epoch : ctx_epoch;\n'
        assigns = '''        view_select_raw=raw_mode;
        view_raw_epoch=context_epoch; view_raw_block=16'(raw_position>>6);
        view_raw_index=raw_position[5:0]; view_raw_value=raw_coefficient; view_raw_band=2'd0;
        view_context_epoch=ctx_epoch; view_context_block=ctx_block;
        view_context_index=ctx_index; view_context_value=ctx_coefficient; view_context_band=band;
'''
        change('direct-existing-register-views', anchor, anchor + assigns)
    elif role == 'wrapper':
        marker = '    function automatic logic [31:0] capacity_legacy_upper(input logic [27:0] units);\n'
        lines = ["        assign view_select_raw=1'b0;"]
        oldfields = {'epoch':'out_epoch','block':'out_block','index':'out_index','value':'out_coefficient','band':'out_band'}
        for lane in ('raw', 'context'):
            for field, _ in FIELDS:
                lines.append(f'        assign view_{lane}_{field}={oldfields[field]};')
        change('legacy-exact-selected-view-fallback', marker, '\n'.join(lines)+'\n'+marker)
        marker = '    end else begin: synchronous\n'
        tail = text.split(marker, 1)[1]
        needle = '            .out_epoch(out_epoch),\n'
        assert tail.count(needle) == 1
        # Scope selection is recorded as an exact entire synchronous prefix.
        old = marker + tail[:tail.index(needle)+len(needle)]
        change('synchronous-direct-view-forwarding', old, old + connections('view','view','            '))
    elif role == 'child':
        anchor = '    logic [31:0] coef_epoch;\n'
        lines = ['    logic coef_select_raw;']
        for lane in ('raw','context'):
            for field,width in FIELDS:
                lines.append(f'    logic {width} coef_{lane}_{field};')
        change('private-sparse-view-wires',anchor,anchor+'\n'.join(lines)+'\n')
        anchor = '        .out_band(coef_band), .meta_valid(meta_valid), .meta_ready(meta_ready),\n'
        change('packet-direct-view-forwarding',anchor,connections('view','coef','        ')+anchor)
        anchor = '        .coef_value(coef_value), .coef_epoch(coef_epoch),\n'
        change('scratch-direct-view-inputs',anchor,anchor+connections('coef','coef','        '))
    elif role == 'scratch':
        anchor = '    input logic [31:0] coef_epoch,\n'
        change('direct-view-input-ports',anchor,anchor+port_declarations('input','coef'))
        anchor = '    for(genvar checking_phase=0;checking_phase<8;checking_phase=checking_phase+1)begin: phase_validation\n'
        change('full-two-lane-validation',anchor,LANES+ASSERTIONS+anchor)
        old = '''        assign phase_input_bad[checking_phase]=coef_epoch!=active_epoch || coef_band!=2'(checking_phase) ||
            coef_block>=16'(blocks) || coef_value < -2048 || coef_value > 2048 ||
            written>=counts[checking_phase & 3] ||
            (raw_mode ? input_raster_bad : checking_phase==0 ? input_dc_bad : input_ac_bad);
'''
        new = '''        assign phase_input_bad[checking_phase]=coef_select_raw ?
            ingress_phase_bad[0][checking_phase] : ingress_phase_bad[1][checking_phase];
'''
        change('select-complete-Boolean-phase-result',old,new)
        change('preserve-epoch-first-error-class','                            error<=coef_epoch!=active_epoch ? 2 : 3;\n','                            error<=input_epoch_bad ? 2 : 3;\n')
    restored = text
    for edit in reversed(edits):
        assert restored.count(edit['new']) == 1, (role, edit['tag'], 'reverse nonunique')
        restored = restored.replace(edit['new'], edit['old'])
    assert restored == original
    oldguards = re.findall(r'`ifndef SYNTHESIS\n.*?`endif', original, re.S)
    assert all(text.count(block) >= original.count(block) for block in oldguards), role
    assert len(re.findall(r'^\s*module\s+', text, re.M)) == 1
    return text, edits, len(oldguards)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--root-grant')
    args = ap.parse_args()
    parent = json.loads(PARENT.read_text())
    assert parent['status'] == 'PASS_V127_OWNER_FULL_FUNCTIONAL'
    planned = json.loads(Path(__file__).with_name('proposal.json').read_text())
    staged = {}
    for role,(alias, old_path) in SOURCES.items():
        p = ROOT / old_path
        assert pin(p) == planned['source_origins'][role]
        assert parent['source_origins'][alias] == pin(p)
        original = p.read_text()
        result, edits, guards = transform(role, original)
        target = DEST / p.name
        staged[role] = {'alias': alias, 'original': pin(p),
            'candidate': {'path': str(target.relative_to(ROOT)), 'sha256': digest(result.encode())},
            'edits': edits, 'retained_original_guarded_blocks': guards,
            'reverse_reconstruction_exact': True, 'text': result}
    recipe = {'schema':'v128-full-sparse-validation-factor-edit-recipe-v1',
        'status':'SOURCE_PREPARED_NOT_RTL_QUALIFIED' if args.apply else 'READONLY_RECIPE_CHECK_NOT_APPLIED',
        'parent':pin(PARENT), 'preparer':pin(Path(__file__)),
        'declared_public_cycle_delta':0, 'source_register_bits_added':0,
        'source_reset_changes':0,'synthesis_attributes_added':0,
        'expected_changed_aliases':sorted(item['alias'] for item in staged.values()),
        'tuple_bits':72,'validation_lanes':2,'phase_encodings':8,
        'selector_true_lane':0,'selector_false_lane':1,
        'original_assertion_blocks_retained_byte_exact':True,
        'production':{role:{k:v for k,v in item.items() if k!='text'} for role,item in staged.items()}}
    if args.apply:
        assert args.root_grant == 'ROOT_V128_RAW_SOURCE', 'Exact Root source-write grant required'
        assert not DEST.exists(), 'Candidate namespace already exists; no overwrite'
        DEST.mkdir()
        for role,item in staged.items():
            target = ROOT / item['candidate']['path'];target.write_text(item['text'])
            assert pin(target) == item['candidate']
            card={'schema':'v128-raw-single-module-packaging-v1','role':role,
                'alias':item['alias'],'source':pin(target),'module_count':1,
                'split_offsets':None,'byte_exact_single_module_packaging':True}
            target.with_suffix('.packaging.json').write_text(json.dumps(card,indent=2,sort_keys=True)+'\n')
        (DEST/'edit-recipe.json').write_text(json.dumps(recipe,indent=2,sort_keys=True)+'\n')
        source_map={'schema':'v128-raw-selected-source-map-v1','parent':pin(PARENT),
                    'source_origins':{item['alias']:item['candidate'] for item in staged.values()},
                    'changed_origin_count':4,'unchanged_origin_count':14,
                    'public_cycle_delta':0,'source_register_bits_added':0,
                    'edit_recipe':pin(DEST/'edit-recipe.json')}
        (DEST/'source-map.json').write_text(json.dumps(source_map,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'status':recipe['status'],'changed_origins':len(staged),
        'input_pins_verified':True,'all_reversals_exact':True,
        'guard_counts':{role:item['retained_original_guarded_blocks'] for role,item in staged.items()},
        'candidate_sha256':{role:item['candidate']['sha256'] for role,item in staged.items()},
        'edit_counts':{role:len(item['edits']) for role,item in staged.items()}},indent=2,sort_keys=True))

if __name__=='__main__':
    main()
