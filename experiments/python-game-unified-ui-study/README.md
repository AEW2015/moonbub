# Exact UI plugin for the unified codec

`ui_plugin.py` provides bounded HP01/HR01 display-patch selection, framing,
validation and application for the new AR02 core. It does not know or mutate
prediction/reference state. The primary coded canvas remains **720×480**, with
720×405 active content in native-source fixtures. `unified_ui.py` is a small
compatibility import; the primary implementation is `ui_plugin.py`.

The core owns its complete header, base body, reference tags, outer CRC and AF02
feedback. It passes the **remaining patch-section byte budget** after those base
costs. This plugin counts each actual four-byte length prefix plus encoded patch,
attempts at most four configured disjoint rectangles in priority order, and
retains all losing/late work. No patch can exceed its supplied budget. A budget
below the minimum header/CRC/prefix skips provably impossible work; it does not
predict a compression ratio.

## API and publication contract

```python
selector = ui_plugin.PatchSelector(rectangles=ui_plugin.COMPACT, max_entries=4)
selected = selector.select(rgb, byte_budget)
section = ui_plugin.pack_patches(selected.patches)
validated = ui_plugin.parse_patches(section, len(selected.patches), width, height)
display_rgb = ui_plugin.apply_patches(base_rgb, validated)
```

`Selection.patches` is a tuple of immutable patch bytes. `used_bytes` includes
length prefixes; `service_ms`, `selected_pixels` and `requested_pixels` describe
the completed call. `details` is JSON-safe and contains per-attempt geometry,
actual lengths, cap decisions, current/historical candidate work, encode/validate
cost and cache state. `select` also accepts `max_attempts`, an observed
`work_budget_ms` and `spent_before_ms`. If that work budget expires after work,
all selected patches fall back to none while paid attempt costs remain recorded.

`pack_patches` frames trusted immutable encoder outputs. Receiver validation must
use `parse_patches` or `validate_patches`; packing alone is not a validity check.
The parser permits zero to four exact prefixes with no trailing padding. It
checks **every header, complete length, CRC, geometry and overlap before invoking
any patch decoder that allocates pixel words**. It then fully decodes every
HP01/HR01 payload. A corrupt later patch prevents the caller from receiving a
partially validated result. The AR02 core must complete this validation before
publishing any base reference or feedback.

Validated words are read-only. `apply_patches` never changes its base RGB input.
With no patches it returns an RGB888 copy preserving all base samples. With any
patches it follows the earlier display contract: quantize the base to RGB565,
overlay selected exact words, and return RGB565-expanded RGB. Thus selected words
equal the original source's RGB565 values; unselected **words** equal base RGB565,
not necessarily all original RGB888 low bits. YUV reference tags must be derived
from the base reconstruction, never this display overlay.

## Exact source-region cache

The existing four-entry payload cache is reused. Each key includes canvas,
rectangle and patch policy; every hit compares current exact RGB565 rectangle
words before reusing immutable bytes. This permits a hit despite changed game
background or RGB888 changes discarded by RGB565. Hits do zero new patch-encoding
candidates, keep prior candidate details explicitly historical, and still pay
current conversion/comparison and full validation. Misses pay all actual HP01/HR01
candidates, current-word storage and any evictions.

The cache only retains source-region words and encoded payloads. Persistent byte
counts exclude Python metadata, old/new transient overlap, decoded patch words,
source/base/output arrays and other codec workspaces. A four-entry bound is not a
claim of physical BRAM/SDRAM fit or measured peak memory. The largest observed
persistent cache in this run is 84,592 bytes, including a valid candidate whose
fourth patch is rejected by the section budget. Section admission is not a cache-
memory limit.

## Retained standalone results

The paired benchmark uses the same plugin with zero cached entries versus four
entries, at a declared **32,768-byte UI-section budget**. It alternates call order
per source ID and case. The budget includes patch prefixes, but there is no
actual base body, AR02 outer header, AF02/GF02 framing or network in this test.
These section byte counts are not complete AR02 or wire bytes.

| Source | Cache hits / patch attempts | Selector mean, uncached → cached |
| --- | ---: | ---: |
| Combat, 60 temporal IDs | 213 / 240 | 6.028 → 1.695 ms |
| Second, 60 temporal IDs | 9 / 240 | 8.696 → 8.607 ms |
| Combat, 8 held-out IDs | 26 / 32 | 6.093 → 1.985 ms |
| Second, 8 held-out IDs | 0 / 32 | 8.734 → 8.882 ms |
| Synthetic moving background / static UI | 44 / 48 | 6.340 → 1.329 ms |
| Synthetic changing noise UI | 0 / 48 | 7.024 → 7.093 ms |

The small second-source difference is not an isolated causal speedup: host load
is uncontrolled and only one retained timing campaign is recorded. The no-hit
held-out/noise cases show cache overhead. Native fixtures have all four selected
rectangles, totaling 21,120 words/frame. These are configured priority regions,
not independently verified HUD locations. In the changing-noise fixture, real bytes
exceed the declared budget for the fourth rectangle, so the first three retain
15,360 exact words/frame; the rejected fourth attempt remains paid.

Across **160 paired IDs and 640 patch attempts**, there are 292 cache hits,
including 176 while the whole source RGB hash changes. Every paired section byte
string and displayed output is identical. Selected original RGB565 words and
unselected base words have zero mismatches. The result contains 16 executed-source
pins and source-media manifests. The host campaign took 4.72 seconds including
verification outside selector clocks.

Selector clocks include current conversion/cache work, actual candidate encoding,
validation and admission. Section assembly and full section parse/display apply
are separately timed. Source acquisition/BOX loading, fixed base generation,
hash and quality checks are outside those clocks. Native inputs are related
precompressed 25/29.88 fps clips, not live 30 distinct fps acquisition. This study
does not prove a complete AR02 stream, finite delivery FPS or hardware timing.

Eight tests cover framing, full-payload rejection, preflight of all patches before
pixel allocation, overlap/geometry/CRC, exact selected and unselected words,
no base mutation, cache equality/bounds, complete byte budgets, priority fallback,
late observed work budgets and canonical count/length/type/padding rules.

```sh
python -m unittest -v test_unified_ui.py
python verify.py                       # read-only retained evidence checks
python benchmark.py > run.log 2>&1     # regenerate; external media required
```

Use the study virtual environment. The parent AR02 integration results must
separately pay base, wrapper, reference, feedback, transport and display service;
standalone selector savings cannot be added to an FPS claim.
