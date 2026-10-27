# RTLab v2 — Codekorrekturen, kein fertiges öffentliches CS-Plugin

Untersuchung: 27.10.2026. Dieses Dokument hat Vorrang vor den historischen v1-Dokumenten.
Die frühere Lieferung bleibt unverändert. Hier wurde eine separate Arbeitskopie benutzt.

## Tatsächliche Basis und Grenzen

Verfügbar sind unser Source-Paket vom 23.10. und dein Compilerlog vom 20.10.
Die auf deinem PC inzwischen laufenden DLLs, deren exakte Commits, aktuelle Laufzeitlogs
und GPU-Captures liegen nicht vor. Deshalb werden die Fehler des untersuchten Quellstands
nicht automatisch als Ursachen aller von dir beobachteten Probleme ausgegeben.

Aktuell abgefragte Quellstände:

| Repository | Ref | Commit |
|---|---|---|
| community-shaders/skyrim-community-shaders | main, beschreibt sich als v1.9.0 | 5db085e77951b84bd6c191ff5b06d56893f08286 |
| community-shaders/skyrim-community-shaders | dev | 87de9b020aa4c23bc6796cd965981e743b317f6a |
| alandtse/open-shaders | dev | c1b1ef1e8078110559e229db4c8de47e5294894e |
| Gistix/CreationEngineRaytracing | main | 670b42da956d604d82ada9445944ba16cb8c1ad5 |

