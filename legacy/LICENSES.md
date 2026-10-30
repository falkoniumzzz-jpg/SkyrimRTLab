# Herkunft und Lizenzumfang

Neue Integration und HLSL unter `overlay/` sowie Änderungen an CS/CER:
GPL-3.0-or-later, im Zusammenhang mit den unverändert beigelegten Modding-/Linking-Ausnahmen
der jeweiligen Projekte. Bestehende Copyright-Hinweise werden nicht entfernt.

Eigenständige Probe, Buildskripte, Root-CMake und Dokumentation: MIT, siehe `LICENSE-MIT.txt`.

Upstream:

- Community Shaders: `COPYING`, `EXCEPTIONS.md` und Hinweise im README.
- Creation Engine Raytracing: `COPYING`, `EXCEPTIONS.md`.
- NVRHI, NRD und weitere NVIDIA-/Microsoft-Komponenten haben eigene Lizenzdateien.
- CommonLib, vcpkg-Pakete, DirectX-Headers, DXC, RTXDI, Streamline/DLSS und FidelityFX
  behalten ihre eigenen Hinweise. Die Buildskripte laden die festgelegten Abhängigkeiten.
- Das Community-Shaders-Logo ist ausdrücklich nicht allgemein zur Weitergabe freigegeben.
  Der Paketierer entfernt den betreffenden Logo-Ordner aus Runtime- und Source-Artefakten.
  Das Runtime-DLL-Namensschema bleibt aus technischen Gründen unverändert.

Diese Lieferung enthält eigene Quellen/Änderungsanweisungen und die Upstream-Lizenztexte,
keine fertig gebauten Skyrim-DLLs. Die lokal cross-kompilierte Probe wird nicht als Binary
mitverteilt; CI baut sie für dich neu und legt ihren Quellcode bei.

Der Windows-Build erzeugt zusätzlich `Corresponding-Source.zip`: geänderte Projektquellen,
Submodule, CMake-FetchContent-Quellen, vcpkg-Ports und die verfügbaren vcpkg-Buildquellen.
Binäres vcpkg-Caching ist deaktiviert, damit diese Quellen tatsächlich lokal anfallen.
System-SDKs und Compiler sind separat beschaffbare Buildwerkzeuge, keine eingebetteten Quellen.

Die Vollständigkeit dieses erst beim Windows-Build entstehenden Archivs ist hier noch nicht
geprüft. Vor öffentlicher Weitergabe fertiger DLLs müssen dessen Vollständigkeit und die
jeweiligen Rechte an eingebundenen proprietären Redistributables geprüft werden.
Ein erfolgreicher Compilerlauf ist keine solche Lizenzprüfung. Für den persönlichen
Build-/Testablauf werden die Herkunft und Lizenzdateien erhalten.
