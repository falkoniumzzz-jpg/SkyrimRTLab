# FalkosLichtspiel RT — separate experiment

This branch preserves the Jiaye raster fork files but builds a **separate native
DXR test variant from the pinned CS PR-2196 / CER pair** in `legacy/sources.lock.json`.
It is not a completed hardware-RT port into Jiaye pp / CS 1.9. The existing
`dev/falkoslichtspiel-jiaye` branch and its packages are independent.

## Foundation update (31 October 2026)

See [CLAUDE_REVIEW.md](CLAUDE_REVIEW.md) for the new material-guide export,
submitted-frame selection, ABI 0x20261031 and independent review checklist.
[JIAYE_PORT_MAP.md](JIAYE_PORT_MAP.md) records concrete Jiaye migration blockers.
The new native source fixes the previously reported menu warning; the latest
Windows run must still confirm full compilation and packaging.

## Changes

- In-game window, heading and home page say **FalkosLichtspiel RT**. DLL names
  remain CommunityShaders.dll and CreationEngineRaytracing.dll.
- RTGI writes a current specular first-hit-distance signal for RR, including zero
  on sky/invalid pixels. This removes the missing-writer / stale-PT-buffer defect.
- Streamline resets reconstruction history when RT settings, mode, output size,
  frame continuity or loading/main-menu state require it. NRD history remains separate.
- The raster-to-RT input conversion receives the current frame's resolution before dispatch.
- ReSTIR GI is connected to raster-primary RTGI, with current/previous packed
  surfaces, secondary positions, incident radiance/PDF and engine motion vectors.
- One rough opaque primary sample per pixel uses a known cosine proposal with full
  non-delta BSDF evaluation. RTXDI temporal/spatial/fused modes can resample it.
- The hybrid final pass **replaces** that sample's original 1/SPP contribution
  in the linear GI buffer. It does not add GI on top of the same estimator twice.
- Misses, smooth/unsupported materials, invalid reservoirs and failed visibility
  retain the original estimator. Raster direct lighting remains in the CS composite.
- ReSTIR history is invalidated on settings, resource size, SPP or frame discontinuities.
  The shared packed-surface writer now initializes padding, which DXIL validation requires.

## Limits and test procedure

Experimental source changes are not proof of fixed image quality. A DLL build only
checks compilation/linking; Skyrim runtime, RR detail retention, ghosting,
lighting stability, GPU validation and performance require a real RTX test.

1. Use a **separate MO2 profile** with matching SKSE/Address Library and this package.
   Enable only one CS distribution at a time; this package supplies both paired DLLs.
2. Start in RTGI, ReSTIR disabled. Compare RR off versus RR on with Linear Lighting
   enabled, fixed exposure, fixed DLSS quality, same camera and same SPP.
3. Check a static shadowed wall and moving character, then PT -> RTGI and fast travel.
   Record whether detail loss and ghosting change independently.
4. Enable ReSTIR GI with RR or None and compare Temporal, Spatial and Temporal+Spatial.
   At 1 SPP, rough opaque surface hits are the intended first test. Higher SPP replaces
   only one sample's contribution, so the visible difference can be smaller.
5. NRD does **not** use this experimental hybrid resampling path. PT ReSTIR still
   requires Stable Planes. A disabled/unsupported combination is not a quality comparison.

This implementation reuses the existing experimental RTXDI application bridge,
including its visibility/material approximations. Sky reuse, transmission, hair,
low-roughness reuse and NRD integration remain out of scope for this first patch.
RR material/color-space contract and reflected-motion quality still need GPU inspection.
The complete Jiaye 1.9/CER port remains further work.

## Reproduction

`legacy/scripts/prepare_sources.py` fetches exact revisions, applies existing
repairs, then checked `cs-rt.patch` and `cer-rt.patch`. The ABI check compares 27
ordered settings declarations. `check_rt_shaders.py` compiles real GI producers,
RTXDI consumers and the RR preprocessor, on both inline and DXR-library paths.
The `rt-experiment.yml` workflow gates the Windows DLL/package build on shader checks.
