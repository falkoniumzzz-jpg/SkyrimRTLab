# FalkosLichtspiel – CS 1.9 mit Hardware-Raytracing

Basis ist das **offizielle Community Shaders 1.9.0** (`5db085e7`) mit allen Features.
Dazu kommt der Raytracing-Host aus Gistix' RT-Zweig (`84114745`) und die gepaarte
RT-DLL Creation Engine Raytracing (CER, `09350844`). Alles ist in
`sources.lock.json` fest gepinnt.

## Was portiert wurde

- **RT-Delta:** Gistix' RT-Änderungen gegenüber seinem letzten CS-dev-Stand
  (`c7270bb2..84114745`, 76 Dateien). Sie wurden per 3-Wege-Merge auf CS 1.9 gelegt,
  21 Konflikte sind von Hand aufgelöst.
- **Ergänzungen:** Codex' Patches aus dem bisherigen RT-Build (Hybrid-RTGI, ReSTIR,
  RR-Guides, ShadowLab-ABI) und der RR-Matrix-Fix.
- **Streamline:** SDK 2.12 und die DLSS-RR-DLLs genau so, wie sie im RT-Zweig liegen.

## Abweichungen vom alten RT-Build, bewusst

- **RT aus kostet nichts:** Ist „Raytracing“ in CS unter *Disable at Boot* abgewählt,
  startet CS keine DX12-Brücke. CER installiert dann **keine einzige Hook**
  (`patches/cer-boot-gate.patch`). Der alte Build hat auch mit RT-Modus „None“ alle
  D3D11-Ressourcen als „shared“ angelegt und jedes Mesh nach DX12 gespiegelt.
  Umschalten braucht einen Neustart.
- **Ohne RT bleibt das Bild wie CS 1.9:** Rauheit im G-Buffer, Cubemap-Größe 256,
  Masks2-Format und DLSS-Schärfung sind nur mit RT verändert.
- **Masks2 bei Gras (mit RT):** Gras nutzt jetzt denselben Vertrag wie Lighting
  (x = 1 − Vertex-AO, y = Metallic, z = 1 − AO). Vorher landete AO im Metallic-Kanal.
- **Nasse Oberflächen (mit RT, ohne PBR):** Sie behalten die Rauheit des Wasserfilms.

## Bekannte offene Punkte

- **Extended Materials:** CS 1.9 hat `ExtendShadows` entfernt. CER liest an dieser
  Stelle jetzt 0, Parallax-Schatten im RT-Pfad bleiben also aus.
- **Gistix-Hooks:** Die RT-Engine-Hooks von CER sind gegen CS 1.9 noch nicht zur
  Laufzeit geprüft. Erst Falkos Test zeigt Abstürze oder falsches Licht.
- **Pflicht-DLLs für CER:** EngineFixes.dll und CrashLogger.dll. Fehlen sie, meldet CER
  einen Fehler und bleibt inaktiv.

## Bauen

GitHub Actions: Workflow „FalkosLichtspiel CS 1.9 RT“. Lokal unter Windows:
`python cs19rt/scripts/build_windows.py`.
