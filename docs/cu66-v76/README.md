# CU66 V76 — warm decode limits and direct-YUV service study

After scanout is warm, burst-HUD validated P intervals are **28.17–30.37 ms**,
and complete transactions are **86.60–89.20 ms** across four controlled phases.
All eight scalar/burst trials remain exact with zero LCD underruns or mismatching
black lines. The 30-fps and strict under-10-ms goals are still unproven.

Actual controller tests identify a candidate direct-YUV path: dedicated-port
early prefetch meets all 90 original strip deadlines under the tested paced
background load. Its modeled consumer timeline requires **three live strips /
29,184 cache data bytes**; the smaller two-live model is insufficient. There is
no new production RTL renderer, hardware cache, generation lease or bitstream.

- [Measured results, integration gates and next steps](hardware-handoff.md)
- [Goal and timestamp contract](milestones.md)
- [Warm phase-controlled replay](phases.md)
- [Actual-controller service and separate schedule ablation](service.md)
- [Structured cache/pixel model and liveness hazards](direct-yuv-architecture.md)
- [Iteration plan](plan.md)

Machine-readable results and retained logs are in `fpga/experiments/cu66-v76/`;
producers and read-only auditors are in `scripts/cu66-v76/`. All V69–V75 files
remain frozen.
