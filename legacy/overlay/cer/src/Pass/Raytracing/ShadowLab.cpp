// SPDX-License-Identifier: GPL-3.0-or-later
#include "ShadowLab.h"
#include "Renderer.h"
#include "Scene.h"
#include "ShaderCache.h"

namespace Pass {
ShadowLab::ShadowLab(Renderer* renderer, SceneTLAS* tlas) : RenderPass(renderer),
    m_TLAS(tlas), m_Inline(renderer->m_Settings.UseRayQuery) {
    m_TLAS->GetTopLevelAS().AddListener(this);
}
void ShadowLab::CreatePipeline() {
    auto* device = GetRenderer()->GetDevice();
    m_Compute = nullptr; m_Pipeline = nullptr; m_Table = nullptr;
    m_Bindings.fill(nullptr);
    nvrhi::BindingLayoutDesc layout;
    layout.visibility = m_Inline ? nvrhi::ShaderType::Compute : nvrhi::ShaderType::AllRayTracing;
    layout.bindings = {
        nvrhi::BindingLayoutItem::VolatileConstantBuffer(0),
        nvrhi::BindingLayoutItem::VolatileConstantBuffer(1),
        nvrhi::BindingLayoutItem::RayTracingAccelStruct(0),
        nvrhi::BindingLayoutItem::Texture_UAV(0)};
    m_Layout = device->createBindingLayout(layout);
    if (!m_Layout) return;
    eastl::vector<DxcDefine> defines{{L"RTLAB_INLINE", m_Inline ? L"1" : L"0"}};
    auto blob = ShaderCache::GetShader(L"data/shaders/raytracing/ShadowLab/ShadowLab.hlsl",
        defines, m_Inline ? L"cs_6_5" : L"lib_6_5", L"Main");
    if (!blob) { logger::error("ShadowLab: shader compilation failed"); return; }
    if (m_Inline) {
        auto shader = device->createShader({nvrhi::ShaderType::Compute, "ShadowLab", "Main"},
            blob->GetBufferPointer(), blob->GetBufferSize());
        if (shader) m_Compute = device->createComputePipeline(nvrhi::ComputePipelineDesc()
            .setComputeShader(shader).addBindingLayout(m_Layout));
    } else {
        auto library = device->createShaderLibrary(blob->GetBufferPointer(), blob->GetBufferSize());
        if (!library) return;
        nvrhi::rt::PipelineDesc pipeline;
        pipeline.shaders = {
            {"RayGen", library->getShader("Main", nvrhi::ShaderType::RayGeneration), nullptr},
            {"Miss", library->getShader("Miss", nvrhi::ShaderType::Miss), nullptr}};
        pipeline.hitGroups = {{"HitGroup", library->getShader("ClosestHit", nvrhi::ShaderType::ClosestHit),
            nullptr, nullptr, nullptr, false}};
        pipeline.addBindingLayout(m_Layout);
        pipeline.maxPayloadSize = sizeof(float);
        pipeline.maxRecursionDepth = 1;
        m_Pipeline = device->createRayTracingPipeline(pipeline);
        if (m_Pipeline) {
            m_Table = m_Pipeline->createShaderTable(nvrhi::rt::ShaderTableDesc().setDebugName("ShadowLab SBT"));
            if (m_Table) {
                m_Table->setRayGenerationShader("RayGen");
                m_Table->addMissShader("Miss");
                m_Table->addHitGroup("HitGroup");
            }
        }
    }
    logger::info("ShadowLab (Community Shaders + Creation Engine Raytracing): {} pipeline {}",
        m_Inline ? "DXR inline" : "DXR SBT", (m_Compute || (m_Pipeline && m_Table)) ? "created" : "FAILED");
}
void ShadowLab::Execute(nvrhi::ICommandList* commands) {
    auto* renderer = GetRenderer();
    const auto slot = renderer->GetCurrentSlot();
    const auto resolution = renderer->GetDynamicResolution();
    commands->clearTextureFloat(renderer->GetMainTexture(), nvrhi::AllSubresources, nvrhi::Color(0.f));
    if ((!m_Compute && !(m_Pipeline && m_Table)) || !resolution.x || !resolution.y) return;
    if (!m_Bindings[slot]) {
        nvrhi::BindingSetDesc bindings;
        bindings.bindings = {
            nvrhi::BindingSetItem::ConstantBuffer(0, Scene::GetSingleton()->GetCameraBuffer()),
            nvrhi::BindingSetItem::ConstantBuffer(1, m_TLAS->GetRaytracingBuffer()),
            nvrhi::BindingSetItem::RayTracingAccelStruct(0, m_TLAS->GetTopLevelAS().GetHandle()),
            nvrhi::BindingSetItem::Texture_UAV(0, renderer->GetMainTexture())};
        m_Bindings[slot] = renderer->GetDevice()->createBindingSet(bindings, m_Layout);
    }
    if (!m_Bindings[slot]) return;
    commands->beginMarker("ShadowLab: primary and sun visibility");
    if (m_Inline) {
        nvrhi::ComputeState state;
        state.pipeline = m_Compute; state.bindings = {m_Bindings[slot]};
        commands->setComputeState(state);
        commands->dispatch((resolution.x + 7u) / 8u, (resolution.y + 7u) / 8u);
    } else {
        nvrhi::rt::State state;
        state.shaderTable = m_Table; state.bindings = {m_Bindings[slot]};
        commands->setRayTracingState(state);
        nvrhi::rt::DispatchRaysArguments args;
        args.width = resolution.x; args.height = resolution.y;
        commands->dispatchRays(args);
    }
    commands->endMarker();
}
}
