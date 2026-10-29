"""Stream combined subprocess output to CI and a persistent UTF-8 log."""
import subprocess
import sys
import time
from pathlib import Path


def run_logged(label, command, log_dir, cwd=None, env=None):
    log_dir = Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / (label + '.log')
    started = time.monotonic()
    print(f'::group::{label}', flush=True)
    try:
        with path.open('w', encoding='utf-8', newline='\n') as log:
            with subprocess.Popen([str(x) for x in command], cwd=cwd, env=env,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                  text=True, encoding='utf-8', errors='replace', bufsize=1) as process:
                for line in process.stdout:
                    log.write(line)
                    log.flush()
                    # Avoid interpreting arbitrary compiler output as Actions commands.
                    sys.stdout.write('  ' + line)
                    sys.stdout.flush()
                code = process.wait()
            summary = f'{label}: exit={code}, elapsed={time.monotonic() - started:.1f}s\n'
            log.write(summary)
            print(summary, end='', flush=True)
        if code:
            raise RuntimeError(f'{label} failed with exit code {code}; see {path.name}')
    finally:
        print('::endgroup::', flush=True)
