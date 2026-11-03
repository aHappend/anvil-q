// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench___024root.h"

VL_INLINE_OPT VlCoroutine Vbench___024root___eval_initial__TOP__Vtiming__2(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_initial__TOP__Vtiming__2\n"); );
    // Body
    while (1U) {
        co_await vlSelf->__VdlySched.delay(0x1388ULL, 
                                           nullptr, 
                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                           31);
        vlSelf->bench__DOT__clk = (1U & (~ (IData)(vlSelf->bench__DOT__clk)));
    }
}

VL_INLINE_OPT void Vbench___024root___act_comb__TOP__0(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___act_comb__TOP__0\n"); );
    // Init
    CData/*0:0*/ bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18;
    bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21;
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20;
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18;
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10;
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle = 0;
    VlWide<5>/*128:0*/ bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient;
    VL_ZERO_W(129, bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle = 0;
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0);
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle = 0;
    VlWide<5>/*159:0*/ __Vtemp_4;
    VlWide<9>/*287:0*/ __Vtemp_19;
    // Body
    if (vlSelf->bench__DOT__rst_n) {
        vlSelf->bench__DOT__token_ready = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__state));
        vlSelf->bench__DOT__logit_valid = (0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__state));
        vlSelf->bench__DOT__dut__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber8 
            = (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 
            = (0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber7 
            = (0x23U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber7 
            = (0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 
            = (0x17U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid 
            = (4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_error 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__logit_index = vlSelf->bench__DOT__dut__DOT__vocabulary;
        vlSelf->bench__DOT__logit_data = vlSelf->bench__DOT__dut__DOT__result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_value 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[3U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result;
        if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a 
                = (((- (QData)((IData)((1U & ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__delta) 
                                              >> 4U))))) 
                    << 5U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__delta)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b 
                = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scale_integer));
        } else if ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a 
                = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation 
                                                >> 0x1fU))))) 
                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b 
                = (((QData)((IData)((0x7ffffffU & (- (IData)(
                                                             (1U 
                                                              & (IData)(
                                                                        (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__dequantized_weight 
                                                                         >> 0x24U)))))))) 
                    << 0x25U) | vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__dequantized_weight);
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__cosine;
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__sine;
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__cosine;
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__sine;
        }
        if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a 
                = (((- (QData)((IData)((1U & ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta) 
                                              >> 4U))))) 
                    << 5U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b 
                = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scale_integer));
        } else if ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a 
                = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation 
                                                >> 0x1fU))))) 
                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b 
                = (((QData)((IData)((0x7ffffffU & (- (IData)(
                                                             (1U 
                                                              & (IData)(
                                                                        (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight 
                                                                         >> 0x24U)))))))) 
                    << 0x25U) | vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight);
        }
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[0U];
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[1U];
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[2U];
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[3U];
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[4U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_kind 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_proj 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_wdata 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__done = (0x16U == (IData)(vlSelf->bench__DOT__dut__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber7 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 
            = (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 
            = (0x17U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__port_idle = (0U 
                                                   == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_write 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active 
            = (3U > vlSelf->bench__DOT__dut__DOT__selected);
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active 
            = (6U > vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected);
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active 
            = (2U > ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                      ? 1U : 0U));
    } else {
        vlSelf->bench__DOT__token_ready = 0U;
        vlSelf->bench__DOT__logit_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_error = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__logit_index = 0U;
        vlSelf->bench__DOT__logit_data = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_value = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U] = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U] = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U] = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U] = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_kind = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_proj = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_wdata = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18 = 0U;
        vlSelf->bench__DOT__done = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber7 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_write = 0U;
        vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active = 0U;
    }
    vlSelf->bench__DOT__error = ((IData)(vlSelf->bench__DOT__done) 
                                 & (IData)(vlSelf->bench__DOT__dut__DOT__failed));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor));
    VL_NEGATE_W(5, __Vtemp_4, bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U] 
            = __Vtemp_4[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U] 
            = __Vtemp_4[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U] 
            = __Vtemp_4[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U] 
            = __Vtemp_4[3U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[4U] 
            = (1U & __Vtemp_4[4U]);
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U] 
            = bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U] 
            = bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U] 
            = bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U] 
            = bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[4U] 
            = (1U & bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U]);
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__ready 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4) 
            << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__finished 
        = (((IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8) 
            << 1U) | (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__faults 
        = ((((IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed)) 
            << 1U) | ((IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8) 
                      & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle))) {
        if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 0U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 7U : 9U));
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 6U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 0xcU : 0xaU));
        } else if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 7U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 0U : 0xbU));
        }
        if ((1U != (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            if ((3U != (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__output_value;
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_data = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle))) {
        if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                    ? 0U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                             ? 7U : 9U));
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                    ? 6U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                             ? 0xcU : 0xaU));
        } else if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                    ? 7U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                             ? 0U : 0xbU));
        }
        if ((1U != (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            if ((3U != (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_request = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_data 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__output_value;
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request 
                                = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                                   | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data 
                                = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y
                                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x);
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                                = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector)
                                    ? 3U : 2U);
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                                = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                                    | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))
                                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y
                                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 8U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request 
                            = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                               | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data 
                            = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                                ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y
                                : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                            = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector)
                                ? 3U : 2U);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                            = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                                | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))
                                ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y
                                : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
                    }
                }
            } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                                 >> 1U)))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 0xbU;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__position;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                        = (VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index, 1U) 
                           + ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                               ? 1U : 0U));
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 0xbU;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__position;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                        = (VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index, 1U) 
                           + ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                               ? 1U : 0U));
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 8U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                    = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector)
                        ? 3U : 2U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                    = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                        | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))
                        ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y
                        : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                          >> 1U)))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request 
                        = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                           | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data 
                        = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y
                            : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x);
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 8U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request 
                    = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                       | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data 
                    = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                        ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y
                        : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                    = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector)
                        ? 3U : 2U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                    = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                        | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))
                        ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y
                        : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(vlSelf->bench__DOT__dut__DOT__port_idle))) {
        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                      >> 4U)))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__activation;
                        }
                    }
                }
            }
            if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__kind = 0U;
                            vlSelf->bench__DOT__dut__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__component;
                            vlSelf->bench__DOT__dut__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__vocabulary;
                        }
                    }
                } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__activation_reuse_valid)))) {
                            vlSelf->bench__DOT__dut__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__component;
                            vlSelf->bench__DOT__dut__DOT__row = 0xeU;
                        }
                    }
                }
            } else {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__component;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__kind = 0U;
                        vlSelf->bench__DOT__dut__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__component;
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__token;
                        }
                    }
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle))) {
        if ((0x20U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                                  >> 2U)))) {
                        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                                      >> 1U)))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_request = 1U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 8U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_data 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__output_value;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row = 5U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                                    = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base 
                                       + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component);
                            }
                        }
                    }
                }
            }
        } else {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                                      >> 1U)))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_request = 1U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_data 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data;
                            }
                        }
                    }
                }
            }
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 0xaU;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                                    = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base 
                                       + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component);
                            }
                        }
                    }
                }
            } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 9U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__k_column;
                        }
                    } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 8U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row = 2U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q_column;
                    }
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind 
                            = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache)
                                ? 0xaU : 9U);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__position;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index;
                    }
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache)
                            ? 4U : 3U);
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index;
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                      >> 5U)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer;
                            }
                        }
                    }
                }
            } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer;
                        }
                    }
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer;
                    }
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__output_value;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c 
                                   + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane));
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 4U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                            = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c 
                               + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane));
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer;
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                            = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c, 3U);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k;
                    }
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot;
                }
            } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 3U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                    = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c 
                       + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane));
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index;
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer;
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 2U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                    = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c, 3U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__output_value;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                                   + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 4U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                            = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                               + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                            = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c, 3U);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k;
                    }
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot;
                }
            } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 3U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                    = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                       + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index;
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 2U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                    = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c, 3U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h6323ea89__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) 
           & (2U == vlSelf->bench__DOT__dut__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h632b4bf4__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) 
           & (0U == vlSelf->bench__DOT__dut__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h62f58b69__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) 
           & (1U == vlSelf->bench__DOT__dut__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (5U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (3U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (2U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (1U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (0U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (4U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    __Vtemp_19[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18;
    __Vtemp_19[1U] = (IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                               << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))));
    __Vtemp_19[2U] = (IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))) 
                              >> 0x20U));
    __Vtemp_19[3U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                       << 3U) | (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15));
    __Vtemp_19[4U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                       << 9U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10) 
                                  << 8U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12) 
                                             << 7U) 
                                            | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13) 
                                                << 3U) 
                                               | (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                                                  >> 0x1dU)))));
    __Vtemp_19[5U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                       >> 0x17U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                                    << 9U));
    __Vtemp_19[6U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                 << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                               << 0x20U) 
                                              | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_19[7U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
                       << 0xcU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_19[8U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10) 
                       << 0x11U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12) 
                                     << 0x10U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13) 
                                                   << 0xcU) 
                                                  | (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
                                                     >> 0x14U))));
    if ((0x111U >= (0x1ffU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                 ? 1U
                                                 : 0U))))) {
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_19[((IData)(1U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_19[(0xfU & (((IData)(0x89U) 
                                       * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                           ? 1U : 0U)) 
                                      >> 5U))] >> (0x1fU 
                                                   & ((IData)(0x89U) 
                                                      * 
                                                      ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                        ? 1U
                                                        : 0U)))));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_19[((IData)(2U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_19[((IData)(1U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_19[((IData)(3U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_19[((IData)(2U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_19[((IData)(4U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_19[((IData)(3U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                               ? 1U
                                               : 0U))))
                           ? 0U : (__Vtemp_19[((IData)(5U) 
                                               + (0xfU 
                                                  & (((IData)(0x89U) 
                                                      * 
                                                      ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                        ? 1U
                                                        : 0U)) 
                                                     >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * 
                                                   ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                     ? 1U
                                                     : 0U)))))) 
                         | (__Vtemp_19[((IData)(4U) 
                                        + (0xfU & (
                                                   ((IData)(0x89U) 
                                                    * 
                                                    ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                      ? 1U
                                                      : 0U)) 
                                                   >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                             ? 1U : 0U))))));
    } else {
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) 
           & (1U == ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                      ? 1U : 0U)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) 
           & (0U == ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                      ? 1U : 0U)));
    if (vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h6323ea89__0) {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber11 
            = vlSelf->bench__DOT__mem_req_ready;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber21 
            = vlSelf->bench__DOT__mem_rsp_rdata;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber22 
            = vlSelf->bench__DOT__mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber19 
            = vlSelf->bench__DOT__mem_rsp_valid;
    } else {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber22 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber19 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h632b4bf4__0) {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_req_ready 
            = vlSelf->bench__DOT__mem_req_ready;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_rdata 
            = vlSelf->bench__DOT__mem_rsp_rdata;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_error 
            = vlSelf->bench__DOT__mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_valid 
            = vlSelf->bench__DOT__mem_rsp_valid;
    } else {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_req_ready = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_rdata = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_error = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_valid = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h62f58b69__0) {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10 
            = vlSelf->bench__DOT__mem_req_ready;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21 
            = vlSelf->bench__DOT__mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20 
            = vlSelf->bench__DOT__mem_rsp_rdata;
        bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18 
            = vlSelf->bench__DOT__mem_rsp_valid;
    } else {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20 = 0U;
        bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 
            = (1U & (bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                     >> 8U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 
            = (1U & (bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                     >> 7U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 
            = (0xfU & (bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                       >> 3U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
            = ((bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                << 0x1dU) | (bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
                             >> 3U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 
            = (7U & bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U]);
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 
            = bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 
            = bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
            = bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U];
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__complete = ((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready) 
                                              & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber10 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber10 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10));
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber21 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber21 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber22 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber22 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21));
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber21 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0)
            ? vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0)
            ? vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber20 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0)
            ? vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber20 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0)
            ? vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber21 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0)
            ? vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0)
            ? vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber18 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber18 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    if (vlSelf->bench__DOT__dut__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__fault = vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT__read_data = vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_rdata;
    } else {
        vlSelf->bench__DOT__dut__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__read_data = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber22 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21));
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22 
            = bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21 
            = bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21 = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0)
            ? bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete)
            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete)
            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete)
            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber21
            : 0U);
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete)
            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21
            : 0U);
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data = 0U;
    }
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__2(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__2\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order) 
                                             << 0x18U))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order) 
                                             << 0x18U))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order) 
                                             << 0x18U))));
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__3(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__3\n"); );
    // Init
    CData/*2:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__head_activations__v0;
    __Vdlyvdim0__bench__DOT__dut__DOT__head_activations__v0 = 0;
    IData/*31:0*/ __Vdlyvval__bench__DOT__dut__DOT__head_activations__v0;
    __Vdlyvval__bench__DOT__dut__DOT__head_activations__v0 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__head_activations__v0;
    __Vdlyvset__bench__DOT__dut__DOT__head_activations__v0 = 0;
    // Body
    __Vdlyvset__bench__DOT__dut__DOT__head_activations__v0 = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (~ (IData)(vlSelf->bench__DOT__dut__DOT__fault)))) {
        if (((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__complete))) {
            __Vdlyvval__bench__DOT__dut__DOT__head_activations__v0 
                = vlSelf->bench__DOT__dut__DOT__read_data;
            __Vdlyvset__bench__DOT__dut__DOT__head_activations__v0 = 1U;
            __Vdlyvdim0__bench__DOT__dut__DOT__head_activations__v0 
                = (7U & vlSelf->bench__DOT__dut__DOT__component);
        }
        if (((0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__activation_reuse_valid))) {
            vlSelf->bench__DOT__dut__DOT__head_activation_q 
                = vlSelf->bench__DOT__dut__DOT__head_activations
                [0U];
        }
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__head_activations__v0) {
        vlSelf->bench__DOT__dut__DOT__head_activations[__Vdlyvdim0__bench__DOT__dut__DOT__head_activations__v0] 
            = __Vdlyvval__bench__DOT__dut__DOT__head_activations__v0;
    }
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__5(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__5\n"); );
    // Body
    if (vlSelf->bench__DOT__rst_n) {
        vlSelf->bench__DOT__rng = (vlSelf->bench__DOT__rng 
                                   ^ VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__rng, 0xdU));
        vlSelf->bench__DOT__rng = (vlSelf->bench__DOT__rng 
                                   ^ VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__rng, 0x11U));
        vlSelf->bench__DOT__rng = (vlSelf->bench__DOT__rng 
                                   ^ VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__rng, 5U));
        vlSelf->bench__DOT__mem_req_ready = (vlSelf->bench__DOT__rng 
                                             & (0U 
                                                != 
                                                VL_MODDIVS_III(32, vlSelf->bench__DOT__cycles, (IData)(7U))));
        vlSelf->bench__DOT__logit_ready = ((vlSelf->bench__DOT__rng 
                                            >> 1U) 
                                           & (0U != 
                                              VL_MODDIVS_III(32, vlSelf->bench__DOT__cycles, (IData)(5U))));
        if (((IData)(vlSelf->bench__DOT__pending) & 
             (~ (IData)(vlSelf->bench__DOT__mem_rsp_valid)))) {
            if ((0U == vlSelf->bench__DOT__delay_count)) {
                vlSelf->bench__DOT__mem_rsp_rdata = 
                    ((0x1feU >= (0x1ffU & vlSelf->bench__DOT__pending_slot))
                      ? vlSelf->bench__DOT__memory[
                     (0x1ffU & vlSelf->bench__DOT__pending_slot)]
                      : vlSelf->bench__DOT____Vxrand_h8d93fe75__0);
                vlSelf->bench__DOT__mem_rsp_error = 
                    (((0U != vlSelf->bench__DOT__fault_config
                       [0U]) & (0U != vlSelf->bench__DOT__fault_config
                                [2U])) & (vlSelf->bench__DOT__pending_slot 
                                          == vlSelf->bench__DOT__fault_config
                                          [1U]));
                if (((0U != vlSelf->bench__DOT__fault_config
                      [0U]) & (vlSelf->bench__DOT__pending_slot 
                               == vlSelf->bench__DOT__fault_config
                               [1U]))) {
                    vlSelf->bench__DOT__injected_responses 
                        = ((IData)(1U) + vlSelf->bench__DOT__injected_responses);
                }
                vlSelf->__Vdly__bench__DOT__mem_rsp_valid = 1U;
            } else {
                vlSelf->bench__DOT__delay_count = (vlSelf->bench__DOT__delay_count 
                                                   - (IData)(1U));
            }
        }
    }
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__0(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__0\n"); );
    // Init
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle = 0;
    VlWide<5>/*128:0*/ bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient;
    VL_ZERO_W(129, bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle = 0;
    VlWide<5>/*159:0*/ __Vtemp_4;
    // Body
    if (vlSelf->bench__DOT__rst_n) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_write 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__port_idle = (0U 
                                                   == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wr;
        bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wr;
        bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wr;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wr;
        bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wr;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wr;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 
            = (0x17U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber7 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_error 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid 
            = (4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber7 
            = (0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 
            = (0x17U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 
            = (0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber8 
            = (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = 0ULL;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[0U];
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[1U];
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[2U];
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[3U];
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[4U];
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_kind 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_proj 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_wdata 
            = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[3U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_value 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_result;
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__cosine;
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__sine;
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__cosine;
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__sine;
        }
        if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a 
                = (((- (QData)((IData)((1U & ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__delta) 
                                              >> 4U))))) 
                    << 5U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__delta)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b 
                = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scale_integer));
        } else if ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a 
                = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation 
                                                >> 0x1fU))))) 
                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b 
                = (((QData)((IData)((0x7ffffffU & (- (IData)(
                                                             (1U 
                                                              & (IData)(
                                                                        (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__dequantized_weight 
                                                                         >> 0x24U)))))))) 
                    << 0x25U) | vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__dequantized_weight);
        }
        if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a 
                = (((- (QData)((IData)((1U & ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta) 
                                              >> 4U))))) 
                    << 5U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b 
                = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scale_integer));
        } else if ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a 
                = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation 
                                                >> 0x1fU))))) 
                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b 
                = (((QData)((IData)((0x7ffffffU & (- (IData)(
                                                             (1U 
                                                              & (IData)(
                                                                        (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight 
                                                                         >> 0x24U)))))))) 
                    << 0x25U) | vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight);
        }
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber7 
            = (0x23U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state));
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 
            = (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state));
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_write = 0U;
        vlSelf->bench__DOT__dut__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber12 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber11 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber11 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_error = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = 0ULL;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U] = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U] = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U] = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U] = 0U;
        bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_kind = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_proj = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_wdata = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_value = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4 = 0U;
        bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid = 0U;
    }
    VL_NEGATE_W(5, __Vtemp_4, bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U] 
            = __Vtemp_4[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U] 
            = __Vtemp_4[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U] 
            = __Vtemp_4[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U] 
            = __Vtemp_4[3U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[4U] 
            = (1U & __Vtemp_4[4U]);
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U] 
            = bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U] 
            = bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U] 
            = bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U] 
            = bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[4U] 
            = (1U & bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U]);
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_data = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle))) {
        if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                    ? 0U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                             ? 7U : 9U));
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                    ? 6U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                             ? 0xcU : 0xaU));
        } else if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                    ? 7U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                             ? 0U : 0xbU));
        }
        if ((1U != (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            if ((3U != (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_request = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_data 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__output_value;
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request 
                                = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                                   | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data 
                                = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y
                                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x);
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                                = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector)
                                    ? 3U : 2U);
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                                = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                                    | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))
                                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y
                                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 8U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request 
                            = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                               | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data 
                            = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                                ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y
                                : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                            = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector)
                                ? 3U : 2U);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                            = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                                | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))
                                ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y
                                : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
                    }
                }
            } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                                 >> 1U)))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 0xbU;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__position;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                        = (VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index, 1U) 
                           + ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                               ? 1U : 0U));
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 0xbU;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__position;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                        = (VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index, 1U) 
                           + ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                               ? 1U : 0U));
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 8U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                    = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector)
                        ? 3U : 2U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                    = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                        | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))
                        ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y
                        : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state) 
                          >> 1U)))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request 
                        = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                           | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data 
                        = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y
                            : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x);
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = 8U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request 
                    = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                       | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data 
                    = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                        ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y
                        : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row 
                    = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector)
                        ? 3U : 2U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col 
                    = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
                        | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))
                        ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y
                        : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle))) {
        if ((0x20U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                                  >> 2U)))) {
                        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                                      >> 1U)))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_request = 1U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 8U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_data 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__output_value;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row = 5U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                                    = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base 
                                       + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component);
                            }
                        }
                    }
                }
            }
        } else {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                                      >> 1U)))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_request = 1U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_data 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data;
                            }
                        }
                    }
                }
            }
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 0xaU;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index;
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                                    = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base 
                                       + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component);
                            }
                        }
                    }
                }
            } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 9U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__k_column;
                        }
                    } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 8U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row = 2U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q_column;
                    }
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind 
                            = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache)
                                ? 0xaU : 9U);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__position;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index;
                    }
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache)
                            ? 4U : 3U);
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index;
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                      >> 5U)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer;
                            }
                        }
                    }
                }
            } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer;
                        }
                    }
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer;
                    }
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__output_value;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c 
                                   + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane));
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 4U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                            = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c 
                               + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane));
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer;
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                            = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c, 3U);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k;
                    }
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot;
                }
            } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 3U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                    = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c 
                       + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane));
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index;
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer;
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = 2U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col 
                    = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c, 3U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle))) {
        if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 0U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 7U : 9U));
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 6U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 0xcU : 0xaU));
        } else if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 7U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 0U : 0xbU));
        }
        if ((1U != (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            if ((3U != (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__output_value;
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__output_value;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                                   + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 4U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                            = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                               + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                            = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c, 3U);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k;
                    }
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot;
                }
            } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 3U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                    = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                       + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index;
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 2U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                    = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c, 3U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__ready 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4) 
            << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__finished 
        = (((IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8) 
            << 1U) | (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__faults 
        = ((((IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed)) 
            << 1U) | ((IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8) 
                      & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed)));
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__6(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__6\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__component = vlSelf->__Vdly__bench__DOT__dut__DOT__component;
    vlSelf->bench__DOT__dut__DOT__activation_reuse_valid 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid;
    vlSelf->bench__DOT__dut__DOT__state = vlSelf->__Vdly__bench__DOT__dut__DOT__state;
    vlSelf->__VdfgTmp_h5391f0e0__0 = ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                      | (7U == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->__VdfgTmp_h930fe3f0__0 = ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                      | (9U == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__selected = ((IData)(vlSelf->__VdfgTmp_h5391f0e0__0)
                                               ? 1U
                                               : ((IData)(vlSelf->__VdfgTmp_h930fe3f0__0)
                                                   ? 2U
                                                   : 0U));
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__2(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__2\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__rst_n) & (IData)(vlSelf->bench__DOT__dut__DOT__port_idle))) {
        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                      >> 4U)))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__activation;
                        }
                    }
                }
            }
            if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__kind = 0U;
                            vlSelf->bench__DOT__dut__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__component;
                            vlSelf->bench__DOT__dut__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__vocabulary;
                        }
                    }
                } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__activation_reuse_valid)))) {
                            vlSelf->bench__DOT__dut__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__component;
                            vlSelf->bench__DOT__dut__DOT__row = 0xeU;
                        }
                    }
                }
            } else {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__component;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__kind = 0U;
                        vlSelf->bench__DOT__dut__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__component;
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__token;
                        }
                    }
                }
            }
        }
    }
    if (vlSelf->bench__DOT__rst_n) {
        vlSelf->bench__DOT__logit_index = vlSelf->bench__DOT__dut__DOT__vocabulary;
        vlSelf->bench__DOT__logit_data = vlSelf->bench__DOT__dut__DOT__result;
        vlSelf->bench__DOT__done = (0x16U == (IData)(vlSelf->bench__DOT__dut__DOT__state));
        vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active 
            = (3U > vlSelf->bench__DOT__dut__DOT__selected);
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__logit_valid = (0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__state));
        vlSelf->bench__DOT__token_ready = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__state));
    } else {
        vlSelf->bench__DOT__logit_index = 0U;
        vlSelf->bench__DOT__logit_data = 0U;
        vlSelf->bench__DOT__done = 0U;
        vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready = 0U;
        vlSelf->bench__DOT__logit_valid = 0U;
        vlSelf->bench__DOT__token_ready = 0U;
    }
    vlSelf->bench__DOT__error = ((IData)(vlSelf->bench__DOT__done) 
                                 & (IData)(vlSelf->bench__DOT__dut__DOT__failed));
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h6323ea89__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) 
           & (2U == vlSelf->bench__DOT__dut__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h632b4bf4__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) 
           & (0U == vlSelf->bench__DOT__dut__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h62f58b69__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) 
           & (1U == vlSelf->bench__DOT__dut__DOT__selected));
    if (vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h6323ea89__0) {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber11 
            = vlSelf->bench__DOT__mem_req_ready;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber21 
            = vlSelf->bench__DOT__mem_rsp_rdata;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber22 
            = vlSelf->bench__DOT__mem_rsp_error;
    } else {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber22 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h632b4bf4__0) {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_req_ready 
            = vlSelf->bench__DOT__mem_req_ready;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_rdata 
            = vlSelf->bench__DOT__mem_rsp_rdata;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_error 
            = vlSelf->bench__DOT__mem_rsp_error;
    } else {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_req_ready = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_rdata = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_error = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h62f58b69__0) {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10 
            = vlSelf->bench__DOT__mem_req_ready;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21 
            = vlSelf->bench__DOT__mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20 
            = vlSelf->bench__DOT__mem_rsp_rdata;
    } else {
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20 = 0U;
    }
}

