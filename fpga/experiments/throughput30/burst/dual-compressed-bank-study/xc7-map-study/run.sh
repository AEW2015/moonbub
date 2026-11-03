#!/usr/bin/env bash
set -euo pipefail
here=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
storage="$here/../bank-storage-rtl"
root="$here/../../../../../.."
: "${BUILD_DIR:?Set BUILD_DIR to an empty new scratch directory}"
if [[ -d "$BUILD_DIR" && -n "$(ls -A "$BUILD_DIR")" ]]; then echo 'BUILD_DIR must be empty' >&2; exit 2; fi
mkdir -p "$BUILD_DIR"; build=$(cd -- "$BUILD_DIR" && pwd)
cd "$here"
sha256sum -c sources.sha256 > "$build/source-check.log"
python3 - "$root/fpga/rtl/moonshine_core.sv" "$here/single_bank_extract.sv" <<'PY'
from pathlib import Path
import sys
a,b=(Path(p).read_text() for p in sys.argv[1:])
declaration=' (* ram_style="block" *) reg [31:0] compressed[0:WORDS-1];'
start=' always @(posedge clk) begin\n  if(bus_write && bus_address=='
end='\n end'
assert declaration in a and declaration in b
block_a=start+a.split(start,1)[1].split(end,1)[0]+end
block_b=start+b.split(start,1)[1].split(end,1)[0]+end
assert block_a==block_b, 'baseline storage block differs from the source'
print('BASELINE_EXTRACT_MATCH')
PY
python3 make_candidate.py "$storage/two_bank_storage.sv" "$build/candidate.sv"
python3 make_lockstep.py "$storage/tb_two_bank_storage.sv" "$build/lockstep.sv" "$build/candidate.sv" "$build/candidate-renamed.sv"
python3 - "$build/candidate-renamed.sv" "$build/candidate-mutant.sv" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text(); old='bank1_data<=compressed1[read_addr]'
assert s.count(old)==1
Path(sys.argv[2]).write_text(s.replace(old,'bank1_data<=~compressed1[read_addr]'))
PY
verilator --version > "$build/tool-versions.txt"
yosys -V >> "$build/tool-versions.txt"
ulimit -c 0
for case_name in candidate mutant; do
 src="$build/candidate-renamed.sv"; [[ "$case_name" != mutant ]] || src="$build/candidate-mutant.sv"
 verilator --binary --timing --assert -Wno-fatal --top-module tb_two_bank_storage --Mdir "$build/$case_name-build" "$build/lockstep.sv" "$storage/two_bank_storage.sv" "$src" "$storage/two_bank_control_storage.sv" > "$build/$case_name-build.log" 2>&1
 code=0; timeout 90s "$build/$case_name-build/Vtb_two_bank_storage" > "$build/$case_name-sim.log" 2>&1 || code=$?
 if [[ "$case_name" == candidate ]]; then
  [[ $code == 0 ]]; grep -q '^LOCKSTEP_CHECKED_CYCLES=204890$' "$build/$case_name-sim.log"
  grep -q '^TEST_PASS_BANK_STORAGE reads=51715 overlap=1024 cap=49152 final_front=60$' "$build/$case_name-sim.log"
 else
  [[ $code != 0 && $code != 124 ]]; grep -q 'lockstep output mismatch' "$build/$case_name-sim.log"
  ! grep -q '^TEST_PASS_BANK_STORAGE' "$build/$case_name-sim.log"
 fi
done
cd "$storage"
for case_name in original candidate baseline; do
 case "$case_name" in
  original) files="two_bank_control_storage.sv two_bank_storage.sv"; top=two_bank_storage ;;
  candidate) files="two_bank_control_storage.sv $build/candidate.sv"; top=two_bank_storage ;;
  baseline) files="$here/single_bank_extract.sv"; top=single_bank_extract ;;
 esac
 # The old original fails to map forced block RAM with the recorded 0.33 tool;
 # other releases may infer it. Preserve its full log and report either outcome.
 code=0; timeout 600s yosys -T -l "$build/$case_name-yosys.log" -p "read_verilog -sv $files; synth_xilinx -family xc7 -top $top -noiopad -noclkbuf; stat -tech xilinx; write_json $build/$case_name-mapped.json" > "$build/$case_name-yosys-stdout.log" 2>&1 || code=$?
 [[ $code != 124 ]] || { echo "$case_name mapping timed out" >&2; exit 1; }
 if [[ "$case_name" == original ]]; then
  if [[ $code != 0 ]]; then grep -q 'no valid mapping found for memory' "$build/$case_name-yosys.log"; fi
 else
  [[ $code == 0 ]]; grep -q 'Found and reported 0 problems' "$build/$case_name-yosys.log"
 fi
done
python3 - "$build" <<'PY'
from pathlib import Path
from collections import Counter
import json,sys
p=Path(sys.argv[1]);out={}
for name in ('baseline','candidate','original'):
 file=p/f'{name}-mapped.json'
 if not file.exists():out[name]={'mapped':False};continue
 j=json.loads(file.read_text());counts=Counter()
 for m in j['modules'].values():
  counts.update(c['type'] for c in m.get('cells',{}).values())
 out[name]={'mapped':True,'RAMB36E1':counts['RAMB36E1'],'RAMB18E1':counts['RAMB18E1']}
assert out['baseline']['RAMB36E1']>0 and out['candidate']['RAMB36E1']>0
(p/'mapping-summary.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
print(json.dumps(out,sort_keys=True))
PY
echo 'XC7_STORAGE_STUDY_PASS (mapped prototypes, not routed target design)'
