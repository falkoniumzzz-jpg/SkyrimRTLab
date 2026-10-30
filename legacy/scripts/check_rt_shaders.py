"""Compile the actual RR/hybrid producer and RTXDI consumers, not substitute shaders."""
import argparse
import re
from pathlib import Path
from common import OUT, run

def check(cer, dxc):
    stage = OUT/'rt-stage'
    for folder in ('shaders', 'interop', 'extern/RTXDI-Library/Include'):
        for source in (cer/folder).rglob('*'):
            if not source.is_file(): continue
            rel = source.relative_to(cer/folder) if folder.startswith('extern/') else source.relative_to(cer)
            target = stage/str(rel).lower()
            target.parent.mkdir(parents=True, exist_ok=True)
            data = re.sub(rb'(#\s*include\s*["<])([^">]+)([">])',
                lambda m: m[1]+m[2].replace(b'\\',b'/').lower()+m[3], source.read_bytes())
            target.write_bytes(data)
    results=[]
    def compile(label, source, defines, profile='cs_6_6', entry='Main'):
        args=[dxc, '-T', profile, '-enable-16bit-types', '-I',stage,'-I',stage/'shaders',
            '-Fo',OUT/(label+'.dxil'), *['-D'+d for d in ['SKYRIM=1','GAME_DEF=1']+defines], stage/source]
        if entry: args[1:1]=['-E',entry]
        run(label,args)
        results.append(label)
    common=['MAX_SAMPLES=1','MAX_BOUNCES=2','THREAD_GROUP_SIZE=8','RUSSIAN_ROULETTE=1']
    for mode,defs in [('rr',['DLSS_RR=1']),('hybrid',['HYBRID_RESTIR=1']),('rr-hybrid',['DLSS_RR=1','HYBRID_RESTIR=1'])]:
        for profile,query in [('cs_6_6','1'),('lib_6_6','0')]:
            compile(mode+'-'+query,'shaders/raytracing/globalillumination/raygeneration.hlsl',
                common+defs+['USE_RAY_QUERY='+query],profile, 'Main' if query=='1' else None)
    for mode,defs in [('pt',[]),('hybrid',['HYBRID_RESTIR=1']),('rr-hybrid',['HYBRID_RESTIR=1','DLSS_RR=1','MAX_SAMPLES=1'])]:
        for shader in ('gitemporalresampling','gispatialresampling','gifusedresampling','gifinalshading'):
            compile(mode+'-'+shader,'shaders/raytracing/rtxdi/restirgi/'+shader+'.hlsl',defs+['USE_RAY_QUERY=1'])
    compile('rr-postprocess','shaders/postprocess.hlsl',['DLSS_RR=1'],'cs_6_6','main')
    (OUT/'RT-SHADERS-PASSED.txt').write_text('\n'.join(results)+'\n')
    print(f'PASS: {len(results)} real RR / ReSTIR shader permutations')

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--cer',type=Path,required=True)
    p.add_argument('--dxc',required=True)
    a=p.parse_args()
    check(a.cer,a.dxc)
