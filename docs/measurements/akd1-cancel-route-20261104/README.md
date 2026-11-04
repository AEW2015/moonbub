# Registered CANCEL boundary: routed result

Candidate `fpga/candidates/akd1-compute-cancel-boundary-20261104`.
Manifest SHA-256:
`ac3ea38161c6f6ca69a9ecba7917b3a4cbdf1d5d2b975558c64480d734df8e3b`.
Root independently verified all 172 local artifact hashes.

The four controller expression changes remove raw QSPI ABORT from the compute
enable path while retaining controller STOP priority. Source selection and seven
functional gates are recorded here. Full golden samples, tag and cycles remain
unchanged. No inverse, ROM, platform RTL or timing constraints changed.

Final setup is **-0.025 ns**, with three failing endpoints, compared with
the parent's -2.184 ns. Hold is +0.051 ns and pulse width +2.000 ns; all 29,750
nets are routed and default DRC has zero errors. This is still a failed setup
result. The remaining worst path is GM01 offset arithmetic to envelope RAM enable.

The uncapped reset/BRAM warning inventory contains all 199 warnings; no severity
or rule enable was changed. Independent inspection also confirms that the
unchanged fixture ROM is enabled during reset before PLL lock. That separate
startup blocker prevents hardware use regardless of the small remaining slack.
A guarded-ROM successor is required. No bitstream was generated or loaded.

These are selected exact records, not the complete candidate/checkpoint/source
distribution. Preserve report whitespace and hashes. The manifest inventories
additional local files that are not included in this folder.
