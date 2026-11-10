# V128 baseline review

Reviewed commit: `c196ad83e4c077bb50f9706058fb6416425d4fc5`. This is a read-only static evidence audit; no simulation, synthesis, new timing run, or hardware claim was made.

## Pinned V127 evidence

- Root results: `5e872674c6243a3faf4aafab1a3df5cca842e23b8427ce91403130a30c6d40b9`; status `COMPLETED_BOUNDED_STUDY_125MHZ_TARGET_FAIL`.
- Native receipt: `47ca8bedc398933be0b70b79f94d1a93ecb9672e94c06139dbf0886d86d9557e`; root pin matches: **True**.
- Independent audit: `46d71ad87837eaa16b04b7d46a923a5e96a1e6f37ffbc7571988bd3b2495da03`; root pin matches: **True**. It reports `PASS_V127_INDEPENDENT_TERMINAL_EVIDENCE` and `COMPONENT_ROUTE_FINISHED_SIGNOFF_OPEN` with 1530/1530 checks passed. The audit validates the evidence; design timing is **FAIL**.
- No `index.json` exists under `experiments/python-gamebub-v127`.

## Timing and parent cycle baseline

At the 125 MHz component target, V127 has WNS **-1.193 ns**, TNS **-1762.554 ns**, and **6980** failing setup endpoints of 104659. It is not timing qualified.

The row parent records 1,145,104 fast cycles and 1,553,197 stalled cycles. At the assumed 125 MHz these project to 9.160832 ms and 12.425576 ms; the complete parent clock is not physically qualified.

## Source and protected-file checks

All 18/18 original qualified B100 physical files match their metadata when checked at the physical paths in Git `69c0f145d1e3969f5418645a79647634b312214b` (not their alias paths). All 18/18 current V127 selected physical sources match the V127 native receipt hashes. Protected marker metadata from the V120 baseline is unchanged for all 2 files, including byte count, SHA-256, and mtime.

## Hardware goals and machine snapshot

Whole-parent routed-clock qualification, validated hardware decode under 10 ms, and sustained hardware 30 fps remain open. No board bitstream was generated and no hardware contact is recorded.

At review time, available RAM was 19.06 GiB; PSI full avg10 was 0.00, root disk use was 88%, and the listed running Docker containers and image IDs are recorded in the JSON. This exceeds the frozen launch thresholds; no heavy job was launched as part of this audit.
