# Quellcodebefunde und Entscheidung

Untersuchung am 23.10.2026. Commit-IDs bezeichnen konkrete untersuchte Stände, keine
Behauptung, dass ein Branch dauerhaft auf diesem Commit bleibt.

| Projekt | Öffentliches Repository | Untersucht |
|---|---|---|
| Community Shaders | https://github.com/community-shaders/skyrim-community-shaders | dev `3c7691e451e4f61d4f55865e59a7c8af3d6dc72f` |
| Open Shaders | https://github.com/alandtse/open-shaders | dev `d66ccad74298929a4cdd07c177ad880f92268b21` |
| Creation Engine Raytracing | https://github.com/Gistix/CreationEngineRaytracing | main `670b42da956d604d82ada9445944ba16cb8c1ad5` |

Community Shaders und Open Shaders ersetzen/ergänzen Skyrim-DX11-Shader und hängen
sich in Renderpasses ein. Vorhandenes ScreenSpaceGI/SSR oder eine DX12-Upscaling-Brücke
ist für sich kein Nachweis von Hardware-Raytracing. Im untersuchten Open-Shaders-Stand
wurde keine entsprechende TraceRay/RayQuery-/Acceleration-Structure-Implementierung gefunden.
Das ist eine Aussage über diesen untersuchten Stand, nicht über alle zukünftigen Branches.

Die konkrete RT-Entwicklung befindet sich in Gistix' Arbeit:

- https://github.com/community-shaders/skyrim-community-shaders/pull/2196 — RT-Plugin-Integration,
  untersuchter Head `84114745a7ee9991bc0543d7a5740cbd09688b1f`.
- https://github.com/community-shaders/skyrim-community-shaders/pull/1658 — älterer monolithischer Ansatz.
- https://github.com/community-shaders/skyrim-community-shaders/issues/1657 — Entwicklungsdiskussion;
  historische Funktionsberichte ersetzen keinen eigenen Test.
- Gistix' `rt-vulkan-pp-water`, untersucht bei `e6c423cf96ff2fff790bba534bae99c29f698230`,
  ist eine neuere Vulkan-Integrationsrichtung und verlangt eine andere Umgebung.

CER enthält reale Geometrie-Hooks, GPU-Skinning, BLAS/TLAS, DXR-/RayQuery-Passes,
Shader Binding Tables, Path-Tracing/GI, RTXDI und NRD. Es handelt sich um eine echte
Implementierung, nicht nur um eine Grafik-Demo oder ein Konzeptpapier. Ob ein bestimmter
Build auf einer bestimmten Skyrim-Version stabil funktioniert, wurde hier nicht festgestellt.

## Gewählte Basis

CS PR 2196: `84114745a7ee9991bc0543d7a5740cbd09688b1f`.
CER: `09350844e63f602a3b788f1c815d29cee1b4fab2`.

Die bewusste ältere Paarung erhält den nativen DX11/DX12-Pfad. Neuester CER-main und
dieser CS-Head sind nicht einfach austauschbar: Die Settings-Strukturen und die
GetSharedTextures-/GetRRInput-Signaturen haben sich verändert. Settings werden als
C++-Werte übergeben; der DLL-Dateiname alleine schützt nicht vor ABI-Fehlern.
`validate.py` vergleicht 27 geordnete Typ-/Enum-Deklarationen. Der zusätzliche Export
`GetShadowLabABI` verhindert die versehentliche Paarung mit einem unmodifizierten Backend.
Compiler-/STL-ABI bleibt zusätzlich zu beachten; deshalb baut CI beide DLLs gemeinsam.

## Nachprüfbare Dateien in der gewählten Basis

| Aufgabe | Tatsächlicher Pfad |
|---|---|
| DX11-Gerät und Renderer-Hooks | CS `src/Hooks.cpp` |
| GPU-Wartekette | CS `src/DX12Interop.h`, `src/DX12Interop/InteropContext.h` |
| RT-Aufruf und Bildintegration | CS `src/Features/Raytracing.cpp` |
| Host-Schnittstelle | CS `include/CreationEngineRaytracing.h` |
| D3D11-Buffer- und Geometrie-Hooks | CER `src/Hooks.cpp` |
| Mesh-Verarbeitung | CER `src/Core/Mesh/BaseMesh.cpp`, `src/Core/BLASCluster.cpp` |
| TLAS | CER `src/Types/TopLevelAS.h`, `src/Pass/Raytracing/Common/SceneTLAS.cpp` |
| Pass-Reihenfolge | CER `src/Scene.cpp` |
| Shared Render Targets | CER `src/Renderer/RenderTargetManager.cpp` |
| Shader-Compiler und Cache | CER `src/ShaderUtils.cpp`, `src/ShaderCache.cpp` |
| Vorhandener SBT-Aufbau | CER `src/Pass/Raytracing/Debug.cpp` |

`scripts/modify.py` enthält die vollständigen, kontrollierten Änderungen. Jede Änderung
prüft ihren exakten Anker und bricht bei unerwartetem Quellcode ab. `overlay/` enthält
alle neuen C++- und HLSL-Dateien. Der erste neue Pass nutzt die bestehende Szenenerfassung;
ein zweiter unabhängiger Skyrim-Geometrieparser wäre hier unnötig und fehleranfälliger.
