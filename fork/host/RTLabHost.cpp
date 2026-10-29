// SPDX-License-Identifier: GPL-3.0-or-later
#include "RTLabHost.h"
#include "FrameEpoch.h"
#include "Globals.h"
#include <chrono>
#include <filesystem>

namespace {
    HMODULE library = nullptr;
    const rtlab::Module* module = nullptr;
    rtlab::FrameEpoch timeline;
    bool attempted = false;
    double totalMicros = 0;
    double maxMicros = 0;
    std::uint32_t observations = 0;

    void Log(const char* message) noexcept {
        try { logger::info("[RTLab] {}", message ? message : "(null)"); } catch (...) {}
    }
    void Stop() noexcept {
        if (module) module->shutdown();
        module = nullptr;
        // Retain the DLL until process exit; no callbacks into unloaded code.
    }
    void Load() {
        attempted = true;
        const auto folder = std::filesystem::absolute("Data/SKSE/Plugins/RTLab");
        if (GetPrivateProfileIntW(L"Diagnostics", L"Enabled", 0, (folder / L"RTLab.ini").c_str()) != 1)
            return;
        if (GetModuleHandleW(L"CreationEngineRaytracing.dll")) {
            Log("Legacy CER detected; refusing diagnostic bridge. Use a separate MO2 profile.");
            return;
        }
        if (REL::Module::IsVR()) {
            Log("VR is not supported by this development bridge.");
            return;
        }
        library = LoadLibraryExW((folder / L"RTLab.Diagnostics.dll").c_str(), nullptr,
            LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
        if (!library) { Log("Diagnostics DLL could not be loaded; continuing with CS."); return; }
        const auto get = reinterpret_cast<rtlab::GetModule>(GetProcAddress(library, "RTLab_GetModule"));
        const auto candidate = get ? get(rtlab::AbiVersion) : nullptr;
        if (!rtlab::Compatible(candidate)) { Log("Rejected incompatible module ABI/capabilities."); return; }
        const rtlab::Host host{ sizeof(rtlab::Host), rtlab::AbiVersion, rtlab::ObserveOnly, globals::d3d::device, Log };
        if (!candidate->initialize(&host)) {
            candidate->shutdown();
            Log("Module initialization failed; continuing with CS.");
            return;
        }
        module = candidate;
        Log("CS 1.9.0 RTLab host active: diagnostic observer only; no RT rendering.");
    }
}
namespace RTLabHost {
    void Invalidate() noexcept { timeline.Invalidate(); }
    bool Active() noexcept {
        try {
            if (!attempted) Load();
            return module != nullptr;
        } catch (...) { Stop(); Log("Host initialization failed; bridge disabled."); return false; }
    }
    void Observe(std::uint32_t frame, bool interior,
        ID3D11ShaderResourceView* depth, ID3D11ShaderResourceView* normals,
        ID3D11ShaderResourceView* albedo, ID3D11ShaderResourceView* reflectance,
        ID3D11ShaderResourceView* motion, ID3D11ShaderResourceView* color) noexcept {
        if (!module) return;
        const bool reset = timeline.Observe(frame);
        const rtlab::Frame packet{ sizeof(rtlab::Frame),
            (interior ? rtlab::Interior : 0u) | (reset ? rtlab::HistoryDiscontinuity : 0u),
            frame, timeline.Value(), { depth, normals, albedo, reflectance, motion, color } };
        const auto start = std::chrono::steady_clock::now();
        if (!module->observe(&packet)) { Stop(); Log("Invalid frame/device; diagnostic module disabled."); return; }
        const double micros = std::chrono::duration<double, std::micro>(std::chrono::steady_clock::now() - start).count();
        totalMicros += micros;
        maxMicros = (std::max)(maxMicros, micros);
        if (++observations == 600) {
            try { logger::info("[RTLab] observer CPU mean={} us max={} us (not GPU timings)", totalMicros / observations, maxMicros); } catch (...) {}
            observations = 0;
            totalMicros = maxMicros = 0;
        }
    }
}
