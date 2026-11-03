# Connected input-buffer/X stream contract

For this explicitly scoped startup, the original `jpeg_idct_ram` connected to original `jpeg_idct_x` satisfies the standalone transpose study's input-stream contract: after reset and initial image-start, each X-valid block has 64 consecutive beats indexed 0–63, with at least two X-invalid cycles before the next block. Yosys SAT checked the original connected modules with their actual data connections. The 200-step bounded check passed; temporal induction proved both base and induction step at depth 96. This is an unbounded control-stream proof under the assumptions below, not a proof of JPEG decode correctness or all reset/restart behavior.

The harness asserts reset for the first edge, then asserts initial image-start for at least one cycle and allows its high level to last any number of cycles, including forever; after deassertion, reset and start remain low forever. It allows arbitrary coefficient valid, coefficient index/data, EOB and parent output-ready on every cycle, including while input accept is low. This overapproximates ordinary input handshakes for this control-stream property. Arbitrary data are connected through the actual RAM to X; no substitute arithmetic or memory is inserted. Source control paths do not use coefficient data, and because X data output is not observed the formal optimizer removes irrelevant data arithmetic and RAM. Yosys reports that X `block_out` memory is replaced by registers during frontend elaboration; that is not a data-integrity proof.

The monitor starts with expected index zero; when a block is in progress it asserts X valid every cycle, checks every valid index, and requires two invalid cycles after index 63. Arbitrary-length waiting before a block is allowed. The original input buffer's reset/start clears its block-ready state and FSM; X reset clears its early valid pipeline, later valid shift and pointer. During the initial start level the monitor is reset. `-set-init-zero` additionally initializes unspecified state. The clean reset before start is essential to this proof.

The previous sibling `variable-gap/` study proves that the original transpose, output-ready fixed high, accepts all offered valid beats for any input stream satisfying this block/gap contract from its matching reset state. The original `jpeg_idct.v` connects input-buffer output valid to X, X valid/index directly to transpose, and ties transpose output ready high. Thus the two results compose for the connected IDCT control path after the same clean reset/initial-start phase and with no subsequent reset/start; they do not establish IDCT data correctness, real board operation or behavior around subsequent images.

## Parser and interrupted start

`jpeg_core.v` connects its input parser's `img_start_o` to the IDCT. In the original parser, start is set on SOI while parser state is IDLE and cleared on SOS, so it is a level, not necessarily one cycle. The experimental `marker-followup/jpeg_input_followup.v` implements the same level concept with additional accepted-byte gating. In IMG_DATA the parser waits for EOI before returning to IDLE; a later SOI may produce a new start. Whether old IDCT/X work can still be in flight at that later start depends on full parser/decoder/queue scheduling and has not been established here.

`restart-negative.v` deliberately allows arbitrary later start pulses and arbitrary coefficient/EOB signals. Its 100-step SAT query produces a counterexample: the saved VCD has an incomplete X block (for example, expected index 2 while X valid is low at SAT timestep 90). This is an adversarial control input, **not a demonstrated reachable JPEG or device bug**. It illustrates why later start was excluded: image-start clears X's late valid shift and pointer, but does not clear the four earlier X valid registers. The unrestricted restart trace and exact solver output are retained. The one-cycle-initial-start proof is also retained separately for audit.

## Reproduction

```sh
FPGA_DIR=/path/to/moonbub-30fps-study/fpga BUILD_DIR=/tmp/idct-stream-contract ./run.sh
FPGA_DIR=/path/to/moonbub-30fps-study/fpga BUILD_DIR=/tmp/idct-restart-negative ./run-negative.sh
```

The main wrapper reports BMC and induction exit statuses individually; inspect the logs for `SAT proof finished - no model found: SUCCESS!`, `Base case for induction length 96 proven`, and `Induction step proven: SUCCESS!`. Each query has a 90-second wall limit; the retained induction completed in about 77 CPU seconds with about 1.2 GB solver memory. The negative wrapper expects `SAT proof finished - model found: FAIL!` and records a VCD. Tool versions, original source hashes, complete compressed logs and witness are in `results/`; production RTL is unmodified.
