# FalkosLichtspiel: Jiaye integration

Pinned upstream: jiayev/skyrim-community-shaders `pp`,
`2f459a4c0d2c2130603555e3bf3ab17e8fd6342d` (2026-10-27).
Separate branch: dev/falkoslichtspiel-jiaye.

This variant uses Jiaye's complete pp snapshot as its coherent raster base.
It includes the requested SSGI, lighting/color processing, Fresnel/material shading
and Rain Refraction, plus their supporting Effects11, scene-management and
postprocessing changes. These are inherited upstream implementations, not features
newly written by RTLab. No older hardware-RT branch is imported.

Our patch adds the FalkosLichtspiel title, observer DLL interface, loading/resource
epoch notifications, and preserves the fixes for disabled DevBench linking and
CommonLib source build options. Visible credits name Community Shaders and Jiaye.
Technical DLL names and settings paths remain compatible with the CS layout.

Current Fresnel behavior is part of the material/BRDF, cubemap and wetness paths;
there is no separate newly invented Vanilla Fresnel toggle. Rain Refraction uses
the bundled raindrop texture; active Effects11 presets can control its appearance.
SSGI remains a screen-space technique. It is not hardware RTGI and does not fix RR.

Local checks: patch applies to the pinned upstream, repeated application produces
the same manifest, git diff --check passes. Windows compilation, shader validation,
MO2 package and Skyrim appearance are pending CI/runtime tests.

The original official-CS-based branch dev/cs-1.9-rt-host stays available for comparison.
The older hardware-RT test package on main remains a different product stage.
