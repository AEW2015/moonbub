# V56/V029 40-frame run: frame 8 allocation failure

## Outcome

The V56/V029 hardware run presented frames 0–7, then failed Native Prepare for frame 8. The receiver stored all 21,733 bytes of frame 8, but did not present it. The sender stopped on the receiver failure, did not retry the whole sequence, and withheld frames 9–39.

The failure was a native allocation refusal: stage 7, opcode 1, reply 4, text `HUD allocation unavailable`. The allocator record was kind 3, request 16,384 bytes, live 51,166 bytes, free 58,740 bytes, and largest block 15,616 bytes. The physical `largest_probe` is diagnostic only; it did not reject this allocation. The failure reflects the native allocation attempt itself.

## Preserved evidence

- DYN1 v3 sender session `12127381189958033730`, declared sequence count 40. Sender records exactly eight presented frames (0–7), then `frame 8: receiver failed/retained`; `whole_run_retry=false`.
- Frame 8 progress snapshot: length 21,733 bytes, stored prefix 21,733, phase 6, accumulated read bytes 189,603, and eight earlier presentation acknowledgements.
- Native snapshot: `valid=true stage=7 op=1 reply=4`; frame 8, reference 7, generation 9; allocation request 16,384 with reported largest block 15,616.
- Two explicit telemetry re-exports each validated as complete with 23 rows and checksum `d5985e9d`. The device labels underlying transport loss `unknown`; validation does not establish loss-free delivery beyond these complete exports.
- Passive FPGA reads at snapshot time were `0x350..0x360` fields `[11,8,8,0,0]` and `0x110=0`. These are time-local passive reads after the native failure, not evidence of final whole-core fault state.
- Offline localization is in `C:/moon/dev/experiments/cu66-clip40-rgb444-q32-20261108-v003/fragmentation-frame8-v001/REPORT.md`. It identifies HR01 vector capacity growth and a simulated contiguous-allocation refusal. The simulator is not a physical heap reconstruction or proof of a general fragmentation model.

The final image remains held in quarantine. Root reports a V57 exact-reserve candidate frozen with `native/hud.hpp` SHA-256 `92171e1573dc78173b12f5739dc632d09d473daefa3186e286344bdd57b784e` and its build underway. This report does not claim V57 is installed or hardware-qualified.

## Evidence SHA-256

- USB raw serial capture: `743d1b0e1e42fbca04c757bae809fc8b486f0e54b1250337bc25a1c8a69099ae`
- Sender JSONL: `6dcc76f0d190e80c75e4a4718fab42d56a5e2305cb51a03bdac96e1bb5d2b91a`
- Telemetry re-export validation: `168ea06574b3df67ea0d80c182218e51aeacf1f93d50d161c08a27f7196ff163`
- Offline frame 8 report: `3d2150c49364736a650f9be43131a0af07652b891a135eedc8b1e0c748404f8a`

JSON summary: `C:/moon/maintenance/V56-CLIP40-FAILURE-20261108.json`.
