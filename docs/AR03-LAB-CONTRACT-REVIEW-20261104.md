# AR03 contract bundle for joint Windows/receiver review

Date: 2026-11-04, America/Denver. Status: versioned **offline laboratory** bundle;
not an agreed/deployed live transport. Existing MSV1 and AV v1 remain unchanged.

Source kit: MoonBub `27a4dde6a7e2ea4fab09d892551ef542f05c8965`.
Coordinated Windows plan: Sunshine
`c9c0bf4bcbe5c95f38b50bf6e190b84822886d53`.
The Windows plan identifies encoder baseline
`19cdd7080e7ee181b9bd7a73f4ba5ac5400a36fc` separately.

## Shareable inputs

- `host/ar03-contract-20261104/`: byte-exact wire/development JSON, regenerated C
  offsets, all1,725 retained serialized FG19 history messages with hashes, and
  eight negative wire vectors. The builder checks source Git blobs, not HEAD
  alone. `plan-source/` contains the exact pinned Windows prompt and plan.
- `host/experiments/ar03-state-transcripts-20261104/generated/`: ten receiver
  scenarios /51 state steps, with explicit supplied model-drain events and
  expected reply bytes from the pinned Python implementation. This supplements
  the histories; it is not a full expected-state replay of all1,725 messages.
- `host/experiments/ar03-gateway-contract-20261104/`: native parser/serializer and
  older C lab ledger used for differential testing. The reply difference below
  must not be silently normalized away.

The bundle's `bundle-manifest.json`, history index and transcript result carry
normative file/message hashes. Model step numbers are ordering indices; original
study history times are model milliseconds, not packet capture timestamps.

## Existing bytes and integrity rules

| Family | Existing laboratory schema | Integrity and meaning |
| --- | --- | --- |
| AR03 | version3, little-endian,61-byte fixed header, variable inner/patch data, final4-byte CRC;49,152-byte complete cap | CRC over preceding body, stored LE; this is not a contiguous65-byte header |
| GF03 | version3,31-byte BE fragment header, prefixed by16-byte TOKEN;1,008 payload maximum | Complete CRC covers the entire AR03 packet including its trailer; body CRC excludes that trailer |
| TOKEN | epoch32, slot16, reserved16, packet sequence64; BE | PC18 binds CRC of TOKEN+GF03 header (47 bytes), not fragment payload |
| FG19 | version1,32 BE field bytes plus4 CRC bytes | Exact epoch/frame/nonce/length/body identity; CRC stored BE |
| PC18 / QC18 | magic identifies family;29 /28 complete bytes, BE | CRC over preceding message bytes; consumed/rejected returns packet permit; unknown does not |
| AF03 | version3,39 LE field bytes plus4 CRC bytes | Only validated ACK and exact stored bank/frame/tag confirm a reference; ordinary no-store acknowledgement is not a new bank publication |

None of GF03, FG19 or AR03 includes a host capture timestamp in the frozen layout.
Do not append one implicitly. Correlate frame IDs with host capture logs and
receiver local microsecond traces. Source-to-display latency needs an optical or
synchronized-clock method. AV v1 has its own timestamp field and does not extend
the custom video header.

Frozen profile geometry is720×480 coded /720×405 active, with the pinned integer
placement and mandatory HUD/map policy in `development-profile.json`. Preserve
profile and predictor-bank preconditions when replaying P frames. IT20 remains
an offline reconstruction fixture, not runtime transport.

## Ownership semantics and discovered differences

Keep packet-buffer permit, request completion, frame-slot release and reference
publication separate. FINISHED returns only control capacity. RELEASE follows
actual ingress/read/decode drain. AF03 never substitutes for packet-buffer release
or physical presentation. Unknown outcomes retain bounded ownership.

1. **Changed-slot duplicate REQUEST:** frozen Python returns the original owned
   slot's GRANT when epoch/frame/nonce/length/body identity matches, even if the
   duplicate names another slot. The older C helper returns BUSY. All compared
   owner states remain held, but the reply bytes differ. The dormant Rust frame
   core follows the frozen Python oracle and passes the10/51 shared state replay.
   This does not authorize a new grant or release for the incorrectly named slot.
2. **No acknowledgement of FINISHED receipt exists.** Enqueue FINISHED before a
   later RELEASE; do not invent an ACK-of-ACK. Loss must lead to the agreed query /
   retained-state/safe-stop behavior, not fabricated capacity.
3. **GF03 does not carry FG19 nonce.** The receiver can bind its current local
   grant to a backend lease, but cannot authenticate an unseen delayed datagram's
   old grant if epoch/frame/body/length is reused. The dormant core includes a
   counterexample test showing this limitation. Local nonce bookkeeping alone
   is not a cross-session replay proof.

Before a live implementation, jointly define frame-ID lifetime: once DATA could
have been sent/owned, that identity must not be reused within the generation.
Candidate-ID reuse is a different case only while DATA cannot have entered the
transport. Decide whether enforcement is strict frame-ID monotonicity or another
explicit generation policy. These are blocking production decisions, not silently
added laboratory grammar or a new wire field.

## Decisions requiring Windows/receiver agreement

| Decision | Current status |
| --- | --- |
| Live capability exchange and profile version | No packet exchange implemented or advertised |
| Custom UDP port and peer/session binding | Unassigned;5533 remains MSV1,5534 remains AV v1 |
| Epoch generation across either peer reboot | Lab fixed epoch1 only; production uniqueness/reset/rekey open |
| Frame-ID reuse after DATA / aborted or ambiguous transactions | Blocking decision described above |
| Counter exhaustion and reconnect | No wrap/rekey shortcut; retain unknown owners until defined recovery |
| Quiesce/drain/reset proof and reference invalidation | Required before a new generation; no automatic success from timeout |
| Missing/late FINISHED, RELEASE, PC18 or AF03 | Shared fault cases and exact recovery still need complete peer replay |
| Concurrent complete decoder/FIFO/backend | Not implemented by a metadata trait or a component timing result |

Proposed lifecycle remains DISABLED→NEGOTIATING→ACTIVE→QUIESCING→DRAINED, followed
by a fresh agreed generation and key/reference initialization. No new handshake
magic/fields/ports are allocated by this note. CRC and peer pinning are not
authentication.

## Evidence limits and next shared tests

The shared receiver-state harness uses explicit **model** drain and immediate
reverse-worker completion. It compares identities, FINISH state, observed indexes,
request/release watermarks and safe stop. It does not prove physical DMA/read
drain, sender publication, packet FIFO service, omitted internal flags, production
rekey or whole-network recovery. Its partial-ingress drain case is not a successful
complete decode. The new Rust gateway has separate packet/backend fault tests.

Windows can now replay the frozen bytes and receiver-state oracle, including the
documented C difference. Next joint deliverables are complete packet/control /
AF03/reference state transcripts, fault/restart vectors, agreed generation rules,
and matched source pins. Tag mismatch and publication/recovery negatives remain
separate from the eight basic wire-grammar negatives.

Current full custom FPGA-only and concurrent physical presentation throughput is
unknown: parser/banks/tagging/patch/scanout integration and a real receiver backend
are still required. No uncoordinated hardware stream or firmware load is requested.
