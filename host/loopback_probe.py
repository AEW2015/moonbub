"""Exercise real UDP sender and reference sink on this PC, never the GameBub."""
import argparse
from io import BytesIO
import json
from pathlib import Path
import socket
import threading
import time
from PIL import Image
from moonshine.encoding import validate_jpeg
from moonshine.protocol import FEEDBACK, Reassembler
from moonshine.sender import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--duration", type=float, default=10)
    parser.add_argument("--clip", type=Path)
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "evidence" / "loopback.json")
    args = parser.parse_args()
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind(("127.0.0.1", 0))
    server.settimeout(0.1)
    port = server.getsockname()[1]
    stop = threading.Event()
    sink = Reassembler()
    metrics = {"scope": "PC localhost UDP sender to Python/Pillow reference sink; no Wi-Fi/QSPI/FPGA/display",
               "received_frames": 0, "received_bytes": 0, "errors": [], "capture_age_ms_max": 0,
               "source": "synthetic moving clip" if args.clip else "static deterministic pattern (not gameplay)"}
    start = time.perf_counter()

    def receive():
        while not stop.is_set():
            try:
                data, peer = server.recvfrom(2048)
            except (socket.timeout, ConnectionResetError):
                continue
            metrics["received_bytes"] += len(data)
            try:
                result = sink.accept(data)
                if result is None:
                    continue
                packet, jpeg = result
                validate_jpeg(jpeg)
                decoded = Image.open(BytesIO(jpeg))
                decoded.load()
                if decoded.size != (720, 480):
                    raise ValueError("decoded canvas mismatch")
                metrics["received_frames"] += 1
                age = (time.time_ns() // 1000 - packet.capture_us) / 1000
                metrics["capture_age_ms_max"] = max(metrics["capture_age_ms_max"], age)
                server.sendto(FEEDBACK.pack(b"MSF1", 1, 0, 0, packet.frame_id, 65536,
                                           metrics["received_frames"], sink.dropped, packet.capture_us), peer)
            except ValueError as exc:
                metrics["errors"].append(str(exc))

    worker = threading.Thread(target=receive, daemon=True)
    worker.start()
    try:
        sender = run(argparse.Namespace(host="127.0.0.1", port=port, fps=30, quality=65, mbps=12,
                                        duration=args.duration, clip=args.clip,
                                        image=None if args.clip else Path(__file__).parent / "fixtures" / "pattern-720x480-420-q65.jpg",
                                        desktop=False, ffmpeg="ffmpeg", input_jsonl=None, metrics=None, save_first=None))
        time.sleep(0.1)
    finally:
        stop.set()
        worker.join(timeout=2)
        server.close()
    elapsed = time.perf_counter() - start
    metrics.update(duration_seconds=elapsed, reference_sink_fps=metrics["received_frames"] / elapsed,
                   received_wire_mbps=metrics["received_bytes"] * 8 / elapsed / 1_000_000,
                   sender=sender, dropped_frames=sink.dropped,
                   transport_lossless=sink.dropped == 0,
                   pass_checks=not metrics["errors"] and metrics["received_frames"] == sender["sent_frames"])
    args.output.parent.mkdir(exist_ok=True, parents=True)
    args.output.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))
    if not metrics["pass_checks"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
