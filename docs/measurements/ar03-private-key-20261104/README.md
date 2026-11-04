# Private KEY reconstruction and tag measurement

These are byte-for-byte retained results from the local isolated FPGA simulation.
`source-snapshot.json` binds the copies to their original files. The manifests
retain original local paths and hashes; their referenced RTL, vectors, simulator
and external dependencies are not all distributed here. This is evidence, not
a portable replay package or a hardware-ready release.

The baseline checked seven main cases, including two native full frames, plus
separate cancellation/error tests. Its final functional manifest is PASS.
The additive A/B uses one identical 48,203-byte 720x480 KEY fixture and changes
only the compiled inverse module, preserving byte-indexed ingress gaps and an
always-ready observer. Both runs checked all 518,400 reconstructed samples
and all 16 stored canonical-tag bytes.

| Actual simulated clocks, accepted start to private result | Baseline | Faster inverse |
| --- | ---: | ---: |
| Controlled near-cap KEY | 3,788,358 | 2,950,451 |

The saving is 837,907 clocks (22.1%). At a nominal 100 MHz, the faster run is
29.50451 ms. That period is a simulation assumption, not a measured board clock
or physical throughput result. The private completion precedes HUD application,
reference-bank publication, AF03, external-memory drain and scanout. P-frame
support and sustained initiation interval are not demonstrated here.

The faster inverse's isolated internal setup/hold estimates are positive;
its ideal-IO hold diagnostic remains FAIL/open. No combined routed implementation
or physical 30 fps acceptance is established by this measurement.
