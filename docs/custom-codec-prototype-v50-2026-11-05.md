# V50 checkpoint: strict whole-frame guard rejects the global-grid proposals

V47 found that a fixed `global_grid` search increased bytes and original-source
error on all four fresh prefixes. V50 evaluates zero and grid proposals from the
same selected incoming reference, then applies a strict complete-packet and
integer RGB565-SSE Pareto guard before publishing any candidate. The guard
preserves all 96 fixed-zero outputs and accepts no grid proposal.

## Same-reference guard results

The selector admits a grid only if its actual complete CS38 packet fits the
49,152-byte cap, is no larger than zero, and has no greater original-source
active RGB565 SSE, with at least one of bytes or SSE strictly better. Ties select
zero. Each proposal receives on a fork; only the selected state may publish.

| Cohort | Selected bytes | Selected active MSE | Grid proposals with fewer bytes | Grid proposals with lower SSE | Grid admitted |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mass Effect 10000 | 368,327 | 17.20233 | 5 | 0 | 0 |
| Mass Effect 4500 | 235,896 | 27.03509 | 3 | 0 | 0 |
| Mass Effect 1600 | 77,365 | 10.49460 | 0 | 1 | 0 |
| Combat | 700,546 | 28.43519 | 15 | 0 | 0 |

Across 96 source frames, 23 grid proposals are smaller, one other proposal has
lower SSE, and the four key-frame proposals tie on both. None jointly improves
both objectives. All 192 proposals fit the final cap and all four 24-frame prefixes
complete. The selected total is 1,382,134 bytes with active MSE 20.79180365 and
2,027,520 exact HUD words. Selected bytes, SSE and histories match the separate
fixed-zero controls exactly. This is a negative result for the tested search and
these four prefixes; it does not show that all motion prediction is ineffective.

## Paid work and limits

The experiment retains four selected and four fixed-zero histories, 192
same-reference proposals, 1,152 full/compact AB38 alternatives, intermediate
CS37 proposals, final CS38 packets and quality records. Candidate analysis,
quantization/RDO, reconstruction and all six AB38 encodes are paid. Shared HUD
generation, source read/conversion and archive writes are outside the clocks.
The paid sender scope covers both candidate construction paths; the separate
policy-with-receive-quality scope also includes fork receives, exact quality
measurements and selection.

Three producer tests and seven independent tests pass. Independent replay
checks 96 selected frames, byte goldens, selected and fixed-zero causal histories,
exact HUD words and the integer SSE gate. A local Pareto decision alone cannot
guarantee future nonregression relative to a separately evolving zero history;
here that issue does not arise in the selected result because no grid proposal
is admitted.

These are Python research results on four previously qualified v40 windows,
not unseen media qualification. They establish no sender latency win, FPGA/ESP32
memory or cycle fit, physical 30 fps, new native-codec frontier or HEVC/AV1
superiority. The next motion change must improve the search objective or
candidate granularity and still pass actual whole-packet and causal checks.

Supporting scope notes: [V48/V49 evidence audit](v48-v49-evidence-audit.md),
[the V47 motion study](../experiments/python-game-motion-v47-study/README.md),
and [the V50 guarded-motion study](../experiments/python-game-guarded-motion-v50-study/README.md).
