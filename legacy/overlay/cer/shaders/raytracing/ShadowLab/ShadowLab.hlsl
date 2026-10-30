// SPDX-License-Identifier: GPL-3.0-or-later
#include "interop/CameraData.hlsli"
#include "interop/RaytracingData.hlsli"
ConstantBuffer<CameraData> Camera : register(b0);
ConstantBuffer<RaytracingData> Data : register(b1);
RaytracingAccelerationStructure Scene : register(t0);
RWTexture2D<float4> Output : register(u0);
struct Payload { float distance; };

float TraceDistance(RayDesc ray) {
#if RTLAB_INLINE
    RayQuery<RAY_FLAG_FORCE_OPAQUE | RAY_FLAG_SKIP_PROCEDURAL_PRIMITIVES> query;
    query.TraceRayInline(Scene, RAY_FLAG_NONE, 0xff, ray);
    while (query.Proceed()) {}
    return query.CommittedStatus() == COMMITTED_TRIANGLE_HIT ? query.CommittedRayT() : -1.0;
#else
    Payload p; p.distance = -1.0;
    TraceRay(Scene, RAY_FLAG_FORCE_OPAQUE | RAY_FLAG_SKIP_PROCEDURAL_PRIMITIVES,
        0xff, 0, 0, 0, ray, p);
    return p.distance;
#endif
}
void Render(uint2 pixel) {
    if (any(pixel >= Camera.RenderSize)) return;
    float2 uv = (float2(pixel) + 0.5) / float2(Camera.RenderSize);
    float4 view = mul(Camera.ProjInverse, float4(uv.x * 2 - 1, 1 - uv.y * 2, 1, 1));
    RayDesc ray;
    ray.Origin = Camera.Position;
    ray.Direction = normalize(mul((float3x3)Camera.ViewInverse, view.xyz / view.w));
    ray.TMin = 0.1; ray.TMax = 100000.0;
    float distance = TraceDistance(ray);
    if (distance < 0) { Output[pixel] = 0; return; }
    float3 sun = Data.DirectionalLight.Direction;
    if (dot(sun, sun) < 0.001) { Output[pixel] = float4(1, 0, 1, 1); return; }
    sun = normalize(sun);
    // Diagnostic bias in Skyrim units, not a material-aware normal offset.
    ray.Origin += ray.Direction * (distance - 0.25) + sun * 0.25;
    ray.Direction = sun;
    float value = TraceDistance(ray) < 0 ? 0.8 : 0.025;
    Output[pixel] = float4(value.xxx, 1);
}
#if RTLAB_INLINE
[numthreads(8, 8, 1)]
void Main(uint2 pixel : SV_DispatchThreadID) { Render(pixel); }
#else
[shader("raygeneration")]
void Main() { Render(DispatchRaysIndex().xy); }
[shader("miss")]
void Miss(inout Payload p) { p.distance = -1; }
[shader("closesthit")]
void ClosestHit(inout Payload p, BuiltInTriangleIntersectionAttributes attributes) { p.distance = RayTCurrent(); }
#endif
