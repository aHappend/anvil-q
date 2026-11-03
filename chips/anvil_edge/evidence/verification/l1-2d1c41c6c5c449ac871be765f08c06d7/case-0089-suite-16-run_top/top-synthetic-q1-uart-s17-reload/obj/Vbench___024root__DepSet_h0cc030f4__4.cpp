// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench___024root.h"

extern const VlUnpacked<IData/*31:0*/, 16> Vbench__ConstPool__TABLE_h1bfbab1a_0;
extern const VlUnpacked<CData/*2:0*/, 16> Vbench__ConstPool__TABLE_h2862d6e0_0;
extern const VlUnpacked<CData/*1:0*/, 16> Vbench__ConstPool__TABLE_h400161fb_0;
extern const VlUnpacked<CData/*1:0*/, 16> Vbench__ConstPool__TABLE_h6243dc1f_0;
extern const VlUnpacked<CData/*1:0*/, 32> Vbench__ConstPool__TABLE_h7831209a_0;

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__7(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__7\n"); );
    // Init
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted_operation;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted_operation = 0;
    IData/*31:0*/ __Vfunc_sat32__102__Vfuncout;
    __Vfunc_sat32__102__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__102__x;
    VL_ZERO_W(128, __Vfunc_sat32__102__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__103__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__103__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__103__x;
    VL_ZERO_W(128, __Vfunc_round_shift__103__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__103__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__103__magnitude);
    CData/*4:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    CData/*3:0*/ __Vtableidx2;
    __Vtableidx2 = 0;
    VlWide<4>/*127:0*/ __Vtemp_35;
    VlWide<5>/*159:0*/ __Vtemp_36;
    VlWide<5>/*159:0*/ __Vtemp_37;
    VlWide<5>/*159:0*/ __Vtemp_44;
    VlWide<5>/*159:0*/ __Vtemp_45;
    VlWide<5>/*159:0*/ __Vtemp_46;
    VlWide<5>/*159:0*/ __Vtemp_47;
    VlWide<4>/*127:0*/ __Vtemp_49;
    VlWide<5>/*159:0*/ __Vtemp_50;
    VlWide<4>/*127:0*/ __Vtemp_54;
    VlWide<4>/*127:0*/ __Vtemp_55;
    // Body
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__layer 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__layer;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__position 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__position;
    __Vtableidx2 = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__step;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected 
        = Vbench__ConstPool__TABLE_h1bfbab1a_0[__Vtableidx2];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__projection 
        = Vbench__ConstPool__TABLE_h2862d6e0_0[__Vtableidx2];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm_mode 
        = Vbench__ConstPool__TABLE_h400161fb_0[__Vtableidx2];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__element_mode 
        = Vbench__ConstPool__TABLE_h6243dc1f_0[__Vtableidx2];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__position 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__position;
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_index 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_index;
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_count 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_count;
    if (vlSelf->__Vdlyvset__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars__v0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars[vlSelf->__Vdlyvdim0__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars__v0] 
            = vlSelf->__Vdlyvval__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars__v0;
    }
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state;
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__out_ready 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)) 
           | (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__in_valid 
        = ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)) 
           | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__out_ready 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)) 
           | (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__in_valid 
        = ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)) 
           | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid;
    __Vtableidx1 = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state;
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected 
        = Vbench__ConstPool__TABLE_h7831209a_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_selected 
        = ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
           | ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
              | ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
                 | (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)))));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
           | ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
              | (3U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state))));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected 
        = ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
           | ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
              | ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
                 | (0x10U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)))));
    if (vlSelf->bench__DOT__dut__DOT__client_rst_n) {
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 8U;
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 8U;
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 8U;
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_valid) 
                        & (0x15U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 0U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result 
                        = (IData)((VL_GTS_IQQ(64, 0ULL, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__total)
                                    ? 0ULL : VL_SHIFTR_QQQ(64,64,64, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__total, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__exponent)));
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 8U;
                } else if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid) {
                    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divide_by_zero) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 8U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__total 
                            = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__total 
                               + vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__signed_quotient);
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__signed_quotient;
                        if ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order))) {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 7U;
                        } else {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order)));
                            vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 3U;
                        }
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 6U;
                }
            } else if (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.out_valid) {
                if ((((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                       ? vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                       : 0U) >> 0x1fU)) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term_negative = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__division_magnitude 
                        = (- (((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                 ? 
                                                vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                                 : 0U))) 
                               << 0x20U) | (QData)((IData)(
                                                           ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                             ? 
                                                            vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                             : 0U)))));
                } else {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term_negative = 0U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__division_magnitude 
                        = (((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                              ? vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                              : 0U))) 
                            << 0x20U) | (QData)((IData)(
                                                        ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                          ? 
                                                         vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                          : 0U))));
                }
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
                if (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier.in_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid) {
                if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divide_by_zero) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 8U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__total = 0x1000000ULL;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__exponent 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__remainder_value 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                            ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result
                            : 0ULL);
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term = 0x1000000ULL;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 3U;
                }
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 2U;
            }
        } else if (((0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_ready))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result = 0U;
            if (VL_GTS_IQQ(64, 0xfffffffffff00000ULL, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_argument)) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 8U;
            } else if (VL_LTES_IQQ(64, 0ULL, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_argument)) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result = 0x1000000U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 8U;
            } else {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__reduced_input 
                    = VL_SHIFTL_QQI(64,64,32, (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_argument), 8U);
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 1U;
            }
        }
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid) 
                        & (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state)))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 0U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result 
                        = (IData)((VL_GTS_IQQ(64, 0ULL, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__total)
                                    ? 0ULL : VL_SHIFTR_QQQ(64,64,64, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__total, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__exponent)));
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
                } else if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) {
                    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__total 
                            = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__total 
                               + vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient);
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient;
                        if ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order))) {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 7U;
                        } else {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order)));
                            vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 3U;
                        }
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 6U;
                }
            } else if (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.out_valid) {
                if ((((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                       ? vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                       : 0U) >> 0x1fU)) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude 
                        = (- (((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                 ? 
                                                vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                                 : 0U))) 
                               << 0x20U) | (QData)((IData)(
                                                           ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                             ? 
                                                            vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                             : 0U)))));
                } else {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = 0U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude 
                        = (((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                              ? vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                              : 0U))) 
                            << 0x20U) | (QData)((IData)(
                                                        ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                          ? 
                                                         vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                          : 0U))));
                }
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                if (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.in_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) {
                if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__total = 0x1000000ULL;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__exponent 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                            ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result
                            : 0ULL);
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term = 0x1000000ULL;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 3U;
                }
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 2U;
            }
        } else if (((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready))) {
            vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
            if (VL_GTS_IQQ(64, 0xfffffffffff00000ULL, 
                           (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__magnitude))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else if (VL_LTES_IQQ(64, 0ULL, (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__magnitude))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result = 0x1000000U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input 
                    = VL_SHIFTL_QQI(64,64,32, (- (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__magnitude)), 8U);
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 1U;
            }
        }
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid) 
                        & (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state)))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 0U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result 
                        = (IData)((VL_GTS_IQQ(64, 0ULL, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__total)
                                    ? 0ULL : VL_SHIFTR_QQQ(64,64,64, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__total, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__exponent)));
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
                } else if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) {
                    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__total 
                            = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__total 
                               + vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient);
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient;
                        if ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order))) {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 7U;
                        } else {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order)));
                            vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 3U;
                        }
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 6U;
                }
            } else if (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.out_valid) {
                if ((((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                       ? vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                       : 0U) >> 0x1fU)) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude 
                        = (- (((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                 ? 
                                                vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                                 : 0U))) 
                               << 0x20U) | (QData)((IData)(
                                                           ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                             ? 
                                                            vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                             : 0U)))));
                } else {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = 0U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude 
                        = (((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                              ? vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                              : 0U))) 
                            << 0x20U) | (QData)((IData)(
                                                        ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                                                          ? 
                                                         vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                          : 0U))));
                }
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
                if (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier.in_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) {
                if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__total = 0x1000000ULL;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__exponent 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                            ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result
                            : 0ULL);
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term = 0x1000000ULL;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 3U;
                }
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 2U;
            }
        } else if (((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
            if (VL_GTS_IQQ(64, 0xfffffffffff00000ULL, 
                           (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else if (VL_LTES_IQQ(64, 0ULL, (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result = 0x1000000U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 8U;
            } else {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input 
                    = VL_SHIFTL_QQI(64,64,32, (- (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude)), 8U);
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 1U;
            }
        }
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 8U;
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 8U;
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 8U;
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid) 
                        & (7U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state)))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 0U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
                    __Vfunc_round_shift__103__x[0U] 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[0U];
                    __Vfunc_round_shift__103__x[1U] 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[1U];
                    __Vfunc_round_shift__103__x[2U] 
                        = (((IData)((0x7fffffffffffffffULL 
                                     & (- (QData)((IData)(
                                                          (1U 
                                                           & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[2U])))))) 
                            << 1U) | vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[2U]);
                    __Vfunc_round_shift__103__x[3U] 
                        = (((IData)((0x7fffffffffffffffULL 
                                     & (- (QData)((IData)(
                                                          (1U 
                                                           & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[2U])))))) 
                            >> 0x1fU) | ((IData)(((0x7fffffffffffffffULL 
                                                   & (- (QData)((IData)(
                                                                        (1U 
                                                                         & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[2U]))))) 
                                                  >> 0x20U)) 
                                         << 1U));
                    __Vtemp_35[0U] = 0U;
                    __Vtemp_35[1U] = 0U;
                    __Vtemp_35[2U] = 0U;
                    __Vtemp_35[3U] = 0U;
                    __Vtemp_36[0U] = __Vfunc_round_shift__103__x[0U];
                    __Vtemp_36[1U] = __Vfunc_round_shift__103__x[1U];
                    __Vtemp_36[2U] = __Vfunc_round_shift__103__x[2U];
                    __Vtemp_36[3U] = __Vfunc_round_shift__103__x[3U];
                    __Vtemp_36[4U] = (__Vfunc_round_shift__103__x[3U] 
                                      >> 0x1fU);
                    VL_NEGATE_W(5, __Vtemp_37, __Vtemp_36);
                    if (VL_GTS_IWW(128, __Vtemp_35, __Vfunc_round_shift__103__x)) {
                        __Vfunc_round_shift__103__magnitude[0U] 
                            = __Vtemp_37[0U];
                        __Vfunc_round_shift__103__magnitude[1U] 
                            = __Vtemp_37[1U];
                        __Vfunc_round_shift__103__magnitude[2U] 
                            = __Vtemp_37[2U];
                        __Vfunc_round_shift__103__magnitude[3U] 
                            = __Vtemp_37[3U];
                        __Vfunc_round_shift__103__magnitude[4U] 
                            = (1U & __Vtemp_37[4U]);
                    } else {
                        __Vfunc_round_shift__103__magnitude[0U] 
                            = __Vfunc_round_shift__103__x[0U];
                        __Vfunc_round_shift__103__magnitude[1U] 
                            = __Vfunc_round_shift__103__x[1U];
                        __Vfunc_round_shift__103__magnitude[2U] 
                            = __Vfunc_round_shift__103__x[2U];
                        __Vfunc_round_shift__103__magnitude[3U] 
                            = __Vfunc_round_shift__103__x[3U];
                        __Vfunc_round_shift__103__magnitude[4U] = 0U;
                    }
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 8U;
                    __Vtemp_44[0U] = 0x800000U;
                    __Vtemp_44[1U] = 0U;
                    __Vtemp_44[2U] = 0U;
                    __Vtemp_44[3U] = 0U;
                    __Vtemp_44[4U] = 0U;
                    VL_ADD_W(5, __Vtemp_45, __Vtemp_44, __Vfunc_round_shift__103__magnitude);
                    __Vtemp_46[0U] = __Vtemp_45[0U];
                    __Vtemp_46[1U] = __Vtemp_45[1U];
                    __Vtemp_46[2U] = __Vtemp_45[2U];
                    __Vtemp_46[3U] = __Vtemp_45[3U];
                    __Vtemp_46[4U] = (1U & __Vtemp_45[4U]);
                    VL_SHIFTR_WWI(129,129,32, __Vtemp_47, __Vtemp_46, 0x18U);
                    __Vfunc_round_shift__103__magnitude[0U] 
                        = __Vtemp_47[0U];
                    __Vfunc_round_shift__103__magnitude[1U] 
                        = __Vtemp_47[1U];
                    __Vfunc_round_shift__103__magnitude[2U] 
                        = __Vtemp_47[2U];
                    __Vfunc_round_shift__103__magnitude[3U] 
                        = __Vtemp_47[3U];
                    __Vfunc_round_shift__103__magnitude[4U] 
                        = (1U & __Vtemp_47[4U]);
                    __Vtemp_49[0U] = 0U;
                    __Vtemp_49[1U] = 0U;
                    __Vtemp_49[2U] = 0U;
                    __Vtemp_49[3U] = 0U;
                    VL_NEGATE_W(5, __Vtemp_50, __Vfunc_round_shift__103__magnitude);
                    if (VL_GTS_IWW(128, __Vtemp_49, __Vfunc_round_shift__103__x)) {
                        __Vfunc_round_shift__103__Vfuncout[0U] 
                            = __Vtemp_50[0U];
                        __Vfunc_round_shift__103__Vfuncout[1U] 
                            = __Vtemp_50[1U];
                        __Vfunc_round_shift__103__Vfuncout[2U] 
                            = __Vtemp_50[2U];
                        __Vfunc_round_shift__103__Vfuncout[3U] 
                            = __Vtemp_50[3U];
                    } else {
                        __Vfunc_round_shift__103__Vfuncout[0U] 
                            = __Vfunc_round_shift__103__magnitude[0U];
                        __Vfunc_round_shift__103__Vfuncout[1U] 
                            = __Vfunc_round_shift__103__magnitude[1U];
                        __Vfunc_round_shift__103__Vfuncout[2U] 
                            = __Vfunc_round_shift__103__magnitude[2U];
                        __Vfunc_round_shift__103__Vfuncout[3U] 
                            = __Vfunc_round_shift__103__magnitude[3U];
                    }
                    __Vfunc_sat32__102__x[0U] = __Vfunc_round_shift__103__Vfuncout[0U];
                    __Vfunc_sat32__102__x[1U] = __Vfunc_round_shift__103__Vfuncout[1U];
                    __Vfunc_sat32__102__x[2U] = __Vfunc_round_shift__103__Vfuncout[2U];
                    __Vfunc_sat32__102__x[3U] = __Vfunc_round_shift__103__Vfuncout[3U];
                    __Vtemp_54[0U] = 0x7fffffffU;
                    __Vtemp_54[1U] = 0U;
                    __Vtemp_54[2U] = 0U;
                    __Vtemp_54[3U] = 0U;
                    __Vtemp_55[0U] = 0x80000000U;
                    __Vtemp_55[1U] = 0xffffffffU;
                    __Vtemp_55[2U] = 0xffffffffU;
                    __Vtemp_55[3U] = 0xffffffffU;
                    __Vfunc_sat32__102__Vfuncout = 
                        (VL_LTS_IWW(128, __Vtemp_54, __Vfunc_sat32__102__x)
                          ? 0x7fffffffU : (VL_GTS_IWW(128, __Vtemp_55, __Vfunc_sat32__102__x)
                                            ? 0x80000000U
                                            : __Vfunc_sat32__102__x[0U]));
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result 
                        = __Vfunc_sat32__102__Vfuncout;
                } else if (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier.out_valid) {
                    if (vlSelf->bench__DOT__dut__DOT__client_rst_n) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[0U] 
                            = vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier.__PVT__multiplier__DOT__result[0U];
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[1U] 
                            = vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U];
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[2U] 
                            = (1U & vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier.__PVT__multiplier__DOT__result[2U]);
                    } else {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[0U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[1U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[2U] = 0U;
                    }
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
                if (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier.in_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 6U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 8U;
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                            ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result
                            : 0ULL);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 5U;
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 8U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__numerator 
                        = (VL_LTES_III(32, 0U, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand)
                            ? 0x1000000000000ULL : 
                           ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential)) 
                            << 0x18U));
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__denominator 
                        = (0x1000000ULL + (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential)));
                    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 3U;
                }
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 2U;
            }
        } else if (((6U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__magnitude 
                = (VL_GTS_III(32, 0U, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a)
                    ? (- (((QData)((IData)((- (IData)(
                                                      (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a 
                                                       >> 0x1fU))))) 
                           << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a))))
                    : (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a)));
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result = 0U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 1U;
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__total = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__reduced_input = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__exponent = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__remainder_value = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__division_magnitude = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term_negative = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__total = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__exponent = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__total = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__exponent = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__magnitude = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__numerator = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__denominator = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____VdfgTmp_hf61b8ee4__0 
        = (1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected)) 
                 & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected) 
                       | (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_selected)))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_argument 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_argument;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__out_ready 
        = ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x1aU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)));
    if ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[0U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__dot[0U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[1U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__dot[1U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[2U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__dot[2U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[3U] 
            = (- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__dot[2U] 
                          >> 0x1fU)));
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[0U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted[0U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[1U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted[1U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[2U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted[2U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[3U] 
            = (- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted[2U] 
                          >> 0x1fU)));
    }
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted_operation 
        = ((0x19U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x1aU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__in_valid 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x19U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)));
    if (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted_operation) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiply_a 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiply_b 
            = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential));
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiply_a 
            = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__q 
                                            >> 0x1fU))))) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__q)));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiply_b 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0;
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state;
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__9(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__9\n"); );
    // Init
    CData/*0:0*/ __Vfunc_bench__DOT__readable__1__Vfuncout;
    __Vfunc_bench__DOT__readable__1__Vfuncout = 0;
    QData/*63:0*/ __Vfunc_bench__DOT__readable__1__address;
    __Vfunc_bench__DOT__readable__1__address = 0;
    CData/*0:0*/ __Vfunc_bench__DOT__readable__2__Vfuncout;
    __Vfunc_bench__DOT__readable__2__Vfuncout = 0;
    QData/*63:0*/ __Vfunc_bench__DOT__readable__2__address;
    __Vfunc_bench__DOT__readable__2__address = 0;
    CData/*2:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0;
    __Vdlyvdim0__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0 = 0;
    IData/*31:0*/ __Vdlyvval__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0;
    __Vdlyvval__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0;
    __Vdlyvset__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0 = 0;
    // Body
    __Vdlyvset__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0 = 0U;
    vlSelf->bench__DOT__cycle = ((IData)(1U) + vlSelf->bench__DOT__cycle);
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(vlSelf->bench__DOT__running))) {
        if (VL_UNLIKELY(((IData)(vlSelf->bench__DOT__cfg_valid) 
                         | (IData)(vlSelf->bench__DOT__cfg_write)))) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:41: Assertion failed in %Nbench: TOP_HOST_INTERVENTION\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name());
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 41, "");
        }
        if (VL_UNLIKELY(((IData)(vlSelf->bench__DOT__error) 
                         & (~ (IData)(vlSelf->bench__DOT__expect_rejection))))) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:43: Assertion failed in %Nbench: TOP_INFERENCE_ERROR code=%x\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name(),8,((IData)(vlSelf->bench__DOT__rst_n)
                                          ? (IData)(vlSelf->bench__DOT__dut__DOT__code)
                                          : 0U));
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 43, "");
        }
        if (VL_UNLIKELY(((IData)(vlSelf->bench__DOT__expect_rejection) 
                         & (((((0U != vlSelf->bench__DOT__embedding_reads) 
                               | (0U != vlSelf->bench__DOT__inference_writes)) 
                              | (IData)(vlSelf->bench__DOT__m_axis_tvalid)) 
                             | (IData)(vlSelf->bench__DOT__done)) 
                            | (~ ((~ (IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n)) 
                                  | ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_active)) 
                                     | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_shift)))))))) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:46: Assertion failed in %Nbench: TOP_REJECTED_FRAME_PREFILL_OR_OUTPUT\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name());
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 46, "");
        }
        if (VL_UNLIKELY(((IData)(vlSelf->bench__DOT__out_held) 
                         & ((~ (IData)(vlSelf->bench__DOT__m_axis_tvalid)) 
                            | ((((IData)(vlSelf->bench__DOT__m_axis_tlast) 
                                 << 8U) | (IData)(vlSelf->bench__DOT__m_axis_tdata)) 
                               != (IData)(vlSelf->bench__DOT__held_output)))))) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:48: Assertion failed in %Nbench: TOP_OUTPUT_STABILITY\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name());
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 48, "");
        }
        vlSelf->bench__DOT__out_held = ((IData)(vlSelf->bench__DOT__m_axis_tvalid) 
                                        & (~ (IData)(vlSelf->bench__DOT__m_axis_tready)));
        vlSelf->bench__DOT__held_output = (((IData)(vlSelf->bench__DOT__m_axis_tlast) 
                                            << 8U) 
                                           | (IData)(vlSelf->bench__DOT__m_axis_tdata));
        if (VL_UNLIKELY(vlSelf->bench__DOT__m_axis_tvalid)) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:51: Assertion failed in %Nbench: TOP_UART_BYPASS_LEAK\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name());
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 51, "");
        }
        if (((IData)(vlSelf->bench__DOT__m_axis_tvalid) 
             & (IData)(vlSelf->bench__DOT__m_axis_tready))) {
            if (VL_UNLIKELY(((VL_LTES_III(32, 2U, vlSelf->bench__DOT__outputs) 
                              | (0U != (IData)(vlSelf->bench__DOT__m_axis_tdata))) 
                             | ((IData)(vlSelf->bench__DOT__m_axis_tlast) 
                                != (1U == vlSelf->bench__DOT__outputs))))) {
                VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:54: Assertion failed in %Nbench: TOP_FIXED_POINT_OUTPUT item=%0d byte=%x last=%b\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),32,vlSelf->bench__DOT__outputs,
                          8,(IData)(vlSelf->bench__DOT__m_axis_tdata),
                          1,vlSelf->bench__DOT__m_axis_tlast);
                VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 54, "");
            }
            vlSelf->bench__DOT__outputs = ((IData)(1U) 
                                           + vlSelf->bench__DOT__outputs);
            vlSelf->bench__DOT__comparisons = ((IData)(1U) 
                                               + vlSelf->bench__DOT__comparisons);
        }
        if (vlSelf->bench__DOT__done) {
            if (VL_UNLIKELY(((((2U != vlSelf->bench__DOT__outputs) 
                               | (0U != vlSelf->bench__DOT__completions)) 
                              | (IData)(vlSelf->bench__DOT__pending)) 
                             | (IData)(vlSelf->bench__DOT__m_axis_tvalid)))) {
                VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:60: Assertion failed in %Nbench: TOP_OUTPUT_DRAIN\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 60, "");
            }
            vlSelf->bench__DOT__completions = ((IData)(1U) 
                                               + vlSelf->bench__DOT__completions);
        }
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (VL_UNLIKELY(((IData)(vlSelf->bench__DOT__held) 
                         & ((~ (IData)(vlSelf->bench__DOT__ddr_req_valid)) 
                            | (0U != ((((((vlSelf->bench__DOT__ddr_req_wdata 
                                           << 4U) | (IData)(vlSelf->bench__DOT__ddr_req_wstrb)) 
                                         ^ vlSelf->bench__DOT__held_payload[0U]) 
                                        | (((vlSelf->bench__DOT__ddr_req_wdata 
                                             >> 0x1cU) 
                                            | ((IData)(vlSelf->bench__DOT__ddr_req_addr) 
                                               << 4U)) 
                                           ^ vlSelf->bench__DOT__held_payload[1U])) 
                                       | ((((IData)(vlSelf->bench__DOT__ddr_req_addr) 
                                            >> 0x1cU) 
                                           | ((IData)(
                                                      (vlSelf->bench__DOT__ddr_req_addr 
                                                       >> 0x20U)) 
                                              << 4U)) 
                                          ^ vlSelf->bench__DOT__held_payload[2U])) 
                                      | ((((IData)(vlSelf->bench__DOT__ddr_req_write) 
                                           << 4U) | 
                                          ((IData)(
                                                   (vlSelf->bench__DOT__ddr_req_addr 
                                                    >> 0x20U)) 
                                           >> 0x1cU)) 
                                         ^ vlSelf->bench__DOT__held_payload[3U]))))))) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:188: Assertion failed in %Nbench: BOOT_DDR_STABILITY\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name());
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 188, "");
        }
        vlSelf->bench__DOT__held = ((IData)(vlSelf->bench__DOT__ddr_req_valid) 
                                    & (~ (IData)(vlSelf->bench__DOT__ddr_req_ready)));
        vlSelf->bench__DOT__held_payload[0U] = ((vlSelf->bench__DOT__ddr_req_wdata 
                                                 << 4U) 
                                                | (IData)(vlSelf->bench__DOT__ddr_req_wstrb));
        vlSelf->bench__DOT__held_payload[1U] = ((vlSelf->bench__DOT__ddr_req_wdata 
                                                 >> 0x1cU) 
                                                | ((IData)(vlSelf->bench__DOT__ddr_req_addr) 
                                                   << 4U));
        vlSelf->bench__DOT__held_payload[2U] = (((IData)(vlSelf->bench__DOT__ddr_req_addr) 
                                                 >> 0x1cU) 
                                                | ((IData)(
                                                           (vlSelf->bench__DOT__ddr_req_addr 
                                                            >> 0x20U)) 
                                                   << 4U));
        vlSelf->bench__DOT__held_payload[3U] = (((IData)(vlSelf->bench__DOT__ddr_req_write) 
                                                 << 4U) 
                                                | ((IData)(
                                                           (vlSelf->bench__DOT__ddr_req_addr 
                                                            >> 0x20U)) 
                                                   >> 0x1cU));
        if (vlSelf->bench__DOT__held) {
            vlSelf->bench__DOT__request_stalls = ((IData)(1U) 
                                                  + vlSelf->bench__DOT__request_stalls);
        }
        if (((IData)(vlSelf->bench__DOT__ddr_rsp_valid) 
             & (~ (IData)(vlSelf->bench__DOT__ddr_rsp_ready)))) {
            vlSelf->bench__DOT__response_stalls = ((IData)(1U) 
                                                   + vlSelf->bench__DOT__response_stalls);
        }
        if (((IData)(vlSelf->bench__DOT__ddr_rsp_valid) 
             & (IData)(vlSelf->bench__DOT__ddr_rsp_ready))) {
            if (VL_UNLIKELY((1U & (~ (IData)(vlSelf->bench__DOT__pending))))) {
                VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:194: Assertion failed in %Nbench: BOOT_ORPHAN_RESPONSE\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 194, "");
            }
            vlSelf->bench__DOT__acknowledgements = 
                ((IData)(1U) + vlSelf->bench__DOT__acknowledgements);
            vlSelf->bench__DOT__pending = 0U;
            vlSelf->__Vdly__bench__DOT__ddr_rsp_valid = 0U;
        }
        if (((IData)(vlSelf->bench__DOT__ddr_req_valid) 
             & (IData)(vlSelf->bench__DOT__ddr_req_ready))) {
            if (VL_UNLIKELY((1U & (((IData)(vlSelf->bench__DOT__pending) 
                                    | (~ (IData)(vlSelf->bench__DOT__ddr_cal_done))) 
                                   | (0xfffcULL <= vlSelf->bench__DOT__ddr_req_addr))))) {
                VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:199: Assertion failed in %Nbench: BOOT_DDR_OUTSTANDING_OR_BOUNDS\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name());
                VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 199, "");
            }
            vlSelf->bench__DOT__pending_address = vlSelf->bench__DOT__ddr_req_addr;
            vlSelf->bench__DOT__delay_count = ((IData)(1U) 
                                               + (7U 
                                                  & (vlSelf->bench__DOT__rng 
                                                     >> 2U)));
            if (vlSelf->bench__DOT__running) {
                if (VL_UNLIKELY((1U & (~ ([&]() {
                                        __Vfunc_bench__DOT__readable__1__address 
                                            = vlSelf->bench__DOT__ddr_req_addr;
                                        __Vfunc_bench__DOT__readable__1__Vfuncout = 0U;
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [1U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [1U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [1U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [2U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [2U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [2U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [3U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [3U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [3U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [4U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [4U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [4U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [5U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [5U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [5U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [6U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [6U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [6U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [7U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [7U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [7U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [8U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [8U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [8U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [9U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [9U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [9U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0xaU]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0xaU] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0xaU]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0xbU]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0xbU] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0xbU]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0xcU]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0xcU] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0xcU]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0xdU]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0xdU] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0xdU]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0xeU]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0xeU] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0xeU]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0xfU]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0xfU] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0xfU]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0x10U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0x10U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0x10U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0x11U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0x11U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0x11U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0x12U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0x12U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0x12U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                        if ((((__Vfunc_bench__DOT__readable__1__address 
                                               >= vlSelf->bench__DOT__segment_base
                                               [0x13U]) 
                                              & (__Vfunc_bench__DOT__readable__1__address 
                                                 < 
                                                 (vlSelf->bench__DOT__segment_base
                                                  [0x13U] 
                                                  + 
                                                  vlSelf->bench__DOT__segment_length
                                                  [0x13U]))) 
                                             & (0U 
                                                == 
                                                (3U 
                                                 & (IData)(__Vfunc_bench__DOT__readable__1__address))))) {
                                            __Vfunc_bench__DOT__readable__1__Vfuncout = 1U;
                                        }
                                    }(), (IData)(__Vfunc_bench__DOT__readable__1__Vfuncout)))))) {
                    VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:202: Assertion failed in %Nbench: TOP_MEMORY_BOUNDS\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name());
                    VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 202, "");
                }
                if ((((~ (IData)(vlSelf->bench__DOT__ddr_req_write)) 
                      & (0x1660ULL <= vlSelf->bench__DOT__ddr_req_addr)) 
                     & (0x3680ULL > vlSelf->bench__DOT__ddr_req_addr))) {
                    vlSelf->bench__DOT__operation_index 
                        = VL_DIVS_III(32, vlSelf->bench__DOT__embedding_reads, (IData)(0x810U));
                    vlSelf->bench__DOT__comparisons 
                        = ((IData)(1U) + vlSelf->bench__DOT__comparisons);
                    vlSelf->bench__DOT__embedding_index 
                        = VL_MODDIVS_III(32, vlSelf->bench__DOT__embedding_reads, (IData)(0x810U));
                    if (VL_UNLIKELY(VL_LTES_III(32, 3U, vlSelf->bench__DOT__operation_index))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:208: Assertion failed in %Nbench: TOP_EXTRA_CORE_OPERATION\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 208, "");
                    }
                    if (VL_GTS_III(32, 8U, vlSelf->bench__DOT__embedding_index)) {
                        if (VL_UNLIKELY((vlSelf->bench__DOT__ddr_req_addr 
                                         != (0x1660ULL 
                                             + (VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                                                ((2U 
                                                                                >= 
                                                                                (3U 
                                                                                & vlSelf->bench__DOT__operation_index))
                                                                                 ? 
                                                                                vlSelf->bench__DOT__expected_tokens
                                                                                [
                                                                                (3U 
                                                                                & vlSelf->bench__DOT__operation_index)]
                                                                                 : vlSelf->bench__DOT____Vxrand_h8d93fe75__0))), 5U) 
                                                + VL_SHIFTL_QQI(64,64,32, (QData)((IData)(vlSelf->bench__DOT__embedding_index)), 2U)))))) {
                            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:212: Assertion failed in %Nbench: TOP_PREFILL_TOKEN operation=%0d column=%0d address=%x token=%0#\n",
                                      64,VL_TIME_UNITED_Q(1000),
                                      -9,vlSymsp->name(),
                                      32,vlSelf->bench__DOT__operation_index,
                                      32,vlSelf->bench__DOT__embedding_index,
                                      64,vlSelf->bench__DOT__ddr_req_addr,
                                      32,((2U >= (3U 
                                                  & vlSelf->bench__DOT__operation_index))
                                           ? vlSelf->bench__DOT__expected_tokens
                                          [(3U & vlSelf->bench__DOT__operation_index)]
                                           : vlSelf->bench__DOT____Vxrand_h8d93fe75__1));
                            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 212, "");
                        }
                    } else if (VL_UNLIKELY((vlSelf->bench__DOT__ddr_req_addr 
                                            != (0x1660ULL 
                                                + VL_SHIFTL_QQI(64,64,32, 
                                                                ((QData)((IData)(vlSelf->bench__DOT__embedding_index)) 
                                                                 - 8ULL), 2U))))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:216: Assertion failed in %Nbench: TOP_PROJECTION_ORDER\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 216, "");
                    }
                    vlSelf->bench__DOT__embedding_reads 
                        = ((IData)(1U) + vlSelf->bench__DOT__embedding_reads);
                }
                if (vlSelf->bench__DOT__ddr_req_write) {
                    if (VL_UNLIKELY((((vlSelf->bench__DOT__ddr_req_addr 
                                       < vlSelf->bench__DOT__segment_base
                                       [3U]) | (vlSelf->bench__DOT__ddr_req_addr 
                                                >= 
                                                (vlSelf->bench__DOT__segment_base
                                                 [3U] 
                                                 + 
                                                 vlSelf->bench__DOT__segment_length
                                                 [3U]))) 
                                     | (0xfU != (IData)(vlSelf->bench__DOT__ddr_req_wstrb))))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:225: Assertion failed in %Nbench: TOP_IMMUTABLE_WRITE\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 225, "");
                    }
                    vlSelf->bench__DOT__ddr[(0xffffU 
                                             & (IData)(vlSelf->bench__DOT__ddr_req_addr))] 
                        = (0xffU & vlSelf->bench__DOT__ddr_req_wdata);
                    vlSelf->bench__DOT__inference_writes 
                        = ((IData)(1U) + vlSelf->bench__DOT__inference_writes);
                    if (VL_UNLIKELY((0U != vlSelf->bench__DOT__ddr_req_wdata))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:226: Assertion failed in %Nbench: TOP_ZERO_MODEL_ACTIVATION\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 226, "");
                    }
                    vlSelf->bench__DOT__ddr[(0xffffU 
                                             & ((IData)(1U) 
                                                + (IData)(vlSelf->bench__DOT__ddr_req_addr)))] 
                        = (0xffU & (vlSelf->bench__DOT__ddr_req_wdata 
                                    >> 8U));
                    if (((0x399cULL <= vlSelf->bench__DOT__ddr_req_addr) 
                         & (0x3a1cULL > vlSelf->bench__DOT__ddr_req_addr))) {
                        if (VL_UNLIKELY((vlSelf->bench__DOT__ddr_req_addr 
                                         != (0x399cULL 
                                             + VL_SHIFTL_QQI(64,64,32, (QData)((IData)(vlSelf->bench__DOT__cache_k_writes)), 2U))))) {
                            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:229: Assertion failed in %Nbench: TOP_CACHE_K_POSITION\n",
                                      64,VL_TIME_UNITED_Q(1000),
                                      -9,vlSymsp->name());
                            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 229, "");
                        }
                        vlSelf->bench__DOT__cache_k_writes 
                            = ((IData)(1U) + vlSelf->bench__DOT__cache_k_writes);
                    }
                    vlSelf->bench__DOT__ddr[(0xffffU 
                                             & ((IData)(2U) 
                                                + (IData)(vlSelf->bench__DOT__ddr_req_addr)))] 
                        = (0xffU & (vlSelf->bench__DOT__ddr_req_wdata 
                                    >> 0x10U));
                    if (((0x3a1cULL <= vlSelf->bench__DOT__ddr_req_addr) 
                         & (0x3a9cULL > vlSelf->bench__DOT__ddr_req_addr))) {
                        if (VL_UNLIKELY((vlSelf->bench__DOT__ddr_req_addr 
                                         != (0x3a1cULL 
                                             + VL_SHIFTL_QQI(64,64,32, (QData)((IData)(vlSelf->bench__DOT__cache_v_writes)), 2U))))) {
                            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:234: Assertion failed in %Nbench: TOP_CACHE_V_POSITION\n",
                                      64,VL_TIME_UNITED_Q(1000),
                                      -9,vlSymsp->name());
                            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 234, "");
                        }
                        vlSelf->bench__DOT__cache_v_writes 
                            = ((IData)(1U) + vlSelf->bench__DOT__cache_v_writes);
                    }
                    vlSelf->bench__DOT__ddr[(0xffffU 
                                             & ((IData)(3U) 
                                                + (IData)(vlSelf->bench__DOT__ddr_req_addr)))] 
                        = (vlSelf->bench__DOT__ddr_req_wdata 
                           >> 0x18U);
                } else {
                    vlSelf->bench__DOT__inference_reads 
                        = ((IData)(1U) + vlSelf->bench__DOT__inference_reads);
                }
            } else if (vlSelf->bench__DOT__ddr_req_write) {
                if (VL_UNLIKELY((1U & ((((~ (IData)(vlSelf->bench__DOT__loading)) 
                                         | VL_LTES_III(32, 0x1138U, vlSelf->bench__DOT__writes)) 
                                        | (vlSelf->bench__DOT__ddr_req_addr 
                                           != vlSelf->bench__DOT__write_address
                                           [(0x1fffU 
                                             & vlSelf->bench__DOT__writes)])) 
                                       | ((IData)(vlSelf->bench__DOT__ddr_req_wstrb) 
                                          != vlSelf->bench__DOT__write_strobe
                                          [(0x1fffU 
                                            & vlSelf->bench__DOT__writes)]))))) {
                    VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:245: Assertion failed in %Nbench: BOOT_WRITE_TUPLE item=%0d addr=%x strobe=%x\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),32,
                              vlSelf->bench__DOT__writes,
                              64,vlSelf->bench__DOT__ddr_req_addr,
                              4,(IData)(vlSelf->bench__DOT__ddr_req_wstrb));
                    VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 245, "");
                }
                if ((1U & (IData)(vlSelf->bench__DOT__ddr_req_wstrb))) {
                    if (VL_UNLIKELY(((0xffU & vlSelf->bench__DOT__ddr_req_wdata) 
                                     != (0xffU & vlSelf->bench__DOT__write_data
                                         [(0x1fffU 
                                           & vlSelf->bench__DOT__writes)])))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:249: Assertion failed in %Nbench.unnamedblk4: BOOT_WRITE_DATA item=%0d expected=%x observed=%x\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name(),
                                  32,vlSelf->bench__DOT__writes,
                                  32,vlSelf->bench__DOT__write_data
                                  [(0x1fffU & vlSelf->bench__DOT__writes)],
                                  32,vlSelf->bench__DOT__ddr_req_wdata);
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 249, "");
                    }
                    vlSelf->bench__DOT__ddr[(0xffffU 
                                             & (IData)(vlSelf->bench__DOT__ddr_req_addr))] 
                        = (0xffU & vlSelf->bench__DOT__ddr_req_wdata);
                }
                if ((2U & (IData)(vlSelf->bench__DOT__ddr_req_wstrb))) {
                    if (VL_UNLIKELY(((0xffU & (vlSelf->bench__DOT__ddr_req_wdata 
                                               >> 8U)) 
                                     != (0xffU & (vlSelf->bench__DOT__write_data
                                                  [
                                                  (0x1fffU 
                                                   & vlSelf->bench__DOT__writes)] 
                                                  >> 8U))))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:249: Assertion failed in %Nbench.unnamedblk4: BOOT_WRITE_DATA item=%0d expected=%x observed=%x\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name(),
                                  32,vlSelf->bench__DOT__writes,
                                  32,vlSelf->bench__DOT__write_data
                                  [(0x1fffU & vlSelf->bench__DOT__writes)],
                                  32,vlSelf->bench__DOT__ddr_req_wdata);
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 249, "");
                    }
                    vlSelf->bench__DOT__ddr[(0xffffU 
                                             & ((IData)(1U) 
                                                + (IData)(vlSelf->bench__DOT__ddr_req_addr)))] 
                        = (0xffU & (vlSelf->bench__DOT__ddr_req_wdata 
                                    >> 8U));
                }
                if ((4U & (IData)(vlSelf->bench__DOT__ddr_req_wstrb))) {
                    if (VL_UNLIKELY(((0xffU & (vlSelf->bench__DOT__ddr_req_wdata 
                                               >> 0x10U)) 
                                     != (0xffU & (vlSelf->bench__DOT__write_data
                                                  [
                                                  (0x1fffU 
                                                   & vlSelf->bench__DOT__writes)] 
                                                  >> 0x10U))))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:249: Assertion failed in %Nbench.unnamedblk4: BOOT_WRITE_DATA item=%0d expected=%x observed=%x\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name(),
                                  32,vlSelf->bench__DOT__writes,
                                  32,vlSelf->bench__DOT__write_data
                                  [(0x1fffU & vlSelf->bench__DOT__writes)],
                                  32,vlSelf->bench__DOT__ddr_req_wdata);
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 249, "");
                    }
                    vlSelf->bench__DOT__ddr[(0xffffU 
                                             & ((IData)(2U) 
                                                + (IData)(vlSelf->bench__DOT__ddr_req_addr)))] 
                        = (0xffU & (vlSelf->bench__DOT__ddr_req_wdata 
                                    >> 0x10U));
                }
                if ((8U & (IData)(vlSelf->bench__DOT__ddr_req_wstrb))) {
                    if (VL_UNLIKELY(((vlSelf->bench__DOT__ddr_req_wdata 
                                      >> 0x18U) != 
                                     (vlSelf->bench__DOT__write_data
                                      [(0x1fffU & vlSelf->bench__DOT__writes)] 
                                      >> 0x18U)))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:249: Assertion failed in %Nbench.unnamedblk4: BOOT_WRITE_DATA item=%0d expected=%x observed=%x\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name(),
                                  32,vlSelf->bench__DOT__writes,
                                  32,vlSelf->bench__DOT__write_data
                                  [(0x1fffU & vlSelf->bench__DOT__writes)],
                                  32,vlSelf->bench__DOT__ddr_req_wdata);
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 249, "");
                    }
                    vlSelf->bench__DOT__ddr[(0xffffU 
                                             & ((IData)(3U) 
                                                + (IData)(vlSelf->bench__DOT__ddr_req_addr)))] 
                        = (vlSelf->bench__DOT__ddr_req_wdata 
                           >> 0x18U);
                }
                vlSelf->bench__DOT__writes = ((IData)(1U) 
                                              + vlSelf->bench__DOT__writes);
            } else {
                if (VL_UNLIKELY((1U & (((0x1138U != vlSelf->bench__DOT__writes) 
                                        | (~ ([&]() {
                                                __Vfunc_bench__DOT__readable__2__address 
                                                    = vlSelf->bench__DOT__ddr_req_addr;
                                                __Vfunc_bench__DOT__readable__2__Vfuncout = 0U;
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [1U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [1U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [1U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [2U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [2U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [2U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [3U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [3U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [3U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [4U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [4U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [4U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [5U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [5U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [5U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [6U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [6U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [6U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [7U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [7U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [7U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [8U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [8U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [8U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [9U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [9U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [9U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0xaU]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0xaU] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0xaU]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0xbU]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0xbU] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0xbU]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0xcU]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0xcU] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0xcU]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0xdU]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0xdU] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0xdU]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0xeU]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0xeU] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0xeU]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0xfU]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0xfU] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0xfU]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0x10U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0x10U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0x10U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0x11U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0x11U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0x11U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0x12U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0x12U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0x12U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                                if (
                                                    (((__Vfunc_bench__DOT__readable__2__address 
                                                       >= 
                                                       vlSelf->bench__DOT__segment_base
                                                       [0x13U]) 
                                                      & (__Vfunc_bench__DOT__readable__2__address 
                                                         < 
                                                         (vlSelf->bench__DOT__segment_base
                                                          [0x13U] 
                                                          + 
                                                          vlSelf->bench__DOT__segment_length
                                                          [0x13U]))) 
                                                     & (0U 
                                                        == 
                                                        (3U 
                                                         & (IData)(__Vfunc_bench__DOT__readable__2__address))))) {
                                                    __Vfunc_bench__DOT__readable__2__Vfuncout = 1U;
                                                }
                                            }(), (IData)(__Vfunc_bench__DOT__readable__2__Vfuncout)))) 
                                       | (0U != (IData)(vlSelf->bench__DOT__ddr_req_wstrb)))))) {
                    VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:257: Assertion failed in %Nbench: BOOT_VALIDATION_READ address=%x\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),64,
                              vlSelf->bench__DOT__ddr_req_addr);
                    VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 257, "");
                }
                vlSelf->bench__DOT__loading = 0U;
                vlSelf->bench__DOT__reads = ((IData)(1U) 
                                             + vlSelf->bench__DOT__reads);
            }
            vlSelf->bench__DOT__pending = 1U;
            vlSelf->bench__DOT__comparisons = ((IData)(1U) 
                                               + vlSelf->bench__DOT__comparisons);
        }
    }
    if (((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
         & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__fault)))) {
        if (((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__complete))) {
            __Vdlyvval__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__read_data;
            __Vdlyvset__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0 = 1U;
            __Vdlyvdim0__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0 
                = (7U & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component);
        }
        if (((0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__activation_reuse_valid))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activation_q 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations
                [(7U & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component)];
        }
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations[__Vdlyvdim0__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0] 
            = __Vdlyvval__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations__v0;
    }
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__13(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__13\n"); );
    // Body
    if ((1U & (~ (IData)(vlSelf->bench__DOT__spi_cs_n)))) {
        if (VL_GTS_III(32, 0x20U, vlSelf->bench__DOT__spi_command_bits)) {
            vlSelf->bench__DOT__command_shift = ((vlSelf->bench__DOT__command_shift 
                                                  << 1U) 
                                                 | ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
                                                    & ((1U 
                                                        == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state)) 
                                                       & (IData)(
                                                                 (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__command_shift 
                                                                  >> 0x27U)))));
            vlSelf->bench__DOT__spi_command_bits = 
                ((IData)(1U) + vlSelf->bench__DOT__spi_command_bits);
            if ((0x20U == vlSelf->bench__DOT__spi_command_bits)) {
                if (VL_UNLIKELY(((3U != (vlSelf->bench__DOT__command_shift 
                                         >> 0x18U)) 
                                 | (0x10000U <= (0xffffffU 
                                                 & vlSelf->bench__DOT__command_shift))))) {
                    VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:128: Assertion failed in %Nbench: BOOT_SPI_COMMAND %x\n",
                              64,VL_TIME_UNITED_Q(1000),
                              -9,vlSymsp->name(),32,
                              vlSelf->bench__DOT__command_shift);
                    VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 128, "");
                }
                vlSelf->bench__DOT__spi_reads = ((IData)(1U) 
                                                 + vlSelf->bench__DOT__spi_reads);
                vlSelf->bench__DOT__flash_address = 
                    (0xffffffU & vlSelf->bench__DOT__command_shift);
            }
        } else if ((7U == vlSelf->bench__DOT__flash_bit)) {
            vlSelf->bench__DOT__flash_address = ((IData)(1U) 
                                                 + vlSelf->bench__DOT__flash_address);
            vlSelf->bench__DOT__flash_bit = 0U;
        } else {
            vlSelf->bench__DOT__flash_bit = ((IData)(1U) 
                                             + vlSelf->bench__DOT__flash_bit);
        }
    }
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__7(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__7\n"); );
    // Init
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber17;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber17 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber16;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber16 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber15;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber15 = 0;
    CData/*2:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber14;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber14 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber13;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber13 = 0;
    CData/*3:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber12;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber12 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber11;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber11 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber9;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber9 = 0;
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0);
    VlWide<26>/*831:0*/ __Vtemp_42;
    VlWide<13>/*415:0*/ __Vtemp_66;
    // Body
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__in_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
           & ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)) 
              & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.out_valid)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____VdfgTmp_h115be047__0) 
           & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.in_ready));
    vlSelf->bench__DOT__dut__DOT__tokenizer_req_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
           & (((((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected)
                  ? ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__classify_selected)
                      ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__class_tbl_valid)
                      : ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__pool_selected)
                          ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__pool_tbl_valid)
                          : (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__record_tbl_valid)))
                  : ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected)
                      ? ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classify_selected)
                          ? (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_tbl_valid)
                          : (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_tbl_valid))
                      : ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_selected)
                          ? (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_tbl_valid)
                          : (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_tbl_valid)))) 
                << 3U) | ((((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__classify_selected)
                             ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__class_req)
                             : ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__edge_selected)
                                 ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__edge_req)
                                 : (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__record_req))) 
                           << 2U) | ((((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__classify_selected)
                                        ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__class_tbl_valid)
                                        : ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__pool_selected)
                                            ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__pool_tbl_valid)
                                            : (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__record_tbl_valid))) 
                                      << 1U) | ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__classify_selected)
                                                 ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__class_req)
                                                 : 
                                                ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__edge_selected)
                                                  ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__edge_req)
                                                  : (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__record_req)))))) 
              >> (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__ready 
        = (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.cmd_ready) 
            << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber4));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__finished 
        = (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.done) 
            << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber7));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__faults 
        = ((((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.done) 
             & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.__PVT__failed)) 
            << 1U) | ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber7) 
                      & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__failed)));
    __Vtemp_42[0U] = vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_wdata;
    __Vtemp_42[1U] = (IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_row)) 
                               << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_col))));
    __Vtemp_42[2U] = (IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_row)) 
                                << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_col))) 
                              >> 0x20U));
    __Vtemp_42[3U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_layer 
                       << 3U) | (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_proj));
    __Vtemp_42[4U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
                       << 9U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_valid) 
                                  << 8U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_write) 
                                             << 7U) 
                                            | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_kind) 
                                                << 3U) 
                                               | (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm.mem_req_layer 
                                                  >> 0x1dU)))));
    __Vtemp_42[5U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
                       >> 0x17U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber17)))) 
                                    << 9U));
    __Vtemp_42[6U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                 << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber17)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                               << 0x20U) 
                                              | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber17))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_42[7U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
                       << 0xcU) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber15) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber17))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_42[8U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
                       << 0x12U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber10) 
                                     << 0x11U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber12) 
                                                   << 0x10U) 
                                                  | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber13) 
                                                      << 0xcU) 
                                                     | (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
                                                        >> 0x14U)))));
    __Vtemp_42[9U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
                       >> 0xeU) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber16)))) 
                                   << 0x12U));
    __Vtemp_42[0xaU] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                   << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber16)))) 
                         >> 0xeU) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                                << 0x20U) 
                                               | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber16))) 
                                              >> 0x20U)) 
                                     << 0x12U));
    __Vtemp_42[0xbU] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
                         << 0x15U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber14) 
                                       << 0x12U) | 
                                      ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber16))) 
                                                >> 0x20U)) 
                                       >> 0xeU)));
    __Vtemp_42[0xcU] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
                         << 0x1bU) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber9) 
                                       << 0x1aU) | 
                                      (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber11) 
                                        << 0x19U) | 
                                       (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber12) 
                                         << 0x15U) 
                                        | (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
                                           >> 0xbU)))));
    __Vtemp_42[0xdU] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
                         >> 5U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber16)))) 
                                   << 0x1bU));
    __Vtemp_42[0xeU] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                   << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber16)))) 
                         >> 5U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber16))) 
                                            >> 0x20U)) 
                                   << 0x1bU));
    __Vtemp_42[0xfU] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
                         << 0x1eU) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber14) 
                                       << 0x1bU) | 
                                      ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber16))) 
                                                >> 0x20U)) 
                                       >> 5U)));
    __Vtemp_42[0x10U] = (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber12) 
                          << 0x1eU) | (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
                                       >> 2U));
    __Vtemp_42[0x11U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
                          << 4U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber9) 
                                     << 3U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber11) 
                                                << 2U) 
                                               | ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber12) 
                                                  >> 2U))));
    __Vtemp_42[0x12U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
                          >> 0x1cU) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                 << 0x20U) 
                                                | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber16)))) 
                                       << 4U));
    __Vtemp_42[0x13U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber16)))) 
                          >> 0x1cU) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber16))) 
                                                >> 0x20U)) 
                                       << 4U));
    __Vtemp_42[0x14U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
                          << 7U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber14) 
                                     << 4U) | ((IData)(
                                                       ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                          << 0x20U) 
                                                         | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber16))) 
                                                        >> 0x20U)) 
                                               >> 0x1cU)));
    __Vtemp_42[0x15U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
                          << 0xdU) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber9) 
                                       << 0xcU) | (
                                                   ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber11) 
                                                    << 0xbU) 
                                                   | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber12) 
                                                       << 7U) 
                                                      | (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
                                                         >> 0x19U)))));
    __Vtemp_42[0x16U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
                          >> 0x13U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                 << 0x20U) 
                                                | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber17)))) 
                                       << 0xdU));
    __Vtemp_42[0x17U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber17)))) 
                          >> 0x13U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber17))) 
                                                >> 0x20U)) 
                                       << 0xdU));
    __Vtemp_42[0x18U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
                          << 0x10U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber15) 
                                        << 0xdU) | 
                                       ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                   << 0x20U) 
                                                  | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber17))) 
                                                 >> 0x20U)) 
                                        >> 0x13U)));
    __Vtemp_42[0x19U] = (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber10) 
                          << 0x15U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber12) 
                                        << 0x14U) | 
                                       (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber13) 
                                         << 0x10U) 
                                        | (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
                                           >> 0x10U))));
    if ((0x335U >= (0x3ffU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected)))) {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_42[((IData)(1U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_42[(0x1fU & (((IData)(0x89U) 
                                        * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                       >> 5U))] >> 
                  (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_42[((IData)(2U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_42[((IData)(1U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_42[((IData)(3U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_42[((IData)(2U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_42[((IData)(4U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_42[((IData)(3U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected)))
                           ? 0U : (__Vtemp_42[((IData)(5U) 
                                               + (0x1fU 
                                                  & (((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                                     >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected))))) 
                         | (__Vtemp_42[((IData)(4U) 
                                        + (0x1fU & 
                                           (((IData)(0x89U) 
                                             * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected) 
                                            >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected)))));
    } else {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active) {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber9 
            = (1U & (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                     >> 8U));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber11 
            = (1U & (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                     >> 7U));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber12 
            = (0xfU & (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                       >> 3U));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber13 
            = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                << 0x1dU) | (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
                             >> 3U));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber14 
            = (7U & bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U]);
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber15 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber16 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber17 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U];
    } else {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber9 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber11 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber12 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber13 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber14 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber15 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber16 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber17 = 0U;
    }
    __Vtemp_66[0U] = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_wdata;
    __Vtemp_66[1U] = (IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_row)) 
                               << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_col))));
    __Vtemp_66[2U] = (IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_row)) 
                                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_col))) 
                              >> 0x20U));
    __Vtemp_66[3U] = ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_layer 
                       << 3U) | (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_proj));
    __Vtemp_66[4U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber17 
                       << 9U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_valid) 
                                  << 8U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_write) 
                                             << 7U) 
                                            | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_kind) 
                                                << 3U) 
                                               | (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_layer 
                                                  >> 0x1dU)))));
    __Vtemp_66[5U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber17 
                       >> 0x17U) | ((IData)((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber15)) 
                                              << 0x20U) 
                                             | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber16)))) 
                                    << 9U));
    __Vtemp_66[6U] = (((IData)((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber15)) 
                                 << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber16)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber15)) 
                                               << 0x20U) 
                                              | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber16))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_66[7U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber13 
                       << 0xcU) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber14) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber15)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber16))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_66[8U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_wdata 
                       << 0x12U) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber9) 
                                     << 0x11U) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber11) 
                                                   << 0x10U) 
                                                  | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber12) 
                                                      << 0xcU) 
                                                     | (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber13 
                                                        >> 0x14U)))));
    __Vtemp_66[9U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_wdata 
                       >> 0xeU) | ((IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_row)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_col)))) 
                                   << 0x12U));
    __Vtemp_66[0xaU] = (((IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_row)) 
                                   << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_col)))) 
                         >> 0xeU) | ((IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_row)) 
                                                << 0x20U) 
                                               | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_col))) 
                                              >> 0x20U)) 
                                     << 0x12U));
    __Vtemp_66[0xbU] = ((vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_layer 
                         << 0x15U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_proj) 
                                       << 0x12U) | 
                                      ((IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_row)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_col))) 
                                                >> 0x20U)) 
                                       >> 0xeU)));
    __Vtemp_66[0xcU] = (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_valid) 
                         << 0x1aU) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_write) 
                                       << 0x19U) | 
                                      (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_kind) 
                                        << 0x15U) | 
                                       (vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm.mem_req_layer 
                                        >> 0xbU))));
    if ((0x19aU >= (0x1ffU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected)))) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected)))
                 ? 0U : (__Vtemp_66[((IData)(1U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))))) 
               | (__Vtemp_66[(0xfU & (((IData)(0x89U) 
                                       * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                      >> 5U))] >> (0x1fU 
                                                   & ((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected)))
                 ? 0U : (__Vtemp_66[((IData)(2U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))))) 
               | (__Vtemp_66[((IData)(1U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected)))
                 ? 0U : (__Vtemp_66[((IData)(3U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))))) 
               | (__Vtemp_66[((IData)(2U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected)))
                 ? 0U : (__Vtemp_66[((IData)(4U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))))) 
               | (__Vtemp_66[((IData)(3U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected)))
                           ? 0U : (__Vtemp_66[((IData)(5U) 
                                               + (0xfU 
                                                  & (((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                                     >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected))))) 
                         | (__Vtemp_66[((IData)(4U) 
                                        + (0xfU & (
                                                   ((IData)(0x89U) 
                                                    * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected) 
                                                   >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected)))));
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____Vcellinp__tensor_mapper__mem_req_valid 
        = ((~ (IData)(vlSelf->bench__DOT__dut__DOT__abort_r)) 
           & ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active) 
              & (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                 >> 8U)));
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__12(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__12\n"); );
    // Init
    CData/*0:0*/ bench__DOT__dut__DOT__tokenizer_req_ready;
    bench__DOT__dut__DOT__tokenizer_req_ready = 0;
    // Body
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_accept 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__abort_r) 
            & (3U != (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner))) 
           | (((0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)) 
               & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_ready)) 
              | (((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)) 
                  & ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
                     & (((((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected)
                            ? ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__classify_selected)
                                ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__class_tbl_ready)
                                : ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__pool_selected)
                                    ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__pool_tbl_ready)
                                    : (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization.__PVT__normalizer__DOT__record_tbl_ready)))
                            : ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected)
                                ? ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classify_selected)
                                    ? (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_tbl_ready)
                                    : (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_tbl_ready))
                                : ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_selected)
                                    ? (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_tbl_ready)
                                    : (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_tbl_ready)))) 
                          << 3U) | ((((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__classify_selected)
                                       ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__class_rsp_ready)
                                       : ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__edge_selected)
                                           ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__edge_rsp_ready)
                                           : (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials.__PVT__splitter__DOT__record_rsp_ready))) 
                                     << 2U) | ((((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__classify_selected)
                                                  ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__class_tbl_ready)
                                                  : 
                                                 ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__pool_selected)
                                                   ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__pool_tbl_ready)
                                                   : (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization.__PVT__normalizer__DOT__record_tbl_ready))) 
                                                << 1U) 
                                               | ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__classify_selected)
                                                   ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__class_rsp_ready)
                                                   : 
                                                  ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__edge_selected)
                                                    ? (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__edge_rsp_ready)
                                                    : (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials.__PVT__splitter__DOT__record_rsp_ready)))))) 
                        >> (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)))) 
                 | (((2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_ready)) 
                    | ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)) 
                       & ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
                          & ((5U >= (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected))
                              ? ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__special_trie__ddr_rsp_ready) 
                                   << 5U) | (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__profile__ddr_rsp_ready) 
                                              << 4U) 
                                             | (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__tokens__ddr_rsp_ready) 
                                                 << 3U) 
                                                | (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__directory__ddr_rsp_ready) 
                                                    << 2U) 
                                                   | (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__manifest__ddr_rsp_ready) 
                                                       << 1U) 
                                                      | (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__image_loader__ddr_rsp_ready)))))) 
                                 >> (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected))
                              : (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__1))))))));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 0U;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state)))) {
        if (vlSelf->bench__DOT__dut__DOT__loader_done) {
            if (vlSelf->bench__DOT__dut__DOT__abort_r) {
                if (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_valid) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 0U;
                }
            } else if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__priority_owner))) {
                if (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_valid) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 0U;
                } else if (vlSelf->bench__DOT__dut__DOT__tokenizer_req_valid) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 1U;
                } else if (vlSelf->bench__DOT__dut__DOT__detokenizer_req_valid) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 2U;
                }
            } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__priority_owner))) {
                if (vlSelf->bench__DOT__dut__DOT__tokenizer_req_valid) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 1U;
                } else if (vlSelf->bench__DOT__dut__DOT__detokenizer_req_valid) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 2U;
                } else if (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_valid) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 0U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__detokenizer_req_valid) {
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 2U;
            } else if (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_valid) {
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 0U;
            } else if (vlSelf->bench__DOT__dut__DOT__tokenizer_req_valid) {
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 1U;
            }
        } else if ((((~ (IData)(vlSelf->bench__DOT__dut__DOT__loader_done)) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__boot_req_valid)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_idle))) {
            vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = 1U;
            vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = 3U;
        }
    }
    vlSelf->bench__DOT__dut__DOT__boot_req_ready = 
        ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid) 
         & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner)));
    bench__DOT__dut__DOT__tokenizer_req_ready = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid) 
                                                 & (1U 
                                                    == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_req_ready 
        = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)) 
           & (IData)(bench__DOT__dut__DOT__tokenizer_req_ready));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_req_ready 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)) 
           & (IData)(bench__DOT__dut__DOT__tokenizer_req_ready));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_req_ready 
        = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)) 
           & (IData)(bench__DOT__dut__DOT__tokenizer_req_ready));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_req_ready 
        = ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)) 
           & (IData)(bench__DOT__dut__DOT__tokenizer_req_ready));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_req_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_req_ready));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__tbl_req_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_req_ready));
}

