#!/usr/bin/env python3
"""Reversible V122 admission bounds preparation; never runs a simulator."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT/'fpga/experiments/cu66-v120-admission-match'
SRC = ROOT/'fpga/experiments/cu66-v122-bounds'
VER = SRC/'verification'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, value):
    p.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

def main():
    VER.mkdir(parents=True, exist_ok=True)
    original=OLD/'cs88_admission_v91i2a.sv'
    assert sha(original)=='275071538fd2de34246bad17ddbeb170f356e8f41e6162969b7a97ab3f45ef3f'
    source=original.read_text();edits=[]
    def edit(before,after,reason):
        nonlocal source
        assert source.count(before)==1,before
        source=source.replace(before,after,1)
        edits.append(dict(before=before,after=after,reason=reason))
    addition='''
    // V122: retain the literal full64 length domain and the separate uint32
    // number-bound wrap. Existing final-word load phases perform preparation;
    // CHUNK_NUMBER and CHUNK_LENGTH keep their original public consume edges.
    logic [63:0] bounds_cursor_base, bounds_word_base, bounds_length_total;
    logic [31:0] bounds_number_plus12;
    logic prepared_number_outside, prepared_length_invalid;
    always_ff @(posedge clk)begin
        if(state==WORD_BYTE&&word_index==2)begin
            bounds_cursor_base<={32'd0,cursor}+64'd4;
            bounds_number_plus12<=cursor+32'd12;
        end
        if(state==FETCH_REQ&&word_index==3&&word_return==CHUNK_LENGTH)
            bounds_word_base<=bounds_cursor_base+{32'd0,word_acc,8'd0};
        if(state==FETCH_WAIT&&word_index==3&&word_return==CHUNK_LENGTH)
            bounds_length_total<=bounds_word_base+{56'd0,ram_data};
        if(state==WORD_BYTE&&word_index==3)begin
            if(word_return==CHUNK_NUMBER)
                prepared_number_outside<=bounds_number_plus12>residual_end;
            if(word_return==CHUNK_LENGTH)
                prepared_length_invalid<=({word_acc,byte_value}<32'd46)||
                    ({word_acc,byte_value}>selected_limit)||
                    (bounds_length_total>{32'd0,residual_end});
        end
    end
`ifndef SYNTHESIS
    logic bounds_owner_valid;
    logic [2:0] bounds_owner_phases;
    logic [31:0] bounds_owner_cursor, bounds_owner_end, bounds_owner_epoch;
    logic [31:0] bounds_owner_limit;
    logic [1:0] bounds_owner_plane;
    logic [7:0] bounds_owner_return;
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)begin
            bounds_owner_valid<=0;bounds_owner_phases<=0;
        end else if(state==WORD_BYTE&&word_index==2)begin
            bounds_owner_valid<=1;bounds_owner_phases<=3'b001;
            bounds_owner_cursor<=cursor;bounds_owner_end<=residual_end;
            bounds_owner_epoch<=receipt_epoch;bounds_owner_plane<=plane;
            bounds_owner_limit<=selected_limit;bounds_owner_return<=word_return;
        end else if(state==FETCH_REQ&&word_index==3&&word_return==CHUNK_LENGTH)
            bounds_owner_phases<=bounds_owner_phases|3'b010;
        else if(state==FETCH_WAIT&&word_index==3&&word_return==CHUNK_LENGTH)
            bounds_owner_phases<=bounds_owner_phases|3'b100;
        else if(state==CHUNK_NUMBER||state==CHUNK_LENGTH)
            bounds_owner_valid<=0;
    end
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&
        (state==CHUNK_NUMBER||state==CHUNK_LENGTH))begin
        assert(bounds_owner_valid&&bounds_owner_cursor==cursor&&
            bounds_owner_end==residual_end&&bounds_owner_epoch==receipt_epoch&&
            bounds_owner_plane==plane&&bounds_owner_return==state&&
            bounds_owner_limit==selected_limit&&bounds_owner_phases[0])
            else $fatal(1,"V122 bounds complete owner mismatch");
        if(state==CHUNK_NUMBER)begin
            assert(bounds_number_plus12==32'(cursor+32'd12))
                else $fatal(1,"V122 literal uint32 number sum");
            assert(prepared_number_outside==(cursor+12>residual_end))
                else $fatal(1,"V122 literal uint32 number bound");
        end else begin
            assert(bounds_owner_phases==3'b111&&
                bounds_length_total=={32'd0,cursor}+64'd4+{32'd0,word_value})
                else $fatal(1,"V122 full64 prepared sum mismatch");
            assert(prepared_length_invalid==(word_value<46||word_value>selected_limit||
                {32'd0,cursor}+4+{32'd0,word_value}>{32'd0,residual_end}))
                else $fatal(1,"V122 literal full64 length predicate");
        end
    end
`endif
'''
    edit('    // V116_SELECTED_END\n','    // V116_SELECTED_END\n'+addition,
         'Separate full64 arithmetic across existing final-word phases; retain unreset unowned payload and verification-only owner validity.')
    edit('                    else if(cursor+12>residual_end)reject(13);',
         '                    else if(prepared_number_outside)reject(13);',
         'Consume prepared literal32 wrapped bound after unchanged number/empty-plane priority.')
    edit('                    if(word_value<46||word_value>selected_limit||\n                        {32\'d0,cursor}+4+{32\'d0,word_value}>{32\'d0,residual_end})reject(13);',
         '                    if(prepared_length_invalid)reject(13);',
         'Consume one complete length-invalid bit on the original edge; no combinational fallback.')
    candidate=SRC/'cs88_admission_v91i2a.sv';candidate.write_text(source)
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original.read_text(),re.S):assert block in source
    write(SRC/'edit-recipe.json',dict(schema='v122-bounds-edit-recipe-v1',original=str(original.relative_to(ROOT)),original_sha256=sha(original),candidate=str(candidate.relative_to(ROOT)),candidate_sha256=sha(candidate),edits=edits,added_source_payload_bits=226,added_natural_public_cycles=0,old_assertions_removed=0,old_private_value_contract_changes=0))
    raw=candidate.read_bytes();cuts=[raw.index(b'module cu66_scale_tdp_v107 ('),raw.index(b'module cu66_mode_store_v107 (')];offsets=[0]+cuts+[len(raw)]
    write(SRC/'packaging.json',dict(schema='v122-bounds-lossless-packaging-v1',production_sha256=sha(candidate),split_byte_offsets=cuts,fragments=[dict(filename=n,bytes=offsets[i+1]-offsets[i],sha256=hashlib.sha256(raw[offsets[i]:offsets[i+1]]).hexdigest())for i,n in enumerate(['cs88_admission_v91i2a.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv'])]))
    oldmeta=json.loads((OLD/'verification-recipe.json').read_text())
    adapters=[]
    for label,p in [('original',original),('candidate',candidate)]:
        text=p.read_text();used=[]
        for e in oldmeta['adapters'][1]['edits']:
            before=e['before'];after=e['after']
            if before.startswith('module cs88_admission'):after=after.replace('admission_candidate','admission_'+label)
            assert text.count(before)==1,before
            text=text.replace(before,after,1);used.append(dict(before=before,after=after))
        dest=VER/('admission_'+label+'.sv');dest.write_text(text)
        adapters.append(dict(original=str(p.relative_to(ROOT)),original_sha256=sha(p),candidate=str(dest.relative_to(ROOT)),candidate_sha256=sha(dest),edits=used))
    copies=[]
    for p in OLD.joinpath('verification').iterdir():
        if p.name.startswith('admission_') and p.suffix=='.sv':continue
        if p.name in ['tb_owner_base.cpp','tb_match.cpp']:continue
        dest=VER/p.name;dest.write_bytes(p.read_bytes())
        copies.append(dict(original=str(p.relative_to(ROOT)),candidate=str(dest.relative_to(ROOT)),sha256=sha(p)))
    oldowner=OLD/'verification/tb_owner_base.cpp';text=oldowner.read_text();fixture=[]
    def fx(before,after):
        nonlocal text
        assert text.count(before)==1,before
        text=text.replace(before,after,1);fixture.append(dict(before=before,after=after))
    fx('#undef main\n','#undef main\n#include "bounds_priming.hpp"\n')
    fx('            unsigned error=0,next=28U;', '            if(state==19U||state==21U)prime_bounds(d,r);\n            unsigned error=0,next=28U;')
    fx('        QBOTH(state,19U);QBOTH(word_value,1U);tick();','        QBOTH(state,19U);QBOTH(word_value,1U);prime_bounds(d,r);tick();')
    fx('        begin(plane,0U);QBOTH(state,19U);QBOTH(word_value,0U);tick();','        begin(plane,0U);QBOTH(state,19U);QBOTH(word_value,0U);prime_bounds(d,r);tick();')
    dest=VER/'tb_owner_base.cpp';dest.write_text(text)
    matchold=OLD/'verification/tb_match.cpp';matchnew=VER/'tb_match.cpp'
    mbefore='int main(int argc,char**argv) {';mafter='int inherited_match_main(int argc,char**argv) {'
    assert matchold.read_text().count(mbefore)==1
    matchnew.write_text(matchold.read_text().replace(mbefore,mafter,1))
    write(SRC/'verification-recipe.json',dict(schema='v122-bounds-verification-recipe-v1',adapters=adapters,unchanged=copies,owner=dict(original=str(oldowner.relative_to(ROOT)),original_sha256=sha(oldowner),candidate=str(dest.relative_to(ROOT)),candidate_sha256=sha(dest),edits=fixture),match=dict(original=str(matchold.relative_to(ROOT)),original_sha256=sha(matchold),candidate=str(matchnew.relative_to(ROOT)),candidate_sha256=sha(matchnew),edits=[dict(before=mbefore,after=mafter)]),old_require_checks_removed=0,fixture_priming_edges_are_natural_packet_cycles=False))
    print('PREPARED_V122_BOUNDS',sha(candidate))

if __name__=='__main__':main()