extern const VlUnpacked<IData/*31:0*/, 16> Vbench__ConstPool__TABLE_h1bfbab1a_0;
extern const VlUnpacked<CData/*2:0*/, 16> Vbench__ConstPool__TABLE_h2862d6e0_0;
extern const VlUnpacked<CData/*1:0*/, 16> Vbench__ConstPool__TABLE_h400161fb_0;
extern const VlUnpacked<CData/*1:0*/, 16> Vbench__ConstPool__TABLE_h6243dc1f_0;

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__8(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__8\n"); );
    // Init
    CData/*3:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    // Body
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 
        = ((IData)(vlSelf->__VdfgTmp_h5391f0e0__0) ? 1U
            : ((IData)(vlSelf->__VdfgTmp_h930fe3f0__0)
                ? 2U : 0U));
    vlSelf->__VdfgTmp_h98a4e623__0 = ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)) 
                                      | (6U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)));
    __Vtableidx1 = vlSelf->bench__DOT__dut__DOT__decoder__DOT__step;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected 
        = Vbench__ConstPool__TABLE_h1bfbab1a_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection 
        = Vbench__ConstPool__TABLE_h2862d6e0_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__norm_mode 
        = Vbench__ConstPool__TABLE_h400161fb_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__element_mode 
        = Vbench__ConstPool__TABLE_h6243dc1f_0[__Vtableidx1];
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__9(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__9\n"); );
    // Body
    vlSelf->bench__DOT__mem_rsp_valid = vlSelf->__Vdly__bench__DOT__mem_rsp_valid;
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__4(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__4\n"); );
    // Init
    CData/*0:0*/ bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18;
    bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18;
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18 = 0;
    // Body
    vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h6323ea89__0) 
           & (IData)(vlSelf->bench__DOT__mem_rsp_valid));
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h632b4bf4__0) 
           & (IData)(vlSelf->bench__DOT__mem_rsp_valid));
    bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h62f58b69__0) 
           & (IData)(vlSelf->bench__DOT__mem_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__complete = ((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready) 
                                              & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber18 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber18 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0) 
           & (IData)(bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber18));
    if (vlSelf->bench__DOT__dut__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__fault = vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT__read_data = vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_rdata;
    } else {
        vlSelf->bench__DOT__dut__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__read_data = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) 
           & (IData)(bench__DOT__dut__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete)
            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete)
            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete)
            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber21
            : 0U);
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete)
            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21
            : 0U);
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21;
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data = 0U;
    }
}

