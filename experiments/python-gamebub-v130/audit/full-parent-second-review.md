# V130 full-parent receipt: independent second review

**Review mode:** read-only. I did not rerun the simulation or modify its
receipt, tests, or RTL.

## Receipt and pinned inputs

Reviewed attempt `20261111T024318444729Z`.

| Item | SHA-256 |
| --- | --- |
| V130 receipt | `33626c670d44c144c8d5942d19022983f9bfba4fb9b616b5fae479f4ef5d08c3` |
| V130 admission candidate | `0b7131bbccc7c9cbc794b51a205210a32138f74bc751d5d8679a87745acb7168` |
| Full-parent runner `qualify.py` | `779e6603014c3ea682341d10a17cea5ba2aea187ddcbddfcea8479728b836a21` |
| Preflight | `2cae98990979d8cbbe9468a770cf314317bbdb51c8258bd3751a461ceac8989e` |
| Testbench `tb_keyframe.cpp` | `cad383becd5a9d20a8722a4ec78b0cb5ae86d7967abdbfac0a4857c6b1da4b18` |
| Parent RTL `cs88_live_v91l.sv` | `0f649831a4143d6afd8983b8f4b72eb1b6caeeee7a26ad5b8ec0d4545046ff4d` |
| V129 exact-parent baseline receipt | `7e7e71ed6e6bdd4b4d8f34a82607df3d592f9dd9b7229ba920153389b887aa44` |

The 108 receipt source hashes match their attempt snapshots, and all 116
receipt-listed artifact hashes match the files on disk. The V129 baseline
receipt hash matches the V130 receipt's baseline binding. The V130 testbench
and parent RTL match the corresponding V129 live-guard snapshots byte for
byte.

Fixture hashes recorded in the V130 receipt:

- `cases.tsv`: `54fe65f22dd8d0fc45b1fd0444e12632e1d800269705371f677aae5e6b8b5abc`
- `transform_tiles.tsv.gz`: `65a197981ccfcb0dc71cff6aa2324619ba9cc43551cff6f81c135ad6c0dba729`
- `canonical_goldens.tsv.gz`: `1670dac7dfd25b4558e7aa469620dc468a8e3dbb63061b1cce2db1c42b6891cb`
- `validation.tsv.gz`: `3884cd2082aa0f8121790b0fea786d7f29e3ab46689251e17747143e2143259d`

## Run and comparator evidence

The receipt records two Verilator builds and four simulation commands in the
pinned network-disabled container `sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf`.
Builds use `--assert -Wall`, C++ `-std=c++17 -O2 -Wall -Wextra -Werror
-DELASTIC=1`, and `-DROW_WRITES=0/1`. Both builds and all four simulations
exited successfully. The receipt reports assertions enabled, no assertion
downgrade, strict warnings, and no warning suppression.

V130 ran four combinations (byte/row writes and seeds 116701/116702). For
each, the runner compares the six terminal dictionaries
(`live_case`, `fences`, `service`, `verdict`, `spatial_pipeline`, and
`parent_guard`) and raw hashes for `events.jsonl`, `actual.tsv`, and
`hashes.jsonl` with the matching V129 run. I independently checked that all
four run keys match and these records and stream hashes are identical. The
checks are implemented in `scripts/cu66-v130/full-parent/qualify.py` around
lines 424–429.

The parent comparison has no invalid-data masks
(`parent_masks: []`, `invalid_data_mask_applied_to_parent_oracles: false`).
It is an exact comparison of the declared terminal/event/output/hash
contracts, not an all-cycle comparison of every public top-level port. The
focused admission pair separately compares `replay_data` when
`replay_rsp_valid` and `stage_read_data` when `stage_read_rsp`.

## Scope and limits

The receipt status is
`PASS_V130_EXPLORATORY_SELECTED_COMPONENT_BYTE_ROW_ACK_C2_HUD_ABSTRACT_PUBLICATION`.
It supports the exploratory candidate's behavior in these finite parent
simulations and agreement with the selected V129 parent stream controls. It
does not qualify the release composition or external invalid-cycle data
behavior. The receipt explicitly leaves unqualified debug consumers
unverified and the external consumer contract unknown.

The run uses abstract finite service and abstract publication, with software
HUD decoding. It does not establish full-parent routed timing, physical SDRAM
behavior, ESP32 execution, hardware contact, hardware 30 fps, a full RTL HUD
decoder, or validated decode below 10 ms. The selected spatial proof remains
V129, not V130. No material receipt, source-freeze, command, or comparator
inconsistency was found within these stated limits.
