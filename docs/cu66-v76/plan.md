# CU66 V76 phase controlled full system service study

## Scope

V76 uses the frozen V75 RTL and exercises warm full system presentations with
phase controlled P source admission. The source is admitted at a fixed absolute
200 ms point, then repeated at four controlled phase offsets. The purpose is to
measure how those phase choices affect the modeled service and presentation
timings.

The service bench sends a synthetic address trace through the actual frozen
controller and checked SDRAM model. It replaces Python service assumptions with
measured command-model transactions while keeping the trace's software-cache
miss and synthetic-data assumptions explicit. Runs cover display-only and
contended service over legal P1 and LCD interfaces. The separate Python
fixed-column model checks miss-set correspondence and mathematical RGB output;
neither bench implements an RTL cache or exact video renderer.

V76 adds testbench RTL while keeping production RTL frozen; it creates no
implementation bitstream. Any timing derived from the command model assumes
100 MHz. It is not Fmax, physical 30 fps proof, or proof of a sub-10 ms response.

## Evidence and verdict rules

Functional correctness and performance are separate verdicts. A functional
PASS requires retained source and data identity checks, exact output/data
comparison against the declared oracle, matching presentation identities, and
complete transaction accounting. A PASS marker alone is insufficient.

The evidence audit must report explicit verdicts against all three targets:

* 33.333 ms serial transaction service budget for the current single-candidate
  path. This is not a universal presentation deadline; native display-vblank
  quantization can create normal presentation jitter.
* strict 10 ms ingress-complete to validated-ready latency, including modeled
  queue, memory, and validation time. This is not a generic response target.
* 147.403 us YUV-strip target.

Each verdict is computed from the actual retained run data and its declared
measurement boundary. The final phase evidence passes functionally, while all
8 phase cases fail both the 33.333 ms serial budget and strict 10 ms interval.
The direct-service evidence passes functionally; 6 of 14 baseline cases meet
the strip deadline and 8 fail. Two of three separate lookahead cases meet their
original strip deadlines, but the Python capacity model requires 29,184 bytes
to keep the three live strip generations. Performance may FAIL while functional
correctness passes. No target is claimed from command-model timing or an
unverified frequency. Missing evidence is UNAVAILABLE, not PASS.

The source-count and timestamp boundaries for sustained goals are recorded in
the [milestones and measurement boundaries](milestones.md). The four-phase,
two-source V76 replay is diagnostic evidence; it does not qualify the 1,800
source / 60 second modeled campaign or 18,000 source / 600 second physical
campaign.

## Frozen baseline

Run `python3 scripts/cu66-v76/verify_baseline.py`. It verifies the V69–V75
frozen bundle counts and source hashes, plus ancestry from the V75 parent
`e848da4288eacd022b04967cc091c4a272a69a97`. This is an integrity check only.

## Reproduction and packaging

The V76 evidence auditor is `scripts/cu66-v76/verify_evidence.py`; it verifies
baseline ancestry and hashes, phase/frame identities and timings, controller
service intervals and deadlines, cross-simulator counters, the structured cache
hazard probes, and milestone arithmetic. Reproduce the individual artifacts
with the producer scripts in `scripts/cu66-v76/` and the service-specific
commands in `service.md`. After the three V76 artifact directories are final,
create and check the bundle with
`python3 scripts/cu66-v76/bundle_manifest.py --write` and then
`python3 scripts/cu66-v76/bundle_manifest.py`. The bundle covers only
`docs/cu66-v76`, `scripts/cu66-v76`, and `fpga/experiments/cu66-v76`, excluding
the manifest itself and generated Python bytecode.
