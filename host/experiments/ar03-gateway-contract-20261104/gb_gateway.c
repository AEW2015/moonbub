#include "gb_gateway.h"
#include <string.h>

static uint16_t be16(const uint8_t *p) {
    return (uint16_t)(((uint16_t)p[0] << 8) | p[1]);
}
static uint32_t be32(const uint8_t *p) {
    return ((uint32_t)p[0] << 24) | ((uint32_t)p[1] << 16) |
           ((uint32_t)p[2] << 8) | p[3];
}
static uint64_t be64(const uint8_t *p) {
    return ((uint64_t)be32(p) << 32) | be32(p + 4);
}
static void put16(uint8_t *p, uint16_t v) {
    p[0] = (uint8_t)(v >> 8); p[1] = (uint8_t)v;
}
static void put32(uint8_t *p, uint32_t v) {
    p[0] = (uint8_t)(v >> 24); p[1] = (uint8_t)(v >> 16);
    p[2] = (uint8_t)(v >> 8); p[3] = (uint8_t)v;
}
static uint32_t crc32(const uint8_t *p, size_t n) {
    uint32_t crc = UINT32_MAX;
    for (size_t i = 0; i < n; ++i) {
        crc ^= p[i];
        for (unsigned j = 0; j < 8; ++j)
            crc = (crc >> 1) ^ (UINT32_C(0xedb88320) & (0u - (crc & 1u)));
    }
    return ~crc;
}
int gb_parse_fg19(const uint8_t *p, size_t n, uint32_t epoch, gb_frame_control *out) {
    if (!p || !out || n != 36 || memcmp(p, "FG19", 4) || p[4] != 1 ||
        crc32(p, 32) != be32(p + 32)) return -1;
    gb_frame_control v = {0};
    v.kind = p[5]; v.slot = be16(p + 6); v.epoch = be32(p + 8);
    v.frame = be32(p + 12); v.nonce = be64(p + 16);
    v.total = be32(p + 24); v.body_crc = be32(p + 28);
    if (v.epoch != epoch || v.kind < 1 || v.kind > 8 || !v.nonce ||
        !v.total || v.total > 49152 ||
        (v.slot != 0 && v.slot != 1 && v.slot != UINT16_MAX)) return -1;
    /* Match frozen FG19 grammar, including NO_SLOT for laboratory controls.
     * Endpoint direction/state policy must reject controls without a real owner. */
    if ((v.kind == 4 && v.slot != UINT16_MAX) ||
        ((v.kind == 1 || v.kind == 3 || v.kind == 5 || v.kind == 8) &&
         v.slot == UINT16_MAX)) return -1;
    *out = v;
    return 0;
}
int gb_parse_data(const uint8_t *p, size_t n, uint32_t epoch, gb_data_route *out) {
    if (!p || !out || n < 47 || n > 1055) return -1;
    gb_data_route v = {0};
    v.epoch = be32(p); v.packet_slot = be16(p + 4);
    v.sequence = be64(p + 8);
    if (v.epoch != epoch || v.packet_slot >= 6 || be16(p + 6) || !v.sequence ||
        memcmp(p + 16, "GF03", 4) || p[20] != 3 || be32(p + 21) != epoch) return -1;
    v.frame = be32(p + 25); v.total = be32(p + 29);
    v.index = be16(p + 33); v.count = be16(p + 35);
    v.payload_bytes = be16(p + 37); v.complete_crc = be32(p + 39);
    v.body_crc = be32(p + 43);
    if (v.frame == UINT32_MAX || !v.total || v.total > 49152 ||
        v.count != (v.total + 1007u) / 1008u || v.index >= v.count) return -1;
    uint32_t remaining = v.total - (uint32_t)v.index * 1008u;
    uint32_t length = remaining < 1008u ? remaining : 1008u;
    if (v.payload_bytes != length || n != 47u + length) return -1;
    /* Not a payload integrity check. Whole-frame CRC is checked at assembly. */
    v.token_header_crc = crc32(p, 47);
    *out = v;
    return 0;
}
int gb_write_fg19(const gb_frame_control *v, uint8_t *out, size_t capacity) {
    if (!v || !out || capacity < 36) return -1;
    uint8_t p[36];
    memcpy(p, "FG19", 4); p[4] = 1; p[5] = v->kind;
    put16(p + 6, v->slot); put32(p + 8, v->epoch); put32(p + 12, v->frame);
    put32(p + 16, (uint32_t)(v->nonce >> 32)); put32(p + 20, (uint32_t)v->nonce);
    put32(p + 24, v->total); put32(p + 28, v->body_crc);
    put32(p + 32, crc32(p, 32));
    gb_frame_control checked;
    if (gb_parse_fg19(p, sizeof(p), v->epoch, &checked)) return -1;
    memcpy(out, p, sizeof(p));
    return 36;
}
int gb_route_matches(const gb_frame_control *f, const gb_data_route *d) {
    return f && d && f->kind == 3 && f->slot < 2 &&
           f->epoch == d->epoch && f->frame == d->frame &&
           f->total == d->total && f->body_crc == d->body_crc;
}
