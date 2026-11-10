# V125: prepare admission tile predicates on existing edges

V124 passed its finite functional suite, but its fresh 8 ns route failed at
−1.170 ns WNS, −2,527.615 ns TNS and 9,787 setup endpoints. Its worst path runs
from admission tile state to a tile clock enable, through shared hidden/group/
terminal control. The data delay is 83.696% routing. V125 tests a bounded
registered-control change, preserving the full-width arithmetic and public cycles.

## Preflight and exact source scope

Before editing candidate production RTL, inspect the existing V123 and V124
routed checkpoints with the same frozen read-only query. Add tile, plane and
group-end source families to tile/coordinate/state D/CE and mode RAM EN/WE/data
targets, with complete register inventory and explicit missing-path gaps.
Keep the earlier owner/RAW/rank/cursor/refill queries. No checkpoint, constraint,
property or implementation is modified. These observations establish comparisons,
not a new physical trial or qualification.

Change only the admission origin relative to frozen V124. Preserve the V124
producer owner lanes, V123 scratch rank, V121 refill queue and the other origins.
Prepare `hidden(plane,tile)`, `tile==tile_count(plane)` and `tile==group_end` in
three scalar registers named `prepared_tile_hidden`, `prepared_tile_terminal`
and `prepared_group_terminal`. Capture on existing parser edges using exact
successor keys. GROUP_BEGIN retains its original group-end write; the completed
MODE_BIT tag-commit edge samples that already registered end before the first
GROUP_TILE consumer. This avoids adding a new `tile → min(tile+16,count) →
group-predicate D` cone. Tag commit takes an atomic three-scalar snapshot;
later mixed/group tile steps refresh it with successor tile keys. Header,
KEY_TILE and plane-clear edges refresh the tile predicates. Verification group
ownership remains invalid until tag commit. Use them consistently at the relevant
state/coordinate/mode-write consumers. No added public phase, cycle, packet field,
quality/rate change, width truncation, KEEP, DONT_TOUCH or placement directive.

Counters remain uint32 and plane remains two bits, including plane three.
Retain wrapping `tile+1` and `tile+16`, literal minimum/equality semantics,
hidden boundaries and all reset/start/abort/error priorities. Payload scalars
need no blanket reset if every actual consume is proven initialized and owned.
Verification-only complete keys and validity may assert this ownership; they
must not substitute for a production predecessor or mask an incorrect result.

## Proof and measurement gates

Preserve every existing assertion, oracle and exact public-cycle comparison.
Use a separate source-bound scalar probe for generic high-bit equations rather
than clocking unreachable coordinate states. Any adaptation of a prepared-domain
fixture must execute an original predecessor to prime the new registers, retain
the original comparison checks, and document its scope. Never force new payload/
owner bits, suppress coordinate assertions or discard inconvenient edges.

Require focused generic and actual-controller seed pairs, then fresh complete
decoder/actual V97 transport, physical-debt peer and byte/row validation parent
runs. All eighteen aliases, their source order, retained source/packaging hashes,
raw events, canonical bytes and terminal dictionaries must match V124 with zero
public-cycle delta. Independent audits rehash the selected receipt/artifact chain
before a native launch.

Use the unchanged V120 core Tcl/XDC recipe, xc7a100tcsg324-1 and pinned Vivado
2026.1/build6511674. Load the 8 ns clock before fresh RTL synthesis. No guessed
board delays, timing exceptions, clock relaxation, checkpoint implementation
start or unchanged-negative-source reroute. A fully positive internal component
result requires a separate fresh same-source/tool/core-recipe repeat. Report
global setup, hold, pulse, coverage, routing and methodology alongside every
queried family and both sides of each new register; a shorter tile path alone
does not qualify 125 MHz.

## System goals and resource control

The retained row parent is 1,145,104/1,553,197 post-final-input→validated-commit
cycles. With zero public-cycle change, an assumed complete-parent 125 MHz still
projects to 9.160832/12.425576 ms. Strict under-10-ms stalled decoding needs at
least 303,198 fewer cycles. Complete-parent timing, calibrated ESP32 Wi-Fi/QSPI/
memory service, distinct hardware 30 fps and validated hardware <10 ms remain
separate gates. V125's broader board-qualification roadmap is not closed by a
component timing experiment. No board access or programming is performed here.

Reserve at most two heavy study jobs, each two CPUs, 8 GiB RAM and 8 GiB combined
RAM-plus-swap. Available RAM/full PSI are primary gates, combined use secondary.
Account for observed external jobs before launch; unrelated agents may start
work after a reservation, so retain live pressure/watchdog checks. No swap changes
or interference with unrelated jobs. Preserve qualified Source B100's actual
eighteen selected files and the unrelated marker files' SHA/size/mtime.
