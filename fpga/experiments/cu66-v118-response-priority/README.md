# Reachable reference-response ownership tests

This auxiliary test uses the unchanged qualified V118 production reconstruction RTL and probe. The new C++ bench is a reversible extension of the qualified focused bench; every original `need` oracle remains and the entire original suite runs again.

There is no natural simultaneous `response_failure` and residual-bank commit: `response_failure` requires an accepted physical response, `ref_rsp_ready` requires `ref_pending`, and reconstruction only acquires a reference lease after the final residual has committed and both residual pipeline stages drained. The test does not deposit an impossible pending owner into private state.

Instead it checks four unsolicited wrong/error response offers during actual good residual commits at indices0,7,61 and63. `ref_rsp_ready` and `response_failure` must remain0, the valid commit must proceed, and no physical debt or fault may appear. Every naturally executed RESIDUAL edge also asserts that no physical reference lease exists.

Two additional legitimate REF_WAIT tests inject a wrong epoch or a matching error response into a real accepted reference lease. The first fault must be3, owners/publication and pending acceptance/copy eligibility must revoke, committed residual count must not advance, wrong tags must retain the physical lease until a real matching drain, and matching errors must retire it. The first fault remains sticky while draining, followed by a full canonical retry with independent pixel checks.

The auxiliary runner requires six complete frames and62 directed checks per seed, including all original four-beat cancellation and residual-pipeline tests. It records strict Verilator execution intent before launch and preserves failures/source snapshots under `experiments/python-gamebub-v118/response-priority/`. Passing this suite covers reachable response ownership and priority behavior; it does not demonstrate an unreachable simultaneous response-fault/residual-commit collision or physical hardware timing.
