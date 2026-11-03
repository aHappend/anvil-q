// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench___024root.h"

VL_ATTR_COLD void Vbench___024root___eval_initial__TOP(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_initial__TOP\n"); );
    // Init
    VlWide<5>/*159:0*/ __Vtemp_1;
    VlWide<5>/*159:0*/ __Vtemp_3;
    VlWide<5>/*159:0*/ __Vtemp_5;
    VlWide<5>/*159:0*/ __Vtemp_7;
    // Body
    vlSelf->bench__DOT____Vxrand_h8d93fe75__1 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__0 = VL_RAND_RESET_I(32);
    __Vtemp_1[0U] = 0x643d2564U;
    __Vtemp_1[1U] = 0x5f736565U;
    __Vtemp_1[2U] = 0x74696f6eU;
    __Vtemp_1[3U] = 0x66696361U;
    __Vtemp_1[4U] = 0x76657269U;
    if (VL_UNLIKELY((! VL_VALUEPLUSARGS_INI(32, VL_CVT_PACK_STR_NW(5, __Vtemp_1), 
                                            vlSelf->bench__DOT__rng)))) {
        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:141: Assertion failed in %Nbench: MISSING_VERIFICATION_SEED\n",
                  64,VL_TIME_UNITED_Q(1000),-9,vlSymsp->name());
        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 141, "");
    }
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT____Vxrand_h8d954d18__0 
        = (0x1ffU & VL_RAND_RESET_I(9));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT____Vxrand_h8d954d18__0 
        = (0x1ffU & VL_RAND_RESET_I(9));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vxrand_h8d96565c__2 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vxrand_h8d96565c__1 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    VL_RAND_RESET_W(137, __Vtemp_3);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[0U] 
        = __Vtemp_3[0U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[1U] 
        = __Vtemp_3[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[2U] 
        = __Vtemp_3[2U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[3U] 
        = __Vtemp_3[3U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[4U] 
        = (0x1ffU & __Vtemp_3[4U]);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    VL_RAND_RESET_W(137, __Vtemp_5);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[0U] 
        = __Vtemp_5[0U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[1U] 
        = __Vtemp_5[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[2U] 
        = __Vtemp_5[2U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[3U] 
        = __Vtemp_5[3U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[4U] 
        = (0x1ffU & __Vtemp_5[4U]);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    VL_RAND_RESET_W(137, __Vtemp_7);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[0U] 
        = __Vtemp_7[0U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[1U] 
        = __Vtemp_7[1U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[2U] 
        = __Vtemp_7[2U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[3U] 
        = __Vtemp_7[3U];
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____Vxrand_had98437b__0[4U] 
        = (0x1ffU & __Vtemp_7[4U]);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d94df49__0 
        = (0xffU & VL_RAND_RESET_I(8));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__2 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__1 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h7d28236b__0 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__6 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h8d93fe75__0 
        = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__5 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__4 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__3 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__2 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__1 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h7d28236b__0 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h8d96565c__2 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h8d96565c__1 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____Vxrand_h7d28236b__2 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____Vxrand_h7d28236b__1 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest__DOT____Vxrand_h7d28236b__0 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____Vxrand_h7d28236b__1 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens__DOT____Vxrand_h7d28236b__0 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT____Vxrand_h7d28236b__1 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile__DOT____Vxrand_h7d28236b__0 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h7d28236b__1 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__5 
        = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d94df49__0 
        = (0xffU & VL_RAND_RESET_I(8));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__4 
        = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__3 
        = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h7d28236b__0 
        = VL_RAND_RESET_Q(64);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__2 
        = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__1 
        = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT____Vxrand_h8d93fe75__0 
        = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][1U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[1U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[1U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[2U][1U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[2U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[2U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[1U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[1U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[2U][1U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[2U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[2U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[1U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[1U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[2U][1U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[2U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__output_multiplier__DOT__multiplier__DOT__tree[2U][3U] = 0ULL;
}

#ifdef VL_DEBUG
VL_ATTR_COLD void Vbench___024root___dump_triggers__stl(Vbench___024root* vlSelf);
#endif  // VL_DEBUG

VL_ATTR_COLD void Vbench___024root___eval_triggers__stl(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_triggers__stl\n"); );
    // Body
    vlSelf->__VstlTriggered.set(0U, (IData)(vlSelf->__VstlFirstIteration));
#ifdef VL_DEBUG
    if (VL_UNLIKELY(vlSymsp->_vm_contextp__->debug())) {
        Vbench___024root___dump_triggers__stl(vlSelf);
    }
#endif
}

VL_ATTR_COLD void Vbench___024root___stl_sequent__TOP__0(Vbench___024root* vlSelf);
VL_ATTR_COLD void Vbench_anvil_edge_special_splitter__pi7___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf);
VL_ATTR_COLD void Vbench_anvil_edge_special_splitter__pi7___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0(Vbench_anvil_edge_special_splitter__pi7* vlSelf);
VL_ATTR_COLD void Vbench_anvil_edge_normalizer__M10___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf);
VL_ATTR_COLD void Vbench_anvil_edge_normalizer__M10___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0(Vbench_anvil_edge_normalizer__M10* vlSelf);
VL_ATTR_COLD void Vbench_anvil_q1_rmsnorm__N1_H8_M4___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
VL_ATTR_COLD void Vbench_anvil_q1_rmsnorm__N1_H8_M4___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
VL_ATTR_COLD void Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
VL_ATTR_COLD void Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
VL_ATTR_COLD void Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply__0(Vbench_anvil_edge_signed_multiplier__pi23* vlSelf);
void Vbench___024root___act_comb__TOP__1(Vbench___024root* vlSelf);

VL_ATTR_COLD void Vbench___024root___eval_stl(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_stl\n"); );
    // Body
    if ((1ULL & vlSelf->__VstlTriggered.word(0U))) {
        Vbench___024root___stl_sequent__TOP__0(vlSelf);
        Vbench_anvil_edge_special_splitter__pi7___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__raw_specials));
        Vbench_anvil_edge_special_splitter__pi7___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalized_specials));
        Vbench_anvil_edge_normalizer__M10___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__normalization));
        Vbench_anvil_edge_normalizer__M10___stl_sequent__TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization__0((&vlSymsp->TOP__bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalization));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__final_norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__norm));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__index_multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi23___stl_sequent__TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply__0((&vlSymsp->TOP__bench__DOT__dut__DOT__boot_loader__DOT__directory__DOT__validator__DOT__multiply));
        Vbench___024root___act_comb__TOP__1(vlSelf);
    }
}
