// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design internal header
// See Vbench.h for the primary calling header

#ifndef VERILATED_VBENCH_ANVIL_EDGE_SIGNED_MULTIPLIER__PI23_H_
#define VERILATED_VBENCH_ANVIL_EDGE_SIGNED_MULTIPLIER__PI23_H_  // guard

#include "verilated.h"
#include "verilated_timing.h"


class Vbench__Syms;

class alignas(VL_CACHE_LINE_BYTES) Vbench_anvil_edge_signed_multiplier__pi23 final : public VerilatedModule {
  public:

    // DESIGN SPECIFIC STATE
    VL_IN8(clk,0,0);
    VL_IN8(rst_n,0,0);
    VL_IN8(in_valid,0,0);
    VL_OUT8(in_ready,0,0);
    VL_OUT8(out_valid,0,0);
    VL_IN8(out_ready,0,0);
    CData/*0:0*/ __PVT__multiplier__DOT__negative;
    CData/*0:0*/ __PVT__multiplier__DOT__busy;
    CData/*0:0*/ __PVT__multiplier__DOT__valid_result;
    CData/*5:0*/ __PVT__multiplier__DOT__valid_pipe;
    CData/*5:0*/ __Vdly__multiplier__DOT__valid_pipe;
    CData/*0:0*/ __Vdly__multiplier__DOT__negative;
    VL_OUTW(product,127,0,4);
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__result;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum;
    VlWide<4>/*127:0*/ __PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum;
    VL_IN64(operand_a,63,0);
    VL_IN64(operand_b,63,0);
    QData/*63:0*/ __PVT__multiplier__DOT__magnitude_a;
    QData/*63:0*/ __PVT__multiplier__DOT__magnitude_b;
    VlUnpacked<VlUnpacked<VlWide<4>/*127:0*/, 16>, 5> __PVT__multiplier__DOT__tree;

    // INTERNAL VARIABLES
    Vbench__Syms* const vlSymsp;

    // CONSTRUCTORS
    Vbench_anvil_edge_signed_multiplier__pi23(Vbench__Syms* symsp, const char* v__name);
    ~Vbench_anvil_edge_signed_multiplier__pi23();
    VL_UNCOPYABLE(Vbench_anvil_edge_signed_multiplier__pi23);

    // INTERNAL METHODS
    void __Vconfigure(bool first);
};


#endif  // guard
