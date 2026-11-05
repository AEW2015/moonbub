# Epoch-3 baseline packet correlation

Saved-evidence audit only. No new hardware run, device query, firmware update, FPGA update or pacing change.

Source: AEW2015/Sunshine commit e732dbd7, `tools/gamebub/measurements/v30-pcap-requested-correlation-20261105.json`; downloaded bytes SHA-256 `48fa074646ce2b01c3c15fd6980c0691b266adf12e0804f759ab97e09be13395`. Exact records and machine-readable joins are saved beside this report.

Host reconciliation: 600 encoded = 526 complete + 74 replacements; zero partials/skips. 526 complete = 522 accepted + 3 rejected + 1 unmatched (2014108). Receiver increases: 522 received/decoded/presented and 3 dropped. Unmatched is not silently classified as accepted or dropped.

## Frame 2013780

Host capture timestamp: 1793862069142206 Unix us. Npcap/NDIS Wi-Fi outbound Ethernet-format capture positively records offsets 9216, 10240 and 11264 in order at 07:01:09.204533, .207144 and .210157 UTC. This extends the evidence beyond the application send API; it is not over-the-air delivery evidence.

Receiver offset 9216: RX 2791758151 us, enqueue sample 2791758222 (q8), dequeue 2791772581 (active2013780/expected9216, q6), recycle2791773246, complete2791773413. Offset11264: RX2791759129, enqueue2791759219(q9), dequeue2791774718(active2013780/expected10240,q6), failure2791775015(detail64), recycle2791780395, complete2791780466. Consumer duration5743 us.

**Offset10240 is last positively observed at the host's outbound Npcap capture point.** There is no retained receiver RX/enqueue/dequeue/assembly event for it. The expected10240 field is assembler state, not an observation of that datagram. Epoch3 lost2085 salient trace records; no per-event loss localization exists. Therefore the segment between host capture and receiver assembly remains unresolved, including possible unrecorded receiver observations.

The assembler software abort occurs inside failed accept before the Failure event; no distinct absolute reset/FPGA-abort completion event is retained. Recycle/Complete are observed, but their context fields describe the pre-accept packet state rather than post-cleanup assembler state.

## Frame2013900

Host capture timestamp1793862075141377. Npcap positively records SOF0 then1024/2048/3072 at07:01:15.188769/.191599/.194598/.197498 UTC. Receiver failure table records incoming3072, RX2797738775, failure2797754880, inactive assembler, q5, detail128, consumer4178us. This later failure lies outside the first-trigger frozen packet ring. SOF reception/admission/rejection and intervening cleanup are **unknown**, not established as missing.

## Boundary2014108 to2014109

Host capture timestamps1793862085541116 and1793862085589548. This boundary is outside Npcap coverage. Host successful-send logs show2014108/17408 is its final37-byte payload, followed353.7us later by2014109/SOF0;2014109/1024 follows2623.4us later. This is a measured short inter-frame API-send gap, not proof of an RF burst or a cause.

Receiver failure for2014109/1024: RX2808156872, failure2808171393; active2014108/expected17408, q6, detail121 (multiple header/offset mismatches), consumer4742us. Thus the previous assembler remained incomplete at this decision. Receipt/disposition of the final37 bytes and next SOF is unknown; later cleanup is outside the frozen ring.2014108 remains an unmatched host outcome.

## Coverage and limits

Host reports Wi-Fi Npcap/NDIS Ethernet encapsulation,8971 captured packets,0 reported capture drops. Capture covered only00:01:00.182122–00:01:20.962951 Denver, excluding the last approximately9 seconds and STOP. Capture counts/CRC validation are host-reported; the raw pcap is not present locally. Exported receiver trace is complete but capture is not lossless:2085 lost records,12425 normal overwritten records,0 lost failure identities and0 queue overflows. Later failure identities are preserved, not their full packet histories.

No subtraction of clocks across machines was performed. Numeric capture timestamps are not stored by the receiver, so joins use frame ID+offset within the unique run; host timestamps remain host-side identities.

Post-STOP counters, camera coverage and power-save restoration are in `../RECEIVER-RESULT.md`. Installedv30/build50 remain unchanged. Next offline work reduces tracing critical-section cost and localizes trace loss before selecting a streaming fix.
