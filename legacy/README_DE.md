# Skyrim RT Lab v2 — GI-/NRD-Reparaturstand

**Zuerst `ERGEBNIS_V2.md` lesen.** Stand 27.10.2026: GI-Depth-Sampling, RAW-Shader-
Compilerfehler, NRD-History-Reset und verzögerte NRD-Initialisierung wurden geändert.
Acht reale GI-Compute-Shadervarianten wurden erfolgreich kompiliert. Der vollständige
MSVC-Build und Skyrim-Tests fehlen. Kein fertiges Drop-in-Plugin für öffentliches CS.
Die folgenden Abschnitte dokumentieren die geerbte Build-/Probe-Basis vom 23.10.;
die v2-Ergebnisse und GI-Testeinstellungen haben Vorrang.

Stand: 23. Oktober 2026. Kein offizieller Community-Shaders-Release.

Dieses Projekt ergänzt den tatsächlich vorhandenen Raytracing-Zweig von Community
Shaders und Gistix' Creation Engine Raytracing um eine kleine Schatten-Diagnoseansicht.
Es enthält C++, HLSL, nachvollziehbare Quellcodeänderungen, einen unabhängigen
DXR-Hardwaretest und einen automatisierten Windows-Build.

**Wichtig: Die Skyrim-DLLs wurden hier nicht erfolgreich gebaut oder im Spiel getestet.**
Der unabhängige Windows-Test wurde mit MinGW cross-kompiliert; die zwei neuen
Raytracing-Shadervarianten und sein Compute-Shader wurden mit Microsoft DXC kompiliert.
Das beweist weder die Ausführung auf einer GPU noch die Funktionsfähigkeit der Skyrim-Integration.
Die tatsächlich ausgeführten Prüfungen stehen in `validation/RESULTS.md`.

## Vom iPad aus bauen

1. Das äußere ZIP in „Dateien“ entpacken. `SkyrimRTLab-source.zip` **nicht** entpacken,
   sondern über Safari in die oberste Ebene eines eigenen GitHub-Repositories hochladen.
2. In GitHub **Add file → Create new file** wählen. Als Dateinamen
   `.github/workflows/build.yml` eingeben. Den vollständigen Text aus der mitgelieferten
   `build.yml` einfügen und committen. Die äußere `START-HERE.html` enthält dafür ein Textfeld.
3. Unter **Actions → Skyrim RT Lab Windows build → Run workflow** starten.
   `probe_only` ausgeschaltet lassen für beide Skyrim-DLLs. Der erste Build lädt viele
   Abhängigkeiten; ein schneller Durchlauf ist nicht zugesagt.
4. Bei Erfolg `SkyrimRTLab-Windows-and-Sources` und `RTLabProbe-Windows` herunterladen.
   GitHub verpackt die Artefakte nochmals als ZIP. Bei Fehlern `RTLab-Diagnostics` herunterladen.
5. Erst auf Windows die Anleitung `TESTING_DE.md` ausführen. Das iPad führt DXR nicht aus.

Dieser eine zusätzliche Webeditor-Schritt ist unvermeidbar: GitHub aktiviert einen
Workflow nicht aus einem nur hochgeladenen ZIP. Eine Verbindung deines GitHub-Kontos
mit ChatGPT ist nicht nötig. Es wurde hier kein Workflow in deinem Konto ausgeführt.
Falls Safari Funktionen versteckt, „Desktop-Website anfordern“ verwenden.

## Inhalt und tatsächlicher Umfang

| Teil | Status |
|---|---|
| Native DXR-Probe mit zwei Dreiecken, BLAS/TLAS, Inline-RayQuery | Windows-EXE cross-kompiliert; GPU-Ausführung offen |
| Neue Sonnen-Schatten-Diagnose, Inline-DXR und DXR-Pipeline/SBT | Beide HLSL-Varianten kompiliert; C++-Integration ungetestet |
| Geometrieextraktion, Skinning, BLAS/TLAS-Lebensdauer | Aus vorhandenem CER übernommen; nicht neu erfunden |
| DX11/DX12-Interop, Shared Textures/Fences | Vorhandenes Backend, ergänzt um explizites DX11-Flush |
| Settings-Abgleich und paarweiser DLL-ABI-Stempel | Implementiert; Quellcodeprüfung bestanden |
| Windows-Gesamtbuild | Workflow und Skripte vorhanden, hier nicht ausgeführt |
| RTGI, Reflexionen, mehrfache PT-Bounces, NRD | Upstream-Code vorhanden, nicht durch dieses Paket validiert |
| Fertige Schatten in der normalen Spielbeleuchtung | Noch nicht implementiert; Diagnose ersetzt RGB getroffener Flächen |

Die Schattenberechnung verwendet echte Dreiecks-Acceleration-Structures und GPU-Raytracing.
Es ist kein Screen-Space-Schattenfilter. In der Diagnose werden alle Dreiecke als
undurchsichtig behandelt. Blattkarten, Haare, Glas und Wasser sind deshalb nicht korrekt.

## Entwicklung

Auf Windows: Python 3.12, Git mit LFS, Visual Studio 2022/2026 C++ und Windows SDK,
`python -m pip install cmake==4.2.3 ninja`, dann `python scripts/build_windows.py`.
Für den unabhängigen Test allein: `python scripts/build_windows.py --probe-only`.
Das Root-CMake-Projekt baut die Probe. Die Plugins nutzen ihre echten Upstream-CMake-Projekte.
Quellen und Abhängigkeiten werden nach `_work` geladen, Ergebnisse nach `out` geschrieben.
Der Installer benutzt ausschließlich `out/runtime/Data`; dieser Ordner wird beim CS-Install
neu erstellt. Niemals diesen Install-Prefix auf einen bestehenden Skyrim-Data-Ordner umstellen.

Siehe `RESEARCH_DE.md`, `ARCHITECTURE_DE.md`, `TESTING_DE.md` und `LICENSES.md`.
