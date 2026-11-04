# PC loopback audio results — November 3, 2026

Two one-minute audio-only runs completed with receiver firmware, FPGA, DAC
volume, timing and margin unchanged. Gain is a host-reported parameter.

| Measurement | First run | Recorded repeat |
|---|---:|---:|
| Host source port | 61347 | 56641 |
| Host gain | 0.25 | 0.75 |
| Host-reported blocks sent | 5,530 | 5,571 |
| Final accepted blocks | 5,477 | 5,542 |
| Final rejected/unconfirmed blocks | 4 | 11 |
| Final queued PCM frames | 0 | 0 |
| Final lifetime played frames | 3,239,425 | 6,036,993 |
| Played-frame increase | 2,763,704 | 2,797,568 |
| Lifetime audio underruns | 30 | 45 |
| Underrun increase | 17 | 15 |
| Audio sequence-gap counter | 73 | 33 |
| Sent minus accepted and rejected | 49 | 18 |
| Webcam microphone recording | Not captured | 61 seconds captured |

The first cookie was `cef6deba49b36459`; the repeat cookie was
`50f7753168335cc7`. The repeat's final two admissions postdate the host's last
MSI1 count of 5,540. Both receiver sessions ended cleanly, restored the captured
Wi-Fi power-save mode, and left zero core faults, malformed packets, socket
errors or transport overflow. The unexplained 49/18 blocks cannot be assigned
to network loss from these aggregate counters alone.

The gains differ, so this is not a controlled gain A/B. The repeat admitted
2,798,710 PCM frames and consumed 2,797,568; 1,142 unconsumed frames are
consistent with STOP flushing the remaining FIFO. Its 15 new underruns show
playback starvation; clean sustained audio is not established.

## Acoustic capture

The original microphone job captured only the earlier short tone and was not
re-armed for the first loopback run. There is no sound-quality evidence for
that minute. This gap is preserved rather than substituting the tone recording.

The replacement recorder automatically starts for each audio-enabled session,
captures through STOP plus two seconds, then re-arms. Five lifecycle tests and
an actual webcam-microphone open/record/close check passed. It owns no serial
port and changes no firmware or FPGA setting. FFmpeg device-open startup time
is not covered; each capture is capped at five minutes by the current command.

The repeat recording used **Microphone (Razer Kiyo)**, mono, 16 kHz signed PCM,
61 seconds, SHA-256
`1962f61248ba9329aa47bf94e4a94bf74db289602255fc0deb84438621aade24`.
Raw room audio remains local on the receiver workstation:
`firmware/evidence/v21-av-acoustic-auto-20261103/session-001.wav`.

The recording contains varying acoustic program content. Its peak is about
7.2% of full scale with no near-full-scale samples, so no microphone ADC clipping
was observed. This does not establish comfortable listener loudness or rule out
DAC/speaker distortion. The unknown variable source and room transients prevent
reliable attribution of individual clicks or music pauses to receiver glitches.
Mono capture cannot establish left/right spatial separation.

Next: compare the sender's encoded/queued/stale-drop/sequence/send-gap records
with the receiver's admission and underrun progression. A localhost reference
sender pacing benchmark is also running. Keep the receiver configuration fixed
until those results identify the next controlled experiment.
