# Routed critical-path priorities after V129

The retained 125 MHz component reports show multiple failing path groups. The
[reproducible report analysis](../../experiments/python-gamebub-v130/route-families.json)
reads the actual source-bound V128 and V129 route reports, checks their receipt
hashes and matches the worst path to each timing summary. It groups only the
**50 paths printed in each report** using descriptive endpoint-name buckets;
the counts are not totals across the whole design and cannot establish why
paths changed between joint RTL edits.

| Path family in reported top 50 | V128 count / worst | V129 count / worst |
| --- | ---: | ---: |
| Kill control → admission RAM | 4 / −1.273 ns | 2 / −1.257 ns |
| Scratch request epoch → successor tile | 0 / not reported | 20 / −1.076 ns |
| Other → scratch | 29 / −1.306 ns | 23 / −0.984 ns |
| Parser → parser | 13 / −1.320 ns | 0 / not reported |
| Other → successor tile | 4 / −1.161 ns | 0 / not reported |
| Other paths | 0 / not reported | 5 / −1.000 ns |

The worst V129 admission path consists of 1.882 ns logic and 6.848 ns routed
net delay across 11 logic levels. It remains a real single-clock setup path;
the evidence does not justify a timing exception or invented board I/O delays.
The [admission read-enable proposal](../cu66-v129/route-next.md) separates
physical speculative reads from logical acceptance, with extra care for invalid
data, address bounds, cancellation and write/ACK ownership. It requires actual
RTL checks and another route before any timing claim. Even eliminating that
worst family leaves the reported successor path failing by 1.076 ns.

The endpoint counts and minima change with placement and source edits. An
absent family may be below the report's top-50 cutoff; it is not evidence that
the family has closed. Both results are out-of-context component measurements,
not board timing or sustained hardware performance. The full V129 check found
1,101 inputs and 12,887 outputs without I/O delay constraints; actual board and
interface data are needed before constraining those paths.
