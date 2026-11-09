# V119 scratch focused results

The selected focused suite passed both generic seeds and both actual-caller seeds, with strict `--assert -Wall` Verilator and C++ `-Wall -Wextra -Werror`. Source/artifact/compiled-source hashes and reversible edits were independently checked in [the audit](../../experiments/python-gamebub-v119/audit/scratch-expert.json).

Per generic seed, the complete inherited suite retains1,048,576 signed16-bit coefficient/all8phase/raw-format cases,15 response/reset/cancel priority cases,10,496 selected AC acquisition cases and192 wrong-owner physical drains. The new matrix adds489,216 full32 count/written/previous-frontier checks:14,908 good and474,308 bad, with all8 phase encodings. An independent mode/order/count partition reproduces those totals.

The complete local output plan passes360 exact17-bit terminal/16-bit next-block endpoint cases per seed, including28 exact terminals and36 wrapped next-block cases. Each seed takes86 real prefetch requests on the public ready/valid interface and retires86 matching responses before reusing its fixture. The fixture does not deposit plan payload or physical outstanding ownership. One real stable-context predecessor edge matures the plan. New prepared endpoint contexts are not presented as natural gameplay transactions.

The actual-caller suite passes40 case rows and56 directed checks per seed, retaining every common output, memory-service event, raw view, counter and clock comparison. Public/error cycle deltas and skipped-edge counts are zero. The original old source/checkers are preserved; the inherited acquisition main is only renamed and invoked by the additional benchmark.

The first compile attempt stopped before RTL execution on two new next-block width-expansion warnings. The preserved repair makes the add explicitly32-bit before16-bit truncation, matching the original arithmetic. No warning or assertion was suppressed; the fresh full campaign then passed.

The timing improvement remains a hypothesis until routed measurement. The V118 critical source is ingress raw_mode selecting upstream coefficient block/index before scratch validation. Parallel local format decisions remove Scratch.raw_mode from late wide comparison selection, but do not by themselves remove that upstream mux. Root must judge the actual routed family. Full integrated source/canonical/transport/parent proofs are separate Root gates, and no hardware30fps, under10ms or clock claim follows from this focused suite.
