# Changelog

## 0.1.0-beta

First public beta.

- Based on Community Shaders 1.9.0 with all its features, plus the Creation Engine
  Raytracing backend (paired build).
- Raytracing modes: Global Illumination, Path Tracing (experimental) and three new hybrid
  modes: **RT AO**, **RT Lights** (all local lights with raytraced shadows) and
  **RT Lights + AO**.
- Raytracing disabled at boot costs nothing: no DirectX 12 bridge, no backend hooks.
- Smoother streaming: new objects are prepared for raytracing over several frames, nearest
  first, and unloaded objects are released over several frames.
- From Open Shaders: Vanilla Fresnel (off by default), Cloud Relight and Foliage Lighting.
- Inverse Square Lighting is not included; lights use the vanilla falloff in raster and RT.
- Menu renamed to Falkos Lichtspiel; bug reports go to the GitHub issue tracker.
