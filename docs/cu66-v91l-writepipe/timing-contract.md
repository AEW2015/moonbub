# Consecutive WRITE timing contract

The [manufacturer W9825G6KH datasheet](https://www.winbond.com/resource-files/w9825g6kh_a04.pdf), A04, 2017-03-20, is pinned by the [source receipt](timing-source.json). Its PDF SHA-256 is `9530f7a59a18e062b6832dc96c7a60725b97d85c295631434a12538ee6e1aaf3`. The manufacturer URL was fetched successfully with `curl` and inspected with `pdftotext -layout`; the web PDF parser failed. The board source catalog identifies the fitted **-6** part.

Section 7.4 (p. 7) permits a new column command each clock to an active row. Section 9.5 (p. 15) specifies minimum `tCCD = 1 tCK`; `tWR = 2 tCK` governs recovery after the last written data before precharge. It does not require idle recovery between every single-word WRITE. Section 10.4 (p. 20) defines mode bit A9: retaining `0x233` means CAS3, BL8 reads, and single-word writes. The candidate therefore issues four separate WRITE commands, rather than silently changing the burst mode. Section 7.6 (p. 8) requires data with the WRITE command.

| Requirement for -6 | Datasheet minimum | Candidate contract |
|---|---:|---|
| Column command spacing, tCCD | 1 source period | Consecutive WRITE only to the same already open bank and row |
| Last write to precharge, tWR | 2 periods | Original three-count recovery after final WRITE retained; inspect actual pin spacing |
| Activate to column, tRCD | 15 ns | Original two-count wait retained |
| Precharge to activate, tRP | 15 ns | Original two-count wait retained |
| Active to precharge, tRAS | 42 ns | Pin model checks at least five 10-ns periods |
| Same-bank active cycle, tRC | 60 ns | Existing row-command/recovery schedule retained; inspect pin trace |
| Different-bank activates, tRRD | 2 periods | No bank activation pipelining added |
| CL3 source period | 6 ns | Simulation assumes 10 ns; no achieved clock claim |

The controller may accept a following word while emitting the previous registered address/data. Each accepted word must appear exactly once at the memory pins. A bridge response is legal only after every accepted word has physically drained through final controller recovery. Cancellation prevents new acceptance but cannot discard an already accepted word. Budget exhaustion must stop chaining and allow existing refresh scheduling to proceed. Read turnaround, initialization, refresh and clock phase stay unchanged.

The unchanged functional pin model uses a 4-ns forwarded-clock flight with a 7.75-ns system-relative read-capture phase. Consecutive writes reduce data/address hold margin compared with an isolated write. Datasheet input setup/hold minima are 1.5/0.8 ns for -6; simulation of ideal registers and one clock-flight value does **not** establish package/board delays, output skew, routed setup/hold, or PVT margin. The 2-/7-ns read-delay probes are selected functional tests, not the manufacturer timing envelope. Physical implementation must constrain command/data/clock paths and qualify their complete setup/hold budgets before this candidate is used on a board.

The model covers selected timings and contents. It is not a vendor model, timing simulation with SDF, or exhaustive protocol proof. Neither this experiment nor the layout study establishes sustained hardware 30 fps or complete validated decoding below 10 ms.
