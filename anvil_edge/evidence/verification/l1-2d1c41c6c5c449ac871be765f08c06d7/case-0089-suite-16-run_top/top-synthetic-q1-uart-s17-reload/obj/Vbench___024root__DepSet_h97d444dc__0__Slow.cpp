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
    vlSelf->bench__DOT__ddr_cal_done = 0U;
    vlSelf->bench__DOT__spi_miso = 0U;
    vlSelf->bench__DOT__uart_rx = 1U;
    vlSelf->bench__DOT__m_axis_tready = 0U;
    vlSelf->bench__DOT__cfg_valid = 0U;
    vlSelf->bench__DOT__cfg_write = 0U;
    vlSelf->bench__DOT__cfg_rsp_ready = 0U;
    vlSelf->bench__DOT__cfg_addr = 0U;
    vlSelf->bench__DOT__cfg_wdata = 0U;
    vlSelf->bench__DOT__running = 0U;
    vlSelf->bench__DOT__out_held = 0U;
    vlSelf->bench__DOT__held_output = 0U;
    vlSelf->bench__DOT__expect_rejection = 0U;
    vlSelf->bench__DOT__control_requests = 0U;
    vlSelf->bench__DOT__control_responses = 0U;
    vlSelf->bench__DOT__reload_events = 0U;
    vlSelf->bench__DOT__outputs = 0U;
    vlSelf->bench__DOT__completions = 0U;
    vlSelf->bench__DOT__cache_k_writes = 0U;
    vlSelf->bench__DOT__cache_v_writes = 0U;
    vlSelf->bench__DOT__inference_reads = 0U;
    vlSelf->bench__DOT__inference_writes = 0U;
    vlSelf->bench__DOT__embedding_reads = 0U;
    vlSelf->bench__DOT__operation_index = 0U;
    vlSelf->bench__DOT__embedding_index = 0U;
    vlSelf->bench__DOT__ddr_req_ready = 0U;
    vlSelf->bench__DOT__ddr_rsp_valid = 0U;
    vlSelf->bench__DOT__ddr_rsp_error = 0U;
    vlSelf->bench__DOT__ddr_rsp_rdata = 0U;
    vlSelf->bench__DOT__command_shift = 0U;
    vlSelf->bench__DOT__spi_command_bits = 0U;
    vlSelf->bench__DOT__flash_address = 0U;
    vlSelf->bench__DOT__flash_bit = 0U;
    vlSelf->bench__DOT__spi_reads = 0U;
    vlSelf->bench__DOT__pending = 0U;
    vlSelf->bench__DOT__held = 0U;
    vlSelf->bench__DOT__loading = 1U;
    vlSelf->bench__DOT__pending_address = 0ULL;
    vlSelf->bench__DOT__cycle = 0U;
    vlSelf->bench__DOT__writes = 0U;
    vlSelf->bench__DOT__reads = 0U;
    vlSelf->bench__DOT__acknowledgements = 0U;
    vlSelf->bench__DOT__delay_count = 0U;
    vlSelf->bench__DOT__request_stalls = 0U;
    vlSelf->bench__DOT__response_stalls = 0U;
    vlSelf->bench__DOT__comparisons = 0U;
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
            VL_FATAL_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 2, "", "Settle region did not converge.");
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

extern const VlUnpacked<IData/*31:0*/, 32> Vbench__ConstPool__TABLE_h109f7c34_0;
extern const VlUnpacked<CData/*2:0*/, 32> Vbench__ConstPool__TABLE_h93373b12_0;
extern const VlUnpacked<CData/*4:0*/, 8> Vbench__ConstPool__TABLE_h90db6da8_0;
extern const VlUnpacked<CData/*2:0*/, 16> Vbench__ConstPool__TABLE_h554b41bf_0;
extern const VlUnpacked<CData/*1:0*/, 32> Vbench__ConstPool__TABLE_h7831209a_0;
extern const VlUnpacked<IData/*31:0*/, 16> Vbench__ConstPool__TABLE_h1bfbab1a_0;
extern const VlUnpacked<CData/*2:0*/, 16> Vbench__ConstPool__TABLE_h2862d6e0_0;
extern const VlUnpacked<CData/*1:0*/, 16> Vbench__ConstPool__TABLE_h400161fb_0;
extern const VlUnpacked<CData/*1:0*/, 16> Vbench__ConstPool__TABLE_h6243dc1f_0;
extern const VlWide<32>/*1023:0*/ Vbench__ConstPool__CONST_hd6b7ba52_0;
extern const VlWide<16>/*511:0*/ Vbench__ConstPool__CONST_h93e1b771_0;