void Vbench___024root___timing_resume(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___timing_resume\n"); );
    // Body
    if ((4ULL & vlSelf->__VactTriggered.word(0U))) {
        vlSelf->__VtrigSched_h0016f595__0.resume("@(posedge bench.clk)");
    }
    if ((2ULL & vlSelf->__VactTriggered.word(0U))) {
        vlSelf->__VtrigSched_h0016f654__0.resume("@(negedge bench.clk)");
    }
    if ((0x10ULL & vlSelf->__VactTriggered.word(0U))) {
        vlSelf->__VdlySched.resume();
    }
}

void Vbench___024root___timing_commit(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___timing_commit\n"); );
    // Body
    if ((! (4ULL & vlSelf->__VactTriggered.word(0U)))) {
        vlSelf->__VtrigSched_h0016f595__0.commit("@(posedge bench.clk)");
    }
    if ((! (2ULL & vlSelf->__VactTriggered.word(0U)))) {
        vlSelf->__VtrigSched_h0016f654__0.commit("@(negedge bench.clk)");
    }
}

void Vbench___024root___eval_triggers__act(Vbench___024root* vlSelf);
void Vbench___024root___eval_act(Vbench___024root* vlSelf);

bool Vbench___024root___eval_phase__act(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_phase__act\n"); );
    // Init
    VlTriggerVec<5> __VpreTriggered;
    CData/*0:0*/ __VactExecute;
    // Body
    Vbench___024root___eval_triggers__act(vlSelf);
    Vbench___024root___timing_commit(vlSelf);
    __VactExecute = vlSelf->__VactTriggered.any();
    if (__VactExecute) {
        __VpreTriggered.andNot(vlSelf->__VactTriggered, vlSelf->__VnbaTriggered);
        vlSelf->__VnbaTriggered.thisOr(vlSelf->__VactTriggered);
        Vbench___024root___timing_resume(vlSelf);
        Vbench___024root___eval_act(vlSelf);
    }
    return (__VactExecute);
}

