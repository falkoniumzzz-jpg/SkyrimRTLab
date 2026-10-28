# CI-Korrekturen

## 2026-10-27: Windows-Zeichenkodierung

Run 40565199008 hat RTLabProbe.exe erfolgreich mit MSVC gebaut. Die Vorbereitung der GI-Shader brach anschließend in check_gi_shaders.py mit UnicodeEncodeError unter cp1252 ab.

Die Shader werden jetzt als Bytes kopiert; nur ASCII-Include-Pfade werden normalisiert. Damit bleiben Kommentare unverändert und die lokale Windows-Codepage spielt keine Rolle. PYTHONUTF8=1 gilt zusätzlich für alle Python-Schritte im Workflow. Acht GI-Varianten wurden nach der Änderung mit DXC unter Linux erfolgreich kompiliert. Die Windows-Nachprüfung und der vollständige Skyrim-Build stehen noch aus.

## 2026-10-27: Vollständige vcpkg-Historie

Run 40571463222 bestätigt die Encoding-Korrektur: acht GI-Varianten, beide ShadowLab-DXR-Varianten und FXC-Compositing kompilieren unter Windows. Danach scheitert cs-configure, weil die flache vcpkg-Kopie die historischen Port-Trees für detours@4.0.1#8 und directx-headers@1.614.1 nicht enthält.

Beide vcpkg-Repositories werden jetzt mit vollständiger Historie bis zum unveränderten Baseline-Commit geladen. Vorhandene flache Checkouts werden ohne Änderung von HEAD vervollständigt. Lokaler Git-Regressionstest bestanden: historische Trees sind danach in neuen und reparierten Checkouts verfügbar; HEAD bleibt festgelegt. Zusätzlich werden vcpkg-Manifest- und Buildtree-Logs als CI-Diagnostik gesichert. Vollständiger Windows-Build weiterhin ausstehend.

## 2026-10-28: CER-PCH und Build-Reihenfolge

Run 40573391088 hat CommunityShaders.dll erfolgreich gebaut und installiert. CER scheiterte im vorkompilierten Header mit Makro-Kollisionen: std::min, REX::W32::MAX_PATH und InterlockedCompareExchange. Die CER-PCH liest jetzt RE/Skyrim.h vor SKSE/SKSE.h, entsprechend dem erfolgreich gebauten CS-Host. NOMINMAX und WIN32_LEAN_AND_MEAN stehen geschützt vor allen Includes, statt erst nach Windows.h.

Patch-Anwendung auf frische festgelegte Quellen, Wiederholbarkeit und der Vergleich der 27 gemeinsamen API-Deklarationen wurden lokal geprüft. Die MSVC-Bestätigung dieser Korrektur steht noch aus. CER wird jetzt vor CS kompiliert, um Backend-Fehler früher zu finden. Installiert wird weiterhin CS zuerst und CER danach, weil CS sein Installationsziel leert. Keine In-Game-Validierung.

## 2026-10-28: Installationspfad für CMake

Run 40672396981 bestätigt: Beide DLLs kompilieren erfolgreich, einschließlich CER mit korrigiertem PCH. cer-install scheitert anschließend an `Invalid character escape '\a'`, weil DEPLOY_DIR als Windows-Pfad mit Backslashes in cmake_install.cmake eingebettet wird. build_windows.py übergibt DEPLOY_DIR nun mit Path.as_posix(). Python-Syntax und Normalisierung eines repräsentativen Windows-Pfads wurden lokal geprüft; der lokale CMake-Reproduktionstest konnte mangels CMake-Executable nicht ausgeführt werden. Windows-Paketierung und Spieltest bleiben offen.
