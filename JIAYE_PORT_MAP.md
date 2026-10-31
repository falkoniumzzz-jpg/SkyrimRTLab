# Jiaye pp -> CER port map

Concrete preparation for the future integration, not an implemented render adapter.
Pinned Jiaye: `2f459a4c0d2c2130603555e3bf3ab17e8fd6342d`.
Pinned CER: `09350844e63f602a3b788f1c815d29cee1b4fab2` plus `legacy/cer-rt.patch`.

## Required pass split

Jiaye `src/Deferred.cpp::DeferredPasses` copies completed opaque depth before SSGI,
then performs SSGI/SSS, cubemap update, the deferred composite and post-deferred
effects. Our existing RTLab observer runs after the composite and is **read-only**.
It must not be reused as a write/submit callback without a new ABI/capability.

The future renderer needs two distinct stages:

1. After opaque G-buffer/depth are complete, before composing indirect light:
   collect raw resources, convert material/normal/depth conventions, submit CER.
2. In the deferred composite: replace explicitly selected indirect-light terms.
   Preserve raster direct lighting, emissive, fog and unrelated surface effects.
   Prevent double counting with SSGI, IBL and environment/cubemap reflections.

## Source-backed input findings

| Input | Jiaye source | Required decision/conversion |
|---|---|---|
| Opaque depth | Deferred.cpp copies kMAIN depth into kPOST_ZPREPASS_COPY, sets sceneDepthFinal. Utils/D3D.cpp::GetCurrentSceneDepthSRV returns that finished copy when available. | Select the current depth at the chosen pass and inspect the actual view/resource format; do not assume every stage uses a prepass or a particular storage format. |
| Shading normals | package/Shaders/Common/GBuffer.hlsli decodes the sign-adjusted octahedral normal. | Decode first, transform view -> world with the matching frame's inverse view matrix, normalize, and keep normal-map detail. |
| Roughness | The legacy RT conversion reads smoothness from the raster normal target's Z channel. | Audit every Jiaye writer/TruePBR path; remap/clamp exactly once for the tracer and its denoiser guides. Do not pass encoded normal/smoothness directly to CER. |
| Masks2 | Jiaye Lighting.hlsl writes `(1 - vertexAO, 0, 0, alpha)`; RunGrass and Effect have their own writers. DeferredCompositeCS explicitly documents inverted vertex AO in X. | **Not** CER's legacy GNMAO contract, which reads metalness from Y and AO from `1-Z`. Blind reuse loses AO and metallic material information. Inventory TruePBR/extended material outputs and supply explicit material channels. |
| Albedo/color | LinearLighting.cpp emits ENABLE_LL, ENABLE_ACESCG and CS_GAME_GAMMA. Common/ColorManagement.hlsli distinguishes PBR material encoding, scene encoding, Effects11 and working color space. | Choose one declared linear working space for CER/RR. Convert all material/light/sky inputs and composite outputs consistently. Do not copy the old pow(2.2) helper into Jiaye's pipeline as a universal conversion. |
| Motion | Native motion SRV is available in DeferredPasses; the composite also writes motion vectors. | Pick a stage, document current->previous direction, jitter inclusion, UV/pixel units and viewport extent; validate camera and skeletal movement. |
| Reflectance | Jiaye exposes a separate REFLECTANCE target to its composite. | Audit its actual writers before using it as F0, RR specular albedo or metalness. These are different quantities. |
| Dimensions | Engine render extent may occupy only a subrectangle of screen-sized resources. | Separate storage sampling coordinates from projection UVs, dispatch extent and denoiser input extent. Keep a common frame/slot identity. |

## Non-image integration work still required

- Own the DX11/DX12 shared-resource lifetime and queue/fence protocol explicitly.
  Use the same adapter; do not assume an upscaling device grants RT capability.
- Inventory CER engine hooks in Hooks.cpp / SceneGraph and their overlap with
  Jiaye hooks; install exactly one owner for conflicting hooks.
- Reconcile feature/material layouts. The older CER copied CS-specific feature
  structs are not binary-compatible with Jiaye's changed color/material settings.
- Port mesh creation/destruction, transforms, skinning, alpha-test and LOD feeds;
  validate BLAS/TLAS contents before judging lighting.
- Implement a new render-capable host contract. Leave the existing ObserveOnly
  diagnostic contract and its SRV borrowing/lifetime rules intact.

## Assembly gates for Claude

1. Pin and reproduce both independently working source preparations.
2. Confirm a pass/input/material contract for each table row; record unresolved ones.
3. Compile and inspect converted guides before enabling RT contribution.
4. Validate geometry and GPU synchronization, then integrate one GI term.
5. Review RR and ReSTIR against that same primary-surface/frame contract.
6. Build a separate MO2 package and run the runtime checks in CLAUDE_REVIEW.md.

The native RT branch supplies useful tracing/denoising work, not a drop-in
backend for arbitrary public CS or Jiaye DLLs. This map is the handoff boundary.
