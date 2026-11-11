"""Exercise real V97 Python host session against real portable Rust receiver."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'host'))
from moonshine import protocol97 as p

proc = subprocess.Popen([sys.argv[1]], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)


def talk(command):
    proc.stdin.write(command + '\n')
    proc.stdin.flush()
    response = proc.stdout.readline().strip()
    assert response, ('bridge terminated', command)
    return response


def rejects(function):
    try:
        function()
    except ValueError:
        return
    raise AssertionError('expected ValueError')


def new(profile=0, core=1):
    assert talk(f'NEW {profile} {core}') == 'OK'


def setup(session):
    return talk('SETUP ' + session.request().hex())


try:
    host = p.HostSession(p.Session(epoch=7))
    rejects(lambda: list(host.packets(b'x', 1, 0)))
    new()
    result = setup(host)
    assert result.startswith('ACK '), result
    ack = bytes.fromhex(result[4:])
    # Every byte is essential: a changed reserved/header/selected field must
    # fail before any datagrams can be generated from this unacknowledged host.
    for i in range(len(ack)):
        mutant = bytearray(ack)
        mutant[i] ^= 1
        h = p.HostSession(p.Session(epoch=7))
        rejects(lambda: h.accept_ack(bytes(mutant)))
        rejects(lambda: list(h.packets(b'x', 1, 0)))
    host.accept_ack(ack)
    # Idempotent setup preserves frame history. Exercise the real host packet
    # generator and byte-exact Rust metadata across three fragments.
    payload = bytes((i * 31 + 7) & 255 for i in range(2801))
    packets = list(host.packets(payload, 10, 42))
    assert len(packets) == 3
    assert talk('DATA ' + packets[0].hex()) == 'CHUNK 0 0 1400 false'
    assert setup(host) == result
    assert talk('DATA ' + packets[1].hex()) == 'CHUNK 1 1400 1400 false'
    assert talk('DATA ' + packets[2].hex()) == 'CHUNK 2 2800 1 true'
    assert talk('DATA ' + packets[0].hex()) == 'ERR Sequence'
    # Core mismatch and a same-epoch change are rejected on the Rust side.
    assert setup(p.HostSession(p.Session(epoch=8, core_generation=2))) == 'ERR Core'
    assert setup(p.HostSession(p.Session(epoch=7, payload_size=1024))) == 'ERR Epoch'
    # Four explicit research profiles are rejected by a default sink and
    # admitted only by a matching separately configured receiver and sender.
    for profile in p.RESEARCH:
        config = p.SinkConfig(profile)
        sess = p.Session(epoch=7, profile=profile, frame_cap=p.RESEARCH_CAP, sink_caps=p.CAP_OPAQUE)
        h = p.HostSession(sess, config)
        new()
        assert setup(h) == 'ERR Capability'
        new(profile)
        response = setup(h)
        assert response.startswith('ACK '), response
        h.accept_ack(bytes.fromhex(response[4:]))
        assert talk('DATA ' + next(h.packets(b'opaque', 1, 12)).hex()) == 'CHUNK 0 0 6 true'
    proc.stdin.close()
    assert proc.wait(timeout=10) == 0
    print(json.dumps(dict(status='PASS', mutated_ack_bytes_rejected=40,
                          unacknowledged_send_rejected=True, jpeg_fragments=3,
                          idempotent_setup_preserved_history=True, replay_rejected=True,
                          wrong_core_rejected=True, same_epoch_change_rejected=True,
                          research_profiles_checked=4, actual_python_host=True,
                          actual_portable_rust_receiver=True, active_network_worker=False,
                          sunshine_esp32_fpga_executed=False), sort_keys=True))
finally:
    if proc.poll() is None:
        proc.kill()
        proc.wait()