VL_ATTR_COLD void Vbench___024root___stl_sequent__TOP__0(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___stl_sequent__TOP__0\n"); );
    // Init
    CData/*0:0*/ bench__DOT__dut__DOT__io_rx_idle;
    bench__DOT__dut__DOT__io_rx_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_he9711bd6__0;
    bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_he9711bd6__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT____VdfgTmp_h3d13e98e__0;
    bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT____VdfgTmp_h3d13e98e__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_error;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_error = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_rdata;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_rdata = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber20;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber20 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber20;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber20 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber21;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber21 = 0;
    CData/*4:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane_shift;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane_shift = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted_operation;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted_operation = 0;
    VlWide<5>/*128:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient;
    VL_ZERO_W(129, bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16 = 0;
    CData/*2:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 = 0;
    CData/*3:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16 = 0;
    CData/*2:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 = 0;
    CData/*3:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 = 0;
    CData/*4:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0 = 0;
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0);
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h6323ea89__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h6323ea89__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h62f58b69__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h62f58b69__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h632b4bf4__0;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h632b4bf4__0 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_inputs;
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_inputs = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_outputs;
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_outputs = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_groups;
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_groups = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h3281ae77__0;
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h3281ae77__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h55965d66__0;
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h55965d66__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____VdfgTmp_h69769b5a__0;
    bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____VdfgTmp_h69769b5a__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar0_valid;
    bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar0_valid = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar1_valid;
    bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar1_valid = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_inputs;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_inputs = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_groups;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_groups = 0;
    VlWide<3>/*65:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_end;
    VL_ZERO_W(66, bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_end);
    CData/*0:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_h304f5f27__0;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_h304f5f27__0 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_haf19dc44__0;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_haf19dc44__0 = 0;
    CData/*0:0*/ __VdfgTmp_h77ceb880__0;
    __VdfgTmp_h77ceb880__0 = 0;
    CData/*0:0*/ __VdfgTmp_had546d50__0;
    __VdfgTmp_had546d50__0 = 0;
    CData/*4:0*/ __Vtableidx1;
    __Vtableidx1 = 0;
    CData/*3:0*/ __Vtableidx2;
    __Vtableidx2 = 0;
    CData/*2:0*/ __Vtableidx3;
    __Vtableidx3 = 0;
    CData/*2:0*/ __Vtableidx4;
    __Vtableidx4 = 0;
    CData/*3:0*/ __Vtableidx5;
    __Vtableidx5 = 0;
    CData/*4:0*/ __Vtableidx6;
    __Vtableidx6 = 0;
    VlWide<3>/*95:0*/ __Vtemp_3;
    VlWide<3>/*95:0*/ __Vtemp_4;
    VlWide<3>/*95:0*/ __Vtemp_5;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_9;
    VlWide<3>/*95:0*/ __Vtemp_10;
    VlWide<3>/*95:0*/ __Vtemp_12;
    VlWide<3>/*95:0*/ __Vtemp_14;
    VlWide<3>/*95:0*/ __Vtemp_15;
    VlWide<3>/*95:0*/ __Vtemp_16;
    VlWide<3>/*95:0*/ __Vtemp_17;
    VlWide<3>/*95:0*/ __Vtemp_18;
    VlWide<3>/*95:0*/ __Vtemp_19;
    VlWide<3>/*95:0*/ __Vtemp_20;
    VlWide<3>/*95:0*/ __Vtemp_22;
    VlWide<3>/*95:0*/ __Vtemp_23;
    VlWide<3>/*95:0*/ __Vtemp_25;
    VlWide<3>/*95:0*/ __Vtemp_26;
    VlWide<3>/*95:0*/ __Vtemp_27;
    VlWide<3>/*95:0*/ __Vtemp_29;
    VlWide<3>/*95:0*/ __Vtemp_30;
    VlWide<3>/*95:0*/ __Vtemp_31;
    VlWide<3>/*95:0*/ __Vtemp_33;
    VlWide<3>/*95:0*/ __Vtemp_34;
    VlWide<3>/*95:0*/ __Vtemp_35;
    VlWide<3>/*95:0*/ __Vtemp_36;
    VlWide<3>/*95:0*/ __Vtemp_37;
    VlWide<3>/*95:0*/ __Vtemp_39;
    VlWide<3>/*95:0*/ __Vtemp_40;
    VlWide<3>/*95:0*/ __Vtemp_41;
    VlWide<3>/*95:0*/ __Vtemp_45;
    VlWide<3>/*95:0*/ __Vtemp_46;
    VlWide<3>/*95:0*/ __Vtemp_47;
    VlWide<3>/*95:0*/ __Vtemp_49;
    VlWide<3>/*95:0*/ __Vtemp_50;
    VlWide<3>/*95:0*/ __Vtemp_57;
    VlWide<3>/*95:0*/ __Vtemp_58;
    VlWide<3>/*95:0*/ __Vtemp_59;
    VlWide<3>/*95:0*/ __Vtemp_60;
    VlWide<3>/*95:0*/ __Vtemp_61;
    VlWide<3>/*95:0*/ __Vtemp_62;
    VlWide<3>/*95:0*/ __Vtemp_63;
    VlWide<3>/*95:0*/ __Vtemp_64;
    VlWide<3>/*95:0*/ __Vtemp_66;
    VlWide<3>/*95:0*/ __Vtemp_67;
    VlWide<3>/*95:0*/ __Vtemp_68;
    VlWide<3>/*95:0*/ __Vtemp_69;
    VlWide<3>/*95:0*/ __Vtemp_70;
    VlWide<3>/*95:0*/ __Vtemp_71;
    VlWide<3>/*95:0*/ __Vtemp_72;
    VlWide<3>/*95:0*/ __Vtemp_73;
    VlWide<3>/*95:0*/ __Vtemp_75;
    VlWide<3>/*95:0*/ __Vtemp_76;
    VlWide<3>/*95:0*/ __Vtemp_77;
    VlWide<5>/*159:0*/ __Vtemp_79;
    VlWide<5>/*159:0*/ __Vtemp_83;
    VlWide<3>/*95:0*/ __Vtemp_87;
    VlWide<3>/*95:0*/ __Vtemp_91;
    VlWide<3>/*95:0*/ __Vtemp_95;
    VlWide<3>/*95:0*/ __Vtemp_99;
    VlWide<3>/*95:0*/ __Vtemp_103;
    VlWide<3>/*95:0*/ __Vtemp_107;
    VlWide<3>/*95:0*/ __Vtemp_108;
    VlWide<3>/*95:0*/ __Vtemp_109;
    VlWide<3>/*95:0*/ __Vtemp_111;
    VlWide<3>/*95:0*/ __Vtemp_112;
    VlWide<3>/*95:0*/ __Vtemp_113;
    VlWide<5>/*159:0*/ __Vtemp_115;
    VlWide<5>/*159:0*/ __Vtemp_116;
    VlWide<3>/*95:0*/ __Vtemp_117;
    VlWide<3>/*95:0*/ __Vtemp_118;
    VlWide<3>/*95:0*/ __Vtemp_119;
    VlWide<3>/*95:0*/ __Vtemp_120;
    VlWide<3>/*95:0*/ __Vtemp_121;
    VlWide<3>/*95:0*/ __Vtemp_123;
    VlWide<3>/*95:0*/ __Vtemp_124;
    VlWide<3>/*95:0*/ __Vtemp_125;
    VlWide<3>/*95:0*/ __Vtemp_126;
    VlWide<3>/*95:0*/ __Vtemp_127;
    VlWide<3>/*95:0*/ __Vtemp_128;
    VlWide<3>/*95:0*/ __Vtemp_129;
    VlWide<3>/*95:0*/ __Vtemp_131;
    VlWide<3>/*95:0*/ __Vtemp_132;
    VlWide<3>/*95:0*/ __Vtemp_133;
    VlWide<3>/*95:0*/ __Vtemp_134;
    VlWide<3>/*95:0*/ __Vtemp_135;
    VlWide<3>/*95:0*/ __Vtemp_136;
    VlWide<3>/*95:0*/ __Vtemp_137;
    VlWide<5>/*159:0*/ __Vtemp_185;
    VlWide<9>/*287:0*/ __Vtemp_202;
    // Body
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable = 1U;
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__address_known = 1U;
    if ((1U & (~ ((((((((0U == vlSelf->bench__DOT__cfg_addr) 
                        | (4U == vlSelf->bench__DOT__cfg_addr)) 
                       | (8U == vlSelf->bench__DOT__cfg_addr)) 
                      | (0xcU == vlSelf->bench__DOT__cfg_addr)) 
                     | (0x10U == vlSelf->bench__DOT__cfg_addr)) 
                    | (0x14U == vlSelf->bench__DOT__cfg_addr)) 
                   | (0x18U == vlSelf->bench__DOT__cfg_addr)) 
                  | (0x1cU == vlSelf->bench__DOT__cfg_addr))))) {
        if ((0x20U != vlSelf->bench__DOT__cfg_addr)) {
            if ((0x24U != vlSelf->bench__DOT__cfg_addr)) {
                vlSelf->bench__DOT__dut__DOT__configuration__DOT__address_known = 0U;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = 0U;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_kind_index = 0U;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_kind_valid = 0U;
    if (((0x100U <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
          [0U]) & (0x103U >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                   [0U]))) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_kind_index 
            = (0x1fU & vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
               [0U]);
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_kind_valid = 1U;
    } else if (((0x200U <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                 [0U]) & (0x20fU >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                          [0U]))) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_kind_index 
            = (0x1fU & ((IData)(4U) + vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                        [0U]));
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_kind_valid = 1U;
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset_valid = 1U;
    if ((4U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
        if ((8U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
            if ((0xcU != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                if ((0x10U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                    if ((0x14U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                        if ((0x18U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                            if ((0x24U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset_valid = 0U;
                            }
                        }
                    }
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 0U;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__writable_key = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__in_valid 
        = ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)) 
           | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__out_ready 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)) 
           | (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__in_valid 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x19U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__out_ready 
        = ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x1aU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__in_valid 
        = ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)) 
           | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__out_ready 
        = ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)) 
           | (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__waiting 
        = ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__state)) 
           | ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__state)) 
              | (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__state))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__kind 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__waiting 
        = ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
           | ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
              | ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
                 | ((0x16U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
                    | ((0x1bU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
                       | (0x20U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)))))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_key[0U] 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_key[1U] 
        = (IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) 
                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[1U]))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_key[2U] 
        = (IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) 
                     << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[1U]))) 
                   >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__rows 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[6U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__columns 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[7U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__format 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[8U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__region_offset 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[5U])) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[4U])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__extent 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0xbU])) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0xaU])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__storage_kind 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[3U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__permissions 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[9U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_offset 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_record[5U])) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_record[4U])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_extent 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_record[0xbU])) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_record[0xaU])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__data_read 
        = ((0x15U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
           | (0x1aU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____Vcellinp__index_multiplier__in_valid 
        = ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
           | (0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____Vcellinp__index_multiplier__out_ready 
        = ((0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
           | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state_accept_end 
        = (0x1ffffffffULL & ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_value[1U])) 
                             + (QData)((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_value[2U]))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[0U] 
        = (1U | ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
                 << 2U));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[1U] 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
            >> 0x1eU) | ((IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                                  >> 0x20U)) << 2U));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[2U] 
        = ((IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                    >> 0x20U)) >> 0x1eU);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[3U] = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial[4U] = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_base 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                            [3U])) << 0x20U) | (QData)((IData)(
                                                               vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                                                               [2U])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_length 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                            [5U])) << 0x20U) | (QData)((IData)(
                                                               vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                                                               [4U])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_offset 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                            [7U])) << 0x20U) | (QData)((IData)(
                                                               vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor
                                                               [6U])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__absolute_header_end[0U] 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__header
        [3U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__absolute_header_end[1U] = 0U;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__absolute_header_end[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__next_crc 
        = (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__crc_value, 1U) 
           ^ ((1U & vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__crc_value)
               ? 0xedb88320U : 0U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__profile_id 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__configuration[4U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__active_vocab 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__configuration[5U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__eos_id 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__configuration[1U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__header_record_count 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__header[3U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__header_data_bytes 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__header[5U])) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__header[4U])));
    __Vtemp_3[0U] = 0x20U;
    __Vtemp_3[1U] = 0U;
    __Vtemp_3[2U] = 0U;
    __Vtemp_4[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__vocab_size;
    __Vtemp_4[1U] = 0U;
    __Vtemp_4[2U] = 0U;
    VL_SHIFTL_WWI(65,65,32, __Vtemp_5, __Vtemp_4, 4U);
    VL_ADD_W(3, __Vtemp_6, __Vtemp_3, __Vtemp_5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_segment_bytes[0U] 
        = __Vtemp_6[0U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_segment_bytes[1U] 
        = __Vtemp_6[1U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_segment_bytes[2U] 
        = (1U & __Vtemp_6[2U]);
    __Vtemp_8[0U] = 0x20U;
    __Vtemp_8[1U] = 0U;
    __Vtemp_8[2U] = 0U;
    __Vtemp_9[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_count;
    __Vtemp_9[1U] = 0U;
    __Vtemp_9[2U] = 0U;
    VL_ADD_W(3, __Vtemp_10, __Vtemp_8, __Vtemp_9);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_segment_bytes[0U] 
        = __Vtemp_10[0U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_segment_bytes[1U] 
        = __Vtemp_10[1U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_segment_bytes[2U] 
        = (1U & __Vtemp_10[2U]);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_offset 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data[1U])) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data[0U])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_length 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data[2U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_flags 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data[3U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__pair_key 
        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data[0U])) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data[1U])));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__w0 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__w1 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__w2 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__transition_count 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[9U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__state_count 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[8U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__w0 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__record_data[0U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__w1 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__record_data[1U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__w2 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__record_data[2U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__w3 
        = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__record_data[3U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_legal = 1U;
    if ((4U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_legal 
            = (4U <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value);
    } else {
        if ((8U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = 1U;
        } else if ((0xcU == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = 2U;
        } else if ((0x10U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = 3U;
        } else if ((0x14U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = 4U;
        } else if ((0x18U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = 5U;
        } else if ((0x24U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = 6U;
        }
        if ((8U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
            if ((0xcU == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_legal 
                    = (4U >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value);
            } else if ((0x10U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_legal 
                    = (1U >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value);
            } else if ((0x14U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_legal 
                    = ((1U <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value) 
                       & (4U >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value));
            } else if ((0x18U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_legal 
                    = (((0x100U <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value) 
                        & (0x40000U >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value)) 
                       & (0x101U >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value));
            } else if ((0x24U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset)) {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_legal = 0U;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__selected_count = 0U;
    if (((0xbU <= (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index)) 
         & (0x13U >= (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index)))) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__selected_count 
            = (((0U == (0x1fU & VL_SHIFTL_III(9,32,32, 
                                              ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index) 
                                               - (IData)(4U)), 5U)))
                 ? 0U : (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[
                         (((IData)(0x1fU) + (0x1ffU 
                                             & VL_SHIFTL_III(9,32,32, 
                                                             ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index) 
                                                              - (IData)(4U)), 5U))) 
                          >> 5U)] << ((IData)(0x20U) 
                                      - (0x1fU & VL_SHIFTL_III(9,32,32, 
                                                               ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index) 
                                                                - (IData)(4U)), 5U))))) 
               | (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[
                  (0xfU & (VL_SHIFTL_III(9,32,32, ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index) 
                                                   - (IData)(4U)), 5U) 
                           >> 5U))] >> (0x1fU & VL_SHIFTL_III(9,32,32, 
                                                              ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index) 
                                                               - (IData)(4U)), 5U))));
    }
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_key = 0U;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 0U;
    vlSelf->bench__DOT__ddr_req_valid = ((IData)(vlSelf->bench__DOT__rst_n) 
                                         & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state)));
    vlSelf->bench__DOT__ddr_req_write = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_write) 
                                         & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__busy = ((IData)(vlSelf->bench__DOT__rst_n) 
                                & ((4U != (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                   & (9U != (IData)(vlSelf->bench__DOT__dut__DOT__state))));
    vlSelf->bench__DOT__cfg_rsp_valid = ((IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_valid) 
                                         & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__engine_start = ((IData)(vlSelf->bench__DOT__rst_n) 
                                                  & (5U 
                                                     == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order) 
                                             << 0x18U))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order) 
                                             << 0x18U))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divisor 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))
            ? 0xb17218ULL : (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order) 
                                             << 0x18U))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__image_loader__start 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (2U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__manifest__start 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (4U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__directory__start 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (6U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__tokens__start 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (8U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__profile__start 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0xaU 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__special_trie__start 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0xcU 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____VdfgTmp_h68ab1d3d__0 
        = (0x7ffU & VL_SHIFTL_III(11,11,32, ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__state))
                                              ? 0U : 
                                             ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__state))
                                               ? 4U
                                               : (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index))), 6U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__same_storage 
        = (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_record[3U] 
           == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[3U]);
    __Vtemp_12[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_base);
    __Vtemp_12[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_base 
                              >> 0x20U));
    __Vtemp_12[2U] = 0U;
    __Vtemp_14[0U] = 0x20U;
    __Vtemp_14[1U] = 0U;
    __Vtemp_14[2U] = 0U;
    __Vtemp_15[0U] = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_count;
    __Vtemp_15[1U] = 0U;
    __Vtemp_15[2U] = 0U;
    VL_SHIFTL_WWI(65,65,32, __Vtemp_16, __Vtemp_15, 5U);
    __Vtemp_17[0U] = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_count;
    __Vtemp_17[1U] = 0U;
    __Vtemp_17[2U] = 0U;
    VL_SHIFTL_WWI(65,65,32, __Vtemp_18, __Vtemp_17, 4U);
    VL_ADD_W(3, __Vtemp_19, __Vtemp_16, __Vtemp_18);
    VL_ADD_W(3, __Vtemp_20, __Vtemp_14, __Vtemp_19);
    __Vtemp_22[0U] = __Vtemp_20[0U];
    __Vtemp_22[1U] = __Vtemp_20[1U];
    __Vtemp_22[2U] = (1U & __Vtemp_20[2U]);
    VL_ADD_W(3, __Vtemp_23, __Vtemp_12, __Vtemp_22);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_end[0U] 
        = __Vtemp_23[0U];
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_end[1U] 
        = __Vtemp_23[1U];
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_end[2U] 
        = (3U & __Vtemp_23[2U]);
    __Vtemp_25[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_base);
    __Vtemp_25[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_base 
                              >> 0x20U));
    __Vtemp_25[2U] = 0U;
    __Vtemp_26[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_bytes);
    __Vtemp_26[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_bytes 
                              >> 0x20U));
    __Vtemp_26[2U] = 0U;
    VL_ADD_W(3, __Vtemp_27, __Vtemp_25, __Vtemp_26);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_end[0U] 
        = __Vtemp_27[0U];
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_end[1U] 
        = __Vtemp_27[1U];
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_end[2U] 
        = (1U & __Vtemp_27[2U]);
    __Vtemp_29[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_base);
    __Vtemp_29[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_base 
                              >> 0x20U));
    __Vtemp_29[2U] = 0U;
    __Vtemp_30[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_bytes);
    __Vtemp_30[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_bytes 
                              >> 0x20U));
    __Vtemp_30[2U] = 0U;
    VL_ADD_W(3, __Vtemp_31, __Vtemp_29, __Vtemp_30);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_end[0U] 
        = __Vtemp_31[0U];
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_end[1U] 
        = __Vtemp_31[1U];
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_end[2U] 
        = (1U & __Vtemp_31[2U]);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__in_last 
        = (((IData)(1U) + vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__scalar_index) 
           == vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__scalar_count);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state_transition_end 
        = (0x1ffffffffULL & (1ULL + ((QData)((IData)(
                                                     vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_value[0U])) 
                                     + (QData)((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_count)))));
    __Vtemp_33[0U] = 0x20U;
    __Vtemp_33[1U] = 0U;
    __Vtemp_33[2U] = 0U;
    __Vtemp_34[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_base);
    __Vtemp_34[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_base 
                              >> 0x20U));
    __Vtemp_34[2U] = 0U;
    __Vtemp_35[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor);
    __Vtemp_35[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor 
                              >> 0x20U));
    __Vtemp_35[2U] = 0U;
    VL_ADD_W(3, __Vtemp_36, __Vtemp_34, __Vtemp_35);
    VL_ADD_W(3, __Vtemp_37, __Vtemp_33, __Vtemp_36);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[0U] 
        = __Vtemp_37[0U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[1U] 
        = __Vtemp_37[1U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[2U] 
        = (1U & __Vtemp_37[2U]);
    __Vtemp_39[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset);
    __Vtemp_39[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset 
                              >> 0x20U));
    __Vtemp_39[2U] = 0U;
    __Vtemp_40[0U] = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length;
    __Vtemp_40[1U] = 0U;
    __Vtemp_40[2U] = 0U;
    VL_ADD_W(3, __Vtemp_41, __Vtemp_39, __Vtemp_40);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end[0U] 
        = __Vtemp_41[0U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end[1U] 
        = __Vtemp_41[1U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end[2U] 
        = (1U & __Vtemp_41[2U]);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry_ok 
        = ((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[0U]) 
           & ((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[1U]) 
              & ((8U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[2U]) 
                 & ((8U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[3U]) 
                    & ((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[4U]) 
                       & ((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[5U]) 
                          & ((8U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[6U]) 
                             & ((8U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[7U]) 
                                & ((4U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[8U]) 
                                   & ((0x101U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[9U]) 
                                      & ((4U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[0xaU]) 
                                         & ((8U == 
                                             vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[0xbU]) 
                                            & ((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[0xcU] 
                                                == 
                                                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__configuration[4U]) 
                                               & (0U 
                                                  == 
                                                  ((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[0xdU] 
                                                    | vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[0xeU]) 
                                                   | vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry[0xfU])))))))))))))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_byte 
        = (0xffU & (((0U == (0x1fU & VL_SHIFTL_III(7,7,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_lane), 3U)))
                      ? 0U : (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data[
                              (((IData)(7U) + (0x7fU 
                                               & VL_SHIFTL_III(7,7,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_lane), 3U))) 
                               >> 5U)] << ((IData)(0x20U) 
                                           - (0x1fU 
                                              & VL_SHIFTL_III(7,7,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_lane), 3U))))) 
                    | (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data[
                       (3U & (VL_SHIFTL_III(7,7,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_lane), 3U) 
                              >> 5U))] >> (0x1fU & 
                                           VL_SHIFTL_III(7,7,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_lane), 3U)))));
    __Vtemp_45[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__terminal_byte_offset);
    __Vtemp_45[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__terminal_byte_offset 
                              >> 0x20U));
    __Vtemp_45[2U] = 0U;
    __Vtemp_46[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__path_index;
    __Vtemp_46[1U] = 0U;
    __Vtemp_46[2U] = 0U;
    VL_ADD_W(3, __Vtemp_47, __Vtemp_45, __Vtemp_46);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__raw_byte_index[0U] 
        = __Vtemp_47[0U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__raw_byte_index[1U] 
        = __Vtemp_47[1U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__raw_byte_index[2U] 
        = (1U & __Vtemp_47[2U]);
    __Vtemp_49[0U] = 3U;
    __Vtemp_49[1U] = 0U;
    __Vtemp_49[2U] = 0U;
    VL_ADD_W(3, __Vtemp_50, __Vtemp_49, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_end);
    if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_index))) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__allowed_table_end[0U] 
            = (0xfffffffcU & __Vtemp_50[0U]);
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__allowed_table_end[1U] 
            = __Vtemp_50[1U];
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__allowed_table_end[2U] 
            = (1U & __Vtemp_50[2U]);
    } else {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__allowed_table_end[0U] 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_end[0U];
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__allowed_table_end[1U] 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_end[1U];
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__allowed_table_end[2U] 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_end[2U];
    }
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal = 1U;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns = 0U;
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_outputs = 8U;
    if (((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]) 
         || (2U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]))) {
        bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_outputs = 8U;
    } else if (((4U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]) 
                || (5U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]))) {
        bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_outputs = 8U;
    }
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
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__selected_length 
        = ((0x4ffU >= (0x7ffU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U)))
            ? (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__lengths[
                                (((IData)(0x3fU) + 
                                  (0x7ffU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U))) 
                                 >> 5U)])) << ((0U 
                                                == 
                                                (0x1fU 
                                                 & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U)))
                                                ? 0x20U
                                                : ((IData)(0x40U) 
                                                   - 
                                                   (0x1fU 
                                                    & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U))))) 
               | (((0U == (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U)))
                    ? 0ULL : ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__lengths[
                                              (((IData)(0x1fU) 
                                                + (0x7ffU 
                                                   & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U))) 
                                               >> 5U)])) 
                              << ((IData)(0x20U) - 
                                  (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U))))) 
                  | ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__lengths[
                                     (0x3fU & (VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U) 
                                               >> 5U))])) 
                     >> (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index), 6U)))))
            : vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____Vxrand_h7d28236b__0);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__multiply_a 
        = (((9U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
            | (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)))
            ? (QData)((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_rows))
            : (QData)((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row)));
    __Vtemp_57[0U] = 0x20U;
    __Vtemp_57[1U] = 0U;
    __Vtemp_57[2U] = 0U;
    __Vtemp_58[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__merge_base);
    __Vtemp_58[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__merge_base 
                              >> 0x20U));
    __Vtemp_58[2U] = 0U;
    __Vtemp_59[0U] = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__search_middle;
    __Vtemp_59[1U] = 0U;
    __Vtemp_59[2U] = 0U;
    VL_SHIFTL_WWI(66,66,32, __Vtemp_60, __Vtemp_59, 4U);
    __Vtemp_61[0U] = ((IData)((QData)((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_word))) 
                      << 2U);
    __Vtemp_61[1U] = (((IData)((QData)((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_word))) 
                       >> 0x1eU) | ((IData)(((QData)((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_word)) 
                                             >> 0x20U)) 
                                    << 2U));
    __Vtemp_61[2U] = ((IData)(((QData)((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_word)) 
                               >> 0x20U)) >> 0x1eU);
    VL_ADD_W(3, __Vtemp_62, __Vtemp_60, __Vtemp_61);
    VL_ADD_W(3, __Vtemp_63, __Vtemp_58, __Vtemp_62);
    VL_ADD_W(3, __Vtemp_64, __Vtemp_57, __Vtemp_63);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_address[0U] 
        = __Vtemp_64[0U];
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_address[1U] 
        = __Vtemp_64[1U];
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_address[2U] 
        = (3U & __Vtemp_64[2U]);
    __Vtemp_66[0U] = 0x20U;
    __Vtemp_66[1U] = 0U;
    __Vtemp_66[2U] = 0U;
    __Vtemp_67[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__records_base);
    __Vtemp_67[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__records_base 
                              >> 0x20U));
    __Vtemp_67[2U] = 0U;
    __Vtemp_68[0U] = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_id;
    __Vtemp_68[1U] = 0U;
    __Vtemp_68[2U] = 0U;
    VL_SHIFTL_WWI(65,65,32, __Vtemp_69, __Vtemp_68, 4U);
    __Vtemp_70[0U] = ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word) 
                      << 2U);
    __Vtemp_70[1U] = 0U;
    __Vtemp_70[2U] = 0U;
    VL_ADD_W(3, __Vtemp_71, __Vtemp_69, __Vtemp_70);
    VL_ADD_W(3, __Vtemp_72, __Vtemp_67, __Vtemp_71);
    VL_ADD_W(3, __Vtemp_73, __Vtemp_66, __Vtemp_72);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[0U] 
        = __Vtemp_73[0U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[1U] 
        = __Vtemp_73[1U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[2U] 
        = (1U & __Vtemp_73[2U]);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__selected_length 
        = ((0x4ffU >= (0x7ffU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U)))
            ? (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__lengths[
                                (((IData)(0x3fU) + 
                                  (0x7ffU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U))) 
                                 >> 5U)])) << ((0U 
                                                == 
                                                (0x1fU 
                                                 & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U)))
                                                ? 0x20U
                                                : ((IData)(0x40U) 
                                                   - 
                                                   (0x1fU 
                                                    & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U))))) 
               | (((0U == (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U)))
                    ? 0ULL : ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__lengths[
                                              (((IData)(0x1fU) 
                                                + (0x7ffU 
                                                   & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U))) 
                                               >> 5U)])) 
                              << ((IData)(0x20U) - 
                                  (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U))))) 
                  | ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__lengths[
                                     (0x3fU & (VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U) 
                                               >> 5U))])) 
                     >> (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment), 6U)))))
            : vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____Vxrand_h7d28236b__0);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_length 
        = ((0x4ffU >= (0x7ffU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U)))
            ? (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__lengths[
                                (((IData)(0x3fU) + 
                                  (0x7ffU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U))) 
                                 >> 5U)])) << ((0U 
                                                == 
                                                (0x1fU 
                                                 & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U)))
                                                ? 0x20U
                                                : ((IData)(0x40U) 
                                                   - 
                                                   (0x1fU 
                                                    & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U))))) 
               | (((0U == (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U)))
                    ? 0ULL : ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__lengths[
                                              (((IData)(0x1fU) 
                                                + (0x7ffU 
                                                   & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U))) 
                                               >> 5U)])) 
                              << ((IData)(0x20U) - 
                                  (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U))))) 
                  | ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__lengths[
                                     (0x3fU & (VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U) 
                                               >> 5U))])) 
                     >> (0x1fU & VL_SHIFTL_III(11,11,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment), 6U)))))
            : vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h7d28236b__0);
    if ((0x10U >= (0x1fU & vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__depth))) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_node 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_node
            [(0x1fU & vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__depth)];
        __Vtemp_75[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_first
            [(0x1fU & vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__depth)];
        __Vtemp_76[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_cursor
            [(0x1fU & vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__depth)];
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_node 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__0;
        __Vtemp_75[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__1;
        __Vtemp_76[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__2;
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_id 
        = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_index))
            ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__left_id
            : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_index))
                ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__right_id
                : vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__result_id));
    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_kind))) {
        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_kind))) {
            vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_base 
                = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__accepts_base;
            vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_count 
                = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__accept_count;
        } else {
            vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_base 
                = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__tag_ops_base;
            vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_count 
                = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__tag_op_count;
        }
    } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_kind))) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_base 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__transitions_base;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_count 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__transition_count;
    } else {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_base 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__states_base;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_count 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state_count;
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows = 0U;
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_inputs = 8U;
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_groups = 1U;
    if ((1U & (~ ((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]) 
                  || (2U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]))))) {
        if ((1U & (~ ((4U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]) 
                      || (5U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]))))) {
            if ((6U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U])) {
                bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_inputs = 8U;
                bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_groups = 1U;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key = 0U;
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_in_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass)
            ? 0U : ((((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes)
                       ? (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count 
                          == (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes 
                              - (IData)(1U))) : (0xaU 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte))) 
                     << 8U) | ((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes)
                                ? (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte)
                                : (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_byte))));
    __Vtemp_75[1U] = 0U;
    __Vtemp_75[2U] = 0U;
    __Vtemp_76[1U] = 0U;
    __Vtemp_76[2U] = 0U;
    VL_ADD_W(3, __Vtemp_77, __Vtemp_75, __Vtemp_76);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_edge[0U] 
        = __Vtemp_77[0U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_edge[1U] 
        = __Vtemp_77[1U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_edge[2U] 
        = (1U & __Vtemp_77[2U]);
    if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state))) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_address = 0ULL;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_bytes = 0x20ULL;
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_address 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_address;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_bytes 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_bytes;
    }
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h3281ae77__0 
        = ((0U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[1U]) 
           & (0U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]));
    bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h55965d66__0 
        = ((1U > vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[1U]) 
           & (0U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_hee8b2130__0 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0x13U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__selected_scalar 
        = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__scalars
        [(0xfU & vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__scalar_index)];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0 
        = (vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data 
           >> ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_lane) 
               << 3U));
    VL_SHIFTL_WWI(130,130,32, __Vtemp_79, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work, 2U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[0U] 
        = (__Vtemp_79[0U] | (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[3U] 
                             >> 0x1eU));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[1U] 
        = __Vtemp_79[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[2U] 
        = __Vtemp_79[2U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[3U] 
        = __Vtemp_79[3U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[4U] 
        = (3U & __Vtemp_79[4U]);
    VL_SHIFTL_WWI(130,130,32, __Vtemp_83, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_83[0U] | (1U & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[4U]));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_83[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = __Vtemp_83[2U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[3U] 
        = __Vtemp_83[3U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[4U] 
        = (3U & __Vtemp_83[4U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_87, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_87[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_87[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_87[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_91, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_91[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_91[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_91[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_95, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_95[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_95[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_95[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_99, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_99[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                           >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_99[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_99[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_103, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_103[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                            >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_103[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_103[2U]);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    __Vtableidx6 = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__expected_record_bytes 
        = Vbench__ConstPool__TABLE_h109f7c34_0[__Vtableidx6];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__record_shift 
        = Vbench__ConstPool__TABLE_h93373b12_0[__Vtableidx6];
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows = 0U;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_inputs = 8U;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_groups = 1U;
    if ((1U & (~ ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)) 
                  || (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)))))) {
        if ((1U & (~ ((4U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)) 
                      || (5U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)))))) {
            if ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection))) {
                bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_inputs = 8U;
                bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_groups = 1U;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__publish 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_columns = 0U;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_columns = 0U;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs = 8U;
    if (((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)) 
         || (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)))) {
        bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs = 8U;
    } else if (((4U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)) 
                || (5U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)))) {
        bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs = 8U;
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (((((((((0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                   | (((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                       || (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) 
                      || (3U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))) 
                  | (4U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) 
                 | ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                    || (6U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))) 
                | (7U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) 
               | (8U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) 
              | ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                 || (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))) 
             | (0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))) {
            if ((0U != (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                if ((1U & (~ (((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                               || (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) 
                              || (3U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))))) {
                    if ((4U != (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                        if ((1U & (~ ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                                      || (6U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))))) {
                            if ((7U != (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                                if ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_key = 1U;
                                } else if (((9U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                                            || (0xaU 
                                                == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))) {
                                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_key = 1U;
                                }
                            }
                        }
                    }
                }
            }
            if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 1U;
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key 
                    = ((0U == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                       & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)));
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows = 0x101U;
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_columns = 8U;
            } else if ((((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                         || (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) 
                        || (3U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))) {
                if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_columns 
                        = bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs;
                } else {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 2U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_columns 
                        = VL_SHIFTR_III(32,32,32, bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs, 3U);
                }
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key 
                    = ((1U > vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                       & (6U >= (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)));
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows 
                    = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))
                        ? bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_inputs
                        : bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_groups);
            } else if ((4U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 1U;
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key 
                    = ((1U > vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                       & (2U >= (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)));
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows = 1U;
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_columns 
                    = bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs;
            } else {
                if (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                     || (6U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key 
                        = ((1U > vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)));
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows = 1U;
                } else if ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 1U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key 
                        = ((0U == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)));
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows = 1U;
                } else if ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 3U;
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key 
                        = ((((0U == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                             & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection))) 
                            & (0xfU > vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row)) 
                           & (0xdU != vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row));
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows = 0xfU;
                } else {
                    if (((9U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                         || (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)))) {
                        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 3U;
                        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key 
                            = ((1U > vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                               & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)));
                    } else {
                        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 4U;
                        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key 
                            = ((0U == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                               & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)));
                    }
                    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows = 4U;
                }
                vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_columns = 8U;
            }
        }
        vlSelf->bench__DOT__error_code = vlSelf->bench__DOT__dut__DOT__code;
        vlSelf->bench__DOT__ddr_req_addr = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_address;
        vlSelf->bench__DOT__ddr_req_wdata = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_data;
        vlSelf->bench__DOT__ddr_req_wstrb = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_strobes;
        vlSelf->bench__DOT__dut__DOT__divisor = vlSelf->bench__DOT__dut__DOT__configuration__DOT__divisor_r;
        vlSelf->bench__DOT__dut__DOT__eos_id = vlSelf->bench__DOT__dut__DOT__configuration__DOT__eos_r;
        vlSelf->bench__DOT__dut__DOT__maximum_tokens 
            = vlSelf->bench__DOT__dut__DOT__configuration__DOT__max_r;
        vlSelf->bench__DOT__dut__DOT__vocabulary = vlSelf->bench__DOT__dut__DOT__configuration__DOT__vocab_r;
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_columns 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_columns;
        if ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind))) {
            vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_columns 
                = (((3U == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row) 
                    || (4U == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row))
                    ? 8U : ((((9U == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row) 
                              || (0xaU == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row)) 
                             || (0xbU == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row))
                             ? 8U : ((0xdU == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row)
                                      ? 0U : 8U)));
        }
        vlSelf->bench__DOT__dut__DOT__core_mem_rsp_rdata 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__response_data;
    } else {
        vlSelf->bench__DOT__error_code = 0U;
        vlSelf->bench__DOT__ddr_req_addr = 0ULL;
        vlSelf->bench__DOT__ddr_req_wdata = 0U;
        vlSelf->bench__DOT__ddr_req_wstrb = 0U;
        vlSelf->bench__DOT__dut__DOT__divisor = 0U;
        vlSelf->bench__DOT__dut__DOT__eos_id = 0U;
        vlSelf->bench__DOT__dut__DOT__maximum_tokens = 0U;
        vlSelf->bench__DOT__dut__DOT__vocabulary = 0U;
        vlSelf->bench__DOT__dut__DOT__core_mem_rsp_rdata = 0U;
    }
    __Vtemp_107[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_offset);
    __Vtemp_107[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_offset 
                               >> 0x20U));
    __Vtemp_107[2U] = 0U;
    __Vtemp_108[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_extent);
    __Vtemp_108[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_extent 
                               >> 0x20U));
    __Vtemp_108[2U] = 0U;
    VL_ADD_W(3, __Vtemp_109, __Vtemp_107, __Vtemp_108);
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_end[0U] 
        = __Vtemp_109[0U];
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_end[1U] 
        = __Vtemp_109[1U];
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_end[2U] 
        = (3U & __Vtemp_109[2U]);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__active_multiply 
        = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
           | (3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted_operation 
        = ((0x19U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)) 
           | (0x1aU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__cache_data 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__cache_data)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_hit_0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_valid) 
           & ((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_kind
               [0U] == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
              & ((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_layer
                  [0U] == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                 & (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_projection
                    [0U] == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)))));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_hit_1 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_valid) 
            >> 1U) & ((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_kind
                       [1U] == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
                      & ((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_layer
                          [1U] == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer) 
                         & (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_projection
                            [1U] == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)))));
    bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____VdfgTmp_h69769b5a__0 
        = (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__byte_index 
           < vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_lengths
           [0U]);
    __Vtableidx3 = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane_shift 
        = Vbench__ConstPool__TABLE_h90db6da8_0[__Vtableidx3];
    __Vtableidx4 = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift 
        = Vbench__ConstPool__TABLE_h90db6da8_0[__Vtableidx4];
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_emit 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid) 
           & ((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes) 
              | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid)));
    vlSelf->__VdfgTmp_h1afe3993__0 = ((2U >= (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr))
                                       ? vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data
                                      [vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr]
                                       : (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT____Vxrand_h8d954d18__0));
    bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT____VdfgTmp_h3d13e98e__0 
        = (vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__left_id 
           == vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_left);
    bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar0_valid 
        = ((~ ((0xd800U <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U]) 
               & (0xdfffU >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U]))) 
           & (0x10ffffU >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U]));
    bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar1_valid 
        = ((~ ((0xd800U <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U]) 
               & (0xdfffU >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U]))) 
           & (0x10ffffU >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U]));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__key 
        = ((0x13U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))
            ? (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U])))
            : (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U])));
    vlSelf->bench__DOT__error = ((IData)(vlSelf->bench__DOT__rst_n) 
                                 & (9U == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->bench__DOT__done = ((IData)(vlSelf->bench__DOT__rst_n) 
                                & ((IData)(vlSelf->bench__DOT__dut__DOT__done_r) 
                                   & (9U != (IData)(vlSelf->bench__DOT__dut__DOT__state))));
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_haf19dc44__0 
        = (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_kind 
           == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind));
    vlSelf->bench__DOT__dut__DOT__serial_update = ((IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__serial_update_r) 
                                                   & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->__VdfgTmp_h5b2387d0__0 = ((2U >= (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr))
                                       ? vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data
                                      [vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr]
                                       : (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT____Vxrand_h8d954d18__0));
    vlSelf->bench__DOT__dut__DOT__loader_error = ((IData)(vlSelf->bench__DOT__rst_n) 
                                                  & (0xfU 
                                                     == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__publish_error = ((IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__publish_failed) 
                                                   & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hf663a351__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_previous) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync));
    vlSelf->bench__DOT__ddr_rsp_ready = ((IData)(vlSelf->bench__DOT__rst_n) 
                                         & (5U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & ((5U 
                                                  == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
                                                 | (0x14U 
                                                    == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state))));
    vlSelf->bench__DOT__dut__DOT__core_mem_rsp_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__response_error) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (6U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__reload_request = 
        ((IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__reload_r) 
         & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & ((4U 
                                                  == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
                                                 | (0x13U 
                                                    == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state))));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_h57a93df3__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__empty_frame_fault) 
           | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_fault));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_idle 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_mem_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (0x15U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classify_selected 
        = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state)) 
           | (3U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_selected 
        = ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
           | ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
              | ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
                 | (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)))));
    __Vtableidx5 = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected 
        = Vbench__ConstPool__TABLE_h554b41bf_0[__Vtableidx5];
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
           | ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
              | (3U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state))));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected 
        = ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
           | ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
              | ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
                 | (0x10U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h065bd496__0 
        = ((0xeU != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)) 
           & (0xfU != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    __Vtableidx1 = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state;
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected 
        = Vbench__ConstPool__TABLE_h7831209a_0[__Vtableidx1];
    vlSelf->bench__DOT__dut__DOT__loader_done = ((IData)(vlSelf->bench__DOT__rst_n) 
                                                 & (0xeU 
                                                    == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__io_rst_n = ((IData)(vlSelf->bench__DOT__dut__DOT__io_enabled) 
                                              & (IData)(vlSelf->bench__DOT__rst_n));
    __VdfgTmp_h77ceb880__0 = ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)) 
                              | (7U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)));
    __VdfgTmp_had546d50__0 = ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)) 
                              | (9U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_enabled) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    __Vtableidx2 = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__step;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected 
        = Vbench__ConstPool__TABLE_h1bfbab1a_0[__Vtableidx2];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__projection 
        = Vbench__ConstPool__TABLE_h2862d6e0_0[__Vtableidx2];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm_mode 
        = Vbench__ConstPool__TABLE_h400161fb_0[__Vtableidx2];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__element_mode 
        = Vbench__ConstPool__TABLE_h6243dc1f_0[__Vtableidx2];
    vlSelf->__VdfgTmp_h26c9701b__0 = ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__state)) 
                                      | (6U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__client_rst_n = ((IData)(vlSelf->bench__DOT__dut__DOT__clients_enabled) 
                                                  & (IData)(vlSelf->bench__DOT__rst_n));
    __Vtemp_111[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_address);
    __Vtemp_111[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_address 
                               >> 0x20U));
    __Vtemp_111[2U] = 0U;
    __Vtemp_112[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_bytes);
    __Vtemp_112[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_bytes 
                               >> 0x20U));
    __Vtemp_112[2U] = 0U;
    VL_ADD_W(3, __Vtemp_113, __Vtemp_111, __Vtemp_112);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__request_end[0U] 
        = __Vtemp_113[0U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__request_end[1U] 
        = __Vtemp_113[1U];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__request_end[2U] 
        = (1U & __Vtemp_113[2U]);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key = 0U;
    if (((((((((0U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
               | (((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
                   || (2U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) 
                  || (3U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))) 
              | (4U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) 
             | ((5U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
                || (6U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))) 
            | (7U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) 
           | (8U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) 
          | ((9U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
             || (0xaU == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))) 
         | (0xbU == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))) {
        if ((0U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 1U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns = 8U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows = 0x101U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key 
                = bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h3281ae77__0;
        } else if ((((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
                     || (2U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) 
                    || (3U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))) {
            if ((3U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 1U;
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns 
                    = bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_outputs;
            } else {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 2U;
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns 
                    = VL_SHIFTR_III(32,32,32, bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_outputs, 3U);
            }
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows 
                = ((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])
                    ? bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_inputs
                    : bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_groups);
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key 
                = ((1U > vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[1U]) 
                   & (6U >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]));
        } else if ((4U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 1U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns 
                = bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__projection_outputs;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows = 1U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key 
                = ((1U > vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[1U]) 
                   & (2U >= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[2U]));
        } else if (((5U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
                    || (6U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 1U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns = 8U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows = 1U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key 
                = bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h55965d66__0;
        } else if ((7U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 1U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns = 8U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows = 1U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key 
                = bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h3281ae77__0;
        } else if ((8U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 3U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns = 8U;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows = 0xfU;
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key 
                = bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h3281ae77__0;
        } else {
            if (((9U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
                 || (0xaU == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))) {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 3U;
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns = 8U;
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key 
                    = bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h55965d66__0;
            } else {
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = 4U;
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns = 8U;
                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key 
                    = bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____VdfgExtracted_h3281ae77__0;
            }
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows = 4U;
        }
        if ((0U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
            if ((1U & (~ (((1U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
                           || (2U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) 
                          || (3U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))))) {
                if ((4U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
                    if ((1U & (~ ((5U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
                                  || (6U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))))) {
                        if ((7U != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
                            if ((8U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U])) {
                                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__writable_key = 1U;
                            } else if (((9U == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]) 
                                        || (0xaU == 
                                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[0U]))) {
                                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__writable_key = 1U;
                            }
                        }
                    }
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_write 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_hee8b2130__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_write));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__input_end 
        = (0x1ffffffffULL & ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__byte_count)) 
                             + ((0x80U > vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__selected_scalar)
                                 ? 1ULL : ((0x800U 
                                            > vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__selected_scalar)
                                            ? 2ULL : 
                                           ((0x10000U 
                                             > vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__selected_scalar)
                                             ? 3ULL
                                             : 4ULL)))));
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__continued_scalar 
        = (0x1fffffU & (VL_SHIFTL_III(21,21,32, vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value, 6U) 
                        | (0x3fU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0)));
    __Vtemp_115[0U] = (1U | ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
                             << 2U));
    __Vtemp_115[1U] = (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
                        >> 0x1eU) | ((IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                                              >> 0x20U)) 
                                     << 2U));
    __Vtemp_115[2U] = ((IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                                >> 0x20U)) >> 0x1eU);
    __Vtemp_115[3U] = 0U;
    __Vtemp_115[4U] = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__subtract 
        = VL_GTE_W(5, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder, __Vtemp_115);
    __Vtemp_116[0U] = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[0U];
    __Vtemp_116[1U] = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[1U];
    __Vtemp_116[2U] = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[2U];
    __Vtemp_116[3U] = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[3U];
    __Vtemp_116[4U] = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[4U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(5, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_116);
    __Vtemp_117[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_117[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_117[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_117);
    __Vtemp_118[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_118[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_118[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_118);
    __Vtemp_119[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_119[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_119[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_119);
    __Vtemp_120[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_120[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_120[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_120);
    __Vtemp_121[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_121[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_121[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_121);
    vlSelf->bench__DOT__cfg_ready = ((~ ((IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__publish) 
                                         | (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_valid))) 
                                     & (IData)(vlSelf->bench__DOT__rst_n));
    __Vtemp_123[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__segment_bytes);
    __Vtemp_123[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__segment_bytes 
                               >> 0x20U));
    __Vtemp_123[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__descriptor_extent_valid 
        = ((0U == (((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__extent_value[0U] 
                     ^ (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_extent)) 
                    | (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__extent_value[1U] 
                       ^ (IData)((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_extent 
                                  >> 0x20U)))) | vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__extent_value[2U])) 
           & (IData)(((0U == bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_end[2U]) 
                      & VL_LTE_W(3, bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_end, __Vtemp_123))));
    if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__active_multiply) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply_b = 8ULL;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply_a 
            = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__active_vocab));
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply_b 
            = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[7U]));
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply_a 
            = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record[6U]));
    }
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
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_hit_index 
        = ((~ (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_hit_0)) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_hit_1));
    if (bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____VdfgTmp_h69769b5a__0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__source_offset 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_offsets
            [0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__source_index 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__byte_index;
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__source_offset 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_offsets
            [1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__source_index 
            = (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__byte_index 
               - vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_lengths
               [0U]);
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__weight_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__qw 
                   >> (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__zero_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__qz 
                   >> (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__weight_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw 
                   >> (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__zero_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz 
                   >> (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_equal 
        = ((IData)(bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT____VdfgTmp_h3d13e98e__0) 
           & (vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_right 
              == vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__right_id));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_before 
        = ((vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_left 
            < vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__left_id) 
           | ((IData)(bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT____VdfgTmp_h3d13e98e__0) 
              & (vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_right 
                 < vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__right_id)));
    __Vtemp_124[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[9U];
    __Vtemp_124[1U] = 0U;
    __Vtemp_124[2U] = 0U;
    __Vtemp_125[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[0xcU];
    __Vtemp_125[1U] = 0U;
    __Vtemp_125[2U] = 0U;
    __Vtemp_126[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[0xbU];
    __Vtemp_126[1U] = 0U;
    __Vtemp_126[2U] = 0U;
    __Vtemp_127[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_index;
    __Vtemp_127[1U] = 0U;
    __Vtemp_127[2U] = 0U;
    __Vtemp_128[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__dead_first_transition;
    __Vtemp_128[1U] = 0U;
    __Vtemp_128[2U] = 0U;
    __Vtemp_129[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_index;
    __Vtemp_129[1U] = 0U;
    __Vtemp_129[2U] = 0U;
    __Vtemp_131[0U] = 1U;
    __Vtemp_131[1U] = 0U;
    __Vtemp_131[2U] = 0U;
    __Vtemp_132[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__dead_first_transition;
    __Vtemp_132[1U] = 0U;
    __Vtemp_132[2U] = 0U;
    __Vtemp_133[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__class_count;
    __Vtemp_133[1U] = 0U;
    __Vtemp_133[2U] = 0U;
    VL_ADD_W(3, __Vtemp_134, __Vtemp_132, __Vtemp_133);
    VL_ADD_W(3, __Vtemp_135, __Vtemp_131, __Vtemp_134);
    __Vtemp_136[0U] = __Vtemp_135[0U];
    __Vtemp_136[1U] = __Vtemp_135[1U];
    __Vtemp_136[2U] = (1U & __Vtemp_135[2U]);
    __Vtemp_137[0U] = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[0xeU];
    __Vtemp_137[1U] = 0U;
    __Vtemp_137[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_legal 
        = (((((((((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index)) 
                  | (0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))) 
                 | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))) 
                | (0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))) 
               | (0x10U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))) 
              | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))) 
             | (0x12U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))) 
            | (0x13U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))) 
           && ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))
                ? (((((((IData)(bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar0_valid) 
                        & (IData)(bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar1_valid)) 
                       & (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U] 
                          <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U])) 
                      & (~ ((0xd800U > vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U]) 
                            & (0xd800U <= vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U])))) 
                     & (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U] 
                        == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__next_scalar)) 
                    & (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U] 
                       < vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__class_count)) 
                   & (0U == (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[3U] 
                             >> 0xaU))) : ((0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))
                                            ? ((((0U 
                                                  == 
                                                  vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[3U]) 
                                                 & VL_LTE_W(3, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__first_end, __Vtemp_124)) 
                                                & VL_LTE_W(3, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__second_end, __Vtemp_125)) 
                                               & ((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_index 
                                                   != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__dead_state) 
                                                  | (0U 
                                                     == 
                                                     vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U])))
                                            : ((0xdU 
                                                == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))
                                                ? (
                                                   (((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U] 
                                                      < 
                                                      vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts[8U]) 
                                                     & (0U 
                                                        == 
                                                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[3U])) 
                                                    & VL_LTE_W(3, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__first_end, __Vtemp_126)) 
                                                   & (~ 
                                                      ((VL_GTE_W(3, __Vtemp_127, __Vtemp_128) 
                                                        & VL_LT_W(3, __Vtemp_129, __Vtemp_136)) 
                                                       & ((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U] 
                                                           != vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__dead_state) 
                                                          | (0U 
                                                             != 
                                                             vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U])))))
                                                : (
                                                   (0xfU 
                                                    == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))
                                                    ? 
                                                   ((((3U 
                                                       >= 
                                                       vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U]) 
                                                      & (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U] 
                                                         < vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__tag_count)) 
                                                     & (0U 
                                                        == 
                                                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[3U])) 
                                                    & (((3U 
                                                         == 
                                                         vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U]) 
                                                        & (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U] 
                                                           < vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__tag_count)) 
                                                       | ((3U 
                                                           != 
                                                           vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[0U]) 
                                                          & (0U 
                                                             == 
                                                             vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U]))))
                                                    : 
                                                   ((0x10U 
                                                     == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))
                                                     ? 
                                                    (((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[1U] 
                                                       < vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__tag_count) 
                                                      & (1U 
                                                         >= 
                                                         vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U])) 
                                                     & (0U 
                                                        == 
                                                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[3U]))
                                                     : 
                                                    ((0x11U 
                                                      == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))
                                                      ? 
                                                     (((((IData)(bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar0_valid) 
                                                         & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__previous_valid)) 
                                                            | (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__key 
                                                               > vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__previous_key))) 
                                                        & (0U 
                                                           != 
                                                           vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U])) 
                                                       & (1U 
                                                          >= 
                                                          vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[3U])) 
                                                      & VL_LTE_W(3, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__first_end, __Vtemp_137))
                                                      : 
                                                     ((0x12U 
                                                       == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index))
                                                       ? (IData)(bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar0_valid)
                                                       : 
                                                      (((((IData)(bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar0_valid) 
                                                          & (IData)(bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__scalar1_valid)) 
                                                         & ((~ 
                                                             ((0xd800U 
                                                               <= 
                                                               vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U]) 
                                                              & (0xdfffU 
                                                                 >= 
                                                                 vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U]))) 
                                                            & (0x10ffffU 
                                                               >= 
                                                               vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[2U]))) 
                                                        & (0U 
                                                           == 
                                                           vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data[3U])) 
                                                       & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__previous_valid)) 
                                                          | (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__key 
                                                             > vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__previous_key)))))))))));
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_h304f5f27__0 
        = ((IData)(bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_haf19dc44__0) 
           & (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_layer 
              == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer));
    vlSelf->bench__DOT__dut__DOT__live_ddr_error = 
        ((IData)(vlSelf->bench__DOT__ddr_rsp_valid) 
         & ((IData)(vlSelf->bench__DOT__ddr_rsp_error) 
            & (IData)(vlSelf->bench__DOT__ddr_rsp_ready)));
    vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0) 
           & (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)));
    vlSelf->bench__DOT__dut__DOT__boot_rsp_valid = 
        ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0) 
         & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)));
    vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0) 
           & (1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)));
    vlSelf->bench__DOT__dut__DOT__receiving = ((IData)(vlSelf->bench__DOT__dut__DOT__admitted) 
                                               & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__abort_r)) 
                                                  & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__reload_request)) 
                                                     & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__serial_update)) 
                                                        & ((4U 
                                                            == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                                           | ((5U 
                                                               == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                                              | (6U 
                                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__state))))))));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__healthy 
        = (1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__framing_fault)) 
                 & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__overflow_fault) 
                       | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_h57a93df3__0)))));
    vlSelf->bench__DOT__dut__DOT__memory_idle = ((IData)(vlSelf->bench__DOT__rst_n) 
                                                 & ((0U 
                                                     == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state)) 
                                                    & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_idle)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____VdfgTmp_hf61b8ee4__0 
        = (1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected)) 
                 & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected) 
                       | (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_selected)))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage 
        = ((IData)(vlSelf->bench__DOT__rst_n) & ((0U 
                                                  != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)) 
                                                 & ((1U 
                                                     != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)) 
                                                    & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h065bd496__0))));
    if (vlSelf->bench__DOT__dut__DOT__loader_done) {
        vlSelf->bench__DOT__dut__DOT__table_bases[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[8U];
        vlSelf->bench__DOT__dut__DOT__table_bases[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[9U];
        vlSelf->bench__DOT__dut__DOT__table_bases[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xaU];
        vlSelf->bench__DOT__dut__DOT__table_bases[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xbU];
        vlSelf->bench__DOT__dut__DOT__table_bases[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xcU];
        vlSelf->bench__DOT__dut__DOT__table_bases[5U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xdU];
        vlSelf->bench__DOT__dut__DOT__table_bases[6U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xeU];
        vlSelf->bench__DOT__dut__DOT__table_bases[7U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xfU];
        vlSelf->bench__DOT__dut__DOT__table_bases[8U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x10U];
        vlSelf->bench__DOT__dut__DOT__table_bases[9U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x11U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xaU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x12U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xbU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x13U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xcU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x14U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xdU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x15U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xeU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x16U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xfU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x17U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x10U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x18U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x11U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x19U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x12U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1aU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x13U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1bU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x14U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1cU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x15U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1dU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x16U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1eU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x17U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1fU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x18U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x20U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x19U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x21U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1aU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x22U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1bU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x23U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1cU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x24U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1dU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x25U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1eU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x26U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1fU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x27U];
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xbU])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xaU])));
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xdU])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xcU])));
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[1U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[2U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[4U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[5U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[5U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[6U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[6U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[7U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[7U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[8U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[8U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[9U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[9U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xaU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xaU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xbU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xbU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xcU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xcU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xdU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xdU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xeU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xeU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xfU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xfU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x10U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x10U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x11U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x11U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x12U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x12U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x13U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x13U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x14U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x14U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x15U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x15U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x16U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x16U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x17U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x17U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x18U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x18U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x19U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x19U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1aU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1aU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1bU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1bU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1cU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1cU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1dU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1dU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1eU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1eU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1fU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1fU];
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xeU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[1U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[2U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[3U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[4U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[5U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[5U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[6U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[6U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[7U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[7U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[8U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[8U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[9U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[9U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xaU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xaU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xbU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xbU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xcU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xcU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xdU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xdU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xeU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xeU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xfU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xfU];
        vlSelf->bench__DOT__dut__DOT__committed_config[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[0U];
        vlSelf->bench__DOT__dut__DOT__committed_config[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[1U];
        vlSelf->bench__DOT__dut__DOT__committed_config[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[2U];
        vlSelf->bench__DOT__dut__DOT__committed_config[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[3U];
        vlSelf->bench__DOT__dut__DOT__committed_config[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[4U];
        vlSelf->bench__DOT__dut__DOT__committed_config[5U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[5U];
        vlSelf->bench__DOT__dut__DOT__committed_config[6U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[6U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x17U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x16U])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x23U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x22U])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x25U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x24U])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x27U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x26U])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[7U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[9U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xdU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xeU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xfU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_states_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x19U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x18U])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_transitions_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1bU])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1aU])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_ops_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1fU])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x1eU])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_accepts_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x21U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x20U])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_byte_map_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xfU])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xeU])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_merge_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x11U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0x10U])));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_vocab_size 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[2U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_max_pretoken_bytes 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xfU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_start_state 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xaU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_dead_state 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xbU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_register_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xcU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_state_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[8U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_transition_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[9U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_op_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xbU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_accept_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xcU];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_merge_count 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[4U];
        vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9e465c1b__0 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[4U];
        vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9ef3e9a0__0 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[5U];
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_directory_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[3U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[2U])));
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_immutable_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[5U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[4U])));
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_writable_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[7U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[6U])));
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_immutable_bytes 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_lengths[5U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_lengths[4U])));
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_writable_bytes 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_lengths[7U])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_lengths[6U])));
    } else {
        vlSelf->bench__DOT__dut__DOT__table_bases[0U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0U];
        vlSelf->bench__DOT__dut__DOT__table_bases[1U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[1U];
        vlSelf->bench__DOT__dut__DOT__table_bases[2U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[2U];
        vlSelf->bench__DOT__dut__DOT__table_bases[3U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[3U];
        vlSelf->bench__DOT__dut__DOT__table_bases[4U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[4U];
        vlSelf->bench__DOT__dut__DOT__table_bases[5U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[5U];
        vlSelf->bench__DOT__dut__DOT__table_bases[6U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[6U];
        vlSelf->bench__DOT__dut__DOT__table_bases[7U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[7U];
        vlSelf->bench__DOT__dut__DOT__table_bases[8U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[8U];
        vlSelf->bench__DOT__dut__DOT__table_bases[9U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[9U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xaU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xbU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xcU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xdU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xeU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0xfU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xfU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x10U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x10U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x11U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x11U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x12U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x12U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x13U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x13U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x14U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x14U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x15U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x15U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x16U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x16U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x17U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x17U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x18U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x18U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x19U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x19U];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1aU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1aU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1bU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1bU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1cU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1cU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1dU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1dU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1eU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1eU];
        vlSelf->bench__DOT__dut__DOT__table_bases[0x1fU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1fU];
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[1U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[1U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[2U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[2U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[3U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[3U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[4U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[4U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[5U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[5U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[6U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[6U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[7U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[7U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[8U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[8U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[9U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[9U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xaU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xbU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xcU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xdU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xeU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0xfU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xfU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x10U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x10U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x11U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x11U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x12U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x12U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x13U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x13U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x14U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x14U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x15U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x15U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x16U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x16U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x17U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x17U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x18U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x18U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x19U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x19U];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1aU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1aU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1bU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1bU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1cU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1cU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1dU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1dU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1eU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1eU];
        vlSelf->bench__DOT__dut__DOT__committed_metadata[0x1fU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1fU];
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_counts[0U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[1U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[1U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[2U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[2U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[3U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[3U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[4U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[4U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[5U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[5U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[6U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[6U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[7U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[7U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[8U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[8U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[9U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[9U];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xaU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xbU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xcU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xdU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xeU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__committed_counts[0xfU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xfU];
        vlSelf->bench__DOT__dut__DOT__committed_config[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[6U] = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_states_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_transitions_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_ops_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_accepts_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_byte_map_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_merge_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_vocab_size = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_max_pretoken_bytes = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_start_state = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_dead_state = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_register_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_state_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_transition_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_op_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_accept_count = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_merge_count = 0U;
        vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9e465c1b__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9ef3e9a0__0 = 0U;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_directory_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_immutable_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_writable_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_immutable_bytes = 0ULL;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_writable_bytes = 0ULL;
    }
    vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count 
        = (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__loader_done)
                            ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[2U]
                            : 0U)));
    vlSelf->bench__DOT__boot_done = ((IData)(vlSelf->bench__DOT__rst_n) 
                                     & ((IData)(vlSelf->bench__DOT__dut__DOT__admitted) 
                                        & (IData)(vlSelf->bench__DOT__dut__DOT__loader_done)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_core_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & ((IData)(vlSelf->bench__DOT__dut__DOT__loader_done) 
                                                 & (0U 
                                                    == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state))));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_pop 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass)
               ? (IData)(vlSelf->bench__DOT__m_axis_tready)
               : (~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_active))));
    vlSelf->bench__DOT__dut__DOT__overflow_error = 
        ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__overflow_fault) 
         & (IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n));
    vlSelf->bench__DOT__dut__DOT__framing_error = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
                                                   & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__framing_fault) 
                                                      | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_h57a93df3__0)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_empty 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & (0U != (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count)));
    bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_he9711bd6__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_state)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_empty 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & (0U != (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count)));
    if (__VdfgTmp_h77ceb880__0) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 = 1U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected = 1U;
    } else if (__VdfgTmp_had546d50__0) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 = 2U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected = 2U;
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected = 0U;
    }
    vlSelf->bench__DOT__spi_cs_n = (1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n)) 
                                          | ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state)) 
                                             | (5U 
                                                == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state)))));
    vlSelf->bench__DOT__spi_sck = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__clock_level) 
                                   & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0x25U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0x18U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__busy 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & ((0U != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)) 
              & ((0x19U != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)) 
                 & (0x1aU != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)) 
              | ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)) 
                 | ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)) 
                    | (0x13U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state))))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_in_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_in_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____Vcellinp__validator__DOT__multiply__in_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
              | (0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____Vcellinp__validator__DOT__multiply__out_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state)) 
              | (0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader_in_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader_out_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (6U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader_in_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader_out_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (6U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader_in_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader_out_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (6U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__stage_error 
        = ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
             & (0x1cU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__state))) 
            << 5U) | ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
                        & (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__state))) 
                       << 4U) | ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
                                   & (0x19U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__state))) 
                                  << 3U) | ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
                                              & (0x26U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state))) 
                                             << 2U) 
                                            | ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
                                                 & (0xfU 
                                                    == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__state))) 
                                                << 1U) 
                                               | ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
                                                  & (0x1aU 
                                                     == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state))))))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__stage_codes 
        = (((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n)
                              ? (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__code)
                              : 0U))) << 0x28U) | (
                                                   ((QData)((IData)(
                                                                    ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n)
                                                                      ? (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__code)
                                                                      : 0U))) 
                                                    << 0x20U) 
                                                   | (QData)((IData)(
                                                                     ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n)
                                                                         ? (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__code)
                                                                         : 0U) 
                                                                       << 0x18U) 
                                                                      | ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n)
                                                                            ? (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__code)
                                                                            : 0U) 
                                                                          << 0x10U) 
                                                                         | ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n)
                                                                               ? (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__code)
                                                                               : 0U) 
                                                                             << 8U) 
                                                                            | ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n)
                                                                                ? (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__code)
                                                                                : 0U))))))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_out_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (6U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_out_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (6U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    if (((((((((0U == vlSelf->bench__DOT__cfg_addr) 
               | (4U == vlSelf->bench__DOT__cfg_addr)) 
              | (8U == vlSelf->bench__DOT__cfg_addr)) 
             | (0xcU == vlSelf->bench__DOT__cfg_addr)) 
            | (0x10U == vlSelf->bench__DOT__cfg_addr)) 
           | (0x14U == vlSelf->bench__DOT__cfg_addr)) 
          | (0x18U == vlSelf->bench__DOT__cfg_addr)) 
         | (0x1cU == vlSelf->bench__DOT__cfg_addr))) {
        if ((0U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable = 0U;
        }
        if ((0U != vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal 
                = ((4U == vlSelf->bench__DOT__cfg_addr)
                    ? (4U <= vlSelf->bench__DOT__cfg_wdata)
                    : ((8U == vlSelf->bench__DOT__cfg_addr)
                        ? (vlSelf->bench__DOT__cfg_wdata 
                           < vlSelf->bench__DOT__dut__DOT__configuration__DOT__vocab_r)
                        : ((0xcU == vlSelf->bench__DOT__cfg_addr)
                            ? (4U >= vlSelf->bench__DOT__cfg_wdata)
                            : ((0x10U == vlSelf->bench__DOT__cfg_addr)
                                ? (1U >= vlSelf->bench__DOT__cfg_wdata)
                                : ((0x14U == vlSelf->bench__DOT__cfg_addr)
                                    ? ((1U <= vlSelf->bench__DOT__cfg_wdata) 
                                       & (4U >= vlSelf->bench__DOT__cfg_wdata))
                                    : ((0x18U == vlSelf->bench__DOT__cfg_addr)
                                        ? (((0x100U 
                                             <= vlSelf->bench__DOT__cfg_wdata) 
                                            & (0x40000U 
                                               >= vlSelf->bench__DOT__cfg_wdata)) 
                                           & (0x101U 
                                              >= vlSelf->bench__DOT__cfg_wdata))
                                        : (1U == vlSelf->bench__DOT__cfg_wdata)))))));
        }
    } else {
        if ((0x20U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable = 0U;
        } else if ((0x24U != vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable = 0U;
        }
        if ((0x20U != vlSelf->bench__DOT__cfg_addr)) {
            if ((0x24U != vlSelf->bench__DOT__cfg_addr)) {
                vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal = 0U;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0x19U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__special_trie__ddr_rsp_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__profile__ddr_rsp_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__tokens__ddr_rsp_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__directory__ddr_rsp_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__manifest__ddr_rsp_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__image_loader__ddr_rsp_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0x17U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__special_trie__ddr_req_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__profile__ddr_req_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__tokens__ddr_req_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__directory__ddr_req_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__manifest__ddr_req_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loader_write 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
           & (0x16U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state)));
    if (vlSelf->bench__DOT__dut__DOT__client_rst_n) {
        vlSelf->bench__DOT__dut__DOT__core_token_valid 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state));
        vlSelf->bench__DOT__dut__DOT__token_ready = 
            (1U == (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__busy 
            = ((0U != (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)) 
               & ((0xeU != (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state)) 
                  & (0xfU != (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state))));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__decode_valid 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__start 
            = (6U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__utf8__start 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____VdfgTmp_h67e2c008__0 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__start 
            = (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__busy 
            = ((0U != (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
               & ((0x12U != (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state)) 
                  & (0x13U != (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state))));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoder_in_ready 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoding__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoder_valid 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoding__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_in_ready 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_in_ready 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__encoding__start 
            = (4U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__start 
            = (7U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_valid 
            = (6U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_valid 
            = (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__generated_ready 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__finish_valid 
            = (6U == (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_token_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber8 
            = (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 
            = (0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber7 
            = (0x23U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber7 
            = (0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 
            = (0x17U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_valid 
            = (4U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_error 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiply_ready 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy)));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiply_valid 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_a = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_b = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__dut__DOT__generated_id 
            = vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_id;
        vlSelf->bench__DOT__dut__DOT__core_token_id 
            = vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__issue_id;
        vlSelf->bench__DOT__dut__DOT__core_logit_index 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__buffered_index;
        vlSelf->bench__DOT__dut__DOT__core_logit_data 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__buffered_logit;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_index 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__vocabulary;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__product 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_value 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result[0U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result[1U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result[2U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result[3U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result;
        if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_a 
                = (((- (QData)((IData)((1U & ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__delta) 
                                              >> 4U))))) 
                    << 5U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__delta)));
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_b 
                = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__scale_integer));
        } else if ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_a 
                = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__activation 
                                                >> 0x1fU))))) 
                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__activation)));
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_b 
                = (((QData)((IData)((0x7ffffffU & (- (IData)(
                                                             (1U 
                                                              & (IData)(
                                                                        (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__dequantized_weight 
                                                                         >> 0x24U)))))))) 
                    << 0x25U) | vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__dequantized_weight);
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__x;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__cosine;
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__y;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__sine;
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__y;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__cosine;
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__product_index))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_a 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__x;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_b 
                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__sine;
        }
        if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a 
                = (((- (QData)((IData)((1U & ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta) 
                                              >> 4U))))) 
                    << 5U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta)));
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b 
                = (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scale_integer));
        } else if ((0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a 
                = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation 
                                                >> 0x1fU))))) 
                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation)));
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b 
                = (((QData)((IData)((0x7ffffffU & (- (IData)(
                                                             (1U 
                                                              & (IData)(
                                                                        (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight 
                                                                         >> 0x24U)))))))) 
                    << 0x25U) | vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight);
        }
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[0U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[1U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[2U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[3U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[4U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_kind 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_layer 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_proj 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_row 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_col 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_wdata 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__controller_code 
            = vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code;
        vlSelf->bench__DOT__dut__DOT__tokenizer_code 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__code;
        vlSelf->bench__DOT__dut__DOT__detokenizer_code 
            = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__kd;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__ly;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__pj;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__rw;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__cl;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wd;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__kd;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__kd;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__ly;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__ly;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__pj;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__pj;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__rw;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__rw;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__cl;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__cl;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wd;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wd;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____VdfgTmp_h115be047__0 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_done 
            = (0x16U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_valid 
            = (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_valid 
            = (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_valid 
            = (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_valid 
            = (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__generated_valid 
            = (5U == (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state));
        vlSelf->bench__DOT__dut__DOT__token_valid = 
            (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_logit_valid 
            = (0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber19 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber19 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_logit_valid 
            = (((2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__state)) 
                | (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__state))) 
               & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__holding));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber7 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__state));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 
            = (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 
            = (0x17U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_rsp_ready 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_valid 
            = (0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__utf8__out_ready 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__decode_ready 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__state));
        vlSelf->bench__DOT__dut__DOT__text_valid = 
            (((0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state)) 
              & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_valid)) 
             | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state)));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT____VdfgTmp_he886f039__0 
            = (1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__abort_r)));
        vlSelf->bench__DOT__dut__DOT__core_logit_ready 
            = ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state)) 
               & (vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count 
                  < vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_valid 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_write 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__wr;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__controller_error 
            = (7U == (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_done = (4U 
                                                   == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_tbl_ready 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_tbl_ready 
            = (7U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_tbl_ready 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_tbl_ready 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_ready 
            = (4U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer_error 
            = (0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__detokenizer_error 
            = (0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__detokenizer_req_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_tbl_valid 
            = (7U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_tbl_valid 
            = (6U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_tbl_valid 
            = (7U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_tbl_valid 
            = (7U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber9 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber9 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active 
            = (6U > vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected);
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wr;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wr;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active 
            = (2U > ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                      ? 1U : 0U));
    } else {
        vlSelf->bench__DOT__dut__DOT__core_token_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__token_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__busy = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__decode_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__start = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__utf8__start = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____VdfgTmp_h67e2c008__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__start = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__busy = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoder_in_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoder_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_in_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_in_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__encoding__start = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__start = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__generated_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__finish_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_token_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber7 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_error = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiply_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiply_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_a = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_b = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = 0ULL;
        vlSelf->bench__DOT__dut__DOT__generated_id = 0U;
        vlSelf->bench__DOT__dut__DOT__core_token_id = 0U;
        vlSelf->bench__DOT__dut__DOT__core_logit_index = 0U;
        vlSelf->bench__DOT__dut__DOT__core_logit_data = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_index = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__product = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_value = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U] = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U] = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U] = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U] = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient = 0ULL;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_kind = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_layer = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_proj = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_row = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_col = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_wdata = 0U;
        vlSelf->bench__DOT__dut__DOT__controller_code = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer_code = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer_code = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber17 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18 = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____VdfgTmp_h115be047__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_done = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__generated_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__token_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_logit_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber19 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber19 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_logit_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber7 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_rsp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__utf8__out_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__decode_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__text_valid = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT____VdfgTmp_he886f039__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_logit_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_write = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__controller_error = 0U;
        vlSelf->bench__DOT__dut__DOT__core_done = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_tbl_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_tbl_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_tbl_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_tbl_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_ready = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__port_idle = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer_error = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer_error = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer_req_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_tbl_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_tbl_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_tbl_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_tbl_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_equal 
        = ((IData)(bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_h304f5f27__0) 
           & (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_projection 
              == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_later 
        = ((vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_kind 
            > (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind)) 
           | (((IData)(bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_haf19dc44__0) 
               & (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_layer 
                  > vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer)) 
              | ((IData)(bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_h304f5f27__0) 
                 & (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_projection 
                    > (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection)))));
    if (vlSelf->bench__DOT__dut__DOT__boot_rsp_valid) {
        vlSelf->bench__DOT__dut__DOT__boot_rsp_data 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data;
        vlSelf->bench__DOT__dut__DOT__boot_rsp_error 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error;
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_rsp_data = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_rsp_error = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_valid) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_rdata 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data;
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_error 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error;
    } else {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_rdata = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_error = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid) {
        vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_data 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data;
        vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_error 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_rsp_valid 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_rsp_valid 
            = (1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_rsp_valid 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected));
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_rsp_valid 
            = (3U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected));
    } else {
        vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_data = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_error = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_rsp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_rsp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_rsp_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_rsp_valid = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__receive_open 
        = ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_closed)) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__receiving));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hb418d625__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__healthy));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h54a152fa__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h556532b1__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
           & (1U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h54b96fd4__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
           & (2U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h4f5601d0__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
           & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h06bb2786__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
           & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h07af84a6__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
           & (5U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected)));
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__bundle_legal 
        = ((4U <= ((IData)(vlSelf->bench__DOT__dut__DOT__loader_done)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[0U]
                    : 0U)) & ((1U >= ((IData)(vlSelf->bench__DOT__dut__DOT__loader_done)
                                       ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[3U]
                                       : 0U)) & ((1U 
                                                  <= vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9e465c1b__0) 
                                                 & ((4U 
                                                     >= vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9e465c1b__0) 
                                                    & ((0x100U 
                                                        <= vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9ef3e9a0__0) 
                                                       & ((0x40000U 
                                                           >= vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9ef3e9a0__0) 
                                                          & ((0x101U 
                                                              >= vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9ef3e9a0__0) 
                                                             & ((((IData)(vlSelf->bench__DOT__dut__DOT__loader_done)
                                                                   ? 
                                                                  vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[1U]
                                                                   : 0U) 
                                                                 < vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9ef3e9a0__0) 
                                                                & (4U 
                                                                   >= 
                                                                   ((IData)(vlSelf->bench__DOT__dut__DOT__loader_done)
                                                                     ? 
                                                                    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[2U]
                                                                     : 0U))))))))));
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_match 
        = (1U & (((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__profile_pending)) 
                  | (vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_profile 
                     == vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9e465c1b__0)) 
                 & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__vocab_pending)) 
                    | (vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_vocab 
                       == vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9ef3e9a0__0))));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_context_matches 
        = ((vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_directory_base 
            == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_base) 
           & ((0x20U == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_count) 
              & ((vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_immutable_base 
                  == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_base) 
                 & ((vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_immutable_bytes 
                     == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_bytes) 
                    & ((vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_writable_base 
                        == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_base) 
                       & (vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_writable_bytes 
                          == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_bytes))))));
    vlSelf->bench__DOT__dut__DOT__core_token_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
           & ((IData)(vlSelf->bench__DOT__boot_done) 
              & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__state))));
    vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__status 
        = (((IData)(vlSelf->bench__DOT__error) << 3U) 
           | (((IData)(vlSelf->bench__DOT__done) << 2U) 
              | ((((IData)(vlSelf->bench__DOT__rst_n) 
                   & ((4U != (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                      & (9U != (IData)(vlSelf->bench__DOT__dut__DOT__state)))) 
                  << 1U) | (IData)(vlSelf->bench__DOT__boot_done))));
    vlSelf->bench__DOT__dut__DOT__core_mem_req_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__abort_r)) 
                                                 & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_core_ready)));
    vlSelf->bench__DOT__dut__DOT__io_tx_idle = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
                                                & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_active)) 
                                                   & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_empty)));
    vlSelf->bench__DOT__m_axis_tvalid = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
                                         & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass) 
                                            & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_valid)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__pop 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_pop));
    bench__DOT__dut__DOT__io_rx_idle = ((IData)(bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_he9711bd6__0) 
                                        & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_empty) 
                                           & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid)) 
                                              & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid)) 
                                                 & ((0U 
                                                     == vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count) 
                                                    & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hf663a351__0))))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
           & (3U > vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected));
    if (((~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_out_valid))) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[5U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[6U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[7U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[8U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[9U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xaU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xbU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xcU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xdU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xeU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xfU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xfU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x10U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x10U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x11U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x11U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x12U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x12U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x13U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x13U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x14U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x14U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x15U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x15U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x16U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x16U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x17U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x17U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x18U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x18U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x19U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x19U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1aU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1aU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1bU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1bU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1cU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1cU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1dU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1dU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1eU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1eU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1fU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1fU];
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[1U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[2U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[3U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[4U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[5U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[6U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[7U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[8U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[9U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xaU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xbU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xcU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xdU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xeU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0xfU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xfU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x10U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x10U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x11U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x11U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x12U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x12U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x13U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x13U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x14U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x14U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x15U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x15U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x16U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x16U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x17U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x17U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x18U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x18U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x19U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x19U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1aU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1aU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1bU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1bU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1cU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1cU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1dU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1dU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1eU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1eU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data[0x1fU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1fU];
    }
    if (((~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_out_valid))) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[5U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[6U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[7U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[8U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[9U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xaU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xbU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xcU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xdU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xeU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xfU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0xfU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x10U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x10U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x11U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x11U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x12U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x12U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x13U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x13U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x14U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x14U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x15U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x15U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x16U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x16U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x17U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x17U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x18U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x18U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x19U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x19U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1aU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1aU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1bU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1bU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1cU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1cU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1dU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1dU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1eU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1eU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1fU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result[0x1fU];
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[1U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[2U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[3U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[4U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[5U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[6U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[7U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[8U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[9U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xaU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xbU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xcU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xdU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xeU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0xfU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xfU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x10U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x10U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x11U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x11U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x12U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x12U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x13U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x13U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x14U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x14U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x15U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x15U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x16U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x16U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x17U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x17U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x18U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x18U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x19U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x19U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1aU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1aU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1bU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1bU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1cU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1cU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1dU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1dU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1eU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1eU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data[0x1fU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1fU];
    }
    if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest_valid) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[5U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[6U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[7U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[8U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[9U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xaU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xbU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xcU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xdU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xeU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xfU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0xfU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x10U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x10U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x11U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x11U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x12U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x12U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x13U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x13U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x14U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x14U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x15U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x15U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x16U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x16U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x17U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x17U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x18U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x18U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x19U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x19U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1aU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x1aU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1bU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x1bU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1cU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x1cU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1dU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x1dU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1eU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x1eU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1fU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata[0x1fU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[5U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[6U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[7U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[8U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[9U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xaU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xbU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xcU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xdU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xeU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xfU] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts[0xfU];
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[1U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[2U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[3U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[4U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[5U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[6U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[7U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[8U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[9U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xaU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xbU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xcU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xdU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xeU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xfU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xfU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x10U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x10U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x11U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x11U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x12U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x12U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x13U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x13U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x14U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x14U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x15U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x15U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x16U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x16U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x17U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x17U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x18U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x18U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x19U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x19U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1aU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1aU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1bU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1bU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1cU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1cU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1dU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1dU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1eU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1eU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1fU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1fU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[1U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[2U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[3U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[4U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[5U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[6U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[7U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[8U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[9U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xaU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xbU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xcU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xdU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xeU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xfU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xfU];
    }
    if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[0U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
            [0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[1U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
            [1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[2U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
            [2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[3U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
            [3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[4U] 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
            [4U];
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[4U] = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[5U] 
        = (IData)((((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                                      ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
                                     [6U] : 0U))) << 0x20U) 
                   | (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                                       ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
                                      [5U] : 0U)))));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[6U] 
        = (IData)(((((QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                                       ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
                                      [6U] : 0U))) 
                     << 0x20U) | (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                                                   ? 
                                                  vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words
                                                  [5U]
                                                   : 0U)))) 
                   >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[1U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[2U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [1U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[3U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [1U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[4U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [2U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[5U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [2U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[6U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [3U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[7U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [3U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[8U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [4U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[9U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [4U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0xaU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [5U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0xbU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [5U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0xcU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [6U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0xdU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [6U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0xeU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [7U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0xfU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [7U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x10U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [8U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x11U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [8U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x12U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [9U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x13U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [9U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x14U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0xaU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x15U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0xaU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x16U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0xbU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x17U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0xbU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x18U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0xcU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x19U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0xcU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x1aU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0xdU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x1bU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0xdU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x1cU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0xeU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x1dU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0xeU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x1eU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0xfU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x1fU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0xfU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x20U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0x10U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x21U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0x10U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x22U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0x11U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x23U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0x11U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x24U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0x12U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x25U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0x12U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x26U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                   [0x13U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[0x27U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases
                    [0x13U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[1U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[2U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [1U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[3U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [1U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[4U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [2U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[5U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [2U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[6U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [3U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[7U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [3U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[8U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [4U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[9U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [4U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0xaU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [5U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0xbU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [5U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0xcU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [6U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0xdU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [6U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0xeU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [7U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0xfU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [7U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x10U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [8U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x11U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [8U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x12U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [9U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x13U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [9U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x14U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0xaU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x15U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0xaU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x16U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0xbU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x17U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0xbU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x18U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0xcU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x19U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0xcU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x1aU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0xdU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x1bU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0xdU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x1cU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0xeU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x1dU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0xeU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x1eU] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0xfU] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x1fU] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0xfU] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x20U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0x10U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x21U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0x10U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x22U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0x11U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x23U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0x11U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x24U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0x12U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x25U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0x12U] : 0ULL) >> 0x20U));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x26U] 
        = (IData)(((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                    ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                   [0x13U] : 0ULL));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[0x27U] 
        = (IData)((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)
                     ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths
                    [0x13U] : 0ULL) >> 0x20U));
    if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data_valid) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data_last 
            = (1ULL == vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__bytes_left);
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__byte_result;
    } else {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data_last = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__boot_req_valid = 
        ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
         & ((5U >= (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected))
             ? ((((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__special_trie__ddr_req_valid) 
                  << 5U) | (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__profile__ddr_req_valid) 
                             << 4U) | (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__tokens__ddr_req_valid) 
                                        << 3U) | (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__directory__ddr_req_valid) 
                                                   << 2U) 
                                                  | (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__manifest__ddr_req_valid) 
                                                      << 1U) 
                                                     | (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loader_write)))))) 
                >> (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected))
             : (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__0)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_done) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__failed));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor));
    VL_NEGATE_W(5, __Vtemp_185, bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U] 
            = __Vtemp_185[0U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U] 
            = __Vtemp_185[1U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U] 
            = __Vtemp_185[2U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U] 
            = __Vtemp_185[3U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[4U] 
            = (1U & __Vtemp_185[4U]);
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U] 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[0U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U] 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[1U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U] 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[2U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U] 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[3U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[4U] 
            = (1U & bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient[4U]);
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__ready 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4) 
            << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term_negative)
            ? (- vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient)
            : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_last 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_valid) 
           & (((IData)(1U) + vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__output_index) 
              == vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__token_count));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_data 
        = (((~ (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__failed)) 
            & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_valid))
            ? vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__result_data
            : 0U);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_last 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_valid) 
           & (((IData)(1U) + vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__output_index) 
              == vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__token_count));
    if (((~ (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed)) 
         & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_valid))) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data[0U] 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[0U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data[1U] 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[1U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data[2U] 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[2U];
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data[3U] 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data[3U];
    } else {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data[3U] = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__finish_ready = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
                                                  & (((~ (IData)(vlSelf->bench__DOT__dut__DOT__generated_valid)) 
                                                      & (1U 
                                                         == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) 
                                                     | (0xeU 
                                                        == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))));
    if (vlSelf->bench__DOT__dut__DOT__token_valid) {
        vlSelf->bench__DOT__dut__DOT__token_id = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__output_token;
        vlSelf->bench__DOT__dut__DOT__token_last = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__output_last;
    } else {
        vlSelf->bench__DOT__dut__DOT__token_id = 0U;
        vlSelf->bench__DOT__dut__DOT__token_last = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__finished 
        = (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8) 
            << 1U) | (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__faults 
        = ((((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber8) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed)) 
            << 1U) | ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber8) 
                      & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed)));
    if (vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_valid) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_start_byte 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__anchor_byte;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_end_byte 
            = vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__best_end_byte;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_last 
            = (vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__best_end_index 
               == vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__scalar_count);
    } else {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_start_byte = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_end_byte = 0U;
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_last = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__io_rx_ready = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
                                                 & ((6U 
                                                     == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                                    & ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__utf8__out_ready) 
                                                       & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__decode_ready))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data = 0U;
    if (((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
         & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__port_idle))) {
        if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 0U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 7U : 9U));
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 6U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 0xcU : 0xaU));
        } else if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                    ? 7U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                             ? 0U : 0xbU));
        }
        if ((1U != (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            if ((3U != (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__output_value;
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__write_data = 0U;
    if (((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
         & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__port_idle))) {
        if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__mode))
                    ? 0U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__mode))
                             ? 7U : 9U));
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__mode))
                    ? 6U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__mode))
                             ? 0xcU : 0xaU));
        } else if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__issue = 1U;
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__row 
                = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__mode))
                    ? 7U : ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__mode))
                             ? 0U : 0xbU));
        }
        if ((1U != (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state))) {
            if ((3U != (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state))) {
                if ((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__write_request = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__write_data 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__output_value;
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT____Vcellinp__edge_io__tx_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT____VdfgTmp_he886f039__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__text_valid));
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__accept_logit 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_logit_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_logit_ready));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_logit_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
           & ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__state)) 
              & ((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_count 
                  >= vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__active_vocabulary) 
                 | ((~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__holding)) 
                    | (IData)(vlSelf->bench__DOT__dut__DOT__core_logit_ready)))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__col = 0U;
    if (((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
         & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state) 
                          >> 3U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_request 
                                = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)) 
                                   | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)));
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_data 
                                = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))
                                    ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_y
                                    : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_x);
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__row 
                                = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__key_vector)
                                    ? 3U : 2U);
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__col 
                                = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)) 
                                    | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)))
                                    ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_y
                                    : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_x);
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__kind = 8U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_request 
                            = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)) 
                               | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)));
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_data 
                            = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))
                                ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_y
                                : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_x);
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__row 
                            = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__key_vector)
                                ? 3U : 2U);
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__col 
                            = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)) 
                                | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)))
                                ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_y
                                : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_x);
                    }
                }
            } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state) 
                                 >> 1U)))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__kind = 0xbU;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__position;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__col 
                        = (VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__pair_index, 1U) 
                           + ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))
                               ? 1U : 0U));
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__kind = 0xbU;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__position;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__col 
                        = (VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__pair_index, 1U) 
                           + ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))
                               ? 1U : 0U));
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__kind = 8U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__row 
                    = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__key_vector)
                        ? 3U : 2U);
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__col 
                    = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)) 
                        | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)))
                        ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_y
                        : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_x);
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state) 
                          >> 1U)))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_request 
                        = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)) 
                           | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)));
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_data 
                        = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))
                            ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_y
                            : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_x);
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__kind = 8U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_request 
                    = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)) 
                       | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)));
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_data 
                    = ((0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state))
                        ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_y
                        : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_x);
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__row 
                    = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__key_vector)
                        ? 3U : 2U);
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__col 
                    = (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)) 
                        | (0x11U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state)))
                        ? vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_y
                        : vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_x);
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
         & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__port_idle))) {
        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state) 
                      >> 4U)))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__activation;
                        }
                    }
                }
            }
            if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__kind = 0U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__vocabulary;
                        }
                    }
                } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__activation_reuse_valid)))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__row = 0xeU;
                        }
                    }
                }
            } else {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__kind = 0U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component;
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__token;
                        }
                    }
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_error = ((IData)(vlSelf->bench__DOT__dut__DOT__core_done) 
                                                & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__failed));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__row = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__col = 0U;
    if (((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
         & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__port_idle))) {
        if ((0x20U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                                  >> 2U)))) {
                        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                                      >> 1U)))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)))) {
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__write_request = 1U;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__issue = 1U;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kind = 8U;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__write_data 
                                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__output_value;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__row = 5U;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__col 
                                    = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__head_base 
                                       + vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__component);
                            }
                        }
                    }
                }
            }
        } else {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                          >> 4U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                                      >> 1U)))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__write_request = 1U;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__write_data 
                                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__cache_data;
                            }
                        }
                    }
                }
            }
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__issue = 1U;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kind = 0xaU;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__row 
                                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__time_index;
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__col 
                                    = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kv_base 
                                       + vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__component);
                            }
                        }
                    }
                }
            } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kind = 9U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__time_index;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__col 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__k_column;
                        }
                    } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kind = 8U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__row = 2U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__q_column;
                    }
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kind 
                            = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__value_cache)
                                ? 0xaU : 9U);
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__position;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__col 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__index;
                    }
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__row 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__value_cache)
                            ? 4U : 3U);
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__index;
                }
            }
        }
        if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                      >> 5U)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_layer 
                                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__layer;
                            }
                        }
                    }
                }
            } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                              >> 2U)))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state)))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__layer;
                        }
                    }
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__layer;
                    }
                }
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_projection = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
         & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__output_value;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__col 
                                = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__c 
                                   + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane));
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__target_slot;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__kind = 4U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__col 
                            = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__c 
                               + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane));
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_projection 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__projection;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__layer;
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__kind = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_projection 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__projection;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__layer;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__col 
                            = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__c, 3U);
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__k;
                    }
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__k;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__source_slot;
                }
            } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__kind = 3U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__col 
                    = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__c 
                       + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane));
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__group_index;
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_projection 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__projection;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_layer 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__layer;
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__kind = 2U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_projection 
                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__projection;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_layer 
                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__layer;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__col 
                    = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__c, 3U);
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__group_index;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col = 0U;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row = 0U;
    if (((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
         & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__port_idle))) {
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 3U)))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 8U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__output_value;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                                = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                                   + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot;
                        }
                    }
                } else if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                     >> 1U)))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 4U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                            = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                               + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                    }
                }
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 2U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                                = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                        }
                    }
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 1U)))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                            = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c, 3U);
                        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k;
                    }
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 8U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot;
                }
            } else if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 3U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                    = (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                       + (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane));
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index;
            }
            if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                          >> 1U)))) {
                if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                        = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = 2U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = 1U;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection 
                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer 
                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer;
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col 
                    = VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c, 3U);
                vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row 
                    = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index;
            }
        }
    }
    vlSelf->bench__DOT__dut__DOT__input_fault = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_error) 
                                                 & ((0x30U 
                                                     != (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_code)) 
                                                    & (0x31U 
                                                       != (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_code))));
    vlSelf->bench__DOT__dut__DOT__output_fault = ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_error) 
                                                  & ((0x30U 
                                                      != (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_code)) 
                                                     & (0x31U 
                                                        != (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_code))));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (5U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (3U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (2U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (1U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (0U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
           & (4U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected));
    __Vtemp_202[0U] = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18;
    __Vtemp_202[1U] = (IData)((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                                << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))));
    __Vtemp_202[2U] = (IData)(((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                                 << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))) 
                               >> 0x20U));
    __Vtemp_202[3U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                        << 3U) | (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15));
    __Vtemp_202[4U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                        << 9U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10) 
                                   << 8U) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12) 
                                              << 7U) 
                                             | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13) 
                                                 << 3U) 
                                                | (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                                                   >> 0x1dU)))));
    __Vtemp_202[5U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                        >> 0x17U) | ((IData)((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                               << 0x20U) 
                                              | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                                     << 9U));
    __Vtemp_202[6U] = (((IData)((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                  << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                        >> 0x17U) | ((IData)(((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                                << 0x20U) 
                                               | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                              >> 0x20U)) 
                                     << 9U));
    __Vtemp_202[7U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
                        << 0xcU) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15) 
                                     << 9U) | ((IData)(
                                                       ((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                                          << 0x20U) 
                                                         | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                                        >> 0x20U)) 
                                               >> 0x17U)));
    __Vtemp_202[8U] = (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10) 
                        << 0x11U) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12) 
                                      << 0x10U) | (
                                                   ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13) 
                                                    << 0xcU) 
                                                   | (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
                                                      >> 0x14U))));
    if ((0x111U >= (0x1ffU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                 ? 1U
                                                 : 0U))))) {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_202[((IData)(1U) + 
                                      (0xfU & (((IData)(0x89U) 
                                                * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_202[(0xfU & (((IData)(0x89U) 
                                        * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                            ? 1U : 0U)) 
                                       >> 5U))] >> 
                  (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                               ? 1U
                                               : 0U)))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_202[((IData)(2U) + 
                                      (0xfU & (((IData)(0x89U) 
                                                * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_202[((IData)(1U) + (0xfU 
                                              & (((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)) 
                                                 >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_202[((IData)(3U) + 
                                      (0xfU & (((IData)(0x89U) 
                                                * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_202[((IData)(2U) + (0xfU 
                                              & (((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)) 
                                                 >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_202[((IData)(4U) + 
                                      (0xfU & (((IData)(0x89U) 
                                                * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)))))) 
               | (__Vtemp_202[((IData)(3U) + (0xfU 
                                              & (((IData)(0x89U) 
                                                  * 
                                                  ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U)) 
                                                 >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                  ? 1U
                                                  : 0U)))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                               ? 1U
                                               : 0U))))
                           ? 0U : (__Vtemp_202[((IData)(5U) 
                                                + (0xfU 
                                                   & (((IData)(0x89U) 
                                                       * 
                                                       ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                         ? 1U
                                                         : 0U)) 
                                                      >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * 
                                                   ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                     ? 1U
                                                     : 0U)))))) 
                         | (__Vtemp_202[((IData)(4U) 
                                         + (0xfU & 
                                            (((IData)(0x89U) 
                                              * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                  ? 1U
                                                  : 0U)) 
                                             >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                             ? 1U : 0U))))));
    } else {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) 
           & (1U == ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                      ? 1U : 0U)));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) 
           & (0U == ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                      ? 1U : 0U)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__tbl_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_valid 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hb418d625__0) 
            & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__receive_open)) 
           & ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass))) 
              && (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_emit)));
    vlSelf->bench__DOT__dut__DOT__io_rx_valid = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hb418d625__0) 
                                                 & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__row_base_hit 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__loader_done) 
           & ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_context_matches) 
              & ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__transaction_cacheable) 
                 & (((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_valid) 
                     >> (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__descriptor_cache_index)) 
                    & (((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_row_valid) 
                        >> (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__descriptor_cache_index)) 
                       & (vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_row
                          [vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__descriptor_cache_index] 
                          == vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row))))));
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value = 0U;
    if (((((((((0U == vlSelf->bench__DOT__cfg_addr) 
               | (4U == vlSelf->bench__DOT__cfg_addr)) 
              | (8U == vlSelf->bench__DOT__cfg_addr)) 
             | (0xcU == vlSelf->bench__DOT__cfg_addr)) 
            | (0x10U == vlSelf->bench__DOT__cfg_addr)) 
           | (0x14U == vlSelf->bench__DOT__cfg_addr)) 
          | (0x18U == vlSelf->bench__DOT__cfg_addr)) 
         | (0x1cU == vlSelf->bench__DOT__cfg_addr))) {
        if ((0U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__status;
        } else if ((4U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT__configuration__DOT__divisor_r;
        } else if ((8U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT__configuration__DOT__eos_r;
        } else if ((0xcU == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT__configuration__DOT__max_r;
        } else if ((0x10U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT__configuration__DOT__transport_r;
        } else if ((0x14U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_profile;
        } else if ((0x18U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_vocab;
        }
    } else if ((0x20U == vlSelf->bench__DOT__cfg_addr)) {
        vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
            = vlSelf->bench__DOT__dut__DOT__code;
    } else if ((0x24U == vlSelf->bench__DOT__cfg_addr)) {
        vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
            = vlSelf->bench__DOT__dut__DOT__configuration__DOT__frame_r;
    }
    if (vlSelf->bench__DOT__m_axis_tvalid) {
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_valid) {
            vlSelf->bench__DOT__m_axis_tlast = ((IData)(vlSelf->__VdfgTmp_h1afe3993__0) 
                                                >> 8U);
            vlSelf->bench__DOT__m_axis_tdata = (0xffU 
                                                & (IData)(vlSelf->__VdfgTmp_h1afe3993__0));
        } else {
            vlSelf->bench__DOT__m_axis_tlast = 0U;
            vlSelf->bench__DOT__m_axis_tdata = 0U;
        }
    } else {
        vlSelf->bench__DOT__m_axis_tlast = 0U;
        vlSelf->bench__DOT__m_axis_tdata = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__io_tx_ready = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
                                                 & ((3U 
                                                     > (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count)) 
                                                    | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__pop)));
    vlSelf->bench__DOT__dut__DOT__reload_allowed = 
        ((IData)(vlSelf->bench__DOT__rst_n) & (((4U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                                | (9U 
                                                   == (IData)(vlSelf->bench__DOT__dut__DOT__state))) 
                                               & ((~ 
                                                   ((IData)(vlSelf->bench__DOT__rst_n) 
                                                    & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h065bd496__0))) 
                                                  & ((IData)(vlSelf->bench__DOT__dut__DOT__memory_idle) 
                                                     & ((IData)(vlSelf->bench__DOT__dut__DOT__io_tx_idle) 
                                                        & (((IData)(bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_he9711bd6__0) 
                                                            & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid)) 
                                                               & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hf663a351__0))) 
                                                           & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__reload_request)) 
                                                              & ((9U 
                                                                  == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                                                 | (IData)(bench__DOT__dut__DOT__io_rx_idle)))))))));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h6323ea89__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active) 
           & (2U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h632b4bf4__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active) 
           & (0U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h62f58b69__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active) 
           & (1U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__assembled_word 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data) 
            << 0x18U) | (0xffffffU & vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__word_buffer));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__pop 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid) 
           & ((IData)(vlSelf->bench__DOT__dut__DOT__io_rx_ready) 
              & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__healthy)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__paths_idle 
        = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_state)) 
           & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_active)) 
              & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_empty) 
                 & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_empty) 
                    & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid)) 
                       & ((0U == vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count) 
                          & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid)) 
                             & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync) 
                                & ((~ (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__edge_io__tx_valid)) 
                                   & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_previous))))))))));
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__frame_complete 
        = ((vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count 
            == vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary) 
           | ((IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__accept_logit) 
              & (vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count 
                 == (vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary 
                     - (IData)(1U)))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_transfer 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_logit_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_logit_ready));
    vlSelf->bench__DOT__dut__DOT__fault = 0U;
    vlSelf->bench__DOT__dut__DOT__fault_code = 0U;
    if ((((IData)(vlSelf->bench__DOT__rst_n) & (9U 
                                                != (IData)(vlSelf->bench__DOT__dut__DOT__state))) 
         & (~ (IData)(vlSelf->bench__DOT__dut__DOT__reload_request)))) {
        if (vlSelf->bench__DOT__dut__DOT__loader_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code 
                = ((IData)(vlSelf->bench__DOT__rst_n)
                    ? (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__code)
                    : 0U);
        } else if (vlSelf->bench__DOT__dut__DOT__live_ddr_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code = 4U;
        } else if (vlSelf->bench__DOT__dut__DOT__publish_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code = 6U;
        } else if (vlSelf->bench__DOT__dut__DOT__input_fault) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code 
                = vlSelf->bench__DOT__dut__DOT__tokenizer_code;
        } else if (vlSelf->bench__DOT__dut__DOT__output_fault) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code 
                = vlSelf->bench__DOT__dut__DOT__detokenizer_code;
        } else if (vlSelf->bench__DOT__dut__DOT__core_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code 
                = ((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n)
                    ? (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__code)
                    : 0U);
        } else if ((((IData)(vlSelf->bench__DOT__dut__DOT__controller_error) 
                     & (0x30U != (IData)(vlSelf->bench__DOT__dut__DOT__controller_code))) 
                    & (0x31U != (IData)(vlSelf->bench__DOT__dut__DOT__controller_code)))) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code 
                = vlSelf->bench__DOT__dut__DOT__controller_code;
        } else if (vlSelf->bench__DOT__dut__DOT__tokenizer_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code 
                = vlSelf->bench__DOT__dut__DOT__tokenizer_code;
        } else if (vlSelf->bench__DOT__dut__DOT__detokenizer_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code 
                = vlSelf->bench__DOT__dut__DOT__detokenizer_code;
        } else if (vlSelf->bench__DOT__dut__DOT__controller_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code 
                = vlSelf->bench__DOT__dut__DOT__controller_code;
        } else if (vlSelf->bench__DOT__dut__DOT__framing_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code = 0x40U;
        } else if (vlSelf->bench__DOT__dut__DOT__overflow_error) {
            vlSelf->bench__DOT__dut__DOT__fault = 1U;
            vlSelf->bench__DOT__dut__DOT__fault_code = 0x41U;
        }
    }
    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 
            = (1U & (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                     >> 8U));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 
            = (1U & (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                     >> 7U));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 
            = (0xfU & (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                       >> 3U));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
            = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[4U] 
                << 0x1dU) | (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U] 
                             >> 3U));
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 
            = (7U & bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[3U]);
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[2U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[0U];
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 = 0U;
    }
    if (vlSelf->bench__DOT__dut__DOT__io_rx_valid) {
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid) {
            vlSelf->bench__DOT__dut__DOT__io_rx_last 
                = ((IData)(vlSelf->__VdfgTmp_h5b2387d0__0) 
                   >> 8U);
            vlSelf->bench__DOT__dut__DOT__io_rx_data 
                = (0xffU & (IData)(vlSelf->__VdfgTmp_h5b2387d0__0));
        } else {
            vlSelf->bench__DOT__dut__DOT__io_rx_last = 0U;
            vlSelf->bench__DOT__dut__DOT__io_rx_data = 0U;
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__io_rx_last = 0U;
        vlSelf->bench__DOT__dut__DOT__io_rx_data = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__write_allowed = ((IData)(vlSelf->bench__DOT__rst_n) 
                                                   & ((4U 
                                                       == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                                      & ((IData)(vlSelf->bench__DOT__dut__DOT__admitted) 
                                                         & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__reload_request)) 
                                                            & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__serial_update)) 
                                                               & ((IData)(bench__DOT__dut__DOT__io_rx_idle) 
                                                                  & ((IData)(vlSelf->bench__DOT__dut__DOT__io_tx_idle) 
                                                                     & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__io_rx_valid)) 
                                                                        & (IData)(vlSelf->bench__DOT__dut__DOT__memory_idle)))))))));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_scalar 
        = (VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__scalar, 6U) 
           | ((IData)(vlSelf->bench__DOT__dut__DOT__io_rx_valid)
               ? ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid)
                   ? (0x3fU & (IData)(vlSelf->__VdfgTmp_h5b2387d0__0))
                   : 0U) : 0U));
    vlSelf->bench__DOT__dut__DOT__text_ready = ((IData)(vlSelf->bench__DOT__dut__DOT____VdfgTmp_he886f039__0) 
                                                & (IData)(vlSelf->bench__DOT__dut__DOT__io_tx_ready));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__push 
        = ((IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__edge_io__tx_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__io_tx_ready));
    if (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h6323ea89__0) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber11 
            = vlSelf->bench__DOT__dut__DOT__core_mem_req_ready;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber21 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_rdata;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber22 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber19 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_valid;
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber11 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber21 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber22 = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber19 = 0U;
    }
    if (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h632b4bf4__0) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_req_ready 
            = vlSelf->bench__DOT__dut__DOT__core_mem_req_ready;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_rdata 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_rdata;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_error 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_valid 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_valid;
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_req_ready = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_rdata = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_error = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_valid = 0U;
    }
    if (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h62f58b69__0) {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10 
            = vlSelf->bench__DOT__dut__DOT__core_mem_req_ready;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_error;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_rdata;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18 
            = vlSelf->bench__DOT__dut__DOT__core_mem_rsp_valid;
    } else {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18 = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & ((3U > (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count)) 
              | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__pop)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__frame_complete 
        = ((0x101U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_count) 
           | ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_transfer) 
              & (0x100U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_count)));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_invalid 
        = ((2U != ((IData)(vlSelf->bench__DOT__dut__DOT__io_rx_valid)
                    ? ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid)
                        ? (3U & ((IData)(vlSelf->__VdfgTmp_h5b2387d0__0) 
                                 >> 6U)) : 0U) : 0U)) 
           | ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__remaining)) 
              & ((vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_scalar 
                  < vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__minimum_scalar) 
                 | ((0x10ffffU < vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_scalar) 
                    | ((0xd800U <= vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_scalar) 
                       & (0xdfffU >= vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_scalar))))));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_rsp_ready) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__norm____pinNumber11 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber11 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber10 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber10 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber11 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber21 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber21 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber22 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__norm____pinNumber22 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber21));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__norm____pinNumber21 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber20 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber20 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber21 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber18 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6b8ead47__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber18 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb569cc__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber19 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75229de2__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__norm____pinNumber19 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h6bb6cca2__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75d30c27__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____VdfgTmp_h75247847__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__decoder____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__push 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_ready));
    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__fault 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_error;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__read_data 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_rdata;
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__read_data = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber11 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber11 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber10));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber22 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21));
    if (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber21;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20;
    } else {
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22 = 0U;
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21 = 0U;
    }
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber19) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber19) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7a913e59__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19 
        = ((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h7b2ffeda__0) 
           & (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__mlp____pinNumber18));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__complete)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__complete)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber20
            : 0U);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__complete)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber21
            : 0U);
    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__fault 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber22;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__read_data 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber21;
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__read_data = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__read_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete)
            ? bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber21
            : 0U);
    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber22;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data 
            = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber21;
    } else {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault = 0U;
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data = 0U;
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
        VL_DBG_MSGF("         'act' region trigger index 0 is active: @(negedge bench.clk)\n");
    }
    if ((2ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 1 is active: @(posedge bench.clk)\n");
    }
    if ((4ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 2 is active: @(negedge bench.spi_cs_n)\n");
    }
    if ((8ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 3 is active: @(posedge bench.spi_sck)\n");
    }
    if ((0x10ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 4 is active: @(negedge bench.spi_sck)\n");
    }
    if ((0x20ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 5 is active: @(edge bench.clk)\n");
    }
    if ((0x40ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 6 is active: @(posedge bench.clk or negedge bench.rst_n)\n");
    }
    if ((0x80ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 7 is active: @(posedge bench.clk or negedge bench.dut.io_rst_n)\n");
    }
    if ((0x100ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 8 is active: @(posedge bench.clk or negedge bench.dut.client_rst_n)\n");
    }
    if ((0x200ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 9 is active: @(posedge bench.clk or negedge bench.dut.boot_loader.epoch_rst_n)\n");
    }
    if ((0x400ULL & vlSelf->__VactTriggered.word(0U))) {
        VL_DBG_MSGF("         'act' region trigger index 10 is active: @([true] __VdlySched.awaitingCurrentTime())\n");
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
        VL_DBG_MSGF("         'nba' region trigger index 0 is active: @(negedge bench.clk)\n");
    }
    if ((2ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 1 is active: @(posedge bench.clk)\n");
    }
    if ((4ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 2 is active: @(negedge bench.spi_cs_n)\n");
    }
    if ((8ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 3 is active: @(posedge bench.spi_sck)\n");
    }
    if ((0x10ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 4 is active: @(negedge bench.spi_sck)\n");
    }
    if ((0x20ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 5 is active: @(edge bench.clk)\n");
    }
    if ((0x40ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 6 is active: @(posedge bench.clk or negedge bench.rst_n)\n");
    }
    if ((0x80ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 7 is active: @(posedge bench.clk or negedge bench.dut.io_rst_n)\n");
    }
    if ((0x100ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 8 is active: @(posedge bench.clk or negedge bench.dut.client_rst_n)\n");
    }
    if ((0x200ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 9 is active: @(posedge bench.clk or negedge bench.dut.boot_loader.epoch_rst_n)\n");
    }
    if ((0x400ULL & vlSelf->__VnbaTriggered.word(0U))) {
        VL_DBG_MSGF("         'nba' region trigger index 10 is active: @([true] __VdlySched.awaitingCurrentTime())\n");
    }
}
#endif  // VL_DEBUG

VL_ATTR_COLD void Vbench___024root___ctor_var_reset(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___ctor_var_reset\n"); );
    // Body
    vlSelf->bench__DOT____Vxrand_h8d93fe75__1 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__clk = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__rst_n = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__ddr_cal_done = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__spi_miso = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__uart_rx = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__m_axis_tready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__m_axis_tvalid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__m_axis_tlast = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__done = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__m_axis_tdata = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__cfg_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__cfg_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__cfg_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__cfg_addr = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__cfg_wdata = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__cfg_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__cfg_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__running = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__out_held = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__held_output = VL_RAND_RESET_I(9);
    vlSelf->bench__DOT__expect_rejection = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__control_requests = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__control_responses = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__reload_events = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__outputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__completions = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__cache_k_writes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__cache_v_writes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__inference_reads = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__inference_writes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__embedding_reads = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__operation_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__embedding_index = VL_RAND_RESET_I(32);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->bench__DOT__expected_tokens[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__spi_sck = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__spi_cs_n = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__ddr_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__ddr_req_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__ddr_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__boot_done = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__ddr_req_addr = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__ddr_req_wdata = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__ddr_req_wstrb = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__error_code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__ddr_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__ddr_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__ddr_rsp_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__ddr_rsp_rdata = VL_RAND_RESET_I(32);
    for (int __Vi0 = 0; __Vi0 < 65536; ++__Vi0) {
        vlSelf->bench__DOT__flash[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 65536; ++__Vi0) {
        vlSelf->bench__DOT__ddr[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 8192; ++__Vi0) {
        vlSelf->bench__DOT__write_address[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 20; ++__Vi0) {
        vlSelf->bench__DOT__segment_base[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 20; ++__Vi0) {
        vlSelf->bench__DOT__segment_length[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 8192; ++__Vi0) {
        vlSelf->bench__DOT__write_data[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 8192; ++__Vi0) {
        vlSelf->bench__DOT__write_strobe[__Vi0] = VL_RAND_RESET_I(4);
    }
    vlSelf->bench__DOT__command_shift = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__spi_command_bits = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__flash_address = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__flash_bit = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__spi_reads = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__rng = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__pending = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__held = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__loading = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(101, vlSelf->bench__DOT__held_payload);
    vlSelf->bench__DOT__pending_address = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__cycle = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__writes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__reads = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__acknowledgements = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__delay_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__request_stalls = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__response_stalls = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__comparisons = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__clients_enabled = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__io_enabled = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__admitted = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__abort_r = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__done_r = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__controller_finished = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer_finished = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__fault_code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__client_rst_n = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__io_rst_n = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__loader_done = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__loader_error = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(224, vlSelf->bench__DOT__dut__DOT__committed_config);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__committed_metadata);
    VL_RAND_RESET_W(512, vlSelf->bench__DOT__dut__DOT__committed_counts);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__table_bases);
    vlSelf->bench__DOT__dut__DOT__divisor = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__eos_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__maximum_tokens = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__vocabulary = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__reload_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__publish_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__serial_update = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__io_rx_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__io_rx_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__io_rx_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__io_tx_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__io_rx_data = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__io_tx_idle = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__framing_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__overflow_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__receiving = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__engine_start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__token_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__token_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__token_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__token_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer_code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__generated_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__generated_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__generated_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__finish_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__finish_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__controller_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__controller_code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__text_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__text_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer_code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__core_token_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_token_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_token_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_logit_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_logit_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_done = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_logit_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_logit_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_mem_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_mem_rsp_rdata = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_mem_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_mem_rsp_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__detokenizer_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_rsp_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_rsp_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_idle = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__write_allowed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__reload_allowed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__live_ddr_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__input_fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__output_fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__publish = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__status = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__edge_io__tx_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_writable_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_writable_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_immutable_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_immutable_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_subsystem__cfg_directory_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT____VdfgTmp_he886f039__0 = 0;
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__reload_r = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__publish_failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__serial_update_r = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__divisor_r = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__eos_r = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__max_r = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__transport_r = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__vocab_r = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__frame_r = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_profile = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_vocab = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__profile_pending = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__vocab_pending = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__address_known = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_match = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__bundle_legal = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9e465c1b__0 = 0;
    vlSelf->bench__DOT__dut__DOT__configuration__DOT____VdfgTmp_h9ef3e9a0__0 = 0;
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_meta = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_previous = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_divisor = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_bit = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_shift = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_byte = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__framing_fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__overflow_fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__empty_frame_fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_active = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_closed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_shift = VL_RAND_RESET_I(10);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_bit = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_counter = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_in_data = VL_RAND_RESET_I(9);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_empty = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_empty = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_pop = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__healthy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__receive_open = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_emit = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__paths_idle = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hb418d625__0 = 0;
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_h57a93df3__0 = 0;
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hf663a351__0 = 0;
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT____Vxrand_h8d954d18__0 = VL_RAND_RESET_I(9);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data[__Vi0] = VL_RAND_RESET_I(9);
    }
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__write_ptr = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__pop = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__push = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT____Vlvbound_h27873815__0 = VL_RAND_RESET_I(9);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT____Vxrand_h8d954d18__0 = VL_RAND_RESET_I(9);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data[__Vi0] = VL_RAND_RESET_I(9);
    }
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__write_ptr = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__pop = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__push = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT____Vlvbound_h27873815__0 = VL_RAND_RESET_I(9);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state = VL_RAND_RESET_I(5);
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__tokens[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__token_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__output_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__outer_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__inner_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__output_token = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__output_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__decode_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__decode_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__span_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__utf8__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__utf8__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_class_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_range_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_composition_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_scalar_pool_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_decomposition_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__cfg_ranges_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__in_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_merge_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_register_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_dead_state = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_start_state = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_accept_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_op_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_transition_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_state_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_merge_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_byte_map_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_accepts_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_tag_ops_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_transitions_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_states_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_max_pretoken_bytes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__cfg_vocab_size = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____VdfgTmp_h67e2c008__0 = 0;
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__remaining = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__minimum_scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__byte_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__final_scalar = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_invalid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state = VL_RAND_RESET_I(5);
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__scalars[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bytes_memory[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__tokens[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__scalar_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__scalar_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__token_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__output_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__scalar_bytes_left = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__consumed_bytes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_cursor = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__boundary_end = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_byte = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__boundary_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_selected = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoder_in_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoder_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_in_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_start_byte = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_end_byte = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_in_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_tbl_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__bpe_tbl_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_tbl_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_tbl_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__base_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__selected_scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__encoding__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__tbl_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__tbl_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__in_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____VdfgTmp_h115be047__0 = 0;
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____VdfgTmp_hf61b8ee4__0 = 0;
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoding__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoding__DOT__remaining = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoding__DOT__encoded = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoding__DOT__final_scalar = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__encoding__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state = VL_RAND_RESET_I(5);
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classes[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__scalar_ends[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__tag_valid[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__tag_bytes[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__tag_scalars[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__ranges_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__states_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__transitions_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__tag_ops_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__accepts_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__range_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__transition_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__tag_op_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__accept_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__start_state = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__dead_state = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__tag_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__scalar_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__byte_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__pending_scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__pending_end = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__pending_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__anchor_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__anchor_byte = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__cursor_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__cursor_byte = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__clear_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__current_state = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state_first_transition = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__step_before_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__step_before_byte = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__step_after_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__step_after_byte = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__step_end_symbol = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__end_consumed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__evaluate_state = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__op_cursor = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__op_remaining = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__accept_cursor = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__accept_remaining = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_kind = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_index = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__read_value);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__best_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__best_shortest = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__best_priority = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__best_end_byte = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__best_end_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classify_selected = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__input_end = VL_RAND_RESET_Q(33);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state_transition_end = VL_RAND_RESET_Q(33);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__state_accept_end = VL_RAND_RESET_Q(33);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_tbl_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__record_tbl_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_tbl_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__class_tbl_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__word_index = VL_RAND_RESET_I(2);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__offset_value);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__data_start);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__table_end);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__request_address);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__result_data);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__records__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__admitted = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__range_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__class_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__low_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__high_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__middle = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__first_scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__last_scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__class_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__property_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_valid = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__reader_data);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__word_index = VL_RAND_RESET_I(2);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__offset_value);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__data_start);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__table_end);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__request_address);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__result_data);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__pretokenization__DOT__dfa__DOT__classification__DOT__record_reader__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__word_index = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__offset_value);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__data_start);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__table_end);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__request_address);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__result_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__byte_map__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__state = VL_RAND_RESET_I(5);
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__tokens[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__vocabulary = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__merge_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__token_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__pair_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__output_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__merge_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__left_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__right_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__search_low = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__search_high = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__search_middle = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_left = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_right = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_rank = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_word = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__response_data = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__request_address);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__best_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__best_rank = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__best_position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__best_result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__shift_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__code = VL_RAND_RESET_I(8);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_address);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_equal = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__ranked_merges__DOT__bpe__DOT__record_before = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__vocabulary = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__maximum_length = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__records_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_count = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_flags = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__remaining_bytes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__request_address = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__reading_record = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_lane = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_length = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__emit_index = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value = VL_RAND_RESET_I(21);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar = VL_RAND_RESET_I(21);
    for (int __Vi0 = 0; __Vi0 < 4; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_byte = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__done_r = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = VL_RAND_RESET_I(8);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__continued_scalar = VL_RAND_RESET_I(21);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0 = 0;
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = VL_RAND_RESET_I(4);
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__eos = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__max_tokens = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__sequence_limit = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__issue_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prefill = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__done_r = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__accept_logit = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__frame_complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__active_vocabulary = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__request_token = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__request_position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__request_new_sequence = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__holding = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__buffered_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__buffered_logit = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_token_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_logit_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_logit_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_done = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_transfer = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__frame_complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__sequence_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__token = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__next_position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__vocabulary = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__tensor_f16 = VL_RAND_RESET_I(16);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__activation = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__weight_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__logit_product = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__logit_sum);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__activation_reuse_valid = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activations[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__head_activation_q = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__multiply_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__multiply_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__ready = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__finished = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__faults = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_wdata = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_proj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__memory_port__mem_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__memory_port__mem_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber7 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellout__decoder____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber21 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT____Vcellinp__final_norm____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vxrand_h8d96565c__2 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vxrand_h8d96565c__1 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__step = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__selected = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm_mode = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__element_mode = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__norm____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__norm____pinNumber21 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__norm____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__norm____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber20 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber15 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber13 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber12 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__gemv____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber8 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__gemv____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber21 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber18 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber15 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber14 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber13 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber12 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__rope____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber9 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber7 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__rope____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber21 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber18 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber15 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber14 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber13 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber12 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__attention____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber9 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber7 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__attention____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber15 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber14 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber12 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber9 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber7 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__mlp____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber20 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber18 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber17 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber16 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber15 = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber14 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber13 = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber12 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellinp__residual____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber8 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vcellout__residual____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____VdfgTmp_h25e570cc__0 = 0;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__k = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__c = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__inputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__outputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__source_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__target_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__group_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__group_offset = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__lane = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__qw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__qz = VL_RAND_RESET_I(32);
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__scales[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__accumulators[__Vi0]);
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__activation = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__bias_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__delta = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__scale_integer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__dequantized_weight = VL_RAND_RESET_Q(37);
    VL_RAND_RESET_W(69, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__product_value);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__weight_nibble = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__zero_nibble = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__operand_b = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT____Vcellinp__multiplier__in_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__key_vector = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__head = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__head_base = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__pair_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_x = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__coordinate_y = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__x = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__y = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__cosine = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__sine = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_x = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__output_y = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__product_index = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__x_cos = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__y_sin = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__y_cos = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__x_sin = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__rotated_x);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__rotated_y);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__operand_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiply_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiply_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__product = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__result = VL_RAND_RESET_Q(64);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 4; ++__Vi1) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[__Vi0][__Vi1] = VL_RAND_RESET_Q(64);
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__value_cache = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__context_pass = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__head = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__head_base = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kv_base = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__group_head = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__time_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__dim = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__component = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__q_column = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__k_column = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__q = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__cache_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__dot_product = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_argument = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted_product);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__dot);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__max_score);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__current_score);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__weighted);
    VL_RAND_RESET_W(97, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__score_difference);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divided_output);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__denominator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__sqrt_dimension = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__divide_error = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__division_result);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiply_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiply_b = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__multiplier__in_valid = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0 = 0;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state = VL_RAND_RESET_I(2);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__iteration = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__root_unit__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_error = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work);
    VL_RAND_RESET_W(129, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(130, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__reduced_input = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__exponent = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__remainder_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__division_magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__total = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__order = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__term_negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divide_by_zero = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__signed_quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__ready = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__finished = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__faults = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber22 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber11 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__inputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz = VL_RAND_RESET_I(32);
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[__Vi0] = VL_RAND_RESET_I(16);
    }
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vi0]);
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__bias_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scale_integer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight = VL_RAND_RESET_Q(37);
    VL_RAND_RESET_W(69, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__weight_nibble = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__zero_nibble = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__operand_b = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT____Vcellinp__multiplier__in_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum = VL_RAND_RESET_Q(33);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__product_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__numerator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__denominator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__truncated_product);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exponential = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__exponent = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__total = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__order = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__result = VL_RAND_RESET_Q(64);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 4; ++__Vi1) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[__Vi0][__Vi1] = VL_RAND_RESET_Q(64);
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(137, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__mode = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__output_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__sum = VL_RAND_RESET_Q(33);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__product_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__complete = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__issue = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__write_request = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__write_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiply_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiply_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wr = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__kd = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__pj = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__ly = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__rw = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__cl = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wd = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__numerator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__denominator = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__exponent = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__remainder_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__total = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__order = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__term_negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__result = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divide_by_zero = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__signed_quotient = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__result = VL_RAND_RESET_Q(64);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 4; ++__Vi1) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[__Vi0][__Vi1] = VL_RAND_RESET_Q(64);
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(137, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT__mux__DOT__active = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(137, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active = VL_RAND_RESET_I(1);
    VL_ZERO_RESET_W(137, vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h3aa3503e__0 = 0;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_a = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_b = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__negative = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__valid_result = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__result = VL_RAND_RESET_Q(64);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        for (int __Vi1 = 0; __Vi1 < 4; ++__Vi1) {
            vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[__Vi0][__Vi1] = VL_RAND_RESET_Q(64);
        }
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d94df49__0 = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__2 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__1 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h7d28236b__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_enabled = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__calibration_meta = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__calibration_sync = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__code = VL_RAND_RESET_I(8);
    VL_RAND_RESET_W(224, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_lengths);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata);
    VL_RAND_RESET_W(512, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__stage_error = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__stage_codes = VL_RAND_RESET_Q(48);
    VL_RAND_RESET_W(224, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata);
    VL_RAND_RESET_W(512, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loader_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__image_loader__ddr_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__image_loader__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__manifest__ddr_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__manifest__ddr_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__manifest__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__directory__ddr_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__directory__ddr_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__directory__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__tokens__ddr_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__tokens__ddr_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__tokens__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__profile__ddr_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__profile__ddr_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__profile__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__special_trie__ddr_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellout__special_trie__ddr_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__special_trie__start = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h54a152fa__0 = 0;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h065bd496__0 = 0;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h556532b1__0 = 0;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h54b96fd4__0 = 0;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h4f5601d0__0 = 0;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h06bb2786__0 = 0;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h07af84a6__0 = 0;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__6 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h8d93fe75__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__5 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__4 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__3 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__2 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__1 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h8d96565c__2 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h8d96565c__1 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__busy = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__state = VL_RAND_RESET_I(5);
    for (int __Vi0 = 0; __Vi0 < 8; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__header[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 7; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_words[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 10; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 20; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_bases[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 20; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_lengths[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 20; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segment_ends[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 20; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_offsets[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 20; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_ends[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 20; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__payload_crcs[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 32; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_order[__Vi0] = VL_RAND_RESET_I(5);
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__word_buffer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__byte_lane = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__header_word = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_record = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_word = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_seen = VL_RAND_RESET_I(7);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__segments_seen = VL_RAND_RESET_I(20);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_number = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__canonical_index = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__pair_index = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_word = VL_RAND_RESET_I(4);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_ddr_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_flash_end);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_absolute_start);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_absolute_end);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__payload_number = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__payload_kind = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_address = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__payload_bytes_seen = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__write_address = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__payload_crc = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__crc_value = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__crc_bit = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__payload_last_byte = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__write_strobes = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_offset_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_value_legal = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__config_index = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_kind_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__descriptor_kind_index = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_length = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__candidate_offset = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__absolute_header_end);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__assembled_word = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__next_crc = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data_last = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_address = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__request_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_h72ba3baa__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_h2691a3cf__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_hf70b483d__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_h9c77adfa__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_h25275004__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_h726b2924__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_h038307bb__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_hd47bdfcc__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_h74e34568__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vlvbound_hc7877924__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__counter = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__clock_level = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__command_shift = VL_RAND_RESET_Q(40);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__command_bits = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__receive_bit = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__receive_shift = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__byte_result = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__bytes_left = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__request_end);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____Vxrand_h7d28236b__2 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____Vxrand_h7d28236b__1 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____Vxrand_h7d28236b__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__state = VL_RAND_RESET_I(4);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__bases);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__lengths);
    VL_RAND_RESET_W(224, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__configuration);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__metadata);
    VL_RAND_RESET_W(512, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__table_counts);
    VL_RAND_RESET_W(512, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry);
    VL_RAND_RESET_W(256, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__header);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__segment_index = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__expected_record_bytes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__record_shift = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__data_bytes = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__expected_length);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_in_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_out_valid = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader_data);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__waiting = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__active_vocab = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__eos_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__profile_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__header_record_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__header_data_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__selected_length = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__geometry_ok = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____VdfgTmp_h68ab1d3d__0 = 0;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__length = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__offset_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__count = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__word_index = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__segment_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__offset_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__physical_address);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__result);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT__validator__DOT__reader__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__state = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__directory_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__directory_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__immutable_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__immutable_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__writable_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__writable_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__active_vocab = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__record_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_index = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(384, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_record);
    VL_RAND_RESET_W(384, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_record);
    VL_RAND_RESET_W(256, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__header);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__previous_key);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__previous_valid = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__record_address);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__region_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_extent);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__active_embedding_bytes);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__scan_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__scan_end = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__scan_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__scan_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__hole_cursor = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__next_region_start = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__next_region_end = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__zero_writable = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__read_word = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__legal_key = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__writable_key = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_rows = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_columns = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__expected_format = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__kind = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__storage_kind = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__region_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__rows = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__columns = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__format = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__permissions = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__extent = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(96, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__current_key);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__other_extent = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__same_storage = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_in_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_out_valid = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader_data);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__waiting = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__data_read = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__active_multiply = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply_a = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply_b = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____Vcellinp__validator__DOT__multiply__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT____Vcellinp__validator__DOT__multiply__in_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__length = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__offset_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__count = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__word_index = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__segment_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__offset_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__physical_address);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__result);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__reader__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____Vxrand_h7d28236b__1 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____Vxrand_h7d28236b__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__state = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__after_read = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__after_raw = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__bases);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__lengths);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__vocab_size = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__maximum_length = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__merge_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__map_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__merge_index = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__record_data);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__merge_length);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__map_token = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__previous_pair = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__previous_pair_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__left_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__right_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__result_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_index = VL_RAND_RESET_I(2);
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_offsets[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 3; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_lengths[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__byte_index = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_offset);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_address);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_lane = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__source_byte = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_segment = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__read_words = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_read = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader_in_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader_out_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__selected_length = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_length = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_flags = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__piece_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__pair_key = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_byte = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__source_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__source_offset = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__token_segment_bytes);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__raw_segment_bytes);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____Vlvbound_hbd706ecd__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____Vlvbound_h56e22c6a__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__length = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__offset_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__count = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__word_index = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__segment_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__offset_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__physical_address);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__result);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT__reader__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT____Vxrand_h7d28236b__1 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT____Vxrand_h7d28236b__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__after_read = VL_RAND_RESET_I(5);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__bases);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__lengths);
    VL_RAND_RESET_W(512, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__counts);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__class_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__tag_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__dead_state = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__dead_first_transition = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__policy_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__next_scalar = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__segment_index = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__read_segment = VL_RAND_RESET_I(5);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_data);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__previous_key = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__previous_valid = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__first_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__second_end);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__accept_priority = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__accept_policy = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__read_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__read_words = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__w0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__w1 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__w2 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__transition_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__state_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__key = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader_in_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader_out_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__record_legal = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__selected_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__length = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__offset_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__count = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__word_index = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__segment_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__offset_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__physical_address);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__result);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT__reader__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h7d28236b__1 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__5 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d94df49__0 = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d96565c__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__4 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__3 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h7d28236b__0 = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__2 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__1 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__state = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__after_read = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__bases);
    VL_RAND_RESET_W(1280, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__lengths);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__node_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__edge_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__special_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__token_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__raw_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__root = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__maximum_length = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__clear_index = VL_RAND_RESET_I(32);
    for (int __Vi0 = 0; __Vi0 < 1048576; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__visited[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 17; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_node[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 17; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_first[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 17; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_count[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 17; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_cursor[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 17; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_previous_byte[__Vi0] = VL_RAND_RESET_I(8);
    }
    for (int __Vi0 = 0; __Vi0 < 17; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__stack_previous_valid[__Vi0] = VL_RAND_RESET_I(1);
    }
    for (int __Vi0 = 0; __Vi0 < 16; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__path_bytes[__Vi0] = VL_RAND_RESET_I(8);
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__depth = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__visited_nodes = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__visited_edges = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__seen_node = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__special_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__duplicate_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__special_token_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__terminal_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__terminal_token_id = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__path_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__terminal_byte_offset = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(128, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__record_data);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__edge_interval_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__raw_address);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__terminal_end);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__raw_lane = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_segment = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__read_words = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__raw_read = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__w0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__w1 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__w2 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__w3 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_node = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_edge);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__selected_length = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__raw_byte_index);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader_in_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader_out_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vlvbound_h73e94318__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vlvbound_h4c82b207__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vlvbound_ha1bc899b__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vlvbound_h46159f21__0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vlvbound_ha1bc899b__1 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vlvbound_h1d0127f2__0 = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vlvbound_h46159f21__1 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vlvbound_h9a4d8d67__0 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__length = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__offset_value = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__count = VL_RAND_RESET_I(6);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__word_index = VL_RAND_RESET_I(6);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__segment_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__offset_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__physical_address);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__result);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__reader__DOT__reader__DOT__code = VL_RAND_RESET_I(8);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__priority_owner = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_address = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_strobes = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_bases);
    VL_RAND_RESET_W(1024, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_bytes);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_index = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_length = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__table_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_end);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_core_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_idle = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_rdata = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_accept = VL_RAND_RESET_I(1);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__allowed_table_end);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____Vcellinp__tensor_mapper__mem_req_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0 = 0;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_write = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_kind = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_projection = VL_RAND_RESET_I(3);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_column = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_count = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__record_index = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__record_word = VL_RAND_RESET_I(4);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_kind = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_layer = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_projection = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__storage_kind = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_offset = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_extent = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_rows = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_columns = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_format = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_permissions = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_offset);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_address);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__extent_value);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__element_index);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__element_offset);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__segment_offset);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__physical_address);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__segment_base = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__segment_bytes = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__read_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__response_data = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__response_error = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_rows = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_columns = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_columns = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_key = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_valid = VL_RAND_RESET_I(2);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_victim = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__descriptor_cached = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__transaction_cacheable = VL_RAND_RESET_I(1);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_kind[__Vi0] = VL_RAND_RESET_I(4);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_layer[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_projection[__Vi0] = VL_RAND_RESET_I(3);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_storage_kind[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_offset[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_extent[__Vi0] = VL_RAND_RESET_Q(64);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_rows[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_columns[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_format[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_permissions[__Vi0] = VL_RAND_RESET_I(32);
    }
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_row_valid = VL_RAND_RESET_I(2);
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_row[__Vi0] = VL_RAND_RESET_I(32);
    }
    for (int __Vi0 = 0; __Vi0 < 2; ++__Vi0) {
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_row_base[__Vi0] = VL_RAND_RESET_Q(64);
    }
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__descriptor_cache_index = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_context_matches = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_hit_0 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_hit_1 = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__cache_hit_index = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__row_base_hit = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__multiply_a = VL_RAND_RESET_Q(64);
    VL_RAND_RESET_W(66, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__directory_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__immutable_end);
    VL_RAND_RESET_W(65, vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_end);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__descriptor_extent_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_equal = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__key_later = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____Vcellinp__index_multiplier__out_ready = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____Vcellinp__index_multiplier__in_valid = VL_RAND_RESET_I(1);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_hee8b2130__0 = 0;
    vlSelf->__VdfgTmp_h1afe3993__0 = 0;
    vlSelf->__VdfgTmp_h5b2387d0__0 = 0;
    vlSelf->__VdfgTmp_h26c9701b__0 = 0;
    vlSelf->__Vtask_bench__DOT__control__34__write = 0;
    vlSelf->__Vtask_bench__DOT__control__34__address = VL_RAND_RESET_I(32);
    vlSelf->__Vtask_bench__DOT__control__34__value = VL_RAND_RESET_I(32);
    vlSelf->__Vtask_bench__DOT__control__34__expect_error = 0;
    vlSelf->__Vtask_bench__DOT__control__34__expect_data = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__ddr_rsp_valid = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__controller_finished = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer_finished = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__memory_subsystem__DOT__response_data = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__memory_subsystem__DOT__response_error = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_columns = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_active = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_shift = VL_RAND_RESET_I(10);
    vlSelf->__Vdly__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->__Vdly__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_count = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalar_index = VL_RAND_RESET_I(32);
    vlSelf->__Vdlyvdim0__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars__v0 = 0;
    vlSelf->__Vdlyvval__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars__v0 = VL_RAND_RESET_I(32);
    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__scalars__v0 = 0;
    vlSelf->__Vdly__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__vocabulary = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__maximum_length = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__bytes_count = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining = VL_RAND_RESET_I(3);
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__scalar_length = VL_RAND_RESET_I(3);
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__tail_valid = VL_RAND_RESET_I(1);
    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v0 = 0;
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar = VL_RAND_RESET_I(21);
    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1 = 0;
    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__reading_record = VL_RAND_RESET_I(1);
    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v2 = 0;
    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v3 = 0;
    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last = VL_RAND_RESET_I(1);
    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0 = 0;
    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__activation_reuse_valid = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state = VL_RAND_RESET_I(5);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__layer = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__position = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__state = VL_RAND_RESET_I(6);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exp_argument = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a = VL_RAND_RESET_I(32);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = VL_RAND_RESET_I(1);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state = VL_RAND_RESET_I(4);
    vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = VL_RAND_RESET_Q(64);
    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state = VL_RAND_RESET_I(3);
    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__command_shift = VL_RAND_RESET_Q(40);
    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__state = VL_RAND_RESET_I(6);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__clk__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__spi_cs_n__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__spi_sck__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__rst_n__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__dut__DOT__io_rst_n__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__dut__DOT__client_rst_n__0 = VL_RAND_RESET_I(1);
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n__0 = VL_RAND_RESET_I(1);
}
