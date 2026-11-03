# Source and licensing notices

MoonBub is an experimental Game Bub streaming prototype assembled from several
source trees. This repository is a standalone publication of the local prototype;
it is not a GitHub fork of the unrelated hgaiser/moonshine streaming server.

- `firmware/handheld` is derived from Game Bub firmware, including existing local
  changes. See `firmware/LICENSE-GPL-V3`, `firmware/source-snapshot.json`, and
  https://github.com/elipsitz/gamebub.
- Game Bub-derived FPGA source and board constraints retain their notices and
  the applicable licenses in `fpga/licenses/`.
- `fpga/vendor/core_jpeg` is derived from ultraembedded/core_jpeg at commit
  `bb03cce45d0b7459d395486e9e1db3de1b416bd2`, under its included Apache 2.0
  license. The local change is `fpga/patches/jpeg-output-elastic.patch`.
- The Ark Pixel font files in `firmware/handheld/res/fonts` are Copyright (c)
  2021 TakWolf and distributed under the included SIL Open Font License 1.1.
- `host/references` contains reference material from Sunshine and Moonlight;
  their own licenses and recorded revisions are retained there. These reference
  snapshots are for the documented compatibility audit.

See the original notices and license files for the terms applying to each part.
