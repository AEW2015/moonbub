# V46 rate-search evidence audit

Audited the V46 search results and component verifier, then checked the generated
24-frame CS38 packet comparison and its independent causal verifier. The evidence
supports a small aggregate complete-frame byte reduction on these first-six
frame prefixes, with unchanged coefficients, references, HUD and quality. It
does not establish frame rate or a general rate advantage.

## Component search

The benchmark searches all three streams in both full and compact AB38 plane
payloads for 24 frames: 144 plane payloads total (72 full/compact pairs). Across
those payloads, the old components total 451,605 bytes and the searched outputs
total 449,785 bytes, a 1,820-byte reduction. The search attempted 2,917 stream
encodes; all candidate streams independently decode to the exact source
coefficients. The AB38 syntax and coefficient profile remain unchanged.

This component total includes both full and compact alternatives, including
representations that lose when forming a complete frame. It is not the actual
selected-stream saving. Search is limited to Rice parameters within ±1 of the
original parameter (with bounded candidate sets), not a global entropy-parameter
optimization. Three focused tests pass. The component verifier reports 144 AB38
packets, all stream candidates decoded, unchanged AB38 wire syntax and no
physical frame-rate proof.

## Complete-frame choices

The subsequent comparison rebuilt 24 actual CS38 complete packets, preserving
the old component as the first choice on byte ties. The independent frame replay
reports 395,448 old complete bytes versus 394,546 bytes after selection: 902
bytes saved, or **0.2280957%** of the old complete-byte total. Per-clip savings
are 278 bytes (10000), 250 (4500), 138 (1600) and 236 (combat).

Across the 72 frame-plane decisions, selection chose the searched full
representation 11 times, compact 30 times, and old fallback 31 times. All 31
fallbacks were size ties with a searched option; the frozen old-first tie rule
retained the old payload. The independent frame verifier recomputes actual
options, selected payload bytes, complete-packet bounds and totals. It confirms
all coefficients, canonical references, HUD words and recorded quality match
CS38. Thus the 1,820-byte component-total reduction must not be substituted for
the measured 902-byte complete-frame reduction.

## Scope limits

The source CS37/CS38 frame encoding was already paid externally. The frame proof
adapter reserializes existing entropy components to check complete packet
choices; it is not an improved native or FPGA receiver. These are 24 short
prefix frames, not a full-history or held-out campaign. No end-to-end sender
clock, hardware mapping, transport admission or physical 30-fps result is shown.
