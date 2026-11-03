// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench___024root.h"

VL_ATTR_COLD void Vbench___024root___eval_initial__TOP(Vbench___024root* vlSelf);
VlCoroutine Vbench___024root___eval_initial__TOP__Vtiming__0(Vbench___024root* vlSelf);
VlCoroutine Vbench___024root___eval_initial__TOP__Vtiming__1(Vbench___024root* vlSelf);
VlCoroutine Vbench___024root___eval_initial__TOP__Vtiming__2(Vbench___024root* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___eval_initial__TOP__bench__DOT__dut__DOT__final_norm(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);

void Vbench___024root___eval_initial(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_initial\n"); );
    // Body
    Vbench___024root___eval_initial__TOP(vlSelf);
    Vbench___024root___eval_initial__TOP__Vtiming__0(vlSelf);
    Vbench___024root___eval_initial__TOP__Vtiming__1(vlSelf);
    Vbench___024root___eval_initial__TOP__Vtiming__2(vlSelf);
    Vbench_anvil_q1_rmsnorm__N1_H8_M4___eval_initial__TOP__bench__DOT__dut__DOT__final_norm((&vlSymsp->TOP__bench__DOT__dut__DOT__final_norm));
    Vbench_anvil_q1_rmsnorm__N1_H8_M4___eval_initial__TOP__bench__DOT__dut__DOT__final_norm((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm));
    Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier));
    Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier));
    Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
    Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier));
    Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
    Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
    Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier));
    Vbench_anvil_edge_signed_multiplier__pi11___eval_initial__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__clk__0 
        = vlSelf->bench__DOT__clk;
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__rst_n__0 
        = vlSelf->bench__DOT__rst_n;
}

VL_INLINE_OPT VlCoroutine Vbench___024root___eval_initial__TOP__Vtiming__0(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_initial__TOP__Vtiming__0\n"); );
    // Init
    IData/*31:0*/ bench__DOT__i;
    bench__DOT__i = 0;
    std::string __Vfunc_bench__DOT__verification_file0__3__Vfuncout;
    std::string __Vfunc_bench__DOT__verification_file0__3__value;
    std::string __Vfunc_bench__DOT__verification_file1__4__Vfuncout;
    std::string __Vfunc_bench__DOT__verification_file1__4__value;
    std::string __Vfunc_bench__DOT__verification_file2__5__Vfuncout;
    std::string __Vfunc_bench__DOT__verification_file2__5__value;
    std::string __Vfunc_bench__DOT__verification_file3__6__Vfuncout;
    std::string __Vfunc_bench__DOT__verification_file3__6__value;
    std::string __Vfunc_bench__DOT__verification_file4__7__Vfuncout;
    std::string __Vfunc_bench__DOT__verification_file4__7__value;
    IData/*31:0*/ __Vtask_bench__DOT__token__9__id;
    __Vtask_bench__DOT__token__9__id = 0;
    IData/*31:0*/ __Vtask_bench__DOT__token__9__pos;
    __Vtask_bench__DOT__token__9__pos = 0;
    CData/*0:0*/ __Vtask_bench__DOT__token__9__first_token;
    __Vtask_bench__DOT__token__9__first_token = 0;
    VlWide<6>/*191:0*/ __Vtemp_14;
    VlWide<6>/*191:0*/ __Vtemp_15;
    VlWide<6>/*191:0*/ __Vtemp_16;
    VlWide<6>/*191:0*/ __Vtemp_17;
    VlWide<6>/*191:0*/ __Vtemp_18;
    // Body
    vlSelf->bench__DOT__rst_n = 0U;
    co_await vlSelf->__VdlySched.delay(1ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       685);
    if (VL_UNLIKELY((0U != ((((((((vlSelf->bench__DOT__mem_req_wdata 
                                   << 1U) | ((IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) 
                                             & ((2U 
                                                 >= (IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h3aa3503e__0))
                                                 ? 
                                                ((((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_rsp_ready) 
                                                   << 2U) 
                                                  | ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) 
                                                       & ((5U 
                                                           >= 
                                                           (7U 
                                                            & vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))
                                                           ? 
                                                          ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20) 
                                                             << 5U) 
                                                            | ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT__mux__DOT__active) 
                                                                 & ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20) 
                                                                      << 1U) 
                                                                     | (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20)) 
                                                                    >> (IData)(vlSelf->__VdfgTmp_h98a4e623__0))) 
                                                                << 4U) 
                                                               | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19) 
                                                                   << 3U) 
                                                                  | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19) 
                                                                      << 2U) 
                                                                     | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20) 
                                                                         << 1U) 
                                                                        | (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_rsp_ready)))))) 
                                                           >> 
                                                           (7U 
                                                            & vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))
                                                           : (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_h8d96565c__0))) 
                                                      << 1U) 
                                                     | (IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready))) 
                                                 >> (IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h3aa3503e__0))
                                                 : (IData)(vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_h8d96565c__0)))) 
                                 | ((vlSelf->bench__DOT__mem_req_wdata 
                                     >> 0x1fU) | ((IData)(
                                                          (((QData)((IData)(vlSelf->bench__DOT__mem_req_row)) 
                                                            << 0x20U) 
                                                           | (QData)((IData)(vlSelf->bench__DOT__mem_req_col)))) 
                                                  << 1U))) 
                                | (((IData)((((QData)((IData)(vlSelf->bench__DOT__mem_req_row)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__mem_req_col)))) 
                                    >> 0x1fU) | ((IData)(
                                                         ((((QData)((IData)(vlSelf->bench__DOT__mem_req_row)) 
                                                            << 0x20U) 
                                                           | (QData)((IData)(vlSelf->bench__DOT__mem_req_col))) 
                                                          >> 0x20U)) 
                                                 << 1U))) 
                               | ((vlSelf->bench__DOT__mem_req_layer 
                                   << 4U) | (((IData)(vlSelf->bench__DOT__mem_req_proj) 
                                              << 1U) 
                                             | ((IData)(
                                                        ((((QData)((IData)(vlSelf->bench__DOT__mem_req_row)) 
                                                           << 0x20U) 
                                                          | (QData)((IData)(vlSelf->bench__DOT__mem_req_col))) 
                                                         >> 0x20U)) 
                                                >> 0x1fU)))) 
                              | (((IData)((((QData)((IData)(vlSelf->bench__DOT__logit_index)) 
                                            << 0x20U) 
                                           | (QData)((IData)(vlSelf->bench__DOT__logit_data)))) 
                                  << 0xcU) | (((IData)(vlSelf->bench__DOT__done) 
                                               << 0xbU) 
                                              | (((IData)(vlSelf->bench__DOT__error) 
                                                  << 0xaU) 
                                                 | (((IData)(vlSelf->bench__DOT__mem_req_valid) 
                                                     << 9U) 
                                                    | (((IData)(vlSelf->bench__DOT__mem_req_write) 
                                                        << 8U) 
                                                       | (((IData)(vlSelf->bench__DOT__mem_req_kind) 
                                                           << 4U) 
                                                          | (vlSelf->bench__DOT__mem_req_layer 
                                                             >> 0x1cU)))))))) 
                             | (((IData)((((QData)((IData)(vlSelf->bench__DOT__logit_index)) 
                                           << 0x20U) 
                                          | (QData)((IData)(vlSelf->bench__DOT__logit_data)))) 
                                 >> 0x14U) | ((IData)(
                                                      ((((QData)((IData)(vlSelf->bench__DOT__logit_index)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(vlSelf->bench__DOT__logit_data))) 
                                                       >> 0x20U)) 
                                              << 0xcU))) 
                            | (((IData)(vlSelf->bench__DOT__token_ready) 
                                << 0xdU) | (((IData)(vlSelf->bench__DOT__logit_valid) 
                                             << 0xcU) 
                                            | ((IData)(
                                                       ((((QData)((IData)(vlSelf->bench__DOT__logit_index)) 
                                                          << 0x20U) 
                                                         | (QData)((IData)(vlSelf->bench__DOT__logit_data))) 
                                                        >> 0x20U)) 
                                               >> 0x14U))))))) {
        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:585: Assertion failed in %Nbench.reset_check: CORE_NUMERIC_RESET t=%0t\n",
                  64,VL_TIME_UNITED_Q(1000),-9,vlSymsp->name(),
                  64,VL_TIME_UNITED_Q(1000),-9);
        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 585, "");
    }
    VL_READMEM_N(true, 97, 511, 0, VL_CVT_PACK_STR_NN(
                                                      ([&]() {
                    __Vtemp_14[0U] = 0x303d2573U;
                    __Vtemp_14[1U] = 0x66696c65U;
                    __Vtemp_14[2U] = 0x696f6e5fU;
                    __Vtemp_14[3U] = 0x69636174U;
                    __Vtemp_14[4U] = 0x65726966U;
                    __Vtemp_14[5U] = 0x76U;
                    if (VL_UNLIKELY((! VL_VALUEPLUSARGS_INN(64, 
                                                            VL_CVT_PACK_STR_NW(6, __Vtemp_14), 
                                                            __Vfunc_bench__DOT__verification_file0__3__value)))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:5: Assertion failed in %Nbench.verification_file0: MISSING_VERIFICATION_INPUT\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 5, "");
                    }
                    __Vfunc_bench__DOT__verification_file0__3__Vfuncout 
                        = __Vfunc_bench__DOT__verification_file0__3__value;
                }(), __Vfunc_bench__DOT__verification_file0__3__Vfuncout))
                 ,  &(vlSelf->bench__DOT__initial_records)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 32, 456, 0, VL_CVT_PACK_STR_NN(
                                                      ([&]() {
                    __Vtemp_15[0U] = 0x313d2573U;
                    __Vtemp_15[1U] = 0x66696c65U;
                    __Vtemp_15[2U] = 0x696f6e5fU;
                    __Vtemp_15[3U] = 0x69636174U;
                    __Vtemp_15[4U] = 0x65726966U;
                    __Vtemp_15[5U] = 0x76U;
                    if (VL_UNLIKELY((! VL_VALUEPLUSARGS_INN(64, 
                                                            VL_CVT_PACK_STR_NW(6, __Vtemp_15), 
                                                            __Vfunc_bench__DOT__verification_file1__4__value)))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:10: Assertion failed in %Nbench.verification_file1: MISSING_VERIFICATION_INPUT\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 10, "");
                    }
                    __Vfunc_bench__DOT__verification_file1__4__Vfuncout 
                        = __Vfunc_bench__DOT__verification_file1__4__value;
                }(), __Vfunc_bench__DOT__verification_file1__4__Vfuncout))
                 ,  &(vlSelf->bench__DOT__expected)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 32, 51, 0, VL_CVT_PACK_STR_NN(
                                                     ([&]() {
                    __Vtemp_16[0U] = 0x323d2573U;
                    __Vtemp_16[1U] = 0x66696c65U;
                    __Vtemp_16[2U] = 0x696f6e5fU;
                    __Vtemp_16[3U] = 0x69636174U;
                    __Vtemp_16[4U] = 0x65726966U;
                    __Vtemp_16[5U] = 0x76U;
                    if (VL_UNLIKELY((! VL_VALUEPLUSARGS_INN(64, 
                                                            VL_CVT_PACK_STR_NW(6, __Vtemp_16), 
                                                            __Vfunc_bench__DOT__verification_file2__5__value)))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:15: Assertion failed in %Nbench.verification_file2: MISSING_VERIFICATION_INPUT\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 15, "");
                    }
                    __Vfunc_bench__DOT__verification_file2__5__Vfuncout 
                        = __Vfunc_bench__DOT__verification_file2__5__value;
                }(), __Vfunc_bench__DOT__verification_file2__5__Vfuncout))
                 ,  &(vlSelf->bench__DOT__expected_logits)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 32, 3, 0, VL_CVT_PACK_STR_NN(
                                                    ([&]() {
                    __Vtemp_17[0U] = 0x333d2573U;
                    __Vtemp_17[1U] = 0x66696c65U;
                    __Vtemp_17[2U] = 0x696f6e5fU;
                    __Vtemp_17[3U] = 0x69636174U;
                    __Vtemp_17[4U] = 0x65726966U;
                    __Vtemp_17[5U] = 0x76U;
                    if (VL_UNLIKELY((! VL_VALUEPLUSARGS_INN(64, 
                                                            VL_CVT_PACK_STR_NW(6, __Vtemp_17), 
                                                            __Vfunc_bench__DOT__verification_file3__6__value)))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:20: Assertion failed in %Nbench.verification_file3: MISSING_VERIFICATION_INPUT\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 20, "");
                    }
                    __Vfunc_bench__DOT__verification_file3__6__Vfuncout 
                        = __Vfunc_bench__DOT__verification_file3__6__value;
                }(), __Vfunc_bench__DOT__verification_file3__6__Vfuncout))
                 ,  &(vlSelf->bench__DOT__token_words)
                 , 0, ~0ULL);
    VL_READMEM_N(true, 32, 3, 0, VL_CVT_PACK_STR_NN(
                                                    ([&]() {
                    __Vtemp_18[0U] = 0x343d2573U;
                    __Vtemp_18[1U] = 0x66696c65U;
                    __Vtemp_18[2U] = 0x696f6e5fU;
                    __Vtemp_18[3U] = 0x69636174U;
                    __Vtemp_18[4U] = 0x65726966U;
                    __Vtemp_18[5U] = 0x76U;
                    if (VL_UNLIKELY((! VL_VALUEPLUSARGS_INN(64, 
                                                            VL_CVT_PACK_STR_NW(6, __Vtemp_18), 
                                                            __Vfunc_bench__DOT__verification_file4__7__value)))) {
                        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:25: Assertion failed in %Nbench.verification_file4: MISSING_VERIFICATION_INPUT\n",
                                  64,VL_TIME_UNITED_Q(1000),
                                  -9,vlSymsp->name());
                        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 25, "");
                    }
                    __Vfunc_bench__DOT__verification_file4__7__Vfuncout 
                        = __Vfunc_bench__DOT__verification_file4__7__value;
                }(), __Vfunc_bench__DOT__verification_file4__7__Vfuncout))
                 ,  &(vlSelf->bench__DOT__fault_config)
                 , 0, ~0ULL);
    bench__DOT__i = 0U;
    while (VL_GTS_III(32, 0x1ffU, bench__DOT__i)) {
        vlSelf->bench__DOT____Vlvbound_h23dbfffc__0 = 0U;
        if ((0x1feU >= (0x1ffU & bench__DOT__i))) {
            vlSelf->bench__DOT____Vlvbound_h6b8dec7b__0 
                = vlSelf->bench__DOT__initial_records
                [(0x1ffU & bench__DOT__i)][0U];
            vlSelf->bench__DOT__memory[(0x1ffU & bench__DOT__i)] 
                = vlSelf->bench__DOT____Vlvbound_h6b8dec7b__0;
            vlSelf->bench__DOT____Vlvbound_h3ed999ac__0 
                = vlSelf->bench__DOT__initial_records
                [(0x1ffU & bench__DOT__i)][1U];
            vlSelf->bench__DOT__first[(0x1ffU & bench__DOT__i)] 
                = vlSelf->bench__DOT____Vlvbound_h3ed999ac__0;
            vlSelf->bench__DOT____Vlvbound_h3078bb6a__0 
                = vlSelf->bench__DOT__initial_records
                [(0x1ffU & bench__DOT__i)][2U];
            vlSelf->bench__DOT__limit[(0x1ffU & bench__DOT__i)] 
                = vlSelf->bench__DOT____Vlvbound_h3078bb6a__0;
            vlSelf->bench__DOT____Vlvbound_h42a46a12__0 
                = (1U & vlSelf->bench__DOT__initial_records
                   [(0x1ffU & bench__DOT__i)][3U]);
            vlSelf->bench__DOT__writable[(0x1ffU & bench__DOT__i)] 
                = vlSelf->bench__DOT____Vlvbound_h42a46a12__0;
            vlSelf->bench__DOT__count[(0x1ffU & bench__DOT__i)] 
                = vlSelf->bench__DOT____Vlvbound_h23dbfffc__0;
        } else {
            vlSelf->bench__DOT____Vlvbound_h6b8dec7b__0 
                = vlSelf->bench__DOT____Vxrand_hd08cd184__0[0U];
            vlSelf->bench__DOT____Vlvbound_h3ed999ac__0 
                = vlSelf->bench__DOT____Vxrand_hd08cd184__1[1U];
            vlSelf->bench__DOT____Vlvbound_h3078bb6a__0 
                = vlSelf->bench__DOT____Vxrand_hd08cd184__2[2U];
            vlSelf->bench__DOT____Vlvbound_h42a46a12__0 
                = (1U & vlSelf->bench__DOT____Vxrand_hd08cd184__3[3U]);
        }
        bench__DOT__i = ((IData)(1U) + bench__DOT__i);
    }
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f654__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       695);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       695);
    vlSelf->bench__DOT__rst_n = 1U;
    __Vtask_bench__DOT__token__9__first_token = 1U;
    __Vtask_bench__DOT__token__9__pos = 0U;
    __Vtask_bench__DOT__token__9__id = vlSelf->bench__DOT__token_words
        [0U];
    co_await vlSelf->__VtrigSched_h0016f654__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       677);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       677);
    vlSelf->bench__DOT__token_id = __Vtask_bench__DOT__token__9__id;
    vlSelf->bench__DOT__token_pos = __Vtask_bench__DOT__token__9__pos;
    vlSelf->bench__DOT__new_sequence = __Vtask_bench__DOT__token__9__first_token;
    vlSelf->bench__DOT__token_valid = 1U;
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       678);
    while ((1U & (~ (IData)(vlSelf->bench__DOT__token_ready)))) {
        co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           678);
    }
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       679);
    co_await vlSelf->__VtrigSched_h0016f654__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(negedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       679);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       679);
    vlSelf->bench__DOT__token_valid = 0U;
    while (VL_LTES_III(32, vlSelf->bench__DOT__completions, __Vtask_bench__DOT__token__9__pos)) {
        co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           674);
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                           674);
    }
    if ((1U & (~ (IData)((0U != vlSelf->bench__DOT__fault_config
                          [0U]))))) {
        __Vtask_bench__DOT__token__9__first_token = 0U;
        __Vtask_bench__DOT__token__9__pos = 1U;
        __Vtask_bench__DOT__token__9__id = vlSelf->bench__DOT__token_words
            [1U];
        co_await vlSelf->__VtrigSched_h0016f654__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           677);
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                           677);
        vlSelf->bench__DOT__token_id = __Vtask_bench__DOT__token__9__id;
        vlSelf->bench__DOT__token_pos = __Vtask_bench__DOT__token__9__pos;
        vlSelf->bench__DOT__new_sequence = __Vtask_bench__DOT__token__9__first_token;
        vlSelf->bench__DOT__token_valid = 1U;
        co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           678);
        while ((1U & (~ (IData)(vlSelf->bench__DOT__token_ready)))) {
            co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(posedge bench.clk)", 
                                                               "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                               678);
        }
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                           679);
        co_await vlSelf->__VtrigSched_h0016f654__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           679);
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                           679);
        vlSelf->bench__DOT__token_valid = 0U;
        while (VL_LTES_III(32, vlSelf->bench__DOT__completions, __Vtask_bench__DOT__token__9__pos)) {
            co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(posedge bench.clk)", 
                                                               "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                               674);
            co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                               nullptr, 
                                               "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                               674);
        }
    }
    if ((1U & (~ (IData)((0U != vlSelf->bench__DOT__fault_config
                          [0U]))))) {
        __Vtask_bench__DOT__token__9__first_token = 0U;
        __Vtask_bench__DOT__token__9__pos = 2U;
        __Vtask_bench__DOT__token__9__id = vlSelf->bench__DOT__token_words
            [2U];
        co_await vlSelf->__VtrigSched_h0016f654__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           677);
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                           677);
        vlSelf->bench__DOT__token_id = __Vtask_bench__DOT__token__9__id;
        vlSelf->bench__DOT__token_pos = __Vtask_bench__DOT__token__9__pos;
        vlSelf->bench__DOT__new_sequence = __Vtask_bench__DOT__token__9__first_token;
        vlSelf->bench__DOT__token_valid = 1U;
        co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           678);
        while ((1U & (~ (IData)(vlSelf->bench__DOT__token_ready)))) {
            co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(posedge bench.clk)", 
                                                               "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                               678);
        }
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                           679);
        co_await vlSelf->__VtrigSched_h0016f654__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(negedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           679);
        co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                           nullptr, 
                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                           679);
        vlSelf->bench__DOT__token_valid = 0U;
        while (VL_LTES_III(32, vlSelf->bench__DOT__completions, __Vtask_bench__DOT__token__9__pos)) {
            co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                               nullptr, 
                                                               "@(posedge bench.clk)", 
                                                               "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                               674);
            co_await vlSelf->__VdlySched.delay(0x3e8ULL, 
                                               nullptr, 
                                               "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                               674);
        }
    }
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                       nullptr, 
                                                       "@(posedge bench.clk)", 
                                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                       674);
    co_await vlSelf->__VdlySched.delay(0x3e8ULL, nullptr, 
                                       "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                       674);
    if ((0U != vlSelf->bench__DOT__fault_config[0U])) {
        if (VL_UNLIKELY((1U & ((((((((1U != vlSelf->bench__DOT__completions) 
                                     | (0U != vlSelf->bench__DOT__logits)) 
                                    | (vlSelf->bench__DOT__requests 
                                       != vlSelf->bench__DOT__responses)) 
                                   | (IData)(vlSelf->bench__DOT__pending)) 
                                  | (IData)(vlSelf->bench__DOT__error)) 
                                 | (IData)(vlSelf->bench__DOT__done)) 
                                | (~ (IData)(vlSelf->bench__DOT__token_ready))) 
                               | (IData)(vlSelf->bench__DOT__mem_req_valid))))) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:705: Assertion failed in %Nbench: CORE_ERROR_SETTLEMENT done=%0d requests=%0d responses=%0d\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name(),32,vlSelf->bench__DOT__completions,
                      32,vlSelf->bench__DOT__requests,
                      32,vlSelf->bench__DOT__responses);
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 705, "");
        }
        vlSelf->bench__DOT__comparisons = ((IData)(1U) 
                                           + vlSelf->bench__DOT__comparisons);
    } else {
        if (VL_UNLIKELY((((((((((3U != vlSelf->bench__DOT__completions) 
                                | (0x33U != vlSelf->bench__DOT__logits)) 
                               | (0x1c8U != vlSelf->bench__DOT__write_count)) 
                              | (vlSelf->bench__DOT__requests 
                                 != vlSelf->bench__DOT__responses)) 
                             | (IData)(vlSelf->bench__DOT__pending)) 
                            | (IData)(vlSelf->bench__DOT__error)) 
                           | (0U == vlSelf->bench__DOT__request_stalls)) 
                          | (0U == vlSelf->bench__DOT__logit_stalls)) 
                         | (0xfffU != (IData)(vlSelf->bench__DOT__kinds_seen))))) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:712: Assertion failed in %Nbench: CORE_NUMERIC_COUNTS done=%0d logits=%0d writes=%0d/456 kinds=%x\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name(),32,vlSelf->bench__DOT__completions,
                      32,vlSelf->bench__DOT__logits,
                      32,vlSelf->bench__DOT__write_count,
                      12,(IData)(vlSelf->bench__DOT__kinds_seen));
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 712, "");
        }
        bench__DOT__i = 0U;
        while (VL_GTS_III(32, 0x1ffU, bench__DOT__i)) {
            if (VL_UNLIKELY((((0x1feU >= (0x1ffU & bench__DOT__i))
                               ? vlSelf->bench__DOT__count
                              [(0x1ffU & bench__DOT__i)]
                               : vlSelf->bench__DOT____Vxrand_h8d93fe75__14) 
                             != ((0x1feU >= (0x1ffU 
                                             & bench__DOT__i))
                                  ? vlSelf->bench__DOT__limit
                                 [(0x1ffU & bench__DOT__i)]
                                  : vlSelf->bench__DOT____Vxrand_h8d93fe75__15)))) {
                VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:715: Assertion failed in %Nbench: CORE_NUMERIC_MISSING_WRITE slot=%0d\n",
                          64,VL_TIME_UNITED_Q(1000),
                          -9,vlSymsp->name(),32,bench__DOT__i);
                VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 715, "");
            }
            bench__DOT__i = ((IData)(1U) + bench__DOT__i);
        }
        if (VL_UNLIKELY((0x1fbU != vlSelf->bench__DOT__comparisons))) {
            VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:716: Assertion failed in %Nbench: CORE_NUMERIC_COMPARISONS\n",
                      64,VL_TIME_UNITED_Q(1000),-9,
                      vlSymsp->name());
            VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 716, "");
        }
    }
    VL_WRITEF("CORE_NUMERIC requests=%0d writes=%0d logits=%0d completions=%0d\nCOMPARED %0d\n",
              32,vlSelf->bench__DOT__requests,32,vlSelf->bench__DOT__write_count,
              32,vlSelf->bench__DOT__logits,32,vlSelf->bench__DOT__completions,
              32,vlSelf->bench__DOT__comparisons);
    VL_FINISH_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 720, "");
}

VL_INLINE_OPT VlCoroutine Vbench___024root___eval_initial__TOP__Vtiming__1(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_initial__TOP__Vtiming__1\n"); );
    // Init
    IData/*31:0*/ bench__DOT____Vrepeat2;
    bench__DOT____Vrepeat2 = 0;
    // Body
    bench__DOT____Vrepeat2 = 0x1312d00U;
    while (VL_LTS_III(32, 0U, bench__DOT____Vrepeat2)) {
        co_await vlSelf->__VtrigSched_h0016f595__0.trigger(0U, 
                                                           nullptr, 
                                                           "@(posedge bench.clk)", 
                                                           "evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 
                                                           722);
        bench__DOT____Vrepeat2 = (bench__DOT____Vrepeat2 
                                  - (IData)(1U));
    }
    VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:722: Assertion failed in %Nbench: CORE_NUMERIC_CYCLE_BOUND\n",
              64,VL_TIME_UNITED_Q(1000),-9,vlSymsp->name());
    VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 722, "");
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbench___024root___dump_triggers__act(Vbench___024root* vlSelf);
#endif  // VL_DEBUG

