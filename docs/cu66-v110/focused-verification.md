# V110 focused verification audit

The focused busy scratch proof passed two actual RTL seeds, 110501 and 110502.
Each covered 72 full transactions, 128 corrupt-response cases, four read-owner
cases, 48 DC-line-boundary transactions, all 16 offsets and all four banks. The
runs executed 291,968 and 291,407 clock edges. The fault proof passed two actual
inverse seeds (110101 and 110102), each covering 128 coefficient words and 51
concurrent math cases, plus a reconstruction comparison across two frames and
51 directed checks over 2,445,067 clocks and 7,335,201 half-cycle comparisons.
Both focused receipts report zero public cycles added.

All recorded source hashes match the current files: 18 busy inputs and 33 fault
inputs. Both compile with Verilator assertions active and warnings treated
strictly; neither records assertion downgrade or warning suppression. These
are focused component proofs. They do not count as full canonical pipeline
passes or establish physical timing.

The active busy and combined canonical attempts had no final receipt at the
time of this audit. Partial seed output is not counted as a pass. See
[focused-final.json](../../experiments/python-gamebub-v110/audit/focused-final.json)
for the actual result pins and exact counts.
