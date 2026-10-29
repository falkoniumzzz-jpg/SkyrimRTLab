"""Build current-CS host in isolation. Produces build evidence, not an RT release."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import traceback
from prepare import ROOT, LOCK, prepare

WORK = ROOT / '_work'
OUT = ROOT / 'out'

def run(label, command, cwd=None, env=None):
    print(label, flush=True)
    with (OUT / (label + '.log')).open('w', encoding='utf-8') as log:
        p = subprocess.run([str(x) for x in command], cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    if p.returncode:
        raise RuntimeError(f'{label} failed with exit code {p.returncode}; see {label}.log')

def build():
    if os.name != 'nt': raise RuntimeError('Full host requires Windows/MSVC')
    source = WORK / 'cs'
    manifest = prepare(source)
    (OUT / 'host-manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    run('submodules', ['git','-c','core.longpaths=true','submodule','update','--init','--recursive','--depth','1'], cwd=source)
    run('lfs', ['git','lfs','pull'], cwd=source)
    run('streamline-lfs', ['git','lfs','pull'], cwd=source / 'extern/Streamline-DX12')
    vcpkg = WORK / 'vcpkg'
    if not vcpkg.exists():
        run('vcpkg-clone', ['git','clone','https://github.com/microsoft/vcpkg.git', vcpkg])
    run('vcpkg-checkout', ['git','checkout','--detach',LOCK['cs']['vcpkg']], cwd=vcpkg)
    run('vcpkg-bootstrap', ['cmd','/c',vcpkg / 'bootstrap-vcpkg.bat','-disableMetrics'])
    vswhere = Path(os.environ['ProgramFiles(x86)']) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    installs = json.loads(subprocess.check_output([str(vswhere),'-products','*','-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64','-format','json'], text=True))
    candidates = sorted([x for x in installs if x['installationVersion'].split('.')[0] in ('17','18')],
                        key=lambda x: tuple(map(int,x['installationVersion'].split('.'))))
    if not candidates: raise RuntimeError('VS 2022/2026 C++ tools missing')
    vs = candidates[-1]
    generator = 'Visual Studio 18 2026' if vs['installationVersion'].startswith('18.') else 'Visual Studio 17 2022'
    (OUT / 'toolchain.json').write_text(json.dumps(vs, indent=2), encoding='utf-8')
    env = os.environ.copy()
    env['VCPKG_ROOT'] = str(vcpkg)
    env['VCPKG_DISABLE_METRICS'] = '1'
    target = WORK / 'build-cs'
    options = [f'-DCMAKE_TOOLCHAIN_FILE={vcpkg.as_posix()}/scripts/buildsystems/vcpkg.cmake',
        f'-DVCPKG_OVERLAY_PORTS={source.as_posix()}/cmake/ports',
        f'-DVCPKG_OVERLAY_TRIPLETS={source.as_posix()}/cmake/triplets',
        '-DVCPKG_TARGET_TRIPLET=x64-windows-static-md-release',
        '-DCMAKE_MSVC_RUNTIME_LIBRARY=MultiThreadedDLL',
        '-DENABLE_SKYRIM_SE=ON','-DENABLE_SKYRIM_AE=ON','-DENABLE_SKYRIM_VR=OFF',
        '-DCOMMONLIB_PREBUILT=OFF','-DCOMMONLIB_PREBUILT_MULTICONFIG=OFF',
        '-DSKSE_SUPPORT_XBYAK=ON','-DDEVBENCH_BRIDGE=OFF','-DZIP_TO_DIST=OFF',
        '-DAIO_ZIP_TO_DIST=OFF','-DAUTO_PLUGIN_DEPLOYMENT=OFF','-DTRACY_SUPPORT=OFF',
        '-DCMAKE_INTERPROCEDURAL_OPTIMIZATION=OFF','-DSC_COMPILE_PDB=OFF']
    run('cs-configure',['cmake','-S',source,'-B',target,'-G',generator,'-A','x64',*options],env=env)
    run('cs-build',['cmake','--build',target,'--config','Release','--target','CommunityShaders','--parallel','2'],env=env)
    dlls = list(target.rglob('CommunityShaders.dll'))
    if not dlls or any(p.read_bytes()[:2] != b'MZ' for p in dlls): raise RuntimeError('Missing/invalid CS DLL')
    (OUT / 'STATUS.txt').write_text('Host compiled. No Skyrim execution. No CER integration, no RT rendering.\n', encoding='utf-8')

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        build()
    except Exception:
        (OUT / 'FAILURE.txt').write_text(traceback.format_exc(), encoding='utf-8')
        raise
