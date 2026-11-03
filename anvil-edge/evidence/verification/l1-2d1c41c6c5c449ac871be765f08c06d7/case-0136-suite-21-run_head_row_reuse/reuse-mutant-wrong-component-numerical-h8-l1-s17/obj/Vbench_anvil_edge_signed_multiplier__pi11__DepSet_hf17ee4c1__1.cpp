// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench_anvil_edge_signed_multiplier__pi11.h"

VL_INLINE_OPT void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0\n"); );
    // Init
    VlWide<4>/*127:0*/ __Vtemp_1;
    VlWide<4>/*127:0*/ __Vtemp_2;
    VlWide<4>/*127:0*/ __Vtemp_3;
    VlWide<4>/*127:0*/ __Vtemp_4;
    VlWide<4>/*127:0*/ __Vtemp_5;
    VlWide<4>/*127:0*/ __Vtemp_6;
    VlWide<4>/*127:0*/ __Vtemp_7;
    VlWide<4>/*127:0*/ __Vtemp_8;
    VlWide<4>/*127:0*/ __Vtemp_9;
    VlWide<4>/*127:0*/ __Vtemp_10;
    VlWide<4>/*127:0*/ __Vtemp_11;
    VlWide<4>/*127:0*/ __Vtemp_12;
    VlWide<4>/*127:0*/ __Vtemp_13;
    VlWide<4>/*127:0*/ __Vtemp_14;
    VlWide<4>/*127:0*/ __Vtemp_15;
    // Body
    vlSelf->__Vdly__multiplier__DOT__valid_pipe = vlSelf->__PVT__multiplier__DOT__valid_pipe;
    vlSelf->__Vdly__multiplier__DOT__negative = vlSelf->__PVT__multiplier__DOT__negative;
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        if (vlSelf->__PVT__multiplier__DOT__busy) {
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [3U][0U], vlSelf->__PVT__multiplier__DOT__tree
                     [3U][1U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [2U][2U], vlSelf->__PVT__multiplier__DOT__tree
                     [2U][3U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [2U][0U], vlSelf->__PVT__multiplier__DOT__tree
                     [2U][1U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [1U][6U], vlSelf->__PVT__multiplier__DOT__tree
                     [1U][7U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [1U][4U], vlSelf->__PVT__multiplier__DOT__tree
                     [1U][5U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [1U][2U], vlSelf->__PVT__multiplier__DOT__tree
                     [1U][3U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [1U][0U], vlSelf->__PVT__multiplier__DOT__tree
                     [1U][1U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [0U][0xeU], vlSelf->__PVT__multiplier__DOT__tree
                     [0U][0xfU]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [0U][0xcU], vlSelf->__PVT__multiplier__DOT__tree
                     [0U][0xdU]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [0U][0xaU], vlSelf->__PVT__multiplier__DOT__tree
                     [0U][0xbU]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [0U][8U], vlSelf->__PVT__multiplier__DOT__tree
                     [0U][9U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [0U][6U], vlSelf->__PVT__multiplier__DOT__tree
                     [0U][7U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [0U][4U], vlSelf->__PVT__multiplier__DOT__tree
                     [0U][5U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [0U][2U], vlSelf->__PVT__multiplier__DOT__tree
                     [0U][3U]);
            VL_ADD_W(4, vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__tree
                     [0U][0U], vlSelf->__PVT__multiplier__DOT__tree
                     [0U][1U]);
            __Vtemp_1[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x30U))) 
                             * (0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                   >> 0x30U))));
            __Vtemp_1[1U] = 0U;
            __Vtemp_1[2U] = 0U;
            __Vtemp_1[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_1, 0x60U);
            __Vtemp_2[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x30U))) 
                             * (0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                   >> 0x20U))));
            __Vtemp_2[1U] = 0U;
            __Vtemp_2[2U] = 0U;
            __Vtemp_2[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_2, 0x50U);
            __Vtemp_3[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x30U))) 
                             * (0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                   >> 0x10U))));
            __Vtemp_3[1U] = 0U;
            __Vtemp_3[2U] = 0U;
            __Vtemp_3[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_3, 0x40U);
            __Vtemp_4[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x30U))) 
                             * (0xffffU & (IData)(vlSelf->__PVT__multiplier__DOT__magnitude_b)));
            __Vtemp_4[1U] = 0U;
            __Vtemp_4[2U] = 0U;
            __Vtemp_4[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_4, 0x30U);
            __Vtemp_5[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x20U))) 
                             * (0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                   >> 0x30U))));
            __Vtemp_5[1U] = 0U;
            __Vtemp_5[2U] = 0U;
            __Vtemp_5[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_5, 0x50U);
            __Vtemp_6[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x20U))) 
                             * (0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                   >> 0x20U))));
            __Vtemp_6[1U] = 0U;
            __Vtemp_6[2U] = 0U;
            __Vtemp_6[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_6, 0x40U);
            __Vtemp_7[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x20U))) 
                             * (0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                   >> 0x10U))));
            __Vtemp_7[1U] = 0U;
            __Vtemp_7[2U] = 0U;
            __Vtemp_7[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_7, 0x30U);
            __Vtemp_8[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x20U))) 
                             * (0xffffU & (IData)(vlSelf->__PVT__multiplier__DOT__magnitude_b)));
            __Vtemp_8[1U] = 0U;
            __Vtemp_8[2U] = 0U;
            __Vtemp_8[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_8, 0x20U);
            __Vtemp_9[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                 >> 0x10U))) 
                             * (0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                   >> 0x30U))));
            __Vtemp_9[1U] = 0U;
            __Vtemp_9[2U] = 0U;
            __Vtemp_9[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_9, 0x40U);
            __Vtemp_10[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                  >> 0x10U))) 
                              * (0xffffU & (IData)(
                                                   (vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                    >> 0x20U))));
            __Vtemp_10[1U] = 0U;
            __Vtemp_10[2U] = 0U;
            __Vtemp_10[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_10, 0x30U);
            __Vtemp_11[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                  >> 0x10U))) 
                              * (0xffffU & (IData)(
                                                   (vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                    >> 0x10U))));
            __Vtemp_11[1U] = 0U;
            __Vtemp_11[2U] = 0U;
            __Vtemp_11[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_11, 0x20U);
            __Vtemp_12[0U] = ((0xffffU & (IData)((vlSelf->__PVT__multiplier__DOT__magnitude_a 
                                                  >> 0x10U))) 
                              * (0xffffU & (IData)(vlSelf->__PVT__multiplier__DOT__magnitude_b)));
            __Vtemp_12[1U] = 0U;
            __Vtemp_12[2U] = 0U;
            __Vtemp_12[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_12, 0x10U);
            __Vtemp_13[0U] = ((0xffffU & (IData)(vlSelf->__PVT__multiplier__DOT__magnitude_a)) 
                              * (0xffffU & (IData)(
                                                   (vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                    >> 0x30U))));
            __Vtemp_13[1U] = 0U;
            __Vtemp_13[2U] = 0U;
            __Vtemp_13[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_13, 0x30U);
            __Vtemp_14[0U] = ((0xffffU & (IData)(vlSelf->__PVT__multiplier__DOT__magnitude_a)) 
                              * (0xffffU & (IData)(
                                                   (vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                    >> 0x20U))));
            __Vtemp_14[1U] = 0U;
            __Vtemp_14[2U] = 0U;
            __Vtemp_14[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_14, 0x20U);
            __Vtemp_15[0U] = ((0xffffU & (IData)(vlSelf->__PVT__multiplier__DOT__magnitude_a)) 
                              * (0xffffU & (IData)(
                                                   (vlSelf->__PVT__multiplier__DOT__magnitude_b 
                                                    >> 0x10U))));
            __Vtemp_15[1U] = 0U;
            __Vtemp_15[2U] = 0U;
            __Vtemp_15[3U] = 0U;
            VL_SHIFTL_WWI(128,128,32, vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_15, 0x10U);
            vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
                = ((0xffffU & (IData)(vlSelf->__PVT__multiplier__DOT__magnitude_a)) 
                   * (0xffffU & (IData)(vlSelf->__PVT__multiplier__DOT__magnitude_b)));
            vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] = 0U;
            vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] = 0U;
            vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] = 0U;
        }
        if (((3U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state)) 
             & (IData)(vlSelf->in_ready))) {
            vlSelf->__Vdly__multiplier__DOT__negative 
                = (1U & ((IData)(((- vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term) 
                                  >> 0x3fU)) ^ (IData)(
                                                       (vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value 
                                                        >> 0x3fU))));
            vlSelf->__PVT__multiplier__DOT__busy = 1U;
            vlSelf->__PVT__multiplier__DOT__magnitude_a 
                = ((1U & (IData)(((- vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term) 
                                  >> 0x3fU))) ? (- 
                                                 (- vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term))
                    : (- vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term));
            vlSelf->__PVT__multiplier__DOT__magnitude_b 
                = ((1U & (IData)((vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value 
                                  >> 0x3fU))) ? (- vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value)
                    : vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value);
        }
        if (((IData)(vlSelf->out_valid) & (4U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state)))) {
            vlSelf->__PVT__multiplier__DOT__busy = 0U;
        }
    } else {
        vlSelf->__Vdly__multiplier__DOT__negative = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__busy = 0U;
        vlSelf->__PVT__multiplier__DOT__magnitude_a = 0ULL;
        vlSelf->__PVT__multiplier__DOT__magnitude_b = 0ULL;
    }
}

