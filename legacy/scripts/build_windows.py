"""MSVC build, shader validation, staging and failure logs. Run with Python 3.12+."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
import urllib.request
import zipfile
from common import ROOT, WORK, OUT, LOCK, fetch, run, sha256
from prepare_sources import prepare

def zip_tree(folder, output):
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file(): z.write(p, p.relative_to(folder))

def tools():
    target = WORK/'dxc'
    target.mkdir(parents=True, exist_ok=True)
    archive = target/'dxc.zip'
    if not archive.exists(): urllib.request.urlretrieve(LOCK['dxc_url'], archive)
    if sha256(archive) != LOCK['dxc_sha256']: raise RuntimeError('DXC archive SHA256 mismatch')
    with zipfile.ZipFile(archive) as z: z.extractall(target)
    dxc = target/'bin/x64/dxc.exe'
    if not dxc.exists(): raise RuntimeError('DXC executable missing')
    vswhere = Path(os.environ['ProgramFiles(x86)'])/'Microsoft Visual Studio/Installer/vswhere.exe'
    installations = json.loads(subprocess.check_output([str(vswhere), '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64', '-format', 'json'], text=True))
    candidates = [v for v in installations if int(v['installationVersion'].split('.')[0]) in (17,18)]
    if not candidates: raise RuntimeError('VS 2022/2026 C++ build tools missing')
    selected = sorted(candidates, key=lambda v: list(map(int,v['installationVersion'].split('.'))))[-1]
    major = int(selected['installationVersion'].split('.')[0])
    generator = 'Visual Studio 18 2026' if major == 18 else 'Visual Studio 17 2022'
    (OUT/'toolchain.json').write_text(json.dumps(selected, indent=2))
    os.environ['PATH'] = str(dxc.parent) + os.pathsep + os.environ['PATH']
    return dxc, generator

def build_probe(dxc, generator):
    build, stage = WORK/'build-probe', OUT/'probe'
    run('probe-configure', ['cmake','-S',ROOT,'-B',build,'-G',generator,'-A','x64',f'-DDXC_EXECUTABLE={dxc}'])
    run('probe-build', ['cmake','--build',build,'--config','Release','--parallel','2'])
    run('probe-install', ['cmake','--install',build,'--config','Release','--prefix',stage])
    shutil.copy2(ROOT/'LICENSE-MIT.txt', stage/'LICENSE.txt')
    shutil.copy2(ROOT/'probe/main.cpp', stage/'main.cpp')
    shutil.copy2(ROOT/'probe/Probe.hlsl', stage/'Probe.hlsl')
    zip_tree(stage, OUT/'RTLabProbe-Windows.zip')

def shaders(dxc):
    target = OUT/'shader-checks'
    target.mkdir(exist_ok=True)
    source = WORK/'cer/shaders/raytracing/ShadowLab/ShadowLab.hlsl'
    for label, profile, inline in [('inline','cs_6_5','1'),('pipeline','lib_6_5','0')]:
        run('shader-'+label, [dxc,'-T',profile,'-E','Main','-DRTLAB_INLINE='+inline,
            '-enable-16bit-types','-WX','-I',WORK/'cer','-Fo',target/(label+'.dxil'),source])
    sdk = Path(os.environ['ProgramFiles(x86)'])/'Windows Kits/10/bin'
    fxcs = sorted(sdk.glob('*/x64/fxc.exe'))
    if not fxcs: raise RuntimeError('Windows SDK fxc.exe missing')
    run('shader-composite', [fxcs[-1],'/T','cs_5_0','/E','main','/WX','/Fo',target/'composite.cso',
        WORK/'cs/features/Raytracing/Shaders/Raytracing/ShadowLabCompositeCS.hlsl'])

def plugins(generator):
    # This directory is owned by this build. CS install removes its prefix!
    stage = OUT/'runtime/Data'
    stage.mkdir(parents=True, exist_ok=True)
    builds = {}
    # Validate the currently failing backend before rebuilding the working host.
    # Installation still happens CS first, because CS clears its install prefix.
    for name, target in [('cer','CreationEngineRaytracing'),('cs','CommunityShaders')]:
        source = WORK/name
        vcpkg = fetch('vcpkg-'+name,'https://github.com/microsoft/vcpkg.git',
                      LOCK[name]['vcpkg'],WORK/('vcpkg-'+name),full_history=True)
        run(name+'-bootstrap', ['cmd','/c',vcpkg/'bootstrap-vcpkg.bat','-disableMetrics'])
        env = os.environ.copy()
        env['VCPKG_ROOT'] = str(vcpkg)
        # CMake embeds this value in generated install scripts; backslashes
        # such as D:\\a are parsed as invalid escape sequences there.
        env['DEPLOY_DIR'] = stage.as_posix()
        env['VCPKG_KEEP_ENV_VARS'] = 'DEPLOY_DIR'
        build = WORK/('build-'+name)
        options = ['-DBUILD_SKYRIM=ON','-DBUILD_FALLOUT4=OFF', '-DENABLE_SKYRIM_SE=ON',
            '-DENABLE_SKYRIM_AE=ON','-DENABLE_SKYRIM_VR=OFF','-DCOMMONLIB_PREBUILT=OFF',
            '-DCOMMONLIB_PREBUILT_MULTICONFIG=OFF','-DSKSE_SUPPORT_XBYAK=ON',
            '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreaded$<$<CONFIG:Debug>:Debug>DLL',
            f'-DCMAKE_TOOLCHAIN_FILE={vcpkg}/scripts/buildsystems/vcpkg.cmake',
            '-DVCPKG_TARGET_TRIPLET=x64-windows-static-md',f'-DVCPKG_OVERLAY_PORTS={source}/cmake/ports',
            '-DBUILD_TESTS=OFF','-DBUILD_BENCHMARKS=OFF']
        if name == 'cs': options += ['-DZIP_TO_DIST=OFF','-DAIO_ZIP_TO_DIST=OFF',
            '-DAUTO_PLUGIN_DEPLOYMENT=OFF','-DBUILD_SHADER_TESTS=OFF','-DTRACY_SUPPORT=OFF']
        else: options += ['-DAUTO_DEPLOYMENT=ON',
            f'-DSHADERMAKE_DXC_PATH={WORK}/dxc/bin/x64/dxc.exe',
            f'-DDXC_PATH={WORK}/dxc/bin/x64/dxc.exe']
        run(name+'-configure',['cmake','-S',source,'-B',build,'-G',generator,'-A','x64',*options],env=env)
        run(name+'-build',['cmake','--build',build,'--config','Release','--target',target,'--parallel','2'],env=env)
        builds[name] = build
    for name in ('cs', 'cer'):
        run(name+'-install',['cmake','--install',builds[name],'--config','Release','--prefix',stage])
    # Match the DXC validator to the compiler supplied by the vcpkg package.
    for p in (WORK/'build-cer/vcpkg_installed/x64-windows-static-md').rglob('dxil.dll'):
        if 'debug' not in p.parts:
            shutil.copy2(p,stage/'SKSE/Plugins/dxil.dll')
            break
    for dll in ('CommunityShaders.dll','CreationEngineRaytracing.dll','dxcompiler.dll','D3D12Core.dll'):
        p = stage/'SKSE/Plugins'/dll
        if not p.is_file() or p.read_bytes()[:2] != b'MZ': raise RuntimeError('Missing/invalid '+dll)
    # Respect upstream logo exclusion. No renaming of the runtime DLL/API identity.
    for p in list(stage.rglob('*')):
        if p.is_file() and 'community shaders logo' in str(p).lower(): p.unlink()
    for p in stage.rglob('*'):
        if p.is_file() and p.stat().st_size < 1024:
            if p.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
                raise RuntimeError('Unresolved LFS pointer: '+str(p))
    notices = OUT/'runtime/licenses'
    shutil.copytree(ROOT/'licenses', notices, dirs_exist_ok=True)
    shutil.copy2(ROOT/'LICENSES.md', notices/'README.md')
    for name in ('cs','cer'):
        for p in (WORK/name).rglob('*'):
            if p.is_file() and '.git' not in p.parts and any(t in p.name.lower() for t in ('license','copying','exceptions','notice')):
                dest = notices/'upstream'/name/p.relative_to(WORK/name)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p,dest)
    for name, build in builds.items():
        for p in (build/'vcpkg_installed').rglob('copyright'):
            destination = notices/name/p.relative_to(build/'vcpkg_installed')
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p,destination)
    shutil.copy2(ROOT/'TESTING_DE.md', OUT/'runtime/TESTING_DE.md')
    shutil.copy2(ROOT.parent/'RT_EXPERIMENT.md', OUT/'runtime/README-FalkosLichtspiel-RT.md')
    for name in ('CLAUDE_REVIEW.md', 'JIAYE_PORT_MAP.md'):
        shutil.copy2(ROOT.parent/name, OUT/'runtime'/name)
    shutil.copy2(ROOT/'sources.lock.json', OUT/'runtime/sources.lock.json')
    # Keep public source and dependency source locally with the binary result.
    # Prebuilt vcpkg caching is disabled in CI so buildtrees contain the built sources.
    archive = OUT/'Corresponding-Source.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        for base, prefix in [(ROOT,'RTLab')]+[(WORK/n,n) for n in ('cs','cer','vcpkg-cs','vcpkg-cer','build-cs','build-cer')]:
            for directory, dirs, files in os.walk(base):
                dirs[:] = [d for d in dirs if d not in ('.git','__pycache__') and
                    not (base == ROOT and d in ('_work','out','validation'))]
                for file in files:
                    p = Path(directory)/file
                    rel = p.relative_to(base)
                    low = str(rel).lower()
                    if 'community shaders logo' in low: continue
                    if base.name.startswith('build-') and not (rel.parts[0] == '_deps' or file.endswith(('.cmake','.json'))): continue
                    if p.suffix.lower() in ('.obj','.pch','.pdb','.exe','.dll','.lib','.zip','.7z','.tar','.gz'): continue
                    if p.is_file(): z.write(p, str(Path(prefix)/rel))
    mo2_package(OUT/'runtime', OUT/'FalkosLichtspiel-RT-MO2.zip')

DOCS_DIR = 'FalkosLichtspiel RT Docs'

def mo2_package(runtime, output):
    """MO2 installs an archive's root into the virtual Data folder.

    Game files (SKSE/, Shaders/, ...) therefore sit at the archive root, and
    documentation/notices go into one clearly named subfolder. A top-level
    Data/ folder next to other files makes MO2 fall back to manual install.
    """
    data = runtime/'Data'
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for p in sorted(data.rglob('*')):
            if p.is_file(): z.write(p, p.relative_to(data).as_posix())
        for p in sorted(runtime.rglob('*')):
            if p.is_file() and data not in p.parents:
                z.write(p, (Path(DOCS_DIR)/p.relative_to(runtime)).as_posix())
    with zipfile.ZipFile(output) as z:
        names = set(z.namelist())
    required = ['SKSE/Plugins/CommunityShaders.dll', 'SKSE/Plugins/CreationEngineRaytracing.dll']
    missing = [n for n in required if n not in names]
    if missing or any(n.lower().startswith('data/') for n in names):
        raise RuntimeError(f'Invalid MO2 layout, missing={missing}')

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--probe-only',action='store_true')
    args = p.parse_args()
    if os.name != 'nt': raise RuntimeError('Full plugin build requires Windows/MSVC. Use the supplied GitHub Actions workflow.')
    OUT.mkdir(exist_ok=True)
    dxc,generator = tools()
    build_probe(dxc,generator)
    if not args.probe_only:
        prepare()
        run('gi-permutations', [sys.executable, ROOT/'scripts/check_gi_shaders.py',
            '--cer', WORK/'cer', '--dxc', dxc])
        run('rr-restir-shaders', [sys.executable, ROOT/'scripts/check_rt_shaders.py',
            '--cer', WORK/'cer', '--dxc', dxc])
        shaders(dxc)
        plugins(generator)
    (OUT/'BUILD-STATUS.txt').write_text('BUILD PASSED. GPU execution and Skyrim runtime NOT tested by CI.\n')

if __name__ == '__main__':
    try: main()
    except Exception:
        (OUT/'logs').mkdir(parents=True,exist_ok=True)
        (OUT/'logs/FAILURE.txt').write_text(traceback.format_exc())
        traceback.print_exc()
        sys.exit(1)
