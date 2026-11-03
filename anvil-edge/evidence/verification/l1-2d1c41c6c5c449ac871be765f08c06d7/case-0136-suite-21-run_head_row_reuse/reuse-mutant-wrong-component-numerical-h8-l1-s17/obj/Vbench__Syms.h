// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table internal header
//
// Internal details; most calling programs do not need this header,
// unless using verilator public meta comments.

#ifndef VERILATED_VBENCH__SYMS_H_
#define VERILATED_VBENCH__SYMS_H_  // guard

#include "verilated.h"

// INCLUDE MODEL CLASS

#include "Vbench.h"

// INCLUDE MODULE CLASSES
#include "Vbench___024root.h"
#include "Vbench_anvil_q1_rmsnorm__N1_H8_M4.h"
#include "Vbench_anvil_edge_signed_multiplier__pi11.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES)Vbench__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vbench* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vbench___024root               TOP;
    Vbench_anvil_edge_signed_multiplier__pi11 TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11 TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11 TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11 TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11 TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11 TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier;
    Vbench_anvil_q1_rmsnorm__N1_H8_M4 TOP__bench__DOT__dut__DOT__decoder__DOT__norm;
    Vbench_anvil_edge_signed_multiplier__pi11 TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi11 TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier;
    Vbench_anvil_q1_rmsnorm__N1_H8_M4 TOP__bench__DOT__dut__DOT__final_norm;

    // SCOPE NAMES
    VerilatedScope __Vscope_bench;
    VerilatedScope __Vscope_bench__reset_check;
    VerilatedScope __Vscope_bench__verification_file0;
    VerilatedScope __Vscope_bench__verification_file1;
    VerilatedScope __Vscope_bench__verification_file2;
    VerilatedScope __Vscope_bench__verification_file3;
    VerilatedScope __Vscope_bench__verification_file4;

    // CONSTRUCTORS
    Vbench__Syms(VerilatedContext* contextp, const char* namep, Vbench* modelp);
    ~Vbench__Syms();

    // METHODS
    const char* name() { return TOP.name(); }
};

#endif  // guard
