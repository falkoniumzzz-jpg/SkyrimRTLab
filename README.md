# SkyrimRTLab

Experimentelles Skyrim-RT-Quellpaket v2 mit reproduzierbarem Windows-Build.

## Windows-Build starten

1. Oben **Actions** öffnen.
2. **Skyrim RT Lab Windows build** auswählen.
3. **Run workflow** öffnen, Branch **main** lassen, **probe_only** nicht aktivieren.
4. Mit **Run workflow** starten.

Die Dateien sind bereits hochgeladen. Es ist kein manueller Upload oder Entpacken erforderlich.

## Aktueller Stand

Der vollständige Windows-/Skyrim-Build ist noch nicht erfolgreich validiert. Lokal wurden die unabhängige DXR-Probe cross-kompiliert und acht GI-Shader-Varianten kompiliert. Keine Validierung im Spiel und keine gemessenen Performanceverbesserungen. Dieses Paket benötigt weiterhin das festgelegte experimentelle Community-Shaders/CER-Paar; es ist noch kein eigenständiges RT-Plugin für die öffentliche Community-Shaders-Version.

Details und Grenzen: [ERGEBNIS_V2.md](ERGEBNIS_V2.md).

## Build-Ausgaben

- **RTLab-Diagnostics**: Logs, auch bei fehlgeschlagenem Build.
- **RTLabProbe-Windows**: unabhängiger DXR-Test, falls erfolgreich erstellt.
- **SkyrimRTLab-Windows-and-Sources**: Skyrim-Paket und zugehöriger Quellcode, nur bei erfolgreichem vollständigem Build.

Bestehende funktionierende Installation nicht überschreiben; später in einem separaten MO2-Testprofil prüfen.