void Vbench___024root___eval_triggers__act(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_triggers__act\n"); );
    // Body
    vlSelf->__VactTriggered.set(0U, ((IData)(vlSelf->bench__DOT__clk) 
                                     ^ (IData)(vlSelf->__Vtrigprevexpr___TOP__bench__DOT__clk__0)));
    vlSelf->__VactTriggered.set(1U, ((~ (IData)(vlSelf->bench__DOT__clk)) 
                                     & (IData)(vlSelf->__Vtrigprevexpr___TOP__bench__DOT__clk__0)));
    vlSelf->__VactTriggered.set(2U, ((IData)(vlSelf->bench__DOT__clk) 
                                     & (~ (IData)(vlSelf->__Vtrigprevexpr___TOP__bench__DOT__clk__0))));
    vlSelf->__VactTriggered.set(3U, (((IData)(vlSelf->bench__DOT__clk) 
                                      & (~ (IData)(vlSelf->__Vtrigprevexpr___TOP__bench__DOT__clk__0))) 
                                     | ((~ (IData)(vlSelf->bench__DOT__rst_n)) 
                                        & (IData)(vlSelf->__Vtrigprevexpr___TOP__bench__DOT__rst_n__0))));
    vlSelf->__VactTriggered.set(4U, vlSelf->__VdlySched.awaitingCurrentTime());
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__clk__0 
        = vlSelf->bench__DOT__clk;
    vlSelf->__Vtrigprevexpr___TOP__bench__DOT__rst_n__0 
        = vlSelf->bench__DOT__rst_n;
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vbench___024root___dump_triggers__act(vlSelf);
    }
#endif
}

VL_INLINE_OPT void Vbench___024root___act_comb__TOP__1(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___act_comb__TOP__1\n"); );
    // Init
    IData/*31:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15 = 0;
    CData/*2:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14 = 0;
    IData/*31:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 = 0;
    CData/*3:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11 = 0;
    CData/*0:0*/ bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9;
    bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9 = 0;
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0);
    VlWide<5>/*136:0*/ bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0;
    VL_ZERO_W(137, bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0);
    VlWide<26>/*831:0*/ __Vtemp_42;
    VlWide<13>/*415:0*/ __Vtemp_66;
    // Body
    vlSelf->bench__DOT__dut__DOT__ready = (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.cmd_ready) 
                                            << 1U) 
                                           | (IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber4));
    vlSelf->bench__DOT__dut__DOT__finished = (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.done) 
                                               << 1U) 
                                              | (IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber7));
    vlSelf->bench__DOT__dut__DOT__faults = ((((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.done) 
                                              & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.__PVT__failed)) 
                                             << 1U) 
                                            | ((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber7) 
                                               & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__failed)));
    __Vtemp_42[0U] = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_wdata;
    __Vtemp_42[1U] = (IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_row)) 
                               << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_col))));
    __Vtemp_42[2U] = (IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_row)) 
                                << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_col))) 
                              >> 0x20U));
    __Vtemp_42[3U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_layer 
                       << 3U) | (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_proj));
    __Vtemp_42[4U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
                       << 9U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_valid) 
                                  << 8U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_write) 
                                             << 7U) 
                                            | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_kind) 
                                                << 3U) 
                                               | (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.mem_req_layer 
                                                  >> 0x1dU)))));
    __Vtemp_42[5U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber18 
                       >> 0x17U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17)))) 
                                    << 9U));
    __Vtemp_42[6U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                 << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                               << 0x20U) 
                                              | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_42[7U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
                       << 0xcU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber15) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber16)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber17))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_42[8U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
                       << 0x12U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10) 
                                     << 0x11U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber12) 
                                                   << 0x10U) 
                                                  | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber13) 
                                                      << 0xcU) 
                                                     | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber14 
                                                        >> 0x14U)))));
    __Vtemp_42[9U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber17 
                       >> 0xeU) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16)))) 
                                   << 0x12U));
    __Vtemp_42[0xaU] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                   << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16)))) 
                         >> 0xeU) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                                << 0x20U) 
                                               | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16))) 
                                              >> 0x20U)) 
                                     << 0x12U));
    __Vtemp_42[0xbU] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
                         << 0x15U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber14) 
                                       << 0x12U) | 
                                      ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber16))) 
                                                >> 0x20U)) 
                                       >> 0xeU)));
    __Vtemp_42[0xcU] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
                         << 0x1bU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9) 
                                       << 0x1aU) | 
                                      (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber11) 
                                        << 0x19U) | 
                                       (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber12) 
                                         << 0x15U) 
                                        | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber13 
                                           >> 0xbU)))));
    __Vtemp_42[0xdU] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber17 
                         >> 5U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16)))) 
                                   << 0x1bU));
    __Vtemp_42[0xeU] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                   << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16)))) 
                         >> 5U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                              << 0x20U) 
                                             | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16))) 
                                            >> 0x20U)) 
                                   << 0x1bU));
    __Vtemp_42[0xfU] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
                         << 0x1eU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber14) 
                                       << 0x1bU) | 
                                      ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber16))) 
                                                >> 0x20U)) 
                                       >> 5U)));
    __Vtemp_42[0x10U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12) 
                          << 0x1eU) | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber13 
                                       >> 2U));
    __Vtemp_42[0x11U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
                          << 4U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9) 
                                     << 3U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber11) 
                                                << 2U) 
                                               | ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber12) 
                                                  >> 2U))));
    __Vtemp_42[0x12U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber17 
                          >> 0x1cU) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                 << 0x20U) 
                                                | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16)))) 
                                       << 4U));
    __Vtemp_42[0x13U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16)))) 
                          >> 0x1cU) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16))) 
                                                >> 0x20U)) 
                                       << 4U));
    __Vtemp_42[0x14U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
                          << 7U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber14) 
                                     << 4U) | ((IData)(
                                                       ((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber15)) 
                                                          << 0x20U) 
                                                         | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber16))) 
                                                        >> 0x20U)) 
                                               >> 0x1cU)));
    __Vtemp_42[0x15U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
                          << 0xdU) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber9) 
                                       << 0xcU) | (
                                                   ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber11) 
                                                    << 0xbU) 
                                                   | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber12) 
                                                       << 7U) 
                                                      | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber13 
                                                         >> 0x19U)))));
    __Vtemp_42[0x16U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber18 
                          >> 0x13U) | ((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                 << 0x20U) 
                                                | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17)))) 
                                       << 0xdU));
    __Vtemp_42[0x17U] = (((IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                    << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17)))) 
                          >> 0x13U) | ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17))) 
                                                >> 0x20U)) 
                                       << 0xdU));
    __Vtemp_42[0x18U] = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
                          << 0x10U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber15) 
                                        << 0xdU) | 
                                       ((IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber16)) 
                                                   << 0x20U) 
                                                  | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber17))) 
                                                 >> 0x20U)) 
                                        >> 0x13U)));
    __Vtemp_42[0x19U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10) 
                          << 0x15U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber12) 
                                        << 0x14U) | 
                                       (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber13) 
                                         << 0x10U) 
                                        | (vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber14 
                                           >> 0x10U))));
    if ((0x335U >= (0x3ffU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))) {
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_42[((IData)(1U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_42[(0x1fU & (((IData)(0x89U) 
                                        * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                       >> 5U))] >> 
                  (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_42[((IData)(2U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_42[((IData)(1U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_42[((IData)(3U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_42[((IData)(2U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                 ? 0U : (__Vtemp_42[((IData)(4U) + 
                                     (0x1fU & (((IData)(0x89U) 
                                                * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                               >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
               | (__Vtemp_42[((IData)(3U) + (0x1fU 
                                             & (((IData)(0x89U) 
                                                 * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                                >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))));
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))
                           ? 0U : (__Vtemp_42[((IData)(5U) 
                                               + (0x1fU 
                                                  & (((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                                     >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))))) 
                         | (__Vtemp_42[((IData)(4U) 
                                        + (0x1fU & 
                                           (((IData)(0x89U) 
                                             * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected) 
                                            >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)))));
    } else {
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT__mux__DOT__active) {
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9 
            = (1U & (bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                     >> 8U));
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11 
            = (1U & (bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                     >> 7U));
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12 
            = (0xfU & (bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                       >> 3U));
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 
            = ((bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[4U] 
                << 0x1dU) | (bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U] 
                             >> 3U));
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14 
            = (7U & bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[3U]);
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15 
            = bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[2U];
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16 
            = bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[1U];
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 
            = bench__DOT__dut__DOT__decoder__DOT__bus__DOT____VdfgTmp_ha936017d__0[0U];
    } else {
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16 = 0U;
        bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 = 0U;
    }
    __Vtemp_66[0U] = vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_wdata;
    __Vtemp_66[1U] = (IData)((((QData)((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row)) 
                               << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col))));
    __Vtemp_66[2U] = (IData)(((((QData)((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_row)) 
                                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_col))) 
                              >> 0x20U));
    __Vtemp_66[3U] = ((vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer 
                       << 3U) | (IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_proj));
    __Vtemp_66[4U] = ((bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 
                       << 9U) | (((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid) 
                                  << 8U) | (((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_write) 
                                             << 7U) 
                                            | (((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_kind) 
                                                << 3U) 
                                               | (vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_layer 
                                                  >> 0x1dU)))));
    __Vtemp_66[5U] = ((bench__DOT__dut__DOT____Vcellout__decoder____pinNumber17 
                       >> 0x17U) | ((IData)((((QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15)) 
                                              << 0x20U) 
                                             | (QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16)))) 
                                    << 9U));
    __Vtemp_66[6U] = (((IData)((((QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15)) 
                                 << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15)) 
                                               << 0x20U) 
                                              | (QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_66[7U] = ((bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 
                       << 0xcU) | (((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber14) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber15)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber16))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_66[8U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_wdata 
                       << 0x12U) | (((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber9) 
                                     << 0x11U) | (((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber11) 
                                                   << 0x10U) 
                                                  | (((IData)(bench__DOT__dut__DOT____Vcellout__decoder____pinNumber12) 
                                                      << 0xcU) 
                                                     | (bench__DOT__dut__DOT____Vcellout__decoder____pinNumber13 
                                                        >> 0x14U)))));
    __Vtemp_66[9U] = ((vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_wdata 
                       >> 0xeU) | ((IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_row)) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_col)))) 
                                   << 0x12U));
    __Vtemp_66[0xaU] = (((IData)((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_row)) 
                                   << 0x20U) | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_col)))) 
                         >> 0xeU) | ((IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_row)) 
                                                << 0x20U) 
                                               | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_col))) 
                                              >> 0x20U)) 
                                     << 0x12U));
    __Vtemp_66[0xbU] = ((vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_layer 
                         << 0x15U) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_proj) 
                                       << 0x12U) | 
                                      ((IData)(((((QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_row)) 
                                                  << 0x20U) 
                                                 | (QData)((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_col))) 
                                                >> 0x20U)) 
                                       >> 0xeU)));
    __Vtemp_66[0xcU] = (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_valid) 
                         << 0x1aU) | (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_write) 
                                       << 0x19U) | 
                                      (((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_kind) 
                                        << 0x15U) | 
                                       (vlSymsp->TOP__bench__DOT__dut__DOT__final_norm.mem_req_layer 
                                        >> 0xbU))));
    if ((0x19aU >= (0x1ffU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))) {
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[0U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))
                 ? 0U : (__Vtemp_66[((IData)(1U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__selected))))) 
               | (__Vtemp_66[(0xfU & (((IData)(0x89U) 
                                       * vlSelf->bench__DOT__dut__DOT__selected) 
                                      >> 5U))] >> (0x1fU 
                                                   & ((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__selected))));
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))
                 ? 0U : (__Vtemp_66[((IData)(2U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__selected))))) 
               | (__Vtemp_66[((IData)(1U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected))));
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[2U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))
                 ? 0U : (__Vtemp_66[((IData)(3U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__selected))))) 
               | (__Vtemp_66[((IData)(2U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected))));
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected)))
                 ? 0U : (__Vtemp_66[((IData)(4U) + 
                                     (0xfU & (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                         << ((IData)(0x20U) - (0x1fU 
                                               & ((IData)(0x89U) 
                                                  * vlSelf->bench__DOT__dut__DOT__selected))))) 
               | (__Vtemp_66[((IData)(3U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * vlSelf->bench__DOT__dut__DOT__selected) 
                                              >> 5U)))] 
                  >> (0x1fU & ((IData)(0x89U) * vlSelf->bench__DOT__dut__DOT__selected))));
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
            = (0x1ffU & (((0U == (0x1fU & ((IData)(0x89U) 
                                           * vlSelf->bench__DOT__dut__DOT__selected)))
                           ? 0U : (__Vtemp_66[((IData)(5U) 
                                               + (0xfU 
                                                  & (((IData)(0x89U) 
                                                      * vlSelf->bench__DOT__dut__DOT__selected) 
                                                     >> 5U)))] 
                                   << ((IData)(0x20U) 
                                       - (0x1fU & ((IData)(0x89U) 
                                                   * vlSelf->bench__DOT__dut__DOT__selected))))) 
                         | (__Vtemp_66[((IData)(4U) 
                                        + (0xfU & (
                                                   ((IData)(0x89U) 
                                                    * vlSelf->bench__DOT__dut__DOT__selected) 
                                                   >> 5U)))] 
                            >> (0x1fU & ((IData)(0x89U) 
                                         * vlSelf->bench__DOT__dut__DOT__selected)))));
    } else {
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[0U] 
            = vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[0U];
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[1U] 
            = vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[1U];
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[2U] 
            = vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[2U];
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U] 
            = vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[3U];
        bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
            = (0x1ffU & vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[4U]);
    }
    if (vlSelf->bench__DOT__dut__DOT__bus__DOT__mux__DOT__active) {
        vlSelf->bench__DOT__mem_req_valid = (1U & (
                                                   bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                                                   >> 8U));
        vlSelf->bench__DOT__mem_req_write = (1U & (
                                                   bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                                                   >> 7U));
        vlSelf->bench__DOT__mem_req_kind = (0xfU & 
                                            (bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                                             >> 3U));
        vlSelf->bench__DOT__mem_req_layer = ((bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[4U] 
                                              << 0x1dU) 
                                             | (bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U] 
                                                >> 3U));
        vlSelf->bench__DOT__mem_req_proj = (7U & bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[3U]);
        vlSelf->bench__DOT__mem_req_row = bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[2U];
        vlSelf->bench__DOT__mem_req_col = bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[1U];
        vlSelf->bench__DOT__mem_req_wdata = bench__DOT__dut__DOT__bus__DOT____VdfgTmp_h7d3b2aeb__0[0U];
    } else {
        vlSelf->bench__DOT__mem_req_valid = 0U;
        vlSelf->bench__DOT__mem_req_write = 0U;
        vlSelf->bench__DOT__mem_req_kind = 0U;
        vlSelf->bench__DOT__mem_req_layer = 0U;
        vlSelf->bench__DOT__mem_req_proj = 0U;
        vlSelf->bench__DOT__mem_req_row = 0U;
        vlSelf->bench__DOT__mem_req_col = 0U;
        vlSelf->bench__DOT__mem_req_wdata = 0U;
    }
}

void Vbench___024root___act_comb__TOP__0(Vbench___024root* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__final_norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
void Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);

void Vbench___024root___eval_act(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_act\n"); );
    // Body
    if ((0x16ULL & vlSelf->__VactTriggered.word(0U))) {
        Vbench___024root___act_comb__TOP__0(vlSelf);
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__final_norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__final_norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench___024root___act_comb__TOP__1(vlSelf);
    }
}

