"""Checked, idempotent edits against the two locked upstream commits."""
from pathlib import Path
import shutil

def replace(path, old, new):
    text = path.read_text(encoding="utf-8-sig")
    if new in text: return
    if text.count(old) != 1: raise RuntimeError(f"Patch anchor not unique/missing: {path}: {old[:60]}")
    path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")

def modify(root, cs, cer):
    for name, dest in (("cs", cs), ("cer", cer)):
        shutil.copytree(root / "overlay" / name, dest, dirs_exist_ok=True)
    # SKSE pulls in xbyak/Windows headers. Parse the complete RE declarations
    # first, as the successfully built CS host does, before Windows macros can
    # replace names such as REX::W32::MAX_PATH and InterlockedCompareExchange.
    pch = cer / "include/PCH.h"
    replace(pch, '#\tinclude <SKSE/SKSE.h>\n#\tinclude <RE/Skyrim.h>',
                 '#\tinclude <RE/Skyrim.h>\n#\tinclude <SKSE/SKSE.h>')
    replace(pch, '#pragma once\n', '''#pragma once

#ifndef NOMINMAX
#define NOMINMAX
#endif
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
''')
    replace(pch, '#define WIN32_LEAN_AND_MEAN\n#include "Windows.h"\n\n#define NOMINMAX',
                 '#include "Windows.h" // Windows policy macros are defined before all includes.')
    replace(cer/"src/Scene.cpp", '#include "Pass/Raytracing/Debug.h"', '#include "Pass/Raytracing/ShadowLab.h"')
    replace(cer/"src/Scene.cpp", 'eastl::make_unique<Pass::Debug>(renderer, sceneTLAS.get())',
        'eastl::make_unique<Pass::ShadowLab>(renderer, sceneTLAS.get())')
    replace(cer/"src/API.h", 'extern "C" {', 'extern "C" {\n\tCERT_API uint32_t GetShadowLabABI();')
    replace(cer/"src/API.cpp", '#include "API.h"', '#include "API.h"\nuint32_t GetShadowLabABI() { return 0x20261023u; }')
    replace(cer/"src/API.cpp", '\treturn Renderer::GetSingleton()->Initialize(rendererSettings, d3d11Device, d3d12Device, commandQueue, computeCommandQueue, copyCommandQueue);', '''
    D3D12_FEATURE_DATA_D3D12_OPTIONS5 options{};
    if (!rendererSettings || !d3d12Device || FAILED(d3d12Device->CheckFeatureSupport(
        D3D12_FEATURE_D3D12_OPTIONS5, &options, sizeof(options))) ||
        options.RaytracingTier < (rendererSettings->UseRayQuery ? D3D12_RAYTRACING_TIER_1_1 : D3D12_RAYTRACING_TIER_1_0)) {
        logger::error("ShadowLab: required DXR tier unavailable");
        return false;
    }
    return Renderer::GetSingleton()->Initialize(rendererSettings, d3d11Device, d3d12Device, commandQueue, computeCommandQueue, copyCommandQueue);''')
    p = cer/"src/Pass/Raytracing/Common/SceneTLAS.cpp"
    old = '''\t\t\tauto dirLight = ce_cast<RE::NiDirectionalLight*>(Util::Adapter::GetShaderManagerState().shadowSceneNode[0]->GetRuntimeData().sunLight->light.get());
\t\t\tauto& lightRuntimeData = dirLight->GetLightRuntimeData();
\t\t\tm_RaytracingData->DirectionalLight.Direction = -Util::Math::Normalize(Util::Math::Float3(dirLight->GetWorldDirection()));
\t\t\tm_RaytracingData->DirectionalLight.Color = Util::Math::Float3(lightRuntimeData.diffuse);
\t\t\tm_RaytracingData->DirectionalLight.Fade = lightRuntimeData.fade;'''
    replace(p, old, '''            m_RaytracingData->DirectionalLight = {};
            auto* node = Util::Adapter::GetShaderManagerState().shadowSceneNode[0];
            if (node && node->GetRuntimeData().sunLight && node->GetRuntimeData().sunLight->light) {
                auto* light = ce_cast<RE::NiDirectionalLight*>(node->GetRuntimeData().sunLight->light.get());
                if (light) {
                    auto& data = light->GetLightRuntimeData();
                    m_RaytracingData->DirectionalLight.Direction = -Util::Math::Normalize(Util::Math::Float3(light->GetWorldDirection()));
                    m_RaytracingData->DirectionalLight.Color = Util::Math::Float3(data.diffuse);
                    m_RaytracingData->DirectionalLight.Fade = data.fade;
                }
            }''')
    api = cs/"include/CreationEngineRaytracing.h"
    # Preserve the host's GI default; ShadowLab remains selectable as Debug.
    replace(api, '\t\tLOAD_FN(InitializeRenderer);', '''        auto stamp = reinterpret_cast<uint32_t (*)()>(GetProcAddress(handle, "GetShadowLabABI"));
        if (!stamp || stamp() != 0x20261023u) {
            logger::critical("ShadowLab: backend pair mismatch; refusing initialization");
            handle = nullptr;
            return;
        }
\t\tLOAD_FN(InitializeRenderer);''')
    # Missing exports must fail before any caller can use the handle.
    text = api.read_text()
    import re
    names = re.findall(r'^\s+LOAD_FN\((\w+)\);', text, re.M)
    old = '\t\tLOAD_FN(GetFakeDoubledVRAMUsage);'
    replace(api, old, old + '\n        if (' + ' || '.join('!'+n for n in names) + ') handle = nullptr;')
    header = cs/"src/Features/Raytracing.h"
    replace(header, 'winrt::com_ptr<ID3D11ComputeShader> ptCompositeCS = nullptr;',
        'winrt::com_ptr<ID3D11ComputeShader> ptCompositeCS = nullptr;\n\twinrt::com_ptr<ID3D11ComputeShader> shadowLabCompositeCS;')
    source = cs/"src/Features/Raytracing.cpp"
    replace(source, 'void Raytracing::CompileShaders()\n{', '''void Raytracing::CompileShaders()
{
    if (auto raw = reinterpret_cast<ID3D11ComputeShader*>(Util::CompileShader(
        L"Data/ shaders/Raytracing/ShadowLabCompositeCS.hlsl", {}, "cs_5_0")); raw)
        shadowLabCompositeCS.attach(raw);'''.replace('Data/ shaders','Data/Shaders'))
    replace(source, '} else if (pathtracing || debug) {', '''} else if (debug && shadowLabCompositeCS) {
        // Debug writes color only; retain Skyrim's valid depth and motion vectors.
        ID3D11ComputeShader* oldShader = nullptr;
        ID3D11ShaderResourceView* oldSRV = nullptr;
        ID3D11UnorderedAccessView* oldUAV = nullptr;
        context->CSGetShader(&oldShader, nullptr, nullptr);
        context->CSGetShaderResources(0, 1, &oldSRV);
        context->CSGetUnorderedAccessViews(0, 1, &oldUAV);
        context->CSSetShader(shadowLabCompositeCS.get(), nullptr, 0);
        context->CSSetShaderResources(0, 1, &mainTexture[currentFrame]->srv);
        ID3D11UnorderedAccessView* uav = main.UAV;
        context->CSSetUnorderedAccessViews(0, 1, &uav, nullptr);
        D3D11_TEXTURE2D_DESC desc{};
        mainTexture[currentFrame]->resource11->GetDesc(&desc);
        context->Dispatch((desc.Width + 7u) / 8u, (desc.Height + 7u) / 8u, 1);
        uav = nullptr;
        ID3D11ShaderResourceView* srv = nullptr;
        context->CSSetUnorderedAccessViews(0, 1, &uav, nullptr);
        context->CSSetShaderResources(0, 1, &srv);
        context->CSSetShader(oldShader, nullptr, 0);
        context->CSSetShaderResources(0, 1, &oldSRV);
        context->CSSetUnorderedAccessViews(0, 1, &oldUAV, nullptr);
        if (oldShader) oldShader->Release();
        if (oldSRV) oldSRV->Release();
        if (oldUAV) oldUAV->Release();
    } else if (pathtracing) {''')
    for path, prefix in ((cs/"src/DX12Interop.h", ''), (cs/"src/DX12Interop/InteropContext.h", 'interop->')):
        line = f'DX::ThrowIfFailed({prefix}d3d11Context->Signal({prefix}d3d11Fence.get(), ++{prefix}currentFenceValue));'
        replace(path, line, line + f'\n\t\t{prefix}d3d11Context->Flush();')

if __name__ == "__main__":
    import sys
    modify(Path(__file__).resolve().parents[1], Path(sys.argv[1]), Path(sys.argv[2]))
