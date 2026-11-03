"""@brief Opt-in audio and ordered Xbox-input companion; video sender stays separate.

Requires new MoonBub build50 AV firmware. No traffic or input injection on import.
"""

import argparse
import json
import queue
import secrets
import socket
import time
from pathlib import Path

from av_protocol import FRAMES, INPUT, KEEP_NS, NONCE, PORT, RATE, InputLease, Packet, decode


def handshake(sock, peer, *, audio=False, timeout=5, clock=time.monotonic_ns):
    """@brief Complete nonce/cookie handshake and wait for an independently ordered MSI1."""
    nonce, flags = secrets.randbits(64) or 1, int(audio)
    cookie, next_send, deadline = None, 0, clock() + int(timeout * 1e9)
    while clock() < deadline:
        now = clock()
        if now >= next_send:
            packet = (Packet(b"MSC1", 1, nonce, flags=flags) if cookie is None else
                      Packet(b"MSC1", 2, cookie, seq=1, flags=flags, payload=NONCE.pack(nonce)))
            sock.send(packet.encode())
            next_send = now + KEEP_NS
        try:
            raw, source = sock.recvfrom(561)
        except TimeoutError:
            continue
        try:
            packet = decode(raw)
        except ValueError:
            continue
        if source != peer:
            continue
        if packet.magic == b"MSR1" and packet.flags == flags and NONCE.unpack(packet.payload)[0] == nonce:
            cookie = packet.session
            next_send = 0
        elif cookie is not None and packet.magic == b"MSI1" and packet.session == cookie:
            values = INPUT.unpack(packet.payload)
            if values[6] & 1 and bool(values[6] & 2) == audio:
                return cookie, raw
    raise TimeoutError("No active AV handshake; check new firmware, source IP filter and UDP5534")


def run(args):
    """@brief Run a finite AV session with bounded audio backlog and neutral shutdown."""
    if not 0 < args.seconds <= 7200 or not 0 <= args.gain <= 1:
        raise ValueError("Duration must be in(0,7200], gain in[0,1]")
    peer = socket.gethostbyname(args.receiver), args.port
    audio = dispatcher = lease = None
    cookie, seq = None, 2
    sock = None
    counts = {"input_packets": 0, "invalid_packets": 0, "stale_packets": 0,
              "audio_sent": 0, "audio_stale": 0, "input_timeouts": 0}
    output = args.log.open("x", encoding="utf-8") if args.log else None

    def event(kind, **fields):
        row = {"event": kind, "monotonic_ns": time.monotonic_ns(), **fields}
        if output:
            output.write(json.dumps(row) + "\n")
            output.flush()
        if kind != "input":
            print(json.dumps(row), flush=True)

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((args.bind, args.source_port))
        sock.connect(peer)
        sock.settimeout(0.005)
        event("socket", local=sock.getsockname(), peer=peer)
        has_audio = bool(args.tone or args.loopback or args.file)
        if args.gamepad:
            from gamepad_backend import GamepadDispatcher, VigemXbox360Backend
            dispatcher = GamepadDispatcher(VigemXbox360Backend.create())
        # Driver/device creation can block: do it before starting the500ms lease.
        cookie, initial = handshake(sock, peer, audio=has_audio)
        lease = InputLease(cookie, peer, dispatcher)
        lease.accept(initial, peer, time.monotonic_ns())
        event("active", session=f"{cookie:016x}", source="tone" if args.tone else "loopback" if args.loopback else "file" if args.file else "input-only")
        if has_audio:
            from av_audio import EncodedAudio
            audio = EncodedAudio("tone" if args.tone else "file" if args.file else "loopback",
                                 gain=args.gain, path=args.file, device=args.device)
            audio.start()
        started = time.monotonic_ns()
        next_keep, next_audio = started, started
        while time.monotonic_ns() - started < args.seconds * 1e9:
            now = time.monotonic_ns()
            if now >= next_keep:
                sock.send(Packet(b"MSC1", 3, cookie, seq=seq).encode())
                seq = (seq + 1) & 0xFFFFFFFF
                next_keep = now + KEEP_NS
            if audio is not None and now >= next_audio:
                if audio.error:
                    raise RuntimeError(audio.error)
                try:
                    audio_seq, stamp, block = audio.blocks.get_nowait()
                except queue.Empty:
                    pass
                else:
                    if now - stamp > 80_000_000:
                        counts["audio_stale"] += 1
                    else:
                        sock.send(Packet(b"MSA1", 1, cookie, seq=audio_seq,
                                         timestamp_us=stamp // 1000, payload=block).encode())
                        counts["audio_sent"] += 1
                        # Preserve the sample clock despite scheduler overshoot.
                        # Permit at most one period of catch-up, never an unbounded burst.
                        period = round(FRAMES * 1e9 / RATE)
                        next_audio = max(next_audio + period, now - period)
            wake = min(next_keep, next_audio if audio is not None and not audio.blocks.empty() else next_keep)
            sock.settimeout(max(0.0001, min(0.005, (wake - time.monotonic_ns()) / 1e9)))
            try:
                raw, source = sock.recvfrom(561)
            except TimeoutError:
                pass
            else:
                try:
                    accepted = lease.accept(raw, source, time.monotonic_ns())
                except ValueError:
                    counts["invalid_packets"] += 1
                else:
                    if accepted:
                        counts["input_packets"] += 1
                        event("input", seq=lease.seq, buttons=lease.status[0], audio_accepted=lease.status[1],
                              audio_rejected=lease.status[2], queued=lease.status[3], played=lease.status[4],
                              underruns=lease.status[5], state=lease.status[6], build=lease.status[7])
                    else:
                        counts["stale_packets"] += 1
            if lease.expire(time.monotonic_ns()):
                counts["input_timeouts"] += 1
                event("input_timeout")
                raise TimeoutError("No newer MSI1 for500ms; controller neutralized")
        sock.send(Packet(b"MSC1", 4, cookie, seq=seq).encode())
        cookie = None
    finally:
        # STOP must use the original pinned UDP endpoint, including exceptions.
        if sock is not None:
            try:
                if cookie is not None:
                    sock.send(Packet(b"MSC1", 4, cookie, seq=seq).encode())
            except OSError:
                pass  # Receiver's500ms lease independently stops the session.
            finally:
                sock.close()
        try:
            if lease is not None:
                lease.close()
            elif dispatcher is not None:
                dispatcher.close()
        finally:
            try:
                if audio is not None:
                    audio.close()
            finally:
                event("summary", **counts, audio_queue_drops=audio.dropped if audio else 0,
                      capture_errors=audio.capture_errors if audio else 0, last_status=lease.status if lease else None)
                if output:
                    output.close()
    return counts


def main():
    """@brief Parse explicit test options; no audio/input output is enabled by default."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receiver", required=True)
    parser.add_argument("--port", type=int, default=PORT)
    parser.add_argument("--bind", default="0.0.0.0")
    parser.add_argument("--source-port", type=int, default=0)
    parser.add_argument("--seconds", type=float, default=30)
    parser.add_argument("--gamepad", action="store_true")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--tone", action="store_true")
    source.add_argument("--loopback", action="store_true")
    source.add_argument("--file", type=Path)
    parser.add_argument("--device", type=int)
    parser.add_argument("--gain", type=float, default=0.25)
    parser.add_argument("--log", type=Path)
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(2, f"{error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
