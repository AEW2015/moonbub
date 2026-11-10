#!/usr/bin/env python3
"""Derive the single existing-edge V121 request cursor experiment."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / 'fpga/experiments/cu66-v121-request'
VER = SRC / 'verification'
OLD = ROOT / 'fpga/experiments/cu66-v91i2b/byte_refill_queue_v91i2b.sv'
LEGACY = OLD.with_name('tb_refill_queue.cpp')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')


def main():
    VER.mkdir(parents=True, exist_ok=True)
    assert sha(OLD) == 'af78e9d263fcdaa5ccc0d13f370aa994f46e2feb198c54c9775122c02d07a505'
    source = OLD.read_text()
    edits = []

    def edit(before, after, reason):
        nonlocal source
        assert source.count(before) == 1
        source = source.replace(before, after, 1)
        edits.append(dict(before=before, after=after, reason=reason))

    edit('    logic blocked, response_fault, issue;\n',
         '    // V121: next full32 address owned by the existing start/issue edges.\n'
         '    // Holds through stalls, responses, pops, completion and faults.\n'
         '    logic [31:0] prepared_req_addr;\n'
         '    logic blocked, response_fault, issue;\n',
         'Add one full32 cursor; do not add an ownership or pipeline edge.')
    edit('    assign req_addr=offset+issued;\n',
         '    assign req_addr=prepared_req_addr;\n',
         'Remove the offset-plus-issued adder from admission address and bounds inputs.')
    edit('            offset<=0;length<=0;owner_epoch<=0;issued<=0;consumed<=0;pending_addr<=0;pending_last<=0;\n',
         '            prepared_req_addr<=0;\n'
         '            offset<=0;length<=0;owner_epoch<=0;issued<=0;consumed<=0;pending_addr<=0;pending_last<=0;\n',
         'Preserve reset/cancel/clear_stats precedence and unqualified address.')
    edit('            offset<=start_offset;length<=start_length;owner_epoch<=start_epoch;\n',
         '            prepared_req_addr<=start_offset;\n'
         '            offset<=start_offset;length<=start_length;owner_epoch<=start_epoch;\n',
         'Capture exact start offset for empty, valid and replacement starts.')
    edit('                issued<=issued+1;pending_addr<=req_addr;pending_last<=issued+1==length;\n',
         '                prepared_req_addr<=prepared_req_addr+32\'d1;\n'
         '                issued<=issued+1;pending_addr<=req_addr;pending_last<=issued+1==length;\n',
         'Advance exactly once on accepted request using literal unsigned modular full32 addition.')
    old_assertions = re.search(r'`ifndef SYNTHESIS.*?`endif', source, re.S).group()
    edit(old_assertions,
         '`ifndef SYNTHESIS\n'
         '    always_ff @(posedge clk) if(!blocked)begin\n'
         '        assert(prepared_req_addr==offset+issued)\n'
         '            else $fatal(1,"V121 prepared full32 request owner mismatch");\n'
         '    end\n'
         '`endif\n\n' + old_assertions,
         'Add a full32 owner invariant while retaining the entire inherited assertion block byte-exact.')
    candidate = SRC / OLD.name
    candidate.write_text(source)
    write(SRC / 'edit-recipe.json', dict(
        schema='v121-prepared-request-existing-edge-v1', original=str(OLD.relative_to(ROOT)),
        original_sha256=sha(OLD), candidate=str(candidate.relative_to(ROOT)), candidate_sha256=sha(candidate),
        edits=edits, added_source_payload_bits=32, added_public_cycles=0,
        old_assertions_removed=0, old_private_value_contract_changes=0,
        external_interface_changes=0, accepted_wrap_contract='Original accepted request span-overflow assertion retained.'))
    # Adapters change only module names. Both complete sources retain assertions.
    adapters = []
    for label, path in [('original', OLD), ('candidate', candidate)]:
        before = 'module byte_refill_queue_v91i2b ('
        after = 'module request_' + label + ' ('
        text = path.read_text()
        assert text.count(before) == 1
        dest = VER / ('request_' + label + '.sv')
        dest.write_text(text.replace(before, after, 1))
        adapters.append(dict(original=str(path.relative_to(ROOT)), original_sha256=sha(path),
                             candidate=str(dest.relative_to(ROOT)), candidate_sha256=sha(dest),
                             edits=[dict(before=before, after=after)]))
    # Generate a comparison wrapper from the unchanged original ANSI port list.
    header = OLD.read_text().split(');', 1)[0]
    inputs, outputs = [], []
    for direction, width, names in re.findall(r'\b(input|output) logic\s*(\[[^\]]+\])?\s*([^\n]+)', header):
        for name in names.rstrip(',').split(','):
            (inputs if direction == 'input' else outputs).append((width or '', name.strip()))
    assert len(inputs) == 14 and len(outputs) == 21, (inputs, outputs)
    ports = ['    input logic ' + w + ' ' + n for w, n in inputs]
    ports += ['    output logic ' + w + ' ' + n for w, n in outputs]
    ports += ['    output logic mismatch']
    wrapper = 'module request_probe (\n' + ',\n'.join(ports) + '\n);\n'
    wrapper += ''.join('    logic ' + w + ' original_' + n + ';\n' for w, n in outputs)
    for label in ('original', 'candidate'):
        wiring = ['.' + n + '(' + n + ')' for _, n in inputs]
        wiring += ['.' + n + '(' + ('original_' if label == 'original' else '') + n + ')' for _, n in outputs]
        wrapper += '    request_' + label + ' ' + label + '(\n        ' + ',\n        '.join(wiring) + '\n    );\n'
    wrapper += '    assign mismatch=' + ' ||\n        '.join('(original_' + n + '!=' + n + ')' for _, n in outputs) + ';\nendmodule\n'
    (VER / 'request_probe.sv').write_text(wrapper)
    # Retain the complete old directed proof and every require expression. Only
    # add pair assertions, an exact next-address scoreboard and an extension.
    text = LEGACY.read_text()
    legacy_edits = []

    def legacy_edit(before, after):
        nonlocal text
        assert text.count(before) == 1
        text = text.replace(before, after, 1)
        legacy_edits.append(dict(before=before, after=after))

    legacy_edit('#include "Vbyte_refill_queue_v91i2b.h"', '#include "Vrequest_probe.h"')
    legacy_edit('    Vbyte_refill_queue_v91i2b d;', '    Vrequest_probe d;')
    legacy_edit('d.rsp_data=flight?flight->byte:0;d.eval();',
                'd.rsp_data=flight?flight->byte:0;d.eval();\n'
                '        need(!d.mismatch,"V121 preedge exact public output mismatch");\n'
                '        if(flight){++physical_responses;if(d.reset||d.cancel||d.start||d.clear_stats)++physical_responses_on_revoke;}')
    legacy_edit('d.clk=1;d.eval();++cycles;',
                'd.clk=1;d.eval();++cycles;\n'
                '        need(!d.mismatch,"V121 postedge exact public output mismatch");')
    legacy_edit('    uint64_t simultaneous=0,read_edges=0,pop_edges=0;',
                '    uint64_t simultaneous=0,read_edges=0,pop_edges=0;\n'
                '    uint64_t physical_responses=0,physical_responses_on_revoke=0;')
    legacy_edit('                need(d.req_epoch==epoch,"read owner epoch changed");',
                '                need(d.req_epoch==epoch,"read owner epoch changed");\n'
                '                need(d.req_addr==uint32_t(offset+uint32_t(read_edges)),"independent exact full32 issue sequence");')
    legacy_edit('int main(int argc,char **argv){', 'int inherited_main(int argc,char **argv){')
    (VER / 'tb_refill_legacy.frozen.cpp').write_bytes(LEGACY.read_bytes())
    (VER / 'tb_refill_legacy.cpp').write_text(text)
    write(SRC / 'verification-recipe.json', dict(schema='v121-request-exact-cycle-adapters-v1', adapters=adapters,
        legacy=dict(original=str(LEGACY.relative_to(ROOT)), original_sha256=sha(LEGACY),
                    candidate=str((VER / 'tb_refill_legacy.cpp').relative_to(ROOT)),
                    candidate_sha256=sha(VER / 'tb_refill_legacy.cpp'), edits=legacy_edits),
        old_require_checks_removed=0, added_public_cycles=0,
        comparison='Every original output, qualified and unqualified, before and after every tested edge.'))
    print('PREPARED_V121_REQUEST', sha(candidate))


if __name__ == '__main__':
    main()
