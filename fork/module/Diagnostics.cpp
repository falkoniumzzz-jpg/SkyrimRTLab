// SPDX-License-Identifier: GPL-3.0-or-later
#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d11_4.h>
#include <d3d12.h>
#include <dxgi1_4.h>
#include <wrl/client.h>
#include <cstdio>
#include <limits>
#include "RTLabBridge.h"
using Microsoft::WRL::ComPtr;
namespace {
    rtlab::Log logMessage = nullptr;
    std::uint64_t lastEpoch = (std::numeric_limits<std::uint64_t>::max)();
    std::uint64_t observations = 0;
    constexpr const char* names[] = { "depth", "normalRoughness", "albedo", "reflectance", "motion", "color" };
    ComPtr<ID3D11Device> device;

    void Shutdown() noexcept {
        device.Reset();
        logMessage = nullptr;
        lastEpoch = (std::numeric_limits<std::uint64_t>::max)();
        observations = 0;
    }
    std::uint32_t Initialize(const rtlab::Host* host) noexcept {
        Shutdown();
        if (!host || host->size != sizeof(*host) || host->abi != rtlab::AbiVersion ||
            host->capabilities != rtlab::ObserveOnly || !host->device || !host->log) return 0;
        logMessage = host->log;
        device = host->device;
        // Use the adapter that actually renders Skyrim, never the default adapter.
        ComPtr<IDXGIDevice> dxgiDevice;
        ComPtr<IDXGIAdapter> adapter;
        ComPtr<ID3D12Device> dx12;
        HRESULT hr = device.As(&dxgiDevice);
        if (SUCCEEDED(hr)) hr = dxgiDevice->GetAdapter(&adapter);
        if (SUCCEEDED(hr)) hr = D3D12CreateDevice(adapter.Get(), D3D_FEATURE_LEVEL_12_0, IID_PPV_ARGS(&dx12));
        D3D12_FEATURE_DATA_D3D12_OPTIONS5 options{};
        if (SUCCEEDED(hr)) hr = dx12->CheckFeatureSupport(D3D12_FEATURE_D3D12_OPTIONS5, &options, sizeof(options));
        ComPtr<ID3D11Device5> device5;
        const bool fences = SUCCEEDED(device.As(&device5));
        char text[256];
        std::snprintf(text, sizeof(text), "Capability probe: HRESULT=0x%08lx DXR tier=%u D3D11Device5=%u. No DXR dispatch or sharing tested.",
            static_cast<unsigned long>(hr), static_cast<unsigned>(options.RaytracingTier), fences ? 1u : 0u);
        logMessage(text);
        // Unsupported DXR is a useful diagnostic outcome, not a reason to lose the audit.
        return 1;
    }
    std::uint32_t Observe(const rtlab::Frame* frame) noexcept {
        if (!frame || frame->size != sizeof(*frame) || !device) return 0;
        if (FAILED(device->GetDeviceRemovedReason())) return 0;
        if (frame->epoch == lastEpoch && ++observations % 600 != 0) return 1;
        lastEpoch = frame->epoch;
        char text[256];
        std::snprintf(text, sizeof(text), "Frame audit: frame=%llu epoch=%llu flags=%u; native CS buffers, not converted NRD inputs.",
            static_cast<unsigned long long>(frame->frame), static_cast<unsigned long long>(frame->epoch), frame->flags);
        logMessage(text);
        for (std::uint32_t i = 0; i < rtlab::ResourceCount; ++i) {
            const auto srv = frame->resources[i];
            if (!srv) {
                std::snprintf(text, sizeof(text), "%s: missing SRV", names[i]);
                logMessage(text);
                continue;
            }
            D3D11_SHADER_RESOURCE_VIEW_DESC view{};
            srv->GetDesc(&view);
            ComPtr<ID3D11Resource> resource;
            ComPtr<ID3D11Texture2D> texture;
            srv->GetResource(&resource);
            if (FAILED(resource.As(&texture))) { logMessage("Non-Texture2D resource: unsupported by audit"); return 0; }
            D3D11_TEXTURE2D_DESC desc{};
            texture->GetDesc(&desc);
            std::snprintf(text, sizeof(text), "%s: allocation=%ux%u resourceFormat=%u viewFormat=%u viewDimension=%u samples=%u misc=0x%x",
                names[i], desc.Width, desc.Height, static_cast<unsigned>(desc.Format), static_cast<unsigned>(view.Format),
                static_cast<unsigned>(view.ViewDimension), desc.SampleDesc.Count, desc.MiscFlags);
            logMessage(text);
        }
        return 1;
    }
    const rtlab::Module api{ sizeof(rtlab::Module), rtlab::AbiVersion, rtlab::ObserveOnly, Initialize, Observe, Shutdown };
}
extern "C" __declspec(dllexport) const rtlab::Module* RTLab_GetModule(std::uint32_t abi) noexcept {
    return abi == rtlab::AbiVersion ? &api : nullptr;
}
