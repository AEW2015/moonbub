#!/usr/bin/env python3
"""Prepare a reversible four-body capacity-control candidate; never run RTL."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'fpga/experiments/cu66-v107-count-threshold'
OUT = ROOT / 'fpga/experiments/cu66-v108-capacity'
HASHES = {
    'br88_packet_ingress_sync_v91h.sv': '079381563a110d26886829c9ebb7b4655c232af6886a86d3f42b7cf4e94b2063',
    'br88_packet_ingress_v91h.sv': '2c4a0ab1ba74b8ede056c6ce9958e6401f35beabcaaeeb681a90abe8947db5e4',
    'br88_pipeline_v91h.sv': 'a5d8a86d4bccca42377423abf8a318fc3acb8bfe9de38fcda9e5dd8eb46a5cc4',
    'packed_scratch_v91g2.sv': 'f0bab2ba60d290405b9726f69fab3e6c2aabb7a474ef1255d3857293b977097f',
}


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def pipeline():
    return r'''
    // CAPACITY_BOUND_PIPELINE_BEGIN: E0 capture through E4 owned commit.
    // P12 is settled before WAIT41. Forward count3's current high byte.
    // Actual plan/start/used_bytes arithmetic remains unchanged downstream.
    logic [27:0] capacity_prefix12_s0, capacity_align3_s0, capacity_prefix_s1;
    logic [27:0] capacity_a_s2, capacity_upper_s3, capacity_lower_s3;
    logic capacity_wrap_s3;
    logic [31:0] capacity_upper, capacity_lower;
    logic capacity_wrap, capacity_live;
    logic [3:0] capacity_valid_pipe;
    logic capacity_capture, capacity_flush;
    assign capacity_capture=prefix_header_capture&&fetch_index==6'd41;
    assign capacity_flush=cancelled||context_failure||(context_active&&ctx_done);
    assign meta_capacity_upper=capacity_upper;
    assign meta_capacity_lower=capacity_lower;
    assign meta_capacity_wrap=capacity_wrap;
    always_ff @(posedge clk)begin
        if(capacity_flush)begin capacity_valid_pipe<=0;capacity_live<=0;end
        else begin
            capacity_valid_pipe<={capacity_valid_pipe[2:0],capacity_capture};
            if(capacity_valid_pipe[3])capacity_live<=1;
        end
    end
    always_ff @(posedge clk)begin
        // E0: capture owned operands separately, with no input carry chain added.
        capacity_prefix12_s0<=plan_prefix12[31:4];
        capacity_align3_s0<=28'(count_aligned({ram_data,fetch_bytes[40],fetch_bytes[39],fetch_bytes[38]})>>4);
        // E1: exact modulo2^28 units; both original low nibbles are zero.
        capacity_prefix_s1<=capacity_prefix12_s0+capacity_align3_s0;
        // E2: add the32-byte scratch header in units of16, modulo2^28.
        capacity_a_s2<=capacity_prefix_s1+28'd2;
        // E3: a normal or wrapped interval; the strict lower bound is essential.
        capacity_upper_s3<=28'd16384-capacity_a_s2;
        capacity_lower_s3<=~capacity_a_s2;
        capacity_wrap_s3<=capacity_a_s2>28'd16384;
        // E4: cache the whole tuple. A simultaneous flush makes it unowned.
        if(capacity_valid_pipe[3])begin
            capacity_upper<={1'b0,capacity_upper_s3,3'd0};
            capacity_lower<={1'b0,capacity_lower_s3,3'd0};
            capacity_wrap<=capacity_wrap_s3;
        end
    end
    // CAPACITY_BOUND_PIPELINE_END
'''


def helpers(prefix):
    return f'''    function automatic logic [31:0] {prefix}_upper(input logic [27:0] units);
        logic [27:0] a,u;
        begin a=units+28'd2;u=28'd16384-a;return {{1'b0,u,3'd0}};end
    endfunction
    function automatic logic [31:0] {prefix}_lower(input logic [27:0] units);
        logic [27:0] a,l;
        begin a=units+28'd2;l=~a;return {{1'b0,l,3'd0}};end
    endfunction
    function automatic logic {prefix}_wrap(input logic [27:0] units);
        logic [27:0] a;
        begin a=units+28'd2;return a>28'd16384;end
    endfunction
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    texts = {n: (BASE/n).read_text() for n in HASHES}
    edits = {n: [] for n in HASHES}
    for n, h in HASHES.items():
        assert digest(texts[n]) == h, ('frozen V107 source drift', n)

    def add(n, before, after):
        assert texts[n].count(before) == 1, (n, before)
        texts[n] = texts[n].replace(before, after, 1)
        edits[n].append(dict(before=before, after=after, expected_occurrences=1))

    sync = 'br88_packet_ingress_sync_v91h.sv'
    wrapper = 'br88_packet_ingress_v91h.sv'
    child = 'br88_pipeline_v91h.sv'
    scratch = 'packed_scratch_v91g2.sv'
    for n in (sync, wrapper):
        add(n, '    output logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3,',
            '    output logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3,\n'
            '    output logic [31:0] meta_capacity_upper, meta_capacity_lower,\n'
            '    output logic meta_capacity_wrap,')
    add(sync, '    function automatic logic [31:0] cached32(input integer at);',
        pipeline()+'\n    function automatic logic [31:0] cached32(input integer at);')
    invariant = helpers('capacity_expected')+'''    always_ff @(posedge clk)if(meta_valid)begin
        assert(capacity_live)else $fatal(1,"capacity bounds not live before metadata");
        assert(meta_prefix123[3:0]==0)else $fatal(1,"capacity prefix unit alignment");
        assert(meta_capacity_upper==capacity_expected_upper(meta_prefix123[31:4]))else $fatal(1,"capacity upper stale owner");
        assert(meta_capacity_lower==capacity_expected_lower(meta_prefix123[31:4]))else $fatal(1,"capacity lower stale owner");
        assert(meta_capacity_wrap==capacity_expected_wrap(meta_prefix123[31:4]))else $fatal(1,"capacity wrap stale owner");
    end
    assert property (@(posedge clk)disable iff(cancelled)
        meta_valid&&!meta_ready |=> cancelled || (meta_valid&&$stable({meta_capacity_upper,meta_capacity_lower,meta_capacity_wrap})))
        else $fatal(1,"held capacity tuple changed");
'''
    add(sync, '`ifndef SYNTHESIS\n    always_ff @(posedge clk)if(meta_valid)begin',
        '`ifndef SYNTHESIS\n'+invariant+'    always_ff @(posedge clk)if(meta_valid)begin')
    add(wrapper, '        // Exact legacy fallback has no timing claim and avoids n+d-1 overflow.',
        helpers('capacity_legacy')+'''        // Legacy has no header staging; preserve exact modular capacity bounds.
        assign meta_capacity_upper=capacity_legacy_upper(meta_prefix123[31:4]);
        assign meta_capacity_lower=capacity_legacy_lower(meta_prefix123[31:4]);
        assign meta_capacity_wrap=capacity_legacy_wrap(meta_prefix123[31:4]);
        // Exact legacy fallback has no timing claim and avoids n+d-1 overflow.''')
    add(wrapper, '            .meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),',
        '            .meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),\n'
        '            .meta_capacity_upper(meta_capacity_upper),.meta_capacity_lower(meta_capacity_lower),.meta_capacity_wrap(meta_capacity_wrap),')
    add(child, '    logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3;',
        '    logic [31:0] meta_threshold1, meta_threshold2, meta_threshold3;\n'
        '    logic [31:0] meta_capacity_upper, meta_capacity_lower;logic meta_capacity_wrap;')
    add(child, '        .meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),',
        '        .meta_threshold1(meta_threshold1),.meta_threshold2(meta_threshold2),.meta_threshold3(meta_threshold3),\n'
        '        .meta_capacity_upper(meta_capacity_upper),.meta_capacity_lower(meta_capacity_lower),.meta_capacity_wrap(meta_capacity_wrap),')
    add(child, '        .begin_threshold1(meta_threshold1),.begin_threshold2(meta_threshold2),.begin_threshold3(meta_threshold3),',
        '        .begin_threshold1(meta_threshold1),.begin_threshold2(meta_threshold2),.begin_threshold3(meta_threshold3),\n'
        '        .begin_capacity_upper(meta_capacity_upper),.begin_capacity_lower(meta_capacity_lower),.begin_capacity_wrap(meta_capacity_wrap),')
    add(scratch, '    input logic [31:0] begin_threshold1, begin_threshold2, begin_threshold3,',
        '    input logic [31:0] begin_threshold1, begin_threshold2, begin_threshold3,\n'
        '    input logic [31:0] begin_capacity_upper, begin_capacity_lower,\n'
        '    input logic begin_capacity_wrap,')
    add(scratch, '    logic cancel;', '''    logic cancel;
    logic capacity_bad;
    assign capacity_bad=begin_raw ? begin_blocks>17'd2047 :
        (32'(begin_blocks)>begin_capacity_upper ||
         (begin_capacity_wrap && 32'(begin_blocks)<=begin_capacity_lower));''')
    add(scratch, '                        plan_used>262144) begin error<=1; state<=FAILED; end',
        '                        capacity_bad) begin error<=1; state<=FAILED; end')
    invariants = helpers('capacity_expected')+'''    always_ff @(posedge clk)if(begin_valid&&begin_ready)begin
        assert(begin_prefix123[3:0]==0)else $fatal(1,"scratch capacity prefix alignment");
        assert(begin_capacity_upper==capacity_expected_upper(begin_prefix123[31:4]))else $fatal(1,"scratch capacity upper ownership mismatch");
        assert(begin_capacity_lower==capacity_expected_lower(begin_prefix123[31:4]))else $fatal(1,"scratch capacity lower ownership mismatch");
        assert(begin_capacity_wrap==capacity_expected_wrap(begin_prefix123[31:4]))else $fatal(1,"scratch capacity wrap ownership mismatch");
        assert(capacity_bad==(plan_used>32'd262144))else $fatal(1,"scratch capacity predicate mismatch");
    end
'''
    add(scratch, '`ifndef SYNTHESIS\n    always_ff @(posedge clk)if(begin_valid&&begin_ready)begin',
        '`ifndef SYNTHESIS\n'+invariants+'    always_ff @(posedge clk)if(begin_valid&&begin_ready)begin')
    recipe = dict(schema='v108-capacity-exact-four-source-v1', status='PREPARED_NOT_RTL_QUALIFIED',
        public_added_cycles=0, registered_positions=5, post_capture_edges=4,
        latest_capture='F_HEADER WAIT41', latest_commit='F_HEADER WAIT43',
        earliest_header='E9 after WAIT41', production={})
    for n, text in texts.items():
        (OUT/n).write_text(text)
        recipe['production'][n] = dict(original=str((BASE/n).relative_to(ROOT)),
            original_sha256=HASHES[n], candidate_sha256=digest(text), edits=edits[n])
        reconstructed = (BASE/n).read_text()
        for e in edits[n]:
            assert reconstructed.count(e['before']) == 1
            reconstructed = reconstructed.replace(e['before'], e['after'], 1)
        assert reconstructed == text
        for e in reversed(edits[n]):
            assert reconstructed.count(e['after']) == 1
            reconstructed = reconstructed.replace(e['after'], e['before'], 1)
        assert reconstructed == (BASE/n).read_text()
    (OUT/'edit-recipe.json').write_text(json.dumps(recipe, indent=2, sort_keys=True)+'\n')
    print(json.dumps({n: e['candidate_sha256'] for n, e in recipe['production'].items()}, indent=2))


if __name__ == '__main__':
    main()
