import contextlib
import io
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from process_log import run_logged

class ProcessLogTests(unittest.TestCase):
    def test_stdout_stderr_and_invalid_utf8_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()) as console:
            run_logged('compile', [sys.executable, '-c',
                "import os; os.write(1,b'compiler output\\n'); os.write(2,b'bad byte \\xff\\n')"], temp)
            log = (Path(temp) / 'compile.log').read_text(encoding='utf-8')
            self.assertIn('compiler output', log)
            self.assertIn('bad byte \ufffd', log)
            self.assertIn('compiler output', console.getvalue())
            self.assertIn('exit=0', log)

    def test_failure_keeps_output_and_exit_code(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()) as console:
            with self.assertRaisesRegex(RuntimeError, 'exit code 7'):
                run_logged('compile', [sys.executable, '-c',
                    "import sys; print('error C1234'); sys.exit(7)"], temp)
            log = (Path(temp) / 'compile.log').read_text(encoding='utf-8')
            self.assertIn('error C1234', log)
            self.assertIn('exit=7', log)
            self.assertTrue(console.getvalue().endswith('::endgroup::\n'))

if __name__ == '__main__':
    unittest.main()
