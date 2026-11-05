# V30 retained Sequence evidence closeout

This closes offline correlation for the two completed controls. It selects no streaming fix. No new sender, device query, firmware/FPGA installation or pacing change was performed during the overnight development window.

## Last positive observations

| Run / packet | Last positive evidence | Receiver conclusion |
|---|---|---|
| Epoch2,2013421/4096 | Windows successful post-send1354793.5164743s | No retained RX/enqueue/dequeue/assembly event. Missing trace does not prove missing datagram. |
| Epoch2,2013422/SOF0 | Windows successful post-send1354793.5550626s | SOF receipt/admission/rejection unknown before1024 met an inactive assembler. |
| Epoch3,2013780/10240 | Outbound Wi-Fi Npcap07:01:09.207144UTC | No retained receiver event. This extends observation beyond the send API, not to RF delivery. |
| Epoch3,2013900/SOF0 | Outbound Wi-Fi Npcap07:01:15.188769UTC | SOF path unknown; later3072 failure is outside the frozen packet ring. |
| Epoch3,2014108/17408→2014109/SOF0 | Host post-send records only; final37-byte tail then353.7us inter-frame API gap | Previous assembler remained active/expected17408 when2014109/1024 failed. Tail/SOF disposition unknown;2014108 remains unmatched. |

Never subtract host and ESP monotonic clocks. Numeric capture timestamps are absent from the receiver trace, so these are frame-ID/offset joins inside uniquely identified runs, with host capture values retained as host labels. A fully independent three-field join cannot be claimed.

The exact event tables, active IDs, cleanup ordering, queue observations and coverage limits are in the adjacent published measurement files. Queue occupancy samples are not atomic push/pop times. Producer active-valid=0 means assembler state was not sampled, rather than proven inactive. Software abort ordering is source-derived where an absolute cleanup event was not retained.

## Final repeat reconciliation

IDs2013600–2014199:600 encoded=526 complete+74 replaced; no partials/skips. Complete outcomes522 accepted+3 rejected+1 unmatched2014108. Receiver523/523/523/2→1045/1045/1045/5 received/decoded/presented/dropped. Queue drops0; cumulative high15/32 was already15 before the repeat. Core faults/overflows/underruns/transport overflow0. No reboot observed. AV STOP restored power saving0→1 with zero entry/restore errors.

Epoch3 export is complete but not lossless:2085 lost trace calls,12425 overwritten ring records, zero lost Failure identities/phase publications/queue overflow. Epoch2 lost2376 trace calls. There is no per-packet loss localization in either capture. Complete export and zero failure-table losses do not repair missing packet histories.

Host Npcap reported8971 packets and zero capture drops, but covered only00:01:00.182122–00:01:20.962951Denver; the last approximately9s and STOP were not captured. Raw pcap is not local, so its capture/CRC assertions remain host-reported. Receiver camera covered START through STOP with changing full-panel scenes; sampled observations do not establish no subsecond freezes or30 unique fps.

## Narrow next receiver candidate

V31 removes full phase-max copying from the hot trace mutex and adds eight per-kind loss counters without changing queues, protocol, FPGA, power-save or pacing. It has passed offline source/host/target/UF2 gates and remains uninstalled. It is not a packet-identity journal and does not add numeric capture timestamps. Its next controlled physical comparison can measure trace-loss/delivery effects; those effects are not established yet. An independent bounded-history design is being evaluated separately rather than claiming these old records locate the failure.

Use fresh unused IDs2014200 or newer, one selected software change, unchanged build50/overlap/32slots, the same saved clip/settings, full camera and outbound capture through STOP. Reconfirm identity/network/start counters after power-up. No run is started by this document.
