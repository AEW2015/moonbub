#ifndef GAMEBUB_V97_PROTOCOL_C_H
#define GAMEBUB_V97_PROTOCOL_C_H
#include <stdint.h>
#include <stddef.h>
#define V97_FIFO_CAPACITY 2048u
#ifdef __cplusplus
extern "C" {
#endif
/* Return 0 success, 1 retry/WouldBlock, 2 abort/drain required, negative error.
   All input/output pointers must designate their stated valid storage. NULL is
   rejected. A returned stage pointer is valid until complete/reset/destroy;
   transfer_bytes has EXACT logical_len; staging_storage is diagnostic padding.
   complete is an authoritative ordered sink acceptance ACK. It is NOT a DMA
   kickoff ACK. After take_commit, matching ingress commit_complete is required.
   Observation is synchronous and ordered; use Rust probes for async queries. */
typedef struct { uint64_t token; uint32_t slot, logical_len, storage_len, reserved; } V97Transfer;
typedef struct { uint32_t epoch, fid, length, crc, core_generation, reserved; uint64_t capture_us; } V97Frame;
typedef struct { V97Frame frame; V97Transfer transfer; uint32_t index, offset, crc_complete, reserved; } V97Chunk;
void *v97_create(uint32_t opaque_profile_or_zero, uint32_t core_generation);
int v97_destroy(void *);
int v97_setup(void *, const uint8_t *, size_t, uint8_t *ack40);
int v97_observe_free(void *, uint32_t epoch, uint32_t core_generation, uint32_t actual_free);
int v97_receive(void *, const uint8_t *, size_t, V97Chunk *);
const uint8_t *v97_transfer_bytes(void *, const V97Transfer *);
const uint8_t *v97_staging_storage(void *, const V97Transfer *);
int v97_issue(void *, const V97Transfer *);
int v97_complete(void *, uint64_t token, int success);
int v97_take_commit(void *, V97Frame *);
int v97_commit_complete(void *, uint32_t epoch, uint32_t fid, uint32_t core_generation, int success);
int v97_abort_frame(void *);
int v97_reset(void *);
int v97_core_changed(void *, uint32_t core_generation);
int v97_drained(void *);
int v97_needs_drain(void *);
int v97_inflight(void *);
uint32_t v97_reserved_bytes(void *);
#ifdef __cplusplus
}
static_assert(sizeof(V97Transfer)==24, "V97Transfer ABI");
static_assert(sizeof(V97Frame)==32, "V97Frame ABI");
static_assert(sizeof(V97Chunk)==72, "V97Chunk ABI");
#endif
#endif
