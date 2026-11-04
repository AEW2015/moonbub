"""Record the webcam microphone for each AV session observed in a serial log.

Owns no serial port and changes no receiver setting. Capture starts on an
audio-enabled START, stops after STOP plus a short tail, then re-arms. Raw
room audio stays in the selected local evidence directory.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import wave


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


class Recorder:
    def __init__(self, output, *, device="Microphone (Razer Kiyo)", max_seconds=300,
                 tail_seconds=2, popen=subprocess.Popen, clock=time.monotonic):
        self.output = Path(output)
        self.output.mkdir(parents=True, exist_ok=False)
        self.device, self.max_seconds, self.tail_seconds = device, max_seconds, tail_seconds
        self.popen, self.clock = popen, clock
        self.active = None
        self.records = []
        self._index("ARMED")

    def _index(self, state):
        data = {"state": state, "updated_utc": utc(), "device": self.device,
                "sessions": self.records, "scope": "Local acoustic capture; no serial ownership or firmware changes"}
        (self.output / "monitor.json").write_text(json.dumps(data, indent=2) + "\n")

    def start(self, line):
        if self.active:
            self.finish("new_audio_start_before_previous_close")
        number = len(self.records) + 1
        stem = self.output / f"session-{number:03d}"
        record = {"status": "STARTING", "trigger": line.strip(), "started_utc": utc(),
                  "wav": str(stem.with_suffix('.wav')), "startup_coverage": "FFmpeg device-open delay is not covered"}
        self.records.append(record)
        error = stem.with_suffix('.ffmpeg.log').open('wb')
        command = ["ffmpeg", "-hide_banner", "-loglevel", "warning", "-f", "dshow",
                   "-i", "audio=" + self.device, "-t", str(self.max_seconds), "-ac", "1",
                   "-ar", "16000", "-c:a", "pcm_s16le", "-n", record["wav"]]
        try:
            process = self.popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                                 stderr=error, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError as exc:
            error.close()
            record.update(status="FAILED_TO_START", error=str(exc), finished_utc=utc())
            self._index("ARMED")
            return
        self.active = {"process": process, "error": error, "record": record,
                       "started": self.clock(), "stop_at": None, "stop_reason": None}
        record["status"] = "CAPTURING"
        self._index("CAPTURING")
        print("MIC_CAPTURE_STARTED " + record["wav"], flush=True)

    def observe(self, line):
        if "av result=active audio_enabled=true" in line:
            self.start(line)
        elif self.active and any(token in line for token in
                                ("av result=stopped", "av result=lease_expired", "av result=worker_stopped")):
            self.active["record"]["stop_trigger"] = line.strip()
            self.active["stop_at"] = self.clock() + self.tail_seconds
            self.active["stop_reason"] = "receiver_session_ended"

    def poll(self):
        if not self.active:
            return
        active = self.active
        if active["stop_at"] is not None and self.clock() >= active["stop_at"]:
            self.finish(active["stop_reason"])
        elif self.clock() - active["started"] >= self.max_seconds:
            self.finish("capture_time_limit")
        elif active["process"].poll() is not None:
            self.finish("microphone_process_ended")

    def finish(self, reason):
        if not self.active:
            return
        active, self.active = self.active, None
        process, record = active["process"], active["record"]
        forced = False
        try:
            if process.poll() is None:
                try:
                    process.stdin.write(b'q\n')
                    process.stdin.flush()
                except (OSError, ValueError):
                    pass
            try:
                code = process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                forced = True
                process.terminate()
                try:
                    code = process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    code = process.wait(timeout=5)
        finally:
            active["error"].close()
            if process.stdin:
                process.stdin.close()
        record.update(finished_utc=utc(), reason=reason, returncode=code, forced_termination=forced)
        wav = Path(record["wav"])
        valid = False
        if wav.exists():
            record.update(bytes=wav.stat().st_size, sha256=hashlib.sha256(wav.read_bytes()).hexdigest())
            try:
                with wave.open(str(wav), 'rb') as audio:
                    record.update(channels=audio.getnchannels(), sample_rate=audio.getframerate(),
                                  duration_seconds=audio.getnframes() / audio.getframerate())
                    valid = audio.getnframes() > 0
            except (wave.Error, EOFError):
                pass
        record["status"] = "CAPTURED" if code == 0 and valid and not forced else "FAILED_OR_PARTIAL"
        if reason not in ("receiver_session_ended", "recorder_selfcheck"):
            record["coverage_partial"] = True
        self._index("ARMED")
        print("MIC_CAPTURE_FINISHED " + json.dumps(record), flush=True)


def request_status(path):
    if path is not None and not path.exists():
        temporary = path.with_suffix('.acoustic.tmp')
        temporary.write_text('s', encoding='ascii')
        os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--query-file', type=Path)
    parser.add_argument('--duration', type=float, default=3600)
    parser.add_argument('--max-session-seconds', type=float, default=300)
    args = parser.parse_args()
    if not 0 < args.duration <= 3600 or not 0 < args.max_session_seconds <= 300:
        parser.error('Monitor duration must be1..3600s and each capture1..300s')
    recorder = Recorder(args.output, max_seconds=args.max_session_seconds)
    deadline, next_status = time.monotonic() + args.duration, 0
    try:
        with args.source.open('r', encoding='utf-8') as source:
            source.seek(0, 2)
            print('MIC_MONITOR_ARMED rearm=every_audio_session device=' + recorder.device, flush=True)
            while time.monotonic() < deadline:
                line = source.readline()
                if line:
                    recorder.observe(line)
                    if '# USB_CAPTURE_FINISHED' in line:
                        break
                was_active = recorder.active is not None
                recorder.poll()
                if was_active and recorder.active is None:
                    request_status(args.query_file)
                if recorder.active and time.monotonic() >= next_status:
                    request_status(args.query_file)
                    next_status = time.monotonic() + 2
                if not line:
                    time.sleep(.1)
    finally:
        recorder.finish('monitor_ended')
        request_status(args.query_file)
        recorder._index('CLOSED')


if __name__ == '__main__':
    main()
