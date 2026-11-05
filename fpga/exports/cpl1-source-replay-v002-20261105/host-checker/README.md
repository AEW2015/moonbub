# Offline CPL1 snapshot checker

`cpl1_snapshot.py` reads saved v32 cached-page logs. It opens no COM port, device or socket and cannot program, start or reset a decoder. The CPL1 FPGA and v32 application have separate build and hardware gates; this tool does not make them hardware-ready.

After a separately coordinated installation and quiet diagnostic query, the application emits `result=retained pages=10`; ten subsequent `P` commands each emit one cached page. Save the original byte/text capture. The pages carry one cookie/generation and all40 retained words; cached values are historical. A fresh query requires another capture after the tenth page. Do not run this workflow against an active stream or treat repeated queries as decoder progress.

```
python cpl1_snapshot.py --log saved.log --expectation frame0-expectation.json --require-fixture --output new-result.json
```

If the log contains several query groups, select one explicitly with `--cookie 0x1234 --generation 7`. Missing/duplicate/mixed/truncated pages, unknown versions, quarantine, exhausted generations, invalid flags and inconsistent completed canvases reject. Output paths must be new. The report retains every raw word, actual decoded value, input hash, state messages and exact expectation comparisons. A wrong actual CRC stays wrong; expected metadata is never used to manufacture status.

The frame0 expectation names the original17,412-byte CP23 fixture, numeric tag limbs, owner/epoch/frame/generation, actual byte/word counts and expected rendered CRC4c5725e5. A fixture match requires checked success, front qualification, positive bootstrap/writer retirement, completed gap-free canvas, zero LCD underruns and zero bridge lost writes. Live physical-idle bits need not remain high while the displayed front is being read. Writer retirement does not release that front's bank. Unsupported-write counts are reported, not silently treated as memory failures.

The parser does not attest the origin of its supplied log. Pad launches are not SDRAM chip ACKs; a rendered CRC is downstream data-path evidence under that log's separately established provenance. Repeated canvas counts are not unique displayed FPS. USB pages do not independently expose the bus identity guards; those are checked by the source-bound firmware before caching. No cross-ESP32-boot identity/ownership continuity follows.

Run `python -B -m unittest discover -s . -v` for parser/CLI tests. `run_checks.py --firmware-export PATH --evidence NEW_EXTERNAL_PATH` additionally compiles the actual exported v32 Rust page formatter, checks emitted synthetic pages against this parser and verifies bad actual CRC rejection. It invokes no target build or hardware. These synthetic round trips test format compatibility, not FPGA values or playback.
