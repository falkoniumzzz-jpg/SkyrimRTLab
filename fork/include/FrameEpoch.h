// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include <cstdint>
namespace rtlab {
// A discontinuity signal, not proof of temporal validity (camera cuts still need detection).
class FrameEpoch {
public:
    void Invalidate() noexcept { dirty = true; }
    bool Observe(std::uint32_t frame) noexcept {
        const bool reset = dirty || !seen || (frame != last && frame != last + std::uint32_t{1});
        if (reset) ++epoch;
        dirty = false;
        seen = true;
        last = frame;
        return reset;
    }
    std::uint64_t Value() const noexcept { return epoch; }
private:
    std::uint64_t epoch = 0;
    std::uint32_t last = 0;
    bool seen = false;
    bool dirty = true;
};
}
