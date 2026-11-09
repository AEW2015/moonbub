# V119: owned validation and local payload control

V119 implements and verifies four coordinated RTL changes: parallel full-width scratch validation with an owned output plan, exact bounded producer arithmetic, reuse of the admission parser’s owned mode extent, and a phase-local reconstruction payload writer. Every tested public output, event, owner and cycle remains exactly V118.

The measured goal remains a timing-qualified 125 MHz component followed by complete-system qualification of sustained 30 fps and decoding under 10 ms. The [native results](native-results.md) record two passing 100 MHz implementations and a failed 125 MHz target. The [handoff](handoff.md) exports the measured V119 development candidate; V118 remains the stable control because V119 regresses timing margins. A positive out-of-context clock does not qualify the complete parent, memory controller, ESP32 transport or board.

- [Plan](plan.md) and [reproduction commands](reproduce.md)
- [Scratch qualification](scratch-results.md) and [owner changes](owner.md)
- [Full-component and actual transport evidence](functional-results.md)
- [Guarded parent evidence and cycle limits](parent-results.md)
- [Native timing](native-results.md), [checkpoint equations](checkpoint-diagnostic-results.md), [standalone RTL range probe](range-probe.md), and [next causal experiments](ingress-control-next.md)
- Machine-readable campaign: `experiments/python-gamebub-v119/results.json`

Source A and all consumed proofs are frozen. Prior versions remain immutable; failed attempts retain their original logs and snapshots. No board programming or hardware test occurred in this campaign.

The complete component/transport and guarded-parent tests preserve V118 outputs, owners, accepted events and cycles. The fast/stalled row fixtures remain 1,145,104/1,553,197 cycles; neither is under 10 ms at 100 MHz. Hardware 30 fps and under-10-ms decoding remain unvalidated.
