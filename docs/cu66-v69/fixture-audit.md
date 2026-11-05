# V69 fixture semantic audit

`experiments/cu66-native-v69/manifest.json` contains 457 exported CU66 packets in four source cases: 119 frames each from `mass-effect-10000`, `mass-effect-4500`, and `mass-effect-1600`, plus 100 from `mass-effect-combat`. These remain clips from the same Mass Effect walkthrough family, not 457 independent games or captures.

The independent audit command is:

```sh
/home/lori/gamebub-streaming-prototype/.venv/bin/python scripts/cu66-v69/audit_python_fixtures.py
```

It replays each stored packet with the frozen Python V66 receiver explicitly configured for CU66, resetting receiver state at each case. It checks packet length and SHA-256, causal frame/key/reference identity, then compares canonical planar-u8 output SHA-256, exact HUD-word SHA-256, displayed RGB565 SHA-256, and canonical output tag against the native fixture manifest. The full replay passed: `119 + 119 + 119 + 100 = 457` frames. It validates the fixture set and native-runner expected-output hashes; it does not validate the C++ decoder, RTL, installed Vivado part, hardware, or 30 fps.
