"""Bounded USB line framing and byte-exact selected diagnostic records.

The binary output preserves accepted bytes, including line endings. It omits
non-diagnostic traffic and replaces entire credential-related records. It is
therefore not a complete, unfiltered UART capture.
"""
import hashlib
import json
import re


class LineFramer:
    def __init__(self, limit=8192):
        self.limit = limit
        self.pending = b''
        self.discarding = 0

    def feed(self, chunk):
        records, discarded = [], []
        data = self.pending + chunk
        self.pending = b''
        parts = data.split(b'\n')
        for part in parts[:-1]:
            line = part + b'\n'
            if self.discarding:
                discarded.append(self.discarding + len(line))
                self.discarding = 0
            elif len(line) > self.limit:
                discarded.append(len(line))
            else:
                records.append(line)
        tail = parts[-1]
        if self.discarding:
            self.discarding += len(tail)
        elif len(tail) > self.limit:
            self.discarding = len(tail)
        else:
            self.pending = tail
        return records, discarded

    def finish(self):
        """Disconnect/stop cannot merge a partial record with a new session."""
        records = [self.pending] if self.pending else []
        discarded = [self.discarding] if self.discarding else []
        self.pending, self.discarding = b'', 0
        return records, discarded


class DiagnosticBytes:
    TAGS = (b'USB_TEST', b'USB_TRACE', b'USB_D24',
            b'Streaming frame drop:', b'Streaming memory ')
    FATAL = re.compile(rb'Reset reason:|Guru Meditation|Backtrace:|abort\(\)|'
                       rb'assert failed|panicked at|stack (overflow|canary)|'
                       rb'task_wdt|brownout|Rebooting|Restarting|rst:', re.I)
    CREDENTIAL = re.compile(rb'\b(ssid|password|passphrase|psk)\b', re.I)

    def __init__(self, binary=None, index=None):
        self.binary, self.index = binary, index
        self.offset = self.records = self.panic_lines = 0

    def select(self, raw, stamp):
        fatal = bool(self.FATAL.search(raw))
        if fatal:
            self.panic_lines = 45
        if not (fatal or self.panic_lines or any(tag in raw for tag in self.TAGS)):
            return None
        if self.panic_lines:
            self.panic_lines -= 1
        redacted = bool(self.CREDENTIAL.search(raw))
        delivered = b'[credential-related record withheld]\n' if redacted else raw
        event = dict(utc=stamp, offset=self.offset, bytes=len(delivered),
                     received_bytes=len(raw), redacted=redacted,
                     partial=not raw.endswith(b'\n'),
                     d24_markers=delivered.count(b'USB_D24'),
                     sha256=hashlib.sha256(delivered).hexdigest())
        if self.binary is not None:
            if self.binary.write(delivered) != len(delivered):
                raise OSError('Short diagnostic evidence write')
            self.binary.flush()
            self.index.write(json.dumps(event) + '\n')
            self.index.flush()
        self.offset += len(delivered)
        self.records += 1
        return delivered.decode('utf-8', 'replace').rstrip('\r\n')
