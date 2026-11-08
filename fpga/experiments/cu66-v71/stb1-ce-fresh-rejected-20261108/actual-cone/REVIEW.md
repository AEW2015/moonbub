# Exact routed CE cone and installed incremental help

Read-only query returned0 in129.391s, with routed DCP and script hashes unchanged and no native errors. No checkpoint, BIT or hardware mutation occurred.

The factoring removes the intended HUD metadata feedback: exact hud_ticket_reg[4]/CE has575 fanin startpoints, with zero hud_gen/ref/fid/bank starts; explicit launches from all those metadata registers find no timing paths. Its final worst setup slack is+0.289ns, hold+0.787ns. The net remains E[0] with324 loads; the driver is now parser/hud_bank[1]_i_1/O (LUT6), rather than the old base LUT4.

This local improvement is separate from whole-design closure: the fresh design fails setup at?0.382ns on a parser metadata arithmetic/CE cone. It is not a new selected image.

Installed Vivado2025.2 verbose help confirms read_checkpoint -incremental -directive RuntimeOptimized and report_incremental_reuse -file. The separately prepared option can request standard incremental reuse using the passing V001 routed reference; actual mode, cell matching, placement reuse and routing reuse remain unmeasured until root authorizes and executes it. Ordinary physopt/place/route directives may be ignored or alter reuse in actual incremental mode; logs and reuse deltas, not requested commands alone, must establish the executed flow. No force_incr or timing exceptions are proposed.

See REVIEW-bindings.json for file hashes and exact measurements. Original baseline remains preserved.
