// Diagnostic reduction only. This is not firmware or a replacement endpoint.
#include "bounded.hpp"
#include <optional>

struct MiniGate { cu66_port::String failure; };
struct MiniEndpoint {
    cu66_port::Arena arena;
    std::optional<MiniGate> gate;
    explicit MiniEndpoint(size_t budget) : arena(budget) {
        cu66_port::Scope scope(arena);
        gate.emplace();
    }
    ~MiniEndpoint() {
        cu66_port::Scope scope(arena);
        gate.reset();
    }
};

extern "C" void* minimal_create(size_t budget) { return new MiniEndpoint(budget); }
extern "C" void minimal_destroy(void* endpoint) { delete static_cast<MiniEndpoint*>(endpoint); }
extern "C" void minimal_set_failure(void* endpoint, const char* text) {
    auto& e = *static_cast<MiniEndpoint*>(endpoint);
    cu66_port::Scope scope(e.arena);
    e.gate->failure = text;
}
