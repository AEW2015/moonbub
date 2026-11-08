# STB1 review addendum ? expanded gates

The reviewed RTL is unchanged from REVIEW.md: FIFO SHAfc9bc79e? and control SHA0fc936e7?. New unit06, full256-unit02 and pins08 freezes all match current sources; exact manifests and log/result hashes are pinned in bindings-addendum01.json.

Expanded gates now demonstrated by retained actual-module simulation:

- Default256 FIFO fills to256 entries with downstream held, rejects an extra word without overwrite, drains all256accepted words/1024bytes with exact native staging RAM/CRC, and explicitly asserts both pointers wrap to0. No activation occurs after the deliberate overflow fault.
- Maximum49152-byte packet traverses actual selected QSPI endpoint/CDC plus prototype control/FIFO and original native staging in48descriptors,12288words; every native byte is read back and checked. This exercises repeated default256 pointer reuse across descriptors. Nominal16MHzQSPI/100MHzcore simulation staging-contract time is6641900ns; this is synthetic protocol simulation, not target throughput.
- Thirteen unit cases include the prior seven plus actual RTL tails1/2, duplicate ticket, nonfinal partial-word rejection, high64-bit generation and incorrect whole-frameCRC seal refusal.
- pins08 reports nine passing pin cases, including maximum-size case; intentional CDC overflow still quarantines and retains the known accepted prefix. The previously reviewed sequential busy-to-ready read transition remains included.

These close the requested default-depth/full/wrap and maximum-packet simulation gates before synthesis exploration. The remaining explicit setup-while-blocked/seal-while-queued and arbitrary simultaneous input fuzz coverage are still not separately exhaustive; RTL review found the existing guards conservative. Parameter DEPTH remains restricted by design assumptions to powers of two<=256; no generic-parameter qualification or elaboration guard was added.

The negative-clock experiment records an EXPECTED_FAILURE at16MHzQSPI/10MHzcore, outside the selected board's100MHzcore. It is NOT a functional pass. It confirms the unchanged fixed dummy/read contract is not valid for arbitrary slow core ratios. That negative directory has no source-freeze.json; only result hash is pinned here, so treat it as diagnostic, not a fully bound qualification run. No clock timing exception or dummy-count change is justified by it.

Whole-system decoder/SDRAM/HUD concurrency, inferred BRAM modes, firmware integration and routed setup/hold/CDC checks remain required. No hardware or Vivado operation by reviewer.
