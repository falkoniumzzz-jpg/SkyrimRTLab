"""Prepare the pinned CS fork without resetting or overwriting a user's checkout."""
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'sources.lock.json').read_text(encoding='utf-8'))

def run(*cmd, cwd=None):
    subprocess.run([str(c) for c in cmd], cwd=cwd, check=True)

def prepare(source):
    source = Path(source).resolve()
    if not source.exists():
        run('git', 'init', source)
        run('git', 'config', 'core.autocrlf', 'false', cwd=source)
        run('git', 'config', 'core.longpaths', 'true', cwd=source)
        run('git', 'remote', 'add', 'origin', LOCK['cs']['url'], cwd=source)
        run('git', 'fetch', '--depth', '1', 'origin', LOCK['cs']['commit'], cwd=source)
        run('git', 'checkout', '--detach', 'FETCH_HEAD', cwd=source)
    head = subprocess.check_output(['git','rev-parse','HEAD'], cwd=source, text=True).strip()
    if head != LOCK['cs']['commit']:
        raise RuntimeError(f'Refusing to modify different CS revision: {head}')
    patch = ROOT / 'host.patch'
    def apply(cwd, *flags, quiet=False):
        # Git on Windows may check this repository out with CRLF. The target CS
        # files use LF; normalize patch bytes instead of weakening context checks.
        result = subprocess.run(['git', 'apply', *flags, '-'], cwd=cwd,
            input=patch.read_bytes().replace(b'\r\n', b'\n'),
            stdout=subprocess.DEVNULL if quiet else None,
            stderr=subprocess.DEVNULL if quiet else None)
        return result

    # Exact content check prevents accepting a partially modified or unrelated patch.
    for filename in ('src/Deferred.cpp', 'src/State.cpp', 'cmake/XSEPlugin.cmake'):
        original = subprocess.check_output(['git','show',f'HEAD:{filename}'], cwd=source)
        current = (source / filename).read_bytes()
        if current != original:
            check = apply(source, '--reverse', '--check', quiet=True)
            if check.returncode:
                raise RuntimeError(f'Refusing to overwrite edits in {filename}')
            # Reverse on a temporary copy verifies that this is exactly our change.
            import tempfile
            with tempfile.TemporaryDirectory() as temp:
                temp = Path(temp)
                for name in ('src/Deferred.cpp', 'src/State.cpp', 'cmake/XSEPlugin.cmake'):
                    target = temp / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes((source / name).read_bytes())
                apply(temp, '--reverse').check_returncode()
                for name in ('src/Deferred.cpp', 'src/State.cpp', 'cmake/XSEPlugin.cmake'):
                    pristine = subprocess.check_output(['git','show',f'HEAD:{name}'], cwd=source)
                    if (temp / name).read_bytes() != pristine:
                        raise RuntimeError(f'Unrelated edits in {name}; use a separate checkout')
            break
    applied = apply(source, '--reverse', '--check', quiet=True).returncode == 0
    if not applied:
        apply(source, '--check').check_returncode()
        apply(source).check_returncode()
    for folder in ('host', 'include'):
        for path in sorted((ROOT / folder).glob('*')):
            target = source / 'src/RTLab' / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != path.read_bytes():
                raise RuntimeError(f'Refusing to overwrite different overlay: {target}')
            shutil.copy2(path, target)
    manifest = {'upstream': head, 'stage': LOCK['stage'], 'files': {}}
    for path in sorted((source / 'src/RTLab').glob('*')):
        manifest['files'][path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
    manifest['patch_sha256'] = hashlib.sha256(patch.read_bytes()).hexdigest()
    return manifest

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source), indent=2))
