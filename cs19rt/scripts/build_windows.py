"""Build official CS 1.9.0 + ported RT host and the paired CER backend, then package for MO2.

Run on Windows with Python 3.12+, Git, VS 2022/2026 C++ tools and CMake 4.2.3.
"""
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
import urllib.request
import zipfile

from common import ROOT, WORK, OUT, LOCK, fetch, run, sha256
from prepare import prepare

DOCS_DIR = "FalkosLichtspiel CS19 RT Docs"
# Debug-only feature from the RT branch: compiled in, but not shipped/loaded.
NOT_SHIPPED = ["Shaders/Features/SceneGraphExplorer.ini"]


def tools():
    target = WORK / "dxc"
    target.mkdir(parents=True, exist_ok=True)
    archive = target / "dxc.zip"
    if not archive.exists():
        urllib.request.urlretrieve(LOCK["dxc_url"], archive)
    if sha256(archive) != LOCK["dxc_sha256"]:
        raise RuntimeError("DXC archive SHA256 mismatch")
    with zipfile.ZipFile(archive) as z:
        z.extractall(target)
    dxc = target / "bin/x64/dxc.exe"
    if not dxc.exists():
        raise RuntimeError("DXC executable missing")
    vswhere = Path(os.environ["ProgramFiles(x86)"]) / "Microsoft Visual Studio/Installer/vswhere.exe"
    installations = json.loads(subprocess.check_output([str(vswhere), "-products", "*", "-requires",
        "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-format", "json"], text=True))
    candidates = [v for v in installations if int(v["installationVersion"].split(".")[0]) in (17, 18)]
    if not candidates:
        raise RuntimeError("VS 2022/2026 C++ build tools missing")
    selected = sorted(candidates, key=lambda v: list(map(int, v["installationVersion"].split("."))))[-1]
    generator = "Visual Studio 18 2026" if selected["installationVersion"].startswith("18.") else "Visual Studio 17 2022"
    (OUT / "toolchain.json").write_text(json.dumps(selected, indent=2), encoding="utf-8")
    os.environ["PATH"] = str(dxc.parent) + os.pathsep + os.environ["PATH"]
    return dxc, generator, selected


def msvc_env(vs):
    """Environment of vcvars64.bat, for the Ninja build (keys upper-cased like os.environ)."""
    vcvars = Path(vs["installationPath"]) / "VC/Auxiliary/Build/vcvars64.bat"
    out = subprocess.check_output(f'cmd /s /c ""{vcvars}" >nul && set"', text=True, errors="replace")
    env = os.environ.copy()
    for line in out.splitlines():
        key, sep, value = line.partition("=")
        if sep and key and not key.startswith("="):
            env[key.upper()] = value
    if not shutil.which("cl.exe", path=env.get("PATH")):
        raise RuntimeError("vcvars64 did not put cl.exe on PATH")
    return env


def vcpkg_for(name):
    vcpkg = fetch("vcpkg-" + name, "https://github.com/microsoft/vcpkg.git", LOCK[name]["vcpkg"],
                  WORK / ("vcpkg-" + name), full_history=True)
    run(name + "-bootstrap", ["cmd", "/c", vcpkg / "bootstrap-vcpkg.bat", "-disableMetrics"])
    return vcpkg


def summarize_compile_errors(label):
    """Collect every compiler/linker error of a failed build into one short file."""
    log = OUT / "logs" / (label + ".log")
    if not log.exists():
        return
    pattern = re.compile(r"(error C\d+|error LNK\d+|fatal error|: error:)")
    errors = []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        if pattern.search(line) and line not in errors:
            errors.append(line)
    (OUT / "logs" / (label + "-errors.txt")).write_text(
        f"{len(errors)} distinct error lines\n" + "\n".join(errors) + "\n", encoding="utf-8")
    print(f"::group::{label}: {len(errors)} distinct error lines", flush=True)
    for line in errors:
        print(line, flush=True)
    print("::endgroup::", flush=True)


