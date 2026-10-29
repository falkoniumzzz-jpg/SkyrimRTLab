# Integrationsentscheidung und Produktpfad

## Entscheidung

Eigener, möglichst kleiner CS-Fork auf dem offiziellen Releasezweig plus separate
RT-DLL. Im aktuellen Schritt liegt der Fork reproduzierbar als Patch/Overlay vor.
Kein Vollport des alten experimentellen CS-Kerns: dessen Feature-Daten und
Materiallayouts sind nicht stillschweigend mit CS 1.9.0 austauschbar.

Der Beobachter ist ein fertig implementierter Diagnoseschritt, keine vorgetäuschte
RT-Implementierung. Seine API erlaubt ausdrücklich keine GPU-Commands. Die spätere
Render-API erhält eine andere Versions-/Capability-Kennung; alte Diagnosen werden
nicht plötzlich schreibend ausgeführt.

## Konkrete Codebelege

Alle CS-Pfade beziehen sich auf `5db085e77951b84bd6c191ff5b06d56893f08286`,
CER auf `09350844e63f602a3b788f1c815d29cee1b4fab2`.

| Stelle | Befund | Konsequenz |
|---|---|---|
| CS `src/Deferred.cpp`, `DeferredPasses` | SSGI läuft vor dem Composite, dessen UAVs werden danach entbunden; anschließend folgen Cubemaps/Effects11 | Beobachter nach dem Entbinden. GI muss später **vor bzw. im Composite** integriert werden; nicht additiv auf das bereits beleuchtete Bild kleben. |
| CS `src/Utils/D3D.cpp`, `GetCurrentSceneDepthSRV` | Tiefe kann aus Terrain Blending stammen | Aktuelle Tiefe über die vorhandene Funktion beziehen; Format feststellen statt R32 voraussetzen. |
| CS `package/Shaders/Common/GBuffer.hlsli` | `EncodeNormal`/`DecodeNormal` verwenden eine vorzeichenangepasste oktah edrische Kodierung | Native NormalRoughness nicht ungeprüft als NRD-Normalen verwenden. |
| CS `package/Shaders/Common/MotionBlur.hlsli` | Bewegung aus unjittered Clip-Positionen, Faktor `(-0.5, 0.5)` | Vor Konvertierung NRD-Konvention, Viewport/Renderauflösung und Jitter dokumentieren und mit Testbewegung belegen. |
| CS `package/Shaders/DeferredCompositeCS.hlsl` | Schreibt auch Sky-Motion-Vectors | Der aktuelle Diagnosepunkt sieht den nachbearbeiteten MV-Puffer; früherer GI-Pass benötigt eigene klare Semantik. |
| CER `src/API.h` | `GetPassTimings(eastl::vector<PassTiming>&)`, Settings-by-value, native D3D12-Pointer | Keine stabile, versionsunabhängige Plugin-ABI. Adapter bleibt zunächst auf CER-Commit festgelegt; öffentliches Interface benutzt feste POD-Layouts. |
| CER `src/Scene.cpp`, `Load`/`PostPostLoad` | Installiert eigene frühe/späte Engine-Hooks | Nicht blind parallel laden: zuerst Hook-Eigentümer zwischen Host und CER festlegen. |
| CER `src/SceneGraph.cpp` und `src/Types/CommunityShaders` | Szenen-/Materialintegration inkl. eigener CS-PBR-/LightLimitFix-Typen | GBuffer-Zugriff allein genügt nicht. Material- und Geometriepfad muss gegen CS 1.9 geprüft werden. |
| CER `src/API.cpp`, `SetSharedTextures`/`GetSharedTextures` | DX12-Ressourcen und Frames-in-flight-Ring statt bloßer DX11-SRVs | Expliziter Ressourcenbesitz, gemeinsamer Adapter und GPU-Fence-Protokoll erforderlich. |

## Reihenfolge bis zum Produkt

1. **Host-Vertrag bestätigen (diese Stufe).** Windows-DLL-Tests, CS-Gesamtbuild,
   später Start ohne Modul / mit Modul / falscher ABI / Lade- und Auflösungswechsel.
   Kein behaupteter Performancegewinn; Diagnosekosten messen.
2. **Interop-Port als getrennte Stufe.** Bewährte v2-DXR-Probe weiterverwenden;
   geteilte Ressourcen mit stabiler Lebensdauer und GPU-Fences am passenden Pass.
   Kein CPU-Warten pro Frame, keine ungeprüfte Verwendung des Upscaling-DX12-Devices.
   VR/DXVK zunächst nicht unterstützen. Fähigkeiten vor Initialisierung prüfen.
3. **CER-Szenenadapter.** Engine-Hooks inventarisieren und genau einen Eigentümer je
   Hook bestimmen; Mesh-/Instanz-Lebensdauer, Löschereignisse, Skinning, Terrain,
   Alpha-Test und Materiallayout portieren. Instanz-/BLAS-/TLAS-Zähler und Uploadkosten
   erfassen. Bestehende GI/NRD-Reparaturen aus v2 mit Regressionstests übernehmen.
4. **RTGI priorisieren.** Welt-/Viewraum, Exposure, Jitter, Normalen, Tiefe, Motion,
   HitDistance und Material-Semantik explizit konvertieren. Radiance-Debugansicht vor
   Denoiser. RTGI ersetzt den passenden indirekten Term; keine Doppelbeleuchtung mit
   SSGI/IBL. Raster bleibt bei ausgeschaltetem/fehlgeschlagenem RT nutzbar.
5. **Produktprüfung.** Paarweise Versionskennung, verständliches Menü, eigenes Branding,
   saubere MO2-Pakete und passender Quellcode. Testmatrix: Innen/Außen, Charaktere,
   Vegetation/Alpha-Test, Schnellreise, Load/Save, dynamische Auflösung, Upscaling.
   GPU-Timings, p95/p99-Frametimes und VRAM auf Falkos 5080 messen. Erst danach
   Standardsamples/Denoiser wählen; RR nur mit nachgewiesen korrekten Inputs.

## Abnahmegrenzen

WARP-Test = DLL-/Resource-Vertrag, nicht Hardware-RT.
MSVC-Build = kompilierbar, nicht im Spiel funktionsfähig.
Ein GPU-Capability-Check = verfügbare Schnittstelle, nicht erfolgreiche Interop.
Kein Paket als RT-Fork-Release markieren, bevor die neue Host/CER-Kombination
im Spiel geprüft ist. Bisheriges v2-Testpaket bleibt als getrennte Vergleichsbasis.
