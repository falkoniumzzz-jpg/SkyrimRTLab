# FalkosLichtspiel RT — experimental second variant

This branch adds a separate native DXR test build with RR corrections and experimental
RTGI ReSTIR. See [RT_EXPERIMENT.md](RT_EXPERIMENT.md) for scope, build and testing.
The native RT variant uses the pinned older CS/CER pair, not a completed Jiaye 1.9 port.

The preserved raster build integrates FalkosLichtspiel with Jiaye's pinned CS 1.9 pp snapshot.
It carries the requested SSGI, material/Fresnel, lighting and rain implementations
as part of the coherent upstream raster stack, including their dependencies.

Details: [fork/JIAYE_INTEGRATION.md](fork/JIAYE_INTEGRATION.md).
Install instructions: [fork/INSTALL_FALKOSLICHTSPIEL.md](fork/INSTALL_FALKOSLICHTSPIEL.md).
Windows compilation and the MO2 artifact must pass CI before installation.
Hardware RT/CER is not integrated in this variant yet.
