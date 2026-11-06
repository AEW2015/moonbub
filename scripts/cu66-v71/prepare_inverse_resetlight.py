"""Drop reset only from payload fully overwritten before valid; separate successors."""
from pathlib import Path
import hashlib, json

root = Path(__file__).resolve().parents[2]
out = root/'fpga/experiments/cu66-v71/inverse-reset'
out.mkdir(parents=True, exist_ok=False)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
bindings = []

def derive(parent, filename, changes, bits, proof):
    path = root/parent
    text = path.read_text()
    for old, new in changes:
        assert text.count(old) == 1, (parent, old)
        text = text.replace(old, new)
    target = out/filename
    target.write_text(text, newline='\n')
    bindings.append(dict(parent=parent, parent_sha256=sha(path),
                         candidate=target.relative_to(root).as_posix(), candidate_sha256=sha(target),
                         payload_reset_bits_removed=bits, initialization_before_valid=proof))

derive('fpga/experiments/cu66-v69/inverse/cu66_idct8x8.sv', 'cu71_idct_resetlight.sv', [
    ('module cu66_idct8x8 (', 'module cu71_idct_resetlight ('),
    ("            source_tile<='0;\n", ''),
    ("            out_tile<='0;\n", ''),
    ("            dc_middle<='0;\n", ''),
    ("""            for (lane=0; lane<8; lane=lane+1) begin
                products[lane]<='0;
                even_sum[lane]<='0;
                odd_sum[lane]<='0;
            end
""", ''),
], 3784, [
    'source_tile captured in accepted IDLE before any multiply',
    'all products overwritten in MUL before ACC',
    'even/odd sums initialized on each accepted tile and each group boundary',
    'dc_middle written in DC_FIRST_ACC before DC_SECOND_MUL',
    'all64 output positions written by fast-zero, DC broadcast or complete second pass before OUTPUT_TILE',
    'FSM/id/error/counters still reset; abort clears validity and cannot resume old work',
])

derive('fpga/experiments/cu66-v71/dequant/cu71_dequant_pipe.sv', 'cu71_dequant_resetlight.sv', [
    ('module cu71_dequant_pipe (', 'module cu71_dequant_resetlight ('),
    ('state<=IDLE; coefficients<=0; chroma<=0; scale_code<=0;', 'state<=IDLE;'),
    ('// The externally visible tile/id/error retain synchronous reset/abort.',
     '// ID/error/valid control retain reset; tile payload is overwritten before valid.'),
    ('''                if(rst||abort_i)out_dequantized[(group_number*8+lane_number)*20 +:20]<=0;
                else if(state==IDLE && in_valid && in_ready && fast_result)''',
     '''                if(!rst && !abort_i && state==IDLE && in_valid && in_ready && fast_result)'''),
    ('else if(state==RUN && product_valid && product_destination[group_number])',
     'else if(!rst && !abort_i && state==RUN && product_valid && product_destination[group_number])'),
], 2307, [
    'coefficients/chroma/scale captured by accepted input before RUN',
    'fast invalid/zero explicitly writes all1280 output bits before HOLD_TILE',
    'all8 complete product groups stored before HOLD_TILE; reset/abort suppress every store',
    'selection/product valid flags and FSM reset, so stale scratch cannot become a valid result',
])

derive('fpga/experiments/cu66-v69/inverse/cu66_reconstruct_tile.sv', 'cu71_reconstruct_resetlight.sv', [
    ('module cu66_reconstruct_tile (', 'module cu71_reconstruct_resetlight ('),
    ('if(rst||abort_i)begin out_valid<=0;out_id<=0;out_pixels<=0;out_error<=0;end',
     'if(rst||abort_i)begin out_valid<=0;out_id<=0;out_error<=0;end'),
], 512, [
    'all64 pixel positions assigned in every accepted key/hidden/valid-reference transaction',
    'out_valid/id/error reset and required-reference identity checks retained',
])
(out/'derivation.json').write_text(json.dumps(dict(
    status='DERIVED_VALID_FENCED_PAYLOAD_RESET_REDUCTION_REGRESSION_PENDING', bindings=bindings,
    total_payload_reset_bits_removed=sum(row['payload_reset_bits_removed'] for row in bindings),
    contract='Payload values while out_valid=false are unspecified; IDs/error/control reset retained',
    pipeline_latency_changed=False, hardware=False, selected_in_board=False,
), indent=2)+'\n')
print(out)
