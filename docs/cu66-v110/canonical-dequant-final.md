# V110 combined-dequant canonical audit

The combined-dequant full canonical candidate passed 44 case profiles and 42
directed checks across V109 FETCH seeds 107601 and 107602 (22 profiles and 21
checks per seed). The candidate uses the frozen 18-source order: 17
SystemVerilog files and one include header, with exactly five declared
replacements for busy, fault and dequant. All recorded current-source hashes
and retained attempt snapshots match.

Both candidate seeds match V109 FETCH stdout, events, cycles and raw canonical
artifacts byte-for-byte. The V109 control was reused, not rebuilt or recounted.
This full canonical result qualifies exact behavior for the tested profile; it
does not establish DSP register packing, improved frequency, native timing,
full-parent behavior or hardware performance.

See [canonical-dequant-final.json](../../experiments/python-gamebub-v110/audit/canonical-dequant-final.json)
for the result and per-seed hash comparisons.
