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
#include "Vbench_anvil_edge_special_splitter__pi7.h"
#include "Vbench_anvil_edge_normalizer__M10.h"
#include "Vbench_anvil_q1_rmsnorm__N1_H8_M4.h"
#include "Vbench_anvil_edge_signed_multiplier__pi23.h"

// SYMS CLASS (contains all model state)
class alignas(VL_CACHE_LINE_BYTES)Vbench__Syms final : public VerilatedSyms {
  public:
    // INTERNAL STATE
    Vbench* const __Vm_modelp;
    VlDeleter __Vm_deleter;
    bool __Vm_didInit = false;

    // MODULE INSTANCE STATE
    Vbench___024root               TOP;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier;
    Vbench_anvil_q1_rmsnorm__N1_H8_M4 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier;
    Vbench_anvil_q1_rmsnorm__N1_H8_M4 TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm;
    Vbench_anvil_edge_signed_multiplier__pi23 TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier;
    Vbench_anvil_edge_normalizer__M10 TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization;
    Vbench_anvil_edge_special_splitter__pi7 TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials;
    Vbench_anvil_edge_normalizer__M10 TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization;
    Vbench_anvil_edge_special_splitter__pi7 TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials;

    // SCOPE NAMES
    VerilatedScope __Vscope_bench;
    VerilatedScope __Vscope_bench__control;
    VerilatedScope __Vscope_bench__decode_serial__unnamedblk2;
    VerilatedScope __Vscope_bench__reload_epoch;
    VerilatedScope __Vscope_bench__reset_check;
    VerilatedScope __Vscope_bench__unnamedblk4;
    VerilatedScope __Vscope_bench__verification_file0;

    // CONSTRUCTORS
    Vbench__Syms(VerilatedContext* contextp, const char* namep, Vbench* modelp);
    ~Vbench__Syms();

    // METHODS
    const char* name() { return TOP.name(); }
};

#endif  // guard
