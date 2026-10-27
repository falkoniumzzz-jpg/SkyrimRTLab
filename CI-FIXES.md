# CI-Korrekturen

## 2026-10-27: Windows-Zeichenkodierung

Run 40565199008 hat RTLabProbe.exe erfolgreich mit MSVC gebaut. Die Vorbereitung der GI-Shader brach anschließend in check_gi_shaders.py mit UnicodeEncodeError unter cp1252 ab.

Die Shader werden jetzt als Bytes kopiert; nur ASCII-Include-Pfade werden normalisiert. Damit bleiben Kommentare unverändert und die lokale Windows-Codepage spielt keine Rolle. PYTHONUTF8=1 gilt zusätzlich für alle Python-Schritte im Workflow. Acht GI-Varianten wurden nach der Änderung mit DXC unter Linux erfolgreich kompiliert. Die Windows-Nachprüfung und der vollständige Skyrim-Build stehen noch aus.

## 2026-10-27: Vollständige vcpkg-Historie

Run 40571463222 bestätigt die Encoding-Korrektur: acht GI-Varianten, beide ShadowLab-DXR-Varianten und FXC-Compositing kompilieren unter Windows. Danach scheitert cs-configure, weil die flache vcpkg-Kopie die historischen Port-Trees für detours@4.0.1#8 und directx-headers@1.614.1 nicht enthält.

Beide vcpkg-Repositories werden jetzt mit vollständiger Historie bis zum unveränderten Baseline-Commit geladen. Vorhandene flache Checkouts werden ohne Änderung von HEAD vervollständigt. Lokaler Git-Regressionstest bestanden: historische Trees sind danach in neuen und reparierten Checkouts verfügbar; HEAD bleibt festgelegt. Zusätzlich werden vcpkg-Manifest- und Buildtree-Logs als CI-Diagnostik gesichert. Vollständiger Windows-Build weiterhin ausstehend.
