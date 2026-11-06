# Structural read/write address split

The original bridge selects either queue BRAM data or the held read address on
one `core_address` wire. Its response register captures only in read state 1,
when that selector always chooses the held address. Nevertheless, the shared
combinational CSR read mux exposes an impossible queue-BRAM-to-response timing
path. This successor removes that combinational connection structurally.

`cu71_bus_cdc_split` emits queue address on `core_address` and the registered
mailbox address on `core_read_address`. `cu71_local_control_split` and
`dy71_local_control_split` use the new `bus_read_address` **only in their final
combinational read-mux case**. Every write decoder, staging upload and command
check continues to use `bus_address`. No FIFO, FSM, counter, reset, mailbox,
response-enable, acknowledgement or dummy cycle changes. Register offsets,
profile identities and the physical QSPI protocol remain unchanged.

## Held-address contract

The SPI-domain `read_address` changes only on a read request. Software/endpoint
must retain the existing rule of at most one outstanding mailbox read. The
request toggle crosses three synchronizer stages. The core drains queued writes
before latching the request address; then, on the next core edge, captures the
CSR response, and on the following edge toggles acknowledgement. The response
remains held for the existing synchronized SPI capture. `latched_address` is
unchanged between these snapshots; separate write-address activity cannot enter
the read mux. This is the same bundled-data protocol, with the same existing
10 ns read-address/response maximum-delay bounds and scoped first-stage/Gray
constraints. No new exception or synchronizer is introduced, and no external
QSPI hold or metastability qualification is claimed.

## Executed functional checks

`evidence/functional03` compares actual original and split CU71/DY71 controls
through paired bridges at two exercised clock phases (0 and 2.3 ns):
4,305 mailbox reads and 559 consumed writes per run, including all 4,096 byte
read addresses, actual typed BEGIN/upload/SEAL/discard, ordered write/read drains,
paused-core FIFO saturation, matching overflow Gray values, internal pointer /
FSM / synchronizer state, held-address snapshots and joint reset cancellation.
All other actual control outputs are compared cycle for cycle. Read-data output
while no response is captured may differ intentionally and is not equated.

The unchanged actual QSPI endpoint wire suite also passes both phases against
an original-bridge shadow: 40 MHz writes, 16 MHz reads, 1,024-byte stream/checksum,
auto-increment reads, framework registers, all button bits, IRQ W1C, overlay,
partial-CS cancellation and reset cancellation. This is simulation only.

Failures are retained: functional01 lacked the local MSYS DLL PATH; functional02
accidentally changed the synthetic test bank's write decoder as well as read
mux. The candidate RTL was unchanged; functional03 corrects that testbench.

The OOC comparison uses actual complete CU71 control/staging/arbiter and exact
xc7a100tcsg324-1, 200 MHz SPI / 100 MHz core and 1 ns I/O budgets. Existing scoped
CDC/bundled-data constraints are copied in disclosed form, not whole-board
exceptions or new queue-response false paths. Synthesis estimates and structural
cone checks are not routed timing, hold, image or hardware signoff. DY71 differs
only in documented identity/capability constants; its full behavioral paired
suite is executed independently.


## Native OOC result

The exact-part unplaced comparison is preserved in `evidence/ooc-old02` and
`evidence/ooc-split01`. The timed queue-BRAM-to-response paths disappear
**32 -> 0**, without an exception added to that cone. Worst response-register
setup improves **+3.173 -> +5.039 ns**. The original source is the queue RAMB36E1;
the new worst response source is a registered staging written-byte count.

Whole-component timing is **not closed**: WNS changes -0.862 -> -1.180 ns, WHS
is -0.751 ns in both, and pulse-width slack is +2.000 ns. Both worst setup paths
are the unchanged staging `packet_bytes_reg[1] -> held_count_reg[0]/CE` cone;
logic has 20/19 levels and 12/11 CARRY4 elements respectively. These are
unplaced estimates; full-board placement/routing is required to judge physical
improvement. Resources change 1681 -> 1689 LUTs, 2247 -> 2244 FFs, while 17 RAMB36
and zero DSPs remain. `ooc-old01` preserves an initial object-count oracle failure
(two queue BRAMs assumed; actual native inference is one 64x44 RAMB36E1).

No complete native HU round trip has yet selected these split control variants;
the independently sealed original-CSR v36 KEY/P proof is not relabeled as this
variant. A new explicitly selected SYNCsafe/math + split-control round trip is
the next integration gate. No programming image or hardware change is included.
