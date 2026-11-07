# DYN1 lab uploader with initial receiver wait

No wire/codec/FPGA/ESP32 change. This uploader extends only the wait for the first KEY chunk's stored-prefix ACK when explicitly requested. Once storage begins, normal per-chunk timeouts and actual-presentation semantics remain. It never retries a complete session after an uncertain outcome. Repeated first datagrams carry identical session/frame/capture/offset/body and are idempotent in the existing receiver.

The first V41 trial did not stage a frame: receiver ready at2026-11-07T16:47:16.532991Z, first-frame deadline at16:49:16.633093Z, resultDeadline/15reads/0writes. Sender reported09:51:03?09:51:14Denver. These wall-clock records indicate a missed window; host/receiver clocks were not cross-calibrated and no cross-machine monotonic subtraction is used. Socket reception/discard counters were not present, so RF arrival and malformed/ignored-packet counts are unknown. Native minimum-free sentinel4294967295 means unobserved, not4GiBfree.

For the next controlled attempt, cold boot the installed V41 normally, prepare the unchanged original fixtures and start this uploader waiting BEFORE the receiver is armed. The operator reports its printed session/source-port line. The receiver agent then verifies/programs V023 and arms USB~ while the uploader continues waiting for that first ACK. No further manual START handoff is required once this ordering has explicitly been arranged.

```powershell
python host/dy71-lab/dy71_fixture_sender.py --receiver 192.168.0.157 --bind 192.168.0.47 --initial-wait-seconds 600 --log fresh-key-p.jsonl packet0.cu66 packet1.cu66
```

Use normal argument spacing: `--receiver 192.168.0.157`, `--bind 192.168.0.47`, `--initial-wait-seconds 600`. Only original KEY/P; no JPEG/video/audio/AV. Sender logs the bound source IP/port, destination, session and initial timeout before transmitting. Wait for actual status2; any later timeout or status3 stops the trial without a whole-session retry.

Four host tests pass, including byte-exact framing, original inner CRC validation, lost-final-storage-ACK recovery and late receiver startup with duplicate initial packets. These are software/localhost results, not a physical playback pass.

Follow-up firmware work: keep a reusable central Wi-Fi owner across a no-mutation idle timeout; do not consume/drop the sole modem and require a power cycle for safe rearm. Preserve exclusive FPGA/native ownership and do not force-release accepted state.
