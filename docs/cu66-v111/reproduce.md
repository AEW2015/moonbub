# Reproduce V111 evidence

Use a new external build directory and the source-bound receipts rather than
changing frozen V110 files. Native tools are the existing legitimate Vivado
2026.1 build 6511674 installation and read-only license supplied for the Acorn
container. The native and simulation images are content-pinned in actual
receipts. Vivado MCP still returned `Transport closed`; CLI is explicit.

## Functional qualification

```sh
python3 scripts/cu66-v111/header/qualify.py --run
python3 scripts/cu66-v111/canonical.py --variant combined --run
```

The first command is a focused old-Count/new-header miter, retaining original
assertions/goldens and additional header/error/cancel checks. The second runs
the complete unchanged two-seed canonical workload. Each creates a unique
attempt with snapshots, logs and hashes. Retained failures are not overwritten.
Coordinate heavy-job grants; do not launch these beside two other heavy jobs.

## Actual guest/RTL and UDP capture

```sh
python3 scripts/cu66-v111/harness/baseline.py
python3 scripts/cu66-v111/harness/trace_probe.py
python3 scripts/cu66-v111/harness/trace.py validate PATH_TO_CAPTURE_JSON
```

Read [harness.md](harness.md) for external guest/tool paths, exact reuse/build
provenance and dependency limitations. Guest binary reuse does not constitute
a target firmware rebuild. Legacy warning policy, related-oracle scope,
unsynchronized time and missing Sunshine/GP-SPI/DMA paths remain explicit.

## Physical implementation

```sh
python3 -m unittest discover -s scripts/cu66-v111/tests -p test_native.py
python3 scripts/cu66-v111/native.py --trial count-125
python3 scripts/cu66-v111/native.py --trial header-100
python3 scripts/cu66-v111/native.py --trial header-125
```

Preparation does not dispatch. Header preparation requires actual focused and
full canonical PASS and exact source/proof bindings. Independently audit the
selected unique preflight, then root serializes its dispatch:

```sh
python3 scripts/cu66-v111/native.py --run \
  --preflight EXACT_PREFLIGHT --audit EXACT_AUDIT
```

The gate file must match the exact preflight and policy hashes. Dispatch checks
current sources, proof receipts, recipes, image, clocks and resources again.
Do not run old prepared-only cards against a changed driver; their pins should
reject drift. Consumed reservations deliberately prohibit replaying a trial as
a new result. A separately budgeted study must use new policies/namespaces.

Only a genuinely positive terminal V111 receipt permits:

```sh
python3 scripts/cu66-v111/native.py --trial MATCHING_TRIAL \
  --repeat-of EXACT_POSITIVE_RECEIPT
```

Its new preflight needs another independent audit. Parent log/retained reports
are rehashed/reparsed; the repeat retains source, target clock, functional Tcl,
tool image and method and begins from RTL. No extra positive repeat is allowed.
Parser unit tests use clearly synthetic positive fixtures only to test guards;
they are not native clock measurements.

```sh
python3 scripts/cu66-v111/summarize.py
```

This regenerates actual-receipt summaries; it never turns a running job,
synthetic test, component clock or functional JPEG baseline into a product
30-fps/under-10-ms result.
