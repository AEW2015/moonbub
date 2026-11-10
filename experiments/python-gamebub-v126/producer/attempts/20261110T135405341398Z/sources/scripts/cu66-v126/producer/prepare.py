#!/usr/bin/env python3
"""Prepare reversible existing-edge producer geometry stages; never compiles."""
import hashlib
import json
import re
from pathlib import Path

R=Path(__file__).resolve().parents[3]
BASE=R/'fpga/experiments/cu66-v124-owner/cs88_coefficients_v91k.sv'
S=R/'fpga/experiments/cu66-v126-producer'
BASE_SHA='963b46c3449d3a31e5ae85763f0681c6e68156c8d8c2c4c330d834ed2554fb53'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')


def main():
    assert sha(BASE)==BASE_SHA
    card=json.loads((R/'experiments/python-gamebub-v125/integration/results.json').read_text())
    assert len(card['source_origins'])==18
    assert all(sha(R/m['path'])==m['sha256'] for m in card['source_origins'].values())
    S.mkdir(parents=True,exist_ok=True);before=BASE.read_text();text=before;edits=[]
    def edit(old,new,why):
        nonlocal text
        assert text.count(old)==1,old
        text=text.replace(old,new,1);edits.append(dict(before=old,after=new,reason=why))
    edit('    logic [10:0] producer_cell_cache;', '''    logic [10:0] producer_cell_cache;
    // V126: private geometry stages, with no public state/cycle added.
    logic [12:0] prepared_successor_tile;
    logic [10:0] prepared_successor_cell;
`ifndef SYNTHESIS
    logic address_owner_valid, cell_owner_valid;
    logic [31:0] address_owner_frame, cell_owner_frame, cell_owner_child_epoch;
    logic [1:0] address_owner_plane, cell_owner_plane;
    logic [12:0] address_owner_tile, cell_owner_tile, cell_owner_address;
`endif''', 'Add exactly24 unreset production payload bits; all owner fields are verification-only.')
    addition='''
    // Successor address is ready before MAP_REQ. On a current-tile advance,
    // next_address is literal uint13(old tile+2), not an add feeding the ROM.
    task automatic prepare_successor_address(input logic [12:0] next_tile,
                                             input logic [12:0] next_address);
        prepared_successor_tile<=next_address;
`ifndef SYNTHESIS
        address_owner_valid<=1;address_owner_frame<=frame_epoch;
        address_owner_plane<=plane;address_owner_tile<=next_tile;
        cell_owner_valid<=0;
`endif
    endtask
    // This unreset payload can sample an old MAP_REQ on a cancellation edge.
    // Logical cancellation invalidates its owner in the original priority tree.
    always_ff @(posedge clk)if(state==MAP_REQ)
        prepared_successor_cell<=quant_cell(plane,prepared_successor_tile);
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!reset&&!abort_packet&&!accepted_start&&
        !(REFILL_OVERLAP!=0&&frame_running&&queue_error!=0)&&
        !(frame_running&&child_owned&&child_error!=0))begin
        if(state==MAP_REQ&&tile_cursor<tiles(plane))begin
            assert(address_owner_valid&&address_owner_frame==frame_epoch&&
                address_owner_plane==plane&&address_owner_tile==tile_cursor&&
                prepared_successor_tile==tile_cursor+13'd1)
                else $fatal(1,"V126 full13 successor address ownership");
        end
        if((state==MAP_WAIT&&lookup_rsp&&lookup_mode!=2)||
           (state==DISPATCH&&!(child_out_valid&&!child_owner_match)&&
            out_valid&&out_ready&&out_index==63&&
            32'(expected_block)+1!=32'(selected_blocks)))begin
            assert(address_owner_valid&&address_owner_frame==frame_epoch&&
                address_owner_plane==plane&&address_owner_tile==tile_cursor&&
                prepared_successor_tile==tile_cursor+13'd1)
                else $fatal(1,"V126 address key stable at original advance");
            assert(cell_owner_valid&&cell_owner_frame==frame_epoch&&
                cell_owner_child_epoch==current_child_epoch&&
                cell_owner_plane==plane&&cell_owner_tile==tile_cursor&&
                cell_owner_address==prepared_successor_tile&&
                prepared_successor_cell==quant_cell(plane,tile_cursor+13'd1))
                else $fatal(1,"V126 complete successor cell ownership");
        end
    end
`endif
'''
    edit('    assign frame_running=frame_running_owned;',addition+'    assign frame_running=frame_running_owned;',
         'Separate ROM-only MAP_REQ payload from increment, with consumer assertions under exact original fault priority.')
    edit('''        if(reset||abort_packet)begin
            begin state<=IDLE;frame_running_owned<=1'b0; end error<=0;''', '''        if(reset||abort_packet)begin
`ifndef SYNTHESIS
            address_owner_valid<=0;cell_owner_valid<=0;
`endif
            begin state<=IDLE;frame_running_owned<=1'b0; end error<=0;''', 'Original reset/abort current-cache values retained; only new owner validity resets.')
    edit('''            if(accepted_start)begin
                begin state<=ADMIT;''', '''            if(accepted_start)begin
`ifndef SYNTHESIS
                address_owner_valid<=0;cell_owner_valid<=0;
`endif
                begin state<=ADMIT;''', 'Accepted start revokes prior frame; blocked raw start continues the original frame untouched.')
    edit('''                if(REFILL_OVERLAP!=0&&frame_running&&queue_error!=0)begin
                    begin state<=FAILED;''', '''                if(REFILL_OVERLAP!=0&&frame_running&&queue_error!=0)begin
`ifndef SYNTHESIS
                    address_owner_valid<=0;cell_owner_valid<=0;
`endif
                    begin state<=FAILED;''', 'Queue error retains first priority and invalidates unobservable preparation.')
    edit('''                end else if(frame_running&&child_owned&&child_error!=0)begin
                    begin state<=FAILED;''', '''                end else if(frame_running&&child_owned&&child_error!=0)begin
`ifndef SYNTHESIS
                    address_owner_valid<=0;cell_owner_valid<=0;
`endif
                    begin state<=FAILED;''', 'Child error keeps original priority ahead of state-specific advance.')
    edit('''                        if(fork_blocks[plane]==0)begin state<=NEXT_PLANE;frame_running_owned<=1'b1; end ''', '''                        if(fork_blocks[plane]==0)begin
`ifndef SYNTHESIS
                            address_owner_valid<=0;cell_owner_valid<=0;
`endif
                            begin state<=NEXT_PLANE;frame_running_owned<=1'b1; end
                        end ''', 'Empty plane creates no address/ROM work and retains original held current geometry.')
    edit('''                            tile_cursor<=0;producer_cell_cache<=0;expected_block<=0;refill_cursor<=0;''', '''                            prepare_successor_address(13'd0,13'd1);
                            tile_cursor<=0;producer_cell_cache<=0;expected_block<=0;refill_cursor<=0;''', 'Nonempty plane establishes successor1 at the original zero-tile writer.')
    edit('''                    MAP_REQ:begin
                        if(tile_cursor>=tiles(plane))''', '''                    MAP_REQ:begin
`ifndef SYNTHESIS
                        if(tile_cursor<tiles(plane))begin
                            cell_owner_valid<=1;cell_owner_frame<=frame_epoch;
                            cell_owner_child_epoch<=current_child_epoch;
                            cell_owner_plane<=plane;cell_owner_tile<=tile_cursor;
                            cell_owner_address<=prepared_successor_tile;
                        end else begin address_owner_valid<=0;cell_owner_valid<=0;end
`endif
                        if(tile_cursor>=tiles(plane))''', 'Bind ROM result to actual request geometry and current allocated child epoch; malformed bound keeps error67.')
    edit('''                        end else begin tile_cursor<=tile_cursor+1;producer_cell_cache<=quant_cell(plane,tile_cursor+13'd1);begin state<=MAP_REQ;frame_running_owned<=1'b1; end end''', '''                        end else begin prepare_successor_address(tile_cursor+13'd1,tile_cursor+13'd2);tile_cursor<=tile_cursor+1;producer_cell_cache<=prepared_successor_cell;begin state<=MAP_REQ;frame_running_owned<=1'b1; end end''', 'MAP_WAIT skip consumes owned ROM result on old edge and prepares following full13 address in parallel.')
    edit('''                        if(child_out_valid&&!child_owner_match)begin begin state<=FAILED;''', '''                        if(child_out_valid&&!child_owner_match)begin
`ifndef SYNTHESIS
                            address_owner_valid<=0;cell_owner_valid<=0;
`endif
                            begin state<=FAILED;''', 'Bad child owner retains error67 precedence over last coefficient acceptance.')
    edit('''                            else begin tile_cursor<=tile_cursor+1;producer_cell_cache<=quant_cell(plane,tile_cursor+13'd1);begin state<=MAP_REQ;frame_running_owned<=1'b1; end end''', '''                            else begin prepare_successor_address(tile_cursor+13'd1,tile_cursor+13'd2);tile_cursor<=tile_cursor+1;producer_cell_cache<=prepared_successor_cell;begin state<=MAP_REQ;frame_running_owned<=1'b1; end end''', 'Nonterminal accepted coefficient63 consumes owned ROM result; terminal block path is unchanged.')
    edit('''                    NEXT_PLANE:begin
                        if(plane==2)''', '''                    NEXT_PLANE:begin
`ifndef SYNTHESIS
                        address_owner_valid<=0;cell_owner_valid<=0;
`endif
                        if(plane==2)''', 'Revoke prior plane ownership while preserving direct current-cell recomputation and empty-plane intermediate values.')
    candidate=S/BASE.name;candidate.write_text(text)
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',before,re.S):assert block in text
    assert text.count('(* keep = "true" *)')==before.count('(* keep = "true" *)')==1
    assert 'DONT_TOUCH' not in text
    reverse=text
    for e in reversed(edits):
        assert reverse.count(e['after'])==1;reverse=reverse.replace(e['after'],e['before'],1)
    assert reverse==before
    save(S/'edit-recipe.json',dict(schema='v126-producer-production-derivation-v1',original=str(BASE.relative_to(R)),original_sha256=sha(BASE),candidate=str(candidate.relative_to(R)),candidate_sha256=sha(candidate),edits=edits,added_source_payload_bits=24,old_assertions_removed=0,old_private_value_contract_changes=0,added_public_cycles=0,added_synthesis_attributes=0,unchanged_other_origins=17))
    save(S/'packaging.json',dict(schema='v126-producer-single-module-packaging-v1',production_sha256=sha(candidate),fragments=[dict(filename=candidate.name,bytes=candidate.stat().st_size,sha256=sha(candidate))],split_byte_offsets=[]))
    print('V126_PRODUCER_PREPARED',sha(candidate))


if __name__=='__main__':main()
