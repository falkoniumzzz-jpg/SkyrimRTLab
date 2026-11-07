# Falkos Lichtspiel

Hardware raytracing for Skyrim Special Edition / Anniversary Edition, built on
**Community Shaders 1.9** and **Creation Engine Raytracing (CER)**.

Falkos Lichtspiel is a complete replacement for Community Shaders. It contains all
Community Shaders 1.9 features plus a hardware-raytracing backend with several modes,
from a light hybrid mode to full raytraced global illumination.

> **Beta.** Tested by the author on one PC (RTX 5080, Windows). Other GPUs and setups
> are untested. Expect bugs and please report them (see *Bug reports* below).

## Requirements

- Skyrim Special Edition or Anniversary Edition (SE 1.5.97 or AE 1.6.x), **not VR**
- [SKSE64](https://skse.silverlock.org/)
- [Address Library for SKSE Plugins](https://www.nexusmods.com/skyrimspecialedition/mods/32444)
- [SSE Engine Fixes](https://www.nexusmods.com/skyrimspecialedition/mods/17230) (the raytracing backend stays off without it)
- Crash Logger SSE AE VR (the raytracing backend stays off without it)
- Windows 10 or 11
- For raytracing: a GPU with hardware raytracing (DirectX Raytracing 1.1), e.g. NVIDIA RTX.
  DLSS Ray Reconstruction is NVIDIA RTX only.

## Installation

1. **Disable or remove Community Shaders** and its feature add-ons. Falkos Lichtspiel
   uses the same file names (`CommunityShaders.dll`, `Shaders/...`) and replaces them.
   Do not install both.
2. Install the archive with Mod Organizer 2 or Vortex like any other mod.
3. Start the game. Open the menu with **End** (same key as Community Shaders).

Optional: install `FalkosLichtspiel-<version>-PDBs.zip` as a second mod. It adds debug
symbols so that Crash Logger writes readable crash logs.

## Raytracing modes

Menu → *Raytracing* → *Mode*:

| Mode | What is raytraced | Cost |
|---|---|---|
| None | Nothing (plain Community Shaders image) | — |
| RT AO | Ambient occlusion only | low |
| RT Lights | All local lights (torches, candles, fires, magic, lamps) with real shadows | medium |
| RT Lights + AO | Both of the above | medium |
| Global Illumination | Indirect diffuse and specular light | high |
| Path Tracing | Full path tracing (experimental) | very high |

- In the hybrid modes (RT AO / RT Lights) the sun, sky light and reflections stay raster.
- **Raytracing off costs nothing:** tick *Raytracing* under *Disable at Boot* and restart.
  The DirectX 12 bridge is then not started and the backend installs no hooks.
- Changing *Disable at Boot* needs a game restart.

## Known issues

- RT Lights: the 4 strongest lights per pixel cast shadows, weaker lights are unshadowed
  (like raster lights). Lights inside a lamp or lantern model may cast slightly wrong shadows.
- Transparent objects, particles and hair keep raster lighting in the RT Lights modes.
- Extended Materials parallax shadows are not raytraced.
- After a loading screen, distant objects can appear in the raytraced lighting a moment later.
  This is intended (streaming is spread over several frames to avoid stutter).
- Only tested on NVIDIA RTX 50. AMD and Intel GPUs are untested.

## Uninstall

Disable or remove the mod. Settings are stored in
`SKSE/Plugins/CommunityShaders/SettingsUser.json` inside the mod (or your overwrite folder).

## Bug reports

Please report problems at <https://github.com/falkoniumzzz-jpg/SkyrimRTLab/issues> and attach:

- `Documents/My Games/Skyrim Special Edition/SKSE/CommunityShaders.log`
- `Documents/My Games/Skyrim Special Edition/SKSE/CreationEngineRaytracing.log`
- a Crash Logger `crash-*.log` if the game crashed
- for a hang (endless loading screen): press **Ctrl+Shift+F12** while the game hangs,
  wait ten seconds, then attach the thread dump Crash Logger writes.

**Do not report Falkos Lichtspiel problems to the Community Shaders or CER developers.**
This is an independent fork; they cannot help with it.

## Credits

- **Community Shaders** team and contributors: the base of this mod.
  <https://github.com/community-shaders/skyrim-community-shaders>
- **Gistix**: Creation Engine Raytracing and the raytracing host integration.
  <https://github.com/Gistix/CreationEngineRaytracing>
- **Open Shaders** (alandtse and contributors): Vanilla Fresnel, Cloud Relight and Foliage Lighting.
- **NVIDIA**: Streamline / DLSS and the Cloud Relight shaders. **AMD**: FidelityFX.

Falkos Lichtspiel adds the hybrid raytracing modes (RT AO, RT Lights, RT Lights + AO),
streaming and stability changes, and the Community Shaders 1.9 port of the raytracing host.

## License and source code

GPL-3.0-or-later with the Community Shaders modding and linking exceptions. All license
texts are in `FalkosLichtspiel Docs/licenses`. The complete corresponding source code is
published with every release (`FalkosLichtspiel-<version>-Source.zip`) and at
<https://github.com/falkoniumzzz-jpg/SkyrimRTLab>.

The Community Shaders logo is not covered by the GPL and is therefore not included.
