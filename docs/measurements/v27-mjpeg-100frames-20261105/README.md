# v27 MSV1 100-frame hardware test

Host IDs2,000,000?2,000,099:100 complete sends,98 accepted and2 rejected.
Receiver:98 received,98 decoded,98 presented,2 dropped. Application packet-queue
loss0; high-water23/32. Core completed98/dropped2; fault, overflow, underrun and
transport-overflow counters all0. No reboot observed; post-run uptime1503.195s.

| Frame | Explicit reason | First expected offset | First observed offset |
| --- | --- | ---: | ---: |
| 2000079 | Invalid/lost frame: Sequence |20480|21504|
| 2000084 | Invalid/lost frame: Sequence |21504|23552|

These are sequence discontinuities, with no recorded application queue loss.
The capture does not distinguish missing from reordered datagrams or locate
where they were lost. Exact warning records are retained in failure-records.txt.
The latest status still reads `Invalid/lost frame: Sequence`; it is the retained
error text, while the core reports READY and98 presentations.

Installed app is v27-diag-headroom-20261105, runtime ELF SHA256
`5cdf81d4e853172a8f7d610f035438675c1d7b65687b0ccea41adb8cdb5ffdd2`.
Retained build50/overlap/32slots; receiver192.168.0.157:5533, sender192.168.0.47.
The screenshot is retained locally, not published: it shows a held streamed
Windows desktop. No continuous camera video was captured during this run, so
continuous motion and absence of freezes are not independently confirmed.
Receiver recording remains active; no reset/disconnect/reprogram was performed
for post-run queries. Diagnostic-page loss/concatenation remains an observability
limitation. This is legacy JPEG, not a CP23 or30fps acceptance result.
