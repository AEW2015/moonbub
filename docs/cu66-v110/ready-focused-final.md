# V110 READY focused proof audit

The selected actual RTL receipt is pinned by SHA-256 `34453cbde56ea4de13a2c31816e17124ff4d8668b36e0208963b3981d04950a2`. Both seeds (111001 and 111002) passed, comparing the complete public interface, producer control/ownership, full raw scale RAM, and independent cache count/error/completion/tag/RAM oracles. Together they cover 33,178 clock edges and 121,180 public comparisons; each seed includes 14,892 accepted cache beats, 12,838 RAM commits, 13 preloads, 19 start attempts, and all 2,048 verification-only count preparations.

The reversible recipe adds same-edge ownership predicates on all 31 producer state writes and all three cache-count writes, with no public cycle added and no registered current-state sample. Original branch/hold/last-write priorities remain in place. Reset, abort, start, final-beat, malformed and missing-last preload, retry, sticky failure, simultaneous start/first-beat, and counter wrap cases are checked. All eight original assertions remain; two assertions check the redundant ownership predicates. Verilator assertions and strict warnings are enabled, with no warning suppression or assertion weakening.

Four earlier failed attempts remain retained: three compile/preparation failures and one driver assertion on partial-preload abort. None reported an old/new RTL equality mismatch; the selected PASS receipt is a later separate run. These focused results do not claim full-frame golden coverage or a full-parent canonical result; those remain the root full-Q gate.

Machine-readable audit: [`ready-focused-final.json`](../../experiments/python-gamebub-v110/audit/ready-focused-final.json).
