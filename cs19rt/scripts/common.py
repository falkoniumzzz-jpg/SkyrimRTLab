import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "_work"
OUT = ROOT / "out"
LOCK = json.loads((ROOT / "sources.lock.json").read_text(encoding="utf-8"))


def run(label, args, cwd=None, env=None):
    logs = OUT / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    args = list(map(str, args))
    print(label, args, flush=True)
    with (logs / (label + ".log")).open("w", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\n")
        with subprocess.Popen(args, cwd=cwd, env=env, stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace") as p:
            for line in p.stdout:
                print(line, end="", flush=True)
                log.write(line)
            code = p.wait()
        log.write(f"\nEXIT_CODE={code}\n")
    if code:
        raise RuntimeError(f"{label} failed, exit {code}; see out/logs")


def fetch(name, url, commit, target, *, full_history=False):
    target.mkdir(parents=True, exist_ok=True)
    if not (target / ".git").exists():
        run(name + "-init", ["git", "init", target])
        run(name + "-config", ["git", "config", "core.autocrlf", "false"], target)
        run(name + "-longpaths", ["git", "config", "core.longpaths", "true"], target)
        run(name + "-remote", ["git", "remote", "add", "origin", url], target)
        depth = [] if full_history else ["--depth", "1"]
        run(name + "-fetch", ["git", "fetch", *depth, "origin", commit], target)
        run(name + "-checkout", ["git", "-c", "core.longpaths=true", "checkout", "--detach", commit], target)
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=target, text=True).strip()
    if actual != commit:
        raise RuntimeError(f"Wrong {name} commit: {actual}")
    if full_history:
        shallow = subprocess.check_output(
            ["git", "rev-parse", "--is-shallow-repository"], cwd=target, text=True).strip()
        if shallow == "true":
            # vcpkg's versions database references historical port tree objects.
            run(name + "-history", ["git", "fetch", "--unshallow", "origin", commit], target)
    return target


def sha256(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()