void Vbench___024root___nba_sequent__TOP__0(Vbench___024root* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench___024root___nba_sequent__TOP__1(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__2(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__3(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__4(Vbench___024root* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench___024root___nba_sequent__TOP__5(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__6(Vbench___024root* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_edge_special_splitter__pi7___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf);
void Vbench_anvil_edge_special_splitter__pi7___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf);
void Vbench_anvil_edge_normalizer__M10___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf);
void Vbench_anvil_edge_normalizer__M10___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier__1(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench___024root___nba_sequent__TOP__8(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__10(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__11(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__12(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__0(Vbench___024root* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___nba_comb__TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench___024root___nba_sequent__TOP__14(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__15(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__16(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__17(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__18(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__1(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__2(Vbench___024root* vlSelf);
void Vbench___024root___nba_sequent__TOP__19(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__3(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__4(Vbench___024root* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench___024root___nba_comb__TOP__5(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__6(Vbench___024root* vlSelf);
void Vbench_anvil_edge_special_splitter__pi7___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf);
void Vbench_anvil_edge_special_splitter__pi7___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf);
void Vbench_anvil_edge_normalizer__M10___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf);
void Vbench_anvil_edge_normalizer__M10___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench___024root___nba_comb__TOP__8(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__9(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__10(Vbench___024root* vlSelf);
void Vbench___024root___nba_comb__TOP__11(Vbench___024root* vlSelf);

void Vbench___024root___eval_nba(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_nba\n"); );
    // Body
    if ((0x40ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__0(vlSelf);
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier));
        Vbench___024root___nba_sequent__TOP__1(vlSelf);
    }
    if ((0x80ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__2(vlSelf);
    }
    if ((0x20ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__3(vlSelf);
    }
    if ((0x200ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__4(vlSelf);
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply__0((&vlSymsp->TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply));
        Vbench___024root___nba_sequent__TOP__5(vlSelf);
    }
    if ((0x100ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__6(vlSelf);
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm));
        Vbench_anvil_edge_special_splitter__pi7___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials));
        Vbench_anvil_edge_special_splitter__pi7___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials));
        Vbench_anvil_edge_normalizer__M10___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization));
        Vbench_anvil_edge_normalizer__M10___nba_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier));
        Vbench___024root___nba_sequent__TOP__7(vlSelf);
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier__1((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier__1((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___nba_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier__1((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench___024root___nba_sequent__TOP__8(vlSelf);
    }
    if ((2ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__9(vlSelf);
    }
    if ((4ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__10(vlSelf);
    }
    if ((0x10ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__11(vlSelf);
    }
    if ((1ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__12(vlSelf);
    }
    if ((8ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__13(vlSelf);
    }
    if ((0x443ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__0(vlSelf);
        Vbench_anvil_edge_signed_multiplier__pi23___nba_comb__TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier));
    }
    if ((0x40ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__14(vlSelf);
    }
    if ((0x80ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__15(vlSelf);
    }
    if ((0x100ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__16(vlSelf);
    }
    if ((0x20ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__17(vlSelf);
    }
    if ((0x200ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__18(vlSelf);
    }
    if ((0x543ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__1(vlSelf);
    }
    if ((0x443ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__2(vlSelf);
    }
    if ((0x40ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_sequent__TOP__19(vlSelf);
    }
    if ((0x463ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__3(vlSelf);
    }
    if ((0x643ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__4(vlSelf);
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply__0((&vlSymsp->TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply));
    }
    if ((0x4c3ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__5(vlSelf);
    }
    if ((0x543ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__6(vlSelf);
        Vbench_anvil_edge_special_splitter__pi7___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials));
        Vbench_anvil_edge_special_splitter__pi7___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials));
        Vbench_anvil_edge_normalizer__M10___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization));
        Vbench_anvil_edge_normalizer__M10___act_comb__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm));
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___act_comb__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench___024root___nba_comb__TOP__7(vlSelf);
    }
    if ((0x443ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__8(vlSelf);
    }
    if ((0x403ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__9(vlSelf);
    }
    if ((0x5c3ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__10(vlSelf);
    }
    if ((0x5e3ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__11(vlSelf);
    }
    if ((0x743ULL & vlSelf->__VnbaTriggered.word(0U))) {
        Vbench___024root___nba_comb__TOP__12(vlSelf);
    }
}
