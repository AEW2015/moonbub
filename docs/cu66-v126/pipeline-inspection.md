# V126 matched-query baseline

The expanded V126 query completed against the existing V125 routed checkpoint
before any V126 simulation or implementation. This is a read-only observation,
not a new physical trial or positive repeat. The checkpoint hash is unchanged.

The [baseline receipt](../../experiments/python-gamebub-v126/pipeline-inspection/baseline-v125-20261110T131624745862Z/receipt.json)
has SHA256 `8cbf3cef787b17f7cd56f9bdc0e865c4b790fc517a1565a951efab4d5d051ae9`
and binds 128 retained artifacts. It pins the final V125 native receipt
`67ac131ffd3aff5365217d5a2f2b362dd4373e5abd5174a0ba8240e5dfada115`.

| Selected family | V125 worst slack |
| --- | ---: |
| Producer tile cursor → all timed endpoints | −1.224 ns |
| Producer tile cursor → current cell cache D/CE | −1.224 ns |
| Scratch emit bank → all timed endpoints | −1.219 ns |
| Admission tile → all timed endpoints | −0.464 ns |

The query retains the prior owner, RAW, rank, queue and admission families.
Producer cursor/cache/plane/state and both proposed new registers have explicit
declared-width inventories, D/CE targets and Q-source all-endpoint families.
New registers do not exist in this V125 checkpoint: their absent selections are
recorded as gaps, not zero-delay or positive-slack results. Mapped replica counts
and renamed/absent bits are not evidence of a changed arithmetic domain.

After a fully qualified V126 functional candidate receives its fresh route,
run the same frozen query and compare its hash-bound reports. Check incoming
and outgoing paths for both new registers, not just the old cache endpoint.
The global timing, hold/pulse, internal coverage and routing gates remain
separate from every subset query.
