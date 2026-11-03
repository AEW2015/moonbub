# Python Game Bub v10 evidence audit

This independent, standard-library-only audit covers the selective UI, service accounting, RGB565 row/span RLE, standard HEVC/AV1, uncompressed color-floor, and common-color codec studies. It rederives stored results from their row data; absent files and fields remain explicit evidence gaps.

The helper separates explicit real-source and synthetic inputs, measures selected ROI pixels against both the requested and broad declared region, checks whole-packet caps and exact GM01 fallback identity, accounts for rejected work, and separates measured host wall time from charged virtual CPU service. It checks all HR01/HP01 candidates against the selected minimum, validates native packet plus extradata totals and decoder PTS, and independently recomputes pooled PSNR from squared-error sums and pixel counts. Reused GM01 rows in the common-color comparison are marked and not counted as new codec decodes.

## Stored evidence audit (2026-11-03)

The selective study has 60 decisions: 48 real-source rows and 12 synthetic rows. Eighteen work-budget fallbacks preserve the byte-identical GM01 base packet. Sixteen rejected patch attempts carry 10.284 ms of recorded encode plus validation service. Broad real-source selection covers about 32.4% of its declared region; compact selection covers its requested region while about 44.6% of the broad area is selected. The study caps complete packets at 49,152 bytes.

The row study contains 20 inputs and 80 profiles; each of the four profiles has patch output. Its stored real-source means rederive: compact HP01 40,047.7 B to adaptive row 31,216.4 B, both fitting 16/16; broad HP01 87,470.7 B to adaptive row 45,557.5 B, changing from 0/16 to 8/16 fitting. All independently checked HP01 versus HR01 candidate choices select the least-byte output. These results are host software measurements and do not establish 30 fps.

The service study contains eight cases: two zero-CPU controls and six cases charging CPU work. The controls still recorded 306.503 ms of actual CPU and resize wall time while charging 0 ms to virtual service. Charged cases total 720.375 ms of CPU/resize service. All modeled CPU queues drain. Scope fields show that capture acquisition, network sockets, hardware CPU, DMA/CDC, scanout and physical display are outside the model.

The standard comparison has 18 profiles and 1,080 decoded rows across two sources, with the same source frame hashes across profiles. The first source has 32 unique RGB frames among 60 IDs; the second has 60. Native HEVC/AV1 packet bytes plus extradata match the stored per-frame and summary totals, decoder output PTS are 0–59, and pooled PSNR recomputes from per-frame error sums. The separate no-compression probe has 240 color-conversion rows. For the second source, its active-region PyAV conversion floor is 35.191 dB versus 37.477 dB for GM integer conversion, so RGB conversion differences affect comparisons against the GM baseline.

The common-color study adds 720 new native codec output rows and reuses 360 already-decoded GM01 rows. The original and common-color codec campaigns therefore total 1,800 unique codec-output rows; reused GM01 rows are not double-counted. Native packet PTS, emitted PTS, packet-plus-extradata sizes, pooled quality, source manifests and the original-results SHA pin all match. The common-color combat points rederive to GM ROI 2.112568 Mbps / 34.020 dB active / 35.739 dB ROI, HEVC q36 0.207412 / 35.904 / 36.389, and AV1 q48 0.131240 / 36.522 / 37.245. Quality parameters across encoders are still not equal-quality settings.

All 31 declared software/source pins and both external media hashes match before and after. There are no missing supplied result files. Remaining evidence gaps are target hardware decoding, live capture/transport/scanout, and demonstrated 30 fps presentation; the reports are offline host/virtual-stage studies.

The audit does not execute codecs, video or timing workloads, and does not modify companion studies. Whole-frame cap fit does not establish ROI coverage; software timing does not establish target CPU timing; offline service does not establish a complete live pipeline.

Run `python3 audit.py` to write `audit.json` for available companion results and list inputs that have not arrived. Run `python3 -m unittest -v test_audit.py` for the lightweight helper tests.
