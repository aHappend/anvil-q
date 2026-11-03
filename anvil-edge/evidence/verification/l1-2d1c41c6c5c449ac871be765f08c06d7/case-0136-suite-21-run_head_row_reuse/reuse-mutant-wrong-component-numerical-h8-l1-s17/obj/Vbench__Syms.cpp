// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vbench__pch.h"
#include "Vbench.h"
#include "Vbench___024root.h"
#include "Vbench_anvil_q1_rmsnorm__N1_H8_M4.h"
#include "Vbench_anvil_edge_signed_multiplier__pi11.h"

// FUNCTIONS
Vbench__Syms::~Vbench__Syms()
{
}

Vbench__Syms::Vbench__Syms(VerilatedContext* contextp, const char* namep, Vbench* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup module instances
    , TOP{this, namep}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.decoder.attention.exponential_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.decoder.attention.multiplier")}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.decoder.gemv.multiplier")}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.decoder.mlp.gemv.multiplier")}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.decoder.mlp.silu_product.silu_unit.exp_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.decoder.mlp.silu_product.silu_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__norm{this, Verilated::catName(namep, "bench.dut.decoder.norm")}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.decoder.residual.silu_unit.exp_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.decoder.residual.silu_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__final_norm{this, Verilated::catName(namep, "bench.dut.final_norm")}
{
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier = &TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier = &TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier = &TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__norm = &TOP__bench__DOT__dut__DOT__decoder__DOT__norm;
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__final_norm = &TOP__bench__DOT__dut__DOT__final_norm;
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.__Vconfigure(true);
    TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__decoder__DOT__norm.__Vconfigure(true);
    TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__final_norm.__Vconfigure(false);
    // Setup scopes
    __Vscope_bench.configure(this, name(), "bench", "bench", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__reset_check.configure(this, name(), "bench.reset_check", "reset_check", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__verification_file0.configure(this, name(), "bench.verification_file0", "verification_file0", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__verification_file1.configure(this, name(), "bench.verification_file1", "verification_file1", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__verification_file2.configure(this, name(), "bench.verification_file2", "verification_file2", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__verification_file3.configure(this, name(), "bench.verification_file3", "verification_file3", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__verification_file4.configure(this, name(), "bench.verification_file4", "verification_file4", -9, VerilatedScope::SCOPE_OTHER);
}
