# v26 offline build records

These are exact copies of selected records from the sealed local
`firmware/experiments/v26-key-diag-access-20261104` candidate. The image is not
installed; no physical stack, heap, SPI or admission/drain qualification is claimed.

`build-manifest.json` SHA-256 is
`00b3d4a4bd6190646d72b817dc22d3802e6f70b87cfec35d9d5b2547cf8c4a66`.
It inventories local files, including preserved history; those referenced files,
the complete SDK/source tree and binary images are not distributed in this folder.
An inventory is not a portable reproduction of the full firmware build.
`BUILD-RESULTS.md` and `resource-observability.json` are hash-bound by that manifest.
`SDK-STACK-UNITS.md` records the actual pinned SDK byte-unit check.

Follow [the planned physical regression](../../V26-AKD1-REGRESSION-20261104.md)
after the separate FPGA routing gates pass. Keep the known v22/build50 recovery
artifacts and normal SD configuration intact.
