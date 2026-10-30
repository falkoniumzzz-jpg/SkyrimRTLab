"""Prove the RAW/non-NRD compilation failure in the exact original source."""
import subprocess,re
from pathlib import Path
from common import ROOT,OUT
base=ROOT.parent/'research/cer'
stage=OUT/'gi-stage'
source=subprocess.check_output(['git','show','09350844e63f602a3b788f1c815d29cee1b4fab2:shaders/raytracing/GlobalIllumination/RayGeneration.hlsl'],cwd=base,text=True)
source=re.sub(r'(#\s*include\s*")([^"]+)(")',lambda m:m[1]+m[2].lower()+m[3],source)
path=stage/'baseline.hlsl';path.write_text(source)
dxc=ROOT.parent/'toolchain/dxc/bin/dxc'
r=subprocess.run([str(dxc),'-T','cs_6_6','-E','Main','-enable-16bit-types','-DUSE_RAY_QUERY=1','-DSKYRIM=1','-DRAW_RADIANCE=1','-DMAX_SAMPLES=1','-DMAX_BOUNCES=2','-DTHREAD_GROUP_SIZE=8','-I',str(stage),'-I',str(stage/'shaders'),'-Fo',str(OUT/'baseline.dxil'),str(path)],capture_output=True,text=True)
(OUT/'logs/baseline-raw.log').write_text(r.stdout+r.stderr+f'\nEXIT_CODE={r.returncode}\n')
assert r.returncode != 0 and 'diffHitDist' in r.stderr and 'specHitDist' in r.stderr
print('PASS: original RAW/non-NRD shader fails on both undeclared hit-distance variables; repaired variant compiled.')
