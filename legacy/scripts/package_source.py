"""Create the iPad upload package without build trees, upstream assets or binaries."""
from pathlib import Path
import hashlib
import html
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT.parent/'deliverables-v2'

def package():
    DEST.mkdir(exist_ok=True)
    source = DEST/'SkyrimRTLab-source.zip'
    entries = []
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob('*')):
            rel = p.relative_to(ROOT)
            if any(part in ('_work','out','__pycache__') for part in rel.parts): continue
            if not p.is_file() or p.suffix.lower() in ('.exe','.pyc','.obj'): continue
            z.write(p,rel)
            entries.append({'path':str(rel),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        z.writestr('FILE-HASHES.json',json.dumps(entries,indent=2))
    workflow = (ROOT/'.github/workflows/build.yml').read_text()
    start = '''<!doctype html><html lang="de"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Skyrim RT Lab — Start</title>
<style>body{font:18px/1.55 system-ui;max-width:850px;margin:32px auto;padding:0 20px;color:#182434;background:#f4f6f9}textarea{box-sizing:border-box;width:100%;height:55vh;font:13px/1.5 monospace}code{background:#e1e6ed;padding:3px}li{margin-bottom:16px}</style>
<h1>Skyrim RT Lab v2</h1><p>Zuerst ERGEBNIS_V2.md lesen: GI-/NRD-Codekorrekturen,
acht erfolgreich kompilierte GI-Shadervarianten. Noch kein Drop-in-Plugin für öffentliches CS.
Die Skyrim-DLLs sind noch nicht gebaut oder im Spiel getestet. Der separate DXR-Test und die
neuen RT-Shader wurden kompiliert; kein GPU-Lauf wurde hier durchgeführt.</p>
<ol><li>In Safari ein eigenes GitHub-Repository öffnen. Über <b>Add file → Upload files</b>
die Datei <code>SkyrimRTLab-source.zip</code> in die oberste Ebene hochladen und committen.
Dieses innere ZIP muss nicht entpackt werden.</li>
<li><b>Add file → Create new file</b>: Dateiname <code>.github/workflows/build.yml</code>.
Den gesamten Text unten markieren, kopieren und in den Editor einfügen. Committen.</li>
<li><b>Actions → Skyrim RT Lab Windows build → Run workflow</b>. Für beide Skyrim-DLLs
<code>probe_only</code> ausgeschaltet lassen.</li>
<li>Bei Erfolg die Artefakte <code>SkyrimRTLab-Windows-and-Sources</code> und
<code>RTLabProbe-Windows</code> herunterladen. Bei Fehlern <code>RTLab-Diagnostics</code>.</li>
<li>Später auf Windows zuerst <code>Run-Probe.cmd</code> ausführen. Für Skyrim unbedingt
<code>TESTING_DE.md</code> lesen; Engine Fixes und Crash Logger werden vom Backend verlangt.</li></ol>
<p>GitHub entpackt hochgeladene ZIPs nicht automatisch. Deshalb ist Schritt 2 einmal nötig.
Falls Menüs fehlen: Safari → Desktop-Website anfordern. Keine ChatGPT-Kontoverbindung nötig.</p>
<h2>Workflow zum Kopieren</h2><textarea readonly aria-label="Vollständiger GitHub Actions Workflow">'''+html.escape(workflow)+'''</textarea>
<p>Kein offizieller Release von Community Shaders, Open Shaders oder Gistix.</p></html>'''
    final = DEST/'SkyrimRTLab-v2.zip'
    with zipfile.ZipFile(final,'w',zipfile.ZIP_DEFLATED) as z:
        z.write(source,source.name)
        z.writestr('build.yml',workflow)
        z.writestr('START-HERE.html',start)
        z.write(ROOT/'README_DE.md','README_DE.md')
        z.write(ROOT/'TESTING_DE.md','TESTING_DE.md')
        z.write(ROOT/'ERGEBNIS_V2.md','ERGEBNIS_V2.md')
    with zipfile.ZipFile(final) as z: assert z.testzip() is None
    with zipfile.ZipFile(source) as z:
        assert z.testzip() is None
        required=['CMakeLists.txt','scripts/build_windows.py','scripts/modify.py','probe/main.cpp',
            'overlay/cer/src/Pass/Raytracing/ShadowLab.cpp','.github/workflows/build.yml']
        assert all(name in z.namelist() for name in required)
    print(final,final.stat().st_size,'bytes',len(entries),'project files')

if __name__ == '__main__': package()
