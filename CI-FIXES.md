# CI-Korrekturen

## 2026-10-27: Windows-Zeichenkodierung

Run 40565199008 hat RTLabProbe.exe erfolgreich mit MSVC gebaut. Die Vorbereitung der GI-Shader brach anschließend in check_gi_shaders.py mit UnicodeEncodeError unter cp1252 ab.

Die Shader werden jetzt als Bytes kopiert; nur ASCII-Include-Pfade werden normalisiert. Damit bleiben Kommentare unverändert und die lokale Windows-Codepage spielt keine Rolle. PYTHONUTF8=1 gilt zusätzlich für alle Python-Schritte im Workflow. Acht GI-Varianten wurden nach der Änderung mit DXC unter Linux erfolgreich kompiliert. Die Windows-Nachprüfung und der vollständige Skyrim-Build stehen noch aus.
