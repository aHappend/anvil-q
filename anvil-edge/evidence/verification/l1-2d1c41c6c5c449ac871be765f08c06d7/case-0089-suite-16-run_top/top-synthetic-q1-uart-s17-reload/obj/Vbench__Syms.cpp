// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vbench__pch.h"
#include "Vbench.h"
#include "Vbench___024root.h"
#include "Vbench_anvil_edge_special_splitter__pi7.h"
#include "Vbench_anvil_edge_normalizer__M10.h"
#include "Vbench_anvil_q1_rmsnorm__N1_H8_M4.h"
#include "Vbench_anvil_edge_signed_multiplier__pi23.h"

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
    , TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply{this, Verilated::catName(namep, "bench.dut.boot_loader.directory.validator.multiply")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.attention.exponential_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.attention.multiplier")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.gemv.multiplier")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.mlp.gemv.multiplier")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.mlp.silu_product.silu_unit.exp_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.mlp.silu_product.silu_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.norm")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.residual.silu_unit.exp_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier{this, Verilated::catName(namep, "bench.dut.core_adapter.core.decoder.residual.silu_unit.multiplier")}
    , TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm{this, Verilated::catName(namep, "bench.dut.core_adapter.core.final_norm")}
    , TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier{this, Verilated::catName(namep, "bench.dut.memory_subsystem.tensor_mapper.index_multiplier")}
    , TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization{this, Verilated::catName(namep, "bench.dut.tokenizer.tokenizer.normalization")}
    , TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials{this, Verilated::catName(namep, "bench.dut.tokenizer.tokenizer.normalized_specials")}
    , TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization{this, Verilated::catName(namep, "bench.dut.tokenizer.tokenizer.ordinary_text.span.normalization")}
    , TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials{this, Verilated::catName(namep, "bench.dut.tokenizer.tokenizer.raw_specials")}
{
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    TOP.__PVT__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply = &TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm = &TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm;
    TOP.__PVT__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier = &TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier;
    TOP.__PVT__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization = &TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization;
    TOP.__PVT__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials = &TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials;
    TOP.__PVT__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization = &TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization;
    TOP.__PVT__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials = &TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials;
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
    TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply.__Vconfigure(true);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.__Vconfigure(true);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__Vconfigure(true);
    TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__Vconfigure(true);
    TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__Vconfigure(false);
    TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__Vconfigure(false);
    // Setup scopes
    __Vscope_bench.configure(this, name(), "bench", "bench", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__control.configure(this, name(), "bench.control", "control", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__decode_serial__unnamedblk2.configure(this, name(), "bench.decode_serial.unnamedblk2", "unnamedblk2", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__reload_epoch.configure(this, name(), "bench.reload_epoch", "reload_epoch", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__reset_check.configure(this, name(), "bench.reset_check", "reset_check", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__unnamedblk4.configure(this, name(), "bench.unnamedblk4", "unnamedblk4", -9, VerilatedScope::SCOPE_OTHER);
    __Vscope_bench__verification_file0.configure(this, name(), "bench.verification_file0", "verification_file0", -9, VerilatedScope::SCOPE_OTHER);
}