void Vbench___024root___eval_nba(Vbench___024root* vlSelf);

bool Vbench___024root___eval_phase__nba(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_phase__nba\n"); );
    // Init
    CData/*0:0*/ __VnbaExecute;
    // Body
    __VnbaExecute = vlSelf->__VnbaTriggered.any();
    if (__VnbaExecute) {
        Vbench___024root___eval_nba(vlSelf);
        vlSelf->__VnbaTriggered.clear();
    }
    return (__VnbaExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbench___024root___dump_triggers__nba(Vbench___024root* vlSelf);
#endif  // VL_DEBUG
#ifdef VL_DEBUG
VL_ATTR_COLD void Vbench___024root___dump_triggers__act(Vbench___024root* vlSelf);
#endif  // VL_DEBUG

void Vbench___024root___eval(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval\n"); );
    // Init
    IData/*31:0*/ __VnbaIterCount;
    CData/*0:0*/ __VnbaContinue;
    // Body
    __VnbaIterCount = 0U;
    __VnbaContinue = 1U;
    while (__VnbaContinue) {
        if (VL_UNLIKELY((0x64U < __VnbaIterCount))) {
#ifdef VL_DEBUG
            Vbench___024root___dump_triggers__nba(vlSelf);
#endif
            VL_FATAL_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 2, "", "NBA region did not converge.");
        }
        __VnbaIterCount = ((IData)(1U) + __VnbaIterCount);
        __VnbaContinue = 0U;
        vlSelf->__VactIterCount = 0U;
        vlSelf->__VactContinue = 1U;
        while (vlSelf->__VactContinue) {
            if (VL_UNLIKELY((0x64U < vlSelf->__VactIterCount))) {
#ifdef VL_DEBUG
                Vbench___024root___dump_triggers__act(vlSelf);
#endif
                VL_FATAL_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 2, "", "Active region did not converge.");
            }
            vlSelf->__VactIterCount = ((IData)(1U) 
                                       + vlSelf->__VactIterCount);
            vlSelf->__VactContinue = 0U;
            if (Vbench___024root___eval_phase__act(vlSelf)) {
                vlSelf->__VactContinue = 1U;
            }
        }
        if (Vbench___024root___eval_phase__nba(vlSelf)) {
            __VnbaContinue = 1U;
        }
    }
}

#ifdef VL_DEBUG
void Vbench___024root___eval_debug_assertions(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_debug_assertions\n"); );
}
#endif  // VL_DEBUG
