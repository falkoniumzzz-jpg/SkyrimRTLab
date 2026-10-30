// SPDX-License-Identifier: GPL-3.0-or-later
Texture2D<float4> Diagnostic : register(t0);
RWTexture2D<float4> MainColor : register(u0);
[numthreads(8, 8, 1)]
void main(uint2 pixel : SV_DispatchThreadID) {
    uint width, height, dw, dh;
    MainColor.GetDimensions(width, height);
    Diagnostic.GetDimensions(dw, dh);
    if (pixel.x >= min(width, dw) || pixel.y >= min(height, dh)) return;
    float4 value = Diagnostic.Load(int3(pixel, 0));
    if (value.a > 0.5) MainColor[pixel] = float4(value.rgb, MainColor[pixel].a);
}
