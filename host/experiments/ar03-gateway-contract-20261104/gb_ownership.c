#include "gb_ownership.h"
#include <string.h>

enum { REQUEST = 1, CANCEL = 2, GRANT = 3, BUSY = 4,
       RELEASE = 5, CANCELED = 6, FINISH = 7, FINISHED = 8 };

static int identity_equal(const gb_frame_control *a, const gb_frame_control *b) {
    return a->epoch == b->epoch && a->frame == b->frame && a->nonce == b->nonce &&
           a->total == b->total && a->body_crc == b->body_crc && a->slot == b->slot;
}

static int control_valid(const gb_frame_control *c) {
    return c && c->epoch == 1 && c->kind >= REQUEST && c->kind <= FINISHED &&
           c->nonce != 0 && c->total != 0 && c->total <= 49152 &&
           (c->slot == 0 || c->slot == 1 || c->slot == GB_OWNERSHIP_NO_SLOT);
}

static gb_frame_control response(const gb_frame_control *in, uint8_t kind, uint16_t slot) {
    gb_frame_control out = *in;
    out.kind = kind;
    out.slot = slot;
    return out;
}

static int find_frame(const gb_ownership *ledger, uint32_t frame) {
    for (unsigned i = 0; i < GB_OWNERSHIP_FRAMES; ++i)
        if (ledger->slots[i].occupied && ledger->slots[i].grant.frame == frame)
            return (int)i;
    return -1;
}

static void free_owner(gb_ownership *ledger, unsigned slot) {
    uint64_t seq = ledger->slots[slot].grant.nonce;
    if (seq > ledger->released_sequence) ledger->released_sequence = seq;
    memset(&ledger->slots[slot], 0, sizeof(ledger->slots[slot]));
}

void gb_ownership_init(gb_ownership *ledger, int finish_ack) {
    if (ledger) {
        memset(ledger, 0, sizeof(*ledger));
        ledger->finish_ack = finish_ack != 0;
    }
}

int gb_ownership_control(gb_ownership *ledger, const gb_frame_control *in,
                         gb_frame_control *reply) {
    if (!ledger || !reply || !control_valid(in) ||
        (in->kind != REQUEST && in->kind != CANCEL && in->kind != FINISH)) return -1;
    if (ledger->safe_stop) return GB_OWNERSHIP_SAFE_STOP;

    gb_frame_control out;
    int index = find_frame(ledger, in->frame);
    if (in->kind == REQUEST) {
        if (index >= 0) {
            const gb_frame_owner *owner = &ledger->slots[index];
            if (identity_equal(&owner->grant, in)) out = response(in, GRANT, owner->grant.slot);
            else out = response(in, BUSY, GB_OWNERSHIP_NO_SLOT);
            *reply = out;
            return identity_equal(&ledger->slots[index].grant, in) ? 0 : 1;
        }
        uint64_t floor = ledger->last_request_sequence > ledger->released_sequence
                       ? ledger->last_request_sequence : ledger->released_sequence;
        if (in->nonce <= floor) {
            *reply = response(in, BUSY, GB_OWNERSHIP_NO_SLOT);
            return 1;
        }
        /* Frozen receiver advances the request serial before testing whether
         * the explicitly requested slot is available. */
        ledger->last_request_sequence = in->nonce;
        if (in->slot >= GB_OWNERSHIP_FRAMES || ledger->slots[in->slot].occupied) {
            *reply = response(in, BUSY, GB_OWNERSHIP_NO_SLOT);
            return 1;
        }
        gb_frame_owner owner;
        memset(&owner, 0, sizeof(owner));
        owner.occupied = 1;
        owner.grant = response(in, GRANT, in->slot);
        ledger->slots[in->slot] = owner;
        *reply = owner.grant;
        return 0;
    }

    if (in->slot >= GB_OWNERSHIP_FRAMES || index != (int)in->slot ||
        !identity_equal(&ledger->slots[in->slot].grant, in)) {
        *reply = response(in, BUSY, GB_OWNERSHIP_NO_SLOT);
        return 1;
    }
    gb_frame_owner *owner = &ledger->slots[in->slot];
    if (in->kind == CANCEL) {
        if (owner->observed_fragments) {
            *reply = response(in, BUSY, GB_OWNERSHIP_NO_SLOT);
            return 1;
        }
        out = response(in, CANCELED, in->slot);
        free_owner(ledger, in->slot);
        *reply = out;
        return 0;
    }

    owner->finished = 1; /* FINISH is a barrier, never physical drain. */
    if (!ledger->finish_ack) return 2;
    owner->finish_reply_issued = 1;
    out = response(in, FINISHED, in->slot);
    *reply = out;
    return 0;
}

int gb_ownership_observe_data(gb_ownership *ledger, const gb_data_route *route) {
    if (!ledger || !route || ledger->safe_stop || route->epoch != 1 ||
        route->frame == UINT32_MAX || !route->sequence || route->packet_slot >= 6 ||
        !route->total || route->total > 49152 || !route->count ||
        route->count > GB_OWNERSHIP_MAX_FRAGMENTS || route->index >= route->count ||
        route->count != (route->total + 1007u) / 1008u) return -1;
    uint32_t remaining = route->total - (uint32_t)route->index * 1008u;
    uint32_t payload = remaining < 1008u ? remaining : 1008u;
    if (route->payload_bytes != payload) return -1;

    int index = find_frame(ledger, route->frame);
    if (index < 0) return 0;
    if (ledger->slots[index].physically_drained) return 0;
    gb_frame_control grant = ledger->slots[index].grant;
    grant.kind = GRANT;
    if (!gb_route_matches(&grant, route)) return 0;
    ledger->slots[index].observed_fragments |= UINT64_C(1) << route->index;
    return 1;
}

int gb_ownership_physical_drain(gb_ownership *ledger, const gb_frame_control *identity) {
    if (!ledger || !control_valid(identity) ||
        (identity->kind != GRANT && identity->kind != FINISH)) return -1;
    if (ledger->safe_stop) return GB_OWNERSHIP_SAFE_STOP;
    int index = find_frame(ledger, identity->frame);
    if (index < 0 || !identity_equal(&ledger->slots[index].grant, identity)) return 0;
    gb_frame_owner *owner = &ledger->slots[index];
    owner->physically_drained = 1;
    return 1;
}

int gb_ownership_take_release(gb_ownership *ledger, const gb_frame_control *expected,
                              gb_frame_control *release) {
    if (!ledger || !release || !control_valid(expected) ||
        (expected->kind != GRANT && expected->kind != FINISHED)) return -1;
    if (ledger->safe_stop) return GB_OWNERSHIP_SAFE_STOP;
    if (expected->slot >= GB_OWNERSHIP_FRAMES) return 0;
    gb_frame_owner *owner = &ledger->slots[expected->slot];
    if (!owner->occupied || !identity_equal(&owner->grant, expected)) return 0;
    if (!owner->occupied || !owner->finished || !owner->physically_drained ||
        (ledger->finish_ack && !owner->finish_reply_issued)) return 0;
    gb_frame_control out = response(&owner->grant, RELEASE, expected->slot);
    free_owner(ledger, expected->slot);
    *release = out;
    return 1;
}

void gb_ownership_safe_stop(gb_ownership *ledger) {
    if (ledger) ledger->safe_stop = 1;
}

unsigned gb_ownership_count(const gb_ownership *ledger) {
    if (!ledger) return 0;
    return (unsigned)ledger->slots[0].occupied + (unsigned)ledger->slots[1].occupied;
}
