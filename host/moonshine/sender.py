"""Paced experimental MJPEG test source. It is not a Sunshine pairing client."""
import argparse
from io import BytesIO
import json
import queue
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path
from PIL import Image, ImageGrab
from .encoding import encode
from .protocol import MAX_FRAME, VIDEO, packets, parse_feedback
from .input import InputSession, KeyboardInjector, WindowsKeyboard


class LatestFrames:
    """One latest raw frame, overwritten by capture rather than accumulated."""
    def __init__(self):
        self.queue = queue.Queue(maxsize=1)
        self.replaced = 0
        self.error = None
        self.ended = False
        self.stop = threading.Event()
        self.process = None

    def put(self, image):
        item = (time.time_ns() // 1000, image)
        try:
            self.queue.put_nowait(item)
        except queue.Full:
            try:
                self.queue.get_nowait()
            except queue.Empty:
                pass
            self.replaced += 1
            self.queue.put_nowait(item)

    def start(self, args):
        self.thread = threading.Thread(target=self._run, args=(args,), daemon=True)
        self.thread.start()

    def _run(self, args):
        try:
            if args.clip:
                executable = shutil.which(args.ffmpeg)
                if executable is None:
                    raise RuntimeError("ffmpeg not found; install it or use --image/--desktop")
                command = [executable, "-nostdin", "-loglevel", "error", "-re", "-i", str(args.clip),
                           "-an", "-sn", "-dn", "-vf", f"fps={args.fps},scale=720:480:force_original_aspect_ratio=decrease,pad=720:480:(ow-iw)/2:(oh-ih)/2:black",
                           "-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1"]
                self.process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None)
                frame_size = 720 * 480 * 3
                while not self.stop.is_set():
                    data = bytearray()
                    while len(data) < frame_size:
                        part = self.process.stdout.read(frame_size - len(data))
                        if not part:
                            break
                        data.extend(part)
                    if len(data) != frame_size:
                        break
                    self.put(Image.frombytes("RGB", (720, 480), bytes(data)))
                code = self.process.wait()
                if code and not self.stop.is_set():
                    raise RuntimeError(f"ffmpeg exited {code}")
            else:
                image = Image.open(args.image).convert("RGB") if args.image else None
                next_capture = time.perf_counter()
                while not self.stop.is_set():
                    self.put(ImageGrab.grab().convert("RGB") if args.desktop else image.copy())
                    next_capture += 1 / args.fps
                    self.stop.wait(max(0, next_capture - time.perf_counter()))
        except Exception as exc:
            self.error = str(exc)
        finally:
            self.ended = True

    def close(self):
        self.stop.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.thread.join(timeout=2)


