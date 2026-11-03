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
    VlWide<4>/*127:0*/ __Vtemp_2;
    VlWide<4>/*127:0*/ __Vtemp_4;
    VlWide<4>/*127:0*/ __Vtemp_6;
    VlWide<4>/*127:0*/ __Vtemp_8;
    VlWide<5>/*159:0*/ __Vtemp_9;
    VlWide<5>/*159:0*/ __Vtemp_11;
    VlWide<5>/*159:0*/ __Vtemp_13;
    VlWide<5>/*159:0*/ __Vtemp_15;
    // Body
    vlSelf->bench__DOT____Vxrand_h8d93fe75__15 = VL_RAND_RESET_I(32);
    vlSelf->bench__DOT____Vxrand_h8d93fe75__14 = VL_RAND_RESET_I(32);
    VL_RAND_RESET_W(97, __Vtemp_2);
    vlSelf->bench__DOT____Vxrand_hd08cd184__3[0U] = 
        __Vtemp_2[0U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__3[1U] = 
        __Vtemp_2[1U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__3[2U] = 
        __Vtemp_2[2U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__3[3U] = 
        (1U & __Vtemp_2[3U]);
    VL_RAND_RESET_W(97, __Vtemp_4);
    vlSelf->bench__DOT____Vxrand_hd08cd184__2[0U] = 
        __Vtemp_4[0U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__2[1U] = 
        __Vtemp_4[1U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__2[2U] = 
        __Vtemp_4[2U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__2[3U] = 
        (1U & __Vtemp_4[3U]);
    VL_RAND_RESET_W(97, __Vtemp_6);
    vlSelf->bench__DOT____Vxrand_hd08cd184__1[0U] = 
        __Vtemp_6[0U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__1[1U] = 
        __Vtemp_6[1U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__1[2U] = 
        __Vtemp_6[2U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__1[3U] = 
        (1U & __Vtemp_6[3U]);
    VL_RAND_RESET_W(97, __Vtemp_8);
    vlSelf->bench__DOT____Vxrand_hd08cd184__0[0U] = 
        __Vtemp_8[0U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__0[1U] = 
        __Vtemp_8[1U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__0[2U] = 
        __Vtemp_8[2U];
    vlSelf->bench__DOT____Vxrand_hd08cd184__0[3U] = 
        (1U & __Vtemp_8[3U]);
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
    vlSelf->bench__DOT____Vxrand_h8d96565c__0 = (1U 
                                                 & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT____Vxrand_h8d93fe75__0 = VL_RAND_RESET_I(32);
    __Vtemp_9[0U] = 0x643d2564U;
    __Vtemp_9[1U] = 0x5f736565U;
    __Vtemp_9[2U] = 0x74696f6eU;
    __Vtemp_9[3U] = 0x66696361U;
    __Vtemp_9[4U] = 0x76657269U;
    if (VL_UNLIKELY((! VL_VALUEPLUSARGS_INI(32, VL_CVT_PACK_STR_NW(5, __Vtemp_9), 
                                            vlSelf->bench__DOT__rng)))) {
        VL_WRITEF("[%0t] %%Fatal: compiled-bench.sv:50: Assertion failed in %Nbench: MISSING_VERIFICATION_SEED\n",
                  64,VL_TIME_UNITED_Q(1000),-9,vlSymsp->name());
        VL_STOP_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0136-suite-21-run_head_row_reuse/reuse-mutant-wrong-component-numerical-h8-l1-s17/compiled-bench.sv", 50, "");
    }
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__2 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__1 
        = (1U & VL_RAND_RESET_I(1));
    vlSelf->bench__DOT__dut__DOT__decoder__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    VL_RAND_RESET_W(137, __Vtemp_11);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[0U] 
        = __Vtemp_11[0U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[1U] 
        = __Vtemp_11[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[2U] 
        = __Vtemp_11[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[3U] 
        = __Vtemp_11[3U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__bus__DOT____Vxrand_had98437b__0[4U] 
        = (0x1ffU & __Vtemp_11[4U]);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    VL_RAND_RESET_W(137, __Vtemp_13);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[0U] 
        = __Vtemp_13[0U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[1U] 
        = __Vtemp_13[1U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[2U] 
        = __Vtemp_13[2U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[3U] 
        = __Vtemp_13[3U];
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__bus__DOT____Vxrand_had98437b__0[4U] 
        = (0x1ffU & __Vtemp_13[4U]);
    vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_h8d96565c__0 
        = (1U & VL_RAND_RESET_I(1));
    VL_RAND_RESET_W(137, __Vtemp_15);
    vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[0U] 
        = __Vtemp_15[0U];
    vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[1U] 
        = __Vtemp_15[1U];
    vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[2U] 
        = __Vtemp_15[2U];
    vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[3U] 
        = __Vtemp_15[3U];
    vlSelf->bench__DOT__dut__DOT__bus__DOT____Vxrand_had98437b__0[4U] 
        = (0x1ffU & __Vtemp_15[4U]);
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[1U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][1U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__rope__DOT__multiplier__DOT__multiplier__DOT__tree[2U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[1U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[1U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[2U][1U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[2U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__multiplier__DOT__multiplier__DOT__tree[2U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[1U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[1U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[2U][1U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[2U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__decoder__DOT__residual__DOT__multiplier__DOT__multiplier__DOT__tree[2U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[1U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[1U][3U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[2U][1U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[2U][2U] = 0ULL;
    vlSelf->bench__DOT__dut__DOT__output_multiplier__DOT__multiplier__DOT__tree[2U][3U] = 0ULL;
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
VL_ATTR_COLD void Vbench_anvil_q1_rmsnorm__N1_H8_M4___stl_sequent__TOP__bench__DOT__dut__DOT__final_norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
VL_ATTR_COLD void Vbench_anvil_q1_rmsnorm__N1_H8_M4___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf);
VL_ATTR_COLD void Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0(Vbench_anvil_edge_signed_multiplier__pi11* vlSelf);
void Vbench___024root___act_comb__TOP__1(Vbench___024root* vlSelf);

VL_ATTR_COLD void Vbench___024root___eval_stl(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___eval_stl\n"); );
    // Body
    if ((1ULL & vlSelf->__VstlTriggered.word(0U))) {
        Vbench___024root___stl_sequent__TOP__0(vlSelf);
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___stl_sequent__TOP__bench__DOT__dut__DOT__final_norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__final_norm));
        Vbench_anvil_q1_rmsnorm__N1_H8_M4___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__norm));
        Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__gemv__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__multiplier));
        Vbench_anvil_edge_signed_multiplier__pi11___stl_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__gemv__DOT__multiplier__0((&vlSymsp->TOP__bench__DOT__dut__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__multiplier));
        Vbench___024root___act_comb__TOP__1(vlSelf);
    }
}
