// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench___024root.h"

VL_ATTR_COLD void Vbench___024root___eval_static__TOP(Vbench___024root* vlSelf);

VL_ATTR_COLD void Vbench___024root___eval_static(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_static\n"); );
    // Body
    Vbench___024root___eval_static__TOP(vlSelf);
}

VL_ATTR_COLD void Vbench___024root___eval_static__TOP(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_static__TOP\n"); );
    // Body
    vlSelf->bench__DOT__clk = 0U;
    vlSelf->bench__DOT__token_valid = 0U;
    vlSelf->bench__DOT__new_sequence = 0U;
    vlSelf->bench__DOT__logit_ready = 0U;
    vlSelf->bench__DOT__token_id = 0U;
    vlSelf->bench__DOT__token_pos = 0U;
    vlSelf->bench__DOT__mem_req_ready = 0U;
    vlSelf->bench__DOT__mem_rsp_valid = 0U;
    vlSelf->bench__DOT__mem_rsp_error = 0U;
    vlSelf->bench__DOT__mem_rsp_rdata = 0U;
    vlSelf->bench__DOT__cycles = 0U;
    vlSelf->bench__DOT__requests = 0U;
    vlSelf->bench__DOT__responses = 0U;
    vlSelf->bench__DOT__write_count = 0U;
    vlSelf->bench__DOT__logits = 0U;
    vlSelf->bench__DOT__completions = 0U;
    vlSelf->bench__DOT__request_stalls = 0U;
    vlSelf->bench__DOT__logit_stalls = 0U;
    vlSelf->bench__DOT__comparisons = 0U;
    vlSelf->bench__DOT__delay_count = 0U;
    vlSelf->bench__DOT__slot = 0U;
    vlSelf->bench__DOT__pending_slot = 0U;
    vlSelf->bench__DOT__accepted_cycle = 0U;
    vlSelf->bench__DOT__active_operation = 0xffffffffU;
    vlSelf->bench__DOT__pending = 0U;
    vlSelf->bench__DOT__request_held = 0U;
    vlSelf->bench__DOT__logit_held = 0U;
    vlSelf->bench__DOT__kinds_seen = 0U;
    vlSelf->bench__DOT__injected_responses = 0U;
}

VL_ATTR_COLD void Vbench___024root___eval_final(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_final\n"); );
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbench___024root___dump_triggers__stl(Vbench___024root* vlSelf);
#endif  // VL_DEBUG
VL_ATTR_COLD bool Vbench___024root___eval_phase__stl(Vbench___024root* vlSelf);

VL_ATTR_COLD void Vbench___024root___eval_settle(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_settle\n"); );
    // Init
    IData/*31:0*/ __VstlIterCount;
    CData/*0:0*/ __VstlContinue;
    // Body
    __VstlIterCount = 0U;
    vlSelf->__VstlFirstIteration = 1U;
    __VstlContinue = 1U;
    while (__VstlContinue) {
        if (VL_UNLIKELY((0x64U < __VstlIterCount))) {
#ifdef VL_DEBUG
            Vbench___024root___dump_triggers__stl(vlSelf);
#endif
            VL_FATAL_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 2, "", "Settle region did not converge.");
        }
        __VstlIterCount = ((IData)(1U) + __VstlIterCount);
        __VstlContinue = 0U;
        if (Vbench___024root___eval_phase__stl(vlSelf)) {
            __VstlContinue = 1U;
        }
        vlSelf->__VstlFirstIteration = 0U;
    }
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbench___024root___dump_triggers__stl(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___dump_triggers__stl\n"); );
    // Body
    if ((1U & (~ (IData)(vlSelf->__VstlTriggered.any())))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelf->__VstlTriggered.word(0U))) {
        VL_DBG_MSGF("         'stl' region trigger index 0 is active: Internal 'stl' trigger - first iteration\n");
    }
}
#endif  // VL_DEBUG

extern const VlUnpacked<CData/*4:0*/, 8> Vbench__ConstPool__TABLE_h90db6da8_0;
extern const VlUnpacked<IData/*31:0*/, 16> Vbench__ConstPool__TABLE_h1bfbab1a_0;
extern const VlUnpacked<CData/*2:0*/, 16> Vbench__ConstPool__TABLE_h2862d6e0_0;
extern const VlUnpacked<CData/*1:0*/, 16> Vbench__ConstPool__TABLE_h400161fb_0;
extern const VlUnpacked<CData/*1:0*/, 16> Vbench__ConstPool__TABLE_h6243dc1f_0;

