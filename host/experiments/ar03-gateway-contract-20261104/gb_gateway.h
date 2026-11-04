#ifndef GB_GATEWAY_H
#define GB_GATEWAY_H
#include <stddef.h>
#include <stdint.h>

/* Offline native port building block. No networking, DMA or credit mutation. */
typedef struct {
    uint32_t epoch, frame, total, body_crc;
    uint64_t nonce;
    uint16_t slot;
    uint8_t kind;
} gb_frame_control;
typedef struct {
    uint32_t epoch, frame, total, complete_crc, body_crc, token_header_crc;
    uint64_t sequence;
    uint16_t packet_slot, index, count, payload_bytes;
} gb_data_route;

/* 0 success; -1 invalid input. On failure, leave output unchanged.
 * expected_epoch is supplied by the caller; production negotiation is absent. */
int gb_parse_fg19(const uint8_t *, size_t, uint32_t expected_epoch, gb_frame_control *);
/* Serialize a grammatical control to exactly 36 bytes. Returns 36 or -1;
 * output remains unchanged on error. Does not authorize sending a reply. */
int gb_write_fg19(const gb_frame_control *, uint8_t *, size_t capacity);
int gb_parse_data(const uint8_t *, size_t, uint32_t expected_epoch, gb_data_route *);
/* Route binding alone is insufficient for admission: caller must also hold
 * the matching frame grant and packet permit, and have real FIFO capacity. */
int gb_route_matches(const gb_frame_control *, const gb_data_route *);
#endif
