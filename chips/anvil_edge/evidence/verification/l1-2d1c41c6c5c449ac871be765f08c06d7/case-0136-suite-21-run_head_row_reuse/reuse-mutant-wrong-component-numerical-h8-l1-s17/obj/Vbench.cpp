// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vbench__pch.h"

//============================================================
// Constructors

Vbench::Vbench(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vbench__Syms(contextp(), _vcname__, this)}
    , __PVT__bench__DOT__dut__DOT__final_norm{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__final_norm}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__norm{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__norm}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier}
    , __PVT__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier{vlSymsp->TOP.__PVT__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vbench::Vbench(const char* _vcname__)
    : Vbench(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vbench::~Vbench() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vbench___024root___eval_debug_assertions(Vbench___024root* vlSelf);
#endif  // VL_DEBUG
void Vbench___024root___eval_static(Vbench___024root* vlSelf);
void Vbench___024root___eval_initial(Vbench___024root* vlSelf);
void Vbench___024root___eval_settle(Vbench___024root* vlSelf);
void Vbench___024root___eval(Vbench___024root* vlSelf);

void Vbench::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vbench::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vbench___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        vlSymsp->__Vm_didInit = true;
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vbench___024root___eval_static(&(vlSymsp->TOP));
        Vbench___024root___eval_initial(&(vlSymsp->TOP));
        Vbench___024root___eval_settle(&(vlSymsp->TOP));
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vbench___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vbench::eventsPending() { return !vlSymsp->TOP.__VdlySched.empty(); }

uint64_t Vbench::nextTimeSlot() { return vlSymsp->TOP.__VdlySched.nextTimeSlot(); }

//============================================================
// Utilities

const char* Vbench::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vbench___024root___eval_final(Vbench___024root* vlSelf);

VL_ATTR_COLD void Vbench::final() {
    Vbench___024root___eval_final(&(vlSymsp->TOP));
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vbench::hierName() const { return vlSymsp->name(); }
const char* Vbench::modelName() const { return "Vbench"; }
unsigned Vbench::threads() const { return 1; }
void Vbench::prepareClone() const { contextp()->prepareClone(); }
void Vbench::atClone() const {
    contextp()->threadPoolpOnClone();
}

//============================================================
// Trace configuration

VL_ATTR_COLD void Vbench::trace(VerilatedVcdC* tfp, int levels, int options) {
    vl_fatal(__FILE__, __LINE__, __FILE__,"'Vbench::trace()' called on model that was Verilated without --trace option");
}
