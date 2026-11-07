#!/usr/bin/env python3
"""Derive optimized controller only; frozen baseline remains untouched."""
import hashlib
import json
from pathlib import Path

AREA = Path(__file__).resolve().parent
ROOT = AREA.parents[2]
BASELINE = ROOT/'fpga/experiments/cu66-v91l-sdram/controller/moonshine_sdram.sv'
TARGET = AREA/'controller/moonshine_sdram.sv'
PATCHES = [
    ("assign request_ready=state==IDLE && 32'(refresh_count)<REFRESH_CYCLES;", """// Accept one next same-open-row write while issuing the current word.
 // All command/data pins use the OLD address/wdata at this clock edge.
 // No queue crosses rows, banks, a read, or the refresh budget.
 wire write_follow=state==RW_CMD && is_write && request_write &&
  request_address[23:9]==address[23:9];
 assign request_ready=(state==IDLE || write_follow) && !reset && 32'(refresh_count)<REFRESH_CYCLES;"""),
    ('if(is_write)begin sdram_we_n<=0;wait_cycles(3,IDLE);end', """if(is_write)begin
      sdram_we_n<=0;
      if(request_valid&&request_ready)begin
       address<=request_address;wdata<=request_data;is_write<=1;state<=RW_CMD;
      end else wait_cycles(3,IDLE);
     end"""),
]


def main():
    source = BASELINE.read_bytes()
    assert hashlib.sha256(source).hexdigest() == '9ecadf0e42bd0c35267e09d4c3b6df632d663d2096f93a80805b78528d2c6d4f'
    text = source.decode()
    for old, new in PATCHES:
        assert text.count(old) == 1
        text = text.replace(old, new)
    if TARGET.exists():
        assert TARGET.read_text() == text, 'optimized controller differs from documented transform'
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        TARGET.write_text(text)
    report = dict(schema='cu66-v91l-writepipe-controller-derivation-v1',
                  baseline=str(BASELINE.relative_to(ROOT)), baseline_sha256=hashlib.sha256(source).hexdigest(),
                  optimized=str(TARGET.relative_to(ROOT)), optimized_sha256=hashlib.sha256(text.encode()).hexdigest(),
                  replacements=[dict(old=old,new=new) for old,new in PATCHES],
                  unchanged='State values, initialization/MRS0x233, physical DQ/command output alignment, read sampling/BL8, PRE/ACT/refresh and final write wait_cycles(3,IDLE).',
                  support='Four aligned x16 words in one open bank/row from bounded row bridge; no read overlap, across-row queue, write-burst MRS, shared-memory or hardware signoff.')
    (AREA/'controller-derivation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(report['optimized_sha256'])


if __name__ == '__main__':
    main()
