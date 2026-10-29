"""Stage and verify a directly installable MO2 archive after a successful host build."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import zipfile
from prepare import ROOT, LOCK


def archive(folder, destination):
    with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED, allowZip64=True) as z:
        for p in sorted(folder.rglob('*')):
            if p.is_file(): z.write(p, p.relative_to(folder).as_posix())
    with zipfile.ZipFile(destination) as z:
        bad = z.testzip()
        if bad: raise RuntimeError('Corrupt archive member: '+bad)


def package(source, build, work, out, generator, run):
    stage = out/'stage-FalkosLichtspiel'
    run('cs-install', ['cmake','--install',build,'--config','Release','--prefix',stage.as_posix()])
    module_build = work/'build-diagnostics'
    run('module-configure', ['cmake','-S',ROOT,'-B',module_build,'-G',generator,'-A','x64'])
    run('module-build', ['cmake','--build',module_build,'--config','Release','--parallel','2'])
    run('module-tests', ['ctest','--test-dir',module_build,'-C','Release','--output-on-failure'])
    plugin = stage/'SKSE/Plugins/RTLab'
    plugin.mkdir(parents=True, exist_ok=True)
    shutil.copy2(module_build/'Release/RTLab.Diagnostics.dll',plugin/'RTLab.Diagnostics.dll')
    shutil.copy2(ROOT/'RTLab.ini',plugin/'RTLab.ini')
    shutil.copy2(ROOT/'INSTALL_FALKOSLICHTSPIEL.md',stage/'INSTALL_FALKOSLICHTSPIEL.md')
    shutil.copy2(out/'host-manifest.json',stage/'FalkosLichtspiel-build.json')
    # The upstream logo has no redistribution license. Text-only header is intentional.
    for p in list(stage.rglob('*')):
        if p.is_file() and ('community shaders logo' in str(p).lower() or p.suffix.lower()=='.pdb'): p.unlink()
    for name in ['SKSE/Plugins/CommunityShaders.dll','SKSE/Plugins/RTLab/RTLab.Diagnostics.dll']:
        if not (stage/name).is_file() or (stage/name).read_bytes()[:2] != b'MZ':
            raise RuntimeError('Missing/invalid '+name)
    if not (stage/'Shaders/Lighting.hlsl').is_file(): raise RuntimeError('Missing shader package')
    for p in stage.rglob('*'):
        if p.is_file() and p.stat().st_size < 1024 and p.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
            raise RuntimeError('Unresolved LFS pointer: '+str(p))
    licenses=stage/'FalkosLichtspiel-Licenses'
    shutil.copytree(ROOT/'licenses',licenses,dirs_exist_ok=True)
    for base,label in [(source,'cs'),(build/'vcpkg_installed','dependencies')]:
        for p in base.rglob('*'):
            if p.is_file() and '.git' not in p.parts and any(t in p.name.lower() for t in ['copyright','license','copying','exceptions','notice']):
                target=licenses/label/p.relative_to(base);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    # Matching project, upstream, submodule and downloaded dependency sources.
    with zipfile.ZipFile(out/'FalkosLichtspiel-Sources.zip','w',zipfile.ZIP_DEFLATED,allowZip64=True) as z:
        for base,label in [(ROOT,'fork'),(source,'cs'),(work/'vcpkg','vcpkg'),(build/'_deps','build-deps')]:
            if not base.exists(): continue
            for directory,dirs,files in os.walk(base):
                dirs[:]=[d for d in dirs if d not in ('.git','__pycache__','node_modules') and not (base==ROOT and d in ('_work','out','build'))]
                for name in files:
                    p=Path(directory)/name
                    if 'community shaders logo' in str(p).lower(): continue
                    if p.suffix.lower() in ('.obj','.pch','.pdb','.dll','.exe','.lib','.zip','.7z','.nupkg'): continue
                    z.write(p, str(Path(label)/p.relative_to(base)))
    archive(stage,out/'FalkosLichtspiel-MO2.zip')
    sums={p.name:hashlib.file_digest(p.open('rb'),'sha256').hexdigest() for p in out.glob('FalkosLichtspiel-*.zip')}
    (out/'SHA256.json').write_text(json.dumps(sums,indent=2),encoding='utf-8')
