# From V86 codec proof to a latency-qualified implementation

## Couple actual frontend arrivals to the complete decoder

Keep the compact CS86 profile and all six encodings immutable as controls. The
largest remaining performance question is the complete decoder, not another
isolated map or entropy result. Feed actual new-stream per-context arrivals
into the bounded reference/inverse/coefficient/output, C2 metadata and physical
memory schedule. Include real map parsing, envelope CRC, quantizers, COPY
transfer/alias work, dequantization, HUD semantics and publication fences.

Start with two arithmetic lanes and the eight-credit contract. Preserve per-
context probability order, DC prediction and lookahead, and model stalls at
every consumer. Compare batched fetch/arithmetic against an instruction-level
trace. Extend the model to the all-visible selector choices too; the current
COPY-only timing table cannot be assigned to those different streams.

The LOW/HIGH weights are assumptions, not physical bounds. Calibrate them with
an isolated RTL implementation, cycle traces, synthesis resource reports and
actual achievable clock. Measure interval/probability multiplication and
renormalization feedback before choosing DSP count or a deeper pipeline.

Smaller packets do not erase the prior conditional pixel-memory bottleneck:
the current COPY/residency cold case required 68,904 data/HUD BL8 operations and
about 11.70 ms under the frozen service intervals, before display/refresh.
Model and implement queued/coalesced/pipelined controller service or a separately
qualified traffic-reducing layout. COPY eligibility alone does not certify that
the chosen physical candidate bank already contains the tile.

## Optimize quantizer metadata without changing target pixels

The raw quantizer map still costs 338 bytes per frame. Prototype actual
uniform/RLE/raw choices under a new explicit profile/version. Also derive a
needed-cell mask from the operation map: each 16×16 luma quantizer cell covers
four Y tiles and one U/V tile each. A cell is needed if any of those six tiles
is RESIDUAL. COPY/CONST-only cells can use a defined implicit value because no
coefficient is dequantized there. Every required cell must preserve its exact
original quantizer.

Actually encode/decode these choices and repeat native coefficient/pixel/HUD/C2
checks for the full corpus, including all-visible matched controls. Price the
method and lengths, worst-case packet, parser state and ports. Do not count
semantically irrelevant omitted values as a quality improvement, or assume a
byte saving before measuring complete packets.

## Make the host policy aware of decoder cost

The rate-only selector proves that one profile can safely switch representations
and replay exact chosen bytes. Its 979-byte corpus gain over fixed grouped COPY
is tiny. It may spend extra entropy work on the 31 all-visible choices; that
latency is not qualified by the existing sparse-stream model. Keep fixed COPY
and all-visible controls while developing a joint byte/work/deadline policy.

Charge every candidate's actual host encoding work and buffer needs. An offline
set of pre-encoded components is not a live 30-fps encoder. Develop cheap
selection predictors only after comparing them with full actual encodes, and
validate unseen content. Cache the exact selected packet for retransmission;
re-encoding a stale frame into different bytes is not the defined replay path.

## Qualify streaming admission and hardware recovery

Implement bounded fragmented parsing, timeouts, duplicates/reordering and
explicit abort/drain behavior. Include accepted generation, roots, HUD, tile
certificates and bank leases in atomic publication. A failed provisional write
cannot restore old candidate certificates. Native synchronous rejection tests
do not prove hardware write cancellation or display coherence.

Replay exact selected bytes through finite ESP32 Wi-Fi and QSPI queues with
concurrent GUI/input work and measured stalls/loss. The research receiver's
2-MiB cap is not a board resource budget. Define the negotiated device packet
limit and an explicit sender recovery/quality/skip policy for future oversized
content; all-six fit on this corpus is not a general bound for all gameplay.

Whole-plane streams have the smallest aggregate wire bytes and lower reported
frontend median/max in this corpus.
Chunked streams might still improve first-byte latency during actual ingress.
Model CRC/admission gates and full arrival traces, and report first-byte and
last-byte validated latency separately. Do not hide work by moving the timing
start fence or treating a partial packet as authenticated.

Retain the milestones: 1,800 distinct accepted frames/60 seconds at fixed
30-fps releases, then 18,000 frames/600 seconds on hardware, with exact required
displayed identities/pixels/HUD and zero detected underruns. After that require
the complete defined validated decoder below 10 ms for every qualified source.
The 457-source research corpus and multiple encodings/replays do not substitute
for those distinct-source sustained runs.
