# Cohort source availability audit

This experiment checks whether the existing Mass Effect source clips can supply
predeclared native-frame windows for a 30 fps cohort study. It uses the
sibling [`python-codec-study/corpus.py`](../python-codec-study/corpus.py)
`load_video` helper to decode native frames and BOX-resample them to 720×480.
There is no frame-rate conversion, interpolation, or implicit repetition.

`audit.py` requests 90 frames from each clip at 1 second (primary) and 4
seconds (held-out), for four windows total. It records source and helper hashes,
source PTS/time base and native FPS, actual and unique image counts, per-frame
rendered hashes, scheduled 30 fps duration, PTS span, and exact PTS overlap.
Only metadata and hashes are written; raw decoded frames remain in memory for
one window at a time and are released before the next decode.

## Findings

Both clips supply all four requested 90-frame windows. The combat source is
25 fps. Its primary window spans PTS 1.00–4.56 seconds, and the held-out window
starts at 4.00 seconds. They share 15 exact PTS values; each of those 15 PTS
has an identical rendered image hash in both windows. The value 7 is the count
of distinct shared image-hash values, because some source images repeat. There
are exactly 75 primary frames with PTS strictly before 4.00 seconds; one
primary frame is exactly at the held-out boundary. Thus the 90-frame primary
window is not independent of held-out data. Cap the primary window at 75
observed frames or select separate corpus windows.

The second clip (`mass-effect-2600.mp4`) is 747/25 fps with time base 1/11952.
Its primary window has PTS 12000–47600 (1.004016–3.982597 seconds) and the
held-out window has PTS 48000–83600 (4.016064–6.994645 seconds). The two
90-frame windows have no shared PTS. Each has 90 unique rendered image hashes.

The nominal duration of 90 capture slots at 30 fps is 3 seconds. Source PTS
span describes elapsed time between the first and last selected native frame;
it does not change or resample the source cadence. See [`audit.json`](audit.json)
for full metadata and [`run.log`](run.log) for the compact run summary.

## Reproduce

Use the sibling study's pinned Python environment and locally available source
files (the video files are outside Git):

```sh
cd experiments/python-cohort-study
/home/lori/gamebub-streaming-prototype/.venv/bin/python -m unittest -v test_audit.py
/home/lori/gamebub-streaming-prototype/.venv/bin/python audit.py
```

`tests.log` records the helper tests. The audit JSON records Python, NumPy,
Pillow, PyAV, and `corpus.py` versions/hashes. A new source file or decoder
version produces new provenance and should be treated as a new corpus audit.

## Scope

This establishes source availability and overlap only. It does not measure
codec quality, actual-time 30 fps delivery, receiver performance, or hardware
behavior. The 90-frame combat primary window must not be described as
independent held-out evaluation.