VL_INLINE_OPT void Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                        Vbench_anvil_edge_signed_multiplier__pi11___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1\n"); );
    // Init
    VlWide<4>/*127:0*/ __Vtemp_1;
    // Body
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        vlSelf->__Vdly__multiplier__DOT__valid_pipe 
            = (0x3fU & VL_SHIFTL_III(6,6,32, (IData)(vlSelf->__PVT__multiplier__DOT__valid_pipe), 1U));
        if (((3U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state)) 
             & (IData)(vlSelf->in_ready))) {
            vlSelf->__Vdly__multiplier__DOT__valid_pipe 
                = (1U | (IData)(vlSelf->__Vdly__multiplier__DOT__valid_pipe));
        }
        if ((0x20U & (IData)(vlSelf->__PVT__multiplier__DOT__valid_pipe))) {
            VL_NEGATE_W(4, __Vtemp_1, vlSelf->__PVT__multiplier__DOT__tree
                        [4U][0U]);
            if (vlSelf->__PVT__multiplier__DOT__negative) {
                vlSelf->__PVT__multiplier__DOT__result[0U] 
                    = __Vtemp_1[0U];
                vlSelf->__PVT__multiplier__DOT__result[1U] 
                    = __Vtemp_1[1U];
                vlSelf->__PVT__multiplier__DOT__result[2U] 
                    = __Vtemp_1[2U];
                vlSelf->__PVT__multiplier__DOT__result[3U] 
                    = __Vtemp_1[3U];
            } else {
                vlSelf->__PVT__multiplier__DOT__result[0U] 
                    = vlSelf->__PVT__multiplier__DOT__tree
                    [4U][0U][0U];
                vlSelf->__PVT__multiplier__DOT__result[1U] 
                    = vlSelf->__PVT__multiplier__DOT__tree
                    [4U][0U][1U];
                vlSelf->__PVT__multiplier__DOT__result[2U] 
                    = vlSelf->__PVT__multiplier__DOT__tree
                    [4U][0U][2U];
                vlSelf->__PVT__multiplier__DOT__result[3U] 
                    = vlSelf->__PVT__multiplier__DOT__tree
                    [4U][0U][3U];
            }
            vlSelf->__PVT__multiplier__DOT__valid_result = 1U;
        }
        if (((IData)(vlSelf->out_valid) & (4U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state)))) {
            vlSelf->__PVT__multiplier__DOT__valid_result = 0U;
        }
    } else {
        vlSelf->__PVT__multiplier__DOT__valid_result = 0U;
        vlSelf->__Vdly__multiplier__DOT__valid_pipe = 0U;
        vlSelf->__PVT__multiplier__DOT__result[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__result[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__result[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__result[3U] = 0U;
    }
    vlSelf->__PVT__multiplier__DOT__negative = vlSelf->__Vdly__multiplier__DOT__negative;
    vlSelf->__PVT__multiplier__DOT__valid_pipe = vlSelf->__Vdly__multiplier__DOT__valid_pipe;
    vlSelf->__PVT__multiplier__DOT__tree[0U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][2U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][2U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][2U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][2U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][3U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][3U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][3U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][3U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][4U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][4U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][4U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][4U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][5U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][5U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][5U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][5U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][6U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][6U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][6U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][6U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][7U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][7U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][7U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][7U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][8U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][8U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][8U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][8U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][9U][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][9U][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][9U][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][9U][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xaU][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xaU][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xaU][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xaU][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xbU][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xbU][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xbU][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xbU][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xcU][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xcU][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xcU][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xcU][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xdU][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xdU][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xdU][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xdU][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xeU][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xeU][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xeU][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xeU][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xfU][0U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xfU][1U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xfU][2U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__tree[0U][0xfU][3U] 
        = vlSelf->__PVT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][2U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][2U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][2U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][2U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][3U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][3U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][3U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][3U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][4U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][4U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][4U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][4U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][5U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][5U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][5U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][5U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][6U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][6U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][6U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][6U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][7U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][7U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][7U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[1U][7U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][2U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][2U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][2U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][2U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][3U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][3U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][3U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[2U][3U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[3U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[3U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[3U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[3U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[3U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[3U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[3U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[3U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__tree[4U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__tree[4U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__tree[4U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__tree[4U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
}
