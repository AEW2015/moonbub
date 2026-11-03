# Streaming desktop UI verification

This isolated harness imports the frozen production `main.slint` and
`src/ui/slint.rs`. It uses the actual firmware software platform, ARGB1555
pixel type, and a persistent 360-pixel line buffer that copies dirty writes
into a retained overlay image. It does not modify firmware inputs or the
firmware build manifest.

Networking, connection, host editing, and teardown callbacks are mocks. The
displayed FPS/bitrate/counters are test data, not hardware measurements.

Run from this directory:

```powershell
$env:PATH = "$env:USERPROFILE\.cargo\bin;$env:PATH"
$env:CARGO_TARGET_DIR = 'C:\mbui'
cargo +stable run --release --locked --manifest-path Cargo.toml --target x86_64-pc-windows-msvc
```

The harness dispatches real Slint controller key events. It verifies access
from the main menu, IPv4 octet focus/edit callbacks, Connect, View, Home,
game-menu Exit, Disconnect, and Back. Callbacks must run outside the mock
device lock held by rendering. View must clear every previously opaque
overlay pixel through the production ARGB1555 line-rendering path.

PPM files are raw software-renderer captures. PNG files are lossless format
conversions of those captures. The complete focused View button occupies
`x=4..355, y=216..237`, inside the 360x240 menu canvas. The screenshot was also
visually inspected for clipping.

This proves desktop UI behavior with mock backend callbacks. It does not
execute ESP-IDF Wi-Fi, QSPI, FPGA overlay scanout, physical buttons, or the
production asynchronous streaming teardown worker.
