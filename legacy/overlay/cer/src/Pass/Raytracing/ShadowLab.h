// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "Pass/RenderPass.h"
#include "Pass/Raytracing/Common/SceneTLAS.h"
#include "Events/ITLASUpdateListener.h"

namespace Pass {
class ShadowLab final : public RenderPass, public ITLASUpdateListener {
    SceneTLAS* m_TLAS;
    bool m_Inline;
    nvrhi::BindingLayoutHandle m_Layout;
    nvrhi::ComputePipelineHandle m_Compute;
    nvrhi::rt::PipelineHandle m_Pipeline;
    nvrhi::rt::ShaderTableHandle m_Table;
    eastl::array<nvrhi::BindingSetHandle, Constants::MAX_FRAMES_IN_FLIGHT> m_Bindings{};
public:
    ShadowLab(Renderer* renderer, SceneTLAS* tlas);
    void OnTLASResized([[maybe_unused]] TopLevelAS& tlas) override { m_Bindings.fill(nullptr); }
    void ResolutionChanged([[maybe_unused]] uint2 resolution) override { m_Bindings.fill(nullptr); }
    void CreatePipeline() override;
    void Execute(nvrhi::ICommandList* commands) override;
};
}
