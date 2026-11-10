# Reproducing the V124 native endpoint probe

The endpoint scripts deliberately require the Moonbub repository HEAD pinned at preparation time. The current V124 checkout has moved on from that commit, so running `--prepare-only` there will stop at the HEAD check. To make a fresh attempt, use a detached worktree at the pinned V123 parent and copy the V124 endpoint probe files byte-for-byte from the published V124 checkout. This note describes commands only; it does not create a worktree, build an image, or launch the probe.

## Pinned inputs and paths

The endpoint probe pins Moonbub HEAD `1d462803bf2a638f25c2d13bd2215ca08a30518d` and checks that the working tree is at that commit. Its Sunshine source catalog is hardcoded to `/home/lori/gamebub-streaming-prototype/repos/sunshine-30fps-study`; that sibling repository must be at HEAD `3d49c6fe87753eb5b35d693991fdff0365e4bbbf`. Preparation additionally byte-compares each catalog file with its Git blob at the pinned commit, so uncommitted edits to those files cause a stop.

`run.py` resolves `_PATH = Path(__file__).resolve()` and infers the Moonbub repository root as `_PATH.parents[3]`. With the script at `scripts/cu66-v124/endpoint/run.py`, that resolves to the checkout root. Keep the script at that relative path in the worktree.

## Prepare a new attempt

Set `PUBLISHED` to the checkout containing the reviewed V124 scripts and `WT` to a new worktree path. The copy includes only the endpoint probe scripts and dependency Dockerfile; it does not overwrite the V123 production sources or any selected attempt receipt.

```sh
PUBLISHED=/home/lori/gamebub-streaming-prototype/repos/moonbub-30fps-study
WT=/tmp/moonbub-v123-endpoint-repro

git -C "$PUBLISHED" worktree add --detach "$WT" 1d462803bf2a638f25c2d13bd2215ca08a30518d
mkdir -p "$WT/scripts/cu66-v124/endpoint"
for file in run.py packetizer_probe.cpp receiver_probe.rs Dockerfile; do
  cp "$PUBLISHED/scripts/cu66-v124/endpoint/$file" "$WT/scripts/cu66-v124/endpoint/$file"
done

test "$(git -C "$WT" rev-parse HEAD)" = 1d462803bf2a638f25c2d13bd2215ca08a30518d
test "$(git -C /home/lori/gamebub-streaming-prototype/repos/sunshine-30fps-study rev-parse HEAD)" = 3d49c6fe87753eb5b35d693991fdff0365e4bbbf
sha256sum "$PUBLISHED"/scripts/cu66-v124/endpoint/{run.py,packetizer_probe.cpp,receiver_probe.rs,Dockerfile}
sha256sum "$WT"/scripts/cu66-v124/endpoint/{run.py,packetizer_probe.cpp,receiver_probe.rs,Dockerfile}
python3 "$WT/scripts/cu66-v124/endpoint/run.py" --prepare-only
```

The two `sha256sum` lines should match. A successful prepare creates a newly named directory under `$WT/experiments/python-gamebub-v124/endpoint/attempts/` with `PREPARED_NOT_RUN` receipt state. It does not change the selected `results.json` pointer or any existing attempt. The new receipt records the V124 working-tree probe scripts and the pinned production-source snapshots separately.

The expected dependency image ID is `sha256:e6e97e6db1c57d0f07530d7ae6912e455bb7079de7428f282a508a2fcca3fb5a`; the Dockerfile is `scripts/cu66-v124/endpoint/Dockerfile`, and its build metadata is in `$PUBLISHED/experiments/python-gamebub-v124/endpoint/dependency/image.json`. The image was built from local base image ID `sha256:b35d0961607ab885b8024ef37ebcac0c3a0d010af00fe6bbdbc63264079a49cf` with `libboost1.83-dev:amd64=1.83.0-2.1ubuntu3.2`. A rebuild is a separate dependency operation and may produce a different image ID; do not treat a tag match as proof of identical image contents. The probe also requires the read-only `/home/lori/gamebub-tools` mount for the pinned Rust toolchain and Cargo/Rustup homes.

## Launch boundary

A prepared attempt remains unexecuted. Running it requires a separate explicit Root grant and the exact prepared attempt path:

```sh
cd "$WT"
python3 "$WT/scripts/cu66-v124/endpoint/run.py" \
  --run --root-grant ROOT_V124_ENDPOINT \
  --attempt experiments/python-gamebub-v124/endpoint/attempts/<fresh-attempt-name>
```

Do not point this command at the selected attempt or an existing receipt. The launch is the bounded native Sunshine packetizer to actual Rust receiver host probe described in [endpoint-results.md](endpoint-results.md); it is not firmware session execution, ESP32 timing, network capture/send, QSPI/RTL, or board qualification.

## Audit without rerunning

To inspect the already selected proof without making a new attempt, read `experiments/python-gamebub-v124/endpoint/results.json` in `$PUBLISHED`, verify its receipt/result SHA-256 values, and inspect the selected receipt and output hashes. The selected receipt path, selected pointer, and hashes are documented in [endpoint-results.md](endpoint-results.md). This audit mode does not invoke `run.py`, rebuild the image, or rewrite the selected pointer.
