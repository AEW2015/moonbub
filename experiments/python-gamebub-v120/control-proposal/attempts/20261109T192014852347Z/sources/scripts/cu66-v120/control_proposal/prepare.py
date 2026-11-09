#!/usr/bin/env python3
"""Prepare an unselected, phase-local ingress payload candidate; never runs tools."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OLD = ROOT / 'fpga/experiments/cu66-v117-ingress-bytecount'
NEW = ROOT / 'fpga/experiments/cu66-v120-control-proposal'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    NEW.mkdir(parents=True, exist_ok=True)
    original = OLD / 'br88_packet_ingress_sync_v91h.sv'
    text = original.read_text()
    edits = []

    def edit(before, after, why):
        nonlocal text
        assert text.count(before) == 1, why
        text = text.replace(before, after, 1)
        edits.append(dict(before=before, after=after, reason=why))

    edit('    logic cancelled, context_failure;\n', '''    logic cancelled, context_failure;

    // V120 proposal: these two fields are private and unreset. Their value is
    // owned only by FETCH_REQ. Preparing a phase value on a canceled/failing
    // edge grants no transaction: the original FSM and public masks below
    // remain the sole sources of request/response eligibility.
    logic [31:0] phase_request_addr;
    always_comb begin
        case(state)
            FETCH_WAIT: phase_request_addr=next_address_at_request;
            DESCRIPTOR: phase_request_addr=cursor;
            CONTEXT_RUN: phase_request_addr=active_offset+(replay_bits>>3);
            RAW: phase_request_addr=32'd42+32'd2*raw_position;
            default: phase_request_addr=32'd0;
        endcase
    end
    always_ff @(posedge clk)begin
        if(state==FETCH_WAIT || state==RECEIVE || state==DESCRIPTOR ||
           state==CONTEXT_RUN || state==RAW)begin
            prepared_request_addr<=phase_request_addr;
            prepared_request_in_bounds<=phase_request_addr<size_bytes &&
                phase_request_addr<32'(MAX_PACKET_BYTES);
        end
    end
`ifndef SYNTHESIS
    typedef struct packed {
        logic [31:0] epoch,size,base,address,descriptor_length,descriptor_tail;
        logic [2:0] kind;
        logic [5:0] index,count;
        logic [3:0] continuation;
        logic [1:0] band;
        logic in_bounds;
    } request_owner_t;
    request_owner_t request_owner;
    logic request_owner_valid;
    logic [31:0] owner_next_addr;
    function automatic logic [31:0] owned_address(
        input logic [2:0] kind,input logic [5:0] index,
        input logic [31:0] base,size,descriptor_length);
        logic [31:0] a;
        begin
            a=base+32'(index);
            if(kind==F_HEADER && index>=6'd42)a=size-32'd4+32'(index)-32'd42;
            if(kind==F_DESCRIPTOR && index==6'd6)a=base+descriptor_length-32'd1;
            return a;
        end
    endfunction
    assign owner_next_addr=owned_address(request_owner.kind,request_owner.index+6'd1,
        request_owner.base,request_owner.size,request_owner.descriptor_length);
`endif
''', 'Isolate two unreset private payload fields from global eligibility; add verification-only complete owner type.')

    edit('''            prepared_request_addr<=base;
            prepared_request_in_bounds<=base<size_bytes && base<32'(MAX_PACKET_BYTES);
''', '''`ifndef SYNTHESIS
            // Capture the actual task arguments, rather than reconstructing a
            // guessed call guard in a second controller.
            request_owner_valid<=1;
            request_owner<='{epoch:context_epoch,size:size_bytes,base:base,address:base,
                descriptor_length:active_length,descriptor_tail:base+active_length_minus1,
                kind:kind,index:6'd0,count:bytes_to_fetch,continuation:continuation,
                band:band,in_bounds:(base<size_bytes && base<32'(MAX_PACKET_BYTES))};
`endif
''', 'Remove only initial payload writes from begin_fetch; logical descriptor and tail assignments are untouched.')

    edit('''    always_ff @(posedge clk) begin
        // Speculative private preparation is independent of cancellation. On a
''', '''    always_ff @(posedge clk) begin
`ifndef SYNTHESIS
        // Each real initial call or successful nonfinal response below owns
        // the next FETCH_REQ. The current request consumes this certificate.
        request_owner_valid<=0;
`endif
        // Speculative private preparation is independent of cancellation. On a
''', 'Default-clear the verification-only first/request certificate in the existing single controller.')

    edit('''            prepared_request_addr<=next_address_at_request;
            prepared_request_in_bounds<=next_address_at_request<size_bytes && next_address_at_request<32'(MAX_PACKET_BYTES);
''', '''            // Address/bounds preparation moved to the phase-local writer.
''', 'Keep existing WAIT replay-word preparation; address and bounds retain the same WAIT edge in the separate writer.')

    edit('''                        end else begin fetch_index<=fetch_index+1'b1; state<=FETCH_REQ; end
''', '''                        end else begin
                            fetch_index<=fetch_index+1'b1; state<=FETCH_REQ;
`ifndef SYNTHESIS
                            // Retain the previous accepted request's complete
                            // owner. Only its six-bit index/address advance.
                            request_owner_valid<=1;
                            request_owner.index<=request_owner.index+6'd1;
                            request_owner.address<=owner_next_addr;
                            request_owner.in_bounds<=owner_next_addr<request_owner.size &&
                                owner_next_addr<32'(MAX_PACKET_BYTES);
`endif
                        end
''', 'Extend the complete owner only on the unchanged successful nonfinal physical-response branch.')

    edit('''`endif
endmodule
''', '''`endif
`ifndef SYNTHESIS
    always_ff @(posedge clk)if(!cancelled && !context_failure && !(context_active&&ctx_done) &&
        (state==FETCH_REQ || state==FETCH_WAIT))begin
        assert(context_epoch==request_owner.epoch && size_bytes==request_owner.size &&
            fetch_kind==request_owner.kind && fetch_index==request_owner.index &&
            fetch_count==request_owner.count && fetch_base==request_owner.base &&
            fetch_return==request_owner.continuation && band==request_owner.band)
            else $fatal(1,"V120 complete fetch owner mismatch");
        if(fetch_kind==F_DESCRIPTOR)
            assert(descriptor_last_addr==request_owner.descriptor_tail &&
                request_owner.descriptor_length==lengths[band])
                else $fatal(1,"V120 descriptor tail owner mismatch");
        if(state==FETCH_REQ)begin
            assert(request_owner_valid)else $fatal(1,"V120 request lacks actual call/response owner");
            assert(prepared_request_addr==request_owner.address &&
                prepared_request_in_bounds==request_owner.in_bounds)
                else $fatal(1,"V120 phase payload differs from complete owned request");
        end else
            assert(expected_fetch_addr==request_owner.address)
                else $fatal(1,"V120 physical response lost preceding request address");
    end
`endif
endmodule
''', 'Certify epoch/kind/count/base/index/continuation/band/address/bounds for every owned request and WAIT physical owner.')

    for block in re.findall(r'`ifndef SYNTHESIS(.*?)`endif', original.read_text(), re.S):
        assert block in text, 'Original RTL assertion block changed'
    candidate = NEW / original.name
    candidate.write_text(text)
    reverse = text
    for entry in reversed(edits):
        assert reverse.count(entry['after']) == 1
        reverse = reverse.replace(entry['after'], entry['before'], 1)
    assert reverse == original.read_text()
    manifest = dict(schema='v120-unselected-phase-payload-proposal-v1',
        status='PREPARED_NOT_RUN_NOT_SELECTED', source_composition_selected=False,
        production=[dict(original=str(original.relative_to(ROOT)), original_sha256=sha(original),
                         candidate=str(candidate.relative_to(ROOT)), candidate_sha256=sha(candidate), edits=edits)],
        original_assertion_blocks_byte_exact=True, declared_public_cycle_delta=0,
        declared_public_value_error_owner_debt_delta=0,
        private_contract_change=dict(fields=['prepared_request_addr','prepared_request_in_bounds'],
            description='Phase writes may change unowned values; every transition must be independently scored. Owned request values remain exact.',
            candidate_private_comparison_edits=1, all_private_equivalence_claim=False),
        unchanged_physical_ports=True, unchanged_memory_port_count=True,
        descriptor_last_addr_unchanged=True, parameter_domain_narrowed=False,
        validation='Not yet simulated, synthesized or routed. Root selection and strict new proof required.')
    (NEW / 'edit-recipes.json').write_text(json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    print(manifest['status'], sha(candidate))


if __name__ == '__main__':
    main()
