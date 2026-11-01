"""Compile the CS 1.9 shaders touched by the RT port with FXC, as the game does at runtime.

Skyrim compiles these permutations on the user's machine; an error there silently breaks
every affected material. This check builds the merged AIO shader tree and compiles the
recorded Lighting pixel-shader permutations with and without RAYTRACING, plus grass and
the deferred composite with the RT defines.
"""
import argparse
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml


def merged_tree(cs, target):
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(cs / "package/Shaders", target)
    for shaders in sorted((cs / "features").glob("*/Shaders")):
        shutil.copytree(shaders, target, dirs_exist_ok=True)
    return target


def jobs_from_config(cs):
    """Returns (file, profile, entry, defines, baseline_defines_or_None).

    A job with a baseline is an RT variant of an existing CS 1.9 permutation: it only
    counts as a regression when the same permutation without the RT define compiles.
    """
    config = yaml.safe_load((cs / ".github/configs/shader-validation.yaml").read_text(encoding="utf-8"))
    jobs = []
    common = []
    for shader in config["shaders"]:
        if shader["file"] != "Lighting.hlsl":
            continue
        ps = shader["configs"]["PSHADER"]
        common = [d for d in ps["common_defines"] if not d.startswith("D3DCOMPILE")]
        for entry in ps["entries"]:
            defines = common + entry["defines"]
            jobs.append(("Lighting.hlsl", "ps_5_0", "main", defines + ["RAYTRACING"], defines))
    features = [d for d in common if d not in ("PSHADER", "VC", "CS_HAIR")]
    grass = [d for d in features if d not in ("TERRAIN_VARIATION", "EXTENDED_MATERIALS", "EXTENDED_TRANSLUCENCY")] + ["PSHADER", "GRASS_LIGHTING"]
    for extra in ([], ["DO_ALPHA_TEST"], ["TRUE_PBR"], ["TRUE_PBR", "DO_ALPHA_TEST"], ["RENDER_DEPTH"]):
        jobs.append(("RunGrass.hlsl", "ps_5_0", "main", grass + extra + ["RAYTRACING"], grass + extra))
    composite = features + ["COMPUTESHADER"]
    jobs.append(("DeferredCompositeCS.hlsl", "cs_5_0", "main", composite + ["RAYTRACING"], composite))
    jobs.append(("DeferredCompositeCS.hlsl", "cs_5_0", "main", composite + ["RAYTRACING", "INTERIOR"], composite + ["INTERIOR"]))
    rt = composite + ["RAYTRACING"]
    jobs += [
        ("Raytracing/ConvertTexturesCS.hlsl", "cs_5_0", "main", rt + ["DLSS_RR=0"], None),
        ("Raytracing/ConvertTexturesCS.hlsl", "cs_5_0", "main", rt + ["DLSS_RR=1"], None),
        ("Raytracing/GICompositeCS.hlsl", "cs_5_0", "main", rt, None),
        ("Raytracing/PTCompositeCS.hlsl", "cs_5_0", "main", rt, None),
        ("Raytracing/CubeToHemiCS.hlsl", "cs_5_0", "main", rt + ["RESOLUTION=512"], None),
        ("Raytracing/ShadowLabCompositeCS.hlsl", "cs_5_0", "main", rt, None),
        ("Raytracing/CopyDepth.hlsl", "vs_5_0", "MainVS", [d for d in rt if d != "COMPUTESHADER"] + ["VSHADER"], None),
        ("Raytracing/CopyDepth.hlsl", "ps_5_0", "MainPS", [d for d in rt if d != "COMPUTESHADER"] + ["PSHADER"], None),
        ("Upscaling/ColorSpaceCS.hlsl", "cs_5_0", "main", rt + ["TO_LINEAR"], None),
        ("Upscaling/ColorSpaceCS.hlsl", "cs_5_0", "main", rt + ["TO_GAMMA"], None),
        ("Upscaling/EncodeTexturesCS.hlsl", "cs_5_0", "main", rt + ["DLSS_RR"], None),
        ("Upscaling/EncodeTexturesCS.hlsl", "cs_5_0", "main", rt, None),
    ]
    return jobs


def find_fxc():
    sdk = Path(os.environ["ProgramFiles(x86)"]) / "Windows Kits/10/bin"
    found = sorted(sdk.glob("*/x64/fxc.exe"))
    if not found:
        raise RuntimeError("Windows SDK fxc.exe missing")
    return found[-1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cs", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    # fxc runs with cwd=tree, so every path it receives must be absolute.
    a.cs, a.out = a.cs.resolve(), a.out.resolve()
    tree = merged_tree(a.cs, a.out / "aio-shaders")
    fxc = find_fxc()
    jobs = jobs_from_config(a.cs)
    variants = {}
    for file, profile, entry, defines, baseline in jobs:
        variants[(file, profile, entry, tuple(sorted(set(defines))))] = None
        if baseline is not None:
            variants[(file, profile, entry, tuple(sorted(set(baseline))))] = None

    def compile_one(key):
        file, profile, entry, defines = key
        args = [str(fxc), "/nologo", "/T", profile, "/E", entry, "/O1", "/I", str(tree)]
        for d in defines:
            # fxc reads "/D NAME=" (empty value) as taking the *next* token as its value,
            # so a value-less define must be passed as "/D NAME" (defined as 1).
            args += ["/D", d]
        args += ["/Fo", os.devnull, str(tree / file)]
        r = subprocess.run(args, cwd=tree, capture_output=True, text=True, errors="replace")
        return key, r.returncode, (r.stdout + r.stderr)

    results = {}
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        for key, code, output in pool.map(compile_one, list(variants)):
            results[key] = (code, output)

    regressions, baseline_failures = [], []
    for file, profile, entry, defines, baseline in jobs:
        key = (file, profile, entry, tuple(sorted(set(defines))))
        code, output = results[key]
        if not code:
            continue
        text = f"{file} {profile} {entry} {' '.join(key[3])}\n{output}"
        if baseline is not None and results[(file, profile, entry, tuple(sorted(set(baseline))))][0]:
            baseline_failures.append(text)  # fails without RT too: not caused by the port
        else:
            regressions.append(text)
    log = a.out / "logs/cs-shader-check.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"{len(results)} compiles, {len(regressions)} RT regressions, {len(baseline_failures)} baseline failures\n\n"
                   + "== RT regressions ==\n" + "\n\n".join(regressions)
                   + "\n\n== also failing without RT ==\n" + "\n\n".join(baseline_failures[:20]), encoding="utf-8")
    print(f"{len(results)} CS shader compiles, {len(regressions)} RT regressions, {len(baseline_failures)} baseline failures", flush=True)
    baselines = sum(1 for job in jobs if job[4] is not None)
    if baselines and len(baseline_failures) * 10 > baselines:
        # Unmodified CS 1.9 permutations must compile; otherwise this check itself is broken
        # and an RT regression could hide among the "baseline" failures.
        print("Check setup invalid: too many CS 1.9 baseline permutations fail.\n")
        print("\n\n".join(baseline_failures[:5]))
        sys.exit(2)
    if regressions:
        print("\n\n".join(regressions[:10]))
        sys.exit(1)


if __name__ == "__main__":
    main()
