// SPDX-License-Identifier: MIT
RaytracingAccelerationStructure Scene : register(t0);
RWTexture2D<float> Output : register(u0);
[numthreads(8,8,1)]
void Main(uint2 pixel : SV_DispatchThreadID) {
    if (any(pixel >= 128)) return;
    RayDesc ray;
    ray.Origin = float3((float2(pixel)+0.5)/128.0*2.0-1.0,-1.0);
    ray.Direction = float3(0,0,1);
    ray.TMin = 0.001; ray.TMax = 2.0;
    RayQuery<RAY_FLAG_FORCE_OPAQUE | RAY_FLAG_ACCEPT_FIRST_HIT_AND_END_SEARCH> q;
    q.TraceRayInline(Scene,RAY_FLAG_NONE,255,ray);
    while(q.Proceed()) {}
    Output[pixel] = q.CommittedStatus() == COMMITTED_TRIANGLE_HIT ? 0.0 : 1.0;
}
