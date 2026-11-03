# Conditional transpose acceptance check

This checks the unchanged transpose RTL's control behavior using Yosys SAT. It does **not** prove that its input contract is produced by the real JPEG front end. The harness applies one initial reset edge, sets image-start low thereafter, ties transpose output ready high permanently and starts with index 0. It offers exactly 64 consecutive valid beats, indices 0 through 63, followed by exactly GAP invalid cycles, forever. The generator advances on offered valid, even if accept is low, matching X's lack of accept input. Data are constant zero and unused output data are removed by optimization. No midstream reset, start, or varying gap is modeled. The reset edge clears the bank flags, pointers, FSM and read index; `-set-init-zero` also initializes any remaining unspecified formal state. This is not arbitrary pre-reset-state reasoning.

Results, with GAP measured in invalid cycles between consecutive 64-beat blocks:

| GAP | SAT through 150 steps | SAT through 300 steps | Meaning |
|---|---|---|---|
| 0 | fail | fail | First rejected beat at VCD time/step 130, index 0; both bank-ready flags 11, write bank 0, read bank 0, reader ACTIVE at index 62. |
| 1 | pass | fail | First rejected beat at step 197, index 0; both ready 11, write/read bank 1, reader ACTIVE at index 63. |
| 2 | pass | pass | No counterexample through 300 steps only. |
| 3 | pass | pass | No counterexample through 300 steps only. |

The counterexample is a genuinely offered beat under this standalone contract, with output ready high; it is not a demonstrated decoder failure. The upstream IDCT input RAM emits 64 ACTIVE cycles followed by at least IDLE and SETUP before the next ACTIVE block. The X output valid is a fixed pipeline of that valid. Thus these zero- and one-gap streams do not represent normal uninterrupted connected input-RAM/X operation without reset/start; this structural observation is not a complete proof of the real JPEG interface, reset behavior, or all error paths. The experiment also excludes independently varying gaps.

Temporal induction was attempted with `-seq 10 -tempinduct -maxsteps 100` for every gap. It did not establish the property: the GAP 2 and 3 induction attempts reach the limit without a proof, despite the 150-step base checks passing. No unbounded result is claimed. Full logs, including failed induction and the 300-step counterexample VCDs, are gzip-compressed under `results/`; SHA-256 and tool version are included. VCD time denotes Yosys SAT timestep, not physical time. `-dump_vcd` emits a witness when a model is found. The 300-step command returns success for either SAT outcome: inspect `SAT proof finished` in the log rather than using its exit status as a proof result.

```sh
FPGA_DIR=/path/to/moonbub-30fps-study/fpga BUILD_DIR=/tmp/transpose-formal-150 ./run.sh
FPGA_DIR=/path/to/moonbub-30fps-study/fpga BUILD_DIR=/tmp/transpose-formal-300 ./trace.sh
```

Each SAT invocation has a wall-time limit (30 seconds for 150-step/induction; 60 seconds for the 300-step run). `run.sh` reports each exit without hiding failed or timed-out attempts. The saved run used Yosys 0.33 from Ubuntu 24.04. Production RTL is unmodified.

## Why the ordinary connected stream has two invalid cycles

In `jpeg_idct_ram.v`, `outport_valid_o` is exactly `(state_q == STATE_ACTIVE)` (line 402). On the cycle where ACTIVE's read index is 63, the next state is IDLE (lines 334–337). From IDLE it can enter SETUP only on the next edge, even with a ready bank and output ready high (lines 325–329); SETUP transitions to ACTIVE only at the following edge (lines 330–332). Therefore, between successive complete ACTIVE runs there are at least the two sampled states IDLE and SETUP with input-RAM valid low. Downstream ready can lengthen IDLE but cannot remove either state. In `jpeg_idct.v`, this valid connects to X `inport_valid_i`. In `jpeg_idct_x.v`, four always-clocked valid registers pass it in order (lines 222–263 and 348–359), followed by the unconditionally shifted `valid_q[6]` (lines 401–421). With reset and image-start absent during the relevant pipeline interval, this fixed delay preserves the two low cycles and does not compress them. The X output index increments on every output-valid beat (lines 411–424). After a clean reset and aligned complete runs, the resulting index sequence wraps 0 through 63 per run. This is a direct RTL control-path argument, not a separate formal theorem; in particular `img_start_i` clears the later valid shift register but not the four earlier X valid registers, so arbitrary interrupted/restarted streams require their own analysis.