VL_ATTR_COLD void Vbench___024root___stl_sequent__TOP__0(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___stl_sequent__TOP__0\n"); );
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
    CData/*4:0*/ bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift;
    bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_operation;
    bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_operation = 0;
    VlWide<5>/*128:0*/ bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient;
    VL_ZERO_W(129, bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 = 0;
    CData/*4:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle = 0;
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0);
    CData/*0:0*/ bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle;
    bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle = 0;
    CData/*3:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    CData/*2:0*/ __Vtableidx2;
    __Vtableidx2 = 0;
    CData/*2:0*/ __Vtableidx3;
    __Vtableidx3 = 0;
    VlWide<5>/*159:0*/ __Vtemp_8;
    VlWide<5>/*159:0*/ __Vtemp_12;
    VlWide<3>/*95:0*/ __Vtemp_16;
    VlWide<3>/*95:0*/ __Vtemp_20;
    VlWide<3>/*95:0*/ __Vtemp_24;
    VlWide<3>/*95:0*/ __Vtemp_28;
    VlWide<3>/*95:0*/ __Vtemp_32;
    VlWide<5>/*159:0*/ __Vtemp_36;
    VlWide<5>/*159:0*/ __Vtemp_39;
    VlWide<5>/*159:0*/ __Vtemp_40;
    VlWide<3>/*95:0*/ __Vtemp_41;
    VlWide<3>/*95:0*/ __Vtemp_42;
    VlWide<3>/*95:0*/ __Vtemp_43;
    VlWide<3>/*95:0*/ __Vtemp_44;
    VlWide<3>/*95:0*/ __Vtemp_45;
    VlWide<9>/*287:0*/ __Vtemp_59;
    // Body
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__in_valid 
        = ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)) 
           | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__out_ready 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)) 
           | (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__in_valid 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x19U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__out_ready 
        = ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x1aU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__in_valid 
        = ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)) 
           | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__out_ready 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)) 
           | (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[0U] 
        = (1U | ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
                 << 2U));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[1U] 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
            >> 0x1eU) | ((IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                                  >> 0x20U)) << 2U));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[2U] 
        = ((IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                    >> 0x20U)) >> 0x1eU);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[3U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[4U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand)));
    vlSelf->bench__DOT__token_ready = ((IData)(vlSelf->bench__DOT__rst_n) 
                                       & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->bench__DOT__logit_valid = ((IData)(vlSelf->bench__DOT__rst_n) 
                                       & (0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__multiply_ready = 
        ((~ (IData)(vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__busy)) 
         & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__multiply_valid = 
        ((IData)(vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_result) 
         & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber4 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber4 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber4 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber8 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0xdU 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0xfU 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber7 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0x23U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber7 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0x14U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0x17U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready 
        = ((~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy)) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (3U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (4U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (8U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order) 
                                             << 0x18U))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (8U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready 
        = ((~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy)) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (8U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (3U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order) 
                                             << 0x18U))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (8U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready 
        = ((~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy)) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (8U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (3U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order) 
                                             << 0x18U))));
    if ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[3U] 
            = (- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U] 
                          >> 0x1fU)));
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[3U] 
            = (- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U] 
                          >> 0x1fU)));
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = 0ULL;
    if (vlSelf->bench__DOT__rst_n) {
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
    } else {
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
    }
    VL_SHIFTL_WWI(130,130,32, __Vtemp_8, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work, 2U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[0U] 
        = (__Vtemp_8[0U] | (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[3U] 
                            >> 0x1eU));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[1U] 
        = __Vtemp_8[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[2U] 
        = __Vtemp_8[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[3U] 
        = __Vtemp_8[3U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[4U] 
        = (3U & __Vtemp_8[4U]);
    VL_SHIFTL_WWI(130,130,32, __Vtemp_12, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_12[0U] | (1U & vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[4U]));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_12[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = __Vtemp_12[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[3U] 
        = __Vtemp_12[3U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[4U] 
        = (3U & __Vtemp_12[4U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_16, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_16[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_16[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_16[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_20, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_20[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_20[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_20[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_24, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_24[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_24[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_24[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_28, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_28[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_28[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_28[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_32[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_32[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_32[2U]);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_operation 
        = ((0x19U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x1aU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data)));
    __Vtableidx2 = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane;
    bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift 
        = Vbench__ConstPool__TABLE_h90db6da8_0[__Vtableidx2];
    __Vtableidx3 = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift 
        = Vbench__ConstPool__TABLE_h90db6da8_0[__Vtableidx3];
    vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber7 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (3U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0xdU 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0x17U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__residual__DOT__port_idle 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__rope__DOT__port_idle 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__port_idle = ((IData)(vlSelf->bench__DOT__rst_n) 
                                               & (0U 
                                                  == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__attention__DOT__port_idle 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__port_idle 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state)));
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_write 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wr) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber12 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wr) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wr) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber11 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wr) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wr) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->__VdfgTmp_h5391f0e0__0 = ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                      | (7U == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->__VdfgTmp_h930fe3f0__0 = ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                      | (9U == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    __Vtableidx1 = vlSelf->bench__DOT__dut__DOT__decoder__DOT__step;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected 
        = Vbench__ConstPool__TABLE_h1bfbab1a_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection 
        = Vbench__ConstPool__TABLE_h2862d6e0_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__norm_mode 
        = Vbench__ConstPool__TABLE_h400161fb_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__element_mode 
        = Vbench__ConstPool__TABLE_h6243dc1f_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wr) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wr) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->__VdfgTmp_h98a4e623__0 = ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)) 
                                      | (6U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)));
    vlSelf->bench__DOT__error = ((IData)(vlSelf->bench__DOT__done) 
                                 & (IData)(vlSelf->bench__DOT__dut__DOT__failed));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor));
    VL_NEGATE_W(5, __Vtemp_36, bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U] 
            = __Vtemp_36[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U] 
            = __Vtemp_36[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U] 
            = __Vtemp_36[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U] 
            = __Vtemp_36[3U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[4U] 
            = (1U & __Vtemp_36[4U]);
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
    __Vtemp_39[0U] = (1U | ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
                            << 2U));
    __Vtemp_39[1U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
                       >> 0x1eU) | ((IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                                             >> 0x20U)) 
                                    << 2U));
    __Vtemp_39[2U] = ((IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                               >> 0x20U)) >> 0x1eU);
    __Vtemp_39[3U] = 0U;
    __Vtemp_39[4U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__subtract 
        = VL_GTE_W(5, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder, __Vtemp_39);
    __Vtemp_40[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[0U];
    __Vtemp_40[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[1U];
    __Vtemp_40[2U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[2U];
    __Vtemp_40[3U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[3U];
    __Vtemp_40[4U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[4U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(5, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_40);
    __Vtemp_41[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_41[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor 
                              >> 0x20U));
    __Vtemp_41[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_41);
    __Vtemp_42[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_42[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                              >> 0x20U));
    __Vtemp_42[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_42);
    __Vtemp_43[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_43[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                              >> 0x20U));
    __Vtemp_43[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_43);
    __Vtemp_44[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_44[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                              >> 0x20U));
    __Vtemp_44[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_44);
    __Vtemp_45[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_45[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                              >> 0x20U));
    __Vtemp_45[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_45);
    if (bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_operation) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiply_a 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiply_b 
            = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential));
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiply_a 
            = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q 
                                            >> 0x1fU))))) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q)));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiply_b 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__weight_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qw 
                   >> (IData)(bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__zero_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qz 
                   >> (IData)(bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__weight_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw 
                   >> (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__zero_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz 
                   >> (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift)));
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
    if (vlSelf->__VdfgTmp_h5391f0e0__0) {
        vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 = 1U;
        vlSelf->bench__DOT__dut__DOT__selected = 1U;
    } else if (vlSelf->__VdfgTmp_h930fe3f0__0) {
        vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 = 2U;
        vlSelf->bench__DOT__dut__DOT__selected = 2U;
    } else {
        vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__selected = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (6U 
                                                 > vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected));
    __Vtemp_59[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18;
    __Vtemp_59[1U] = (IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                               << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))));
    __Vtemp_59[2U] = (IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))) 
                              >> 0x20U));
    __Vtemp_59[3U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                       << 3U) | (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15));
    __Vtemp_59[4U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                       << 9U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10) 
                                  << 8U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12) 
                                             << 7U) 
                                            | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13) 
                                                << 3U) 
                                               | (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                                                  >> 0x1dU)))));
    __Vtemp_59[5U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                       >> 0x17U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                                    << 9U));
    __Vtemp_59[6U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                 << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                               << 0x20U) 
                                              | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_59[7U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
                       << 0xcU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_59[8U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10) 
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
                 ? 0U : (__Vtemp_59[((IData)(1U) + 
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
               | (__Vtemp_59[(0xfU & (((IData)(0x89U) 
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
                 ? 0U : (__Vtemp_59[((IData)(2U) + 
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
               | (__Vtemp_59[((IData)(1U) + (0xfU & 
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
                 ? 0U : (__Vtemp_59[((IData)(3U) + 
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
               | (__Vtemp_59[((IData)(2U) + (0xfU & 
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
                 ? 0U : (__Vtemp_59[((IData)(4U) + 
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
               | (__Vtemp_59[((IData)(3U) + (0xfU & 
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
                           ? 0U : (__Vtemp_59[((IData)(5U) 
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
                         | (__Vtemp_59[((IData)(4U) 
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
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 > 
                                                 ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                                                   ? 1U
                                                   : 0U)));
    vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (3U 
                                                 > vlSelf->bench__DOT__dut__DOT__selected));
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
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0 
            = (1U == ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                       ? 1U : 0U));
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0 
            = (0U == ((IData)(vlSelf->__VdfgTmp_h98a4e623__0)
                       ? 1U : 0U));
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
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 = 0U;
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

VL_ATTR_COLD void Vbench___024root___eval_triggers__stl(Vbench___024root* vlSelf);
VL_ATTR_COLD void Vbench___024root___eval_stl(Vbench___024root* vlSelf);

VL_ATTR_COLD bool Vbench___024root___eval_phase__stl(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_phase__stl\n"); );
    // Init
    CData/*0:0*/ __VstlExecute;
    // Body
    Vbench___024root___eval_triggers__stl(vlSelf);
    __VstlExecute = vlSelf->__VstlTriggered.any();
    if (__VstlExecute) {
        Vbench___024root___eval_stl(vlSelf);
    }
    return (__VstlExecute);
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbench___024root___dump_triggers__act(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___dump_triggers__act\n"); );
    // Body
    if ((1U & (~ (IData)(vlSelf->__VactTriggered.any())))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 0 is active: @(edge bench.clk)\n");
    }
    if ((2ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 1 is active: @(negedge bench.clk)\n");
    }
    if ((4ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 2 is active: @(posedge bench.clk)\n");
    }
    if ((8ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 3 is active: @(posedge bench.clk or negedge bench.rst_n)\n");
    }
    if ((0x10ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 4 is active: @([true] __VdlySched.awaitingCurrentTime())\n");
    }
}
#endif  // VL_DEBUG

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbench___024root___dump_triggers__nba(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___dump_triggers__nba\n"); );
    // Body
    if ((1U & (~ (IData)(vlSelf->__VnbaTriggered.any())))) {
        VL_DBG_MSGF("         No triggers active\n");
    }
    if ((1ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 0 is active: @(edge bench.clk)\n");
    }
    if ((2ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 1 is active: @(negedge bench.clk)\n");
    }
    if ((4ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 2 is active: @(posedge bench.clk)\n");
    }
    if ((8ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 3 is active: @(posedge bench.clk or negedge bench.rst_n)\n");
    }
    if ((0x10ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 4 is active: @([true] __VdlySched.awaitingCurrentTime())\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vbench___024root___ctor_var_reset(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___ctor_var_reset\n"); );
    // Body
    vlSelf->bench__DOT____Vxrand_h8d93fe75__15 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__14 = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(97, vlSelf->bench__DOT____Vxrand_hd08cd184__3);
    VL_RAND_RESET_W(97, vlSelf->bench__DOT____Vxrand_hd08cd184__2);
    VL_RAND_RESET_W(97, vlSelf->bench__DOT____Vxrand_hd08cd184__1);
    VL_RAND_RESET_W(97, vlSelf->bench__DOT____Vxrand_hd08cd184__0);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__12 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__11 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__10 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__9 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__8 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__7 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__6 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__5 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__4 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__3 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__2 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__1 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__rst_n = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__token_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__new_sequence = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__logit_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__token_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__token_pos = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__token_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__logit_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__done = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__logit_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__logit_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__mem_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__mem_req_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__mem_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__mem_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__mem_rsp_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__mem_req_kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__mem_req_proj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__mem_req_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__mem_req_row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__mem_req_col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__mem_req_wdata = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__mem_rsp_rdata = VL_RAND_RESET_I(32);
    for (int __Vi0 = 0; __Vi0 < 511; ++__Vi0) {
        vlSelf->bench__DOT__memory[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 456; ++__Vi0) {
        vlSelf->bench__DOT__expected[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 511; ++__Vi0) {
        vlSelf->bench__DOT__first[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 511; ++__Vi0) {
        vlSelf->bench__DOT__limit[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 511; ++__Vi0) {
        vlSelf->bench__DOT__count[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 511; ++__Vi0) {
        vlSelf->bench__DOT__writable[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 51; ++__Vi0) {
        vlSelf->bench__DOT__expected_logits[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__rng = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__cycles = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__requests = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__responses = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__write_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__logits = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__completions = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__request_stalls = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__logit_stalls = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__comparisons = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__delay_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__pending_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__accepted_cycle = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__active_operation = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__pending = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__request_held = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__logit_held = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(136, vlSelf->bench__DOT__held_request);
    vlSelf->bench__DOT__held_logit = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__kinds_seen = VL_RAND_RESET_I(12);
    for (int __Vi0 = 0; __Vi0 < 511; ++__Vi0) {
        VL_RAND_RESET_W(97, vlSelf->bench__DOT__initial_records[__Vi0]);
    }
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->bench__DOT__token_words[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->bench__DOT__fault_config[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__injected_responses = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vlvbound_h69f4120e__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vlvbound_ha5961289__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vlvbound_h6b8dec7b__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vlvbound_h3ed999ac__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vlvbound_h3078bb6a__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vlvbound_h42a46a12__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT____Vlvbound_h23dbfffc__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__sequence_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__token = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__next_position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__component = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__vocabulary = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tensor_f16 = VL_RAND_RESET_I(16);
    vlSelf->bench__DOT__dut__DOT__activation = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__weight_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__logit_product = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__logit_sum);
    vlSelf->bench__DOT__dut__DOT__activation_reuse_valid = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__head_activations[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__head_activation_q = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__multiply_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__multiply_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__ready = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__finished = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__faults = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__selected = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__port_idle = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_rdata = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_wdata = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_proj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber21 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber20 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__decoder____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber7 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber21 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__2 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__1 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__step = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__norm_mode = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__element_mode = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber21 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber15 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber13 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber21 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber20 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber18 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber14 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber12 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber7 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber21 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber20 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber18 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber14 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber7 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber21 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber15 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber13 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber12 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber8 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__inputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qz = VL_RAND_RESET_I(32);
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vi0]);
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__bias_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__delta = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scale_integer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__dequantized_weight = VL_RAND_RESET_Q(37);
    VL_RAND_RESET_W(69, vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__weight_nibble = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__zero_nibble = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__operand_b = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__in_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__cosine = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__sine = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_cos = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_sin = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_cos = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_sin = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__result = VL_RAND_RESET_Q(64);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 4; ++__Vi1) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[__Vi0][__Vi1] = VL_RAND_RESET_Q(64);
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q_column = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__k_column = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot_product = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_argument = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted);
    VL_RAND_RESET_W(97, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__sqrt_dimension = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_error = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiply_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiply_b = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__in_valid = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state = VL_RAND_RESET_I(2);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__iteration = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_error = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__reduced_input = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__exponent = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__remainder_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__division_magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__total = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term_negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divide_by_zero = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__signed_quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__ready = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__finished = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__faults = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__inputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz = VL_RAND_RESET_I(32);
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vi0]);
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__bias_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scale_integer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight = VL_RAND_RESET_Q(37);
    VL_RAND_RESET_W(69, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__weight_nibble = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__zero_nibble = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__in_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum = VL_RAND_RESET_Q(33);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__product_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__numerator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__denominator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__exponent = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__total = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__result = VL_RAND_RESET_Q(64);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 4; ++__Vi1) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[__Vi0][__Vi1] = VL_RAND_RESET_Q(64);
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(137, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum = VL_RAND_RESET_Q(33);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__product_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__numerator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__denominator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__exponent = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__total = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__result = VL_RAND_RESET_Q(64);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 4; ++__Vi1) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[__Vi0][__Vi1] = VL_RAND_RESET_Q(64);
        }
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(137, vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0 = 0;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0 = 0;
    vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(137, vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0);
    vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h6323ea89__0 = 0;
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h62f58b69__0 = 0;
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h632b4bf4__0 = 0;
    vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 = 0;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__result = VL_RAND_RESET_Q(64);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 4; ++__Vi1) {
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[__Vi0][__Vi1] = VL_RAND_RESET_Q(64);
        }
    }
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->__VdfgTmp_h5391f0e0__0 = 0;
    vlSelf->__VdfgTmp_h930fe3f0__0 = 0;
    vlSelf->__VdfgTmp_h98a4e623__0 = 0;
    vlSelf->__Vdly__bench__DOT__mem_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->__Vdly__bench__DOT__dut__DOT__component = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = VL_RAND_RESET_I(6);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_argument = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__clk__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__rst_n__0 = VL_RAND_RESET_I(1);
}
