import argparse
import json
import shutil
from common import ROOT, WORK, LOCK, fetch, run
from modify import modify
from validate import check

def prepare(skip_submodules=False):
    for name in ('cs', 'cer'):
        info = LOCK[name]
        target = fetch(name, info['url'], info['commit'], WORK/name)
        run(name+'-longpaths', ['git','config','core.longpaths','true'], target)
        if not skip_submodules:
            # CS contains an unused NRD gitlink without a .gitmodules URL.
            run(name+'-submodules', ['git','-c','core.longpaths=true','submodule','update','--init','--depth','1','--',*info['submodules']], target)
            run(name+'-commonlib', ['git','submodule','update','--init','--recursive','--depth','1'], target/'extern/CommonLibSSE-NG')
            if name == 'cer':
                run('nvrhi-headers', ['git','submodule','update','--init','--depth','1','--','thirdparty/DirectX-Headers','thirdparty/Vulkan-Headers'], target/'extern/NVRHI')
            elif shutil.which('git-lfs'):
                run('cs-lfs', ['git','lfs','pull'], target)
                run('streamline-lfs', ['git','lfs','pull'], target/'extern/Streamline-DX12')
        if json.loads((target/'vcpkg.json').read_text())['builtin-baseline'] != info['vcpkg']:
            raise RuntimeError(name+' vcpkg baseline mismatch')
    # Legacy repair anchors include the old ABI marker. Unwind only our exact
    # final delta before invoking them, so repeated preparation stays idempotent.
    from apply_rt import remove_if_applied
    remove_if_applied(WORK/'cs', WORK/'cer')
    modify(ROOT, WORK/'cs', WORK/'cer')
    from repair_gi import repair
    repair(WORK/'cer')
    from apply_rt import apply
    apply(WORK/'cs', WORK/'cer')
    check(WORK/'cs', WORK/'cer')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--skip-submodules', action='store_true')
    prepare(p.parse_args().skip_submodules)
