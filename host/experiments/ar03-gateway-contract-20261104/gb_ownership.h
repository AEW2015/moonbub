#ifndef GB_OWNERSHIP_H
#define GB_OWNERSHIP_H
#include "gb_gateway.h"

#define GB_OWNERSHIP_FRAMES 2
#define GB_OWNERSHIP_MAX_FRAGMENTS 49
#define GB_OWNERSHIP_NO_SLOT UINT16_MAX

enum {
    GB_OWNERSHIP_GRANTED = 0,
    GB_OWNERSHIP_BUSY = 1,
    GB_OWNERSHIP_NO_REPLY = 2,
    GB_OWNERSHIP_SAFE_STOP = 3,
    GB_OWNERSHIP_INVALID = -1
};

typedef struct {
    uint8_t occupied, finished, physically_drained;
    uint8_t finish_reply_issued;
    gb_frame_control grant;
    uint64_t observed_fragments;
} gb_frame_owner;

/* Fixed epoch-1 receiver-side laboratory ledger. It owns only frame reservations
 * and records observed GF03 fragment indices. It does not implement packet
 * permits, FIFO capacity/admission, decode, publication, or production reset. */
typedef struct {
    gb_frame_owner slots[GB_OWNERSHIP_FRAMES];
    uint64_t last_request_sequence, released_sequence;
    uint8_t safe_stop, finish_ack;
} gb_ownership;

/* Cold construction only; this is not a ledger reset/rekey operation. */
void gb_ownership_init(gb_ownership *, int finish_ack);
/* Accept only sender-direction REQUEST/CANCEL/FINISH. Results are named above.
 * Reply is valid only for GRANTED/BUSY; it is unchanged for other results. */
int gb_ownership_control(gb_ownership *, const gb_frame_control *, gb_frame_control *reply);
/* Record only route-matched data observation; no packet permit is consumed. */
int gb_ownership_observe_data(gb_ownership *, const gb_data_route *);
/* Caller-provided physical drain event. Returns 1 when recorded for the exact
 * current owner, 0 for stale/unowned identity, -1 for invalid input, or 3 after
 * safe stop. This records drain only; it does not emit RELEASE. */
int gb_ownership_physical_drain(gb_ownership *, const gb_frame_control *);
/* Explicit identity-bound release poll. In ACK mode caller must first enqueue
 * the FINISHED reply returned by gb_ownership_control; no receipt ACK exists
 * on wire. Caller owns the send-order obligation. */
int gb_ownership_take_release(gb_ownership *, const gb_frame_control *expected_owner,
                              gb_frame_control *release);
/* Unknown outcome is a sticky safe stop and deliberately retains both owners. */
void gb_ownership_safe_stop(gb_ownership *);
unsigned gb_ownership_count(const gb_ownership *);

#endif
