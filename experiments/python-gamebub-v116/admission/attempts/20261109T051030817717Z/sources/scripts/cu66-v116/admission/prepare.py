#!/usr/bin/env python3
"""Prepare reversible V116 admission RTL and complete frozen-body adapters."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'fpga/experiments/cu66-v116-admission'
AREA = ROOT / 'experiments/python-gamebub-v116/admission'
OLD = ROOT / 'fpga/experiments/cu66-v112-control/cs88_admission_v91i2a.sv'
BASE = '49f23fe56894012d1f647192bb030025eb79331fe24b173c11a2252bee4ff8b7'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(p, obj):
    p.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


PREPARATION = '''    // V116_SELECTED_BEGIN: two existing edges separate plane selection from
    // the original uint32 wrapped length expression. No fetch is advanced.
    logic selected_valid, selected_limit_valid;
    logic [1:0] selected_plane;
    logic [31:0] selected_owner, selected_blocks, selected_limit;
    logic selected_zero;
    always_ff @(posedge clk)begin
        if(reset||start||abort_packet)begin
            selected_valid<=0;selected_limit_valid<=0;
        end else if(state==PLANE_BEGIN)begin
            selected_plane<=plane;selected_owner<=receipt_epoch;
            selected_blocks<=plane_blocks[plane];
            selected_zero<=plane_blocks[plane]==0;
            selected_valid<=1;selected_limit_valid<=0;
        end else if(state==PLANE_NEXT)begin
            selected_valid<=0;selected_limit_valid<=0;
        end else if(state==FETCH_REQ&&selected_valid&&!selected_limit_valid)begin
            selected_limit<=46+128*selected_blocks;
            selected_limit_valid<=1;
        end
    end
`ifndef SYNTHESIS
    // Check the complete owned tuple throughout all real fetch/word edges.
    // plane_blocks has no writer during this interval; equality to the held
    // selected count checks that stability rather than assuming it.
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&selected_valid&&
        (state==FETCH_REQ||state==FETCH_WAIT||state==WORD_BYTE||
         state==CHUNK_NUMBER||state==CHUNK_BLOCKS||state==CHUNK_LENGTH||
         state==CHUNK_MAGIC||state==PLANE_NEXT))begin
        assert(selected_plane==plane&&selected_owner==receipt_epoch)
            else $fatal(1,"V116 selected tuple owner/plane stability");
        assert(selected_blocks==plane_blocks[plane]&&selected_zero==(plane_blocks[plane]==0))
            else $fatal(1,"V116 selected count/zero stability");
    end
    // Literal old arithmetic and predicates, including expression width, are
    // retained at every actual consume. The residual-end bound stays separate.
    always_ff @(posedge clk)if(!reset&&!start&&!abort_packet&&
        (state==CHUNK_NUMBER||state==CHUNK_BLOCKS||state==CHUNK_LENGTH))begin
        assert(selected_valid&&selected_limit_valid&&selected_plane==plane&&selected_owner==receipt_epoch)
            else $fatal(1,"V116 selected consume without current preparation");
        assert(selected_blocks==plane_blocks[plane]&&selected_zero==(plane_blocks[plane]==0))
            else $fatal(1,"V116 selected consume count/zero");
        assert(selected_limit==46+128*plane_blocks[plane])
            else $fatal(1,"V116 selected consume literal old limit");
        if(state==CHUNK_NUMBER)
            assert((word_value!=(selected_zero?32'd0:32'd1))==
                (word_value!=(plane_blocks[plane]==0?32'd0:32'd1)))
                else $fatal(1,"V116 literal CHUNK_NUMBER predicate");
        if(state==CHUNK_BLOCKS)
            assert((word_value!=selected_blocks||word_value==0)==
                (word_value!=plane_blocks[plane]||word_value==0))
                else $fatal(1,"V116 literal CHUNK_BLOCKS predicate");
        if(state==CHUNK_LENGTH)
            assert((word_value<46||word_value>selected_limit||
                {32'd0,cursor}+4+{32'd0,word_value}>{32'd0,residual_end})==
                (word_value<46||word_value>46+128*plane_blocks[plane]||
                {32'd0,cursor}+4+{32'd0,word_value}>{32'd0,residual_end}))
                else $fatal(1,"V116 literal CHUNK_LENGTH predicate");
    end
`endif
    // V116_SELECTED_END

'''


def main():
    SRC.mkdir(parents=True, exist_ok=True)
    AREA.mkdir(parents=True, exist_ok=True)
    assert sha(OLD) == BASE
    edits = [
        ('    task automatic reject', PREPARATION + '    task automatic reject'),
        ("if(word_value!=(plane_blocks[plane]==0?32'd0:32'd1))reject(12);", "if(word_value!=(selected_zero?32'd0:32'd1))reject(12);"),
        ('if(word_value!=plane_blocks[plane]||word_value==0)reject(13);', 'if(word_value!=selected_blocks||word_value==0)reject(13);'),
        ('if(word_value<46||word_value>46+128*plane_blocks[plane]||', 'if(word_value<46||word_value>selected_limit||'),
    ]
    s = OLD.read_text()
    for before, after in edits:
        assert s.count(before) == 1, before
        s = s.replace(before, after, 1)
    candidate = SRC / OLD.name
    candidate.write_text(s)
    write(SRC / 'edit-recipe.json', dict(schema='v116-admission-existing-edge-v1', original=str(OLD.relative_to(ROOT)), original_sha256=BASE,
          candidate=str(candidate.relative_to(ROOT)), candidate_sha256=sha(candidate), edits=[dict(before=a, after=b) for a, b in edits],
          added_public_cycles=0, all_original_assertions_retained=True, residual_end_expression_unchanged=True))
    offsets = [s.index('module cu66_scale_tdp_v107 ('), s.index('module cu66_mode_store_v107 (')]
    parts = [s[:offsets[0]], s[offsets[0]:offsets[1]], s[offsets[1]:]]
    write(SRC / 'packaging.json', dict(schema='v116-admission-lossless-packaging-v1', production_sha256=sha(candidate), split_byte_offsets=offsets,
          fragments=[dict(filename=n, bytes=len(t.encode()), sha256=hashlib.sha256(t.encode()).hexdigest()) for n, t in zip(
              ['cs88_admission_v91i2a.sv', 'cu66_scale_tdp_v107.sv', 'cu66_mode_store_v107.sv'], parts)]))
    frozen = ROOT / 'fpga/experiments/cu66-v112-control/verification'
    inherited = json.loads((frozen / 'adapters.json').read_text())
    annotations = inherited['adapters'][0]['edits']
    adapters = []

    def adapt(source, name, changes):
        text = source.read_text()
        for before, after in changes:
            assert text.count(before) == 1, (name, before, text.count(before))
            text = text.replace(before, after, 1)
        out = SRC / name
        out.write_text(text)
        adapters.append(dict(source=str(source.relative_to(ROOT)), source_sha256=sha(source), path=str(out.relative_to(ROOT)), sha256=sha(out), edits=changes))

    for variant, source in [('original', OLD), ('candidate', candidate)]:
        changes = [[a, b.replace('module admission_original (', 'module admission_' + variant + ' (')] for a, b in annotations]
        adapt(source, 'admission_' + variant + '.sv', changes)
    adapt(frozen / 'admission_probe.sv', 'admission_probe.sv', [])
    # Keep an exact frozen oracle copy. Only hierarchy translation and legal
    # dependent poststate binding alter the separately compiled legacy adapter.
    adapt(frozen / 'tb_admission.cpp', 'tb_admission.frozen.cpp', [])
    bind = '''  // V116: forced states bind the complete new private poststate. No old
  // assertion, corruption predicate, expected value, or branch is changed.
  NEW(selected_valid)=c.state>=19U&&c.state<=23U;
  NEW(selected_limit_valid)=NEW(selected_valid);
  NEW(selected_plane)=c.p;NEW(selected_owner)=d.receipt_epoch;
  NEW(selected_blocks)=d.plane_blocks[c.p];NEW(selected_zero)=d.plane_blocks[c.p]==0U;
  NEW(selected_limit)=uint32_t(46U+128U*d.plane_blocks[c.p]);
'''
    # Repeated identical hierarchy names are recorded as a literal count recipe.
    legacy = SRC / 'tb_admission_legacy.cpp'
    original_text = (frozen / 'tb_admission.cpp').read_text()
    assert original_text.count('original__DOT__modes') == 4
    translated = original_text.replace('original__DOT__modes', 'original__DOT__mode_store__DOT__words')
    anchor = '  d.eval();require(!d.mismatch,"preedge public output mismatch");'
    assert translated.count(anchor) == 1
    translated = translated.replace(anchor, bind + anchor, 1)
    legacy.write_text(translated)
    write(SRC / 'legacy-recipe.json', dict(source=str((frozen / 'tb_admission.cpp').relative_to(ROOT)), source_sha256=sha(frozen / 'tb_admission.cpp'),
          candidate=str(legacy.relative_to(ROOT)), candidate_sha256=sha(legacy), hierarchy_before='original__DOT__modes', hierarchy_after='original__DOT__mode_store__DOT__words', hierarchy_occurrences=4,
          before=anchor, after=bind + anchor, semantic_checker_edits=0, frozen_copy_sha256=sha(SRC / 'tb_admission.frozen.cpp')))
    write(SRC / 'adapters.json', dict(adapters=adapters, all_public_ports_including_invalid_and_counters=True,
          all_original_assertions_and_goldens_retained=True))
    write(AREA / 'preparation.json', dict(status='PREPARED_NOT_RTL_QUALIFIED', actual_RTL_run=False, source_overrides={str(OLD.relative_to(ROOT)):str(candidate.relative_to(ROOT))},
          candidate_sha256=sha(candidate), recipe_sha256=sha(SRC / 'edit-recipe.json'), packaging_sha256=sha(SRC / 'packaging.json')))
    print('V116_ADMISSION_PREPARED_NOT_RUN', sha(candidate))


if __name__ == '__main__':
    main()
