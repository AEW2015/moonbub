"""Cross-language tests use the production Python packetizer and Rust receiver.

This exercises a real JPEG through chunking and the firmware state machine;
it does not substitute for ESP32 Wi-Fi or SPI hardware execution.
"""
import hashlib
import json
import os
import random
import shutil
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "host"))
from moonshine.protocol import packets, parse_packet, parse_feedback

HARNESS = r'''
#[path = "@PROTOCOL@"] mod protocol;
use std::io::Read;
fn main() {
    let mut bytes=Vec::new(); std::io::stdin().read_to_end(&mut bytes).unwrap();
    let mut pos=0; let mut receiver=protocol::Receiver::default();
    while pos<bytes.len() {
        let len=u32::from_be_bytes(bytes[pos..pos+4].try_into().unwrap()) as usize;
        pos+=4;
        if len==0 {receiver=protocol::Receiver::default(); println!("RESET"); continue;}
        let packet=&bytes[pos..pos+len]; pos+=len;
        let header=protocol::Header::parse(packet).is_ok();
        match receiver.accept(packet) {
            Ok((h,done)) => println!("{} 1 {} {} {}",header as u8,done as u8,h.id,h.offset),
            Err(_) => println!("{} 0 0 0 0",header as u8),
        }
    }
    let feedback=protocol::feedback(1,0x845,0x12345678,8192,71,9,123456789);
    for byte in feedback {print!("{:02x}",byte);} println!();
}
'''


def main():
    output = ROOT / "evidence" / "integration"
    output.mkdir(parents=True, exist_ok=True)
    protocol = ROOT / "firmware/handheld/src/streaming/protocol.rs"
    harness = output / "firmware_protocol_harness.rs"
    harness.write_text(HARNESS.replace("@PROTOCOL@", protocol.as_posix()))
    compiler = shutil.which("rustc") or str(Path(os.environ["USERPROFILE"]) / ".cargo/bin/rustc.exe")
    executable = output / "firmware_protocol_harness.exe"
    build = subprocess.run([compiler, "+stable", "--edition=2021", "-A", "dead_code", "-O", str(harness), "-o", str(executable)], capture_output=True, text=True)
    (output / "compile.log").write_text(build.stdout + build.stderr)
    build.check_returncode()
    records, expectations, names = [], [], []

    def add(packet, accepted=None, done=None, name="packet"):
        records.append(struct.pack("!I", len(packet)) + packet)
        names.append(name)
        try:
            p = parse_packet(packet)
            header_valid = True
        except ValueError:
            p, header_valid = None, False
        expectations.append((header_valid, accepted, done))

    def reset():
        records.append(b"\0\0\0\0")
        names.append("reset")
        expectations.append(None)

    jpeg = (ROOT / "host/fixtures/pattern-720x480-420-q65.jpg").read_bytes()
    chunks = list(packets(jpeg, 100, 987654321))
    for i, chunk in enumerate(chunks):
        add(chunk, True, i == len(chunks)-1, "actual-JPEG")
    # Loss, a late duplicate, corrupt data, metadata changes and new-frame recovery.
    reset()
    add(chunks[0], True, False, "loss-start")
    add(chunks[2], False, False, "lost-middle")
    add(chunks[1], False, False, "late-after-abort")
    for chunk in packets(b"recovered", 101, 42):
        add(chunk, True, True, "recovery")
    reset()
    bad_crc = bytearray(next(packets(b"corrupted", 4, 42)))
    bad_crc[-1] ^= 1
    add(bytes(bad_crc), False, False, "bad-crc")
    add(next(packets(b"next", 5, 43)), True, True, "crc-recovery")
    add(next(packets(b"stale", 4, 44)), False, False, "stale-frame")
    reset()
    add(next(packets(b"wrap", 0xffffffff, 45)), True, True, "before-wrap")
    add(next(packets(b"wrap", 0, 46)), True, True, "after-wrap")

    # Deterministic differential parser corpus includes every truncated header,
    # every bit in the fixed header, hostile overflow values and random bytes.
    reset()
    base = next(packets(b"protocol-validation", 1, 3))
    for n in range(1, 40):
        add(base[:n], False, False, "short-header")
    for offset in range(40):
        for bit in range(8):
            mutation = bytearray(base)
            mutation[offset] ^= 1 << bit
            add(bytes(mutation), name="header-bit-mutation")
    rng = random.Random(20261102)
    for _ in range(1000):
        mutation = bytearray(base)
        for __ in range(rng.randrange(1, 5)):
            mutation[rng.randrange(len(mutation))] = rng.randrange(256)
        add(bytes(mutation), name="seeded-mutation")

    corpus = b"".join(records)
    (output / "packets.bin").write_bytes(corpus)
    run = subprocess.run([str(executable)], input=corpus, capture_output=True)
    (output / "execution.log").write_bytes(run.stdout + run.stderr)
    run.check_returncode()
    lines = run.stdout.decode().splitlines()
    assert len(lines) == len(expectations) + 1
    checked = 0
    for name, expected, line in zip(names, expectations, lines):
        if expected is None:
            assert line == "RESET", (name, line)
            continue
        actual = list(map(int, line.split()))
        assert bool(actual[0]) == expected[0], (name, expected, actual)
        if expected[1] is not None:
            assert bool(actual[1]) == expected[1], (name, expected, actual)
            assert bool(actual[2]) == expected[2], (name, expected, actual)
        checked += 1
    feedback = parse_feedback(bytes.fromhex(lines[-1]))
    assert (feedback.status, feedback.buttons, feedback.frame_id, feedback.free_bytes,
            feedback.received_frames, feedback.dropped_frames, feedback.capture_us) == (
                1, 0x845, 0x12345678, 8192, 71, 9, 123456789)
    result = {"status": "pass", "packet_cases": checked, "seed": 20261102,
              "actual_jpeg_chunks": len(chunks), "jpeg_bytes": len(jpeg),
              "firmware_source_sha256": hashlib.sha256(protocol.read_bytes()).hexdigest(),
              "host_source_sha256": hashlib.sha256((ROOT / "host/moonshine/protocol.py").read_bytes()).hexdigest(),
              "limitations": "Host-native production Rust protocol only; no Wi-Fi, QSPI or physical display measurements."}
    (output / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print("CROSS_LANGUAGE_PROTOCOL_PASS", checked, "packets; JPEG and feedback verified")


if __name__ == "__main__":
    main()
