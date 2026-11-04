# Fixed-profile native GM25 R/D probe

This exploratory probe tests eight declared policies on the first 12 retained
frames of each v24 native scene. It keeps the 720×480 coded canvas, active 720×405
quality crop, exact RGB565 HUD overlay, and only decoded reconstructed YUV as
its next acknowledged reference. Each policy independently starts with key0.

`probe.py` executes and decodes every actual packet; `results.json` retains source
pins, per-frame byte counts, packet/display hashes, RGB error and full paid work.
It compares zero/block16/block32 prediction, background16/32 quantization and
lossy skip lambda0/4/16. The two additional policies are block16/lambda4 and
ROI16/background32/lambda4. Priority regions remain the frozen two base regions.
No transport admission rejects candidates during this rate/distortion probe.

Run with the project NumPy/Pillow environment:

```sh
python probe.py > run.log
```

Projected hybrid bytes add retained HD25 HUD accounting and 57 binding bytes;
they are not a new serialized combined packet. Only base packets are encoded
here. Results are not a full48-frame cohort, physical30fps, native endpoint or
FPGA resource/timing proof. Separate display/conversion/metric timing is outside
encoder clocks; all one-shot base encode and decode work is included.
