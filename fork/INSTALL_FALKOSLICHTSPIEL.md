# FalkosLichtspiel – Entwicklungsbuild

Eigenständiger CS-1.9-Fork mit Diagnose-Anbindung, noch OHNE portiertes Hardware-RT.
Die sichtbare Menübezeichnung lautet FalkosLichtspiel.
Basiert auf Community Shaders 1.9.0; Copyright und Lizenz der ursprünglichen Autoren bleiben erhalten.

1. FalkosLichtspiel-MO2.zip direkt über MO2 installieren. SKSE und Shaders liegen im ZIP-Hauptverzeichnis.
2. Separates MO2-Testprofil verwenden. Andere CS-/Open-Shaders-Installationen und das alte
   SkyrimRTLab/CER-Paket in diesem Profil deaktivieren. Keine CER-DLL dazumischen.
3. Passendes SKSE, Address Library und weitere Voraussetzungen der zugrunde liegenden
   CS-Version müssen vorhanden sein. Skyrim über SKSE/MO2 starten.
4. Menü mit der bisherigen CS-Menütaste öffnen (standardmäßig Ende). Titel und Startseite:
   FalkosLichtspiel. Vorhandene Einstellungen können die Taste ändern.
5. Diagnose bei Bedarf in SKSE/Plugins/RTLab/RTLab.ini aktivieren und Spiel neu starten.
   Ausgaben stehen mit [RTLab] in CommunityShaders.log.

Die Datei CommunityShaders.dll, interne Plugin-ID und Einstellungsordner behalten ihre
technischen Namen. Ein sichtbarer Eigenname ist kein neues kompatibles Plugin-ABI.
Keine Ingame-Validierung und keine Zusage besserer Bildqualität oder FPS.