def diagnose_unresolved(build, env):
    """After LNK2019/LNK2001: did every compiled object reach the link, and which define the symbol?"""
    log = OUT / "logs/cs-build.log"
    text = log.read_text(encoding="utf-8", errors="replace") if log.exists() else ""
    names = sorted(set(re.findall(r"unresolved external symbol .*?\((\?[^)\s]+)\)", text)))
    if not names:
        return
    lines = []
    try:
        objdir = build / "CMakeFiles/CommunityShaders.dir"
        objs = sorted(objdir.rglob("*.obj"))
        lines.append(f"{len(objs)} objects under {objdir}")
        rsp = build / "CMakeFiles/CommunityShaders.rsp"
        if rsp.exists():
            listed = rsp.read_text(encoding="utf-8", errors="replace").replace("/", "\\").lower()
            missing = [o for o in objs if str(o.relative_to(build)).replace("/", "\\").lower() not in listed]
            lines.append(f"objects missing from {rsp.name}: {len(missing)}")
            lines += ["  " + str(o.relative_to(build)) for o in missing[:50]]
        else:
            lines.append(f"{rsp} not found")
        for name in names:
            hits = [o for o in objs if name.encode() in o.read_bytes()]
            lines.append(f"{name}: named in {len(hits)} object(s)")
            for o in hits[:6]:
                out = subprocess.run(["dumpbin", "/nologo", "/symbols", str(o)], env=env,
                    capture_output=True, text=True, errors="replace").stdout
                lines += [f"  {o.relative_to(build)}: {l.strip()}" for l in out.splitlines() if name in l]
    except Exception as e:  # diagnostics must never hide the real failure
        lines.append(f"diagnostics failed: {e!r}")
    (OUT / "logs/cs-link-diagnostics.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("::group::cs-link diagnostics", flush=True)
    print("\n".join(lines), flush=True)
    print("::endgroup::", flush=True)


def build_cs(cs, vs):
    vcpkg = vcpkg_for("cs")
    env = msvc_env(vs)
    env["VCPKG_ROOT"] = str(vcpkg)
    build = WORK / "build-cs"
    # CS 1.9.0 host options, built with CS's own "ninja" preset settings so that
    # "ninja -k 0" reports every compile error of a run instead of stopping at the first.
    options = [f"-DCMAKE_TOOLCHAIN_FILE={vcpkg.as_posix()}/scripts/buildsystems/vcpkg.cmake",
        f"-DVCPKG_OVERLAY_PORTS={cs.as_posix()}/cmake/ports",
        f"-DVCPKG_OVERLAY_TRIPLETS={cs.as_posix()}/cmake/triplets",
        "-DVCPKG_TARGET_TRIPLET=x64-windows-static-md-release",
        "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL",
        "-DENABLE_SKYRIM_SE=ON", "-DENABLE_SKYRIM_AE=ON", "-DENABLE_SKYRIM_VR=OFF",
        "-DCOMMONLIB_PREBUILT=OFF", "-DCOMMONLIB_PREBUILT_MULTICONFIG=OFF",
        "-DSKSE_SUPPORT_XBYAK=ON", "-DDEVBENCH_BRIDGE=OFF", "-DZIP_TO_DIST=OFF",
        "-DAIO_ZIP_TO_DIST=OFF", "-DAUTO_PLUGIN_DEPLOYMENT=OFF", "-DTRACY_SUPPORT=OFF",
        "-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF", "-DSC_COMPILE_PDB=OFF",
        "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_FLAGS=/EHsc",
        # Exactly this value: FidelityFX-SDK detects x64 under Ninja by string equality.
        "-DCMAKE_EXE_LINKER_FLAGS=/machine:x64",
        "-DCMAKE_C_COMPILER=cl.exe", "-DCMAKE_CXX_COMPILER=cl.exe"]
    run("cs-configure", ["cmake", "-S", cs, "-B", build, "-G", "Ninja", *options], env=env)
    try:
        run("cs-build", ["cmake", "--build", build, "--target", "CommunityShaders", "--parallel", "4", "--", "-k", "0"], env=env)
    except RuntimeError:
        summarize_compile_errors("cs-build")
        diagnose_unresolved(build, env)
        raise
    return build


def build_cer(cer, generator, stage):
    vcpkg = vcpkg_for("cer")
    env = os.environ.copy()
    env["VCPKG_ROOT"] = str(vcpkg)
    # CMake embeds this value in generated install scripts; use forward slashes.
    env["DEPLOY_DIR"] = stage.as_posix()
    env["VCPKG_KEEP_ENV_VARS"] = "DEPLOY_DIR"
    build = WORK / "build-cer"
    options = ["-DBUILD_SKYRIM=ON", "-DBUILD_FALLOUT4=OFF", "-DENABLE_SKYRIM_SE=ON",
        "-DENABLE_SKYRIM_AE=ON", "-DENABLE_SKYRIM_VR=OFF", "-DCOMMONLIB_PREBUILT=OFF",
        "-DCOMMONLIB_PREBUILT_MULTICONFIG=OFF", "-DSKSE_SUPPORT_XBYAK=ON",
        "-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded$<$<CONFIG:Debug>:Debug>DLL",
        f"-DCMAKE_TOOLCHAIN_FILE={vcpkg}/scripts/buildsystems/vcpkg.cmake",
        "-DVCPKG_TARGET_TRIPLET=x64-windows-static-md", f"-DVCPKG_OVERLAY_PORTS={cer}/cmake/ports",
        "-DBUILD_TESTS=OFF", "-DBUILD_BENCHMARKS=OFF", "-DAUTO_DEPLOYMENT=ON",
        f"-DSHADERMAKE_DXC_PATH={WORK}/dxc/bin/x64/dxc.exe", f"-DDXC_PATH={WORK}/dxc/bin/x64/dxc.exe"]
    run("cer-configure", ["cmake", "-S", cer, "-B", build, "-G", generator, "-A", "x64", *options], env=env)
    run("cer-build", ["cmake", "--build", build, "--config", "Release", "--target", "CreationEngineRaytracing", "--parallel", "2"], env=env)
    return build


def stage_runtime(cs, cer, cs_build, cer_build):
    stage = OUT / "runtime/Data"
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True)
    # CS install clears its prefix, so it goes first.
    run("cs-install", ["cmake", "--install", cs_build, "--config", "Release", "--prefix", stage])
    run("cer-install", ["cmake", "--install", cer_build, "--config", "Release", "--prefix", stage])
    for p in (cer_build / "vcpkg_installed/x64-windows-static-md").rglob("dxil.dll"):
        if "debug" not in p.parts:
            shutil.copy2(p, stage / "SKSE/Plugins/dxil.dll")
            break
    for rel in NOT_SHIPPED:
        if (stage / rel).exists():
            (stage / rel).unlink()
    # Test builds keep the PDBs next to the DLLs (as CS's own install rules do): Crash Logger
    # needs them for readable crash logs and for thread dumps (Ctrl+Shift+F12) during a hang.
    for p in list(stage.rglob("*")):
        if p.is_file() and "community shaders logo" in str(p).lower():
            p.unlink()
    required = ["SKSE/Plugins/CommunityShaders.dll", "SKSE/Plugins/CreationEngineRaytracing.dll",
        "SKSE/Plugins/dxcompiler.dll", "SKSE/Plugins/D3D12Core.dll", "Shaders/Lighting.hlsl",
        "Shaders/Features/Raytracing.ini", "Shaders/Raytracing/ConvertTexturesCS.hlsl"]
    for rel in required:
        p = stage / rel
        if not p.is_file():
            raise RuntimeError("Missing " + rel)
        if p.suffix == ".dll" and p.read_bytes()[:2] != b"MZ":
            raise RuntimeError("Invalid DLL " + rel)
    streamline = list(stage.rglob("nvngx_dlssd.dll")) + list(stage.rglob("sl.dlss_d.dll"))
    if len(streamline) < 2:
        raise RuntimeError("DLSS-RR runtime DLLs missing from package")
    for p in stage.rglob("*"):
        if p.is_file() and p.stat().st_size < 1024 and p.read_bytes().startswith(b"version https://git-lfs.github.com/spec/v1"):
            raise RuntimeError("Unresolved LFS pointer: " + str(p))
    return stage


