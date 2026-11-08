# V110 focused dequant proof

The actual paired dequant RTL proof passes three seeds: 110901, 110902 and
110903. Each accepts 6,716 transactions, retires 6,686 and discards 30 through
reset/abort. All 17 recorded source files match both current files and retained
snapshots. Verilator assertions remain enabled; warnings are strict and
unsuppressed; the proof records zero added public cycles.

The unchanged testbench compares all public outputs against the original on
every evaluation, checks all 64 packed output words against its independent
integer oracle through partial, invalid, held and reset/abort states, and
preserves the golden and assertion paths. This is focused component evidence;
full combined-dequant canonical qualification and native timing are separate
gates.

See [dequant-focused-final.json](../../experiments/python-gamebub-v110/audit/dequant-focused-final.json)
for receipt pins and exact per-seed counts.
