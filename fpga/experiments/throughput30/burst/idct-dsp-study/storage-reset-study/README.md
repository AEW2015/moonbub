# IDCT storage reset and X-to-transpose acceptance study

This isolated Verilator study uses the unchanged vendor IDCT RTL. It is directed simulation and empirical monitoring, not a universal reset-safety or no-drop proof. It makes no claim about physical hardware. The saved text evidence is in `results/`; generated images and binaries are not included.

## Reproduction

Set `FPGA_DIR` to the repository's `fpga` directory and choose fresh, nonexistent output directories. Verilator with timing support, a C++ compiler, Python 3 and standard Unix utilities are required. The retained runs used the version in each `results/*version.txt`.

```sh
FPGA_DIR=/path/to/moonbub-30fps-study/fpga BUILD_DIR=/tmp/idct-reset-new ./run.sh
FPGA_DIR=/path/to/moonbub-30fps-study/fpga \
  FIXTURE_DIR=/path/to/gameplay-repro/fixtures \
  BUILD_DIR=/tmp/idct-game-monitor-new ./run-game-monitor.sh
```

`VERILATOR` and `PYTHON` may override the executables. The gameplay fixtures are external; the wrapper verifies their manifest and JPEG hashes before copying the first three into the new output directory. Their manifest, source hashes, simulation output and per-frame verification are retained under `results/game-monitor/`. The original fixture directory used was `/home/lori/gamebub-tools/verilator-study/gameplay-repro/fixtures`: precompressed 512×288, 25 fps Mass Effect clip frames sampled for a 30 Hz workload and upscaled in the study. These are simulated fixture data, not a live capture or network. The pinned JPEG SHA-256 values are `6540d2531cf49453fc43b38a07c329c6ddec5fd4619dac3f26ed4c75fceaa149`, `1674cec81028d6730e6c61a6f23eded7e2f260d843c9cc46edf277b8afd9a641`, and `680bbeea3c45a5308ee72f243d704047afad35eedd15e46f77ce326facf7a479`.

## Connected full-path monitor

`tb_qspi_x_accept_monitor.sv` is an isolated copy of the long-run testbench with counters sampling `core.decoder.u_jpeg_idct.idct_x_valid_w` and `core.decoder.u_jpeg_idct.idct_x_accept_w` at `posedge clk`. Cycles with `core.decoder.u_jpeg_idct.rst_i || core.decoder.u_jpeg_idct.img_start_i` high are excluded entirely; the exclusion counter counts *all* such cycles, including held reset, not merely valid transfers. All other cycles with valid high count accepted or rejected according to accept. The saved three-frame run observed **1,555,926 accepted, 0 rejected, and 6,001,353 excluded reset/start cycles**. This is a finite workload observation, not an invariant. The checker also compared all 1,036,800 output pixels to the associated C model, observed three presentations and no modeled underrun; that reference shares decoder algorithms and does not independently prove all JPEG behavior.

The model uses experimental marker and burst-memory RTL, functional SDRAM, modeled LCD and QSPI and an abstract single-frame queue with instantaneous complete compressed arrivals. It does not model actual ESP networking or demonstrate real-time throughput. The signal counter is strictly an X/transpose acceptance observation.

## Directed controls

`tb_storage.sv` seeds paired input, transpose and FIFO RAM with different stale values, applies reset/start with input valid low, and checks a sparse block, both coincident and separate EOB. The input produces 64 matching valid values; a complete accepted 64-index transpose block produces 64 matching valid cycles. FIFO raw output differs while invalid, then the pushed valid ID matches. `tb_idct_reset.sv` similarly compares the complete connected IDCT pair over one sparse block, forces distinct stale X outputs on the first reset edge and confirms different transpose RAM writes occurred on that edge, then checks all 64 valid outputs and ID after reset/start. It observes 64 X beats accepted and no transpose output before the complete set of indices has been seen. These are chosen initial values and one block, not an exhaustive proof; Verilator's two-state model does not establish behavior of unknown values.

The missing-index negative intentionally suppresses transpose index 5 while still supplying index 63: valid transpose output then differs in four cycles between the stale patterns. This injected sequence is not shown reachable from the connected decoder. The busy control drives the standalone transpose output ready low, fills both banks and observes a rejected offer. The actual parent hardwires transpose output ready high, so this forced-busy setup is not the parent configuration and does not establish a production risk or reachable decoder behavior.

## Flow control and proof gap

Transpose accept is `~block_ready_q[block_wr_q]`: it goes low when the selected write bank remains ready, for example when both banks are occupied. The X stage emits valid and advances its output pointer without consuming this accept signal; `idct_x_accept_w` is not fed back into X. A valid beat while accept is low would therefore not be written by transpose. The input buffer's output ready comes from parent downstream output accept, and its state machine checks ready when starting a block, not during the 64-cycle active block. MCU block initiation is indirectly controlled by DQT/IDCT input buffer space. These connections do not by themselves prove that transpose accept is always high for connected decoder traffic.

The MCU can signal EOB independently of coefficient valid, and DQT registers EOB separately. Sparse coefficient indices are legal: input-buffer address-valid bits are cleared by reset/start and mask stale input RAM, so a complete block need not contain every coefficient at its input. The X output stream, however, normally advances its pointer with each valid output; the missing-index control is intentionally outside that stream contract. The FIFO resets pointers/count but not RAM, and its raw output is not meaningful when invalid. System reset/start therefore does not erase all storage, nor does it itself establish equality of arbitrary pre-reset states.

A useful connected-path obligation is `assert property (@(posedge clk) disable iff (rst_i || img_start_i) idct_x_valid_w |-> idct_x_accept_w);` under explicitly stated real upstream protocol, reset/start and backpressure assumptions. Additional per-bank ghost write masks checked on valid transpose reads, and FIFO push/accept and pop/valid association, are needed to establish overwrite-before-read for all legal cases. In particular, reachability of missing writes during malformed JPEG/error handling and no-reject behavior under all legal downstream stalls remain unproved.