def docs_and_licenses(cs, cer, builds):
    runtime = OUT / "runtime"
    shutil.copy2(ROOT / "TESTING_DE.md", runtime / "TESTING_DE.md")
    shutil.copy2(ROOT / "README_DE.md", runtime / "README_DE.md")
    shutil.copy2(ROOT / "sources.lock.json", runtime / "sources.lock.json")
    notices = runtime / "licenses"
    for name, base in (("cs", cs), ("cer", cer)):
        for p in base.rglob("*"):
            if p.is_file() and ".git" not in p.parts and any(t in p.name.lower() for t in ("license", "copying", "exceptions", "notice")):
                dest = notices / "upstream" / name / p.relative_to(base)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, dest)
    for name, build in builds.items():
        for p in (build / "vcpkg_installed").rglob("copyright"):
            dest = notices / name / p.relative_to(build / "vcpkg_installed")
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dest)


def corresponding_source():
    archive = OUT / "Corresponding-Source.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for base, prefix in [(ROOT, "cs19rt")] + [(WORK / n, n) for n in ("cs", "cer", "build-cs", "build-cer")]:
            for directory, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in (".git", "__pycache__") and not (base == ROOT and d in ("_work", "out"))]
                for file in files:
                    p = Path(directory) / file
                    rel = p.relative_to(base)
                    if "community shaders logo" in str(rel).lower():
                        continue
                    if base.name.startswith("build-") and not (rel.parts[0] == "_deps" or file.endswith((".cmake", ".json"))):
                        continue
                    if p.suffix.lower() in (".obj", ".pch", ".pdb", ".exe", ".dll", ".lib", ".zip", ".7z", ".tar", ".gz"):
                        continue
                    if p.is_file():  # skips broken links, as the legacy pipeline did
                        z.write(p, str(Path(prefix) / rel))


