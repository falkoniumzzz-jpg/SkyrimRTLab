"""Compile real GI permutations. Lower-case staging emulates Windows include casing on Linux."""
import argparse
import re
import shutil
from pathlib import Path
from common import OUT, run

p=argparse.ArgumentParser()
p.add_argument('--cer',type=Path,required=True)
p.add_argument('--dxc',required=True)
a=p.parse_args()
stage=OUT/'gi-stage'
for folder in ('shaders','interop'):
    for source in (a.cer/folder).rglob('*'):
        if not source.is_file(): continue
        rel=source.relative_to(a.cer)
        target=stage/str(rel).lower()
        target.parent.mkdir(parents=True,exist_ok=True)
        # Only include paths need rewriting. Preserve all other bytes, including
        # upstream comments, without depending on the Windows ANSI code page.
        data=source.read_bytes()
        data=re.sub(rb'(#\s*include\s*")([^"]+)(")',
                    lambda m:m[1]+m[2].replace(b'\\',b'/').lower()+m[3],data)
        target.write_bytes(data)
for name,defines in [('plain',[]),('raw',['RAW_RADIANCE']),('reblur',['RAW_RADIANCE','NRD','NRD_REBLUR']),('relax',['RAW_RADIANCE','NRD'])]:
    for spp in (1,2):
        run(f'gi-{name}-{spp}',[a.dxc,'-T','cs_6_6','-E','Main','-enable-16bit-types',
            '-DUSE_RAY_QUERY=1','-DSKYRIM=1',f'-DMAX_SAMPLES={spp}','-DMAX_BOUNCES=2','-DTHREAD_GROUP_SIZE=8',
            *['-D'+d+'=1' for d in defines],'-I',stage,'-I',stage/'shaders',
            '-Fo',OUT/f'gi-{name}-{spp}.dxil',stage/'shaders/raytracing/globalillumination/raygeneration.hlsl'])
