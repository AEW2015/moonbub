# V115 refined ingress: prepare exact header length validation

This candidate targets the measured header sum/control path from staged length
bytes into HEADER decisions. It derives only from the frozen initial V115
ingress. The initial parser, context, production composition and earlier proofs
remain unchanged. The selected fresh focused RTL run **passes**; this is functional/cycle
evidence, with native timing still unqualified.

The old expression adds four zero-extended unsigned 32-bit lengths at 34-bit
width and compares that sum with zero-extended `size_bytes` minus 46 at the same
34-bit width. The new pipeline preserves that expression, including carry bits
and subtraction wrap. No guessed packet-size bound, truncation or saturation is
introduced. Two 32-bit terms need 33 bits; both pair sums fit exactly in the
34-bit total, whose maximum is `4 × (2^32 − 1) = 2^34 − 4`.

| Edge | Owned preparation |
| --- | --- |
| E0, header WAIT29 | Capture lengths 0/1/2 from already stored bytes and length 3 with its current high byte forwarded from `ram_data`; capture the same packet size. |
| E1 | Register two exact 33-bit pair sums and the exact 34-bit expected payload size. |
| E2 | Register the 34-bit total and delayed expected size. |
| E3 | Commit one mismatch predicate and mark it live for this header owner. |

The capture guard is exactly the existing `prefix_header_capture` plus index29:
no canceled, failed-context, completed-context, wrong-address or wrong-epoch
response can arm the validity pipeline. Its valid bits and live flag clear on
the existing cancellation/failure/done guard. Payload registers have no reset.
Only a valid E3 result updates the owned predicate, so subsequent unrelated RAM
data cannot replace it. The unstalled request/wait schedule leaves 30 further
edges between this commit and HEADER consumption; it adds no public FSM edge.

HEADER retains the same CRC and structural-error priority. Its old inline sum
condition becomes the registered predicate. Added assertions check the full
34-bit sum/RHS at E3 and compare the predicate with the **literal old expression**
when HEADER consumes it. Every original assertion block remains byte-identical
inside the derived body.

The prepared focused runner rebuilds the unchanged initial parser suite and a
new original-versus-refined ingress pair with `--assert -Wall`, strict owned C++
warnings and no waiver. The pair asserts equality of every original public
output on every edge, including invalid payload and counters. It preserves the
complete old 160-profile dense/owner corpus, four malformed cases, 54 original
cancel/retry checks, and its original coverage gate. It then adds:

- Thirty cancellation/retry checks spanning WAIT29 request/response, each
  validity position and the committed predicate; each retry uses no extra reset.
- Ten real packet length cases covering pair and total carry bits, full-word
  overflow, low-32-bit aliasing, descriptor bounds and the forwarded high byte.
- A combined bad-CRC/bad-length case that must retain CRC as the first cause.

The parser rerun retains its original 1,520 historical cases across eight
configurations, 104 directed checks, 6,096 parameter cases and prepared-state
checks. Its actual production source hash is unchanged. Seeds are 115801/115802
for parser and 115901/115902 for ingress. Any failed compilation/assertion is
retained as a failed attempt, never synthetic PASS. CPU, RAM, swap, pressure and
watchdog limits match the controlled two-CPU/8-GiB workflow. Root reviews the
prepared sources and grants a heavy slot before execution.

```sh
python3 scripts/cu66-v115/refined-ingress/prepare.py
python3 scripts/cu66-v115/refined-ingress/qualify.py
# Only after the exact prepared source receives Root's heavy-slot grant:
python3 scripts/cu66-v115/refined-ingress/qualify.py --run
```

The source cut is an RTL timing candidate. A passing focused run would establish
bounded functional/cycle evidence; only fresh full-composition simulation and
native 100/125-MHz routes can establish its integration behavior and timing.


## Selected focused result

Attempt `20261109T020712236590Z` passes both fresh parser seeds and both ingress
seeds. Each ingress run retains the initial 160 profiles, 54 cancel/retries and
218 successful packets, then completes the additive tests: 259 successful
packets, 84 total cancellations, 11 new length/CRC cases and 2,575,650 exact
coefficients. Its 2,256,431 requests equal 2,256,398 responses plus 33 canceled
private read owners. The direct original/refined public pair checks every edge:
29,634,196 for seed115901 and 29,630,233 for seed115902. The unchanged parser
passes its complete original corpus and prepared-state checks again.

The selector SHA-256 is
`816765f1c20a79787ea639098024694b5a1e6402a720e7cb6fbf637e87d76f5d`;
raw receipt SHA-256 is
`09a8b9ae41d7121e659acaac90b03516091981dce00356536fb38a7f379a7b2f`.
A source self-review independently rehashes all 25 current/snapshot bindings and
34 artifacts; it is disclosed as an author's review. The earlier attempt
`20261109T020409363604Z` remains FAIL: unchanged parser runs passed, but the
reference ingress filename differed from its module name and strict compilation
stopped. The corrected source filename matches the module; no waiver was used.
The production timing candidate remains SHA
`93b965d5d02d89e9f8b88b64340af7bd8f7c08568694e1dc0aaeb41c19bfcaf2`.
