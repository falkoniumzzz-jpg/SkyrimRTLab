"""Prepare official CS 1.9.0 with the ported hardware-RT host, plus the paired CER backend.

Every step is pinned in sources.lock.json and idempotent: an already-applied patch is
detected by a reverse check and skipped; a tree with foreign edits is refused.
"""
import argparse
import json
import shutil
import subprocess

from common import ROOT, WORK, LOCK, fetch, run

PATCHES = ROOT / "patches"


def _git_apply(source, patch, *flags):
    # A Windows checkout of this repository may convert patch files to CRLF.
    data = patch.read_bytes().replace(b"\r\n", b"\n")
    return subprocess.run(["git", "apply", *flags, "-"], cwd=source, input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def apply_patches(name, source):
    for patch_name in LOCK["patches"][name]:
        patch = PATCHES / patch_name
        if _git_apply(source, patch, "--reverse", "--check").returncode == 0:
            print(f"{name}: {patch_name} already applied", flush=True)
            continue
        check = _git_apply(source, patch, "--check")
        if check.returncode:
            raise RuntimeError(f"{name}: {patch_name} cannot apply:\n" + check.stderr.decode(errors="replace"))
        result = _git_apply(source, patch)
        if result.returncode:
            raise RuntimeError(result.stderr.decode(errors="replace"))
        print(f"{name}: applied {patch_name}", flush=True)


def take_rt_binaries(cs):
    """Streamline 2.12 + DLSS-RR runtime DLLs exactly as shipped with the RT host commit."""
    rt = LOCK["rt_host"]["commit"]
    have = subprocess.run(["git", "cat-file", "-e", rt + "^{commit}"], cwd=cs, stderr=subprocess.DEVNULL).returncode == 0
    if not have:
        run("cs-fetch-rt-host", ["git", "fetch", "--depth", "1", "origin", rt], cs)
    run("cs-rt-binaries", ["git", "-c", "core.longpaths=true", "checkout", rt, "--", *LOCK["rt_host"]["binary_paths"]], cs)


def pin_streamline(cs):
    sl = cs / "extern/Streamline-DX12"
    commit = LOCK["cs"]["streamline"]
    actual = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=sl, text=True).strip()
    if actual != commit:
        run("streamline-fetch", ["git", "fetch", "--depth", "1", "origin", commit], sl)
        run("streamline-checkout", ["git", "checkout", "--detach", commit], sl)


def prepare(skip_submodules=False):
    cs = fetch("cs", LOCK["cs"]["url"], LOCK["cs"]["commit"], WORK / "cs")
    cer = fetch("cer", LOCK["cer"]["url"], LOCK["cer"]["commit"], WORK / "cer")

    for name, target in (("cs", cs), ("cer", cer)):
        if json.loads((target / "vcpkg.json").read_text(encoding="utf-8"))["builtin-baseline"] != LOCK[name]["vcpkg"]:
            raise RuntimeError(name + " vcpkg baseline mismatch")

    apply_patches("cs", cs)
    take_rt_binaries(cs)
    apply_patches("cer", cer)

    if not skip_submodules:
        run("cs-submodules", ["git", "-c", "core.longpaths=true", "submodule", "update", "--init", "--depth", "1", "--", *LOCK["cs"]["submodules"]], cs)
        run("cs-commonlib", ["git", "submodule", "update", "--init", "--recursive", "--depth", "1"], cs / "extern/CommonLibSSE-NG")
        pin_streamline(cs)
        run("cer-submodules", ["git", "-c", "core.longpaths=true", "submodule", "update", "--init", "--depth", "1", "--", *LOCK["cer"]["submodules"]], cer)
        run("cer-commonlib", ["git", "submodule", "update", "--init", "--recursive", "--depth", "1"], cer / "extern/CommonLibSSE-NG")
        run("nvrhi-headers", ["git", "submodule", "update", "--init", "--depth", "1", "--", "thirdparty/DirectX-Headers", "thirdparty/Vulkan-Headers"], cer / "extern/NVRHI")
        if shutil.which("git-lfs"):
            run("cs-lfs", ["git", "lfs", "pull"], cs)
            run("streamline-lfs", ["git", "lfs", "pull"], cs / "extern/Streamline-DX12")

    # Contract checks that would otherwise only fail at runtime.
    header = (cs / "include/CreationEngineRaytracing.h").read_text(encoding="utf-8")
    api = (cer / "src/API.cpp").read_text(encoding="utf-8")
    stamp = "0x" + LOCK["abi"] + "u"
    if stamp not in header or stamp not in api:
        raise RuntimeError("CS host and CER backend ABI stamps differ from sources.lock.json")
    for dll in ("nvngx_dlssd.dll", "sl.dlss_d.dll"):
        if not (cs / "features/Upscaling/Shaders/Upscaling/Streamline" / dll).is_file():
            raise RuntimeError("Missing DLSS-RR runtime " + dll)
    return cs, cer


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--skip-submodules", action="store_true")
    prepare(p.parse_args().skip_submodules)
