# Stale-upload hazard reachability

The retained standalone and actual CSR tests demonstrate a public-interface
hazard. They do **not** demonstrate reachability through the current physical
transport. The direct CSR harness can drive consecutive core bus writes, which
is a wider input schedule than the present bridge can emit.

For `cu71_bus_cdc_split` (`56628dc5…409596b`), `core_write=consume`,
`consume=fetched && read_state==0`, and a consumed beat assigns `fetched<=0`.
The same edge cannot also fetch because `fetch` requires `!fetched`. Thus every
core_write is followed by a core cycle with core_write=0. Reset also clears
fetched. This is a source-level one-step invariant, not a new formally executed
proof or physical measurement.

The CSR accepts opcode4 by setting `command_state<=DISCARD_PACKET` on its bus
write edge. Its next core edge executes DISCARD and unconditionally calls
finish, returning command_state to IDLE. That next edge is precisely the bridge
gap cycle. Therefore this exact bridge cannot present the upload write needed
for the demonstrated overlap. The fixed metadata/command/read queue ordering
and the reviewed v36 driver's wait-for-ACK and exact-written-count loops are
additional constraints, rather than assumptions used in the safe stager tests.

Safety-v002 deliberately closes the hazard at the public CSR and standalone
stager interfaces so correctness does not depend on this transport bubble.
This matters if a future bridge supports consecutive consumed writes or another
client drives the CSR directly. No installed-device failure is attributed to
this hazard, and no physical bridge reproduction is claimed.