extern const VlUnpacked<CData/*4:0*/, 8> Vbench__ConstPool__TABLE_h90db6da8_0;

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__0(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__0\n"); );
    // Init
    CData/*4:0*/ bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift;
    bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift = 0;
    CData/*4:0*/ bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift = 0;
    IData/*31:0*/ __Vfunc_sat32__12__Vfuncout;
    __Vfunc_sat32__12__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__12__x;
    VL_ZERO_W(128, __Vfunc_sat32__12__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__13__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__13__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__13__x;
    VL_ZERO_W(128, __Vfunc_round_shift__13__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__13__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__13__magnitude);
    IData/*31:0*/ __Vfunc_f16_q16__14__Vfuncout;
    __Vfunc_f16_q16__14__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_q16__14__h;
    __Vfunc_f16_q16__14__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__14__magnitude;
    __Vfunc_f16_q16__14__magnitude = 0;
    QData/*32:0*/ __Vfunc_f16_q16__14__signed_value;
    __Vfunc_f16_q16__14__signed_value = 0;
    IData/*31:0*/ __Vfunc_f16_scale__15__Vfuncout;
    __Vfunc_f16_scale__15__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_scale__15__h;
    __Vfunc_f16_scale__15__h = 0;
    IData/*31:0*/ __Vfunc_f16_scale__15__magnitude;
    __Vfunc_f16_scale__15__magnitude = 0;
    IData/*31:0*/ __Vfunc_f16_scale__15__shift;
    __Vfunc_f16_scale__15__shift = 0;
    IData/*31:0*/ __Vfunc_sat32__16__Vfuncout;
    __Vfunc_sat32__16__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__16__x;
    VL_ZERO_W(128, __Vfunc_sat32__16__x);
    CData/*0:0*/ __Vfunc_f16_invalid__17__Vfuncout;
    __Vfunc_f16_invalid__17__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_invalid__17__h;
    __Vfunc_f16_invalid__17__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__18__Vfuncout;
    __Vfunc_f16_q16__18__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_q16__18__h;
    __Vfunc_f16_q16__18__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__18__magnitude;
    __Vfunc_f16_q16__18__magnitude = 0;
    QData/*32:0*/ __Vfunc_f16_q16__18__signed_value;
    __Vfunc_f16_q16__18__signed_value = 0;
    IData/*31:0*/ __Vfunc_f16_scale__19__Vfuncout;
    __Vfunc_f16_scale__19__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_scale__19__h;
    __Vfunc_f16_scale__19__h = 0;
    IData/*31:0*/ __Vfunc_f16_scale__19__magnitude;
    __Vfunc_f16_scale__19__magnitude = 0;
    IData/*31:0*/ __Vfunc_f16_scale__19__shift;
    __Vfunc_f16_scale__19__shift = 0;
    IData/*31:0*/ __Vfunc_sat32__20__Vfuncout;
    __Vfunc_sat32__20__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__20__x;
    VL_ZERO_W(128, __Vfunc_sat32__20__x);
    CData/*0:0*/ __Vfunc_f16_invalid__21__Vfuncout;
    __Vfunc_f16_invalid__21__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_invalid__21__h;
    __Vfunc_f16_invalid__21__h = 0;
    IData/*31:0*/ __Vfunc_sat32__22__Vfuncout;
    __Vfunc_sat32__22__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__22__x;
    VL_ZERO_W(128, __Vfunc_sat32__22__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__23__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__23__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__23__x;
    VL_ZERO_W(128, __Vfunc_round_shift__23__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__23__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__23__magnitude);
    CData/*0:0*/ __Vfunc_f16_invalid__24__Vfuncout;
    __Vfunc_f16_invalid__24__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_invalid__24__h;
    __Vfunc_f16_invalid__24__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__25__Vfuncout;
    __Vfunc_f16_q16__25__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_q16__25__h;
    __Vfunc_f16_q16__25__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__25__magnitude;
    __Vfunc_f16_q16__25__magnitude = 0;
    QData/*32:0*/ __Vfunc_f16_q16__25__signed_value;
    __Vfunc_f16_q16__25__signed_value = 0;
    IData/*31:0*/ __Vfunc_f16_scale__26__Vfuncout;
    __Vfunc_f16_scale__26__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_scale__26__h;
    __Vfunc_f16_scale__26__h = 0;
    IData/*31:0*/ __Vfunc_f16_scale__26__magnitude;
    __Vfunc_f16_scale__26__magnitude = 0;
    IData/*31:0*/ __Vfunc_f16_scale__26__shift;
    __Vfunc_f16_scale__26__shift = 0;
    IData/*31:0*/ __Vfunc_sat32__27__Vfuncout;
    __Vfunc_sat32__27__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__27__x;
    VL_ZERO_W(128, __Vfunc_sat32__27__x);
    IData/*31:0*/ __Vfunc_f16_scale__28__Vfuncout;
    __Vfunc_f16_scale__28__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_scale__28__h;
    __Vfunc_f16_scale__28__h = 0;
    IData/*31:0*/ __Vfunc_f16_scale__28__magnitude;
    __Vfunc_f16_scale__28__magnitude = 0;
    IData/*31:0*/ __Vfunc_f16_scale__28__shift;
    __Vfunc_f16_scale__28__shift = 0;
    CData/*0:0*/ __Vfunc_f16_invalid__29__Vfuncout;
    __Vfunc_f16_invalid__29__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_invalid__29__h;
    __Vfunc_f16_invalid__29__h = 0;
    IData/*31:0*/ __Vfunc_sat32__30__Vfuncout;
    __Vfunc_sat32__30__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__30__x;
    VL_ZERO_W(128, __Vfunc_sat32__30__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__31__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__31__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__31__x;
    VL_ZERO_W(128, __Vfunc_round_shift__31__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__31__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__31__magnitude);
    IData/*31:0*/ __Vfunc_sat32__32__Vfuncout;
    __Vfunc_sat32__32__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__32__x;
    VL_ZERO_W(128, __Vfunc_sat32__32__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__33__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__33__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__33__x;
    VL_ZERO_W(128, __Vfunc_round_shift__33__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__33__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__33__magnitude);
    IData/*31:0*/ __Vfunc_sat32__34__Vfuncout;
    __Vfunc_sat32__34__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__34__x;
    VL_ZERO_W(128, __Vfunc_sat32__34__x);
    IData/*31:0*/ __Vfunc_sat32__35__Vfuncout;
    __Vfunc_sat32__35__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__35__x;
    VL_ZERO_W(128, __Vfunc_sat32__35__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__36__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__36__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__36__x;
    VL_ZERO_W(128, __Vfunc_round_shift__36__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__36__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__36__magnitude);
    CData/*0:0*/ __Vfunc_f16_invalid__37__Vfuncout;
    __Vfunc_f16_invalid__37__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_invalid__37__h;
    __Vfunc_f16_invalid__37__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__38__Vfuncout;
    __Vfunc_f16_q16__38__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_q16__38__h;
    __Vfunc_f16_q16__38__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__38__magnitude;
    __Vfunc_f16_q16__38__magnitude = 0;
    QData/*32:0*/ __Vfunc_f16_q16__38__signed_value;
    __Vfunc_f16_q16__38__signed_value = 0;
    IData/*31:0*/ __Vfunc_f16_scale__39__Vfuncout;
    __Vfunc_f16_scale__39__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_scale__39__h;
    __Vfunc_f16_scale__39__h = 0;
    IData/*31:0*/ __Vfunc_f16_scale__39__magnitude;
    __Vfunc_f16_scale__39__magnitude = 0;
    IData/*31:0*/ __Vfunc_f16_scale__39__shift;
    __Vfunc_f16_scale__39__shift = 0;
    IData/*31:0*/ __Vfunc_sat32__40__Vfuncout;
    __Vfunc_sat32__40__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__40__x;
    VL_ZERO_W(128, __Vfunc_sat32__40__x);
    IData/*31:0*/ __Vfunc_f16_scale__41__Vfuncout;
    __Vfunc_f16_scale__41__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_scale__41__h;
    __Vfunc_f16_scale__41__h = 0;
    IData/*31:0*/ __Vfunc_f16_scale__41__magnitude;
    __Vfunc_f16_scale__41__magnitude = 0;
    IData/*31:0*/ __Vfunc_f16_scale__41__shift;
    __Vfunc_f16_scale__41__shift = 0;
    CData/*0:0*/ __Vfunc_f16_invalid__42__Vfuncout;
    __Vfunc_f16_invalid__42__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_invalid__42__h;
    __Vfunc_f16_invalid__42__h = 0;
    IData/*31:0*/ __Vfunc_sat32__43__Vfuncout;
    __Vfunc_sat32__43__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__43__x;
    VL_ZERO_W(128, __Vfunc_sat32__43__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__44__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__44__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__44__x;
    VL_ZERO_W(128, __Vfunc_round_shift__44__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__44__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__44__magnitude);
    IData/*31:0*/ __Vfunc_sat32__45__Vfuncout;
    __Vfunc_sat32__45__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__45__x;
    VL_ZERO_W(128, __Vfunc_sat32__45__x);
    IData/*31:0*/ __Vfunc_sat32__48__Vfuncout;
    __Vfunc_sat32__48__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__48__x;
    VL_ZERO_W(128, __Vfunc_sat32__48__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__49__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__49__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__49__x;
    VL_ZERO_W(128, __Vfunc_round_shift__49__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__49__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__49__magnitude);
    IData/*31:0*/ __Vfunc_sat32__50__Vfuncout;
    __Vfunc_sat32__50__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__50__x;
    VL_ZERO_W(128, __Vfunc_sat32__50__x);
    IData/*31:0*/ __Vfunc_sat32__51__Vfuncout;
    __Vfunc_sat32__51__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__51__x;
    VL_ZERO_W(128, __Vfunc_sat32__51__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__52__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__52__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__52__x;
    VL_ZERO_W(128, __Vfunc_round_shift__52__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__52__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__52__magnitude);
    CData/*2:0*/ __Vtableidx2;
    __Vtableidx2 = 0;
    CData/*2:0*/ __Vtableidx3;
    __Vtableidx3 = 0;
    CData/*0:0*/ __Vdly__bench__DOT__dut__DOT__sequence_valid;
    __Vdly__bench__DOT__dut__DOT__sequence_valid = 0;
    VlWide<3>/*95:0*/ __Vdly__bench__DOT__dut__DOT__logit_sum;
    VL_ZERO_W(96, __Vdly__bench__DOT__dut__DOT__logit_sum);
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__next_position;
    __Vdly__bench__DOT__dut__DOT__next_position = 0;
    SData/*15:0*/ __Vdly__bench__DOT__dut__DOT__tensor_f16;
    __Vdly__bench__DOT__dut__DOT__tensor_f16 = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state = 0;
    CData/*3:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__step;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__step = 0;
    CData/*2:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 0;
    CData/*4:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0;
    CData/*2:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v0;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v0 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v1;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v1 = 0;
    CData/*2:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8;
    __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8 = 0;
    VlWide<4>/*127:0*/ __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8;
    VL_ZERO_W(128, __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8);
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8 = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset = 0;
    CData/*2:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9;
    __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9 = 0;
    VlWide<4>/*127:0*/ __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9;
    VL_ZERO_W(128, __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9);
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9 = 0;
    CData/*2:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8;
    __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8 = 0;
    SData/*15:0*/ __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8;
    __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v9;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v9 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v10;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v10 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v17;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v17 = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state = 0;
    CData/*4:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state = 0;
    CData/*3:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim = 0;
    VlWide<3>/*95:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot;
    VL_ZERO_W(96, __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot);
    VlWide<3>/*95:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted;
    VL_ZERO_W(96, __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted);
    QData/*63:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head = 0;
    CData/*0:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass = 0;
    VlWide<3>/*95:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score;
    VL_ZERO_W(96, __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score);
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state = 0;
    QData/*63:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work = 0;
    CData/*2:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state = 0;
    VlWide<5>/*128:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work;
    VL_ZERO_W(129, __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work);
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state = 0;
    QData/*63:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0;
    CData/*3:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0;
    CData/*4:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0;
    CData/*2:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v0;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v0 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v1;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v1 = 0;
    CData/*2:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8;
    __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8 = 0;
    VlWide<4>/*127:0*/ __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8;
    VL_ZERO_W(128, __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8);
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8 = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset = 0;
    CData/*2:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9;
    __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9 = 0;
    VlWide<4>/*127:0*/ __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9;
    VL_ZERO_W(128, __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9);
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9 = 0;
    CData/*2:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8;
    __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8 = 0;
    SData/*15:0*/ __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8;
    __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v9;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v9 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v10;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v10 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v17;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v17 = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 0;
    QData/*63:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 0;
    QData/*63:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0;
    CData/*3:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = 0;
    CData/*3:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b = 0;
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 0;
    QData/*63:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 0;
    QData/*63:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0;
    QData/*63:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0;
    CData/*0:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = 0;
    CData/*3:0*/ __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = 0;
    CData/*3:0*/ __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe = 0;
    CData/*0:0*/ __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative;
    __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative = 0;
    VlWide<5>/*159:0*/ __Vtemp_4;
    VlWide<5>/*159:0*/ __Vtemp_7;
    VlWide<5>/*159:0*/ __Vtemp_10;
    VlWide<5>/*159:0*/ __Vtemp_11;
    VlWide<5>/*159:0*/ __Vtemp_13;
    VlWide<4>/*127:0*/ __Vtemp_15;
    VlWide<5>/*159:0*/ __Vtemp_17;
    VlWide<3>/*95:0*/ __Vtemp_21;
    VlWide<3>/*95:0*/ __Vtemp_22;
    VlWide<3>/*95:0*/ __Vtemp_26;
    VlWide<3>/*95:0*/ __Vtemp_27;
    VlWide<3>/*95:0*/ __Vtemp_31;
    VlWide<3>/*95:0*/ __Vtemp_32;
    VlWide<5>/*159:0*/ __Vtemp_38;
    VlWide<5>/*159:0*/ __Vtemp_39;
    VlWide<5>/*159:0*/ __Vtemp_40;
    VlWide<5>/*159:0*/ __Vtemp_42;
    VlWide<5>/*159:0*/ __Vtemp_43;
    VlWide<3>/*95:0*/ __Vtemp_49;
    VlWide<3>/*95:0*/ __Vtemp_50;
    VlWide<3>/*95:0*/ __Vtemp_54;
    VlWide<3>/*95:0*/ __Vtemp_55;
    VlWide<4>/*127:0*/ __Vtemp_59;
    VlWide<5>/*159:0*/ __Vtemp_60;
    VlWide<5>/*159:0*/ __Vtemp_61;
    VlWide<5>/*159:0*/ __Vtemp_68;
    VlWide<5>/*159:0*/ __Vtemp_69;
    VlWide<5>/*159:0*/ __Vtemp_70;
    VlWide<5>/*159:0*/ __Vtemp_71;
    VlWide<4>/*127:0*/ __Vtemp_73;
    VlWide<5>/*159:0*/ __Vtemp_74;
    VlWide<4>/*127:0*/ __Vtemp_78;
    VlWide<4>/*127:0*/ __Vtemp_79;
    VlWide<4>/*127:0*/ __Vtemp_83;
    VlWide<4>/*127:0*/ __Vtemp_84;
    VlWide<4>/*127:0*/ __Vtemp_87;
    VlWide<5>/*159:0*/ __Vtemp_88;
    VlWide<5>/*159:0*/ __Vtemp_89;
    VlWide<5>/*159:0*/ __Vtemp_96;
    VlWide<5>/*159:0*/ __Vtemp_97;
    VlWide<5>/*159:0*/ __Vtemp_98;
    VlWide<5>/*159:0*/ __Vtemp_99;
    VlWide<4>/*127:0*/ __Vtemp_101;
    VlWide<5>/*159:0*/ __Vtemp_102;
    VlWide<4>/*127:0*/ __Vtemp_106;
    VlWide<4>/*127:0*/ __Vtemp_107;
    VlWide<4>/*127:0*/ __Vtemp_109;
    VlWide<4>/*127:0*/ __Vtemp_110;
    VlWide<4>/*127:0*/ __Vtemp_115;
    VlWide<4>/*127:0*/ __Vtemp_116;
    VlWide<4>/*127:0*/ __Vtemp_119;
    VlWide<5>/*159:0*/ __Vtemp_152;
    VlWide<5>/*159:0*/ __Vtemp_157;
    VlWide<3>/*95:0*/ __Vtemp_161;
    VlWide<3>/*95:0*/ __Vtemp_165;
    VlWide<3>/*95:0*/ __Vtemp_169;
    VlWide<3>/*95:0*/ __Vtemp_173;
    VlWide<3>/*95:0*/ __Vtemp_177;
    VlWide<4>/*127:0*/ __Vtemp_182;
    VlWide<5>/*159:0*/ __Vtemp_183;
    VlWide<5>/*159:0*/ __Vtemp_184;
    VlWide<4>/*127:0*/ __Vtemp_189;
    VlWide<5>/*159:0*/ __Vtemp_190;
    VlWide<5>/*159:0*/ __Vtemp_191;
    VlWide<5>/*159:0*/ __Vtemp_198;
    VlWide<5>/*159:0*/ __Vtemp_199;
    VlWide<5>/*159:0*/ __Vtemp_200;
    VlWide<5>/*159:0*/ __Vtemp_201;
    VlWide<5>/*159:0*/ __Vtemp_205;
    VlWide<5>/*159:0*/ __Vtemp_206;
    VlWide<5>/*159:0*/ __Vtemp_207;
    VlWide<5>/*159:0*/ __Vtemp_208;
    VlWide<4>/*127:0*/ __Vtemp_210;
    VlWide<5>/*159:0*/ __Vtemp_211;
    VlWide<4>/*127:0*/ __Vtemp_216;
    VlWide<5>/*159:0*/ __Vtemp_217;
    VlWide<4>/*127:0*/ __Vtemp_221;
    VlWide<4>/*127:0*/ __Vtemp_222;
    VlWide<4>/*127:0*/ __Vtemp_223;
    VlWide<4>/*127:0*/ __Vtemp_224;
    VlWide<3>/*95:0*/ __Vtemp_226;
    VlWide<3>/*95:0*/ __Vtemp_227;
    VlWide<3>/*95:0*/ __Vtemp_228;
    VlWide<3>/*95:0*/ __Vtemp_230;
    VlWide<3>/*95:0*/ __Vtemp_231;
    VlWide<3>/*95:0*/ __Vtemp_232;
    VlWide<4>/*127:0*/ __Vtemp_236;
    VlWide<5>/*159:0*/ __Vtemp_237;
    VlWide<5>/*159:0*/ __Vtemp_238;
    VlWide<5>/*159:0*/ __Vtemp_245;
    VlWide<5>/*159:0*/ __Vtemp_246;
    VlWide<5>/*159:0*/ __Vtemp_247;
    VlWide<5>/*159:0*/ __Vtemp_248;
    VlWide<4>/*127:0*/ __Vtemp_250;
    VlWide<5>/*159:0*/ __Vtemp_251;
    VlWide<4>/*127:0*/ __Vtemp_255;
    VlWide<4>/*127:0*/ __Vtemp_256;
    VlWide<4>/*127:0*/ __Vtemp_258;
    VlWide<4>/*127:0*/ __Vtemp_259;
    VlWide<4>/*127:0*/ __Vtemp_264;
    VlWide<4>/*127:0*/ __Vtemp_265;
    VlWide<4>/*127:0*/ __Vtemp_268;
    VlWide<4>/*127:0*/ __Vtemp_278;
    VlWide<4>/*127:0*/ __Vtemp_279;
    VlWide<3>/*95:0*/ __Vtemp_280;
    VlWide<4>/*127:0*/ __Vtemp_285;
    VlWide<4>/*127:0*/ __Vtemp_286;
    VlWide<4>/*127:0*/ __Vtemp_288;
    VlWide<4>/*127:0*/ __Vtemp_289;
    VlWide<4>/*127:0*/ __Vtemp_290;
    VlWide<3>/*95:0*/ __Vtemp_291;
    VlWide<4>/*127:0*/ __Vtemp_297;
    VlWide<5>/*159:0*/ __Vtemp_298;
    VlWide<5>/*159:0*/ __Vtemp_299;
    VlWide<5>/*159:0*/ __Vtemp_306;
    VlWide<5>/*159:0*/ __Vtemp_307;
    VlWide<5>/*159:0*/ __Vtemp_308;
    VlWide<5>/*159:0*/ __Vtemp_309;
    VlWide<4>/*127:0*/ __Vtemp_311;
    VlWide<5>/*159:0*/ __Vtemp_312;
    VlWide<4>/*127:0*/ __Vtemp_316;
    VlWide<4>/*127:0*/ __Vtemp_317;
    VlWide<4>/*127:0*/ __Vtemp_321;
    VlWide<4>/*127:0*/ __Vtemp_322;
    VlWide<5>/*159:0*/ __Vtemp_323;
    VlWide<5>/*159:0*/ __Vtemp_325;
    VlWide<3>/*95:0*/ __Vtemp_326;
    VlWide<3>/*95:0*/ __Vtemp_327;
    VlWide<3>/*95:0*/ __Vtemp_328;
    VlWide<3>/*95:0*/ __Vtemp_329;
    VlWide<3>/*95:0*/ __Vtemp_330;
    VlWide<4>/*127:0*/ __Vtemp_357;
    VlWide<5>/*159:0*/ __Vtemp_358;
    VlWide<5>/*159:0*/ __Vtemp_359;
    VlWide<5>/*159:0*/ __Vtemp_366;
    VlWide<5>/*159:0*/ __Vtemp_367;
    VlWide<5>/*159:0*/ __Vtemp_368;
    VlWide<5>/*159:0*/ __Vtemp_369;
    VlWide<4>/*127:0*/ __Vtemp_371;
    VlWide<5>/*159:0*/ __Vtemp_372;
    VlWide<4>/*127:0*/ __Vtemp_376;
    VlWide<4>/*127:0*/ __Vtemp_377;
    VlWide<3>/*95:0*/ __Vtemp_378;
    VlWide<4>/*127:0*/ __Vtemp_383;
    VlWide<4>/*127:0*/ __Vtemp_384;
    VlWide<4>/*127:0*/ __Vtemp_390;
    VlWide<4>/*127:0*/ __Vtemp_391;
    VlWide<4>/*127:0*/ __Vtemp_393;
    VlWide<5>/*159:0*/ __Vtemp_394;
    VlWide<5>/*159:0*/ __Vtemp_395;
    VlWide<5>/*159:0*/ __Vtemp_402;
    VlWide<5>/*159:0*/ __Vtemp_403;
    VlWide<5>/*159:0*/ __Vtemp_404;
    VlWide<5>/*159:0*/ __Vtemp_405;
    VlWide<4>/*127:0*/ __Vtemp_407;
    VlWide<5>/*159:0*/ __Vtemp_408;
    VlWide<4>/*127:0*/ __Vtemp_412;
    VlWide<4>/*127:0*/ __Vtemp_413;
    // Body
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state;
    __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8 = 0U;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9 = 0U;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v0 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v1 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v9 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v10 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v17 = 0U;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__failed;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state;
    vlSelf->__Vdly__bench__DOT__dut__DOT__position 
        = vlSelf->bench__DOT__dut__DOT__position;
    __Vdly__bench__DOT__dut__DOT__tensor_f16 = vlSelf->bench__DOT__dut__DOT__tensor_f16;
    __Vdly__bench__DOT__dut__DOT__next_position = vlSelf->bench__DOT__dut__DOT__next_position;
    __Vdly__bench__DOT__dut__DOT__logit_sum[0U] = vlSelf->bench__DOT__dut__DOT__logit_sum[0U];
    __Vdly__bench__DOT__dut__DOT__logit_sum[1U] = vlSelf->bench__DOT__dut__DOT__logit_sum[1U];
    __Vdly__bench__DOT__dut__DOT__logit_sum[2U] = vlSelf->bench__DOT__dut__DOT__logit_sum[2U];
    __Vdly__bench__DOT__dut__DOT__sequence_valid = vlSelf->bench__DOT__dut__DOT__sequence_valid;
    vlSelf->__Vdly__bench__DOT__dut__DOT__component 
        = vlSelf->bench__DOT__dut__DOT__component;
    vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid 
        = vlSelf->bench__DOT__dut__DOT__activation_reuse_valid;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state;
    vlSelf->__Vdly__bench__DOT__dut__DOT__state = vlSelf->bench__DOT__dut__DOT__state;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_argument 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_argument;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[0U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[1U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U];
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state;
    __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative 
        = vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v0 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v1 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v9 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v10 = 0U;
    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v17 = 0U;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__position 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__position;
    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__layer 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__state 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__state;
    __Vdly__bench__DOT__dut__DOT__decoder__DOT__step 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__step;
    if (vlSelf->bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__24__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data);
                                                __Vfunc_f16_invalid__24__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__24__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__24__Vfuncout))) {
                                    } else {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlSelf->bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__24__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data);
                                                __Vfunc_f16_invalid__24__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__24__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__24__Vfuncout))) {
                                    } else {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlSelf->bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state)))) {
                                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__24__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data);
                                                __Vfunc_f16_invalid__24__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__24__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__24__Vfuncout))) {
                                    } else {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlSelf->bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__37__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data);
                                                __Vfunc_f16_invalid__37__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__37__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__37__Vfuncout))) {
                                    } else {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlSelf->bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__37__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data);
                                                __Vfunc_f16_invalid__37__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__37__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__37__Vfuncout))) {
                                    } else {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlSelf->bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault)))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state) 
                                  >> 2U)))) {
                        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                            if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state)))) {
                                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__37__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data);
                                                __Vfunc_f16_invalid__37__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__37__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__37__Vfuncout))) {
                                    } else {
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__multiply_ready))) {
            __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative 
                = ((vlSelf->bench__DOT__dut__DOT__activation 
                    ^ vlSelf->bench__DOT__dut__DOT__weight_value) 
                   >> 0x1fU);
        }
        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid) 
                     & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state)))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[0U] = 0U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[1U] = 0U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[2U] = 0U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[3U] = 0U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[4U] = 0U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[0U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[1U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[2U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[3U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[4U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U];
                }
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state))) {
            VL_SHIFTL_WWI(129,129,32, __Vtemp_4, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift, 1U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[0U] 
                = __Vtemp_4[0U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[1U] 
                = __Vtemp_4[1U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[2U] 
                = __Vtemp_4[2U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[3U] 
                = __Vtemp_4[3U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[4U] 
                = (1U & __Vtemp_4[4U]);
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__subtract) {
                VL_SHIFTL_WWI(129,129,32, __Vtemp_7, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work, 1U);
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U] 
                    = (1U | __Vtemp_7[0U]);
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U] 
                    = __Vtemp_7[1U];
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U] 
                    = __Vtemp_7[2U];
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U] 
                    = __Vtemp_7[3U];
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U] 
                    = (1U & __Vtemp_7[4U]);
                __Vtemp_10[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[0U];
                __Vtemp_10[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[1U];
                __Vtemp_10[2U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[2U];
                __Vtemp_10[3U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[3U];
                __Vtemp_10[4U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[4U];
                VL_SUB_W(5, __Vtemp_11, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_10);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = __Vtemp_11[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = __Vtemp_11[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = __Vtemp_11[2U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[3U] 
                    = __Vtemp_11[3U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[4U] 
                    = (3U & __Vtemp_11[4U]);
            } else {
                VL_SHIFTL_WWI(129,129,32, __Vtemp_13, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work, 1U);
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U] 
                    = __Vtemp_13[0U];
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U] 
                    = __Vtemp_13[1U];
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U] 
                    = __Vtemp_13[2U];
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U] 
                    = __Vtemp_13[3U];
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U] 
                    = (1U & __Vtemp_13[4U]);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[2U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[3U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[3U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[4U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[4U];
            }
            if ((0x80U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__iterations))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__iterations 
                    = (0xffU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__iterations)));
            }
        } else if (((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[0U] 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[0U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[1U] 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[1U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[2U] 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[2U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[3U] 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[3U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[4U] 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[4U];
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[0U] 
                = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[1U] 
                = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator 
                           >> 0x20U));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[2U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[3U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[4U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[3U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[4U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor 
                = (0ULL == vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state = 1U;
        }
        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_valid) 
                     & (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state = 0U;
                }
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_result 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state))) {
            VL_SHIFTL_WWI(128,128,32, __Vtemp_15, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift, 2U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[0U] 
                = __Vtemp_15[0U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[1U] 
                = __Vtemp_15[1U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[2U] 
                = __Vtemp_15[2U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[3U] 
                = __Vtemp_15[3U];
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__subtract) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                    = (1ULL | VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work, 1U));
                VL_SUB_W(5, __Vtemp_17, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__trial);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[0U] 
                    = __Vtemp_17[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[1U] 
                    = __Vtemp_17[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[2U] 
                    = __Vtemp_17[2U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[3U] 
                    = __Vtemp_17[3U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[4U] 
                    = (3U & __Vtemp_17[4U]);
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                    = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work, 1U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[0U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[1U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[2U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[2U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[3U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[3U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[4U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[4U];
            }
            if ((0x3fU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__iteration))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state = 2U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__iteration 
                    = (0x3fU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__iteration)));
            }
        } else if (((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[1U] = 8U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[2U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[3U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work = 0ULL;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__iteration = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[1U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[2U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[3U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[4U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state = 1U;
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__issue) {
                vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wr 
                    = vlSelf->bench__DOT__dut__DOT__write_request;
                vlSelf->bench__DOT__dut__DOT__memory_port__DOT__kd 
                    = vlSelf->bench__DOT__dut__DOT__kind;
                vlSelf->bench__DOT__dut__DOT__memory_port__DOT__pj = 0U;
                vlSelf->bench__DOT__dut__DOT__memory_port__DOT__ly = 0U;
                vlSelf->bench__DOT__dut__DOT__memory_port__DOT__rw 
                    = vlSelf->bench__DOT__dut__DOT__row;
                vlSelf->bench__DOT__dut__DOT__memory_port__DOT__cl 
                    = vlSelf->bench__DOT__dut__DOT__col;
                vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wd 
                    = vlSelf->bench__DOT__dut__DOT__write_data;
                __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_req_valid) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_req_ready))) {
                __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__memory_port__mem_rsp_valid) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__memory_port__mem_rsp_ready))) {
                __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state = 0U;
            }
        } else {
            __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state = 0U;
        }
        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree
                   [1U][0U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree
                   [1U][1U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][2U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][3U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][0U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][1U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_a, 0x10U) 
                                                           * 
                                                           VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_b, 0x10U)))), 0x20U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_a, 0x10U) 
                                                           * 
                                                           (0xffffU 
                                                            & vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_b)))), 0x10U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          ((0xffffU 
                                                            & vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_a) 
                                                           * 
                                                           VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_b, 0x10U)))), 0x10U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered 
                = (QData)((IData)(((0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_a) 
                                   * (0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_b))));
        }
        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree
                   [1U][0U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree
                   [1U][1U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][2U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][3U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][0U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][1U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_a, 0x10U) 
                                                           * 
                                                           VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_b, 0x10U)))), 0x20U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_a, 0x10U) 
                                                           * 
                                                           (0xffffU 
                                                            & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_b)))), 0x10U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          ((0xffffU 
                                                            & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_a) 
                                                           * 
                                                           VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_b, 0x10U)))), 0x10U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered 
                = (QData)((IData)(((0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_a) 
                                   * (0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_b))));
        }
        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree
                   [1U][0U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree
                   [1U][1U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][2U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][3U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][0U] + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree
                   [0U][1U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_a, 0x10U) 
                                                           * 
                                                           VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_b, 0x10U)))), 0x20U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_a, 0x10U) 
                                                           * 
                                                           (0xffffU 
                                                            & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_b)))), 0x10U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          ((0xffffU 
                                                            & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_a) 
                                                           * 
                                                           VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_b, 0x10U)))), 0x10U);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered 
                = (QData)((IData)(((0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_a) 
                                   * (0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_b))));
        }
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
            = (0xfU & VL_SHIFTL_III(4,4,32, (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe), 1U));
        if (((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready))) {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
                = (1U | (IData)(__Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe));
        }
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__result 
                = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__negative)
                    ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree
                       [2U][0U]) : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree
                   [2U][0U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result = 1U;
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid) 
             & (0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result = 0U;
        }
        if (vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__busy) {
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree
                   [1U][0U] + vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree
                   [1U][1U]);
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree
                   [0U][2U] + vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree
                   [0U][3U]);
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum 
                = (vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree
                   [0U][0U] + vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree
                   [0U][1U]);
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_a, 0x10U) 
                                                           * 
                                                           VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_b, 0x10U)))), 0x20U);
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_a, 0x10U) 
                                                           * 
                                                           (0xffffU 
                                                            & vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_b)))), 0x10U);
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered 
                = VL_SHIFTL_QQI(64,64,32, (QData)((IData)(
                                                          ((0xffffU 
                                                            & vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_a) 
                                                           * 
                                                           VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_b, 0x10U)))), 0x10U);
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered 
                = (QData)((IData)(((0xffffU & vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_a) 
                                   * (0xffffU & vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_b))));
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wr 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_request;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__kd = 8U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__pj = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__ly = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__rw 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__row;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__cl 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__index;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__write_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber10) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber11))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber19) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber20))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state = 0U;
            }
        } else {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state = 0U;
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wr 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_request;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__kd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__kind;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__pj = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__ly = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__rw 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__row;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__cl 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__col;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__write_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber9) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber10))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber18) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber19))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state = 0U;
            }
        } else {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state = 0U;
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wr 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_request;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__kd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kind;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__pj = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__ly 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_layer;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__rw 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__row;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__cl 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__col;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__write_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber9) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber10))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber18) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber19))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state = 0U;
            }
        } else {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state = 0U;
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wr 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_request;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__kd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__kind;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__pj 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_projection;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__ly 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_layer;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__rw 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__row;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__cl 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__col;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__write_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber10) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber11))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__gemv____pinNumber19) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber20))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state = 0U;
            }
        } else {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state = 0U;
        }
        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) 
                     & ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state)) 
                        | (6U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0ULL;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = 0ULL;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result 
                        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U])) 
                            << 0x20U) | (QData)((IData)(
                                                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U])));
                }
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift, 1U);
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = (1ULL | VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U));
                __Vtemp_21[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor);
                __Vtemp_21[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                                          >> 0x20U));
                __Vtemp_21[2U] = 0U;
                VL_SUB_W(3, __Vtemp_22, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_21);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = __Vtemp_22[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = __Vtemp_22[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = (1U & __Vtemp_22[2U]);
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U];
            }
            if ((0x3fU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations 
                    = (0x7fU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations)));
            }
        } else if ((((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state)) 
                     | (5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state))
                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divisor;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
                = (0ULL == vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divisor);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 1U;
        }
        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_valid) 
                     & ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state)) 
                        | (6U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__zero_divisor) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0ULL;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result = 0ULL;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_result 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result 
                        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U])) 
                            << 0x20U) | (QData)((IData)(
                                                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U])));
                }
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift, 1U);
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__subtract) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = (1ULL | VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U));
                __Vtemp_26[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor);
                __Vtemp_26[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor 
                                          >> 0x20U));
                __Vtemp_26[2U] = 0U;
                VL_SUB_W(3, __Vtemp_27, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_26);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = __Vtemp_27[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = __Vtemp_27[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = (1U & __Vtemp_27[2U]);
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U];
            }
            if ((0x3fU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__iterations))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__iterations 
                    = (0x7fU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__iterations)));
            }
        } else if ((((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state)) 
                     | (5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state))
                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__reduced_input
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__division_magnitude);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divisor;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
                = (0ULL == vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divisor);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state = 1U;
        }
        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_valid) 
                     & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state)))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result 
                    = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor)
                        ? 0ULL : vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work);
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift, 1U);
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = (1ULL | VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U));
                __Vtemp_31[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor);
                __Vtemp_31[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                                          >> 0x20U));
                __Vtemp_31[2U] = 0U;
                VL_SUB_W(3, __Vtemp_32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_31);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = __Vtemp_32[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = __Vtemp_32[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = (1U & __Vtemp_32[2U]);
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U];
            }
            if ((0x3fU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations 
                    = (0x7fU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations)));
            }
        } else if (((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__numerator;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__denominator;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
                = (0ULL == vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__denominator);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 1U;
        }
        if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U] = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U] = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U] = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U] = 0U;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 4U;
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U] = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U] = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U] = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U] = 0U;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 4U;
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid) 
                        & ((0x10U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)) 
                           | (0x1eU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 0U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_error) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed = 1U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U];
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U];
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U];
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U];
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed = 0U;
                    }
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_ready) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state))) {
            __Vtemp_38[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator);
            __Vtemp_38[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator 
                                      >> 0x20U));
            __Vtemp_38[2U] = 0U;
            __Vtemp_38[3U] = 0U;
            __Vtemp_38[4U] = 0U;
            VL_SHIFTR_WWI(129,129,32, __Vtemp_39, __Vtemp_38, 1U);
            VL_ADD_W(5, __Vtemp_40, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude, __Vtemp_39);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[0U] 
                = __Vtemp_40[0U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[1U] 
                = __Vtemp_40[1U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[2U] 
                = __Vtemp_40[2U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[3U] 
                = __Vtemp_40[3U];
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[4U] 
                = (1U & __Vtemp_40[4U]);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 2U;
        } else if ((((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state)) 
                     | (0x1dU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready))) {
            __Vtemp_42[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[0U];
            __Vtemp_42[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[1U];
            __Vtemp_42[2U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[2U];
            __Vtemp_42[3U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[3U];
            __Vtemp_42[4U] = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[3U] 
                              >> 0x1fU);
            VL_NEGATE_W(5, __Vtemp_43, __Vtemp_42);
            if ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[3U] 
                 >> 0x1fU)) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[0U] 
                    = __Vtemp_43[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[1U] 
                    = __Vtemp_43[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[2U] 
                    = __Vtemp_43[2U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[3U] 
                    = __Vtemp_43[3U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[4U] 
                    = (1U & __Vtemp_43[4U]);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative = 1U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[0U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[1U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[2U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[2U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[3U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____Vcellinp__rounded_divider__numerator[3U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[4U] = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative = 0U;
            }
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator 
                = ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))
                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__sqrt_dimension
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 1U;
        }
        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid) 
                     & (4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state)))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result 
                    = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor)
                        ? 0ULL : vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work);
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift, 1U);
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = (1ULL | VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U));
                __Vtemp_49[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor);
                __Vtemp_49[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                                          >> 0x20U));
                __Vtemp_49[2U] = 0U;
                VL_SUB_W(3, __Vtemp_50, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_49);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = __Vtemp_50[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = __Vtemp_50[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = (1U & __Vtemp_50[2U]);
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U];
            }
            if ((0x3fU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations 
                    = (0x7fU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations)));
            }
        } else if (((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__numerator;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__denominator;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
                = (0ULL == vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__denominator);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 1U;
        }
        if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_valid) 
                     & ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state)) 
                        | (6U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0ULL;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = 0ULL;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result 
                        = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U])) 
                            << 0x20U) | (QData)((IData)(
                                                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U])));
                }
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift, 1U);
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = (1ULL | VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U));
                __Vtemp_54[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor);
                __Vtemp_54[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                                          >> 0x20U));
                __Vtemp_54[2U] = 0U;
                VL_SUB_W(3, __Vtemp_55, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_54);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = __Vtemp_55[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = __Vtemp_55[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = (1U & __Vtemp_55[2U]);
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work 
                    = VL_SHIFTL_QQI(64,64,32, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work, 1U);
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U];
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U];
            }
            if ((0x3fU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations 
                    = (0x7fU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations)));
            }
        } else if ((((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state)) 
                     | (5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state))
                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__reduced_input
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__division_magnitude);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divisor;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
                = (0ULL == vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divisor);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 1U;
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wr 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_request;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__kd = 8U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__pj = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__ly = 0U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__rw 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__row;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__cl 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__index;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__write_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber11))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber19) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber20))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state = 0U;
            }
        } else {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state = 0U;
        }
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wr 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_request;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__kd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__kind;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__pj 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_projection;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__ly 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_layer;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__rw 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__row;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__cl 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__col;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wd 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__write_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber11))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__gemv____pinNumber19) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber20))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state = 0U;
            }
        } else {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state = 0U;
        }
    } else {
        __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[4U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_result[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[3U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__iteration = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_result = 0ULL;
        __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wr = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_port__DOT__kd = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_port__DOT__pj = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_port__DOT__ly = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_port__DOT__rw = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_port__DOT__cl = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_port__DOT__wd = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_result = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__result = 0ULL;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wr = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__kd = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__pj = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__ly = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__rw = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__cl = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__wd = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wr = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__kd = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__pj = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__ly = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__rw = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__cl = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__wd = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wr = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__kd = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__pj = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__ly = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__rw = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__cl = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__wd = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wr = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__kd = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__pj = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__ly = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__rw = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__cl = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__wd = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_result = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__magnitude[4U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__denominator = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__result[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_result = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_result = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered = 0ULL;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wr = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__kd = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__pj = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__ly = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__rw = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__cl = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__wd = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wr = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__kd = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__pj = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__ly = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__rw = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__cl = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__wd = 0U;
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellinp__silu_product____pinNumber22))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed = 1U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xdU;
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xdU;
                    } else {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xdU;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0U;
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete) {
                    if ((8U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__index))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__index 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__index);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 1U;
                    } else {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xdU;
                    }
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xcU;
                    }
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__output_value 
                        = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                            ? ([&]() {
                                __Vfunc_round_shift__44__x[0U] 
                                    = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__product_value);
                                __Vfunc_round_shift__44__x[1U] 
                                    = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__product_value 
                                               >> 0x20U));
                                __Vfunc_round_shift__44__x[2U] 
                                    = (IData)((- (QData)((IData)(
                                                                 (1U 
                                                                  & (IData)(
                                                                            (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__product_value 
                                                                             >> 0x3fU)))))));
                                __Vfunc_round_shift__44__x[3U] 
                                    = (IData)(((- (QData)((IData)(
                                                                  (1U 
                                                                   & (IData)(
                                                                             (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__product_value 
                                                                              >> 0x3fU)))))) 
                                               >> 0x20U));
                                __Vtemp_59[0U] = 0U;
                                __Vtemp_59[1U] = 0U;
                                __Vtemp_59[2U] = 0U;
                                __Vtemp_59[3U] = 0U;
                                __Vtemp_60[0U] = __Vfunc_round_shift__44__x[0U];
                                __Vtemp_60[1U] = __Vfunc_round_shift__44__x[1U];
                                __Vtemp_60[2U] = __Vfunc_round_shift__44__x[2U];
                                __Vtemp_60[3U] = __Vfunc_round_shift__44__x[3U];
                                __Vtemp_60[4U] = (__Vfunc_round_shift__44__x[3U] 
                                                  >> 0x1fU);
                                VL_NEGATE_W(5, __Vtemp_61, __Vtemp_60);
                                __Vfunc_round_shift__44__magnitude[0U] 
                                    = (VL_GTS_IWW(128, __Vtemp_59, __Vfunc_round_shift__44__x)
                                        ? __Vtemp_61[0U]
                                        : __Vfunc_round_shift__44__x[0U]);
                                __Vfunc_round_shift__44__magnitude[1U] 
                                    = (VL_GTS_IWW(128, __Vtemp_59, __Vfunc_round_shift__44__x)
                                        ? __Vtemp_61[1U]
                                        : __Vfunc_round_shift__44__x[1U]);
                                __Vfunc_round_shift__44__magnitude[2U] 
                                    = (VL_GTS_IWW(128, __Vtemp_59, __Vfunc_round_shift__44__x)
                                        ? __Vtemp_61[2U]
                                        : __Vfunc_round_shift__44__x[2U]);
                                __Vfunc_round_shift__44__magnitude[3U] 
                                    = (VL_GTS_IWW(128, __Vtemp_59, __Vfunc_round_shift__44__x)
                                        ? __Vtemp_61[3U]
                                        : __Vfunc_round_shift__44__x[3U]);
                                __Vfunc_round_shift__44__magnitude[4U] 
                                    = (VL_GTS_IWW(128, __Vtemp_59, __Vfunc_round_shift__44__x)
                                        ? (1U & __Vtemp_61[4U])
                                        : 0U);
                                __Vtemp_68[0U] = 0x8000U;
                                __Vtemp_68[1U] = 0U;
                                __Vtemp_68[2U] = 0U;
                                __Vtemp_68[3U] = 0U;
                                __Vtemp_68[4U] = 0U;
                                VL_ADD_W(5, __Vtemp_69, __Vtemp_68, __Vfunc_round_shift__44__magnitude);
                                __Vtemp_70[0U] = __Vtemp_69[0U];
                                __Vtemp_70[1U] = __Vtemp_69[1U];
                                __Vtemp_70[2U] = __Vtemp_69[2U];
                                __Vtemp_70[3U] = __Vtemp_69[3U];
                                __Vtemp_70[4U] = (1U 
                                                  & __Vtemp_69[4U]);
                                VL_SHIFTR_WWI(129,129,32, __Vtemp_71, __Vtemp_70, 0x10U);
                                __Vfunc_round_shift__44__magnitude[0U] 
                                    = __Vtemp_71[0U];
                                __Vfunc_round_shift__44__magnitude[1U] 
                                    = __Vtemp_71[1U];
                                __Vfunc_round_shift__44__magnitude[2U] 
                                    = __Vtemp_71[2U];
                                __Vfunc_round_shift__44__magnitude[3U] 
                                    = __Vtemp_71[3U];
                                __Vfunc_round_shift__44__magnitude[4U] 
                                    = (1U & __Vtemp_71[4U]);
                                __Vtemp_73[0U] = 0U;
                                __Vtemp_73[1U] = 0U;
                                __Vtemp_73[2U] = 0U;
                                __Vtemp_73[3U] = 0U;
                                VL_NEGATE_W(5, __Vtemp_74, __Vfunc_round_shift__44__magnitude);
                                __Vfunc_round_shift__44__Vfuncout[0U] 
                                    = (VL_GTS_IWW(128, __Vtemp_73, __Vfunc_round_shift__44__x)
                                        ? __Vtemp_74[0U]
                                        : __Vfunc_round_shift__44__magnitude[0U]);
                                __Vfunc_round_shift__44__Vfuncout[1U] 
                                    = (VL_GTS_IWW(128, __Vtemp_73, __Vfunc_round_shift__44__x)
                                        ? __Vtemp_74[1U]
                                        : __Vfunc_round_shift__44__magnitude[1U]);
                                __Vfunc_round_shift__44__Vfuncout[2U] 
                                    = (VL_GTS_IWW(128, __Vtemp_73, __Vfunc_round_shift__44__x)
                                        ? __Vtemp_74[2U]
                                        : __Vfunc_round_shift__44__magnitude[2U]);
                                __Vfunc_round_shift__44__Vfuncout[3U] 
                                    = (VL_GTS_IWW(128, __Vtemp_73, __Vfunc_round_shift__44__x)
                                        ? __Vtemp_74[3U]
                                        : __Vfunc_round_shift__44__magnitude[3U]);
                                __Vfunc_sat32__43__x[0U] 
                                    = __Vfunc_round_shift__44__Vfuncout[0U];
                                __Vfunc_sat32__43__x[1U] 
                                    = __Vfunc_round_shift__44__Vfuncout[1U];
                                __Vfunc_sat32__43__x[2U] 
                                    = __Vfunc_round_shift__44__Vfuncout[2U];
                                __Vfunc_sat32__43__x[3U] 
                                    = __Vfunc_round_shift__44__Vfuncout[3U];
                                __Vtemp_78[0U] = 0x7fffffffU;
                                __Vtemp_78[1U] = 0U;
                                __Vtemp_78[2U] = 0U;
                                __Vtemp_78[3U] = 0U;
                                __Vtemp_79[0U] = 0x80000000U;
                                __Vtemp_79[1U] = 0xffffffffU;
                                __Vtemp_79[2U] = 0xffffffffU;
                                __Vtemp_79[3U] = 0xffffffffU;
                                __Vfunc_sat32__43__Vfuncout 
                                    = (VL_LTS_IWW(128, __Vtemp_78, __Vfunc_sat32__43__x)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(128, __Vtemp_79, __Vfunc_sat32__43__x)
                                            ? 0x80000000U
                                            : __Vfunc_sat32__43__x[0U]));
                            }(), __Vfunc_sat32__43__Vfuncout)
                            : ([&]() {
                                __Vfunc_sat32__45__x[0U] 
                                    = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum);
                                __Vfunc_sat32__45__x[1U] 
                                    = (((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum 
                                                               >> 0x20U))))) 
                                        << 1U) | (IData)(
                                                         (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum 
                                                          >> 0x20U)));
                                __Vfunc_sat32__45__x[2U] 
                                    = (((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum 
                                                               >> 0x20U))))) 
                                        >> 0x1fU) | 
                                       ((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum 
                                                               >> 0x20U))))) 
                                        << 1U));
                                __Vfunc_sat32__45__x[3U] 
                                    = (((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum 
                                                               >> 0x20U))))) 
                                        >> 0x1fU) | 
                                       ((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum 
                                                               >> 0x20U))))) 
                                        << 1U));
                                __Vtemp_83[0U] = 0x7fffffffU;
                                __Vtemp_83[1U] = 0U;
                                __Vtemp_83[2U] = 0U;
                                __Vtemp_83[3U] = 0U;
                                __Vtemp_84[0U] = 0x80000000U;
                                __Vtemp_84[1U] = 0xffffffffU;
                                __Vtemp_84[2U] = 0xffffffffU;
                                __Vtemp_84[3U] = 0xffffffffU;
                                __Vfunc_sat32__45__Vfuncout 
                                    = (VL_LTS_IWW(128, __Vtemp_83, __Vfunc_sat32__45__x)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(128, __Vtemp_84, __Vfunc_sat32__45__x)
                                            ? 0x80000000U
                                            : __Vfunc_sat32__45__x[0U]));
                            }(), __Vfunc_sat32__45__Vfuncout));
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xbU;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__product_value 
                        = ((IData)(vlSelf->bench__DOT__rst_n)
                            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__result
                            : 0ULL);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xaU;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_valid) {
                        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__failed) 
                             & (IData)(vlSelf->bench__DOT__rst_n))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed = 1U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xdU;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value 
                                = ((IData)(vlSelf->bench__DOT__rst_n)
                                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__result
                                    : 0U);
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 8U;
                        }
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum 
                    = (0x1ffffffffULL & ((((QData)((IData)(
                                                           (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a 
                                                            >> 0x1fU))) 
                                           << 0x20U) 
                                          | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a))) 
                                         + (((QData)((IData)(
                                                             (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b 
                                                              >> 0x1fU))) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b)))));
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xaU;
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__read_data;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state 
                    = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode))
                        ? 6U : 5U);
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__complete) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__read_data;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__issue) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 2U;
            }
        } else if (((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber4))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__index = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode = 2U;
            if (((1U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__layer) 
                 | (4U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__position))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0xeU;
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 1U;
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__index = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__mode = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__failed = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__a = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__output_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__product_value = 0ULL;
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__fault) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 1U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x17U;
        } else if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x17U;
                } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x17U;
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x17U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x17U;
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0U;
                        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v0 = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0U;
                        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v1 = 1U;
                    } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                        if ((7U > (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane))) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane)));
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x14U;
                        } else if ((((IData)(8U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c) 
                                    < vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs)) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c 
                                = ((IData)(8U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c);
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 1U;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x17U;
                        }
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x16U;
                    }
                } else {
                    __Vfunc_round_shift__36__x[0U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane][0U];
                    __Vfunc_round_shift__36__x[1U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane][1U];
                    __Vfunc_round_shift__36__x[2U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane][2U];
                    __Vfunc_round_shift__36__x[3U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane][3U];
                    __Vtemp_87[0U] = 0U;
                    __Vtemp_87[1U] = 0U;
                    __Vtemp_87[2U] = 0U;
                    __Vtemp_87[3U] = 0U;
                    __Vtemp_88[0U] = __Vfunc_round_shift__36__x[0U];
                    __Vtemp_88[1U] = __Vfunc_round_shift__36__x[1U];
                    __Vtemp_88[2U] = __Vfunc_round_shift__36__x[2U];
                    __Vtemp_88[3U] = __Vfunc_round_shift__36__x[3U];
                    __Vtemp_88[4U] = (__Vfunc_round_shift__36__x[3U] 
                                      >> 0x1fU);
                    VL_NEGATE_W(5, __Vtemp_89, __Vtemp_88);
                    if (VL_GTS_IWW(128, __Vtemp_87, __Vfunc_round_shift__36__x)) {
                        __Vfunc_round_shift__36__magnitude[0U] 
                            = __Vtemp_89[0U];
                        __Vfunc_round_shift__36__magnitude[1U] 
                            = __Vtemp_89[1U];
                        __Vfunc_round_shift__36__magnitude[2U] 
                            = __Vtemp_89[2U];
                        __Vfunc_round_shift__36__magnitude[3U] 
                            = __Vtemp_89[3U];
                        __Vfunc_round_shift__36__magnitude[4U] 
                            = (1U & __Vtemp_89[4U]);
                    } else {
                        __Vfunc_round_shift__36__magnitude[0U] 
                            = __Vfunc_round_shift__36__x[0U];
                        __Vfunc_round_shift__36__magnitude[1U] 
                            = __Vfunc_round_shift__36__x[1U];
                        __Vfunc_round_shift__36__magnitude[2U] 
                            = __Vfunc_round_shift__36__x[2U];
                        __Vfunc_round_shift__36__magnitude[3U] 
                            = __Vfunc_round_shift__36__x[3U];
                        __Vfunc_round_shift__36__magnitude[4U] = 0U;
                    }
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x15U;
                    __Vtemp_96[0U] = 0x8000U;
                    __Vtemp_96[1U] = 0U;
                    __Vtemp_96[2U] = 0U;
                    __Vtemp_96[3U] = 0U;
                    __Vtemp_96[4U] = 0U;
                    VL_ADD_W(5, __Vtemp_97, __Vtemp_96, __Vfunc_round_shift__36__magnitude);
                    __Vtemp_98[0U] = __Vtemp_97[0U];
                    __Vtemp_98[1U] = __Vtemp_97[1U];
                    __Vtemp_98[2U] = __Vtemp_97[2U];
                    __Vtemp_98[3U] = __Vtemp_97[3U];
                    __Vtemp_98[4U] = (1U & __Vtemp_97[4U]);
                    VL_SHIFTR_WWI(129,129,32, __Vtemp_99, __Vtemp_98, 0x10U);
                    __Vfunc_round_shift__36__magnitude[0U] 
                        = __Vtemp_99[0U];
                    __Vfunc_round_shift__36__magnitude[1U] 
                        = __Vtemp_99[1U];
                    __Vfunc_round_shift__36__magnitude[2U] 
                        = __Vtemp_99[2U];
                    __Vfunc_round_shift__36__magnitude[3U] 
                        = __Vtemp_99[3U];
                    __Vfunc_round_shift__36__magnitude[4U] 
                        = (1U & __Vtemp_99[4U]);
                    __Vtemp_101[0U] = 0U;
                    __Vtemp_101[1U] = 0U;
                    __Vtemp_101[2U] = 0U;
                    __Vtemp_101[3U] = 0U;
                    VL_NEGATE_W(5, __Vtemp_102, __Vfunc_round_shift__36__magnitude);
                    if (VL_GTS_IWW(128, __Vtemp_101, __Vfunc_round_shift__36__x)) {
                        __Vfunc_round_shift__36__Vfuncout[0U] 
                            = __Vtemp_102[0U];
                        __Vfunc_round_shift__36__Vfuncout[1U] 
                            = __Vtemp_102[1U];
                        __Vfunc_round_shift__36__Vfuncout[2U] 
                            = __Vtemp_102[2U];
                        __Vfunc_round_shift__36__Vfuncout[3U] 
                            = __Vtemp_102[3U];
                    } else {
                        __Vfunc_round_shift__36__Vfuncout[0U] 
                            = __Vfunc_round_shift__36__magnitude[0U];
                        __Vfunc_round_shift__36__Vfuncout[1U] 
                            = __Vfunc_round_shift__36__magnitude[1U];
                        __Vfunc_round_shift__36__Vfuncout[2U] 
                            = __Vfunc_round_shift__36__magnitude[2U];
                        __Vfunc_round_shift__36__Vfuncout[3U] 
                            = __Vfunc_round_shift__36__magnitude[3U];
                    }
                    __Vfunc_sat32__35__x[0U] = __Vfunc_round_shift__36__Vfuncout[0U];
                    __Vfunc_sat32__35__x[1U] = __Vfunc_round_shift__36__Vfuncout[1U];
                    __Vfunc_sat32__35__x[2U] = __Vfunc_round_shift__36__Vfuncout[2U];
                    __Vfunc_sat32__35__x[3U] = __Vfunc_round_shift__36__Vfuncout[3U];
                    __Vtemp_106[0U] = 0x7fffffffU;
                    __Vtemp_106[1U] = 0U;
                    __Vtemp_106[2U] = 0U;
                    __Vtemp_106[3U] = 0U;
                    __Vtemp_107[0U] = 0x80000000U;
                    __Vtemp_107[1U] = 0xffffffffU;
                    __Vtemp_107[2U] = 0xffffffffU;
                    __Vtemp_107[3U] = 0xffffffffU;
                    __Vfunc_sat32__35__Vfuncout = (
                                                   VL_LTS_IWW(128, __Vtemp_106, __Vfunc_sat32__35__x)
                                                    ? 0x7fffffffU
                                                    : 
                                                   (VL_GTS_IWW(128, __Vtemp_107, __Vfunc_sat32__35__x)
                                                     ? 0x80000000U
                                                     : 
                                                    __Vfunc_sat32__35__x[0U]));
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__output_value 
                        = __Vfunc_sat32__35__Vfuncout;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    __Vtemp_109[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__bias_value;
                    __Vtemp_109[1U] = (- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__bias_value 
                                                  >> 0x1fU)));
                    __Vtemp_109[2U] = (- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__bias_value 
                                                  >> 0x1fU)));
                    __Vtemp_109[3U] = (- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__bias_value 
                                                  >> 0x1fU)));
                    VL_SHIFTL_WWI(128,128,32, __Vtemp_110, __Vtemp_109, 0x10U);
                    VL_ADD_W(4, __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8, 
                             vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators
                             [vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane], __Vtemp_110);
                    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8 = 1U;
                    __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
                    if ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane))) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x14U;
                    } else {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane 
                            = (7U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane)));
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x11U;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                    if (([&]() {
                                __Vfunc_f16_invalid__37__h 
                                    = (0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data);
                                __Vfunc_f16_invalid__37__Vfuncout 
                                    = (0x1fU == (0x1fU 
                                                 & ((IData)(__Vfunc_f16_invalid__37__h) 
                                                    >> 0xaU)));
                            }(), (IData)(__Vfunc_f16_invalid__37__Vfuncout))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x17U;
                    } else {
                        __Vfunc_f16_q16__38__h = (0xffffU 
                                                  & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data);
                        __Vfunc_f16_scale__39__h = __Vfunc_f16_q16__38__h;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x13U;
                        if ((0U == (0x1fU & ((IData)(__Vfunc_f16_scale__39__h) 
                                             >> 0xaU)))) {
                            __Vfunc_f16_scale__39__magnitude 
                                = (0x3ffU & (IData)(__Vfunc_f16_scale__39__h));
                            __Vfunc_f16_scale__39__shift = 0xfffffff8U;
                        } else {
                            __Vfunc_f16_scale__39__magnitude 
                                = (0x400U | (0x3ffU 
                                             & (IData)(__Vfunc_f16_scale__39__h)));
                            __Vfunc_f16_scale__39__shift 
                                = ((0x1fU & ((IData)(__Vfunc_f16_scale__39__h) 
                                             >> 0xaU)) 
                                   - (IData)(9U));
                        }
                        __Vfunc_f16_scale__39__magnitude 
                            = (VL_LTES_III(32, 0U, __Vfunc_f16_scale__39__shift)
                                ? VL_SHIFTL_III(32,32,32, __Vfunc_f16_scale__39__magnitude, __Vfunc_f16_scale__39__shift)
                                : VL_SHIFTR_III(32,32,32, 
                                                (__Vfunc_f16_scale__39__magnitude 
                                                 + 
                                                 VL_SHIFTL_III(32,32,32, (IData)(1U), 
                                                               ((- __Vfunc_f16_scale__39__shift) 
                                                                - (IData)(1U)))), 
                                                (- __Vfunc_f16_scale__39__shift)));
                        __Vfunc_f16_scale__39__Vfuncout 
                            = __Vfunc_f16_scale__39__magnitude;
                        __Vfunc_f16_q16__38__magnitude 
                            = __Vfunc_f16_scale__39__Vfuncout;
                        __Vfunc_f16_q16__38__signed_value 
                            = (0x1ffffffffULL & ((0x8000U 
                                                  & (IData)(__Vfunc_f16_q16__38__h))
                                                  ? 
                                                 (- (QData)((IData)(__Vfunc_f16_q16__38__magnitude)))
                                                  : (QData)((IData)(__Vfunc_f16_q16__38__magnitude))));
                        __Vfunc_sat32__40__x[0U] = (IData)(__Vfunc_f16_q16__38__signed_value);
                        __Vfunc_sat32__40__x[1U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__38__signed_value 
                                                        >> 0x20U))))) 
                              << 1U) | (IData)((__Vfunc_f16_q16__38__signed_value 
                                                >> 0x20U)));
                        __Vfunc_sat32__40__x[2U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__38__signed_value 
                                                        >> 0x20U))))) 
                              >> 0x1fU) | ((- (IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (__Vfunc_f16_q16__38__signed_value 
                                                                  >> 0x20U))))) 
                                           << 1U));
                        __Vfunc_sat32__40__x[3U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__38__signed_value 
                                                        >> 0x20U))))) 
                              >> 0x1fU) | ((- (IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (__Vfunc_f16_q16__38__signed_value 
                                                                  >> 0x20U))))) 
                                           << 1U));
                        __Vtemp_115[0U] = 0x7fffffffU;
                        __Vtemp_115[1U] = 0U;
                        __Vtemp_115[2U] = 0U;
                        __Vtemp_115[3U] = 0U;
                        __Vtemp_116[0U] = 0x80000000U;
                        __Vtemp_116[1U] = 0xffffffffU;
                        __Vtemp_116[2U] = 0xffffffffU;
                        __Vtemp_116[3U] = 0xffffffffU;
                        __Vfunc_sat32__40__Vfuncout 
                            = (VL_LTS_IWW(128, __Vtemp_115, __Vfunc_sat32__40__x)
                                ? 0x7fffffffU : (VL_GTS_IWW(128, __Vtemp_116, __Vfunc_sat32__40__x)
                                                  ? 0x80000000U
                                                  : 
                                                 __Vfunc_sat32__40__x[0U]));
                        __Vfunc_f16_q16__38__Vfuncout 
                            = __Vfunc_sat32__40__Vfuncout;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__bias_value 
                            = __Vfunc_f16_q16__38__Vfuncout;
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x12U;
                }
            } else if ((((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k) 
                        < vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__inputs)) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k 
                    = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k);
                if ((8U == ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index 
                        = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index);
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 2U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset 
                        = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset);
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 6U;
                }
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state 
                    = ((3U > (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection))
                        ? 0x11U : 0x14U);
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                        __Vtemp_119[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[0U];
                        __Vtemp_119[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[1U];
                        __Vtemp_119[2U] = (((IData)(
                                                    (0x7ffffffffffffffULL 
                                                     & (- (QData)((IData)(
                                                                          (1U 
                                                                           & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[2U] 
                                                                              >> 4U))))))) 
                                            << 5U) 
                                           | vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[2U]);
                        __Vtemp_119[3U] = (((IData)(
                                                    (0x7ffffffffffffffULL 
                                                     & (- (QData)((IData)(
                                                                          (1U 
                                                                           & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[2U] 
                                                                              >> 4U))))))) 
                                            >> 0x1bU) 
                                           | ((IData)(
                                                      ((0x7ffffffffffffffULL 
                                                        & (- (QData)((IData)(
                                                                             (1U 
                                                                              & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[2U] 
                                                                                >> 4U)))))) 
                                                       >> 0x20U)) 
                                              << 5U));
                        VL_ADD_W(4, __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9, 
                                 vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators
                                 [vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane], __Vtemp_119);
                        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9 = 1U;
                        __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
                        if ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane))) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0U;
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x10U;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane)));
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0xaU;
                        }
                    } else if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.out_valid) {
                        if (vlSelf->bench__DOT__rst_n) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[0U] 
                                = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[0U];
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[1U] 
                                = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[1U];
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[2U] 
                                = (0x1fU & vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[2U]);
                        } else {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[0U] = 0U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[1U] = 0U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[2U] = 0U;
                        }
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0xfU;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.in_ready) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0xeU;
                    }
                } else if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.out_valid) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight 
                        = (0x1fffffffffULL & (((QData)((IData)(
                                                               ((IData)(vlSelf->bench__DOT__rst_n)
                                                                 ? 
                                                                vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                                                 : 0U))) 
                                               << 0x20U) 
                                              | (QData)((IData)(
                                                                ((IData)(vlSelf->bench__DOT__rst_n)
                                                                  ? 
                                                                 vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                                  : 0U)))));
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0xdU;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier.in_ready) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0xcU;
                    }
                } else {
                    __Vfunc_f16_scale__41__h = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta 
                        = (0x1fU & ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__weight_nibble) 
                                    - (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__zero_nibble)));
                    if ((0U == (0x1fU & ((IData)(__Vfunc_f16_scale__41__h) 
                                         >> 0xaU)))) {
                        __Vfunc_f16_scale__41__magnitude 
                            = (0x3ffU & (IData)(__Vfunc_f16_scale__41__h));
                        __Vfunc_f16_scale__41__shift = 0xfffffff8U;
                    } else {
                        __Vfunc_f16_scale__41__magnitude 
                            = (0x400U | (0x3ffU & (IData)(__Vfunc_f16_scale__41__h)));
                        __Vfunc_f16_scale__41__shift 
                            = ((0x1fU & ((IData)(__Vfunc_f16_scale__41__h) 
                                         >> 0xaU)) 
                               - (IData)(9U));
                    }
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0xbU;
                    __Vfunc_f16_scale__41__magnitude 
                        = (VL_LTES_III(32, 0U, __Vfunc_f16_scale__41__shift)
                            ? VL_SHIFTL_III(32,32,32, __Vfunc_f16_scale__41__magnitude, __Vfunc_f16_scale__41__shift)
                            : VL_SHIFTR_III(32,32,32, 
                                            (__Vfunc_f16_scale__41__magnitude 
                                             + VL_SHIFTL_III(32,32,32, (IData)(1U), 
                                                             ((- __Vfunc_f16_scale__41__shift) 
                                                              - (IData)(1U)))), 
                                            (- __Vfunc_f16_scale__41__shift)));
                    __Vfunc_f16_scale__41__Vfuncout 
                        = __Vfunc_f16_scale__41__magnitude;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scale_integer 
                        = __Vfunc_f16_scale__41__Vfuncout;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0xaU;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 8U;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                    if ((([&]() {
                                    __Vfunc_f16_invalid__42__h 
                                        = (0xffffU 
                                           & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data);
                                    __Vfunc_f16_invalid__42__Vfuncout 
                                        = (0x1fU == 
                                           (0x1fU & 
                                            ((IData)(__Vfunc_f16_invalid__42__h) 
                                             >> 0xaU)));
                                }(), (IData)(__Vfunc_f16_invalid__42__Vfuncout)) 
                         | ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data 
                             >> 0xfU) & (0U != (0x7fffU 
                                                & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data))))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x17U;
                    } else {
                        __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8 
                            = (0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data);
                        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8 = 1U;
                        __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
                        if ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane))) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0U;
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 6U;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane)));
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 4U;
                        }
                    }
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__complete) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__read_data;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__issue) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation = 0U;
            __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v9 = 1U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 2U;
            __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v10 = 1U;
        } else if ((((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)) 
                     | ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)) 
                        | (7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)))) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber4))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__layer;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection;
            if ((((1U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__layer) 
                  | (4U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__position)) 
                 | (6U < (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 1U;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0x18U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__inputs = 8U;
                if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = 2U;
                } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = 3U;
                } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = 4U;
                } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = 5U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = 6U;
                } else if ((4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = 9U;
                } else if ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = 0xaU;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = 0xbU;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = 0xcU;
                }
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 1U;
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__k = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__c = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_index = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__layer = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__inputs = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__outputs = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__source_slot = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__target_slot = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__projection = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__activation = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__bias_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__output_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__delta = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scale_integer = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__dequantized_weight = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__product_value[2U] = 0U;
        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v17 = 1U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[0U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[3U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__quotient_work[4U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__memory_port__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__memory_port__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__memory_port__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__memory_port__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__memory_port__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__memory_port__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__quotient_work;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__memory_port__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__memory_port__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__group_offset;
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][3U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v1) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[6U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[7U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][3U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v8;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v9) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[0U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v10) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[6U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[7U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8][0U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8][1U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8][2U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8][3U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v8[3U];
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9][0U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9][1U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9][2U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9][3U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators__v9[3U];
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v9) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][3U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v10) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][3U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales__v17) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[6U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__scales[7U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[0U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[1U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[2U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[3U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[4U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[5U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[6U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__accumulators[7U][3U] = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__state;
    if (vlSelf->bench__DOT__rst_n) {
        if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state))) {
            if (((6U == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellout__decoder____pinNumber4))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__layer 
                    = vlSelf->bench__DOT__dut__DOT__layer;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__position 
                    = vlSelf->bench__DOT__dut__DOT__position;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__failed = 0U;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__step = 0U;
                if (((1U <= vlSelf->bench__DOT__dut__DOT__layer) 
                     | (4U <= vlSelf->bench__DOT__dut__DOT__position))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 4U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 1U;
                }
            }
        } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state))) {
            if ((1U & ((5U >= (7U & vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))
                        ? ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber4) 
                             << 5U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber4) 
                                        << 4U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber4) 
                                                   << 3U) 
                                                  | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber4) 
                                                      << 2U) 
                                                     | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber4) 
                                                         << 1U) 
                                                        | (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.cmd_ready)))))) 
                           >> (7U & vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))
                        : (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__0)))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state))) {
            if ((1U & ((5U >= (7U & vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))
                        ? ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber8) 
                             << 5U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber7) 
                                        << 4U) | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber7) 
                                                   << 3U) 
                                                  | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber7) 
                                                      << 2U) 
                                                     | (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber8) 
                                                         << 1U) 
                                                        | (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.done)))))) 
                           >> (7U & vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))
                        : (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__1)))) {
                if ((1U & ((5U >= (7U & vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))
                            ? (((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber8) 
                                  & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__failed)) 
                                 << 5U) | ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber7) 
                                             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed)) 
                                            << 4U) 
                                           | ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber7) 
                                                & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed)) 
                                               << 3U) 
                                              | ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber7) 
                                                   & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__failed)) 
                                                  << 2U) 
                                                 | ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber8) 
                                                      & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed)) 
                                                     << 1U) 
                                                    | ((IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.done) 
                                                       & (IData)(vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm.__PVT__failed))))))) 
                               >> (7U & vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected))
                            : (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__2)))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 3U;
                } else if ((0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__step))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 3U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__step 
                        = (0xfU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__step)));
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 1U;
                }
            }
        } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state))) {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 0U;
        } else if ((4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__state))) {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 3U;
        } else {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__failed = 1U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 3U;
        }
    } else {
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__state = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__step = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__failed = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__layer = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__position = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__step 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__step;
    VL_SHIFTL_WWI(130,130,32, __Vtemp_152, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_152[0U] | (1U & vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__dividend_shift[4U]));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_152[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = __Vtemp_152[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[3U] 
        = __Vtemp_152[3U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder[4U] 
        = (3U & __Vtemp_152[4U]);
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
    VL_SHIFTL_WWI(130,130,32, __Vtemp_157, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__remainder_work, 2U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[0U] 
        = (__Vtemp_157[0U] | (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__radicand_shift[3U] 
                              >> 0x1eU));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[1U] 
        = __Vtemp_157[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[2U] 
        = __Vtemp_157[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[3U] 
        = __Vtemp_157[3U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder[4U] 
        = (3U & __Vtemp_157[4U]);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][3U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][2U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][1U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[0U][0U] 
        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered;
    VL_SHIFTL_WWI(65,65,32, __Vtemp_161, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_161[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                            >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_161[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_161[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_165, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_165[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                            >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_165[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_165[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_169, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_169[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                            >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_169[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_169[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_173, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_173[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                            >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_173[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_173[2U]);
    VL_SHIFTL_WWI(65,65,32, __Vtemp_177, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_177[0U] | (1U & (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__dividend_shift 
                                            >> 0x3fU))));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_177[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = (1U & __Vtemp_177[2U]);
    __Vtableidx3 = vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane;
    bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift 
        = Vbench__ConstPool__TABLE_h90db6da8_0[__Vtableidx3];
    if (vlSelf->bench__DOT__rst_n) {
        if (((0xbU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__negative 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                    ^ vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b) 
                   >> 0x1fU);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_a 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a 
                    >> 0x1fU) ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a)
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_a);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_b 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b 
                    >> 0x1fU) ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b)
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__operand_b);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy = 1U;
        }
        if (((8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_a 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value 
                    >> 0x1fU) ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value)
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_b 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b 
                    >> 0x1fU) ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b)
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy = 1U;
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid) 
             & (9U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state)))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy = 0U;
        }
        if (((8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_a 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value 
                    >> 0x1fU) ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value)
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_b 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b 
                    >> 0x1fU) ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b)
                    : vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy = 1U;
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid) 
             & (0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state)))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy = 0U;
        }
        if (((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__multiply_ready))) {
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__busy = 1U;
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_b 
                = ((vlSelf->bench__DOT__dut__DOT__weight_value 
                    >> 0x1fU) ? (- vlSelf->bench__DOT__dut__DOT__weight_value)
                    : vlSelf->bench__DOT__dut__DOT__weight_value);
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_a 
                = ((vlSelf->bench__DOT__dut__DOT__activation 
                    >> 0x1fU) ? (- vlSelf->bench__DOT__dut__DOT__activation)
                    : vlSelf->bench__DOT__dut__DOT__activation);
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__multiply_valid) 
             & (0x10U == (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__busy = 0U;
        }
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
            = (0xfU & VL_SHIFTL_III(4,4,32, (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe), 1U));
        if (((8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready))) {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
                = (1U | (IData)(__Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe));
        }
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__result 
                = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__negative)
                    ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree
                       [2U][0U]) : vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree
                   [2U][0U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result = 1U;
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_valid) 
             & (9U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state)))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result = 0U;
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__rope____pinNumber21))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__failed = 1U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x14U;
        } else if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__failed = 1U;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x14U;
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x14U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state 
                        = ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))
                            ? 0x14U : 0U);
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    if ((4U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index))) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index);
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 1U;
                    } else if ((1U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head))) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head);
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base 
                            = ((IData)(8U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base);
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 1U;
                    } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x14U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 1U;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x13U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x12U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x11U;
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x10U;
                        }
                    } else {
                        __Vfunc_round_shift__31__x[0U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[0U];
                        __Vfunc_round_shift__31__x[1U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[1U];
                        __Vfunc_round_shift__31__x[2U] 
                            = (((IData)((0x7fffffffffffffffULL 
                                         & (- (QData)((IData)(
                                                              (1U 
                                                               & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[2U])))))) 
                                << 1U) | vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[2U]);
                        __Vfunc_round_shift__31__x[3U] 
                            = (((IData)((0x7fffffffffffffffULL 
                                         & (- (QData)((IData)(
                                                              (1U 
                                                               & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[2U])))))) 
                                >> 0x1fU) | ((IData)(
                                                     ((0x7fffffffffffffffULL 
                                                       & (- (QData)((IData)(
                                                                            (1U 
                                                                             & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[2U]))))) 
                                                      >> 0x20U)) 
                                             << 1U));
                        __Vfunc_round_shift__33__x[0U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[0U];
                        __Vfunc_round_shift__33__x[1U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[1U];
                        __Vfunc_round_shift__33__x[2U] 
                            = (((IData)((0x7fffffffffffffffULL 
                                         & (- (QData)((IData)(
                                                              (1U 
                                                               & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[2U])))))) 
                                << 1U) | vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[2U]);
                        __Vfunc_round_shift__33__x[3U] 
                            = (((IData)((0x7fffffffffffffffULL 
                                         & (- (QData)((IData)(
                                                              (1U 
                                                               & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[2U])))))) 
                                >> 0x1fU) | ((IData)(
                                                     ((0x7fffffffffffffffULL 
                                                       & (- (QData)((IData)(
                                                                            (1U 
                                                                             & vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[2U]))))) 
                                                      >> 0x20U)) 
                                             << 1U));
                        __Vtemp_182[0U] = 0U;
                        __Vtemp_182[1U] = 0U;
                        __Vtemp_182[2U] = 0U;
                        __Vtemp_182[3U] = 0U;
                        __Vtemp_183[0U] = __Vfunc_round_shift__31__x[0U];
                        __Vtemp_183[1U] = __Vfunc_round_shift__31__x[1U];
                        __Vtemp_183[2U] = __Vfunc_round_shift__31__x[2U];
                        __Vtemp_183[3U] = __Vfunc_round_shift__31__x[3U];
                        __Vtemp_183[4U] = (__Vfunc_round_shift__31__x[3U] 
                                           >> 0x1fU);
                        VL_NEGATE_W(5, __Vtemp_184, __Vtemp_183);
                        if (VL_GTS_IWW(128, __Vtemp_182, __Vfunc_round_shift__31__x)) {
                            __Vfunc_round_shift__31__magnitude[0U] 
                                = __Vtemp_184[0U];
                            __Vfunc_round_shift__31__magnitude[1U] 
                                = __Vtemp_184[1U];
                            __Vfunc_round_shift__31__magnitude[2U] 
                                = __Vtemp_184[2U];
                            __Vfunc_round_shift__31__magnitude[3U] 
                                = __Vtemp_184[3U];
                            __Vfunc_round_shift__31__magnitude[4U] 
                                = (1U & __Vtemp_184[4U]);
                        } else {
                            __Vfunc_round_shift__31__magnitude[0U] 
                                = __Vfunc_round_shift__31__x[0U];
                            __Vfunc_round_shift__31__magnitude[1U] 
                                = __Vfunc_round_shift__31__x[1U];
                            __Vfunc_round_shift__31__magnitude[2U] 
                                = __Vfunc_round_shift__31__x[2U];
                            __Vfunc_round_shift__31__magnitude[3U] 
                                = __Vfunc_round_shift__31__x[3U];
                            __Vfunc_round_shift__31__magnitude[4U] = 0U;
                        }
                        __Vtemp_189[0U] = 0U;
                        __Vtemp_189[1U] = 0U;
                        __Vtemp_189[2U] = 0U;
                        __Vtemp_189[3U] = 0U;
                        __Vtemp_190[0U] = __Vfunc_round_shift__33__x[0U];
                        __Vtemp_190[1U] = __Vfunc_round_shift__33__x[1U];
                        __Vtemp_190[2U] = __Vfunc_round_shift__33__x[2U];
                        __Vtemp_190[3U] = __Vfunc_round_shift__33__x[3U];
                        __Vtemp_190[4U] = (__Vfunc_round_shift__33__x[3U] 
                                           >> 0x1fU);
                        VL_NEGATE_W(5, __Vtemp_191, __Vtemp_190);
                        if (VL_GTS_IWW(128, __Vtemp_189, __Vfunc_round_shift__33__x)) {
                            __Vfunc_round_shift__33__magnitude[0U] 
                                = __Vtemp_191[0U];
                            __Vfunc_round_shift__33__magnitude[1U] 
                                = __Vtemp_191[1U];
                            __Vfunc_round_shift__33__magnitude[2U] 
                                = __Vtemp_191[2U];
                            __Vfunc_round_shift__33__magnitude[3U] 
                                = __Vtemp_191[3U];
                            __Vfunc_round_shift__33__magnitude[4U] 
                                = (1U & __Vtemp_191[4U]);
                        } else {
                            __Vfunc_round_shift__33__magnitude[0U] 
                                = __Vfunc_round_shift__33__x[0U];
                            __Vfunc_round_shift__33__magnitude[1U] 
                                = __Vfunc_round_shift__33__x[1U];
                            __Vfunc_round_shift__33__magnitude[2U] 
                                = __Vfunc_round_shift__33__x[2U];
                            __Vfunc_round_shift__33__magnitude[3U] 
                                = __Vfunc_round_shift__33__x[3U];
                            __Vfunc_round_shift__33__magnitude[4U] = 0U;
                        }
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0xfU;
                        __Vtemp_198[0U] = 0x20000000U;
                        __Vtemp_198[1U] = 0U;
                        __Vtemp_198[2U] = 0U;
                        __Vtemp_198[3U] = 0U;
                        __Vtemp_198[4U] = 0U;
                        VL_ADD_W(5, __Vtemp_199, __Vtemp_198, __Vfunc_round_shift__31__magnitude);
                        __Vtemp_200[0U] = __Vtemp_199[0U];
                        __Vtemp_200[1U] = __Vtemp_199[1U];
                        __Vtemp_200[2U] = __Vtemp_199[2U];
                        __Vtemp_200[3U] = __Vtemp_199[3U];
                        __Vtemp_200[4U] = (1U & __Vtemp_199[4U]);
                        VL_SHIFTR_WWI(129,129,32, __Vtemp_201, __Vtemp_200, 0x1eU);
                        __Vfunc_round_shift__31__magnitude[0U] 
                            = __Vtemp_201[0U];
                        __Vfunc_round_shift__31__magnitude[1U] 
                            = __Vtemp_201[1U];
                        __Vfunc_round_shift__31__magnitude[2U] 
                            = __Vtemp_201[2U];
                        __Vfunc_round_shift__31__magnitude[3U] 
                            = __Vtemp_201[3U];
                        __Vfunc_round_shift__31__magnitude[4U] 
                            = (1U & __Vtemp_201[4U]);
                        __Vtemp_205[0U] = 0x20000000U;
                        __Vtemp_205[1U] = 0U;
                        __Vtemp_205[2U] = 0U;
                        __Vtemp_205[3U] = 0U;
                        __Vtemp_205[4U] = 0U;
                        VL_ADD_W(5, __Vtemp_206, __Vtemp_205, __Vfunc_round_shift__33__magnitude);
                        __Vtemp_207[0U] = __Vtemp_206[0U];
                        __Vtemp_207[1U] = __Vtemp_206[1U];
                        __Vtemp_207[2U] = __Vtemp_206[2U];
                        __Vtemp_207[3U] = __Vtemp_206[3U];
                        __Vtemp_207[4U] = (1U & __Vtemp_206[4U]);
                        VL_SHIFTR_WWI(129,129,32, __Vtemp_208, __Vtemp_207, 0x1eU);
                        __Vfunc_round_shift__33__magnitude[0U] 
                            = __Vtemp_208[0U];
                        __Vfunc_round_shift__33__magnitude[1U] 
                            = __Vtemp_208[1U];
                        __Vfunc_round_shift__33__magnitude[2U] 
                            = __Vtemp_208[2U];
                        __Vfunc_round_shift__33__magnitude[3U] 
                            = __Vtemp_208[3U];
                        __Vfunc_round_shift__33__magnitude[4U] 
                            = (1U & __Vtemp_208[4U]);
                        __Vtemp_210[0U] = 0U;
                        __Vtemp_210[1U] = 0U;
                        __Vtemp_210[2U] = 0U;
                        __Vtemp_210[3U] = 0U;
                        VL_NEGATE_W(5, __Vtemp_211, __Vfunc_round_shift__31__magnitude);
                        if (VL_GTS_IWW(128, __Vtemp_210, __Vfunc_round_shift__31__x)) {
                            __Vfunc_round_shift__31__Vfuncout[0U] 
                                = __Vtemp_211[0U];
                            __Vfunc_round_shift__31__Vfuncout[1U] 
                                = __Vtemp_211[1U];
                            __Vfunc_round_shift__31__Vfuncout[2U] 
                                = __Vtemp_211[2U];
                            __Vfunc_round_shift__31__Vfuncout[3U] 
                                = __Vtemp_211[3U];
                        } else {
                            __Vfunc_round_shift__31__Vfuncout[0U] 
                                = __Vfunc_round_shift__31__magnitude[0U];
                            __Vfunc_round_shift__31__Vfuncout[1U] 
                                = __Vfunc_round_shift__31__magnitude[1U];
                            __Vfunc_round_shift__31__Vfuncout[2U] 
                                = __Vfunc_round_shift__31__magnitude[2U];
                            __Vfunc_round_shift__31__Vfuncout[3U] 
                                = __Vfunc_round_shift__31__magnitude[3U];
                        }
                        __Vtemp_216[0U] = 0U;
                        __Vtemp_216[1U] = 0U;
                        __Vtemp_216[2U] = 0U;
                        __Vtemp_216[3U] = 0U;
                        VL_NEGATE_W(5, __Vtemp_217, __Vfunc_round_shift__33__magnitude);
                        if (VL_GTS_IWW(128, __Vtemp_216, __Vfunc_round_shift__33__x)) {
                            __Vfunc_round_shift__33__Vfuncout[0U] 
                                = __Vtemp_217[0U];
                            __Vfunc_round_shift__33__Vfuncout[1U] 
                                = __Vtemp_217[1U];
                            __Vfunc_round_shift__33__Vfuncout[2U] 
                                = __Vtemp_217[2U];
                            __Vfunc_round_shift__33__Vfuncout[3U] 
                                = __Vtemp_217[3U];
                        } else {
                            __Vfunc_round_shift__33__Vfuncout[0U] 
                                = __Vfunc_round_shift__33__magnitude[0U];
                            __Vfunc_round_shift__33__Vfuncout[1U] 
                                = __Vfunc_round_shift__33__magnitude[1U];
                            __Vfunc_round_shift__33__Vfuncout[2U] 
                                = __Vfunc_round_shift__33__magnitude[2U];
                            __Vfunc_round_shift__33__Vfuncout[3U] 
                                = __Vfunc_round_shift__33__magnitude[3U];
                        }
                        __Vfunc_sat32__30__x[0U] = 
                            __Vfunc_round_shift__31__Vfuncout[0U];
                        __Vfunc_sat32__30__x[1U] = 
                            __Vfunc_round_shift__31__Vfuncout[1U];
                        __Vfunc_sat32__30__x[2U] = 
                            __Vfunc_round_shift__31__Vfuncout[2U];
                        __Vfunc_sat32__30__x[3U] = 
                            __Vfunc_round_shift__31__Vfuncout[3U];
                        __Vfunc_sat32__32__x[0U] = 
                            __Vfunc_round_shift__33__Vfuncout[0U];
                        __Vfunc_sat32__32__x[1U] = 
                            __Vfunc_round_shift__33__Vfuncout[1U];
                        __Vfunc_sat32__32__x[2U] = 
                            __Vfunc_round_shift__33__Vfuncout[2U];
                        __Vfunc_sat32__32__x[3U] = 
                            __Vfunc_round_shift__33__Vfuncout[3U];
                        __Vtemp_221[0U] = 0x7fffffffU;
                        __Vtemp_221[1U] = 0U;
                        __Vtemp_221[2U] = 0U;
                        __Vtemp_221[3U] = 0U;
                        __Vtemp_222[0U] = 0x80000000U;
                        __Vtemp_222[1U] = 0xffffffffU;
                        __Vtemp_222[2U] = 0xffffffffU;
                        __Vtemp_222[3U] = 0xffffffffU;
                        __Vfunc_sat32__30__Vfuncout 
                            = (VL_LTS_IWW(128, __Vtemp_221, __Vfunc_sat32__30__x)
                                ? 0x7fffffffU : (VL_GTS_IWW(128, __Vtemp_222, __Vfunc_sat32__30__x)
                                                  ? 0x80000000U
                                                  : 
                                                 __Vfunc_sat32__30__x[0U]));
                        __Vtemp_223[0U] = 0x7fffffffU;
                        __Vtemp_223[1U] = 0U;
                        __Vtemp_223[2U] = 0U;
                        __Vtemp_223[3U] = 0U;
                        __Vtemp_224[0U] = 0x80000000U;
                        __Vtemp_224[1U] = 0xffffffffU;
                        __Vtemp_224[2U] = 0xffffffffU;
                        __Vtemp_224[3U] = 0xffffffffU;
                        __Vfunc_sat32__32__Vfuncout 
                            = (VL_LTS_IWW(128, __Vtemp_223, __Vfunc_sat32__32__x)
                                ? 0x7fffffffU : (VL_GTS_IWW(128, __Vtemp_224, __Vfunc_sat32__32__x)
                                                  ? 0x80000000U
                                                  : 
                                                 __Vfunc_sat32__32__x[0U]));
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x 
                            = __Vfunc_sat32__30__Vfuncout;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y 
                            = __Vfunc_sat32__32__Vfuncout;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    __Vtemp_226[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_cos);
                    __Vtemp_226[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_cos 
                                               >> 0x20U));
                    __Vtemp_226[2U] = (1U & (IData)(
                                                    (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_cos 
                                                     >> 0x3fU)));
                    __Vtemp_227[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_sin);
                    __Vtemp_227[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_sin 
                                               >> 0x20U));
                    __Vtemp_227[2U] = (1U & (IData)(
                                                    (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_sin 
                                                     >> 0x3fU)));
                    VL_SUB_W(3, __Vtemp_228, __Vtemp_226, __Vtemp_227);
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[0U] 
                        = __Vtemp_228[0U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[1U] 
                        = __Vtemp_228[1U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[2U] 
                        = (1U & __Vtemp_228[2U]);
                    __Vtemp_230[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_cos);
                    __Vtemp_230[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_cos 
                                               >> 0x20U));
                    __Vtemp_230[2U] = (1U & (IData)(
                                                    (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_cos 
                                                     >> 0x3fU)));
                    __Vtemp_231[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_sin);
                    __Vtemp_231[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_sin 
                                               >> 0x20U));
                    __Vtemp_231[2U] = (1U & (IData)(
                                                    (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_sin 
                                                     >> 0x3fU)));
                    VL_ADD_W(3, __Vtemp_232, __Vtemp_230, __Vtemp_231);
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[0U] 
                        = __Vtemp_232[0U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[1U] 
                        = __Vtemp_232[1U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[2U] 
                        = (1U & __Vtemp_232[2U]);
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0xeU;
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_valid) {
                    if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_cos 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product;
                    } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_sin 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product;
                    } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_cos 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product;
                    } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_sin 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product;
                    }
                    if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index))) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0xdU;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index 
                            = (3U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index)));
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0xbU;
                    }
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiply_ready) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0xcU;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index = 0U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__sine 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__read_data;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0xbU;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0xaU;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__cosine 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__read_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 8U;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__read_data;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 6U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__complete) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__read_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 4U;
                }
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y 
                    = ((IData)(4U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x);
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x 
                = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base 
                   + vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index);
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 2U;
        } else if ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0) 
                     & (2U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__rope____pinNumber4))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__position 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__position;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector = 0U;
            if (((1U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer) 
                 | (4U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__position))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__failed = 1U;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0x15U;
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 1U;
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__negative = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__busy = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__busy = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_a = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__magnitude_b = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__busy = 0U;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__busy = 0U;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_b = 0U;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__magnitude_a = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_result = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__result = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__product_index = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__key_vector = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__position = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_x = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__coordinate_y = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__cosine = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__sine = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_x = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__output_y = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_cos = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_sin = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__y_cos = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__x_sin = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_x[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__rotated_y[2U] = 0U;
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__fault) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 1U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x17U;
        } else if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x17U;
                } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x17U;
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x17U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x17U;
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qw = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qz = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0U;
                        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v0 = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0U;
                        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v1 = 1U;
                    } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                        if ((7U > (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane))) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane)));
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x14U;
                        } else if ((((IData)(8U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c) 
                                    < vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs)) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c 
                                = ((IData)(8U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c);
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 1U;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x17U;
                        }
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x16U;
                    }
                } else {
                    __Vfunc_round_shift__23__x[0U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane][0U];
                    __Vfunc_round_shift__23__x[1U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane][1U];
                    __Vfunc_round_shift__23__x[2U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane][2U];
                    __Vfunc_round_shift__23__x[3U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane][3U];
                    __Vtemp_236[0U] = 0U;
                    __Vtemp_236[1U] = 0U;
                    __Vtemp_236[2U] = 0U;
                    __Vtemp_236[3U] = 0U;
                    __Vtemp_237[0U] = __Vfunc_round_shift__23__x[0U];
                    __Vtemp_237[1U] = __Vfunc_round_shift__23__x[1U];
                    __Vtemp_237[2U] = __Vfunc_round_shift__23__x[2U];
                    __Vtemp_237[3U] = __Vfunc_round_shift__23__x[3U];
                    __Vtemp_237[4U] = (__Vfunc_round_shift__23__x[3U] 
                                       >> 0x1fU);
                    VL_NEGATE_W(5, __Vtemp_238, __Vtemp_237);
                    if (VL_GTS_IWW(128, __Vtemp_236, __Vfunc_round_shift__23__x)) {
                        __Vfunc_round_shift__23__magnitude[0U] 
                            = __Vtemp_238[0U];
                        __Vfunc_round_shift__23__magnitude[1U] 
                            = __Vtemp_238[1U];
                        __Vfunc_round_shift__23__magnitude[2U] 
                            = __Vtemp_238[2U];
                        __Vfunc_round_shift__23__magnitude[3U] 
                            = __Vtemp_238[3U];
                        __Vfunc_round_shift__23__magnitude[4U] 
                            = (1U & __Vtemp_238[4U]);
                    } else {
                        __Vfunc_round_shift__23__magnitude[0U] 
                            = __Vfunc_round_shift__23__x[0U];
                        __Vfunc_round_shift__23__magnitude[1U] 
                            = __Vfunc_round_shift__23__x[1U];
                        __Vfunc_round_shift__23__magnitude[2U] 
                            = __Vfunc_round_shift__23__x[2U];
                        __Vfunc_round_shift__23__magnitude[3U] 
                            = __Vfunc_round_shift__23__x[3U];
                        __Vfunc_round_shift__23__magnitude[4U] = 0U;
                    }
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x15U;
                    __Vtemp_245[0U] = 0x8000U;
                    __Vtemp_245[1U] = 0U;
                    __Vtemp_245[2U] = 0U;
                    __Vtemp_245[3U] = 0U;
                    __Vtemp_245[4U] = 0U;
                    VL_ADD_W(5, __Vtemp_246, __Vtemp_245, __Vfunc_round_shift__23__magnitude);
                    __Vtemp_247[0U] = __Vtemp_246[0U];
                    __Vtemp_247[1U] = __Vtemp_246[1U];
                    __Vtemp_247[2U] = __Vtemp_246[2U];
                    __Vtemp_247[3U] = __Vtemp_246[3U];
                    __Vtemp_247[4U] = (1U & __Vtemp_246[4U]);
                    VL_SHIFTR_WWI(129,129,32, __Vtemp_248, __Vtemp_247, 0x10U);
                    __Vfunc_round_shift__23__magnitude[0U] 
                        = __Vtemp_248[0U];
                    __Vfunc_round_shift__23__magnitude[1U] 
                        = __Vtemp_248[1U];
                    __Vfunc_round_shift__23__magnitude[2U] 
                        = __Vtemp_248[2U];
                    __Vfunc_round_shift__23__magnitude[3U] 
                        = __Vtemp_248[3U];
                    __Vfunc_round_shift__23__magnitude[4U] 
                        = (1U & __Vtemp_248[4U]);
                    __Vtemp_250[0U] = 0U;
                    __Vtemp_250[1U] = 0U;
                    __Vtemp_250[2U] = 0U;
                    __Vtemp_250[3U] = 0U;
                    VL_NEGATE_W(5, __Vtemp_251, __Vfunc_round_shift__23__magnitude);
                    if (VL_GTS_IWW(128, __Vtemp_250, __Vfunc_round_shift__23__x)) {
                        __Vfunc_round_shift__23__Vfuncout[0U] 
                            = __Vtemp_251[0U];
                        __Vfunc_round_shift__23__Vfuncout[1U] 
                            = __Vtemp_251[1U];
                        __Vfunc_round_shift__23__Vfuncout[2U] 
                            = __Vtemp_251[2U];
                        __Vfunc_round_shift__23__Vfuncout[3U] 
                            = __Vtemp_251[3U];
                    } else {
                        __Vfunc_round_shift__23__Vfuncout[0U] 
                            = __Vfunc_round_shift__23__magnitude[0U];
                        __Vfunc_round_shift__23__Vfuncout[1U] 
                            = __Vfunc_round_shift__23__magnitude[1U];
                        __Vfunc_round_shift__23__Vfuncout[2U] 
                            = __Vfunc_round_shift__23__magnitude[2U];
                        __Vfunc_round_shift__23__Vfuncout[3U] 
                            = __Vfunc_round_shift__23__magnitude[3U];
                    }
                    __Vfunc_sat32__22__x[0U] = __Vfunc_round_shift__23__Vfuncout[0U];
                    __Vfunc_sat32__22__x[1U] = __Vfunc_round_shift__23__Vfuncout[1U];
                    __Vfunc_sat32__22__x[2U] = __Vfunc_round_shift__23__Vfuncout[2U];
                    __Vfunc_sat32__22__x[3U] = __Vfunc_round_shift__23__Vfuncout[3U];
                    __Vtemp_255[0U] = 0x7fffffffU;
                    __Vtemp_255[1U] = 0U;
                    __Vtemp_255[2U] = 0U;
                    __Vtemp_255[3U] = 0U;
                    __Vtemp_256[0U] = 0x80000000U;
                    __Vtemp_256[1U] = 0xffffffffU;
                    __Vtemp_256[2U] = 0xffffffffU;
                    __Vtemp_256[3U] = 0xffffffffU;
                    __Vfunc_sat32__22__Vfuncout = (
                                                   VL_LTS_IWW(128, __Vtemp_255, __Vfunc_sat32__22__x)
                                                    ? 0x7fffffffU
                                                    : 
                                                   (VL_GTS_IWW(128, __Vtemp_256, __Vfunc_sat32__22__x)
                                                     ? 0x80000000U
                                                     : 
                                                    __Vfunc_sat32__22__x[0U]));
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__output_value 
                        = __Vfunc_sat32__22__Vfuncout;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    __Vtemp_258[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__bias_value;
                    __Vtemp_258[1U] = (- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__bias_value 
                                                  >> 0x1fU)));
                    __Vtemp_258[2U] = (- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__bias_value 
                                                  >> 0x1fU)));
                    __Vtemp_258[3U] = (- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__bias_value 
                                                  >> 0x1fU)));
                    VL_SHIFTL_WWI(128,128,32, __Vtemp_259, __Vtemp_258, 0x10U);
                    VL_ADD_W(4, __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8, 
                             vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators
                             [vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane], __Vtemp_259);
                    __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8 = 1U;
                    __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane;
                    if ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane))) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x14U;
                    } else {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane 
                            = (7U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane)));
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x11U;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                    if (([&]() {
                                __Vfunc_f16_invalid__24__h 
                                    = (0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data);
                                __Vfunc_f16_invalid__24__Vfuncout 
                                    = (0x1fU == (0x1fU 
                                                 & ((IData)(__Vfunc_f16_invalid__24__h) 
                                                    >> 0xaU)));
                            }(), (IData)(__Vfunc_f16_invalid__24__Vfuncout))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x17U;
                    } else {
                        __Vfunc_f16_q16__25__h = (0xffffU 
                                                  & vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data);
                        __Vfunc_f16_scale__26__h = __Vfunc_f16_q16__25__h;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x13U;
                        if ((0U == (0x1fU & ((IData)(__Vfunc_f16_scale__26__h) 
                                             >> 0xaU)))) {
                            __Vfunc_f16_scale__26__magnitude 
                                = (0x3ffU & (IData)(__Vfunc_f16_scale__26__h));
                            __Vfunc_f16_scale__26__shift = 0xfffffff8U;
                        } else {
                            __Vfunc_f16_scale__26__magnitude 
                                = (0x400U | (0x3ffU 
                                             & (IData)(__Vfunc_f16_scale__26__h)));
                            __Vfunc_f16_scale__26__shift 
                                = ((0x1fU & ((IData)(__Vfunc_f16_scale__26__h) 
                                             >> 0xaU)) 
                                   - (IData)(9U));
                        }
                        __Vfunc_f16_scale__26__magnitude 
                            = (VL_LTES_III(32, 0U, __Vfunc_f16_scale__26__shift)
                                ? VL_SHIFTL_III(32,32,32, __Vfunc_f16_scale__26__magnitude, __Vfunc_f16_scale__26__shift)
                                : VL_SHIFTR_III(32,32,32, 
                                                (__Vfunc_f16_scale__26__magnitude 
                                                 + 
                                                 VL_SHIFTL_III(32,32,32, (IData)(1U), 
                                                               ((- __Vfunc_f16_scale__26__shift) 
                                                                - (IData)(1U)))), 
                                                (- __Vfunc_f16_scale__26__shift)));
                        __Vfunc_f16_scale__26__Vfuncout 
                            = __Vfunc_f16_scale__26__magnitude;
                        __Vfunc_f16_q16__25__magnitude 
                            = __Vfunc_f16_scale__26__Vfuncout;
                        __Vfunc_f16_q16__25__signed_value 
                            = (0x1ffffffffULL & ((0x8000U 
                                                  & (IData)(__Vfunc_f16_q16__25__h))
                                                  ? 
                                                 (- (QData)((IData)(__Vfunc_f16_q16__25__magnitude)))
                                                  : (QData)((IData)(__Vfunc_f16_q16__25__magnitude))));
                        __Vfunc_sat32__27__x[0U] = (IData)(__Vfunc_f16_q16__25__signed_value);
                        __Vfunc_sat32__27__x[1U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__25__signed_value 
                                                        >> 0x20U))))) 
                              << 1U) | (IData)((__Vfunc_f16_q16__25__signed_value 
                                                >> 0x20U)));
                        __Vfunc_sat32__27__x[2U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__25__signed_value 
                                                        >> 0x20U))))) 
                              >> 0x1fU) | ((- (IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (__Vfunc_f16_q16__25__signed_value 
                                                                  >> 0x20U))))) 
                                           << 1U));
                        __Vfunc_sat32__27__x[3U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__25__signed_value 
                                                        >> 0x20U))))) 
                              >> 0x1fU) | ((- (IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (__Vfunc_f16_q16__25__signed_value 
                                                                  >> 0x20U))))) 
                                           << 1U));
                        __Vtemp_264[0U] = 0x7fffffffU;
                        __Vtemp_264[1U] = 0U;
                        __Vtemp_264[2U] = 0U;
                        __Vtemp_264[3U] = 0U;
                        __Vtemp_265[0U] = 0x80000000U;
                        __Vtemp_265[1U] = 0xffffffffU;
                        __Vtemp_265[2U] = 0xffffffffU;
                        __Vtemp_265[3U] = 0xffffffffU;
                        __Vfunc_sat32__27__Vfuncout 
                            = (VL_LTS_IWW(128, __Vtemp_264, __Vfunc_sat32__27__x)
                                ? 0x7fffffffU : (VL_GTS_IWW(128, __Vtemp_265, __Vfunc_sat32__27__x)
                                                  ? 0x80000000U
                                                  : 
                                                 __Vfunc_sat32__27__x[0U]));
                        __Vfunc_f16_q16__25__Vfuncout 
                            = __Vfunc_sat32__27__Vfuncout;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__bias_value 
                            = __Vfunc_f16_q16__25__Vfuncout;
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x12U;
                }
            } else if ((((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k) 
                        < vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__inputs)) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k 
                    = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k);
                if ((8U == ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index 
                        = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index);
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 2U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset 
                        = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset);
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 6U;
                }
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state 
                    = ((3U > (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection))
                        ? 0x11U : 0x14U);
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                        __Vtemp_268[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[0U];
                        __Vtemp_268[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[1U];
                        __Vtemp_268[2U] = (((IData)(
                                                    (0x7ffffffffffffffULL 
                                                     & (- (QData)((IData)(
                                                                          (1U 
                                                                           & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[2U] 
                                                                              >> 4U))))))) 
                                            << 5U) 
                                           | vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[2U]);
                        __Vtemp_268[3U] = (((IData)(
                                                    (0x7ffffffffffffffULL 
                                                     & (- (QData)((IData)(
                                                                          (1U 
                                                                           & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[2U] 
                                                                              >> 4U))))))) 
                                            >> 0x1bU) 
                                           | ((IData)(
                                                      ((0x7ffffffffffffffULL 
                                                        & (- (QData)((IData)(
                                                                             (1U 
                                                                              & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[2U] 
                                                                                >> 4U)))))) 
                                                       >> 0x20U)) 
                                              << 5U));
                        VL_ADD_W(4, __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9, 
                                 vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators
                                 [vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane], __Vtemp_268);
                        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9 = 1U;
                        __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane;
                        if ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane))) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0U;
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x10U;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane)));
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0xaU;
                        }
                    } else if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.out_valid) {
                        if (vlSelf->bench__DOT__rst_n) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[0U] 
                                = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[0U];
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[1U] 
                                = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[1U];
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[2U] 
                                = (0x1fU & vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[2U]);
                        } else {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[0U] = 0U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[1U] = 0U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[2U] = 0U;
                        }
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0xfU;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.in_ready) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0xeU;
                    }
                } else if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.out_valid) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__dequantized_weight 
                        = (0x1fffffffffULL & (((QData)((IData)(
                                                               ((IData)(vlSelf->bench__DOT__rst_n)
                                                                 ? 
                                                                vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                                                 : 0U))) 
                                               << 0x20U) 
                                              | (QData)((IData)(
                                                                ((IData)(vlSelf->bench__DOT__rst_n)
                                                                  ? 
                                                                 vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                                  : 0U)))));
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0xdU;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier.in_ready) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0xcU;
                    }
                } else {
                    __Vfunc_f16_scale__28__h = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales
                        [vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__delta 
                        = (0x1fU & ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__weight_nibble) 
                                    - (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__zero_nibble)));
                    if ((0U == (0x1fU & ((IData)(__Vfunc_f16_scale__28__h) 
                                         >> 0xaU)))) {
                        __Vfunc_f16_scale__28__magnitude 
                            = (0x3ffU & (IData)(__Vfunc_f16_scale__28__h));
                        __Vfunc_f16_scale__28__shift = 0xfffffff8U;
                    } else {
                        __Vfunc_f16_scale__28__magnitude 
                            = (0x400U | (0x3ffU & (IData)(__Vfunc_f16_scale__28__h)));
                        __Vfunc_f16_scale__28__shift 
                            = ((0x1fU & ((IData)(__Vfunc_f16_scale__28__h) 
                                         >> 0xaU)) 
                               - (IData)(9U));
                    }
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0xbU;
                    __Vfunc_f16_scale__28__magnitude 
                        = (VL_LTES_III(32, 0U, __Vfunc_f16_scale__28__shift)
                            ? VL_SHIFTL_III(32,32,32, __Vfunc_f16_scale__28__magnitude, __Vfunc_f16_scale__28__shift)
                            : VL_SHIFTR_III(32,32,32, 
                                            (__Vfunc_f16_scale__28__magnitude 
                                             + VL_SHIFTL_III(32,32,32, (IData)(1U), 
                                                             ((- __Vfunc_f16_scale__28__shift) 
                                                              - (IData)(1U)))), 
                                            (- __Vfunc_f16_scale__28__shift)));
                    __Vfunc_f16_scale__28__Vfuncout 
                        = __Vfunc_f16_scale__28__magnitude;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scale_integer 
                        = __Vfunc_f16_scale__28__Vfuncout;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qw 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0xaU;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 8U;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                    if ((([&]() {
                                    __Vfunc_f16_invalid__29__h 
                                        = (0xffffU 
                                           & vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data);
                                    __Vfunc_f16_invalid__29__Vfuncout 
                                        = (0x1fU == 
                                           (0x1fU & 
                                            ((IData)(__Vfunc_f16_invalid__29__h) 
                                             >> 0xaU)));
                                }(), (IData)(__Vfunc_f16_invalid__29__Vfuncout)) 
                         | ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data 
                             >> 0xfU) & (0U != (0x7fffU 
                                                & vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data))))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x17U;
                    } else {
                        __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8 
                            = (0xffffU & vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data);
                        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8 = 1U;
                        __Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane;
                        if ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane))) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0U;
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 6U;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane 
                                = (7U & ((IData)(1U) 
                                         + (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane)));
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 4U;
                        }
                    }
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__complete) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qz 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__read_data;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__issue) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qw = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qz = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation = 0U;
            __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v9 = 1U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 2U;
            __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v10 = 1U;
        } else if ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0) 
                     & (1U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__gemv____pinNumber4))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection;
            if ((((1U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer) 
                  | (4U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__position)) 
                 | (6U < (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection)))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 1U;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0x18U;
            } else {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__inputs = 8U;
                if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = 2U;
                } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = 3U;
                } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = 1U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = 4U;
                } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = 5U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = 6U;
                } else if ((4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = 9U;
                } else if ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__projection))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = 0xaU;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = 0xbU;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = 0xcU;
                }
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 1U;
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__k = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__c = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_index = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__layer = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__inputs = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__outputs = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__source_slot = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__target_slot = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__projection = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qw = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qz = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__activation = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__bias_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__output_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__delta = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scale_integer = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__dequantized_weight = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__product_value[2U] = 0U;
        __Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v17 = 1U;
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__attention____pinNumber21))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
        } else if ((0x20U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
            if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
            } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U] = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U] = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U] = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[0U] = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[1U] = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U] = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator = 0ULL;
                    if ((8U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 7U;
                    } else if ((1U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head);
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base 
                            = ((IData)(8U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base);
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component = 0U;
                        if ((1U == ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head))) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base 
                                = ((IData)(8U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base);
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head = 0U;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head 
                                = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head);
                        }
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U] = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U] = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U] = 0x80000000U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 7U;
                    } else {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x22U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x21U;
            }
        } else if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
            if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                            __Vfunc_sat32__34__x[0U] 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[0U];
                            __Vfunc_sat32__34__x[1U] 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[1U];
                            __Vfunc_sat32__34__x[2U] 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[2U];
                            __Vfunc_sat32__34__x[3U] 
                                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[3U];
                            __Vtemp_278[0U] = 0x7fffffffU;
                            __Vtemp_278[1U] = 0U;
                            __Vtemp_278[2U] = 0U;
                            __Vtemp_278[3U] = 0U;
                            __Vtemp_279[0U] = 0x80000000U;
                            __Vtemp_279[1U] = 0xffffffffU;
                            __Vtemp_279[2U] = 0xffffffffU;
                            __Vtemp_279[3U] = 0xffffffffU;
                            __Vfunc_sat32__34__Vfuncout 
                                = (VL_LTS_IWW(128, __Vtemp_278, __Vfunc_sat32__34__x)
                                    ? 0x7fffffffU : 
                                   (VL_GTS_IWW(128, __Vtemp_279, __Vfunc_sat32__34__x)
                                     ? 0x80000000U : 
                                    __Vfunc_sat32__34__x[0U]));
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__output_value 
                                = __Vfunc_sat32__34__Vfuncout;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x20U;
                        } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid) {
                            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_error) {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                            } else {
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[0U] 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[0U];
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[1U] 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[1U];
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[2U] 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[2U];
                                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[3U] 
                                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[3U];
                                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x1fU;
                            }
                        }
                    } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready) {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x1eU;
                        }
                    } else if ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index 
                                < vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__position)) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index);
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U] = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U] = 0U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U] = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 7U;
                    } else if ((0ULL == vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator)) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                    } else {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x1dU;
                    }
                } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        __Vtemp_280[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[0U];
                        __Vtemp_280[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[1U];
                        __Vtemp_280[2U] = (((- (IData)(
                                                       (1U 
                                                        & vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[2U]))) 
                                            << 1U) 
                                           | vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[2U]);
                        VL_ADD_W(3, __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted, __Vtemp_280);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x1cU;
                    } else if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.out_valid) {
                        if (vlSelf->bench__DOT__rst_n) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[0U] 
                                = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.__PVT__multiplier__DOT__result[0U];
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[1U] 
                                = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.__PVT__multiplier__DOT__result[1U];
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[2U] 
                                = (1U & vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.__PVT__multiplier__DOT__result[2U]);
                        } else {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[0U] = 0U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[1U] = 0U;
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[2U] = 0U;
                        }
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x1bU;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.in_ready) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x1aU;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__read_data;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x19U;
                }
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue) {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x18U;
                        }
                    } else {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator 
                            = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator 
                               + (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential)));
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x17U;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_valid) {
                        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__failed) 
                             & (IData)(vlSelf->bench__DOT__rst_n))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                        } else {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential 
                                = ((IData)(vlSelf->bench__DOT__rst_n)
                                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__result
                                    : 0U);
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x16U;
                        }
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x15U;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    __Vtemp_285[0U] = 0xfff00000U;
                    __Vtemp_285[1U] = 0xffffffffU;
                    __Vtemp_285[2U] = 0xffffffffU;
                    __Vtemp_285[3U] = 1U;
                    __Vtemp_286[0U] = 0U;
                    __Vtemp_286[1U] = 0U;
                    __Vtemp_286[2U] = 0U;
                    __Vtemp_286[3U] = 0U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_argument 
                        = (VL_GTS_IWW(97, __Vtemp_285, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference)
                            ? 0xffffffffffefffffULL
                            : (VL_LTS_IWW(97, __Vtemp_286, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference)
                                ? 0ULL : (((QData)((IData)(
                                                           vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[1U])) 
                                           << 0x20U) 
                                          | (QData)((IData)(
                                                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[0U])))));
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x14U;
                } else {
                    __Vtemp_288[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[0U];
                    __Vtemp_288[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[1U];
                    __Vtemp_288[2U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[2U];
                    __Vtemp_288[3U] = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[2U] 
                                       >> 0x1fU);
                    __Vtemp_289[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U];
                    __Vtemp_289[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U];
                    __Vtemp_289[2U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U];
                    __Vtemp_289[3U] = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U] 
                                       >> 0x1fU);
                    VL_SUB_W(4, __Vtemp_290, __Vtemp_288, __Vtemp_289);
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[0U] 
                        = __Vtemp_290[0U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[1U] 
                        = __Vtemp_290[1U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[2U] 
                        = __Vtemp_290[2U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[3U] 
                        = (1U & __Vtemp_290[3U]);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x13U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x12U;
                } else {
                    if (VL_GTS_IWW(96, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score)) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[0U];
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[1U];
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U] 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[2U];
                    }
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index 
                        = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index 
                            < vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__position)
                            ? ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index)
                            : 0U);
                    if ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index 
                         == vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__position)) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass = 1U;
                    }
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U] = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U] = 0U;
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U] = 0U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 7U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_valid) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_error) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[0U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[0U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[1U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[1U];
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[2U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__division_result[2U];
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x11U;
                }
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                        if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divide_ready) {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x10U;
                        }
                    } else {
                        __Vtemp_291[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot_product);
                        __Vtemp_291[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot_product 
                                                   >> 0x20U));
                        __Vtemp_291[2U] = (- (IData)(
                                                     (1U 
                                                      & (IData)(
                                                                (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot_product 
                                                                 >> 0x3fU)))));
                        VL_ADD_W(3, __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot, __Vtemp_291);
                        if ((8U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim))) {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim 
                                = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim);
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 7U;
                        } else {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0xfU;
                        }
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.out_valid) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot_product 
                            = (((QData)((IData)(((IData)(vlSelf->bench__DOT__rst_n)
                                                  ? 
                                                 vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.__PVT__multiplier__DOT__result[1U]
                                                  : 0U))) 
                                << 0x20U) | (QData)((IData)(
                                                            ((IData)(vlSelf->bench__DOT__rst_n)
                                                              ? 
                                                             vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.__PVT__multiplier__DOT__result[0U]
                                                              : 0U))));
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0xeU;
                    }
                } else if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier.in_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0xdU;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data 
                            = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__read_data;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0xcU;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0xbU;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__read_data;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0xaU;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q_column 
                        = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base 
                           + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 8U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__k_column 
                        = (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base 
                           + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim);
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete) {
                    if ((8ULL > (1ULL + (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index))))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 3U;
                    } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 7U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 3U;
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 6U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__complete) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__read_data;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__issue) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_valid) {
                if ((0ULL == vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_value)) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x23U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__sqrt_dimension 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_value;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 3U;
                }
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_ready) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 2U;
            }
        } else if ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0) 
                     & (3U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__attention____pinNumber4))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__position 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__position;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U] = 0x80000000U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[0U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[1U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U] = 0U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator = 0ULL;
            if (((1U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer) 
                 | (4U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__position))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0x24U;
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 1U;
            }
        }
        if (((((((((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)) 
                   | (1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) 
                  | (2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) 
                 | (3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) 
                | (4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) 
               | (5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) 
              | (6U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) 
             | (7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state)))) {
            if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
                if ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0) 
                      & (4U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__mlp____pinNumber4))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed = 0U;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__layer 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__position 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__position;
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection = 4U;
                    if (((1U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer) 
                         | (4U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__position))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0xeU;
                    } else {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 1U;
                    }
                }
            } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__ready))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 2U;
                }
            } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__finished))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__faults))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0xfU;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection = 5U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 3U;
                    }
                }
            } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__ready))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 4U;
                }
            } else if ((4U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__finished))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__faults))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0xfU;
                    } else {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 5U;
                    }
                }
            } else if ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__ready))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 6U;
                }
            } else if ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__finished))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__faults))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0xfU;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection = 6U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 7U;
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__ready))) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 8U;
            }
        } else if ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__finished))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed 
                    = (1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__faults));
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0xfU;
            }
        } else if ((0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0xfU;
        } else if ((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state))) {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0U;
        } else {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed = 1U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0xfU;
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__index = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__component = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__value_cache = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__layer = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__position = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q_column = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__k_column = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__q = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__output_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot_product = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exp_argument = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted_product[2U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__current_score[2U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[0U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[1U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__score_difference[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__divided_output[3U] = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__sqrt_dimension = 0ULL;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__layer = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__position = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__projection = 0U;
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellinp__residual____pinNumber22))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__failed = 1U;
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xdU;
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xdU;
                    } else {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xdU;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0U;
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete) {
                    if ((8U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__index))) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__index 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__index);
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 1U;
                    } else {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xdU;
                    }
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue) {
                        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xcU;
                    }
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__output_value 
                        = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                            ? ([&]() {
                                __Vfunc_round_shift__49__x[0U] 
                                    = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__product_value);
                                __Vfunc_round_shift__49__x[1U] 
                                    = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__product_value 
                                               >> 0x20U));
                                __Vfunc_round_shift__49__x[2U] 
                                    = (IData)((- (QData)((IData)(
                                                                 (1U 
                                                                  & (IData)(
                                                                            (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__product_value 
                                                                             >> 0x3fU)))))));
                                __Vfunc_round_shift__49__x[3U] 
                                    = (IData)(((- (QData)((IData)(
                                                                  (1U 
                                                                   & (IData)(
                                                                             (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__product_value 
                                                                              >> 0x3fU)))))) 
                                               >> 0x20U));
                                __Vtemp_297[0U] = 0U;
                                __Vtemp_297[1U] = 0U;
                                __Vtemp_297[2U] = 0U;
                                __Vtemp_297[3U] = 0U;
                                __Vtemp_298[0U] = __Vfunc_round_shift__49__x[0U];
                                __Vtemp_298[1U] = __Vfunc_round_shift__49__x[1U];
                                __Vtemp_298[2U] = __Vfunc_round_shift__49__x[2U];
                                __Vtemp_298[3U] = __Vfunc_round_shift__49__x[3U];
                                __Vtemp_298[4U] = (
                                                   __Vfunc_round_shift__49__x[3U] 
                                                   >> 0x1fU);
                                VL_NEGATE_W(5, __Vtemp_299, __Vtemp_298);
                                __Vfunc_round_shift__49__magnitude[0U] 
                                    = (VL_GTS_IWW(128, __Vtemp_297, __Vfunc_round_shift__49__x)
                                        ? __Vtemp_299[0U]
                                        : __Vfunc_round_shift__49__x[0U]);
                                __Vfunc_round_shift__49__magnitude[1U] 
                                    = (VL_GTS_IWW(128, __Vtemp_297, __Vfunc_round_shift__49__x)
                                        ? __Vtemp_299[1U]
                                        : __Vfunc_round_shift__49__x[1U]);
                                __Vfunc_round_shift__49__magnitude[2U] 
                                    = (VL_GTS_IWW(128, __Vtemp_297, __Vfunc_round_shift__49__x)
                                        ? __Vtemp_299[2U]
                                        : __Vfunc_round_shift__49__x[2U]);
                                __Vfunc_round_shift__49__magnitude[3U] 
                                    = (VL_GTS_IWW(128, __Vtemp_297, __Vfunc_round_shift__49__x)
                                        ? __Vtemp_299[3U]
                                        : __Vfunc_round_shift__49__x[3U]);
                                __Vfunc_round_shift__49__magnitude[4U] 
                                    = (VL_GTS_IWW(128, __Vtemp_297, __Vfunc_round_shift__49__x)
                                        ? (1U & __Vtemp_299[4U])
                                        : 0U);
                                __Vtemp_306[0U] = 0x8000U;
                                __Vtemp_306[1U] = 0U;
                                __Vtemp_306[2U] = 0U;
                                __Vtemp_306[3U] = 0U;
                                __Vtemp_306[4U] = 0U;
                                VL_ADD_W(5, __Vtemp_307, __Vtemp_306, __Vfunc_round_shift__49__magnitude);
                                __Vtemp_308[0U] = __Vtemp_307[0U];
                                __Vtemp_308[1U] = __Vtemp_307[1U];
                                __Vtemp_308[2U] = __Vtemp_307[2U];
                                __Vtemp_308[3U] = __Vtemp_307[3U];
                                __Vtemp_308[4U] = (1U 
                                                   & __Vtemp_307[4U]);
                                VL_SHIFTR_WWI(129,129,32, __Vtemp_309, __Vtemp_308, 0x10U);
                                __Vfunc_round_shift__49__magnitude[0U] 
                                    = __Vtemp_309[0U];
                                __Vfunc_round_shift__49__magnitude[1U] 
                                    = __Vtemp_309[1U];
                                __Vfunc_round_shift__49__magnitude[2U] 
                                    = __Vtemp_309[2U];
                                __Vfunc_round_shift__49__magnitude[3U] 
                                    = __Vtemp_309[3U];
                                __Vfunc_round_shift__49__magnitude[4U] 
                                    = (1U & __Vtemp_309[4U]);
                                __Vtemp_311[0U] = 0U;
                                __Vtemp_311[1U] = 0U;
                                __Vtemp_311[2U] = 0U;
                                __Vtemp_311[3U] = 0U;
                                VL_NEGATE_W(5, __Vtemp_312, __Vfunc_round_shift__49__magnitude);
                                __Vfunc_round_shift__49__Vfuncout[0U] 
                                    = (VL_GTS_IWW(128, __Vtemp_311, __Vfunc_round_shift__49__x)
                                        ? __Vtemp_312[0U]
                                        : __Vfunc_round_shift__49__magnitude[0U]);
                                __Vfunc_round_shift__49__Vfuncout[1U] 
                                    = (VL_GTS_IWW(128, __Vtemp_311, __Vfunc_round_shift__49__x)
                                        ? __Vtemp_312[1U]
                                        : __Vfunc_round_shift__49__magnitude[1U]);
                                __Vfunc_round_shift__49__Vfuncout[2U] 
                                    = (VL_GTS_IWW(128, __Vtemp_311, __Vfunc_round_shift__49__x)
                                        ? __Vtemp_312[2U]
                                        : __Vfunc_round_shift__49__magnitude[2U]);
                                __Vfunc_round_shift__49__Vfuncout[3U] 
                                    = (VL_GTS_IWW(128, __Vtemp_311, __Vfunc_round_shift__49__x)
                                        ? __Vtemp_312[3U]
                                        : __Vfunc_round_shift__49__magnitude[3U]);
                                __Vfunc_sat32__48__x[0U] 
                                    = __Vfunc_round_shift__49__Vfuncout[0U];
                                __Vfunc_sat32__48__x[1U] 
                                    = __Vfunc_round_shift__49__Vfuncout[1U];
                                __Vfunc_sat32__48__x[2U] 
                                    = __Vfunc_round_shift__49__Vfuncout[2U];
                                __Vfunc_sat32__48__x[3U] 
                                    = __Vfunc_round_shift__49__Vfuncout[3U];
                                __Vtemp_316[0U] = 0x7fffffffU;
                                __Vtemp_316[1U] = 0U;
                                __Vtemp_316[2U] = 0U;
                                __Vtemp_316[3U] = 0U;
                                __Vtemp_317[0U] = 0x80000000U;
                                __Vtemp_317[1U] = 0xffffffffU;
                                __Vtemp_317[2U] = 0xffffffffU;
                                __Vtemp_317[3U] = 0xffffffffU;
                                __Vfunc_sat32__48__Vfuncout 
                                    = (VL_LTS_IWW(128, __Vtemp_316, __Vfunc_sat32__48__x)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(128, __Vtemp_317, __Vfunc_sat32__48__x)
                                            ? 0x80000000U
                                            : __Vfunc_sat32__48__x[0U]));
                            }(), __Vfunc_sat32__48__Vfuncout)
                            : ([&]() {
                                __Vfunc_sat32__50__x[0U] 
                                    = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum);
                                __Vfunc_sat32__50__x[1U] 
                                    = (((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum 
                                                               >> 0x20U))))) 
                                        << 1U) | (IData)(
                                                         (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum 
                                                          >> 0x20U)));
                                __Vfunc_sat32__50__x[2U] 
                                    = (((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum 
                                                               >> 0x20U))))) 
                                        >> 0x1fU) | 
                                       ((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum 
                                                               >> 0x20U))))) 
                                        << 1U));
                                __Vfunc_sat32__50__x[3U] 
                                    = (((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum 
                                                               >> 0x20U))))) 
                                        >> 0x1fU) | 
                                       ((- (IData)(
                                                   (1U 
                                                    & (IData)(
                                                              (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum 
                                                               >> 0x20U))))) 
                                        << 1U));
                                __Vtemp_321[0U] = 0x7fffffffU;
                                __Vtemp_321[1U] = 0U;
                                __Vtemp_321[2U] = 0U;
                                __Vtemp_321[3U] = 0U;
                                __Vtemp_322[0U] = 0x80000000U;
                                __Vtemp_322[1U] = 0xffffffffU;
                                __Vtemp_322[2U] = 0xffffffffU;
                                __Vtemp_322[3U] = 0xffffffffU;
                                __Vfunc_sat32__50__Vfuncout 
                                    = (VL_LTS_IWW(128, __Vtemp_321, __Vfunc_sat32__50__x)
                                        ? 0x7fffffffU
                                        : (VL_GTS_IWW(128, __Vtemp_322, __Vfunc_sat32__50__x)
                                            ? 0x80000000U
                                            : __Vfunc_sat32__50__x[0U]));
                            }(), __Vfunc_sat32__50__Vfuncout));
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xbU;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__product_value 
                        = ((IData)(vlSelf->bench__DOT__rst_n)
                            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__result
                            : 0ULL);
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xaU;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_valid) {
                        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed) 
                             & (IData)(vlSelf->bench__DOT__rst_n))) {
                            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__failed = 1U;
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xdU;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value 
                                = ((IData)(vlSelf->bench__DOT__rst_n)
                                    ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result
                                    : 0U);
                            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 8U;
                        }
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_ready) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum 
                    = (0x1ffffffffULL & ((((QData)((IData)(
                                                           (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a 
                                                            >> 0x1fU))) 
                                           << 0x20U) 
                                          | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a))) 
                                         + (((QData)((IData)(
                                                             (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b 
                                                              >> 0x1fU))) 
                                             << 0x20U) 
                                            | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b)))));
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xaU;
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__read_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state 
                    = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode))
                        ? 6U : 5U);
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue) {
                    __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__complete) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a 
                    = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__read_data;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__issue) {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 2U;
            }
        } else if ((((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0) 
                     & (5U == vlSelf->bench__DOT__dut__DOT__decoder__DOT__selected)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vcellout__residual____pinNumber4))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__index = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__failed = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__element_mode;
            if ((((2U < (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__element_mode)) 
                  | (1U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__layer)) 
                 | (4U <= vlSelf->bench__DOT__dut__DOT__decoder__DOT__position))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__failed = 1U;
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0xeU;
            } else {
                __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 1U;
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__index = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__mode = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__failed = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__output_value = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__sum = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__product_value = 0ULL;
    }
    __Vtemp_323[0U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[0U];
    __Vtemp_323[1U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[1U];
    __Vtemp_323[2U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[2U];
    __Vtemp_323[3U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[3U];
    __Vtemp_323[4U] = vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__divisor[4U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(5, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_323);
    __Vtemp_325[0U] = (1U | ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
                             << 2U));
    __Vtemp_325[1U] = (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work) 
                        >> 0x1eU) | ((IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                                              >> 0x20U)) 
                                     << 2U));
    __Vtemp_325[2U] = ((IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__root_work 
                                >> 0x20U)) >> 0x1eU);
    __Vtemp_325[3U] = 0U;
    __Vtemp_325[4U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__subtract 
        = VL_GTE_W(5, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__root_unit__DOT__shifted_remainder, __Vtemp_325);
    __Vtemp_326[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_326[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_326[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_326);
    __Vtemp_327[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_327[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_327[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_327);
    __Vtemp_328[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_328[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_328[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_328);
    __Vtemp_329[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_329[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_329[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_329);
    __Vtemp_330[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor);
    __Vtemp_330[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__divisor 
                               >> 0x20U));
    __Vtemp_330[2U] = 0U;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(3, vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_330);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
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
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__weight_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qw 
                   >> (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__zero_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__qz 
                   >> (IData)(bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__head_base;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__pair_index;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__rope__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__group_offset;
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v0) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][3U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v1) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[6U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[7U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][3U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v8;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v9) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[0U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v10) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[6U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[7U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8][0U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8][1U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8][2U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8][3U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v8[3U];
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9][0U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9[0U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9][1U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9[1U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9][2U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9[2U];
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[__Vdlyvdim0__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9][3U] 
            = __Vdlyvval__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators__v9[3U];
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v9) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][3U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v10) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][3U] = 0U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales__v17) {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[6U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__scales[7U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[0U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[1U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[2U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[3U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[4U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[5U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[6U][3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__accumulators[7U][3U] = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__state;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dim;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__group_head;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__context_pass;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[0U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__max_score[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__denominator;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[0U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__dot[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[0U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[0U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[1U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U] 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__weighted[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__time_index;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__head_base;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__kv_base;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__state;
    if (vlSelf->bench__DOT__rst_n) {
        if (vlSelf->bench__DOT__dut__DOT__fault) {
            vlSelf->bench__DOT__dut__DOT__failed = 1U;
            __Vdly__bench__DOT__dut__DOT__sequence_valid = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x16U;
        } else if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__failed = 1U;
                __Vdly__bench__DOT__dut__DOT__sequence_valid = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x16U;
            } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                        vlSelf->bench__DOT__dut__DOT__activation 
                            = vlSelf->bench__DOT__dut__DOT__head_activation_q;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xcU;
                    } else {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0U;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x16U;
                } else if (((IData)(vlSelf->bench__DOT__logit_valid) 
                            & (IData)(vlSelf->bench__DOT__logit_ready))) {
                    if ((0x11U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__vocabulary))) {
                        vlSelf->bench__DOT__dut__DOT__vocabulary 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__vocabulary);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__component = 0U;
                        __Vdly__bench__DOT__dut__DOT__logit_sum[0U] = 0U;
                        __Vdly__bench__DOT__dut__DOT__logit_sum[1U] = 0U;
                        __Vdly__bench__DOT__dut__DOT__logit_sum[2U] = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xaU;
                    } else {
                        __Vdly__bench__DOT__dut__DOT__next_position 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__position);
                        __Vdly__bench__DOT__dut__DOT__sequence_valid = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x16U;
                    }
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    __Vfunc_round_shift__13__x[0U] 
                        = vlSelf->bench__DOT__dut__DOT__logit_sum[0U];
                    __Vfunc_round_shift__13__x[1U] 
                        = vlSelf->bench__DOT__dut__DOT__logit_sum[1U];
                    __Vfunc_round_shift__13__x[2U] 
                        = vlSelf->bench__DOT__dut__DOT__logit_sum[2U];
                    __Vfunc_round_shift__13__x[3U] 
                        = (- (IData)((vlSelf->bench__DOT__dut__DOT__logit_sum[2U] 
                                      >> 0x1fU)));
                    __Vtemp_357[0U] = 0U;
                    __Vtemp_357[1U] = 0U;
                    __Vtemp_357[2U] = 0U;
                    __Vtemp_357[3U] = 0U;
                    __Vtemp_358[0U] = __Vfunc_round_shift__13__x[0U];
                    __Vtemp_358[1U] = __Vfunc_round_shift__13__x[1U];
                    __Vtemp_358[2U] = __Vfunc_round_shift__13__x[2U];
                    __Vtemp_358[3U] = __Vfunc_round_shift__13__x[3U];
                    __Vtemp_358[4U] = (__Vfunc_round_shift__13__x[3U] 
                                       >> 0x1fU);
                    VL_NEGATE_W(5, __Vtemp_359, __Vtemp_358);
                    if (VL_GTS_IWW(128, __Vtemp_357, __Vfunc_round_shift__13__x)) {
                        __Vfunc_round_shift__13__magnitude[0U] 
                            = __Vtemp_359[0U];
                        __Vfunc_round_shift__13__magnitude[1U] 
                            = __Vtemp_359[1U];
                        __Vfunc_round_shift__13__magnitude[2U] 
                            = __Vtemp_359[2U];
                        __Vfunc_round_shift__13__magnitude[3U] 
                            = __Vtemp_359[3U];
                        __Vfunc_round_shift__13__magnitude[4U] 
                            = (1U & __Vtemp_359[4U]);
                    } else {
                        __Vfunc_round_shift__13__magnitude[0U] 
                            = __Vfunc_round_shift__13__x[0U];
                        __Vfunc_round_shift__13__magnitude[1U] 
                            = __Vfunc_round_shift__13__x[1U];
                        __Vfunc_round_shift__13__magnitude[2U] 
                            = __Vfunc_round_shift__13__x[2U];
                        __Vfunc_round_shift__13__magnitude[3U] 
                            = __Vfunc_round_shift__13__x[3U];
                        __Vfunc_round_shift__13__magnitude[4U] = 0U;
                    }
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x14U;
                    __Vtemp_366[0U] = 0x8000U;
                    __Vtemp_366[1U] = 0U;
                    __Vtemp_366[2U] = 0U;
                    __Vtemp_366[3U] = 0U;
                    __Vtemp_366[4U] = 0U;
                    VL_ADD_W(5, __Vtemp_367, __Vtemp_366, __Vfunc_round_shift__13__magnitude);
                    __Vtemp_368[0U] = __Vtemp_367[0U];
                    __Vtemp_368[1U] = __Vtemp_367[1U];
                    __Vtemp_368[2U] = __Vtemp_367[2U];
                    __Vtemp_368[3U] = __Vtemp_367[3U];
                    __Vtemp_368[4U] = (1U & __Vtemp_367[4U]);
                    VL_SHIFTR_WWI(129,129,32, __Vtemp_369, __Vtemp_368, 0x10U);
                    __Vfunc_round_shift__13__magnitude[0U] 
                        = __Vtemp_369[0U];
                    __Vfunc_round_shift__13__magnitude[1U] 
                        = __Vtemp_369[1U];
                    __Vfunc_round_shift__13__magnitude[2U] 
                        = __Vtemp_369[2U];
                    __Vfunc_round_shift__13__magnitude[3U] 
                        = __Vtemp_369[3U];
                    __Vfunc_round_shift__13__magnitude[4U] 
                        = (1U & __Vtemp_369[4U]);
                    __Vtemp_371[0U] = 0U;
                    __Vtemp_371[1U] = 0U;
                    __Vtemp_371[2U] = 0U;
                    __Vtemp_371[3U] = 0U;
                    VL_NEGATE_W(5, __Vtemp_372, __Vfunc_round_shift__13__magnitude);
                    if (VL_GTS_IWW(128, __Vtemp_371, __Vfunc_round_shift__13__x)) {
                        __Vfunc_round_shift__13__Vfuncout[0U] 
                            = __Vtemp_372[0U];
                        __Vfunc_round_shift__13__Vfuncout[1U] 
                            = __Vtemp_372[1U];
                        __Vfunc_round_shift__13__Vfuncout[2U] 
                            = __Vtemp_372[2U];
                        __Vfunc_round_shift__13__Vfuncout[3U] 
                            = __Vtemp_372[3U];
                    } else {
                        __Vfunc_round_shift__13__Vfuncout[0U] 
                            = __Vfunc_round_shift__13__magnitude[0U];
                        __Vfunc_round_shift__13__Vfuncout[1U] 
                            = __Vfunc_round_shift__13__magnitude[1U];
                        __Vfunc_round_shift__13__Vfuncout[2U] 
                            = __Vfunc_round_shift__13__magnitude[2U];
                        __Vfunc_round_shift__13__Vfuncout[3U] 
                            = __Vfunc_round_shift__13__magnitude[3U];
                    }
                    __Vfunc_sat32__12__x[0U] = __Vfunc_round_shift__13__Vfuncout[0U];
                    __Vfunc_sat32__12__x[1U] = __Vfunc_round_shift__13__Vfuncout[1U];
                    __Vfunc_sat32__12__x[2U] = __Vfunc_round_shift__13__Vfuncout[2U];
                    __Vfunc_sat32__12__x[3U] = __Vfunc_round_shift__13__Vfuncout[3U];
                    __Vtemp_376[0U] = 0x7fffffffU;
                    __Vtemp_376[1U] = 0U;
                    __Vtemp_376[2U] = 0U;
                    __Vtemp_376[3U] = 0U;
                    __Vtemp_377[0U] = 0x80000000U;
                    __Vtemp_377[1U] = 0xffffffffU;
                    __Vtemp_377[2U] = 0xffffffffU;
                    __Vtemp_377[3U] = 0xffffffffU;
                    __Vfunc_sat32__12__Vfuncout = (
                                                   VL_LTS_IWW(128, __Vtemp_376, __Vfunc_sat32__12__x)
                                                    ? 0x7fffffffU
                                                    : 
                                                   (VL_GTS_IWW(128, __Vtemp_377, __Vfunc_sat32__12__x)
                                                     ? 0x80000000U
                                                     : 
                                                    __Vfunc_sat32__12__x[0U]));
                    vlSelf->bench__DOT__dut__DOT__result 
                        = __Vfunc_sat32__12__Vfuncout;
                } else if ((8U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__component))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__component 
                        = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__component);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xaU;
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x13U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                __Vtemp_378[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__logit_product);
                __Vtemp_378[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__logit_product 
                                           >> 0x20U));
                __Vtemp_378[2U] = (- (IData)((1U & (IData)(
                                                           (vlSelf->bench__DOT__dut__DOT__logit_product 
                                                            >> 0x3fU)))));
                VL_ADD_W(3, __Vdly__bench__DOT__dut__DOT__logit_sum, vlSelf->bench__DOT__dut__DOT__logit_sum, __Vtemp_378);
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x12U;
            } else if (vlSelf->bench__DOT__dut__DOT__multiply_valid) {
                vlSelf->bench__DOT__dut__DOT__logit_product 
                    = ((IData)(vlSelf->bench__DOT__rst_n)
                        ? vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__result
                        : 0ULL);
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x11U;
            }
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                        if (vlSelf->bench__DOT__dut__DOT__multiply_ready) {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x10U;
                        }
                    } else {
                        __Vfunc_f16_q16__14__h = vlSelf->bench__DOT__dut__DOT__tensor_f16;
                        __Vfunc_f16_scale__15__h = __Vfunc_f16_q16__14__h;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xfU;
                        if ((0U == (0x1fU & ((IData)(__Vfunc_f16_scale__15__h) 
                                             >> 0xaU)))) {
                            __Vfunc_f16_scale__15__magnitude 
                                = (0x3ffU & (IData)(__Vfunc_f16_scale__15__h));
                            __Vfunc_f16_scale__15__shift = 0xfffffff8U;
                        } else {
                            __Vfunc_f16_scale__15__magnitude 
                                = (0x400U | (0x3ffU 
                                             & (IData)(__Vfunc_f16_scale__15__h)));
                            __Vfunc_f16_scale__15__shift 
                                = ((0x1fU & ((IData)(__Vfunc_f16_scale__15__h) 
                                             >> 0xaU)) 
                                   - (IData)(9U));
                        }
                        __Vfunc_f16_scale__15__magnitude 
                            = (VL_LTES_III(32, 0U, __Vfunc_f16_scale__15__shift)
                                ? VL_SHIFTL_III(32,32,32, __Vfunc_f16_scale__15__magnitude, __Vfunc_f16_scale__15__shift)
                                : VL_SHIFTR_III(32,32,32, 
                                                (__Vfunc_f16_scale__15__magnitude 
                                                 + 
                                                 VL_SHIFTL_III(32,32,32, (IData)(1U), 
                                                               ((- __Vfunc_f16_scale__15__shift) 
                                                                - (IData)(1U)))), 
                                                (- __Vfunc_f16_scale__15__shift)));
                        __Vfunc_f16_scale__15__Vfuncout 
                            = __Vfunc_f16_scale__15__magnitude;
                        __Vfunc_f16_q16__14__magnitude 
                            = __Vfunc_f16_scale__15__Vfuncout;
                        __Vfunc_f16_q16__14__signed_value 
                            = (0x1ffffffffULL & ((0x8000U 
                                                  & (IData)(__Vfunc_f16_q16__14__h))
                                                  ? 
                                                 (- (QData)((IData)(__Vfunc_f16_q16__14__magnitude)))
                                                  : (QData)((IData)(__Vfunc_f16_q16__14__magnitude))));
                        __Vfunc_sat32__16__x[0U] = (IData)(__Vfunc_f16_q16__14__signed_value);
                        __Vfunc_sat32__16__x[1U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__14__signed_value 
                                                        >> 0x20U))))) 
                              << 1U) | (IData)((__Vfunc_f16_q16__14__signed_value 
                                                >> 0x20U)));
                        __Vfunc_sat32__16__x[2U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__14__signed_value 
                                                        >> 0x20U))))) 
                              >> 0x1fU) | ((- (IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (__Vfunc_f16_q16__14__signed_value 
                                                                  >> 0x20U))))) 
                                           << 1U));
                        __Vfunc_sat32__16__x[3U] = 
                            (((- (IData)((1U & (IData)(
                                                       (__Vfunc_f16_q16__14__signed_value 
                                                        >> 0x20U))))) 
                              >> 0x1fU) | ((- (IData)(
                                                      (1U 
                                                       & (IData)(
                                                                 (__Vfunc_f16_q16__14__signed_value 
                                                                  >> 0x20U))))) 
                                           << 1U));
                        __Vtemp_383[0U] = 0x7fffffffU;
                        __Vtemp_383[1U] = 0U;
                        __Vtemp_383[2U] = 0U;
                        __Vtemp_383[3U] = 0U;
                        __Vtemp_384[0U] = 0x80000000U;
                        __Vtemp_384[1U] = 0xffffffffU;
                        __Vtemp_384[2U] = 0xffffffffU;
                        __Vtemp_384[3U] = 0xffffffffU;
                        __Vfunc_sat32__16__Vfuncout 
                            = (VL_LTS_IWW(128, __Vtemp_383, __Vfunc_sat32__16__x)
                                ? 0x7fffffffU : (VL_GTS_IWW(128, __Vtemp_384, __Vfunc_sat32__16__x)
                                                  ? 0x80000000U
                                                  : 
                                                 __Vfunc_sat32__16__x[0U]));
                        __Vfunc_f16_q16__14__Vfuncout 
                            = __Vfunc_sat32__16__Vfuncout;
                        vlSelf->bench__DOT__dut__DOT__weight_value 
                            = __Vfunc_f16_q16__14__Vfuncout;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__complete) {
                        if (([&]() {
                                    __Vfunc_f16_invalid__17__h 
                                        = (0xffffU 
                                           & vlSelf->bench__DOT__dut__DOT__read_data);
                                    __Vfunc_f16_invalid__17__Vfuncout 
                                        = (0x1fU == 
                                           (0x1fU & 
                                            ((IData)(__Vfunc_f16_invalid__17__h) 
                                             >> 0xaU)));
                                }(), (IData)(__Vfunc_f16_invalid__17__Vfuncout))) {
                            vlSelf->bench__DOT__dut__DOT__failed = 1U;
                            __Vdly__bench__DOT__dut__DOT__sequence_valid = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x16U;
                        } else {
                            __Vdly__bench__DOT__dut__DOT__tensor_f16 
                                = (0xffffU & vlSelf->bench__DOT__dut__DOT__read_data);
                            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xeU;
                        }
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__issue) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xdU;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__complete) {
                        vlSelf->bench__DOT__dut__DOT__activation 
                            = vlSelf->bench__DOT__dut__DOT__read_data;
                        if ((7U == vlSelf->bench__DOT__dut__DOT__component)) {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 1U;
                        }
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xcU;
                    }
                } else if (vlSelf->bench__DOT__dut__DOT__activation_reuse_valid) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x17U;
                } else if (vlSelf->bench__DOT__dut__DOT__issue) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xbU;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__finished))) {
                    if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__faults))) {
                        vlSelf->bench__DOT__dut__DOT__failed = 1U;
                        __Vdly__bench__DOT__dut__DOT__sequence_valid = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x16U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__vocabulary = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__component = 0U;
                        __Vdly__bench__DOT__dut__DOT__logit_sum[0U] = 0U;
                        __Vdly__bench__DOT__dut__DOT__logit_sum[1U] = 0U;
                        __Vdly__bench__DOT__dut__DOT__logit_sum[2U] = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xaU;
                    }
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__ready))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__finished))) {
                        if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__faults))) {
                            vlSelf->bench__DOT__dut__DOT__failed = 1U;
                            __Vdly__bench__DOT__dut__DOT__sequence_valid = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x16U;
                        } else if ((1U > ((IData)(1U) 
                                          + vlSelf->bench__DOT__dut__DOT__layer))) {
                            vlSelf->bench__DOT__dut__DOT__layer 
                                = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__layer);
                            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 6U;
                        } else {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 8U;
                        }
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__ready))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__complete) {
                    if ((8U > ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__component))) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__component 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__component);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 1U;
                    } else {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 6U;
                    }
                }
            } else if (vlSelf->bench__DOT__dut__DOT__issue) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                __Vfunc_f16_q16__18__h = vlSelf->bench__DOT__dut__DOT__tensor_f16;
                __Vfunc_f16_scale__19__h = __Vfunc_f16_q16__18__h;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 4U;
                if ((0U == (0x1fU & ((IData)(__Vfunc_f16_scale__19__h) 
                                     >> 0xaU)))) {
                    __Vfunc_f16_scale__19__magnitude 
                        = (0x3ffU & (IData)(__Vfunc_f16_scale__19__h));
                    __Vfunc_f16_scale__19__shift = 0xfffffff8U;
                } else {
                    __Vfunc_f16_scale__19__magnitude 
                        = (0x400U | (0x3ffU & (IData)(__Vfunc_f16_scale__19__h)));
                    __Vfunc_f16_scale__19__shift = 
                        ((0x1fU & ((IData)(__Vfunc_f16_scale__19__h) 
                                   >> 0xaU)) - (IData)(9U));
                }
                __Vfunc_f16_scale__19__magnitude = 
                    (VL_LTES_III(32, 0U, __Vfunc_f16_scale__19__shift)
                      ? VL_SHIFTL_III(32,32,32, __Vfunc_f16_scale__19__magnitude, __Vfunc_f16_scale__19__shift)
                      : VL_SHIFTR_III(32,32,32, (__Vfunc_f16_scale__19__magnitude 
                                                 + 
                                                 VL_SHIFTL_III(32,32,32, (IData)(1U), 
                                                               ((- __Vfunc_f16_scale__19__shift) 
                                                                - (IData)(1U)))), 
                                      (- __Vfunc_f16_scale__19__shift)));
                __Vfunc_f16_scale__19__Vfuncout = __Vfunc_f16_scale__19__magnitude;
                __Vfunc_f16_q16__18__magnitude = __Vfunc_f16_scale__19__Vfuncout;
                __Vfunc_f16_q16__18__signed_value = 
                    (0x1ffffffffULL & ((0x8000U & (IData)(__Vfunc_f16_q16__18__h))
                                        ? (- (QData)((IData)(__Vfunc_f16_q16__18__magnitude)))
                                        : (QData)((IData)(__Vfunc_f16_q16__18__magnitude))));
                __Vfunc_sat32__20__x[0U] = (IData)(__Vfunc_f16_q16__18__signed_value);
                __Vfunc_sat32__20__x[1U] = (((- (IData)(
                                                        (1U 
                                                         & (IData)(
                                                                   (__Vfunc_f16_q16__18__signed_value 
                                                                    >> 0x20U))))) 
                                             << 1U) 
                                            | (IData)(
                                                      (__Vfunc_f16_q16__18__signed_value 
                                                       >> 0x20U)));
                __Vfunc_sat32__20__x[2U] = (((- (IData)(
                                                        (1U 
                                                         & (IData)(
                                                                   (__Vfunc_f16_q16__18__signed_value 
                                                                    >> 0x20U))))) 
                                             >> 0x1fU) 
                                            | ((- (IData)(
                                                          (1U 
                                                           & (IData)(
                                                                     (__Vfunc_f16_q16__18__signed_value 
                                                                      >> 0x20U))))) 
                                               << 1U));
                __Vfunc_sat32__20__x[3U] = (((- (IData)(
                                                        (1U 
                                                         & (IData)(
                                                                   (__Vfunc_f16_q16__18__signed_value 
                                                                    >> 0x20U))))) 
                                             >> 0x1fU) 
                                            | ((- (IData)(
                                                          (1U 
                                                           & (IData)(
                                                                     (__Vfunc_f16_q16__18__signed_value 
                                                                      >> 0x20U))))) 
                                               << 1U));
                __Vtemp_390[0U] = 0x7fffffffU;
                __Vtemp_390[1U] = 0U;
                __Vtemp_390[2U] = 0U;
                __Vtemp_390[3U] = 0U;
                __Vtemp_391[0U] = 0x80000000U;
                __Vtemp_391[1U] = 0xffffffffU;
                __Vtemp_391[2U] = 0xffffffffU;
                __Vtemp_391[3U] = 0xffffffffU;
                __Vfunc_sat32__20__Vfuncout = (VL_LTS_IWW(128, __Vtemp_390, __Vfunc_sat32__20__x)
                                                ? 0x7fffffffU
                                                : (
                                                   VL_GTS_IWW(128, __Vtemp_391, __Vfunc_sat32__20__x)
                                                    ? 0x80000000U
                                                    : 
                                                   __Vfunc_sat32__20__x[0U]));
                __Vfunc_f16_q16__18__Vfuncout = __Vfunc_sat32__20__Vfuncout;
                vlSelf->bench__DOT__dut__DOT__activation 
                    = __Vfunc_f16_q16__18__Vfuncout;
            } else if (vlSelf->bench__DOT__dut__DOT__complete) {
                if (([&]() {
                            __Vfunc_f16_invalid__21__h 
                                = (0xffffU & vlSelf->bench__DOT__dut__DOT__read_data);
                            __Vfunc_f16_invalid__21__Vfuncout 
                                = (0x1fU == (0x1fU 
                                             & ((IData)(__Vfunc_f16_invalid__21__h) 
                                                >> 0xaU)));
                        }(), (IData)(__Vfunc_f16_invalid__21__Vfuncout))) {
                    vlSelf->bench__DOT__dut__DOT__failed = 1U;
                    __Vdly__bench__DOT__dut__DOT__sequence_valid = 0U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x16U;
                } else {
                    __Vdly__bench__DOT__dut__DOT__tensor_f16 
                        = (0xffffU & vlSelf->bench__DOT__dut__DOT__read_data);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 3U;
                }
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__issue) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 2U;
            }
        } else if (((IData)(vlSelf->bench__DOT__token_valid) 
                    & (IData)(vlSelf->bench__DOT__token_ready))) {
            vlSelf->bench__DOT__dut__DOT__failed = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
            if ((1U & ((((0x11U <= vlSelf->bench__DOT__token_id) 
                         | (4U <= vlSelf->bench__DOT__token_pos)) 
                        | ((IData)(vlSelf->bench__DOT__new_sequence) 
                           & (0U != vlSelf->bench__DOT__token_pos))) 
                       | ((~ (IData)(vlSelf->bench__DOT__new_sequence)) 
                          & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__sequence_valid)) 
                             | (vlSelf->bench__DOT__token_pos 
                                != vlSelf->bench__DOT__dut__DOT__next_position)))))) {
                vlSelf->bench__DOT__dut__DOT__failed = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0x15U;
            } else {
                vlSelf->bench__DOT__dut__DOT__vocabulary = 0U;
                vlSelf->bench__DOT__dut__DOT__layer = 0U;
                vlSelf->bench__DOT__dut__DOT__token 
                    = vlSelf->bench__DOT__token_id;
                vlSelf->__Vdly__bench__DOT__dut__DOT__position 
                    = vlSelf->bench__DOT__token_pos;
                vlSelf->__Vdly__bench__DOT__dut__DOT__component = 0U;
                __Vdly__bench__DOT__dut__DOT__logit_sum[0U] = 0U;
                __Vdly__bench__DOT__dut__DOT__logit_sum[1U] = 0U;
                __Vdly__bench__DOT__dut__DOT__logit_sum[2U] = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 1U;
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__vocabulary = 0U;
        vlSelf->bench__DOT__dut__DOT__layer = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__failed = 0U;
        __Vdly__bench__DOT__dut__DOT__sequence_valid = 1U;
        vlSelf->bench__DOT__dut__DOT__token = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__position = 0U;
        __Vdly__bench__DOT__dut__DOT__next_position = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__component = 0U;
        __Vdly__bench__DOT__dut__DOT__tensor_f16 = 0U;
        vlSelf->bench__DOT__dut__DOT__activation = 0U;
        vlSelf->bench__DOT__dut__DOT__weight_value = 0U;
        vlSelf->bench__DOT__dut__DOT__result = 0U;
        vlSelf->bench__DOT__dut__DOT__logit_product = 0ULL;
        __Vdly__bench__DOT__dut__DOT__logit_sum[0U] = 0U;
        __Vdly__bench__DOT__dut__DOT__logit_sum[1U] = 0U;
        __Vdly__bench__DOT__dut__DOT__logit_sum[2U] = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__activation_reuse_valid = 0U;
    }
    if (vlSelf->bench__DOT__rst_n) {
        if (((8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiply_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__negative 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value 
                    ^ vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b) 
                   >> 0x1fU);
        }
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
            = (0xfU & VL_SHIFTL_III(4,4,32, (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe), 1U));
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__result 
                = ((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__negative)
                    ? (- vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree
                       [2U][0U]) : vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree
                   [2U][0U]);
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result = 1U;
        }
        if (((8U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_ready))) {
            __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
                = (1U | (IData)(__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__negative 
                = ((vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value 
                    ^ vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b) 
                   >> 0x1fU);
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiply_valid) 
             & (9U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state)))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result = 0U;
        }
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 8U;
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 8U;
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = 1U;
                vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 8U;
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_valid) 
                        & (7U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state)))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 0U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
                    __Vfunc_round_shift__52__x[0U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[0U];
                    __Vfunc_round_shift__52__x[1U] 
                        = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[1U];
                    __Vfunc_round_shift__52__x[2U] 
                        = (((IData)((0x7fffffffffffffffULL 
                                     & (- (QData)((IData)(
                                                          (1U 
                                                           & vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[2U])))))) 
                            << 1U) | vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[2U]);
                    __Vfunc_round_shift__52__x[3U] 
                        = (((IData)((0x7fffffffffffffffULL 
                                     & (- (QData)((IData)(
                                                          (1U 
                                                           & vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[2U])))))) 
                            >> 0x1fU) | ((IData)(((0x7fffffffffffffffULL 
                                                   & (- (QData)((IData)(
                                                                        (1U 
                                                                         & vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[2U]))))) 
                                                  >> 0x20U)) 
                                         << 1U));
                    __Vtemp_393[0U] = 0U;
                    __Vtemp_393[1U] = 0U;
                    __Vtemp_393[2U] = 0U;
                    __Vtemp_393[3U] = 0U;
                    __Vtemp_394[0U] = __Vfunc_round_shift__52__x[0U];
                    __Vtemp_394[1U] = __Vfunc_round_shift__52__x[1U];
                    __Vtemp_394[2U] = __Vfunc_round_shift__52__x[2U];
                    __Vtemp_394[3U] = __Vfunc_round_shift__52__x[3U];
                    __Vtemp_394[4U] = (__Vfunc_round_shift__52__x[3U] 
                                       >> 0x1fU);
                    VL_NEGATE_W(5, __Vtemp_395, __Vtemp_394);
                    if (VL_GTS_IWW(128, __Vtemp_393, __Vfunc_round_shift__52__x)) {
                        __Vfunc_round_shift__52__magnitude[0U] 
                            = __Vtemp_395[0U];
                        __Vfunc_round_shift__52__magnitude[1U] 
                            = __Vtemp_395[1U];
                        __Vfunc_round_shift__52__magnitude[2U] 
                            = __Vtemp_395[2U];
                        __Vfunc_round_shift__52__magnitude[3U] 
                            = __Vtemp_395[3U];
                        __Vfunc_round_shift__52__magnitude[4U] 
                            = (1U & __Vtemp_395[4U]);
                    } else {
                        __Vfunc_round_shift__52__magnitude[0U] 
                            = __Vfunc_round_shift__52__x[0U];
                        __Vfunc_round_shift__52__magnitude[1U] 
                            = __Vfunc_round_shift__52__x[1U];
                        __Vfunc_round_shift__52__magnitude[2U] 
                            = __Vfunc_round_shift__52__x[2U];
                        __Vfunc_round_shift__52__magnitude[3U] 
                            = __Vfunc_round_shift__52__x[3U];
                        __Vfunc_round_shift__52__magnitude[4U] = 0U;
                    }
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 8U;
                    __Vtemp_402[0U] = 0x800000U;
                    __Vtemp_402[1U] = 0U;
                    __Vtemp_402[2U] = 0U;
                    __Vtemp_402[3U] = 0U;
                    __Vtemp_402[4U] = 0U;
                    VL_ADD_W(5, __Vtemp_403, __Vtemp_402, __Vfunc_round_shift__52__magnitude);
                    __Vtemp_404[0U] = __Vtemp_403[0U];
                    __Vtemp_404[1U] = __Vtemp_403[1U];
                    __Vtemp_404[2U] = __Vtemp_403[2U];
                    __Vtemp_404[3U] = __Vtemp_403[3U];
                    __Vtemp_404[4U] = (1U & __Vtemp_403[4U]);
                    VL_SHIFTR_WWI(129,129,32, __Vtemp_405, __Vtemp_404, 0x18U);
                    __Vfunc_round_shift__52__magnitude[0U] 
                        = __Vtemp_405[0U];
                    __Vfunc_round_shift__52__magnitude[1U] 
                        = __Vtemp_405[1U];
                    __Vfunc_round_shift__52__magnitude[2U] 
                        = __Vtemp_405[2U];
                    __Vfunc_round_shift__52__magnitude[3U] 
                        = __Vtemp_405[3U];
                    __Vfunc_round_shift__52__magnitude[4U] 
                        = (1U & __Vtemp_405[4U]);
                    __Vtemp_407[0U] = 0U;
                    __Vtemp_407[1U] = 0U;
                    __Vtemp_407[2U] = 0U;
                    __Vtemp_407[3U] = 0U;
                    VL_NEGATE_W(5, __Vtemp_408, __Vfunc_round_shift__52__magnitude);
                    if (VL_GTS_IWW(128, __Vtemp_407, __Vfunc_round_shift__52__x)) {
                        __Vfunc_round_shift__52__Vfuncout[0U] 
                            = __Vtemp_408[0U];
                        __Vfunc_round_shift__52__Vfuncout[1U] 
                            = __Vtemp_408[1U];
                        __Vfunc_round_shift__52__Vfuncout[2U] 
                            = __Vtemp_408[2U];
                        __Vfunc_round_shift__52__Vfuncout[3U] 
                            = __Vtemp_408[3U];
                    } else {
                        __Vfunc_round_shift__52__Vfuncout[0U] 
                            = __Vfunc_round_shift__52__magnitude[0U];
                        __Vfunc_round_shift__52__Vfuncout[1U] 
                            = __Vfunc_round_shift__52__magnitude[1U];
                        __Vfunc_round_shift__52__Vfuncout[2U] 
                            = __Vfunc_round_shift__52__magnitude[2U];
                        __Vfunc_round_shift__52__Vfuncout[3U] 
                            = __Vfunc_round_shift__52__magnitude[3U];
                    }
                    __Vfunc_sat32__51__x[0U] = __Vfunc_round_shift__52__Vfuncout[0U];
                    __Vfunc_sat32__51__x[1U] = __Vfunc_round_shift__52__Vfuncout[1U];
                    __Vfunc_sat32__51__x[2U] = __Vfunc_round_shift__52__Vfuncout[2U];
                    __Vfunc_sat32__51__x[3U] = __Vfunc_round_shift__52__Vfuncout[3U];
                    __Vtemp_412[0U] = 0x7fffffffU;
                    __Vtemp_412[1U] = 0U;
                    __Vtemp_412[2U] = 0U;
                    __Vtemp_412[3U] = 0U;
                    __Vtemp_413[0U] = 0x80000000U;
                    __Vtemp_413[1U] = 0xffffffffU;
                    __Vtemp_413[2U] = 0xffffffffU;
                    __Vtemp_413[3U] = 0xffffffffU;
                    __Vfunc_sat32__51__Vfuncout = (
                                                   VL_LTS_IWW(128, __Vtemp_412, __Vfunc_sat32__51__x)
                                                    ? 0x7fffffffU
                                                    : 
                                                   (VL_GTS_IWW(128, __Vtemp_413, __Vfunc_sat32__51__x)
                                                     ? 0x80000000U
                                                     : 
                                                    __Vfunc_sat32__51__x[0U]));
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result 
                        = __Vfunc_sat32__51__Vfuncout;
                } else if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier.out_valid) {
                    if (vlSelf->bench__DOT__rst_n) {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[0U] 
                            = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier.__PVT__multiplier__DOT__result[0U];
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[1U] 
                            = vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier.__PVT__multiplier__DOT__result[1U];
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[2U] 
                            = (1U & vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier.__PVT__multiplier__DOT__result[2U]);
                    } else {
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[0U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[1U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[2U] = 0U;
                    }
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
                if (vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier.in_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 6U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_valid) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 8U;
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid 
                        = ((IData)(vlSelf->bench__DOT__rst_n)
                            ? vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result
                            : 0ULL);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 5U;
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider_ready) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 4U;
                }
            } else if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_valid) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__failed) 
                     & (IData)(vlSelf->bench__DOT__rst_n))) {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 8U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__numerator 
                        = (VL_LTES_III(32, 0U, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand)
                            ? 0x1000000000000ULL : 
                           ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential)) 
                            << 0x18U));
                    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__denominator 
                        = (0x1000000ULL + (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exponential)));
                    vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 3U;
                }
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_ready) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 2U;
            }
        } else if (((6U == (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_ready))) {
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand 
                = vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a;
            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude 
                = (VL_GTS_III(32, 0U, vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a)
                    ? (- (((QData)((IData)((- (IData)(
                                                      (vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a 
                                                       >> 0x1fU))))) 
                           << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a))))
                    : (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a)));
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result = 0U;
            vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 1U;
        }
        __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe 
            = (0xfU & VL_SHIFTL_III(4,4,32, (IData)(vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe), 1U));
        if (((0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__multiply_ready))) {
            __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe 
                = (1U | (IData)(__Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe));
        }
        if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe))) {
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__result 
                = ((IData)(vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative)
                    ? (- vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree
                       [2U][0U]) : vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree
                   [2U][0U]);
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_result = 1U;
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__multiply_valid) 
             & (0x10U == (IData)(vlSelf->bench__DOT__dut__DOT__state)))) {
            vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_result = 0U;
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__negative = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_result = 0U;
        __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__result = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__operand = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__result = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__magnitude = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__numerator = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__denominator = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__sigmoid = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__truncated_product[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__failed = 0U;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_result = 0U;
        __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe = 0U;
        vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__result = 0ULL;
        vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__negative = 0U;
    }
    __Vtableidx2 = vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane;
    bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift 
        = Vbench__ConstPool__TABLE_h90db6da8_0[__Vtableidx2];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT____VdfgTmp_hede8dfa6__0 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__decoder__DOT__attention__DOT__cache_data)));
    vlSelf->bench__DOT__dut__DOT__sequence_valid = __Vdly__bench__DOT__dut__DOT__sequence_valid;
    vlSelf->bench__DOT__dut__DOT__logit_sum[0U] = __Vdly__bench__DOT__dut__DOT__logit_sum[0U];
    vlSelf->bench__DOT__dut__DOT__logit_sum[1U] = __Vdly__bench__DOT__dut__DOT__logit_sum[1U];
    vlSelf->bench__DOT__dut__DOT__logit_sum[2U] = __Vdly__bench__DOT__dut__DOT__logit_sum[2U];
    vlSelf->bench__DOT__dut__DOT__next_position = __Vdly__bench__DOT__dut__DOT__next_position;
    vlSelf->bench__DOT__dut__DOT__tensor_f16 = __Vdly__bench__DOT__dut__DOT__tensor_f16;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_value;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__b;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__weight_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qw 
                   >> (IData)(bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__zero_nibble 
        = (0xfU & (vlSelf->bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__qz 
                   >> (IData)(bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__lane_shift)));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__valid_pipe;
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
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__quotient_result;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__divider__DOT__divider__DOT__zero_divisor;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__a;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative 
        = __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__negative;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe 
        = __Vdly__bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__valid_pipe;
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
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_value;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__b;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state 
        = __Vdly__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__state;
}
