"""Apply checked RT experiment deltas after the existing legacy repairs."""
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def apply(cs,cer):
    for name,source in [('cs',cs),('cer',cer)]:
        patch=(ROOT/(name+'-rt.patch')).read_bytes()
        def git(*args):
            return subprocess.run(['git','apply',*args,'-'],cwd=source,input=patch,
                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if git('--reverse','--check').returncode==0:
            continue
        check=git('--check')
        if check.returncode:
            raise RuntimeError(f'{name} RT patch cannot apply: '+check.stderr.decode(errors='replace'))
        result=git()
        if result.returncode: raise RuntimeError(result.stderr.decode(errors='replace'))

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--cs',type=Path,required=True)
    p.add_argument('--cer',type=Path,required=True)
    a=p.parse_args()
    apply(a.cs,a.cer)
