# V114 primary 100 MHz prepared-card audit

**PASS_V114_NATIVE_PREFLIGHT_AUDIT**. The independent
[audit](../../experiments/python-gamebub-v114/audit/primary-100-preflight.json)
binds the exact [prepared card](../../experiments/python-gamebub-v114/prepared/v114-spatial-100-20261108T231844737185Z-b820e2/preflight.json),
SHA-256 `49df46e9df2090ae6c25d2fc2d22d3bc740abeef1a210d43b1c19be63e9ed093`,
policy `d88a760642491b38176b050169e36ae92bbcabb85f7c6d32973b3cd69acab8dd`
and native guard `66ff33717fbeb566a2be46c7931fc5687bf993430c86e285e278051aa5c273a5`.
No build, native launch, source/proof edit or hardware action was performed.

All 18 external source snapshots match current source pins and the qualified
functional composition; only the V113 top controller is replaced. Geometry,
scratch, IV113.1 inverse and source ordering remain frozen. All local/external
recipe copies and tool hashes match. The immutable image resolves to
`sha256:dd51b5dd44148c23bb0059b929697243797022172d5efb01ffdd8b8dd7a89742`.
Fresh RTL is mandatory, the 10.000 ns clock XDC is read before default synthesis,
and its period/waveform are checked after synthesis. Opt/route remain Default,
placement ExtraNetDelay_high; no retiming, false/multicycle path, guessed IO delay,
bitstream or hardware command is added.

All focused proofs and the fresh 44/42 canonical plus 24/4 transport qualification
are pinned and validated, including stdout-verdict equality and raw canonical
hashes. The reversible API adapter reconstructs the untouched 496-line original.
Its 144 `need(` occurrences (including the helper definition) become 145 with the
new pending-eligibility assertion; immediate cache consumption and metadata poison
precede the E+1 delivery tick. The separate transport derivation reconstructs this
adapted base. Functional/public-cycle equivalence to the earlier top is not claimed.

The six retained controls were hash-checked and reparsed at their own clocks:
Count100/V112100/V113100 at 10 ns, WNS −1.022/−1.034/−1.686 ns;
Count125/V112125/V113125 at 8 ns, WNS −3.264/−2.844/−3.303 ns.
The candidate must be compared with its same-clock controls. These negative
controls do not predict candidate timing.

The global native ledger allows four initial source-qualified 100/125 trials and
one fresh repeat of a positive result, with no failed-clock repeat. Each
composition also permits only two initial trials. Root owns serialized dispatch
and at most two heavy jobs globally, including simulations. Native jobs enforce
two CPUs, two tool threads, 8 GiB RAM with 8 GiB memory-plus-swap, a 3,600-second
watchdog and available-memory/PSI/combined-use stop gates. Docker active-name
checks supplement Root's scheduler. Existing read-only license/tool mounts and
host networking retain the validated license method; no host identity is changed.

This audit authorizes no achieved-clock, routed timing, board FPS or complete
under-10-ms result. Actual internal setup/hold/pulse, route completion, before/after
XDC, methodology, fanout and primitive reports remain terminal-result checks.
External IO requirements, complete production PCTL1, parent CDC/memory/panel and
publication qualification remain open.
