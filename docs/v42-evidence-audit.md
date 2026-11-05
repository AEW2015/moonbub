# V42 evidence audit

Audited the frozen `python-game-hud-fast-v42-study` README, results, test logs,
independent verify log and whole-chain profile. The reported paired arithmetic
and retained replay counts agree with those artifacts.

## Paired stage and exactness

The results contain 24 inputs, six from each of four qualified clips. Each input
has three paired timings with alternating order. The per-clip means of paired
medians are 187.722238→46.712712 ms (10000), 135.584970→22.446594 ms (4500),
19.493715→6.542234 ms (1600), and 207.610876→61.704564 ms (combat). Their
aggregate means are 137.602950→34.351526 ms, a 4.006× component speedup. HU25
generation, motion search, and source patch selection are excluded from that
paired stage; the result cannot be presented as whole-chain service or 30-fps
capacity.

The producer and independent logs each pass six tests. Independent verification
reports 24 inputs, 24 exact HX32 outputs, 24 exact HX33 outputs, 506,880 HUD
words, 568 recipe plans, 2,556 channel/scheme plans, four accepted-reference
chains and 1,295 source pins. The results also preserve the three paired
repetitions and their order. No evidence here indicates a compression gain.

## Whole-chain profile limit

The separate 24-frame cProfile diagnostic includes source selection and HU25
motion generation in addition to fast HX32/HX33; it matches the qualified
packets. Its README reports 3.163314 s instrumented total. However, the profile
JSON's top `generate` cumulative value is 3.172660 s, about 9.35 ms greater than
that total. `whole_chain_profile.py` assembles rows from `pstats.Stats.stats`
keyed by filename, line and function name, which can overwrite distinct code
aliases as observed and fixed in the V41 profiler. This makes the summary
internally inconsistent; treat total and per-function rankings as qualitative
only. The V42 study is frozen, so this audit does not regenerate its profile.

The paired speedup is independent of that cProfile run. The exact HUD work is
shared by native and custom hybrid paths. Neither the paired stage nor profile
establishes physical throughput, compression advantage, or hardware fit.
