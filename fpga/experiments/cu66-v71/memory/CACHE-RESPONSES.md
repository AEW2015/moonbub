# Optional independent cache-hit response variant

`cu71_memory_system_burst_cache` / `cu71_word_bridge_burst_cache` are separate
modules. They preserve the passing RGB burst variant and have identical ports.
They are not automatically selected by the full-system source manifest.

Previously, even a private canonical/auxiliary cache hit waited until the
global controller FSM became IDLE and consumed a background arbitration grant.
The optional variant completes those held-request cache hits independently
while another client uses SDRAM. Actual controller transactions retain the
same LCD quota/lookahead and three-way background fairness. Cache hits consume
no SDRAM grant and have separate held response slots.

Cache blocks are invalidated at an aliasing write's grant and recovery. An
active write therefore cannot be bypassed by a stale valid cached block.
Different clients' unsynchronized concurrent operations remain unordered:
readers requiring a new write must observe its completion/fence. Concurrent
hits can update both private responses; the aggregate hit count accounts for
both in the same clock. No interfaces, generation rules, PHY clocks or external
timing budgets changed.

Four fast/slow ×original/cross-bank runs (`cache-alias-*01`) each pass5,175
checks and43 abort/drain probes. They retain masks, guards, independent held
responses, complete concurrent readbacks and all8accepted abort positions.
Additional tests prime an old cached RGB block then read during an active
aliasing RGB write, and prime a canonical cache via an accepted read abort
then read while an aliasing auxiliary write is active. Both prove invalidation
and fresh functional readback instead of stale fast responses.

The same four contended reference reads still issue32actual BL8 operations
and96private cache hits. Observed worst tile service changes from1,979 to1,170
modeled clocks with the original map, and2,362 to1,194 with the cross-bank map.
These are small, declared component workloads, not complete decoder timing or
a30fps result. Model, resource, routed timing and whole-system integration gates
remain separate. `verify_cache.py` binds executed evidence to current sources.

The first generator attempt failed a source-pattern assertion before writing
any RTL. Its empty preparation/run directories remain retained; no simulation
failure was relabeled as a pass.
