# First physical audio tone —2026-11-03

Audio reaches the FPGA and produces a recorded acoustic tone. Playback is
**not yet clean**:13underrun events occurred during the10-second audio-only run.
Video and virtual Xbox injection remained off; receiver configuration unchanged.

Host reported source192.168.0.47:59499, cookie7f9b475dd3cb7ed2 and944sent blocks.
Its last MSI1 showed942accepted,0rejected/unconfirmed,1142queued PCMframes,
474067played and13lifetime underruns. Receiver final stable snapshots after
STOP resolve the final two sends:

| Receiver counter afterSTOP | Value |
|---|---:|
|Accepted audio blocks|944|
|Rejected or unconfirmed blocks|0|
|Queued PCMframes|0|
|Played PCMframes|475721|
|Audio underruns, lifetime/run increase|13/13|
|Audio sequence-gap counter|9|
|Malformed packets/socket errors|0/0|
|Core faults/overflow/transport overflow|0/0/0|
|Video/LCD underruns|0|
|Power-save entry/restore errors|0/0|

STOP was recorded at01:37:46.879UTC onNovember4 (November3evening inDenver),
and power-save mode restored to its captured value1. The FIFO is empty and AV
session inactive. All944host-reported sends were admitted. The9audio sequence
gaps do not establish network loss; sender-side skipped sequence IDs need review.

944×505=476720PCMframes were admitted;475721were consumed beforeSTOP.
The999not consumed are consistent with immediate final flush. This is not a
claim that all admitted samples were audibly played. Underruns were already6
around2seconds and12around8seconds, so they were not only an end-of-test event.

## Acoustic evidence

The mono Razer Kiyo microphone recorded11.953seconds. A strong660Hz component
is approximately40dB above the postSTOP background in250ms narrow-band windows.
The440Hz component is weaker, approximately16dB above its postSTOP background
and27dB below660Hz in this microphone geometry. These are acoustic observations,
not calibrated loudness or proof of left/right speaker routing.

Several brief tone-level dips are visible, including candidate20–30ms spans.
They are consistent with playback interruptions; the room recording does not
reliably classify clicks or map all13underruns individually. A large transient
at recording startup must not be assigned to the handheld without more evidence.
Mono capture cannot establish stereo spatial separation. Channel-isolated tests
are the next way to check left/right routing.

The receiver workspace retains the WAV, microphone metadata, analysis JSON/plot
and hashed serial snapshot under
`evidence/v21-av-hardware-20261103/tone-first/` and
`firmware/evidence/v21-av-tone1-mic-20261103.*`. Raw room audio is not published.

Next: inspect the same host run's encoded/queued/dropped blocks, sequence range
and send-gap timing before changing receiver firmware or FPGA. Then test
channels individually and a controlled jitter/prefill adjustment, retaining
audio-only operation before adding5fpsvideo. Windows Xbox injection is separate
and still requires its driver/test.
