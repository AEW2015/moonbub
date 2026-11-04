import io
import json
from pathlib import Path
import tempfile
import unittest

from scripts.capture_av_acoustic import Recorder


class FakeProcess:
    def __init__(self):
        self.stdin = io.BytesIO()
        self.code = None

    def poll(self):
        return self.code

    def wait(self, timeout):
        self.code = 0
        return 0


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.now = 0
        self.commands = []

        def spawn(command, **kwargs):
            self.commands.append(command)
            return FakeProcess()

        self.rec = Recorder(Path(self.temp.name) / 'audio', clock=lambda: self.now,
                            popen=spawn, max_seconds=30, tail_seconds=2)
        self.addCleanup(self.rec.finish, 'test_cleanup')

    def test_input_only_does_not_open_microphone(self):
        self.rec.observe('USB_TRACE av result=active audio_enabled=false')
        self.assertFalse(self.commands)

    def test_audio_stop_tail_then_next_session_rearms(self):
        self.rec.observe('USB_TRACE av result=active audio_enabled=true')
        self.assertIn('audio=Microphone (Razer Kiyo)', self.commands[0])
        self.rec.observe('USB_TRACE av result=stopped')
        self.now = 1
        self.rec.poll()
        self.assertIsNotNone(self.rec.active)
        self.now = 2
        self.rec.poll()
        self.assertIsNone(self.rec.active)
        self.rec.observe('USB_TRACE av result=active audio_enabled=true')
        self.assertEqual(len(self.commands), 2)
        self.assertNotEqual(self.commands[0][-1], self.commands[1][-1])

    def test_time_limit_closes_and_marks_partial(self):
        self.rec.start('audio start')
        self.now = 30
        self.rec.poll()
        self.assertIsNone(self.rec.active)
        self.assertTrue(self.rec.records[0]['coverage_partial'])

    def test_no_capture_file_cannot_be_reported_success(self):
        self.rec.start('audio start')
        self.rec.finish('receiver_session_ended')
        self.assertEqual(self.rec.records[0]['status'], 'FAILED_OR_PARTIAL')
        self.assertEqual(json.loads((self.rec.output / 'monitor.json').read_text())['state'], 'ARMED')

    def test_failed_device_open_stays_armed(self):
        def fail(*args, **kwargs):
            raise OSError('device unavailable')
        self.rec.popen = fail
        self.rec.start('audio start')
        self.assertIsNone(self.rec.active)
        self.assertEqual(self.rec.records[0]['status'], 'FAILED_TO_START')


if __name__ == '__main__':
    unittest.main()
