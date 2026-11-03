// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench___024root.h"

void Vbench___024root___ctor_var_reset(Vbench___024root* vlSelf);

Vbench___024root::Vbench___024root(Vbench__Syms* symsp, const char* v__name)
    : VerilatedModule{v__name}
    , __VdlySched{*symsp->_vm_contextp__}
    , vlSymsp{symsp}
 {
    // Reset structure values
    Vbench___024root___ctor_var_reset(this);
}

void Vbench___024root::__Vconfigure(bool first) {
    if (false && first) {}  // Prevent unused
}

Vbench___024root::~Vbench___024root() {
}