def budgeted_encode(image, quality, target_bytes, min_quality=15):
    """Bound quality before transmission; never let oversized frames queue."""
    while True:
        jpeg = encode(image, quality=quality, subsampling="420")
        wire_size = len(jpeg) + ((len(jpeg) + 1023) // 1024) * VIDEO.size
        if wire_size <= target_bytes and len(jpeg) <= MAX_FRAME:
            return jpeg, quality
        if quality <= min_quality:
            return None, quality
        quality = max(min_quality, quality - 5)


def run(args):
    if not 1 <= args.fps <= 60 or not 1 <= args.quality <= 95 or args.mbps <= 0 or args.duration <= 0:
        raise ValueError("fps1..60, quality1..95, positive Mbps/duration required")
    inject_keys = getattr(args, "inject_keys", False)
    injector = KeyboardInjector(WindowsKeyboard()) if inject_keys else None
    sink = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sink.connect((args.host, args.port))
    sink.setblocking(False)
    capture = LatestFrames()
    capture.start(args)
    began = time.perf_counter()
    deadline = began
    frame_id = 0
    quality = args.quality
    metrics = {"mode": "standalone MSV1 test sender (not Sunshine)", "canvas": [720, 480],
               "codec": "JPEG SOF0 YCbCr420 standard DHT", "requested_fps": args.fps, "wire_budget_mbps": args.mbps,
               "sent_frames": 0, "sent_bytes": 0, "budget_drops": 0, "late_drops": 0, "feedback_packets": 0,
               "malformed_feedback": 0, "latest_receiver": None, "feedback_rtt_ms_max": None,
               "max_capture_age_ms_at_send": 0, "quality_initial": quality}
    input_file = Path(args.input_jsonl).open("w") if args.input_jsonl else None
    last_reported_drops = 0
    stamps = {}

    def input_event(mask, reason):
        if input_file:
            input_file.write(json.dumps({"host_time_us": time.time_ns() // 1000, "buttons": mask, "reason": reason}) + "\n")
            input_file.flush()

    inputs = InputSession(injector=injector, logger=input_event)

    def receive_feedback():
        nonlocal quality, last_reported_drops
        while True:
            try:
                data = sink.recv(2048)
            except BlockingIOError:
                break
            except OSError:
                inputs.disconnect("socket error")
                raise
            try:
                f = parse_feedback(data)
            except ValueError:
                metrics["malformed_feedback"] += 1
                continue
            last_feedback = time.perf_counter()
            metrics["feedback_packets"] += 1
            metrics["latest_receiver"] = vars(f)
            inputs.feedback(f.buttons, last_feedback)
            sent = stamps.pop(f.capture_us, None)
            if sent is not None:
                rtt = (last_feedback - sent) * 1000
                metrics["feedback_rtt_ms_max"] = max(metrics["feedback_rtt_ms_max"] or 0, rtt)
            if f.status or f.dropped_frames:
                # Immediate conservative decrease. We do not infer display FPS from ACKs.
                metrics["receiver_reported_drops"] = f.dropped_frames
            if f.status or f.dropped_frames != last_reported_drops:
                quality = max(min(15, quality), quality - 5)
            last_reported_drops = f.dropped_frames
        inputs.tick(time.perf_counter())

    try:
        while time.perf_counter() - began < args.duration:
            receive_feedback()
            now = time.perf_counter()
            if now < deadline:
                time.sleep(min(0.002, deadline - now))
                continue
            try:
                capture_us, image = capture.queue.get_nowait()
            except queue.Empty:
                if capture.ended:
                    break
                time.sleep(0.001)
                continue
            # Schedule after obtaining a fresh source frame. An empty capture
            # queue must not consume a whole output frame interval.
            deadline = max(deadline + 1 / args.fps, now + 1 / args.fps)
            frame_id = (frame_id + 1) & 0xffffffff
            jpeg, quality = budgeted_encode(image, quality, args.mbps * 1_000_000 / 8 / args.fps * 0.9,
                                             min_quality=min(15, quality))
            if jpeg is None:
                metrics["budget_drops"] += 1
                continue
            if time.perf_counter() >= deadline:
                metrics["late_drops"] += 1
                continue
            if args.save_first and metrics["sent_frames"] == 0:
                Path(args.save_first).write_bytes(jpeg)
            send_started = time.perf_counter()
            age = max(0, (time.time_ns() // 1000 - capture_us) / 1000)
            metrics["max_capture_age_ms_at_send"] = max(age, metrics["max_capture_age_ms_at_send"])
            stamps[capture_us] = send_started
            # Bound ACK bookkeeping even if there is no receiver.
            while len(stamps) > 128:
                stamps.pop(next(iter(stamps)))
            sent_frame = True
            cumulative = 0
            for datagram in packets(jpeg, frame_id, capture_us):
                send_at = send_started + cumulative / (args.mbps * 1_000_000 / 8)
                while time.perf_counter() < send_at:
                    receive_feedback()
                    time.sleep(min(0.001, max(0, send_at - time.perf_counter())))
                if time.perf_counter() >= deadline:
                    metrics["late_drops"] += 1
                    sent_frame = False
                    break
                try:
                    sent = sink.send(datagram)
                except BlockingIOError:
                    metrics["late_drops"] += 1
                    sent_frame = False
                    break
                except OSError:
                    inputs.disconnect("socket error")
                    raise
                metrics["sent_bytes"] += sent
                cumulative += sent
            metrics["sent_frames"] += int(sent_frame)
            if metrics["sent_frames"] and metrics["sent_frames"] % 30 == 0:
                print(json.dumps({"sent_frames": metrics["sent_frames"], "quality": quality,
                                  "receiver": metrics["latest_receiver"]}), flush=True)
        if capture.error:
            raise RuntimeError(capture.error)
    finally:
        try:
            inputs.disconnect("sender shutdown")
        finally:
            capture.close()
            sink.close()
        if input_file:
            input_file.close()
        elapsed = time.perf_counter() - began
        metrics.update(duration_seconds=elapsed, sender_completed_fps=metrics["sent_frames"] / elapsed,
                       sent_wire_mbps=metrics["sent_bytes"] * 8 / elapsed / 1_000_000,
                       capture_replacements=capture.replaced, quality_final=quality,
                       displayed_fps=None, end_to_end_latency_ms=None,
                       keyboard_injection=inject_keys,
                       limitations="Host send rate/ACK RTT only; no FPGA display measurement. Keyboard input requires explicit --inject-keys.")
        if args.metrics:
            Path(args.metrics).write_text(json.dumps(metrics, indent=2) + "\n")
        print(json.dumps(metrics, indent=2))
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("host", help="GameBub IPv4 address (experimental test-source firmware)")
    parser.add_argument("--port", type=int, default=5533)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--clip", type=Path, help="gameplay video; ffmpeg reads it in real time, audio disabled")
    source.add_argument("--image", type=Path, help="repeat a diagnostic image; not representative gameplay")
    source.add_argument("--desktop", action="store_true", help="capture desktop using Pillow ImageGrab")
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--fps", type=float, default=30)
    parser.add_argument("--quality", type=int, default=65)
    parser.add_argument("--mbps", type=float, default=12)
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--metrics", type=Path)
    parser.add_argument("--save-first", type=Path)
    parser.add_argument("--input-jsonl", type=Path, help="record input mask changes")
    parser.add_argument("--inject-keys", action="store_true", help="opt in to Windows keyboard injection: arrows,Z/X/A/S,Q/E,Enter/Space; focus the game manually")
    args = parser.parse_args()
    try:
        run(args)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(1, f"moonshine: {exc}\n")


if __name__ == "__main__":
    main()
