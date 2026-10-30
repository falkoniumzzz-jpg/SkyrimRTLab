"""Narrow fixes for the locked CER snapshot; never edit an unknown installation."""
from modify import replace
from pathlib import Path

def repair(cer):
    shader=cer/'shaders/raytracing/GlobalIllumination/RayGeneration.hlsl'
    replace(shader, '    const float depth = Depth.SampleLevel(DefaultSampler, dynamicUVUnjittered, 0);', '''    // Depth is a surface identity, not a filterable color. Clamp jitter at the border.
    uint depthWidth, depthHeight;
    Depth.GetDimensions(depthWidth, depthHeight);
    int2 depthPixel = clamp(int2(floor(dynamicUVUnjittered * float2(depthWidth, depthHeight))),
        int2(0, 0), int2(depthWidth, depthHeight) - 1);
    const float depth = Depth.Load(int3(depthPixel, 0));''')
    # RAW_RADIANCE without NRD is a separately validated variant, not an RR integration.
    replace(shader, '#if defined(NRD)\n     float diffHitDist = 0.0f;', '#if defined(RAW_RADIANCE) && !defined(NRD)\n    float diffHitDist = 0.0f;\n    float specHitDist = 0.0f;\n#endif\n#if defined(NRD)\n     float diffHitDist = 0.0f;')
    replace(shader, '#if defined(NRD)\n        float accumulatedHitDist = 0;', '#if defined(NRD) || defined(RAW_RADIANCE)\n        float accumulatedHitDist = 0;')
    replace(shader, '#if defined(NRD)\n            if (j == 0)\n                accumulatedHitDist = payload.hitDistance;', '#if defined(NRD) || defined(RAW_RADIANCE)\n            if (j == 0)\n                accumulatedHitDist = payload.hitDistance;')
    replace(shader, '#if defined(RAW_RADIANCE)\n        if (isSpecularSample)\n            specularRadiance += sampleRadiance;', '''#if defined(RAW_RADIANCE) && !defined(NRD)
        // Raw first-hit distances in game units; this is not NRD normalized distance.
        if (isSpecularSample) specHitDist += accumulatedHitDist / MAX_SAMPLES;
        else diffHitDist += accumulatedHitDist / MAX_SAMPLES;
#endif
#if defined(RAW_RADIANCE)
        if (isSpecularSample)
            specularRadiance += sampleRadiance;''')
    header=cer/'src/Pass/NRD/NRDIntegration.h'
    replace(header, 'bool m_ResourcesDirty = true;', 'bool m_ResourcesDirty = true;\n        bool m_ResetHistory = true;\n        uint32_t m_LastHistoryFrame = 0;')
    source=cer/'src/Pass/NRD/NRDIntegration.cpp'
    # Same lifecycle correction as newer CER: instantiate only the selected denoiser.
    replace(source, '\t\tSettingsChanged(Scene::GetSingleton()->m_Settings);\n\t\tSetup();', '\t\tSettingsChanged(Scene::GetSingleton()->m_Settings);')
    replace(source, 'void NRDIntegration::Initialize()\n\t{', 'void NRDIntegration::Initialize()\n\t{\n        Setup();\n        if (!m_NRD) return;')
    replace(source, 'void NRDIntegration::SettingsChanged(const Settings& settings)\n\t{', 'void NRDIntegration::SettingsChanged(const Settings& settings)\n\t{\n        const bool wasEnabled = m_Enabled;')
    replace(source, '\t\tUpdateSettings(settings);', '\t\tUpdateSettings(settings);\n        if (wasEnabled != m_Enabled) m_ResetHistory = true;')
    replace(source, 'void NRDIntegration::CreateResources()\n\t{', 'void NRDIntegration::CreateResources()\n\t{\n        m_ResetHistory = true;')
    replace(source, '\t\tUpdateCommonSettings();', '''        UpdateCommonSettings();
        const bool resetHistory = m_ResetHistory ||
            m_CommonSettings.frameIndex != static_cast<uint32_t>(m_LastHistoryFrame + 1u);
        m_CommonSettings.accumulationMode = resetHistory ?
            nrd::AccumulationMode::CLEAR_AND_RESTART : nrd::AccumulationMode::CONTINUE;
        if (resetHistory) {
            // Previous matrices/sizes are not meaningful for new history textures.
            std::memcpy(m_CommonSettings.worldToViewMatrixPrev, m_CommonSettings.worldToViewMatrix, sizeof(float4x4));
            std::memcpy(m_CommonSettings.viewToClipMatrixPrev, m_CommonSettings.viewToClipMatrix, sizeof(float4x4));
            std::memcpy(m_CommonSettings.resourceSizePrev, m_CommonSettings.resourceSize, sizeof(m_CommonSettings.resourceSize));
            std::memcpy(m_CommonSettings.rectSizePrev, m_CommonSettings.rectSize, sizeof(m_CommonSettings.rectSize));
            std::memcpy(m_CommonSettings.cameraJitterPrev, m_CommonSettings.cameraJitter, sizeof(m_CommonSettings.cameraJitter));
            logger::info("RTLab NRD history reset: frame={}, resources={}", m_CommonSettings.frameIndex, m_ResetHistory);
        }''')
    replace(source, '\t\t\tcommandList->endMarker();\n\t\t}\n\t}\n}', '''\t\t\tcommandList->endMarker();
\t\t}
        // Only advance history after all dispatches have been recorded successfully.
        m_ResetHistory = false;
        m_LastHistoryFrame = m_CommonSettings.frameIndex;
\t}
}''')

if __name__=='__main__':
    import sys
    repair(Path(sys.argv[1]))
