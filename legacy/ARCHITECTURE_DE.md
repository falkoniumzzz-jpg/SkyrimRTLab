# Architektur und Grenzen

Der neue Pass läuft im bestehenden Debug-Modus: GPU-Skinning → TransformComposition
→ SceneTLAS → ShadowLab. Der normale Rasterpfad bleibt erhalten. Pro sichtbarem Pixel
wird zuerst ein Primärstrahl gegen die TLAS geschickt; bei einem Treffer folgt ein Strahl
zur gerichteten Lichtquelle. Die Ausgabe ist hell bei freier Sicht, dunkel bei Verdeckung,
magenta bei fehlender Richtung. Hintergrundtreffer bleiben transparent.

`RTLAB_INLINE=1` verwendet DXR 1.1 `RayQuery`. Die Alternative kompiliert als `lib_6_5`,
erstellt eine DXR-Pipeline mit RayGeneration/Miss/ClosestHit und eine SBT mit einem
Hit-Group-Eintrag. Der Payload enthält nur vier Byte Trefferentfernung. Beide Strahlen
werden nacheinander aus RayGeneration gestartet; Rekursionstiefe 1 reicht dafür.
Shaderwechsel über `UseRayQuery` erfordern für diesen Prototyp einen Neustart.

Die Kamera- und Lichtlayouts werden direkt aus CERs `interop/` eingebunden. Es werden
keine geratenen Skyrim-Struktur-Offsets hinzugefügt. Vorhandene CommonLib-Hooks und
Relocations bleiben jedoch abhängig von der tatsächlich unterstützten Spielversion.

DX11 signalisiert den gemeinsamen Fence und sendet die Arbeit mit Flush ab. Die
DX12-Queue wartet darauf, führt den vorhandenen CER-Pfad aus und signalisiert zurück;
DX11 wartet vor der Nutzung der geteilten Texturen. NVRHI verwaltet UAV-/AS-Barrieren
innerhalb des DX12-Passes. Die bestehenden Ringpuffer und Ressourcen-Lebensdauern
werden übernommen, nicht durch den neuen Pass generell als korrekt bewiesen.

Der neue DX11-Composite schreibt ausschließlich RGB und erhält Alpha, Rastertiefe und
Motion Vectors. Dies behebt für diesen Diagnosemodus die bisherige Mitbenutzung des
PT-Composites, obwohl Debug keine passenden Tiefen-/Motion-Vector-Ausgaben erzeugt.

Die unabhängige Probe baut zwei Dreiecke als BLAS und eine TLAS-Instanz. Sie schreibt
128×128 Schattenwerte in eine zwischen DX12 und DX11 geteilte R32_FLOAT-Textur.
Ein DX11-Clear wird vor DX12 abgearbeitet; DX11 liest danach das DX12-Ergebnis zurück.
Alle 16.384 Pixel werden gegen eine analytisch bekannte quadratische Silhouette geprüft.
Exitcode 77 bedeutet fehlende DXR-Hardware, ausdrücklich keinen bestandenen GPU-Test.

## Leistung und Speicher

Bei 1920×1080 sind maximal 4.147.200 Strahlen pro Bild nötig, bei 2560×1440 maximal
7.372.800. Das ist nur die Strahlenanzahl, keine FPS-Prognose. Geometrieaufbereitung,
BLAS-Updates, Synchronisierung und CPU-Traversal können auch auf dem 9800X3D limitieren.
Die Probe meldet tatsächliche vom Treiber angeforderte BLAS-/TLAS-Größen.

CERs Main-Target ist RGBA16_FLOAT: 8 Byte pro Pixel, ca. 15,8 MiB bei 1080p beziehungsweise
28,1 MiB bei WQHD pro Textur, ohne Alignment, Shared-Kopien und weitere Ringpuffer.
BLAS/TLAS, Material-/Geometriedaten und Upstream-GI/PT-Ziele kommen hinzu. Für die RTX 5080
wird keine gemessene VRAM-Belegung oder Performance behauptet. Start mit 1080p.

## Bewusst offen

- Materialkorrekte Alpha-Tests, Transmission und Wasser; derzeit FORCE_OPAQUE.
- Normalenbasierter robuster Ray-Offset; derzeit fixer Bias von 0,25 Skyrim-Einheiten.
- Direkte Integration der Sichtbarkeit in die normale Sonnenbeleuchtung.
- Verlässliche Offscreen-Geometrieabdeckung über die tatsächlich von CER erfasste Szene hinaus.
- Tests beim Zellwechsel, Laden, Teleportieren, dynamischen Meshes und Auflösungswechseln.
- Eigenständiger zeitlicher Denoiser für diesen Pass. Harte deterministische Sonnenschatten
  brauchen zunächst keine Monte-Carlo-Entrauschung; für weiche Schatten/GI ist sie später nötig.
- Validierung der vorhandenen RTGI-/Reflexions-/Mehrfachbounce-/NRD-Pfade.

Der nächste sinnvolle Schritt nach einem erfolgreichen Windows-Build ist zunächst die
Probe auf der RTX 5080, danach eine einfache Außenwelt-Testszene mit dem Diagnosepass.
Erst anschließend sollte Sichtbarkeit materialkorrekt in den normalen Lighting-Pass wandern.
