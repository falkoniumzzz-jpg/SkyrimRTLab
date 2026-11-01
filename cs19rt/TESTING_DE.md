# Test-Anleitung (RTX 5080, WQHD)

**Status:** implementiert und gebaut. **Im Spiel noch nicht bestätigt.**

## Installation

1. Lege in MO2 ein **neues Profil** an.
2. Installiere `FalkosLichtspiel-CS19-RT-MO2.zip` über „Mod aus Archiv installieren“.
   Ein anderes Community Shaders darf im selben Profil nicht aktiv sein.
3. Voraussetzungen: SKSE, Address Library, Engine Fixes und Crash Logger.

## Die drei Messläufe

Nimm immer denselben Spielstand, dieselbe Kamera und dieselbe Tageszeit. Schau dir je
60 Sekunden Stillstand und einen Kameraschwenk an.

| Lauf | Einstellung | Erwartung |
|---|---|---|
| A | Offizielles CS 1.9 (separates Profil) | Referenz-FPS |
| B | Dieser Build, Raytracing unter *Disable at Boot* abgehakt, Neustart | ≈ A |
| C | Dieser Build, Raytracing aktiv | RT-Bild, FPS je nach Modus |

Bei B schreibt `Documents/My Games/Skyrim Special Edition/SKSE/CreationEngineRaytracing.log`
die Zeile „no hooks installed, backend idle“.

## Raytracing prüfen (Lauf C)

Das CS-Menü öffnest du mit **Ende**, dort unter *Raytracing*.

1. **RTGI ohne RR:** Upscaling auf DLSS. Achte auf Licht, Schatten und Metalle.
2. **RTGI mit RR:** Upscaling auf DLSS-RR und Linear Lighting an. Vergleiche direkt
   nach einem frischen Start mit Schritt 1: Ist der Detailverlust weg?
3. **ReSTIR:** Schalte ReSTIR GI ein und aus.
4. **Pathtracing → RTGI:** Wechsle von PT auf RTGI. Siehst du Ghosting?

## Bitte zurückmelden

- **FPS:** die Werte aus A, B und C.
- **Abstürze:** Datei `crash-*.log` von Crash Logger.
- **Logs:** `CommunityShaders.log` und `CreationEngineRaytracing.log` (beide in
  `Documents/My Games/Skyrim Special Edition/SKSE/`).
- **Bildfehler:** Screenshot mit kurzer Beschreibung.
