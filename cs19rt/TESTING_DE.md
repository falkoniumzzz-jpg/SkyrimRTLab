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

## Nachlade-Ruckler prüfen (Lauf C)

Dieser Build richtet neu geladene Objekte für RT nicht mehr alle im selben Frame ein,
sondern verteilt sie auf mehrere Frames, die nächsten zuerst.

1. Lauf oder reite mit RT etwa fünf Minuten durch die offene Welt, am besten dieselbe
   Strecke wie beim letzten Test.
2. Achte darauf, ob die Ruckler seltener oder kürzer sind.
3. Nach einem Ladebildschirm kann die RT-Beleuchtung weiter entfernter Objekte einen
   Moment später erscheinen. Das ist so gewollt.

Längere Frames schreibt der Build selbst als „RTLab frame spike“ in
`CreationEngineRaytracing.log`.

Auch die BLAS-Neubauten sind begrenzt: etwa 24 Objekte pro Frame, die am längsten
wartenden und dann die nächsten zuerst. Bei großem Rückstand (nach einem Ladebildschirm)
steigt die Zahl, damit er in rund einer Sekunde abgebaut ist statt in einem Rutsch. Neu
geladene Objekte zählen dabei nicht mehr als „bewegt“ und fallen damit unter die Grenze.
Ein Objekt, das gerade sichtbar oder unsichtbar wurde, kann im RT deshalb ein paar Frames
lang noch im alten Zustand sein.

Entladene Objekte werden über mehrere Frames freigegeben (höchstens 1,5 ms pro Frame),
statt alle auf einmal. Die Spike-Zeile zeigt das als „meshes released“. Alle 30 Sekunden
steht außerdem eine Zeile „RTLab VRAM“ im Log.

## Vanilla Fresnel vergleichen (optional)

Vanilla Fresnel ist standardmäßig aus. Zum Vergleichen im CS-Menü unter *Vanilla
Fresnel* „Enable Vanilla Fresnel“ und „Enable Phong to GGX“ einschalten. Mit RT ändern
sich nur die Glanzlichter von Sonne und Lampen auf normalen (nicht PBR) Materialien.
Bitte erst nach dem Ruckel-Test einschalten.

## Flackern mit DLSS RR prüfen

Diese Version ändert nur die Eingaben für DLSS RR und den Hybrid-ReSTIR-Pfad. Mit NRD
Reblur oder Relax bleibt das Bild gleich (ReSTIR ist im GI-Modus mit NRD ohnehin aus).

1. Gleiche Stelle, an der es vorher geflackert hat. Upscaling DLSS, Denoiser DLSS RR,
   ReSTIR GI aus. Flackert es noch, wo und wie stark?
2. Dasselbe mit ReSTIR GI an (Defaults, Boiling Filter an, Final Visibility an).
3. Zum Vergleich einmal NRD Reblur.

Geändert: Abstand der Spiegelstrahlen springt nicht mehr auf 0, Ausreißer-Pixel werden
begrenzt, verdeckte ReSTIR-Samples zählen als 0 statt auf den Roh-Wert zurückzufallen,
und der Albedo-Hinweis für RR liegt im selben Farbraum wie das Bild. Wenn RR jetzt
irgendwo dunkle Sprenkel zeigt, bitte melden (Hinweis auf den ReSTIR-Sichtbarkeitstest).

## Neu: Cloud Relight, Foliage Lighting, ohne Inverse Square Lighting

Aus Open Shaders übernommen, beide standardmäßig an. Inverse Square Lighting wird nicht mehr
mitgeliefert: Lichter nutzen den Vanilla-Abfall, im Raster und im RT.

1. **Wolken (Cloud Relight):** Sonnenauf- oder -untergang mit Wolken. Wolken sollten von der
   Sonne beleuchtet wirken, mit dunkleren Unterseiten und hellen Rändern zur Sonne hin.
   Vergleich: CS-Menü → *Cloud Relight* → „Enabled“ aus und an. Braucht Cloud Shadows (an).
2. **Laub (Foliage Lighting):** Gegen die Sonne durch Baumkronen und über Gras schauen. Blätter
   und Gras sollten etwas durchleuchten. Vergleich: CS-Menü → *Foliage Lighting* → „Enable
   Foliage Lighting“ aus und an.
3. **Lichter:** Fackeln und Kerzen sollten so hell und weit leuchten wie in Vanilla. Unter
   *Disable at Boot* steht Inverse Square Lighting nicht mehr in der Liste der geladenen
   Features (`CommunityShaders.log`: „InverseSquareLighting.ini failed to load“).

## Wenn das Spiel hängt (z. B. endloser Ladebildschirm)

1. Drücke **Strg+Umschalt+F12**, solange das Spiel hängt. Crash Logger schreibt dann
   einen Thread-Dump in den SKSE-Ordner.
2. Warte etwa zehn Sekunden. Beende das Spiel erst danach.
3. Notiere, was du gerade gemacht hast (Tür, Schnellreise, Spielstand laden) und ob die
   Spielzeit im CS-Editor pausiert war.

## Bitte zurückmelden

- **FPS:** die Werte aus A, B und C.
- **Abstürze:** Datei `crash-*.log` von Crash Logger.
- **Hänger:** den Thread-Dump von Crash Logger und in welchem Lauf (A, B oder C) es passiert ist.
- **Logs:** `CommunityShaders.log` und `CreationEngineRaytracing.log` (beide in
  `Documents/My Games/Skyrim Special Edition/SKSE/`).
- **Bildfehler:** Screenshot mit kurzer Beschreibung.
