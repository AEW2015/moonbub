# Cadence sensitivity summary

**Analytical sensitivity estimate only; not an 1,800-frame RTL run or hardware proof.**

Paired cases: 1620; captures modeled per case: 1800; capture window: 60 s; phase steps: 20; ppm set: [-1000, -500, -100, -10, 0, 10, 100, 500, 1000].

| Modeled timing | First-to-last rate (fps) | Max age (ms) | Captures / 60 s | Presents / 60 s | Gaps / 60 s |
|---|---:|---:|---:|---:|---:|
| Nominal ~65 Hz | 29.9647–30.0383 | 36.940–40.513 | 1799–1800 | 1798–1800 | 296–312 |
| Hypothetical ~60 Hz | 29.9676–30.0292 | 29.801–166.965 | 1799–1800 | 1797–1800 | 0–7 |

Each paired case applies the same display/source ppm offsets and phase fraction to both traces. Gap count and duration range report intervals greater than 1.1 modeled source periods; gaps do not prove frame loss. Capture count is source arrivals in the half-open 60-second window. Arrivals wait for prior presentations with no backlog limit or drop policy, so long age results depend on this unbounded scheduling assumption. Service traces repeat ten measured frames and ignore variable contention.
