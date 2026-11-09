# V118 per-band scratch head decisions

Candidate preserves V117 payload ownership and schedule. Three spatial lanes compare each band's full32-bit cursor/count and head geometry before the 2-bit band selects a compact fetch/apply decision. Predicates are registered, with complete poststate forwarding on the two actual head transitions: valid AC_EXTRACT installs a head; AC_CHECK consumes a matching head. Stable contexts refresh during fetch/read/DC control edges. No new queue, transaction, memory request, or public edge is introduced.

Every eligible AC_CHECK asserts equality with the frozen full expressions, and all inherited assertions remain. Whole packet and actual-caller suites compare every original public/raw field on every original clock. Explicitly deposited private fixtures initialize the new redundant predicates once from their declared whole poststate; natural transactions never call those initializers. No per-eval refresh or skipped clock hides transition errors.

This is a source architecture hypothesis. Actual fixed-method routed reports must decide whether read_band fanout, selection and carry paths improve. No timing qualification or achieved clock is implied by this source change. Replay extents are unchanged in this candidate.

The first strict compile stopped before executing RTL because a new certificate redundantly tested `read_band<=3` on a 2-bit field (`CMPCONST`). The failed snapshot is retained; the repair removes only that tautological upper bound. The meaningful nonzero-band owner check, complete predicate certificates, all old assertions, and fatal-warning policy remain.
