// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
#include <type_traits>

struct ID3D11Device;
struct ID3D11ShaderResourceView;

namespace rtlab {
// Private experimental ABI. Changes to any layout or semantics require a new version.
inline constexpr std::uint32_t AbiVersion = 0x00010000;
inline constexpr std::uint64_t ObserveOnly = 1;
inline constexpr std::uint32_t ResourceCount = 6;
enum ResourceSlot : std::uint32_t { Depth, NormalRoughness, Albedo, Reflectance, Motion, Color };
enum FrameFlags : std::uint32_t { Interior = 1, HistoryDiscontinuity = 2 };
using Log = void (*)(const char*) noexcept;
struct Host {
    std::uint32_t size;
    std::uint32_t abi;
    std::uint64_t capabilities;
    ID3D11Device* device; // Borrowed during Initialize only; AddRef if retained.
    Log log;            // UTF-8, copied synchronously. Valid until process exit.
};
struct Frame {
    std::uint32_t size;
    std::uint32_t flags;
    std::uint64_t frame;
    std::uint64_t epoch;
    // Native CS 1.9.0 views AFTER deferred composite, before post-deferred effects.
    // Borrowed until Observe returns. No GPU submissions, retention, state changes
    // or cross-thread access permitted by ObserveOnly. These are NOT NRD inputs.
    ID3D11ShaderResourceView* resources[ResourceCount];
};
struct Module {
    std::uint32_t size;
    std::uint32_t abi;
    std::uint64_t capabilities;
    std::uint32_t (*initialize)(const Host*) noexcept;
    std::uint32_t (*observe)(const Frame*) noexcept;
    void (*shutdown)() noexcept;
};
using GetModule = const Module* (*)(std::uint32_t) noexcept;
inline bool Compatible(const Module* m) noexcept {
    return m && m->size == sizeof(Module) && m->abi == AbiVersion &&
        m->capabilities == ObserveOnly && m->initialize && m->observe && m->shutdown;
}
static_assert(std::is_standard_layout_v<Host> && std::is_standard_layout_v<Frame> &&
              std::is_standard_layout_v<Module>);
static_assert(sizeof(void*) == 8, "RTLab requires a 64-bit process");
static_assert(sizeof(Host) == 32 && sizeof(Frame) == 72 && sizeof(Module) == 40);
} // namespace rtlab
