#!/usr/bin/env python3
"""Prepare a reversible, unselected V120 admission equality payload experiment."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT/'fpga/experiments/cu66-v119-owner'
SRC = ROOT/'fpga/experiments/cu66-v120-admission-match'
VER = SRC/'verification'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, value):
    p.write_text(json.dumps(value, indent=2, sort_keys=True)+'\n')

def main():
    VER.mkdir(parents=True, exist_ok=True)
    original = OLD/'cs88_admission_v91i2a.sv'
    assert sha(original)=='23d031d48e3934f1c33ccffcb2c2e707d884daa68ed799cd7ff3c639c6c1496b'
    source = original.read_text()
    edits = []
    def edit(before, after, reason):
        nonlocal source
        assert source.count(before)==1
        source=source.replace(before, after, 1)
        edits.append(dict(before=before, after=after, reason=reason))
    edit('    logic [34:0] header_residual_end, header_packet_total;\n', '''    logic [34:0] header_residual_end, header_packet_total;
    // V120: one unreset payload bit on an existing byte-load phase. The
    // complete total is stable after byte55, before final HEADER_BYTE127.
    // Extra canceled/early captures are unowned and never authorize work.
    logic prepared_header_total_matches;
    always_ff @(posedge clk)if(state==HEADER_BYTE)
        prepared_header_total_matches<=header_packet_total=={3'd0,size_bytes};
`ifndef SYNTHESIS
    logic header_match_owner_valid;
    logic [31:0] header_match_owner_epoch, header_match_owner_size;
    logic [34:0] header_match_owner_total;
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)header_match_owner_valid<=0;
        else if(state==HEADER_BYTE&&header_index==127)begin
            header_match_owner_valid<=1;
            header_match_owner_epoch<=receipt_epoch;
            header_match_owner_size<=size_bytes;
            header_match_owner_total<=header_packet_total;
        end else if(state==HEADER_CHECK)header_match_owner_valid<=0;
    end
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&state==HEADER_CHECK)begin
        assert(header_match_owner_valid&&header_index==127&&
            header_match_owner_epoch==receipt_epoch&&header_match_owner_size==size_bytes&&
            header_match_owner_total==header_packet_total)
            else $fatal(1,"V120 header equality complete owner mismatch");
        assert(prepared_header_total_matches==(header_packet_total=={3'd0,size_bytes}))
            else $fatal(1,"V120 full35 header equality payload mismatch");
    end
`endif
''', 'Capture one phase-local full35 equality bit; verification-only owner covers exact epoch, size and total at every consume.')
    edit('                        header_packet_total!={3\'d0,size_bytes})reject(5);',
         '                        !prepared_header_total_matches)reject(5);',
         'Replace only the HEADER_CHECK total comparison; all other branches and priorities remain exact.')
    candidate=SRC/'cs88_admission_v91i2a.sv';candidate.write_text(source)
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original.read_text(),re.S):
        assert block in source
    recipe=dict(schema='v120-header-total-equality-payload-recipe-v1', original=str(original.relative_to(ROOT)), original_sha256=sha(original), candidate=str(candidate.relative_to(ROOT)), candidate_sha256=sha(candidate), edits=edits, added_source_payload_bits=1, old_assertions_removed=0, old_private_value_contract_changes=0, added_natural_public_cycles=0)
    write(SRC/'edit-recipe.json',recipe)
    raw=candidate.read_bytes();cuts=[raw.index(b'module cu66_scale_tdp_v107 ('),raw.index(b'module cu66_mode_store_v107 (')]
    offsets=[0]+cuts+[len(raw)]
    names=['cs88_admission_v91i2a.sv','cu66_scale_tdp_v107.sv','cu66_mode_store_v107.sv']
    packaging=dict(schema='v120-admission-match-lossless-packaging-v1',production_sha256=sha(candidate),split_byte_offsets=cuts,fragments=[dict(filename=n,bytes=offsets[i+1]-offsets[i],sha256=hashlib.sha256(raw[offsets[i]:offsets[i+1]]).hexdigest())for i,n in enumerate(names)])
    write(SRC/'packaging.json',packaging)
    lineage=json.loads((OLD/'admission-verification/lineage.json').read_text())
    adapters=[]
    for label,p in [('original',original),('candidate',candidate)]:
        text=p.read_text();used=[]
        for before,after in lineage['adapter_edits']:
            if before.startswith('module cs88_admission'):after=after.replace('admission_candidate','admission_'+label)
            assert text.count(before)==1;text=text.replace(before,after,1);used.append(dict(before=before,after=after))
        if label=='candidate':
            before='    logic prepared_header_total_matches;'
            after='    logic prepared_header_total_matches /* verilator public_flat_rw */;'
            assert text.count(before)==1;text=text.replace(before,after,1);used.append(dict(before=before,after=after))
        dest=VER/('admission_'+label+'.sv');dest.write_text(text)
        adapters.append(dict(original=str(p.relative_to(ROOT)),original_sha256=sha(p),candidate=str(dest.relative_to(ROOT)),candidate_sha256=sha(dest),edits=used))
    copies=[]
    for n in ['admission_probe.sv','tb_admission.cpp']:
        src=OLD/'admission-verification'/n;dest=VER/n;dest.write_bytes(src.read_bytes())
        copies.append(dict(original=str(src.relative_to(ROOT)),candidate=str(dest.relative_to(ROOT)),sha256=sha(src)))
    # Keep the literal inherited fixture as a frozen input, and derive only
    # two coherent predecessor insertions plus the helper include. Every old
    # require expression and every original tick body remains byte-exact.
    legacy=OLD/'admission-verification/tb_admission_legacy.cpp';text=legacy.read_text();fixture_edits=[]
    def fixture(before,after):
        nonlocal text
        assert text.count(before)==1;text=text.replace(before,after,1);fixture_edits.append(dict(before=before,after=after))
    fixture('#define QBOTH(n,v) do {const auto z=(v);QOLD(n)=z;QNEW(n)=z;}while(0)\n', '#define QBOTH(n,v) do {const auto z=(v);QOLD(n)=z;QNEW(n)=z;}while(0)\n#include "header_match_priming.hpp"\n')
    fixture('  QBOTH(header_mode_start,m);QBOTH(header_residual_start,rs);QBOTH(header_hud_tail,ht);QBOTH(header_residual_end,re);QBOTH(header_packet_total,re+ht);\n };', '  QBOTH(header_mode_start,m);QBOTH(header_residual_start,rs);QBOTH(header_hud_tail,ht);QBOTH(header_residual_end,re);QBOTH(header_packet_total,re+ht);\n  prime_header_match(d,r);\n };')
    fixture('  BOTH(selected_limit,uint32_t(46U+128U*d.plane_blocks[c.p]));\n  d.eval();require(!d.mismatch,"preedge public output mismatch");', '  BOTH(selected_limit,uint32_t(46U+128U*d.plane_blocks[c.p]));\n  if(c.state==5U)prime_header_match(d,r);\n  d.eval();require(!d.mismatch,"preedge public output mismatch");')
    derived=VER/'tb_admission_legacy.cpp';derived.write_text(text)
    (VER/'tb_admission_legacy.frozen.cpp').write_bytes(legacy.read_bytes())
    old_owner=OLD/'admission-verification/tb_owner.cpp';text=old_owner.read_text()
    before='int main(int argc,char**argv)';after='int inherited_owner_main(int argc,char**argv)';assert text.count(before)==1;text=text.replace(before,after,1)
    dest=VER/'tb_owner_base.cpp';dest.write_text(text)
    write(SRC/'verification-recipe.json',dict(schema='v120-admission-match-verification-recipe-v1',adapters=adapters,unchanged=copies,legacy=dict(original=str(legacy.relative_to(ROOT)),original_sha256=sha(legacy),candidate=str(derived.relative_to(ROOT)),candidate_sha256=sha(derived),edits=fixture_edits),owner=dict(original=str(old_owner.relative_to(ROOT)),original_sha256=sha(old_owner),candidate=str(dest.relative_to(ROOT)),candidate_sha256=sha(dest),edits=[dict(before=before,after=after)]),old_require_checks_removed=0,fixture_clock_delta='One real HEADER_BYTE127 predecessor only for live direct HEADER_CHECK fixture preparations; counted separately, no state/error/cache restoration, no new-bit forcing.',prepared_fixture_edges_are_natural_packet_cycles=False))
    print('PREPARED_SOURCE',sha(candidate),'packaging',sha(SRC/'packaging.json'))

if __name__=='__main__':main()
