# Independent v24 audit

`audit.py` independently verifies the frozen native HEVC/AV1 campaign and the
retained owned/lazy and RS24 reset evidence. It runs offline from source pins,
bounded RGB565/YUV420/HC22 objects, v23 packet streams, native elementary
packets and control traces. It does not acquire source video or rerun encoding.

The audit decoded 20 native profiles across two 48-frame windows (960 outputs),
recomputed 1,920 bare/hybrid quality rows, replayed 192 custom baseline outputs,
and checked 96 HC22 sidecars. It also checked 288 owned/lazy decisions and 10
reset campaigns with 100 parsed control messages, including the three-epoch
reboot sequence and stale-frame rejection.

The recorded RGB input hashes link each retained source canvas to the pinned
v23 row. The original RGB888 frames are not retained, so the audit does not
independently rederive the RGB888-to-RGB565 conversion. It does verify the
stored RGB565 and YUV420 artifacts by digest and length and recomputes all
quality metrics from the retained words and decoded streams.

Run with the repository Python environment:

```sh
python audit.py --check
python -m unittest -v
```

See `audit.json`, `audit-check.log`, `tests.log`, `lazy-verify.log`, and
`recovery-verify.log` for retained results. Standards codec CRFs are not
comparable; operating points are sampled MSE thresholds, not BD-rate. The
native-plus-HUD hybrid uses actual native decode and HC22 bytes, with CP23
binding, ACK and transport charges modeled. Nothing here demonstrates a Game
Bub HEVC/AV1 decoder or physical 30-fps operation.
