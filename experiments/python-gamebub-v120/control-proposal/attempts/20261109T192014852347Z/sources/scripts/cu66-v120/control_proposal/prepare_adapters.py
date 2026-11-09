#!/usr/bin/env python3
"""Derive verification adapters for an explicit two-field private contract change."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'fpga/experiments/cu66-v120-range/verification'
DEST = ROOT / 'fpga/experiments/cu66-v120-control-proposal/verification'
META = DEST.parent / 'edit-recipes.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    original = {p.name: p for p in SOURCE.iterdir() if p.is_file()}
    DEST.mkdir(parents=True, exist_ok=True)
    m = json.loads(META.read_text())
    m['adapters'] = []
    m['unchanged_verification'] = {}

    def derive(name, output, replacements):
        source = original[name]
        text = source.read_text()
        edits = []
        for before, after, reason in replacements:
            assert text.count(before) == 1, (name, reason)
            text = text.replace(before, after, 1)
            edits.append(dict(before=before, after=after, reason=reason))
        target = DEST / output
        target.write_text(text)
        reverse = text
        for edit in reversed(edits):
            assert reverse.count(edit['after']) == 1
            reverse = reverse.replace(edit['after'], edit['before'], 1)
        assert reverse == source.read_text()
        m['adapters'].append(dict(original=str(source.relative_to(ROOT)), original_sha256=sha(source),
            candidate=str(target.relative_to(ROOT)), candidate_sha256=sha(target), edits=edits))

    changed = {'ingress_base.cpp','extents_base.cpp','tb_range.cpp'}
    for name, path in original.items():
        if name in changed:
            continue
        (DEST/name).write_bytes(path.read_bytes())
        m['unchanged_verification'][str(path.relative_to(ROOT))] = sha(path)

    derive('ingress_base.cpp','ingress_base.cpp',[
        ('static void need(bool ok,const std::string& why){if(!ok)throw std::runtime_error(why);}\n',
         'static void need(bool ok,const std::string& why){if(!ok)throw std::runtime_error(why);}\n#include "writer_scoreboard.hpp"\n',
         'Add the independent full-transition payload writer oracle after the existing fatal need helper.'),
        ('  d.clk=1;d.eval();d.clk=0;d.eval();\n  if(kill||rsp)pending=false;',
         '  ControlPrivateStep private_step(d);d.clk=1;d.eval();d.clk=0;d.eval();private_step.finish(d);\n  if(kill||rsp)pending=false;',
         'Check original and candidate private writes/holds on every natural packet clock without touching physical-owner or public checks.'),
        ('   if(target==10)target_hit=d.probe_length_live&&d.stage_purpose==0&&d.probe_fetch_index<42;\n',
         '   if(target==10)target_hit=d.probe_length_live&&d.stage_purpose==0&&d.probe_fetch_index<42;\n   if(target>=11&&target<=14)target_hit=writer_initial_kind(d)==target-11;\n',
         'Add four reachable actual initial-call cancellation targets; retain all old target predicates.')])
    derive('extents_base.cpp','extents_base.cpp',[
        (' need(IOLD(prepared_request_addr)==INEW(prepared_request_addr)&&IOLD(prepared_request_in_bounds)==INEW(prepared_request_in_bounds)&&IOLD(descriptor_last_addr)==INEW(descriptor_last_addr),"postedge request/last-address exact pair");',
         ' need(IOLD(descriptor_last_addr)==INEW(descriptor_last_addr),"unchanged descriptor-tail exact pair; two unowned fields independently transition-scored");',
         'The ONE admitted comparison edit: two unowned fields use complete old/new writer oracles; descriptor tail remains exact. The unchanged equality is retained in frozen A control evidence.'),
        (' d.clk=0;d.eval();compare(d);d.clk=1;d.eval();d.clk=0;d.eval();compare(d);need(++c.edges<1000000,"extent finite edge watchdog");',
         ' d.clk=0;d.eval();compare(d);ControlPrivateStep private_step(d);d.clk=1;d.eval();d.clk=0;d.eval();private_step.finish(d);compare(d);need(++c.edges<1000000,"extent finite edge watchdog");',
         'Score every prepared extent edge, including rejected descriptors, reset/start/abort and all hold cases.')])
    derive('tb_range.cpp','range_base.cpp',[
        (' d.eval();d.clk=1;d.eval();d.clk=0;d.eval();d.reset=0;++edges;',
         ' d.eval();{ControlPrivateStep private_step(d);d.clk=1;d.eval();d.clk=0;d.eval();private_step.finish(d);}d.reset=0;++edges;',
         'Score the first actual reset edge in the exhaustive prepared-domain instance.'),
        ('  d.clk=1;d.eval();d.clk=0;d.eval();++edges;',
         '  {ControlPrivateStep private_step(d);d.clk=1;d.eval();d.clk=0;d.eval();private_step.finish(d);}++edges;',
         'Score all 65536 actual prepared RAW edges; no predicate or public oracle changes.'),
        ('int main(int argc,char**argv){try{','int inherited_range_main(int argc,char**argv){try{',
         'Rename only the old entry so the additive control driver executes all inherited checks first.')])
    m['required_old_control_proof'] = 'experiments/python-gamebub-v120/range/results.json'
    m['old_control_proof_scope'] = ('Reuse only frozen A control evidence: its original unconditional private equality is unchanged. '
        'All candidate models must compile fresh from the selected candidate; no candidate binary reuse.')
    m['new_verification_files'] = {str(p.relative_to(ROOT)):sha(p) for p in
        [DEST/'writer_scoreboard.hpp',DEST/'tb_control.cpp']}
    m['candidate_private_comparison_edits'] = 1
    m['changed_private_fields'] = ['prepared_request_addr','prepared_request_in_bounds']
    m['candidate_all_private_equivalence_claim'] = False
    m['candidate_public_cycle_value_error_owner_debt_delta'] = 0
    m['new_natural_coverage'] = dict(initial_call_cancellations=24,first_request_response_cancellations=24,
                                    context_error_cases=32,nonreset_retries=80)
    m['new_prepared_coverage'] = dict(canceled_unowned_full32_cases=11424,physical_requests=0,natural_frame_claim=False)
    m['next_address_shadow'] = 'Independent modulo32/six-bit-next-index math captured only on actual stage_read_req; checked and used on owned WAIT. Unowned cache before first actual request remains an explicit input.'
    META.write_text(json.dumps(m,indent=2,sort_keys=True)+'\n')
    print('V120_CONTROL_ADAPTERS_PREPARED_NOT_RUN',sha(META))


if __name__ == '__main__':
    main()
