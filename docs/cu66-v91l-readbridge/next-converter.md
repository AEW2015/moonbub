# Next converter comparison after the physical read join

Keep the newly joined scalar converter, retention reader, tagged BL8 bridge and timed controller as the functional control. The native base RGB565 result is a display-consumer component; a source or decoded frame is preloaded before measurement. It does not include live entropy/reconstruction, semantic HUD, validation/publication or a shared controller workload.

The isolated retention reader's read count is useful but does not predict the complete converter time. The actual converter still issues 518,400 byte requests per frame through its byte-to-line adapter. It performs 345,600 registered chroma lookups and pixel conversions, even though external canonical reads are already grouped into 32,400 logical lines. The timed campaign adds state/wait occupancy to locate the cost before changing this path.

The final timed report's `actual_006` sample (seed 912701, tAC 2 ns) closes in 3,361,069 cycles. Its disjoint converter-state occupancy is:

| State group | Cycles | Fraction of frame fence |
|---|---:|---:|
| Chroma fill request/wait | 628,999 | 18.71% |
| Luma request/wait | 1,262,670 | 37.57% |
| Registered lookup and conversion stages | 1,036,800 | 30.85% |
| Pixel emit (including ready stalls) | 431,876 | 12.85% |
| Other states | 724 | 0.02% |

The same sample observes 543,034 controller-busy cycles and 660,469 reader-physical-pending cycles. Those counters **overlap** the state groups and each other. They are diagnostic observations from the pinned C++ bench, not independently reconstructed state traces or separate latency costs. The scalar lookup/conversion stages alone visit three clocks per output pixel; removing or overlapping a stage must still meet physical timing, RAM and ownership requirements.

The next bounded alternative should be **burst-aware canonical consumption**, with the existing arithmetic and physical layout preserved:

1. Put an explicit aligned 16-byte canonical response register and cursor inside the converter consumer. Reuse the three plane-line payload slots where practical; account for every additional register if they cannot be reused. A byte already in an owned line can enter the local consumer without a separate external byte request/response lease. A line miss retains the current tagged 16-byte request contract.
2. Fill the original registered chroma-row RAM from a held burst one byte per cycle, respecting its existing bank/byte-enable structure. Do not assume sixteen simultaneous writes to one RAM. Maintain complete-row validity and the registered neighbor lookup before a pixel can be emitted.
3. For luma hits, consume the next byte from the owned line directly, then use the same registered chroma lookup, bilinear rounding, Q8 color arithmetic, clipping and RGB565 packing. Keep output stable under backpressure. The first alternative should avoid adding another line or speculative frame owner.
4. Preserve actual converter-order plane cursors, immutable bank/epoch/generation leases, rejected invalid order, held responses, cancellation at all memory/line/pixel boundaries, accepted BL8 drain and clean retry. A local line cannot remain valid after its lease changes.
5. Compare separate static scalar/burst builds with both native canonical/base-RGB goldens, existing edge cases, two seeds and both selected timed SDRAM data delays. Check every output pixel, row digest, memory address/data, controller capture and completion fence. Compare start→first pixel, start→last pixel, final closure and state/physical-stall counts under the same declared ready policy. Unchanged bitstream syntax/quality is a gate.

This is an implementation candidate, not a promised speedup. State occupancy includes overlap between a waiting converter state and memory activity; those counters cannot simply be added or subtracted as independent savings. No nominal cycle budget establishes achieved FPGA frequency, routed memory timing, continuous cadence or hardware FPS.

After this controlled consumer comparison, join live producer/writer, accepted-reference and scratch reads, hashing/publication and display consumption on one finite physical controller. Use measured display service deadlines and bank-role ownership; do not sum independent write/read component fences. RTL HUD decode/overlay and mixed-entropy or negotiated fallback remain open. V91m's full source-cadence path and V100–V110 exact-device mapping/timing/hardware gates remain separate requirements.
