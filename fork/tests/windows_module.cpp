#define NOMINMAX
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d11.h>
#include <wrl/client.h>
#include <filesystem>
#include <iostream>
#include "RTLabBridge.h"
using Microsoft::WRL::ComPtr;
#define CHECK(x) do { if (!(x)) { std::cerr << "FAILED: " #x << '\n'; return 1; } } while(false)
unsigned logs = 0;
void Log(const char* text) noexcept { if (text) ++logs; }
int main(int argc, char** argv) {
    CHECK(argc == 2);
    const auto path = std::filesystem::absolute(argv[1]);
    HMODULE library = LoadLibraryExW(path.c_str(), nullptr, LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_SYSTEM32);
    CHECK(library);
    const auto get = reinterpret_cast<rtlab::GetModule>(GetProcAddress(library, "RTLab_GetModule"));
    CHECK(get); CHECK(get(0) == nullptr);
    const auto api = get(rtlab::AbiVersion);
    CHECK(rtlab::Compatible(api)); CHECK(!api->initialize(nullptr));
    ComPtr<ID3D11Device> device;
    ComPtr<ID3D11DeviceContext> context;
    CHECK(SUCCEEDED(D3D11CreateDevice(nullptr, D3D_DRIVER_TYPE_WARP, nullptr, 0, nullptr, 0,
        D3D11_SDK_VERSION, &device, nullptr, &context)));
    rtlab::Host host{sizeof(host), rtlab::AbiVersion, rtlab::ObserveOnly, device.Get(), Log};
    CHECK(api->initialize(&host)); CHECK(logs > 0);
    CHECK(!api->observe(nullptr));
    D3D11_TEXTURE2D_DESC desc{};
    desc.Width = desc.Height = 16; desc.MipLevels = desc.ArraySize = desc.SampleDesc.Count = 1;
    desc.Format = DXGI_FORMAT_R16G16B16A16_FLOAT; desc.BindFlags = D3D11_BIND_SHADER_RESOURCE;
    ComPtr<ID3D11Texture2D> texture;
    ComPtr<ID3D11ShaderResourceView> srv;
    CHECK(SUCCEEDED(device->CreateTexture2D(&desc, nullptr, &texture)));
    CHECK(SUCCEEDED(device->CreateShaderResourceView(texture.Get(), nullptr, &srv)));
    rtlab::Frame frame{sizeof(frame), rtlab::HistoryDiscontinuity, 1, 1, {}};
    for (auto& view : frame.resources) view = srv.Get();
    const auto before = logs;
    CHECK(api->observe(&frame)); CHECK(logs == before + 7);
    frame.size--; CHECK(!api->observe(&frame)); frame.size++;
    frame.epoch++; frame.resources[0] = nullptr;
    CHECK(api->observe(&frame)); // Missing data is logged, never fabricated.
    api->shutdown(); CHECK(!api->observe(&frame));
    CHECK(api->initialize(&host)); api->shutdown();
    FreeLibrary(library);
    std::cout << "PASS: Windows DLL ABI, WARP resource audit and lifecycle. No hardware DXR execution tested.\n";
}
