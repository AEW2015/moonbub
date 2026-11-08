# V111 source-only replay exports audit

**Status:** `PASS_V111_SOURCE_EXPORT_AUDIT` for all three exported source trees. They remain `PREPARED_NOT_RUN`; this audit is not Vivado or timing evidence.

## count125

- Manifest: `/home/lori/gamebub-build/cu66-v69/v111-replay-count125-20261108T1858/replay-manifest.json` (SHA-256 `1fde9cea72f5d7f341a2733d508ebb4a9ad47c3cc4ffa6e05c824dcd459ddec0`).
- Pinned preflight SHA-256 `e82157ded34aecbca26ce387949e17edeafad4bffa7101e54afdc09587dbec5a`; inputs SHA-256 `077e60529d950b934e1e8d1e91e5a23530efb9c6969779f5dc816d0fbbb40561`.
- 18 source files (17 RTL plus one included header), 23 copied/generated payload files; 8.0 ns target, 3600 s watchdog.
- Rehashed manifest-listed files, copied source bytes against prepared source/origin pins, and all three recipe files against preflight hashes. The include directory contains the one `.svh` source; Tcl derives RTL/include/XDC paths relative to `$build`.
- Re-evaluated input Tcl with `tclsh` for actual and relocated paths; both path expansions passed. No DCP, bitstream, or run results are present.

## header100

- Manifest: `/home/lori/gamebub-build/cu66-v69/v111-replay-header100-20261108T1858/replay-manifest.json` (SHA-256 `934c48da8d29bcade8b2989e67d5a318491892923e775f8b92d9b5e198d1f88b`).
- Pinned preflight SHA-256 `35c267c3804f83dde05485a7f28f58171834c04c559f33b787b356e218fb95c3`; inputs SHA-256 `9e14f35b5b6521c6bdc76a6e738dd28749201978bd3c8e99df5cea48553a4ff1`.
- 18 source files (17 RTL plus one included header), 23 copied/generated payload files; 10.0 ns target, 3600 s watchdog.
- Rehashed manifest-listed files, copied source bytes against prepared source/origin pins, and all three recipe files against preflight hashes. The include directory contains the one `.svh` source; Tcl derives RTL/include/XDC paths relative to `$build`.
- Re-evaluated input Tcl with `tclsh` for actual and relocated paths; both path expansions passed. No DCP, bitstream, or run results are present.

## header125

- Manifest: `/home/lori/gamebub-build/cu66-v69/v111-replay-header125-20261108T1858/replay-manifest.json` (SHA-256 `2d2f9f3042911e2cbcb798d2309216d64e6ebee3a17b4788a3802da870b903b0`).
- Pinned preflight SHA-256 `52f13be8dc3914d15b199c6d0464d28e4f1df488094a47deba981980e0a8fce5`; inputs SHA-256 `31b0d0a605575a3f8ce299e325710c3fc4bed86c2bed484af335dd8f2041338b`.
- 18 source files (17 RTL plus one included header), 23 copied/generated payload files; 8.0 ns target, 3600 s watchdog.
- Rehashed manifest-listed files, copied source bytes against prepared source/origin pins, and all three recipe files against preflight hashes. The include directory contains the one `.svh` source; Tcl derives RTL/include/XDC paths relative to `$build`.
- Re-evaluated input Tcl with `tclsh` for actual and relocated paths; both path expansions passed. No DCP, bitstream, or run results are present.

These exports contain no checkpoint and make no timing claim. They preserve the prepared target clocks (Count-125 8 ns, Header-100 10 ns, Header-125 8 ns). A replay would be a new native run with its own dispatch/resource gate.
