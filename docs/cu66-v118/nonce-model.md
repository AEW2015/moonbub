# V118 nonce arithmetic prototype

The Python-only prototype passed1,036,720 primary matrix cases for a future V119 arithmetic change. Production RTL remains unchanged. The model targets the actual32-bit `child_nonce` in `cs88_coefficients_v91k.sv`; the original expression extends that nonce to64 bits before adding three Boolean nonzero-plane terms. This is not a64-bit nonce design.

Let `needed` be the count of nonzero planes,0–3. The proposed overflow test is:

```text
child_nonce[31:2] == allones && (zero_extend(child_nonce[1:0]) + needed) >3
```

The low-part addition needs three bits. For an unsigned32-bit nonce `x=4h+l`, with low part `l` in0–3, any upper part below its maximum gives `x≤2^32−5`, so adding at most3 cannot overflow. At the maximum upper part, `x=2^32−4+l`, and overflow occurs exactly when `l+needed>3`. The original widened sum is at most`2^32+2`, so its64-bit arithmetic cannot itself wrap. This establishes arithmetic predicate equivalence under the stated input domain; it does not establish a particular RTL mapping or physical clock.

| Executed matrix | Cases |
| --- | ---: |
| Exhaustive reduced widths2–16, every nonce and count0–3 |524272|
| Two seeded full32-bit runs,250000 each, with endpoint bias |500000|
| All plane masks, entropy combinations, four full-width nonzero block values and six nonce boundaries |12288|
| Five representative upper classes × all low bits/counts |80|
| Twenty full32-bit endpoints × count0–3 |80|
| **Primary matrix total** |**1036720**|

These cases overlap; this is not a claim to enumerate1,036,720 unique full32-bit inputs. Sixteen additional recorded boundary witnesses recheck the final four nonce values against each count. The random seeds118661 and118662 observed2956 and2945 overflowing cases respectively, aided by the explicit endpoint bias. Random testing alone would rarely encounter the narrow overflow region.

The entropy matrix preserves the actual source's first-error order: unsupported entropy on a nonzero plane returns64 before nonce overflow can return66. It produced9288 entropy rejects,300 nonce rejects and2700 accepts. In2772 cases both conditions were bad and error64 won. Zero-plane entropy values were correctly ignored in2808 cases where only those entropy fields were invalid. An independent combinatorial audit reproduced these matrix totals without rerunning the campaign.

Root ran the pinned tool image with two CPUs,8GiB memory, no additional swap, no network, a read-only repository and only the model output writable. The receipt records actual Python execution and explicitly records no RTL execution. The source branch and script hashes match the selected artifact.

The observed routed plane-block-to-producer-cache path has not been proven to map to this nonce branch's arithmetic. This prototype therefore supplies an exact future arithmetic candidate, not a measured timing improvement. It does not test owned receipt staging, nonce/anti-replay lifetime across reset, monotonic child allocation, physical debt drain, hardware30fps or validated under10ms decoding. Those requirements remain part of the coordinated V119 RTL/full-component/LIVE/native qualification in `admission-owner-next.md`.

Model: `scripts/cu66-v118/nonce_model.py`. Receipt: `experiments/python-gamebub-v118/nonce-model/attempts/20261109T160013004001Z/receipt.json`. Independent21-check audit: `experiments/python-gamebub-v118/audit/nonce-model-terminal.json`. Root dispatch metadata: `experiments/python-gamebub-v118/orchestration/nonce-dispatch.json`.
