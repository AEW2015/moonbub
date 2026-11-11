#!/usr/bin/env python3
"""Bounded readiness wait; callers retain their original launch assertion."""
import time


def wait_ready(memory, samples):
    started = time.monotonic()
    deadline = started + 120.0
    while True:
        gate = memory()
        now = time.monotonic()
        ready = (gate['available_bytes'] >= 8*1024**3
                 and gate['psi_full_avg10'] < 1
                 and gate['combined_used_ratio'] < .85)
        samples.append(dict(elapsed_seconds=now-started, ready=ready, **gate))
        if ready or now >= deadline:
            return gate
        time.sleep(min(2.0, deadline-now))
