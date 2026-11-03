#include "Vbench.h"
#include "verilated.h"
#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <memory>

int main(int argc, char** argv) {
    auto context = std::make_unique<VerilatedContext>();
    context->commandArgs(argc, argv);
    auto bench = std::make_unique<Vbench>(context.get());
    bench->clk = 0;
    bench->eval();
    uint64_t edge = 5000;  // 1 ns / 1 ps timescale: first rising edge at 5 ns.
    uint64_t edges = 0;
    while (!context->gotFinish()) {
        uint64_t next = edge;
        if (bench->eventsPending()) next = std::min(next, bench->nextTimeSlot());
        if (next <= context->time()) {
            std::fprintf(stderr, "EXPLICIT_CLOCK_NONPROGRESS time=%llu\n",
                         static_cast<unsigned long long>(context->time()));
            return 2;
        }
        context->time(next);
        if (next == edge) {
            bench->clk = !bench->clk;
            edge += 5000;
            ++edges;
        }
        bench->eval();
    }
    bench->final();
    std::printf("EXPLICIT_CLOCK edges=%llu time_ps=%llu\n",
                static_cast<unsigned long long>(edges),
                static_cast<unsigned long long>(context->time()));
    return 0;
}
