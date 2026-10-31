"""Apply checked RT experiment deltas after the existing legacy repairs.

Each source receives an ordered patch series. The first entry is the RT
experiment delta; later entries are independently reviewable follow-up fixes.
"""
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

PATCHES={
    'cs': ['cs-rt.patch', 'cs-rr-review.patch'],
    'cer': ['cer-rt.patch'],
}

def _git(source, patch, *args):
    return subprocess.run(['git','apply',*args,'-'],cwd=source,input=patch,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE)

def remove_if_applied(cs,cer):
    """Unwind only our exact delta before re-running older preparation repairs."""
    for name,source in [('cs',cs),('cer',cer)]:
        for patch_name in reversed(PATCHES[name]):
            patch=(ROOT/patch_name).read_bytes()
            if _git(source, patch, '--reverse', '--check').returncode == 0:
                result=_git(source, patch, '--reverse')
                if result.returncode:
                    raise RuntimeError(result.stderr.decode(errors='replace'))
            elif patch_name == PATCHES[name][0]:
                marker=source/('include/CreationEngineRaytracing.h' if name=='cs' else 'src/API.cpp')
                if marker.exists() and 'GetHybridRRInputs' in marker.read_text():
                    raise RuntimeError(f'{name}: different RT patch or local edits; use a separate pinned source directory')

def apply(cs,cer):
    for name,source in [('cs',cs),('cer',cer)]:
        for patch_name in PATCHES[name]:
            patch=(ROOT/patch_name).read_bytes()
            if _git(source, patch, '--reverse', '--check').returncode==0:
                continue
            check=_git(source, patch, '--check')
            if check.returncode:
                raise RuntimeError(f'{name} {patch_name} cannot apply: '+check.stderr.decode(errors='replace'))
            result=_git(source, patch)
            if result.returncode: raise RuntimeError(result.stderr.decode(errors='replace'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--cs',type=Path,required=True)
    p.add_argument('--cer',type=Path,required=True)
    a=p.parse_args()
    apply(a.cs,a.cer)
