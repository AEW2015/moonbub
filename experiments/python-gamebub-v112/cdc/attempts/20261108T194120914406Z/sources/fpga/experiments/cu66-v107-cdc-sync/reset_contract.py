#!/usr/bin/env python3
"""Small independent restart counterexample and reset-isolation model."""
import json

def model():
    # Peer clock stops with up=1. Running side resets for3localedges and then
    # resumes, while stopped peer cannot synchronously clear its previous up.
    stale_up=1
    sampled=[0,0]
    for _ in range(3):sampled=[0,0]
    for _ in range(2):sampled=[stale_up,sampled[0]]
    assert sampled[1]==1  # all-synchronous up would incorrectly unblock here
    # A dedicated async notification clears without the stopped peer's clock.
    notified=0;sampled=[0,0]
    for _ in range(30):
        sampled=[notified,sampled[0]]
        assert sampled[1]==0
    # Reset stays high for3resumed local edges. All pointer/issue/reservation
    # state resets on the first edge and remains empty for the next two.
    held=[1,1,1]
    pointer,issue,up=7,1,0
    for _ in range(3):
        assert held[2]==1
        pointer=issue=up=0
        held=[0,held[0],held[1]]
    assert pointer==issue==up==0 and held[2]==0
    up=1
    return dict(schema='v107-cdc-sync-reset-contract-v1',status='PASS',unsafe_sync_up_stale_counterexample=True,async_notification_blocks_stopped_peer=True,local_reset_edges_before_recovery=3,scope='Protocol/model reasoning, not RTL, primitive reset timing, four-state or hardware proof.')
if __name__=='__main__':print(json.dumps(model(),sort_keys=True))
