#include "RTLabBridge.h"
#include "FrameEpoch.h"
#include <cstdlib>
#include <iostream>
#define CHECK(x) do { if (!(x)) { std::cerr << "FAILED: " #x << '\n'; return EXIT_FAILURE; } } while (false)
std::uint32_t Init(const rtlab::Host*) noexcept { return 1; }
std::uint32_t Frame(const rtlab::Frame*) noexcept { return 1; }
void Stop() noexcept {}
int main() {
    rtlab::Module m{sizeof(m), rtlab::AbiVersion, rtlab::ObserveOnly, Init, Frame, Stop};
    CHECK(rtlab::Compatible(&m));
    CHECK(!rtlab::Compatible(nullptr));
    m.size--; CHECK(!rtlab::Compatible(&m)); m.size++;
    m.abi++; CHECK(!rtlab::Compatible(&m)); m.abi--;
    m.capabilities |= 2; CHECK(!rtlab::Compatible(&m)); m.capabilities = rtlab::ObserveOnly;
    m.observe = nullptr; CHECK(!rtlab::Compatible(&m));
    rtlab::FrameEpoch e;
    CHECK(e.Observe(1)); CHECK(e.Value() == 1);
    CHECK(!e.Observe(2)); CHECK(!e.Observe(2));
    CHECK(e.Observe(9)); CHECK(e.Value() == 2);
    e.Invalidate(); e.Invalidate(); CHECK(e.Observe(10)); CHECK(e.Value() == 3);
    CHECK(!e.Observe(11));
    CHECK(e.Observe(0xffffffffu)); CHECK(!e.Observe(0));
    std::cout << "PASS: ABI rejection, discontinuities, duplicate frames, uint32 wrap\n";
}