def mo2_package(runtime, output):
    """Game files at the archive root; docs/licenses in one named subfolder (MO2 auto-install)."""
    data = runtime / "Data"
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for p in sorted(data.rglob("*")):
            if p.is_file():
                z.write(p, p.relative_to(data).as_posix())
        for p in sorted(runtime.rglob("*")):
            if p.is_file() and data not in p.parents:
                z.write(p, (Path(DOCS_DIR) / p.relative_to(runtime)).as_posix())
    with zipfile.ZipFile(output) as z:
        bad = z.testzip()
        names = set(z.namelist())
    if bad:
        raise RuntimeError("Corrupt archive member " + bad)
    required = ["SKSE/Plugins/CommunityShaders.dll", "SKSE/Plugins/CreationEngineRaytracing.dll"]
    missing = [n for n in required if n not in names]
    if missing or any(n.lower().startswith("data/") for n in names):
        raise RuntimeError(f"Invalid MO2 layout, missing={missing}")


def main():
    if os.name != "nt":
        raise RuntimeError("Full build requires Windows/MSVC. Use the GitHub Actions workflow.")
    OUT.mkdir(parents=True, exist_ok=True)
    dxc, generator, vs = tools()
    cs, cer = prepare()
    run("cer-gi-permutations", [sys.executable, ROOT.parent / "legacy/scripts/check_gi_shaders.py", "--cer", cer, "--dxc", dxc])
    run("cer-rr-restir-shaders", [sys.executable, ROOT.parent / "legacy/scripts/check_rt_shaders.py", "--cer", cer, "--dxc", dxc])
    # CS first: it carries the port, so a failure shows up before the (known-good) CER build.
    cs_build = build_cs(cs, vs)
    cer_build = build_cer(cer, generator, OUT / "runtime/Data")
    stage_runtime(cs, cer, cs_build, cer_build)
    docs_and_licenses(cs, cer, {"cs": cs_build, "cer": cer_build})
    corresponding_source()
    mo2_package(OUT / "runtime", OUT / "FalkosLichtspiel-CS19-RT-MO2.zip")
    (OUT / "BUILD-STATUS.txt").write_text("BUILD PASSED. Skyrim runtime and GPU execution NOT tested by CI.\n", encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        (OUT / "logs").mkdir(parents=True, exist_ok=True)
        (OUT / "logs/FAILURE.txt").write_text(traceback.format_exc(), encoding="utf-8")
        traceback.print_exc()
        sys.exit(1)
