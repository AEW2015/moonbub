#!/usr/bin/env python3
"""Reversible V125 tile-control preparation. No compile or simulation."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'fpga/experiments/cu66-v122-bounds'
AREA = ROOT / 'fpga/experiments/cu66-v125-tile'
BASE_SHA = '54dc87ded7abf37a9dc6757a4dabe62d6530f8127989d0fef2a4fc0f723376cf'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    AREA.mkdir(parents=True, exist_ok=True)
    original = BASE / 'cs88_admission_v91i2a.sv'
    assert sha(original) == BASE_SHA
    before = original.read_text()
    text = before
    edits = []

    def edit(old, new, reason):
        nonlocal text
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
        edits.append(dict(before=old, after=new, reason=reason))

    addition = '''
    // V125: register literal full32 scalar decisions at existing coordinate
    // writers. Group equality is prepared on tag commit after GROUP_BEGIN has
    // registered group_end; it never extends the tile+16/min input cone.
    // All payload is unreset and consumed only under complete owned keys.
    logic prepared_tile_hidden, prepared_tile_terminal, prepared_group_terminal;
`ifndef SYNTHESIS
    logic tile_pred_owner_valid, group_pred_owner_valid;
    logic [31:0] tile_pred_owner_epoch, tile_pred_owner_tile;
    logic [1:0] tile_pred_owner_plane;
    logic [31:0] group_pred_owner_epoch, group_pred_owner_tile, group_pred_owner_end;
    logic [1:0] group_pred_owner_plane;
`endif
    task automatic prepare_tile_key(input logic [1:0] next_plane,
                                    input logic [31:0] next_tile);
        prepared_tile_hidden<=hidden(next_plane,next_tile);
        prepared_tile_terminal<=next_tile==tile_count(next_plane);
`ifndef SYNTHESIS
        tile_pred_owner_valid<=1;
        tile_pred_owner_epoch<=receipt_epoch;
        tile_pred_owner_plane<=next_plane;tile_pred_owner_tile<=next_tile;
        group_pred_owner_valid<=0;
`endif
    endtask
    task automatic prepare_group_key(input logic [1:0] next_plane,
                                     input logic [31:0] next_tile,
                                     input logic [31:0] owned_end);
        // Atomic group snapshot intentionally refreshes all three scalars,
        // including tile decisions when the tag commit leaves tile unchanged.
        prepare_tile_key(next_plane,next_tile);
        prepared_group_terminal<=next_tile==owned_end;
`ifndef SYNTHESIS
        group_pred_owner_valid<=1;
        group_pred_owner_epoch<=receipt_epoch;
        group_pred_owner_plane<=next_plane;group_pred_owner_tile<=next_tile;
        group_pred_owner_end<=owned_end;
`endif
    endtask
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&
        (state==KEY_TILE||state==GROUP_TILE||state==GROUP_NEXT))begin
        assert(tile_pred_owner_valid&&tile_pred_owner_epoch==receipt_epoch&&
            tile_pred_owner_plane==plane&&tile_pred_owner_tile==tile)
            else $fatal(1,"V125 full tile predicate owner");
        assert(prepared_tile_hidden==hidden(plane,tile)&&
            prepared_tile_terminal==(tile==tile_count(plane)))
            else $fatal(1,"V125 literal full32 tile predicates");
        if(state==GROUP_TILE)begin
            assert(group_pred_owner_valid&&group_pred_owner_epoch==receipt_epoch&&
                group_pred_owner_plane==plane&&group_pred_owner_tile==tile&&
                group_pred_owner_end==group_end)
                else $fatal(1,"V125 full group predicate owner");
            assert(prepared_group_terminal==(tile==group_end))
                else $fatal(1,"V125 literal full32 group predicate");
        end
    end
`endif
'''
    edit('    // V112_VISIBILITY_BEGIN:', addition + '\n    // V112_VISIBILITY_BEGIN:',
         'Add three scalar payload FFs and verification-only complete-key owners; no reset or synthesis directives.')
    edit('            coord_valid<=0;\n            state<=IDLE;',
         '''            coord_valid<=0;
`ifndef SYNTHESIS
            tile_pred_owner_valid<=0;group_pred_owner_valid<=0;
`endif
            state<=IDLE;''', 'Keep original reset/start/abort precedence; invalidate verification ownership only.')
    edit('                        plane<=0;tile<=0;mode_cursor<=128;',
         '                        prepare_tile_key(2\'d0,32\'d0);\n                        plane<=0;tile<=0;mode_cursor<=128;',
         'Successful header establishes first tile predicate key on original edge.')
    edit('''                KEY_TILE:begin
                    if(tile==tile_count(plane))begin
                        clear_coordinate();
                        tile<=0;''', '''                KEY_TILE:begin
                    if(prepared_tile_terminal)begin
                        clear_coordinate();
                        prepare_tile_key(plane==2?plane:plane+2'd1,32'd0);
                        tile<=0;''', 'Keep equality/terminal state semantics; prepare exact successor plane and zero tile.')
    edit('''                        if(!hidden(plane,tile))residual_tile();
                        advance_coordinate(1);tile<=tile+1;''', '''                        if(!prepared_tile_hidden)residual_tile();
                        prepare_tile_key(plane,tile+32'd1);
                        advance_coordinate(1);tile<=tile+1;''', 'KEY nonterminal consumes cached visibility and prepares wrapping uint32 successor.')
    edit('''                GROUP_BEGIN:begin
                    group_end<=tile+16<tile_count(plane)?tile+16:tile_count(plane);''', '''                GROUP_BEGIN:begin
`ifndef SYNTHESIS
                    group_pred_owner_valid<=0;
`endif
                    group_end<=tile+16<tile_count(plane)?tile+16:tile_count(plane);''',
         'Keep original min expression byte-identical; group ownership waits for stable-end tag commit.')
    edit('''                            advance_coordinate(1);tile<=tile+1;state<=GROUP_TILE;''', '''                            prepare_group_key(plane,tile+32'd1,group_end);
                            advance_coordinate(1);tile<=tile+1;state<=GROUP_TILE;''',
         'Mixed bit consume prepares successor group tuple on original tile write.')
    edit('''                            group_tag<={first_tag_bit,bit_cache[7]};
                            if(group_visible==0)begin''', '''                            group_tag<={first_tag_bit,bit_cache[7]};
                            prepare_group_key(plane,tile,group_end);
                            if(group_visible==0)begin''',
         'Real architectural tag commit samples already-registered group end and atomically owns scalar tuple.')
    edit('''                                else begin advance_coordinate(5'(group_end-tile));tile<=group_end;state<=GROUP_NEXT;end''', '''                                else begin prepare_group_key(plane,group_end,group_end);advance_coordinate(5'(group_end-tile));tile<=group_end;state<=GROUP_NEXT;end''',
         'Accepted hidden-only group overrides the tag snapshot with its actual successor tile.')
    edit('''                GROUP_TILE:begin
                    if(tile==group_end)begin''', '''                GROUP_TILE:begin
                    if(prepared_group_terminal)begin''', 'Terminal group equality retains first-fault precedence.')
    edit('''                    end else if(hidden(plane,tile)||group_tag==0)begin
                        
                        advance_coordinate(1);tile<=tile+1;''', '''                    end else if(prepared_tile_hidden||group_tag==0)begin
                        
                        prepare_group_key(plane,tile+32'd1,group_end);
                        advance_coordinate(1);tile<=tile+1;''', 'Hidden/tag-zero step retains mode/residual behavior and exact successor.')
    edit('''                        residual_tile();advance_coordinate(1);tile<=tile+1;''', '''                        prepare_group_key(plane,tile+32'd1,group_end);
                        residual_tile();advance_coordinate(1);tile<=tile+1;''', 'Tag-one residual step retains original write edge.')
    edit('''                GROUP_NEXT:begin
                    if(tile==tile_count(plane))begin
                        if(plane==2)state<=MODE_END;
                        else begin clear_coordinate();plane<=plane+1;tile<=0;state<=GROUP_BEGIN;end''', '''                GROUP_NEXT:begin
                    if(prepared_tile_terminal)begin
                        if(plane==2)state<=MODE_END;
                        else begin prepare_tile_key(plane+2'd1,32'd0);clear_coordinate();plane<=plane+1;tile<=0;state<=GROUP_BEGIN;end''',
         'Plane terminal equality and modulo two-bit successor remain exact.')
    edit('''            end else if(state==KEY_TILE&&tile!=tile_count(plane))begin''', '''            end else if(state==KEY_TILE&&!prepared_tile_terminal)begin''', 'Canonical mode port uses same cached KEY terminal decision.')
    edit('''                mode_write_data=hidden(plane,tile)?2'd1:2'd2;''', '''                mode_write_data=prepared_tile_hidden?2'd1:2'd2;''', 'Canonical mode port KEY visibility remains coupled to parser decision.')
    edit('''            end else if(state==GROUP_TILE&&tile!=group_end)begin
                if(hidden(plane,tile)||group_tag==0)begin''', '''            end else if(state==GROUP_TILE&&!prepared_group_terminal)begin
                if(prepared_tile_hidden||group_tag==0)begin''', 'Canonical group mode port shares exact terminal and visibility decisions.')
    edit('''                    mode_write_data=hidden(plane,tile)?2'd1:2'd0;''', '''                    mode_write_data=prepared_tile_hidden?2'd1:2'd0;''', 'Preserve hidden/tag-zero mode values on original edge.')
    candidate = AREA / original.name
    candidate.write_text(text)
    save(AREA/'edit-recipe.json', dict(schema='v125-tile-production-derivation-v1',
        original=str(original.relative_to(ROOT)), original_sha256=sha(original),
        candidate=str(candidate.relative_to(ROOT)), candidate_sha256=sha(candidate), edits=edits,
        added_source_payload_bits=3, old_assertions_removed=0, old_private_value_contract_changes=0,
        added_public_cycles=0, added_synthesis_attributes=0))
    data=candidate.read_bytes()
    offsets=[data.index(b'module cu66_scale_tdp_v107 ('),data.index(b'module cu66_mode_store_v107 (')]
    bounds=[0]+offsets+[len(data)]
    save(AREA/'packaging.json',dict(schema='v125-lossless-admission-packaging-v1',
        production=str(candidate.relative_to(ROOT)),production_sha256=sha(candidate),split_byte_offsets=offsets,
        fragments=[dict(filename=name,bytes=bounds[i+1]-bounds[i],sha256=hashlib.sha256(data[bounds[i]:bounds[i+1]]).hexdigest())
                   for i,name in enumerate(['cs88_admission_v91i2a.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv'])]))
    # Source preparation is reversible without invoking any older prepare entry point.
    reverse=text
    for e in reversed(edits):
        assert reverse.count(e['after'])==1
        reverse=reverse.replace(e['after'],e['before'],1)
    assert reverse==before
    import re
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',before,re.S):assert block in text
    assert 'KEEP' not in text and 'DONT_TOUCH' not in text
    print('V125_TILE_SOURCE_PREPARED',sha(candidate))


if __name__=='__main__':
    main()
