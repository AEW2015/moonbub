EC93 adds two literal coding controls to frozen AB38 and BR88 context streams.
The packet header is 44 bytes, followed by four streams and a four-byte CRC.
Byte 6 contains four two-bit methods in DC, AC1, AC2, AC3 order, with method 0
AB, 1 BR, 2 HY and 3 SG. RAW packets require selector zero and canonical
128*blocks coefficient bytes, with all other lengths and AC counts zero.

HY uses frozen whole-context best_k values. Its only arithmetic symbols are
Rice unary quotient decisions, with the frozen 88-entry probability state
reset to 128 for every context. All remainder and escape bits are MSB-first
plain bits, by a fixed rule declared before corpus observation. The arithmetic
stream retains AB's exact two-zero termination and bit padding, including for
zero AC events. The histogram is descriptive and is never used to fit a
suffix bypass rule. The histogram indexes run/DC versus level, LSB bit
position 0 through 23, then zero/one observed counts.

SG is a bounded small-block Rice control, with at most 32 DC values or AC
run/level events in each group. The six-byte stream descriptor declares group
size 32, reserved zero and the exact implicit group count. Each group charges
its own two best_k bytes and four-byte bit length. Run positions continue
across groups. There is no RLGR conformance claim.

The helper runs each of AB, BR, HY and SG once per plane, retaining discarded
alternatives. It assembles four homogeneous selectors (0,85,170,255) and one
contextwise minimum stream-byte selector. Ties choose the lower method.
Each assembly uses RAW if coded bytes reach the coefficient payload size.
If either frozen AB/BR encoder already discarded streams for RAW, every
assembly conservatively uses RAW; the new HY and SG work still runs and is
included in generation timing. The collector's byte and work claims are host
software measurements only. They do not establish target hardware timing.

Native decoding validates every emitted packet. Independent Python decoding
validates all four context alternatives and verifies the local packet's exact
stream composition. Small synthetic fixture families exercise every one of
256 selectors, including RAW behavior and malformed-header/CRC/truncation
rejection. Campaigns compile and run snapshotted sources using g++ 13.3 in
the existing build container, retain failed attempts, and impose a finite
watchdog. Native peak RSS is read using getrusage(RUSAGE_SELF).
