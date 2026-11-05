# Git-sized AKD1 source-only export

This is a packaging derivative of the sealed145-artifact export, parent manifest
SHA256852f12839e39dae04e87659c1d0c34b0c4a2eb148ca686d52b8e7da02bc9d902.
provenance/parent-manifest.json contains that exact record. This derivative's
manifest binds only files actually included here; it does not require omitted
checkpoints, simulator binaries or build caches to verify successfully.

The exact21 design RTL files, fixture/quantizer HEX images, live constraints,
positive proofs, licenses and portable launchers are retained. Every input in
the executed parent's clean-build input hash map and every portable launcher
is byte-identical. No GameBub/MoonBub/codec checkout or old checkpoint is needed.
Use Python3 and licensed Vivado2025.2 for xc7a100tcsg324-1:

```powershell
python C:/path/to/export/rebuild.py --out build-local-001 --vivado C:/Xilinx/2025.2/Vivado/bin/vivado.bat
python C:/path/to/export/verify_export.py
```

The default rebuild starts fresh from local sources. Its report readback opens
only the new checkpoint it generates. No image is generated or automatically
selected. Do not use --adopt-completed-source-build on the inherited records:
the parent working directory and its checkpoints are intentionally absent.

No new full FPGA build was run for this packaging task. Compact records under
evidence/inherited-clean-build describe the parent's executed clean build:
+0.015ns setup,+0.039ns hold,+2ns pulse,0failing endpoints; all16ROM/all44overlay
and exact106BRAM coverage passed. The qualifying183-warning report is under
that directory's fresh-drc-audit/. These are inherited executed results bound
to identical source inputs, not a claimed build at this derivative's path.
Relocated portable controls20 and actual-QSPI ordering58 smoke tests were rerun
PASS; their logs/input hashes are under evidence/derivative-smoke/. Generated
.vvp files and duplicate runtime HEX copies were removed after those tests.
Optional executable benches and original payloads remain under verification/.

selected-image/akd1-compute-rev4.1.bit is the supplied ORIGINAL2419167-byte BIT,
SHA256b1ca685e457446838b9d6c78b86f02c4b793dad42eccb3b5c50075d17e20e260.
It belongs to the selected qualified resumed flow, not the later clean source
run. selected-provenance/ preserves that distinction. This task generated no
replacement BIT and performed no programming or hardware action. There is no
byte-identical image reproduction claim. selected-image.json marks its missing
qualified checkpoint as an omitted hash reference, not an included dependency.

Omitted checkpoint hashes, using parent paths:

| Parent checkpoint | SHA256 |
| --- | --- |
| build-clean-001/akd1-clean-routed.dcp | a4668cf73671a0ca88d349d10c5f242459c1a12429feeeeaffe3fe186eaa8d30 |
| build-clean-001/constrained.dcp | f8fe3009c10f7047892cc9cee91e7321c247eaa58abd5fadb04783dd30b4b3f2 |
| build-clean-001/synthesized.dcp | 933ba8c741207cede70bad05fa2328016881b40a1ae85dc6704d9b5c39373b78 |
| selected-image/qualified-routed.dcp | 26dd84ab25389cc62011fc0e2ed648e187c6a4c3cf29582605657e425820e760 |

derivation.json also records omitted simulator hashes and inherited evidence.
The full106664129-byte parent ZIP remains local, SHA256
b1ad8c673816e59b98428e60f9eb16364c714e662a5c8a01979fa533d071499e.
It is not included here and was not staged or published by this task.

Scope remains controlled fresh-configuration AKD1 diagnostics: <=16MHz QSPI
lab assumptions, audioOFF/provisional electrical budgets, noresetduringjob,
no warmPLL-loss retention or maximum-rate/external-hold qualification. SDRAM
is inactive/unqualified. LCD shows native bars/overlay, not private decoded KEY
pixels. Root owns physical actions/publication. Codec pins remain unchanged.
