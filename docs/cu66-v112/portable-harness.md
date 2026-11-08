# Portable V112 harness fixture preparation

The [new wrapper](../../scripts/cu66-v112/portable_harness.py) removes the
original harness's dependency on the two absolute external fixture locations.
It imports the unchanged runner and overrides only `GUEST` (the directory
containing `fixture.trace`) and `JPEG`. DUT sources, C oracle, source snapshots,
commands, acceptance checks and resource limits remain the original runner's.
The Docker tools image and original runner's external build-directory
requirements still apply; this is fixture-location portability only.

The wrapper verifies the selected harness receipt hash, all 49 current and
retained source pins, and the retained guest-accepted trace against both of
its receipt bindings. It reuses the original event reconstruction to verify
all 28 original guest event hashes, then concatenates the **26 DATA payloads**
in checked offset order. The resulting **26,159-byte JPEG** matches both the
original CRC32 `eceeb9c5` and selected JPEG SHA-256
`8cc99ea7d50d1d20255e41ff7247b0770b3349e705c27152a41817418ce5c9de`.
Copies named `fixture.trace` and `0000.jpg` live in a temporary directory
outside the repository, which is removed when the wrapper returns.

Fixture preparation was actually executed successfully:

```sh
python3 scripts/cu66-v112/portable_harness.py --check-only
```

The [check summary](../../experiments/python-gamebub-v112/portability/results.json)
binds the [preparation receipt](../../experiments/python-gamebub-v112/portability/checks/20261108T195357729346Z/receipt.json),
including wrapper, unchanged runner, selected original receipt, trace,
reconstructed JPEG and original event hashes. This check does not invoke
Docker, compile RTL, run the C oracle or execute a simulation.

A full fresh invocation is available through:

```sh
python3 scripts/cu66-v112/portable_harness.py
```

**The full wrapper invocation has not been executed.** The existing harness
PASS remains the original runner's executed evidence, with its original
external fixtures. The new PASS is only source binding and fixture
preparation. A future full invocation calls the unchanged runner, which
creates a new harness attempt and its own execution receipt; the portability
receipt describes the preceding preparation check. No frozen harness source,
document, receipt, trace or other evidence was edited for this wrapper.
