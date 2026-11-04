# `gamebub-mandatory-hud-v1`

`results.json` records a relative `source_sha256` map, four cases, per-case source
manifest, 48 decisions per case, summaries, matched-source comparisons and scope.
Two policy decisions reuse each acquired source frame; there are 96 acquisitions
and 192 actual encoder/decoder decisions, not 192 distinct source acquisitions.

A decision records original canvas hash, measured BOX/policy/patch/attempt work,
mandatory framed bytes and remaining inner budget, each attempted map/complete
byte size, acceptance, semantic state before/after builds, external reader baseline/candidate-reader
delta, issued references,
packet hash/bytes, requested subset coverage, exact selected word count, output
hashes, active expanded-RGB565 channel MSE, actual receive/ACK work and lease drain.
Every accepted mandatory decision selects all four declared rectangles. An
unsuccessful attempt never becomes an issued packet/reference publication.

`vectors` contains actual complete `packet`/`ack` blobs, source/decoded/display
arrays, precondition bank objects and postcondition bank identities/tags. Array
descriptors specify shape and portable dtype (`|u1`, `<i2`, `<u2`) plus a blob.
Blob descriptors contain a safe relative path, zlib encoding, exact raw byte
length/hash and stored SHA-256. Objects are addressed by stored-content hash.
A fixture is independently replayable only after its explicit precondition banks
are loaded; sampled IDs do not form a complete transmitted sequence.

`analysis.json` binds the result and analyzer hashes, exact full-HUD outcomes,
per-decoded requested/selected/omitted coverage, paid rejected work, same-source
quality/byte comparisons and same-reference subsets. Packet syntax is unchanged
AR03/AF03. The file contains no FPGA cycle schedule or hardware FPS claim.
