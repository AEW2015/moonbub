# Reachable reference-response cases

The auxiliary response suite uses the unchanged qualified V118 production reconstruction source and probe. It retains the complete focused benchmark and adds unsolicited responses during four real residual commits, natural residual/reference ownership checks, and legitimate reference mismatch/error with drain and complete retry.

`ref_rsp_ready` is `ref_pending`; residual collection precedes the reference request. An accepted physical reference failure cannot coincide with a valid residual commit in this architecture. No impossible private pending state is deposited to claim that coverage. Unsolicited response offers during residual work must remain unaccepted and leave the real commit intact. Accepted mismatched responses keep the physical lease until the matching response drains; a matching error retires the lease and reports the first fault. Retry uses real drain/ack behavior.

Reproduce after the selected reconstruction proof:

```bash
python3 scripts/cu66-v118/response_priority/qualify.py --run --root-grant ROOT_V118_RESPONSE
```

The first campaign passed both seeds. Native qualification separately requires its source-bound selected receipt. See [results](../../experiments/python-gamebub-v118/response-priority/results.json) and [derivation](../../fpga/experiments/cu66-v118-response-priority/derivation.json).
