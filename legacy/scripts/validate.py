"""Compare ordered declarations, not guessed binary sizes. MSVC ABI remains a build check."""
import re
from pathlib import Path
import argparse

def declarations(source):
    source = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
    result = {}
    for m in re.finditer(r'\b(struct|enum class|enum struct)\s+(\w+)\s*(?::[^{}]+)?\{', source):
        depth, end = 1, m.end()
        while depth:
            depth += (source[end] == '{') - (source[end] == '}')
            end += 1
        body = source[m.end():end-1]
        if m[1].startswith('enum'):
            result[m[2]] = [re.sub(r'\s+', '', s) for s in body.split(',') if s.strip()]
        else:
            fields = []
            for line in body.splitlines():
                line = re.sub(r'\s*=.*', ';', line.strip())
                if ';' in line and not any(x in line for x in ('operator', '(', 'return')):
                    fields.append(re.sub(r'\s+', ' ', line))
            result[m[2]] = fields
    return result

def check(cs, cer):
    host = declarations((cs/'include/CreationEngineRaytracing.h').read_text())
    backend = declarations((cer/'src/Types/Settings.h').read_text())
    assert 'Settings' in backend
    for name, fields in backend.items():
        if host.get(name) != fields: raise RuntimeError(f'ABI declaration drift: {name}: {host.get(name)} != {fields}')
    api = (cer/'src/API.h').read_text()
    assert 'SharedTexture* depth, SharedTexture* motionVector, SharedTexture* main, SharedTexture* diffuseAlbedo' in api
    print(f'PASS: {len(backend)} ordered settings/enum declarations, four-array shared-texture API')

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--cs', type=Path, required=True)
    p.add_argument('--cer', type=Path, required=True)
    a = p.parse_args()
    check(a.cs, a.cer)
