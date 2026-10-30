# Windows-Test — erst Probe, dann Skyrim

## 1. Unabhängiger Hardwaretest

`RTLabProbe-Windows.zip` entpacken und `Run-Probe.cmd` starten. EXE und `Probe.cso`
müssen im selben Ordner liegen. Der Test injiziert nichts in Skyrim und braucht kein SKSE.
Er erzeugt `Probe.log` und `Probe.pgm` (weißes Bild mit schwarzem Quadrat).

- Exit 0 / PASS: Alle 16.384 GPU-Pixel stimmen nach DX11-Readback.
- Exit 1: API-/Datei-/Timeoutfehler; HRESULT im Log.
- Exit 2: GPU-Ergebnis stimmt nicht mit der erwarteten Silhouette überein.
- Exit 77: Kein DXR-1.1-Hardwareadapter erkannt; kein bestandener Test.

GitHub-Standardrunner werden hier nur zum Kompilieren verwendet, nicht als DXR-Testhardware.
Die Cross-Compile-Prüfung in dieser Lieferung wurde unter Linux durchgeführt.
Die ausgelieferte CI-Probe wird unter MSVC gebaut. Visual-C++-Runtime kann erforderlich sein.

## 2. Skyrim in separatem MO2-Testprofil

Voraussetzungen, die dieser Quellcode tatsächlich erwartet:

- Skyrim SE/AE mit zur EXE passendem SKSE und Address Library.
- SSE Engine Fixes (`EngineFixes.dll`) **und Crash Logger (`CrashLogger.dll`)**.
  CER lädt beide ausdrücklich in `src/XSEPlugin.cpp`; sie sind keine bloßen Empfehlungen.
- Passende Visual-C++-Runtime und NVIDIA-Treiber. Der Code prüft DXR-Unterstützung beim Start.
- Die gemeinsame experimentelle CommunityShaders.dll/CreationEngineRaytracing.dll aus
  demselben Build. Open Shaders und reguläre Community Shaders in diesem Profil deaktivieren.

Keine Skyrim-, SKSE-, Engine-Fixes- oder Crash-Logger-Dateien sind im Quellpaket enthalten.
Installiere deren zur Spielversion passende reguläre Pakete. Die SE-/AE-Buildoptionen sind
kein Nachweis, dass jede neu erschienene Skyrim-EXE unterstützt wird. VR ist ausgeschaltet.

Das innere `SkyrimRTLab-Windows.zip` in MO2 installieren; der Ordner `Data` enthält den
Modinhalt. Bestehende Shader-/Config-Dateien anderer CS-Versionen nicht darüber mischen.
Zum ersten Test 1920×1080, keine dynamische Auflösung, kein Frame Generation und kein
DLSS Ray Reconstruction. Kein DXVK-Wrapper für diesen nativen DX12-Versuch.

Im CS-Menü Raytracing aktivieren und Modus **Debug** wählen. Der geänderte Standard ist
Debug, bestehende Nutzerkonfigurationen können ihn überschreiben. Denoiser **None**,
ResolutionScale **1.0**, `UseRayQuery=true`; danach Skyrim neu starten.
Der vorhandene Schalter „Raytraced Shadows“ anderer Modi ist nicht der neue Pass.

Eine einfache Außenszene am Tag laden. Erwartetes Diagnosebild: getroffene undurchsichtige
Flächen sind hell oder dunkel je nach Sicht zur Sonne; Himmel bleibt Rasterbild.
Magenta bedeutet fehlende/ungültige Lichtrichtung. Nachfolgende Spieleffekte können die
Farben verändern. Dies ist keine fertige normale Beleuchtung und kein PT-Vergleichsbild.

## 3. Abnahmeplan

1. Logs auf beide DLL-Versionen, ABI-Fehler und „ShadowLab ... pipeline created“ prüfen.
2. Gebäudeschatten ansehen; Kamera drehen, sodass ein Schattenwerfer aus dem Bild verschwindet.
   Ein Schatten darf nur dann bestehen bleiben, wenn CER dessen Geometrie weiterhin erfasst.
3. Tageszeit ändern; Schattenrichtung muss folgen.
4. Animationen, Zellwechsel und Laden getrennt testen. Crashs/Artefakte dokumentieren.
5. Optional `UseRayQuery=false`, Neustart: gleiche Szene über SBT-Pipeline vergleichen.
6. Erst nach stabiler Grundfunktion WQHD, weitere Effekte und größere Modlast testen.

Benötigte Fehlerdaten: `RTLab-Diagnostics` bei Buildfehlern; bei Laufzeitfehlern
`Probe.log`, Community-Shaders-/CER-/Crash-Logger-Logs, Skyrim-EXE-Version,
Treiber-Version, Modliste und reproduzierbare Szene. Keine behaupteten FPS-Ziele.

Rückbau: Testmod im MO2-Profil deaktivieren und die bisherigen Shader wieder aktivieren.
Nicht in der produktiven Modliste beginnen; Upstream-Szenenlebensdauer und Hook-Kompatibilität
sind hier nicht durch einen Test bewiesen.
