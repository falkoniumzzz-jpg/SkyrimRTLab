# RTLab: eigener CS-Fork, Entwicklungsstufe 0.1

Stand: 29.10.2026. Basis: offizielles CS **1.9.0**, Commit
`5db085e77951b84bd6c191ff5b06d56893f08286` aus `community-shaders/skyrim-community-shaders`.
Der Fork wird als festgehaltener Upstream plus kleiner Patch und vollständigen neuen
Quelldateien gepflegt. Kein separates GitHub-Fork-Repository, sondern ein isolierter
Entwicklungszweig im vorhandenen RTLab-Repository. Upstream-Updates erfolgen bewusst,
nicht automatisch während eines Builds.

**Das ist noch kein neues RT-Modpaket.** Das erfolgreiche v2-Testpaket auf `main`
(Windows-Run 40687353054) bleibt unverändert. Dessen experimentelle CS/CER-DLLs dürfen
nicht mit diesem neuen Host gemischt werden.

## Bereits implementiert

- Kleine Erweiterung des aktuellen Deferred-Passes und der Ressourcen-/Frame-Lebensdauer.
- Separat geladene `RTLab.Diagnostics.dll` mit versionierter, streng geprüfter Schnittstelle.
  Kein EASTL, STL-Container, C++-Objektbesitz oder Speicherfreigabe über die DLL-Grenze.
- Sechs echte CS-SRVs nach Deferred Composite: Tiefe, Normalen/Rauheit, Albedo,
  Reflectance, Motion Vectors und Farbe. Die Diagnose liest nur Beschreibungen;
  keine Bildkopien, kein GPU-Readback, keine GPU-Dispatches.
- DXR-Fähigkeitsabfrage auf demselben Adapter wie Skyrim. Das ist kein DXR-Ausführungstest.
- Generation bei Ressourcen-Setup, Lade-/Hauptmenü und Unterbrechung der Frame-Folge.
  Das ist noch keine vollständige Kamera-Cut-/Disocclusion-/History-Validierung.
- Protokollierung von echten Format-/Größenangaben und CPU-Kosten der Diagnose.
  Texturgröße bezeichnet die Allokation, nicht automatisch den dynamischen Renderbereich.
- Windows-Tests des DLL-Ladewegs und der tatsächlichen Resource-Abfragen mit WARP;
  unabhängiger Test für ABI-Ablehnung und Frame-Epochen.
- Separate CI baut zuerst diese kleine Stufe, danach den aktuellen gepatchten CS-Kern.
  CommonLibs explizite Source-Build-Option wird respektiert statt per FORCE überschrieben.

## Was fehlt

Noch keine CER-Anbindung, Geometrieübergabe, BLAS/TLAS, Shared-Texture/Fence-Anbindung,
Materialkonvertierung, GI-Integration, Motion-/Normalen-Konvertierung für NRD oder
Ray Reconstruction. Der neue Host verändert die Beleuchtung nicht.
Eine bestehende CER-DLL wird bewusst nicht über die neue Schnittstelle geladen.

## Entwicklung und Prüfung

```text
python fork/scripts/prepare.py --source <separates-CS-Verzeichnis>
cmake -S fork -B fork/build
cmake --build fork/build --config Release
ctest --test-dir fork/build -C Release --output-on-failure
```

`prepare.py` holt bei fehlendem Verzeichnis genau den festgehaltenen Commit.
Bei vorhandenem Verzeichnis prüft es Commit, eigene Änderungen und Patch-Wiederholbarkeit;
es führt keinen Hard-Reset aus. Ein anderer oder bereits abweichend bearbeiteter Stand
wird abgewiesen. Vollständiger Windows-Hostbuild:

```text
python fork/scripts/build_windows.py
```

CI: **RTLab CS fork validation**, ausschließlich auf `dev/cs-1.9-rt-host`.
Build-Evidence enthält Logs und Quellstand-Manifest. Noch keine neue MO2-ZIP.
Die DLL ist absichtlich kein SKSE-Plugin: der CS-Host lädt sie aus
`Data/SKSE/Plugins/RTLab/RTLab.Diagnostics.dll`. Dort liegt auch `RTLab.ini`;
`[Diagnostics] Enabled=1` aktiviert sie beim nächsten Spielstart. Standard ist 0.
Logging erfolgt in `CommunityShaders.log` mit Präfix `[RTLab]`.
Nur für ein späteres separates SE/AE-Testprofil, kein VR. Fehlende/inkompatible
Diagnose-DLL lässt den CS-Pfad weiterlaufen. Der CER-Konfliktcheck kann bereits
installierte Hooks einer versehentlich geladenen Alt-DLL nicht rückgängig machen.

## Lizenz und Distribution

Neue Dateien: GPL-3.0-or-later. CS Copyright/Lizenz bleiben erhalten, siehe `licenses/`.
Upstream-Logo ist ausdrücklich nicht zur Weiterverteilung freigegeben. Vor einer
binären Distribution: eigene Kennzeichnung, Logo ausschließen, vollständige passende
Quellen und Bibliotheks-Lizenzen beilegen. Aktuelle CI veröffentlicht nur Prüfprotokolle.

Konkreter Portierungsplan und Codebelege: [INTEGRATION.md](INTEGRATION.md).
