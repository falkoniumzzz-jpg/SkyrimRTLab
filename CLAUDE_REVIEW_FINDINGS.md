# Claude-Review: Befunde zum RT-Zweig (31.10.2026)

Geprüfter Stand: `dev/falkoslichtspiel-rt` @ `69c2f88`. Grundlage waren die
Pins in `legacy/sources.lock.json`. Die Quellen wurden mit
`legacy/scripts/prepare_sources.py` lokal erzeugt.

Status-Legende: **implementiert** = Quelltext geändert · **kompiliert/gebaut** =
Windows-CI grün · **im Spiel bestätigt** = Test auf Falkos PC.

## Behoben

### 1. DLSS-RR bekam keine Welt→View-Matrizen (wahrscheinliche Ursache des RR-Detailverlusts)

Alle RR-Normalen sind Weltraum-Normalen. Das gilt für `ConvertTexturesCS`
(PT) und für die neuen CER-PostProcess-Guides (RTGI). Auch die
Specular-Trefferdistanz ist eine Weltraum-Distanz. Laut Streamline-Doku
(`ProgrammingGuideDLSS_RR.md` §4.1.9, `sl_dlss_d.h`) muss die Anwendung dafür
`DLSSDOptions::worldToCameraView` und `cameraViewToWorld` setzen.

`Streamline::SetDLSSDOptions` hat beide nie gesetzt. Durch `DLSSDOptions{}`
waren es Nullmatrizen. RR konnte Normalen und Hit-Distanzen deshalb nicht in
den View-Raum transformieren. Das passt zum Symptom: Der Detailverlust tritt
nur mit RR auf und schon nach einem frischen Start.

Fix: `legacy/cs-rr-review.patch`. Die Matrizen werden jedes Frame aus
`frameBufferCached` übernommen. Dabei gilt dieselbe Transpose-Konvention wie
bei `cameraViewToClip`. Der Fix betrifft RTGI und PT.

Status: implementiert. Kompiliert/gebaut: siehe CI-Run dieses Zweigs. Im Spiel
**noch nicht bestätigt**.

### 2. MO2-Paketstruktur

Das alte ZIP hatte oben `Data/` neben Doku-Dateien. MO2 erkennt das nicht als
gültigen Mod und fällt auf die manuelle Installation zurück. Jetzt liegen
`SKSE/` und `Shaders/` direkt an der Wurzel. Doku und Lizenzen liegen unter
`FalkosLichtspiel RT Docs/`. Der Build bricht ab, wenn die beiden DLLs nicht an
der richtigen Stelle liegen.

### 3. Patch-Reihenfolge

`apply_rt.py` wendet jetzt pro Quelle eine geordnete Patchserie an. Codex'
`cs-rt.patch` und `cer-rt.patch` bleiben unverändert, Review-Fixes liegen
getrennt. Eine wiederholte Vorbereitung erzeugt byte-identische Dateien.

## Geprüft, ohne Änderung

- **Auflösung:** Die RR-Guides laufen in `Camera.RenderSize`, also der
  dynamischen Größe. `GetResolutionScale()` ist bei RR immer 1. Die
  Extents in Streamline passen dazu. Kein Größen-Mismatch gefunden.
- **Farbraum:** CER `LLGammaToTrueLinear` und CS `ConvertTexturesCS`
  linearisieren die Albedo gleich, gesteuert über das Linear-Lighting-Flag.
  Ohne Linear Lighting ist das Hauptbild selbst gamma-basiert. Dann passt
  das lineare Albedo-Guide nicht radiometrisch zum Farb-Input von RR. Für
  RR-Tests deshalb **Linear Lighting einschalten**.
- **Hybrid-ReSTIR:** Kandidatengewicht, AO-Faktor und 1/SPP-Ersatz sind im
  linearen GI-Puffer (Denoiser None/RR) konsistent. Ein Ausgabe-Puffer
  `GIOriginalContribution` wird bewusst auf `secondaryGBufferDiffuseAlbedo`
  gelegt. Ob der Schätzer erwartungstreu ist, lässt sich nur auf der GPU
  prüfen.
- **RR-History-Reset:** Er nutzt das memberweise `operator==` der Settings.
  Keine Felder gefunden, die sich jedes Frame ändern.

## Offen

- Im Hybrid-ReSTIR-Pfad bei 1 SPP wird die Specular-Hit-Distanz für RR durch
  die Distanz des *diffusen* Kosinus-Samples ersetzt. Betrifft nur raue
  Oberflächen (Rauheit ≥ 0.2), ist aber nicht sauber.
- Der Jiaye-Zweig hat weiterhin **keine** CER-Anbindung. Dieses Paket ist die
  native RT-Variante auf der älteren CS/CER-Basis und noch nicht der fertige
  Jiaye-1.9-RT-Port. Die Blocker stehen in `JIAYE_PORT_MAP.md`.
