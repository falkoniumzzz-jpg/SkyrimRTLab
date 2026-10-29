// SPDX-License-Identifier: GPL-3.0-or-later
#pragma once
#include "RTLabBridge.h"
namespace RTLabHost {
    // All calls run on the CS render thread. No live module reload.
    void Invalidate() noexcept;
    bool Active() noexcept;
    void Observe(std::uint32_t frame, bool interior,
        ID3D11ShaderResourceView* depth, ID3D11ShaderResourceView* normals,
        ID3D11ShaderResourceView* albedo, ID3D11ShaderResourceView* reflectance,
        ID3D11ShaderResourceView* motion, ID3D11ShaderResourceView* color) noexcept;
}
