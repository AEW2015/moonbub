# V55 actual Rust receiver full-system gate

Qualification passed; see result.json and comparison.json. This isolated replay uses exact V55 network_driver/local/Hud/framing/STB1 copies, fixtures and the native DLL/import library from v55-host01. Native source hashes match that qualified host build, including the combined Huffman and READ-slice changes. The target ELF is not used by this host simulation. The app-only network failure diagnostic hook is not invoked by a successful pair.

The actual Rust receiver drives the same selected STB1 RTL/decoder, full SDRAM model, HBU write/readback, native drain/commit, presentation and raster capture as the V52 control. The new hbu_status_words override performs five sequential direct-CSR RPC reads at 608/60c/610/614/618 and returns fields 0/2/3/4. Batching is logical only; no actual SPI/ESP-IDF/DMA/radio timing is modeled.

Native Prepare includes a fixed explicit 200 ms virtual delay while RTL/refresh/scanout keep running. Native host computation itself pauses virtual time, so its virtual CPU timer is 0; this is not target CPU performance or 30 fps proof. Model clock 100 MHz, eight core cycles per CSR, accelerated 20-cycle powerup and 750-cycle refresh are retained. Host allocations do not apply the target physical heap reserve callback.

The original small KEY/P fixtures are used, not the 120-second Mass Effect clip. Independent comparison checks both complete canonical banks, all 691,200 composed video pixels, black simulation borders and 42,240 displayed HUD words. Simulation placement remains origin 40, not physical margin 13.

See bindings.json, fixture-binding.json, compile-command.json and raw logs. The V52 control, selected overlay, all Vivado builds and hardware remain untouched. Everything is confined to C:/moon.

Final result: 2 accepted/presented, zero rejects/underruns; 42,240 HBU words written and verified. Both canonical banks, all 691,200 video pixels and all 42,240 displayed HUD words matched independent goldens exactly. Native arena cap 98,304 bytes, peak 88,942 bytes, allocation failures 0. Replay wall time 436.203 seconds; target throughput remains unmeasured.
