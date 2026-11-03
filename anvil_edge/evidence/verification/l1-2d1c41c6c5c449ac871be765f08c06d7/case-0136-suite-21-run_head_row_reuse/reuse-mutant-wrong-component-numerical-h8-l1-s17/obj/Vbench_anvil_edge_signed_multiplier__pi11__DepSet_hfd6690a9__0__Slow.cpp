// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench_anvil_edge_signed_multiplier__pi11.h"

VL_ATTR_COLD void Vbench_anvil_edge_signed_multiplier__pi11___ctor_var_reset(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                        Vbench_anvil_edge_signed_multiplier__pi11___ctor_var_reset\n"); );
    // Body
    vlSelf->clk = VL_RAND_RESET_I(1);
    vlSelf->rst_n = VL_RAND_RESET_I(1);
    vlSelf->in_valid = VL_RAND_RESET_I(1);
    vlSelf->in_ready = VL_RAND_RESET_I(1);
    vlSelf->operand_a = VL_RAND_RESET_Q(64);
    vlSelf->operand_b = VL_RAND_RESET_Q(64);
    vlSelf->out_valid = VL_RAND_RESET_I(1);
    vlSelf->out_ready = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->product);
    vlSelf->__PVT__multiplier__DOT__magnitude_a = VL_RAND_RESET_Q(64);
    vlSelf->__PVT__multiplier__DOT__magnitude_b = VL_RAND_RESET_Q(64);
    vlSelf->__PVT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->__PVT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->__PVT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->__PVT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__result);
    for (int __Vi0 = 0; __Vi0 < 5; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 16; ++__Vi1) {
            VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__tree[__Vi0][__Vi1]);
        }
    }
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum);
    VL_RAND_RESET_W(128, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum);
    vlSelf->__Vdly__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(6);
    vlSelf->__Vdly__multiplier__DOT__negative = VL_RAND_RESET_I(1);
}
