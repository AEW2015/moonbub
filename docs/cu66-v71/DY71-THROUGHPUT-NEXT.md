# DY71: next throughput measurement

**Update:** the unchanged profiling replay has completed. [Measured results](DY71-PROFILE-RESULTS.md) identify completed-IDCT reference blocking as the dominant P2 bin; the unattributed analysis below is the preserved pre-replay baseline.

The latest complete SYNCsafe/math/grouped KEY/P/P simulation is clean, but **P2 takes45.52368ms** and its presentation interval is46.10029ms. The largest measured nonoverlapping region is **BASE_RUN:41.62844ms (91.44% of P2)**. Existing logs do **not** identify whether entropy, IDCT, hashing, reference reads, HUD completion or memory drain dominates inside that region.

## Measured timing

Source: `fpga/experiments/cu66-v71/direct-system/syncsafe-math-v002/evidence/new-fence-three01`, chronological cohort0 IDs0/1/2. One memory cycle is10ns. These are receiver stage-transition durations, not host wall time.

| Region, ms | KEY | P1 | P2 |
|---|---:|---:|---:|
| METADATA |0.49521|0.37751|0.27421|
| BASE_RUN, combined gate |18.86613|30.34583|41.62844|
| CACHE_PREPARE_RUN |1.13095|3.66074|3.62094|
| COMMIT_ACK |0.00002|0.00068|0.00002|
| Total transaction |20.49238|34.38483|45.52368|

Unlisted ownership transitions total7clocks per frame. Cache-worker counters differ from enclosing stage duration by one observation clock. P1 intentionally drops one processor ACK and retries; P2 ACK is only2clocks. WAIT_BANK and WAIT_CACHE each take one clock here.

BASE_RUN exits only when canonical completion **and** HUD semantic success,21120write/readback completion, and memory drain are satisfied. HUD starts concurrently with BASE. Native C++ HUD computation takes no HDL time; this is not ESP32/FreeRTOS/QSPI timing. Individual entropy/IDCT/hash active/stall counters are not logged; their outputs are disconnected in this binding. A short final hash tail would not exclude earlier row/hash backpressure.

P2 reserved controller idle is **8.01729ms**, the cumulative-counter difference1251024?449295, not12.51024ms. LCD-class reservation contributes6.73261ms; BG-class1.28468ms. These are real idle slots with eligible physical work held by reservation, but overlap BASE/PREPARE and are not additive stage time or guaranteed recoverable latency. Existing timer-expiry counters can increment while the controller is busy; they do not count actual idle-hold expirations.

## Traffic, not internal latency attribution

| Per transaction | KEY | P1 | P2 |
|---|---:|---:|---:|
| LCD physical commands, counter delta |3600|54240|99360|
| BG physical commands, delta |56160|87384|87384|
| Actual READ BL8 commands |6240|88104|133224|
| Actual write beats |428160|428160|428160|

Each frame writes259200canonical words plus21120HUD words. Scalar HUD writes consume168960physical beats (eight per word), explaining all428160write beats:39.46% of physical write traffic, **not** measured latency. HUD readback adds2640READ BL8 commands. Each P adds31224reference READ BL8 commands =7806referenced64-byte tiles;294tiles need no reference. P1/P2 BG counts are identical, while P2 serves45120more LCD commands. Longer execution and repeated scanout amplify each other; the log does not identify which initiated the difference.

Presentation cycles are3073370,6146723,10756752: intervals30.73353ms and46.10029ms. P2 acceptance ends at10040197; presentation follows7.16555ms later. ACK is not display. P1 starts before the first image is presented, so its initial LCD exposure is not steady state. Three frames/two intervals do not qualify sustained30fps. The33.333ms target still needs about12.19035ms less P2 transaction time plus sustained clean presentation/coexistence evidence.

## Smallest next experiment

Replay the **same complete KEY/P/P fixture**, unchanged DUT, clocks, PHY, map,8:4grouping/grace/quota, generator and HUD service. Add simulation-wrapper observations only:

1. Log existing receiver `base_at`/`hud_at` timestamps (diagnostic070/074 and078/07c) plus `b_cycles`/`b_tiles` (03c/040) per generation, without adding simulated service cycles. This distinguishes canonical completion from HUD/drain tail inside BASE_RUN.
2. Add mutually exclusive BASE frame/tile-state bins: entropy/scatter wait, quantizer/dequant wait, IDCT computing, completed-IDCT blocked for reference, reconstruction, write fork, final hash wait. Split write-fork waits into memory-only, row/hash-only and both. Record reference request?response and actual write?drain as overlapping latency, not additive critical-path time.
3. Attribute reserved-idle deltas to these bins and BASE/PREPARE; retain LCD page deadlines and physical-command counts. One summary per frame and bounded first-event detail suffice.

Choose the next change from the largest **measured blocking bin**. Until then preserve PHY/map/quota; more IDCT lanes, less reservation, burst HUD or deeper caches are not yet selected. This analysis changed no sources/manifests and launched no simulation/build/hardware run.

## Exact bindings

The source-freeze file supplies every RTL/header/fixture/helper binding. Its result excludes live ESP32/QSPI/CSR/network timing and hardware/routed qualification.

| Evidence/source | SHA-256 |
|---|---|
| `new-fence-three01/frames.log` | `a4649570bad8cadc3d358bbf6a1d1d1d2d781447c183282532eb1d8f2c94adc4` |
| `new-fence-three01/source-freeze.json` | `542a612074618feb3e3d2463f4688e6318281f11e3d8ff1f2876f13575d51ad3` |
| `new-fence-three01/tb.cpp` | `188c7351107fabe4bdb64b3c2345fdf888455be4d94d46369126598ed70c0c0e` |
| `new-fence-three01/cu71_direct_system_sim.sv` | `eaf1d2690146939d4fe330c8d071f1a718703a584308f900761fd9b742480d2b` |
| `cu71_system_direct_syncsafe.sv` | `f49ad95f3b5cfe2b954e94cfaf44b924515329c79fab44f32328d04bdb1377af` |
| `cu71_receiver_direct_math.sv` | `7991bfc59ddf2942080185196b103e9af0b72b94857460f5570b92d035bd71d3` |
| `cu71_base_pipeline_math.sv` | `9befe8fe345a22c9c7d6f08ad8937a7e6cd3c1d07c9bef13ede29709f2391fc3` |
| `cu71_ab38_decoder_arithpipe_v4.sv` | `93b79e7d074aa606b4461d7fcd73069e323739012d66963fa1a0d5fa6633763b` |
| `cu71_idct_indexed.sv` | `fe1d7f3684ac7e8c15bc80e5a9b4734863103510faa2087d75b00a6b94d2d41d` |
| `cu71_sha256_bytes_lookahead.sv` | `f29332de9fe41ba679bef91fba71698e4efb4a05860221ab0ea3268e19c28006` |
| `cu71_word_bridge_direct.sv` | `8c73e1f3bac525e51db7777416c6a291a7e061c8e9e2ed0d23a532c9097c7a9a` |
| `cu71_direct_scanout_syncsafe.sv` | `1db37889aee6149724f0987a5b12270195879b8bae285e7eb181736a54f77fae` |
