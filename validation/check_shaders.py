"""Compile a focused matrix of real SSGI and refractive-rain shaders with SDK FXC."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'fork/scripts'))
from prepare import ROOT, LOCK, prepare


def main():
    source = ROOT/'_work/shader-source'
    out = ROOT/'out/shader-checks'
    out.mkdir(parents=True, exist_ok=True)
    manifest = prepare(source)
    stage = ROOT/'_work/shader-stage'
    shutil.copytree(source/'package/Shaders',stage,dirs_exist_ok=True)
    for feature in sorted((source/'features').iterdir()):
        if (feature/'Shaders').is_dir():
            shutil.copytree(feature/'Shaders',stage,dirs_exist_ok=True)
    sdk=Path(os.environ['ProgramFiles(x86)'])/'Windows Kits/10/bin'
    compilers=sorted(sdk.glob('*/x64/fxc.exe'))
    if not compilers: raise RuntimeError('Windows SDK FXC missing')
    compiler=compilers[-1]
    cases=[]
    for resolution in ('FULL','HALF_RES','QUARTER_RES'):
        for linear in (False,True):
            defines=['CSHADER','GI','TEMPORAL_DENOISER']
            if resolution!='FULL':defines.append(resolution)
            if linear:defines.append('ENABLE_LL')
            for path in sorted((stage/'ScreenSpaceGI').glob('*.cs.hlsl')):
                case_defines=defines+(['LINEAR_FILTER'] if path.name=='prefilterDepths.cs.hlsl' else [])
                cases.append((f'{resolution}-LL{int(linear)}-{path.stem}',path,'cs_5_0',case_defines))
    for linear in (False,True):
        for stage_define,profile in [('VSHADER','vs_5_0'),('PSHADER','ps_5_0')]:
            defines=[stage_define,'ENVCUBE','RAIN','RAIN_REFRACTION','DYNAMIC_CUBEMAPS']
            if linear:defines.append('ENABLE_LL')
            cases.append((f'rain-{profile}-LL{int(linear)}',stage/'Particle.hlsl',profile,defines))
    results=[]
    for label,path,profile,defines in cases:
        cmd=[str(compiler),'/nologo','/T',profile,'/E','main','/I',str(stage),'/Fo',str(out/(label+'.cso'))]
        for define in defines:cmd+=['/D',define]
        cmd.append(str(path))
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/(label+'.log')).write_bytes(p.stdout)
        print(f'{label}: exit={p.returncode}',flush=True)
        if p.returncode:print(p.stdout.decode('utf-8',errors='replace'),flush=True)
        results.append({'label':label,'file':str(path.relative_to(stage)),'defines':defines,'exit':p.returncode})
    (out/'results.json').write_text(json.dumps({'source':manifest,'fxc':str(compiler),'cases':results},indent=2),encoding='utf-8')
    if any(r['exit'] for r in results):raise RuntimeError('Shader failures; inspect per-case logs')
    print(f'PASS: {len(results)} SSGI/rain permutations. No GPU execution or image-quality test.',flush=True)

if __name__=='__main__':main()