PRs: [2196 Hardware-RT-Plugin](https://github.com/community-shaders/skyrim-community-shaders/pull/2196),
[2365 Aktualisierung des RT-Zweigs](https://github.com/community-shaders/skyrim-community-shaders/pull/2365),
[2197 Screen-Space-Raytracing](https://github.com/community-shaders/skyrim-community-shaders/pull/2197).
2197 ist kein Ersatz für Hardware-RT mit Szenengeometrie. PR-Beschreibungen sind kein Laufzeittest.

## Architekturentscheidung

| Variante | Codebeleg / Machbarkeit | Aufwand, Leistung und Wartbarkeit |
|---|---|---|
| A: unverändertes öffentliches CS + Plugin nur über öffentliche Interfaces | Kein ausreichender öffentlicher RT-Vertrag gefunden. `src/Feature.cpp::GetFeatureList` registriert interne Features statisch. Kein vollständiger externer Vertrag für G-Buffer, Pass-Reihenfolge, Geometrie und Ressourcenlebensdauer. | Mit eigenen internen Hooks prinzipiell denkbar, aber versionsabhängig und konfliktanfällig; kein nachgewiesenes Drop-in-Plugin. |
| B: kleiner CS-Hostadapter + getrenntes RT-Modul | Technisch geeignet: CER existiert bereits als eigene DLL. Der experimentelle CS-Host liefert jedoch erhebliche notwendige Integrationsarbeit, nicht nur einen DLL-Loader. | Gewählte Zielarchitektur. Vertrag und Upstream-Adapter nötig; keine FPS-Verbesserung allein durch DLL-Trennung. |
| C: Open Shaders | `API.md`, `include/VRAPI/CSinterface001.h`: Revision 4 bietet Einstellungen/Upscaler/Wind. Keine dort exponierte vollständige RT-Szene oder G-Buffer-/Rendercallback-API. | Gleicher Adapterbedarf; zusätzliche Portierungsarbeit. Aktuell kein belegbarer Vorteil für dieses RT-Ziel. |

Minimaler künftiger Hostvertrag: versionierter C-ABI-Handshake mit Größen-/Capability-Prüfung;
Renderthread-Callbacks nach G-Buffer und vor Lighting-Composite; Depth/Normal/Roughness/Albedo/Motion
mit expliziten Formaten, Koordinaten, Jitter und Renderextent; DX11-Gerät/Adapteridentität;
Invalidierungsereignisse bei Resize, Zell-/Save-Wechsel und Geräteverlust; definierte Output-Komposition.
Keine STL-Container oder by-value-C++-Settings über die DLL-Grenze. Host hält Ressourcen bis zum
vereinbarten Fence-Wert gültig. CER behält zunächst eigene CommonLib-Geometrie-Hooks; deren
Versionsabhängigkeit verschwindet durch diesen Vertrag nicht. Doppelte API-Brücken vermeiden.

**Der Adapter für aktuelles öffentliches CS und ein darüber lauffähiges separates Modul sind
in dieser Lieferung noch nicht implementiert.** Die ausführbare Integrationsbasis bleibt das
fixierte, passende CS/CER-Paar aus v1. Eine erfundene Plugin-API wird nicht als vorhanden dargestellt.

## Implementierte Änderungen

`scripts/repair_gi.py` ergänzt die vorhandene Vorbereitung automatisch:

1. **Depth-Sampling:** `GlobalIllumination/RayGeneration.hlsl` liest Tiefe mit geklemmtem
   Texel-Load statt linearer Wrap-Filterung. Vorher konnten an Silhouetten zwei Oberflächentiefen
   interpolieren bzw. jitternde Randkoordinaten zur gegenüberliegenden Bildkante umbrechen.
   Kamera-/Jitter-Konvention bleibt erhalten. Das ist eine konkrete Eingabekorrektur, keine
   vollständige Reparatur aller Normal-/Motion-Vector-Konventionen.
2. **RAW-RADIANCE-Variante ohne NRD:** `diffHitDist`/`specHitDist` waren dort nicht deklariert.
   Nun werden rohe Ersttrefferentfernungen definiert und über die Samples akkumuliert.
   Diese Variante ist im alten Generator nicht der normale RR-Pfad; die Korrektur allein
   aktiviert keine funktionierende Ray-Reconstruction-Integration.
3. **NRD-History:** Erstnutzung, neu angelegte History-Ressourcen, erkannte Frame-Lücken und
   Denoiser-Aktivierungswechsel führen zu `CLEAR_AND_RESTART`. Bisher stand der Default auf
   CONTINUE, auch wenn History-Texturen neu erstellt wurden. Nach erfolgreich aufgezeichneten
   Dispatches wird der gültige History-Frame gespeichert. Log: `RTLab NRD history reset`.
   Kamera-Cuts ohne Ressourcen-/Frame-/Aktivierungswechsel werden damit noch nicht erkannt.
4. **NRD-Initialisierung:** `Setup()` vom Konstruktor nach `Initialize()` verschoben, mit
   Nullprüfung. Dieses Muster ist im neueren CER ebenfalls vorhanden. Im GI-Graph existieren
   REBLUR und RELAX als Nodes; dadurch wird nicht mehr schon im Konstruktor die nicht ausgewählte
   NRD-Instanz erstellt. Kein künstliches Abschalten aktiver Effekte, keine gemessene FPS-Zusage.
5. **Buildprüfung:** Acht echte GI-Shader-Varianten vor dem Windows-Plugin-Build. Die erste
   Lieferung prüfte nur den ShadowLab-Shader. Der neue Standard bleibt GI statt Debug.

Vollständige geänderte CER-Dateien unter `changes/`, reproduzierbare Änderungen unter `scripts/`.
`gi-repairs.patch` ist zusätzlich zur Durchsicht vorhanden; nicht zusätzlich zum Skript anwenden.
Upstream-Lizenzen und Attribution bleiben erhalten.

## Befunde zu Bildqualität und Performance

Dein altes MSVC-Log enthält C2039 für `IAccelStruct::getBufferSize` und fehlende
`AccelStructMemoryStats`/`getAccelStructMemoryStats`. Das belegt einen Abhängigkeits-/API-Mismatch.
Der gewählte alte CER-Stand verlangt nicht dieselben neuesten Statistik-APIs; sein NVRHI-Gitlink
ist festgelegt. Neuester CER setzt weitere NVRHI-/RTXMU-Anpassungen voraus und wird nicht blind
gegen alte Header gebaut. Neueste Commits behandeln u.a. RTXMU-Scratch-Freigabe nach Queue-Abschluss;
sie lassen sich nicht isoliert in den hier verwendeten Backend-Stand ohne RTXMU übertragen.

`Scene::Execute` und CS `Raytracing::DeferredPasses` kehren bei Mode=None bereits früh zurück.
Die Aussage „None zeichnet trotzdem das ganze GI“ wäre für diesen Stand falsch. Bestehende Hooks,
Allokationen, Shader-Fork-Unterschiede und andere Effekte können dennoch Kosten verursachen.
Für massive Ladezeiten sind SceneGraph-Traversal, ThreadPool-Waits, Material-/Texturimport und
BLAS-Aufbau plausible Messstellen. Volumetrischer Nebel ist anhand des vorliegenden Materials
kein nachgewiesener Verursacher. GPU-Zeiten existieren im CER-Pass-Timing und CPU-Phasen im SceneGraph.

GI rekonstruiert den Primärtreffer aus Raster-G-Buffern, PT aus Strahlentreffern. Daher können
GI-spezifische Depth-/Normal-/Jitter-/Materialfehler auftreten, obwohl PT besser aussieht.
Die probabilistische Lobenauswahl liefert bei 1 SPP häufig keine neue Messung für eine der
beiden Komponenten. Mehr SPP reduziert Varianz und erleichtert dem Denoiser die Rekonstruktion;
das erklärt die Beobachtung plausibel, beweist aber keine einzelne Ursache. Kein Hochsetzen
der Samplezahl als vermeintlicher Fix. RR ist nicht als repariert ausgewiesen: korrekte getrennte
Radiance-, Albedo-, Hit-Distance-, Motion-, Depth- und Exposure-Eingaben müssen separat validiert werden.

## Build, Messung und Installation

Windows-Build wie bisher: Python 3.12, Git/LFS, VS C++, Windows SDK, CMake 4.2.3;
`python scripts/build_windows.py`. Alternativ mitgelieferter GitHub-Actions-Workflow.
Kein Workflow wurde hier in deinem Konto gestartet; keine Skyrim-DLL liegt fertig kompiliert vor.
Erst ein erfolgreicher Windows-Build erzeugt `SkyrimRTLab-Windows.zip` für MO2.
Dieses Paket ersetzt weiterhin das experimentelle CS im separaten Testprofil und ist **nicht**
zusätzlich zum unveränderten öffentlichen CS zu installieren.

Für GI-Tests: GeneralSettings.Mode=GlobalIllumination, 1 SPP, NRD REBLUR/RELAX einzeln testen,
zunächst feste Auflösung. V1s Debug-Anleitung gilt nur noch für den separaten Schatten-Test.
Vergleiche denselben Save, dieselbe Kamera und Tageszeit vor/nach der Änderung: 60 Sekunden
Stillstand, Schwenk, Verdeckung, Denoiserwechsel, Auflösungswechsel, Schnellreise, jeweils drei Läufe.
Erfasse Median/p95/p99-Frametime, CER-Passzeiten, VRAM und Ladezeit. Gleiche Tests im kleinen und
großen Modprofil. GPU-Aufnahmen/Frametime-Messungen fehlen hier; es werden keine Vorher/Nachher-Zahlen erfunden.

Die neue Lieferung ist ein überprüfbarer Reparaturstand, keine abgeschlossene modulare Portierung.
Offen: aktueller-CS-Hostadapter, gesamte MSVC-Integration, GPU-Validierung, RR-GI-Datenvertrag,
Kamera-Cut-Erkennung, Profiling der Lade-Ruckler und endgültiger MO2-Binärrelease.
