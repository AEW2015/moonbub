# V47 cached12 attempt: no admitted header before timeout

One `@` arm was issued for the Windows-reported sequence-v3/count12 session2166481219566865132, source`.47:56478`, destination`.157:5535`. Exact V47 ELF and unchanged V027 had been verified. The initial USB capture had completed its1,800-second bound while waiting; a new capture was opened without resetting the device, and its fresh runtime query confirmed the same image and advancing uptime before arming.

The receiver joined Wi-Fi at`.157`, reported116,264free/36,864largest and waited for its first admissible source header. It ended with `Error::Deadline` after the bounded120-second header wait. Retained progress has no active identity, length0, stored0, read_bytes0 and presentation ACKs0. Native stats show live0/peak0/allocations0/failures0. Bus counters report23reads and0writes; passive FPGA owner/accepted/presented/rejected/underruns/stage-error were all0.

This attempt did **not exercise native decoding or V47's allocation-order change**. No valid header was admitted; the trace does not establish whether datagrams reached the radio/network stack, were filtered, or were never sent. Windows' actual result is pending. It must not be recorded as a successful or failed fragmentation fix.

Both23-record retained exports independently passed count/index/checksum validation with hash`48c5761e`. The underlying USB loss count is unknown. Native minimum-free remained its unused sentinel4,294,967,295 and is not a valid measurement. Wi-Fi disconnect/stop/deinitialization followed the timeout. A later query confirmed the same ELF/reset reason3 and168,252free/38,912largest. No retry, rearm, power cycle or programming followed.

The90-second camera capture ended before the receiver's120-second wait completed; no new hardware presentation is inferred. Sources and images remain unchanged. Next is reconciliation with the same Windows uploader, then a separately coordinated retry only after the cause of this empty attempt is understood. No new firmware or FPGA fix is selected from this result.

Evidence: `C:/moon/dev/evidence/v47-v027-network-20261107-run01`, raw USB`usb02`, [machine-readable result](V47-CACHED12-HEADER-TIMEOUT-20261107.json).
