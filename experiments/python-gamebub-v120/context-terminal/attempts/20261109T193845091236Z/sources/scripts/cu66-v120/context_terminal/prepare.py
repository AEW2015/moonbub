#!/usr/bin/env python3
"""Prepare an unselected exact context terminal-predicate pipeline."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / 'fpga/experiments/cu66-v113-geometry/br88_context.sv'
DEST = ROOT / 'fpga/experiments/cu66-v120-context-terminal'
VER = DEST / 'verification'
VOLD = OLD.parent / 'verification'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    VER.mkdir(exist_ok=True)
    original = OLD.read_text()
    text = original
    edits = []

    def edit(before, after, why):
        nonlocal text
        assert text.count(before) == 1, why
        text = text.replace(before, after, 1)
        edits.append(dict(before=before,after=after,reason=why))

    edit('    logic [31:0] start_limit;\n', '''    logic [31:0] start_limit;
    // V120 proposal: one new private payload bit, unreset and phase-local.
    // WAIT is entered only on a real request handshake at this same REQ edge.
    // A canceled/stalled REQ may prepare an unowned bit; WAIT/HELD hold it.
    logic terminal_last_event;
    always_ff @(posedge clk)if(state==REQ_DC || state==REQ_RUN || state==REQ_LEVEL)
        terminal_last_event<=(emitted+32'd1==target);
`ifndef SYNTHESIS
    logic terminal_owner_valid;
    logic [31:0] terminal_owner_epoch,terminal_owner_emitted,terminal_owner_target;
    always_ff @(posedge clk)begin
        if(reset || abort_context || start)terminal_owner_valid<=0;
        else if(req_valid && req_ready)begin
            terminal_owner_valid<=1;
            terminal_owner_epoch<=context_epoch;
            terminal_owner_emitted<=emitted;
            terminal_owner_target<=target;
        end else if(state==IDLE || state==FINISHED || state==FAILED)terminal_owner_valid<=0;
    end
`endif
''', 'Prepare the exact wrapped predicate at the existing REQ edge; actual acceptance alone births its verification owner.')
    edit('else if (emitted+1==target && parser_consumed!=size_bits) fail_context(7);',
         'else if (terminal_last_event && parser_consumed!=size_bits) fail_context(7);',
         'Use the owned terminal predicate in the unchanged coefficient/error-priority branch.')
    edit('if (emitted+1==target) begin done<=1; state<=FINISHED; end',
         'if (terminal_last_event) begin done<=1; state<=FINISHED; end',
         'Use the same owned predicate only at the unchanged accepted-output edge.')
    edit('`endif\nendmodule\n', '''`endif
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!reset && !abort_context && !start &&
        (state==WAIT_DC || state==WAIT_RUN || state==WAIT_LEVEL || state==HELD))begin
        assert(terminal_owner_valid)else $fatal(1,"V120 terminal consumption lacks accepted request owner");
        assert(terminal_owner_epoch==context_epoch && terminal_owner_emitted==emitted &&
            terminal_owner_target==target)else $fatal(1,"V120 terminal owner changed before consumption");
        assert(terminal_last_event==(emitted+32'd1==target))
            else $fatal(1,"V120 wrapped full32 terminal predicate mismatch");
    end
`endif
endmodule
''', 'Certify full-width epoch/count ownership and exact wrapped identity throughout every WAIT/HELD consumption.')
    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif',original,re.S):
        assert block in text
    production = DEST / 'br88_context.sv'
    production.write_text(text)
    reverse = text
    for e in reversed(edits):
        assert reverse.count(e['after']) == 1
        reverse = reverse.replace(e['after'],e['before'],1)
    assert reverse == original
    adapters = []
    for source,name,module in [(OLD,'context_original.sv','context_original'),
                               (production,'context_candidate.sv','context_candidate')]:
        body = source.read_text()
        replacements = [
            ('module br88_context','module '+module),
            ('\n);',',\n    output logic [15:0] verify_sparse_block,\n    output logic [5:0] verify_sparse_index\n);'),
            ('\nendmodule','\n    assign verify_sparse_block=sparse_block;assign verify_sparse_index=sparse_index;\nendmodule')]
        for before,after in replacements:
            assert body.count(before)==1
            body=body.replace(before,after,1)
        target=VER/name;target.write_text(body)
        adapters.append(dict(source=str(source.relative_to(ROOT)),source_sha256=sha(source),
            path=str(target.relative_to(ROOT)),sha256=sha(target),edits=replacements))
    probe = (VOLD/'context_probe.sv').read_text()
    probe_edits = [
        ('    output logic [21:0] verify_original_geometry,verify_candidate_geometry\n',
         '    output logic [21:0] verify_original_geometry,verify_candidate_geometry,\n    output logic verify_terminal_req_fire,verify_terminal_last,verify_terminal_special,verify_original_terminal\n'),
        ('\nendmodule\n','''
    assign verify_terminal_req_fire=candidate.req_valid && candidate.req_ready;
    assign verify_terminal_last=candidate.terminal_last_event;
    assign verify_terminal_special=specialized.terminal_last_event;
    assign verify_original_terminal=(original.emitted+1==original.target);
endmodule
''')]
    for before,after in probe_edits:
        assert probe.count(before)==1
        probe=probe.replace(before,after,1)
    (VER/'context_probe.sv').write_text(probe)
    adapters.append(dict(source=str((VOLD/'context_probe.sv').relative_to(ROOT)),source_sha256=sha(VOLD/'context_probe.sv'),
        path=str((VER/'context_probe.sv').relative_to(ROOT)),sha256=sha(VER/'context_probe.sv'),edits=probe_edits))
    for name in ['inherited_context.cpp','tb_count_domain.cpp']:
        body=(VOLD/name).read_text()
        if name=='tb_count_domain.cpp':
            before='int main(int argc,char**argv){try{';after='int inherited_domain_main(int argc,char**argv){try{'
            assert body.count(before)==1
            body=body.replace(before,after,1);name_out='count_domain_base.cpp'
            (VER/name_out).write_text(body)
            adapters.append(dict(source=str((VOLD/name).relative_to(ROOT)),source_sha256=sha(VOLD/name),
                path=str((VER/name_out).relative_to(ROOT)),sha256=sha(VER/name_out),edits=[(before,after)]))
        else:
            (VER/name).write_bytes((VOLD/name).read_bytes())
    manifest=dict(schema='v120-unselected-owned-terminal-predicate-v1',status='PREPARED_NOT_RUN_NOT_SELECTED',
        selected_for_native_composition=False,original=str(OLD.relative_to(ROOT)),original_sha256=sha(OLD),
        candidate=str(production.relative_to(ROOT)),candidate_sha256=sha(production),edits=edits,
        adapters=adapters,unchanged_verification={str((VOLD/'inherited_context.cpp').relative_to(ROOT)):sha(VOLD/'inherited_context.cpp')},
        added_source_payload_bits=1,added_public_cycles=0,added_tile_buffers=0,added_memory_ports=0,
        existing_private_value_contract_changes=0,original_assertion_blocks_byte_exact=True,
        predicate_domain='Unsigned32 modulo wrap: (emitted + 32\'d1) == target; all epoch bits retained.',
        hardware_capture='REQ_DC/REQ_RUN/REQ_LEVEL state only; no reset, global ready or kill CE.',
        ghost_owner_capture='Actual req_valid && req_ready; revocation on reset/start/abort or terminal phase.',
        proof_scope='Prepared/full-domain and current natural-context proof must run fresh; no timing or hardware claim.',
        new_verification_files={str((VER/'tb_terminal.cpp').relative_to(ROOT)):sha(VER/'tb_terminal.cpp')})
    (DEST/'edit-recipe.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    print(manifest['status'],sha(production))


if __name__=='__main__':
    main()
