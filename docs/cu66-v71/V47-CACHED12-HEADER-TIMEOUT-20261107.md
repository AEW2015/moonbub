# V47 cached12 attempt: no admitted header before timeout

One `@` arm was issued for the Windows-reported sequence-v3/count12 session2166481219566865132, source`.47:56478`, destination`.157:5535`. Exact V47 ELF and unchanged V027 had been verified. The initial USB capture had completed its1,800-second bound while waiting; a new capture was opened without resetting the device, and its fresh runtime query confirmed the same image and advancing uptime before arming.

The receiver joined Wi-Fi at`.157`, reported116,264free/36,864largest and waited for its first admissible source header. It ended with `Error::Deadline` after the bounded120-second header wait. Retained progress has no active identity, length0, stored0, read_bytes0 and presentation ACKs0. Native stats show live0/peak0/allocations0/failures0. Bus counters report23reads and0writes; passive FPGA owner/accepted/presented/rejected/underruns/stage-error were all0.

Windows subsequently confirmed its invocation ran10:20:19–10:30:20pm Denver on November7, exited1 after timing out for the first KEY stored-prefix ACK at offset1,024, and transmitted no frames1–11. No presentation or status3 was confirmed; raw replies were not logged. This is an operator/agent relay, not a locally inspected raw host file.

The receiver PC recorded arm at05:36:53.844533UTC and readiness at05:36:58.036882UTC on November8, corresponding to10:36:53/58pm Denver on November7. The recorded wall-clock windows therefore do not overlap: the uploader had expired before receiver readiness. Independent clock synchronization was not measured; no cross-machine monotonic subtraction was performed. This is a coordination failure consistent with the empty receiver trace, not evidence of a codec regression.

This attempt did **not exercise native decoding or V47's allocation-order change**. No valid header was admitted; the trace does not identify individual datagram fate. It must not be recorded as a successful or failed fragmentation fix.

Both23-record retained exports independently passed count/index/checksum validation with hash`48c5761e`. The underlying USB loss count is unknown. Native minimum-free remained its unused sentinel4,294,967,295 and is not a valid measurement. Wi-Fi disconnect/stop/deinitialization followed the timeout. A later query confirmed the same ELF/reset reason3 and168,252free/38,912largest. No retry, rearm, power cycle or programming followed.

The90-second camera capture ended before the receiver's120-second wait completed; no new hardware presentation is inferred. Sources and images remain unchanged. Next is a normal reboot to restore the one-shot Wi-Fi owner, same-image verification/V027 reload, then a fresh separately coordinated invocation with current sender start time and remaining wait confirmed immediately before arm. No new firmware or FPGA fix is selected from this result.

Evidence: `C:/moon/dev/evidence/v47-v027-network-20261107-run01`, raw USB`usb02`, [machine-readable result](V47-CACHED12-HEADER-TIMEOUT-20261107.json).
