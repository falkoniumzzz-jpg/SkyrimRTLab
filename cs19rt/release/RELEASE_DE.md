# Release auf Nexus – Ablauf

## 1. Vor dem Release

- Den Stand im Spiel bestätigen, in beiden MO2-Profilen. Ohne bestätigten Stand wird nichts veröffentlicht.
- `cs19rt/VERSION` und `cs19rt/release/CHANGELOG.md` anpassen. Die Überschrift im Changelog
  muss die Version enthalten, z. B. `## 0.1.0-beta`.
- Empfohlen: Gistix und dem CS-Team kurz Bescheid geben, dass ein Fork auf Nexus kommt.

## 2. Release bauen

Ein Tag `v<VERSION>` auf `claude/cs19-rt` (z. B. `v0.1.0-beta`) startet den Workflow
„FalkosLichtspiel CS 1.9 RT“. Am Ende legt er ein GitHub-Release (Pre-Release) mit drei Dateien an:

| Datei | Auf Nexus als |
|---|---|
| `FalkosLichtspiel-<version>.zip` | Main File |
| `FalkosLichtspiel-<version>-PDBs.zip` | Optional File („Debug symbols for Crash Logger“) |
| `FalkosLichtspiel-<version>-Source.zip` | Optional File („Source code, GPL“) oder nur Link aufs GitHub-Release |

Passt der Tag nicht zu `VERSION`, bricht der Build absichtlich ab.

Jeder normale Build auf dem Branch erzeugt dieselben Dateien als Artefakt „FalkosLichtspiel-Release“.
Die Version im Menü trägt dann den Commit, z. B. `0.1.0-beta+abc1234`.

## 3. Nexus-Seite

- **Spiel:** Skyrim Special Edition. **Kategorie:** Visuals and Graphics.
- **Beschreibung:** Inhalt von `NEXUS_PAGE.bbcode` einfügen.
- **Requirements:** SKSE64, Address Library, SSE Engine Fixes, Crash Logger.
  Unter „Off-site requirements“ nichts eintragen.
- **Permissions:** „This mod contains assets/code from other authors“ ankreuzen.
  Credits: Community Shaders, Gistix (CER), Open Shaders. Lizenz: GPL-3.0-or-later,
  und dazu den Link zum Quellcode.
- **Screenshots:** Vergleichsbilder None ↔ RT Lights ↔ GI, am besten nachts in einer Stadt.
- Die Nexus-Mod-ID gibt es erst, wenn die Seite angelegt ist. Danach kann der Link im Menü
  von GitHub auf Nexus umgestellt werden (nächstes Release).
