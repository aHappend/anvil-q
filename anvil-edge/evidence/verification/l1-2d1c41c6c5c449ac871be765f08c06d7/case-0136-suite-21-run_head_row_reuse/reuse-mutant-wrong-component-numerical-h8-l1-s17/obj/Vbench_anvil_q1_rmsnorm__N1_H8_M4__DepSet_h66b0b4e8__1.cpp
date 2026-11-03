// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench_anvil_q1_rmsnorm__N1_H8_M4.h"

extern const VlWide<8>/*255:0*/ Vbench__ConstPool__CONST_h9e67c271_0;

VL_INLINE_OPT void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__0\n"); );
    // Init
    CData/*0:0*/ __PVT__port_idle;
    __PVT__port_idle = 0;
    // Body
    vlSelf->__PVT__root_ready = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                                 & (0U == (IData)(vlSelf->__PVT__root_unit__DOT__state)));
    vlSelf->__PVT__root_valid = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                                 & (3U == (IData)(vlSelf->__PVT__root_unit__DOT__state)));
    vlSelf->__PVT__divide_ready = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                                   & (0U == (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__state)));
    vlSelf->__PVT__divide_valid = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                                   & (3U == (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__state)));
    vlSelf->mem_req_write = ((IData)(vlSelf->__PVT__memory_port__DOT__wr) 
                             & (IData)(vlSymsp->TOP.bench__DOT__rst_n));
    __PVT__port_idle = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                        & (0U == (IData)(vlSelf->__PVT__memory_port__DOT__state)));
    vlSelf->mem_req_valid = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                             & (1U == (IData)(vlSelf->__PVT__memory_port__DOT__state)));
    vlSelf->cmd_ready = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                         & (0U == (IData)(vlSelf->__PVT__state)));
    vlSelf->done = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                    & (0x18U == (IData)(vlSelf->__PVT__state)));
    vlSelf->__PVT__operand_a[0U] = 0U;
    vlSelf->__PVT__operand_a[1U] = 0U;
    vlSelf->__PVT__operand_a[2U] = 0U;
    vlSelf->__PVT__operand_a[3U] = 0U;
    vlSelf->__PVT__operand_b[0U] = 0U;
    vlSelf->__PVT__operand_b[1U] = 0U;
    vlSelf->__PVT__operand_b[2U] = 0U;
    vlSelf->__PVT__operand_b[3U] = 0U;
    vlSelf->__PVT__multiply_valid = ((IData)(vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_result) 
                                     & (IData)(vlSymsp->TOP.bench__DOT__rst_n));
    vlSelf->__PVT__multiply_ready = ((~ (IData)(vlSelf->__PVT__multiplier__DOT__multiplier__DOT__busy)) 
                                     & (IData)(vlSymsp->TOP.bench__DOT__rst_n));
    vlSelf->__PVT__divide_by_zero = ((IData)(vlSelf->__PVT__divide_valid) 
                                     & (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->__PVT__write_request = 0U;
    vlSelf->__PVT__issue = 0U;
    vlSelf->__PVT__write_data = 0U;
    vlSelf->__PVT__kind = 0U;
    vlSelf->__PVT__row = 0U;
    vlSelf->__PVT__memory_layer = 0U;
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        vlSelf->__PVT__root_value = vlSelf->__PVT__root_unit__DOT__root_result;
        vlSelf->__PVT__quotient[0U] = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[0U];
        vlSelf->__PVT__quotient[1U] = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[1U];
        vlSelf->__PVT__quotient[2U] = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[2U];
        vlSelf->__PVT__quotient[3U] = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[3U];
        vlSelf->mem_req_kind = vlSelf->__PVT__memory_port__DOT__kd;
        vlSelf->mem_req_proj = vlSelf->__PVT__memory_port__DOT__pj;
        vlSelf->mem_req_layer = vlSelf->__PVT__memory_port__DOT__ly;
        vlSelf->mem_req_row = vlSelf->__PVT__memory_port__DOT__rw;
        vlSelf->mem_req_col = vlSelf->__PVT__memory_port__DOT__cl;
        vlSelf->mem_req_wdata = vlSelf->__PVT__memory_port__DOT__wd;
        vlSelf->__PVT__product[0U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[0U];
        vlSelf->__PVT__product[1U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[1U];
        vlSelf->__PVT__product[2U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[2U];
        vlSelf->__PVT__product[3U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[3U];
        vlSelf->__PVT__product[4U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[4U];
        vlSelf->__PVT__product[5U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[5U];
        vlSelf->__PVT__product[6U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[6U];
        vlSelf->__PVT__product[7U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[7U];
        if ((3U == (IData)(vlSelf->__PVT__state))) {
            vlSelf->__PVT__operand_a[0U] = vlSelf->__PVT__x;
            vlSelf->__PVT__operand_a[1U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_a[2U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_a[3U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[0U] = vlSelf->__PVT__x;
            vlSelf->__PVT__operand_b[1U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[2U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[3U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
        } else if ((0x11U == (IData)(vlSelf->__PVT__state))) {
            vlSelf->__PVT__operand_a[0U] = vlSelf->__PVT__x;
            vlSelf->__PVT__operand_a[1U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_a[2U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_a[3U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[0U] = vlSelf->__PVT__gamma;
            vlSelf->__PVT__operand_b[1U] = (- (IData)(
                                                      (vlSelf->__PVT__gamma 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[2U] = (- (IData)(
                                                      (vlSelf->__PVT__gamma 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[3U] = (- (IData)(
                                                      (vlSelf->__PVT__gamma 
                                                       >> 0x1fU)));
        } else if ((0x13U == (IData)(vlSelf->__PVT__state))) {
            vlSelf->__PVT__operand_a[0U] = (IData)(vlSelf->__PVT__norm_product);
            vlSelf->__PVT__operand_a[1U] = (IData)(
                                                   (vlSelf->__PVT__norm_product 
                                                    >> 0x20U));
            vlSelf->__PVT__operand_a[2U] = (IData)(
                                                   (- (QData)((IData)(
                                                                      (1U 
                                                                       & (IData)(
                                                                                (vlSelf->__PVT__norm_product 
                                                                                >> 0x3fU)))))));
            vlSelf->__PVT__operand_a[3U] = (IData)(
                                                   ((- (QData)((IData)(
                                                                       (1U 
                                                                        & (IData)(
                                                                                (vlSelf->__PVT__norm_product 
                                                                                >> 0x3fU)))))) 
                                                    >> 0x20U));
            vlSelf->__PVT__operand_b[0U] = (IData)(vlSelf->__PVT__reciprocal);
            vlSelf->__PVT__operand_b[1U] = (IData)(
                                                   (vlSelf->__PVT__reciprocal 
                                                    >> 0x20U));
            vlSelf->__PVT__operand_b[2U] = 0U;
            vlSelf->__PVT__operand_b[3U] = 0U;
        }
        if (__PVT__port_idle) {
            if ((0x10U & (IData)(vlSelf->__PVT__state))) {
                if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->__PVT__state))) {
                        if ((2U & (IData)(vlSelf->__PVT__state))) {
                            if ((1U & (~ (IData)(vlSelf->__PVT__state)))) {
                                vlSelf->__PVT__write_request = 1U;
                                vlSelf->__PVT__issue = 1U;
                                vlSelf->__PVT__write_data 
                                    = vlSelf->__PVT__output_value;
                                vlSelf->__PVT__kind = 8U;
                                vlSelf->__PVT__row 
                                    = vlSelf->__PVT__target_slot;
                            }
                        }
                    }
                }
            } else if ((8U & (IData)(vlSelf->__PVT__state))) {
                if ((4U & (IData)(vlSelf->__PVT__state))) {
                    if ((2U & (IData)(vlSelf->__PVT__state))) {
                        if ((1U & (IData)(vlSelf->__PVT__state))) {
                            vlSelf->__PVT__issue = 1U;
                            vlSelf->__PVT__kind = vlSelf->__PVT__norm_kind;
                        }
                    } else if ((1U & (IData)(vlSelf->__PVT__state))) {
                        vlSelf->__PVT__issue = 1U;
                        vlSelf->__PVT__kind = 8U;
                    }
                    if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->__PVT__state))) {
                            vlSelf->__PVT__row = vlSelf->__PVT__source_slot;
                        }
                    }
                }
            } else if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                 >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelf->__PVT__state))) {
                        vlSelf->__PVT__issue = 1U;
                        vlSelf->__PVT__kind = 8U;
                        vlSelf->__PVT__row = vlSelf->__PVT__source_slot;
                    }
                }
            }
            if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                          >> 4U)))) {
                if ((8U & (IData)(vlSelf->__PVT__state))) {
                    if ((4U & (IData)(vlSelf->__PVT__state))) {
                        if ((2U & (IData)(vlSelf->__PVT__state))) {
                            if ((1U & (IData)(vlSelf->__PVT__state))) {
                                vlSelf->__PVT__memory_layer 
                                    = ((7U == (IData)(vlSelf->__PVT__norm_kind))
                                        ? 0U : vlSelf->__PVT__layer);
                            }
                        }
                    }
                }
            }
        }
    } else {
        vlSelf->__PVT__root_value = 0ULL;
        vlSelf->__PVT__quotient[0U] = 0U;
        vlSelf->__PVT__quotient[1U] = 0U;
        vlSelf->__PVT__quotient[2U] = 0U;
        vlSelf->__PVT__quotient[3U] = 0U;
        vlSelf->mem_req_kind = 0U;
        vlSelf->mem_req_proj = 0U;
        vlSelf->mem_req_layer = 0U;
        vlSelf->mem_req_row = 0U;
        vlSelf->mem_req_col = 0U;
        vlSelf->mem_req_wdata = 0U;
        vlSelf->__PVT__product[0U] = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__product[1U] = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__product[2U] = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__product[3U] = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__product[4U] = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__product[5U] = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__product[6U] = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__product[7U] = Vbench__ConstPool__CONST_h9e67c271_0[7U];
    }
}

VL_INLINE_OPT void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__1(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__1\n"); );
    // Body
    vlSelf->mem_rsp_ready = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                             & (2U == (IData)(vlSelf->__PVT__memory_port__DOT__state)));
}

VL_INLINE_OPT void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__2(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__final_norm__2\n"); );
    // Body
    vlSelf->__PVT__complete = ((IData)(vlSelf->mem_rsp_ready) 
                               & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber19));
    if (vlSelf->__PVT__complete) {
        vlSelf->__PVT__fault = vlSymsp->TOP.bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber22;
        vlSelf->__PVT__read_data = vlSymsp->TOP.bench__DOT__dut__DOT____Vcellinp__final_norm____pinNumber21;
    } else {
        vlSelf->__PVT__fault = 0U;
        vlSelf->__PVT__read_data = 0U;
    }
}

VL_INLINE_OPT void Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                Vbench_anvil_q1_rmsnorm__N1_H8_M4___act_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0\n"); );
    // Init
    CData/*0:0*/ __PVT__port_idle;
    __PVT__port_idle = 0;
    // Body
    vlSelf->cmd_ready = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                         & (0U == (IData)(vlSelf->__PVT__state)));
    vlSelf->done = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                    & (0x18U == (IData)(vlSelf->__PVT__state)));
    vlSelf->__PVT__multiply_ready = ((~ (IData)(vlSelf->__PVT__multiplier__DOT__multiplier__DOT__busy)) 
                                     & (IData)(vlSymsp->TOP.bench__DOT__rst_n));
    vlSelf->__PVT__multiply_valid = ((IData)(vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_result) 
                                     & (IData)(vlSymsp->TOP.bench__DOT__rst_n));
    vlSelf->__PVT__divide_ready = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                                   & (0U == (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__state)));
    vlSelf->__PVT__root_ready = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                                 & (0U == (IData)(vlSelf->__PVT__root_unit__DOT__state)));
    vlSelf->__PVT__root_valid = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                                 & (3U == (IData)(vlSelf->__PVT__root_unit__DOT__state)));
    vlSelf->__PVT__operand_a[0U] = 0U;
    vlSelf->__PVT__operand_a[1U] = 0U;
    vlSelf->__PVT__operand_a[2U] = 0U;
    vlSelf->__PVT__operand_a[3U] = 0U;
    vlSelf->__PVT__operand_b[0U] = 0U;
    vlSelf->__PVT__operand_b[1U] = 0U;
    vlSelf->__PVT__operand_b[2U] = 0U;
    vlSelf->__PVT__operand_b[3U] = 0U;
    vlSelf->__PVT__divide_valid = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                                   & (3U == (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__state)));
    vlSelf->mem_rsp_ready = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                             & (2U == (IData)(vlSelf->__PVT__memory_port__DOT__state)));
    __PVT__port_idle = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                        & (0U == (IData)(vlSelf->__PVT__memory_port__DOT__state)));
    vlSelf->mem_req_valid = ((IData)(vlSymsp->TOP.bench__DOT__rst_n) 
                             & (1U == (IData)(vlSelf->__PVT__memory_port__DOT__state)));
    vlSelf->mem_req_write = ((IData)(vlSelf->__PVT__memory_port__DOT__wr) 
                             & (IData)(vlSymsp->TOP.bench__DOT__rst_n));
    vlSelf->__PVT__divide_by_zero = ((IData)(vlSelf->__PVT__divide_valid) 
                                     & (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__zero_divisor));
    vlSelf->__PVT__complete = ((IData)(vlSelf->mem_rsp_ready) 
                               & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber19));
    vlSelf->__PVT__write_request = 0U;
    vlSelf->__PVT__issue = 0U;
    vlSelf->__PVT__write_data = 0U;
    vlSelf->__PVT__kind = 0U;
    vlSelf->__PVT__row = 0U;
    vlSelf->__PVT__memory_layer = 0U;
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        vlSelf->__PVT__product[0U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[0U];
        vlSelf->__PVT__product[1U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[1U];
        vlSelf->__PVT__product[2U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[2U];
        vlSelf->__PVT__product[3U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[3U];
        vlSelf->__PVT__product[4U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[4U];
        vlSelf->__PVT__product[5U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[5U];
        vlSelf->__PVT__product[6U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[6U];
        vlSelf->__PVT__product[7U] = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[7U];
        vlSelf->__PVT__quotient[0U] = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[0U];
        vlSelf->__PVT__quotient[1U] = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[1U];
        vlSelf->__PVT__quotient[2U] = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[2U];
        vlSelf->__PVT__quotient[3U] = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[3U];
        vlSelf->__PVT__root_value = vlSelf->__PVT__root_unit__DOT__root_result;
        if ((3U == (IData)(vlSelf->__PVT__state))) {
            vlSelf->__PVT__operand_a[0U] = vlSelf->__PVT__x;
            vlSelf->__PVT__operand_a[1U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_a[2U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_a[3U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[0U] = vlSelf->__PVT__x;
            vlSelf->__PVT__operand_b[1U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[2U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[3U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
        } else if ((0x11U == (IData)(vlSelf->__PVT__state))) {
            vlSelf->__PVT__operand_a[0U] = vlSelf->__PVT__x;
            vlSelf->__PVT__operand_a[1U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_a[2U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_a[3U] = (- (IData)(
                                                      (vlSelf->__PVT__x 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[0U] = vlSelf->__PVT__gamma;
            vlSelf->__PVT__operand_b[1U] = (- (IData)(
                                                      (vlSelf->__PVT__gamma 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[2U] = (- (IData)(
                                                      (vlSelf->__PVT__gamma 
                                                       >> 0x1fU)));
            vlSelf->__PVT__operand_b[3U] = (- (IData)(
                                                      (vlSelf->__PVT__gamma 
                                                       >> 0x1fU)));
        } else if ((0x13U == (IData)(vlSelf->__PVT__state))) {
            vlSelf->__PVT__operand_a[0U] = (IData)(vlSelf->__PVT__norm_product);
            vlSelf->__PVT__operand_a[1U] = (IData)(
                                                   (vlSelf->__PVT__norm_product 
                                                    >> 0x20U));
            vlSelf->__PVT__operand_a[2U] = (IData)(
                                                   (- (QData)((IData)(
                                                                      (1U 
                                                                       & (IData)(
                                                                                (vlSelf->__PVT__norm_product 
                                                                                >> 0x3fU)))))));
            vlSelf->__PVT__operand_a[3U] = (IData)(
                                                   ((- (QData)((IData)(
                                                                       (1U 
                                                                        & (IData)(
                                                                                (vlSelf->__PVT__norm_product 
                                                                                >> 0x3fU)))))) 
                                                    >> 0x20U));
            vlSelf->__PVT__operand_b[0U] = (IData)(vlSelf->__PVT__reciprocal);
            vlSelf->__PVT__operand_b[1U] = (IData)(
                                                   (vlSelf->__PVT__reciprocal 
                                                    >> 0x20U));
            vlSelf->__PVT__operand_b[2U] = 0U;
            vlSelf->__PVT__operand_b[3U] = 0U;
        }
        vlSelf->mem_req_kind = vlSelf->__PVT__memory_port__DOT__kd;
        vlSelf->mem_req_layer = vlSelf->__PVT__memory_port__DOT__ly;
        vlSelf->mem_req_proj = vlSelf->__PVT__memory_port__DOT__pj;
        vlSelf->mem_req_row = vlSelf->__PVT__memory_port__DOT__rw;
        vlSelf->mem_req_col = vlSelf->__PVT__memory_port__DOT__cl;
        vlSelf->mem_req_wdata = vlSelf->__PVT__memory_port__DOT__wd;
        if (__PVT__port_idle) {
            if ((0x10U & (IData)(vlSelf->__PVT__state))) {
                if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                              >> 3U)))) {
                    if ((4U & (IData)(vlSelf->__PVT__state))) {
                        if ((2U & (IData)(vlSelf->__PVT__state))) {
                            if ((1U & (~ (IData)(vlSelf->__PVT__state)))) {
                                vlSelf->__PVT__write_request = 1U;
                                vlSelf->__PVT__issue = 1U;
                                vlSelf->__PVT__write_data 
                                    = vlSelf->__PVT__output_value;
                                vlSelf->__PVT__kind = 8U;
                                vlSelf->__PVT__row 
                                    = vlSelf->__PVT__target_slot;
                            }
                        }
                    }
                }
            } else if ((8U & (IData)(vlSelf->__PVT__state))) {
                if ((4U & (IData)(vlSelf->__PVT__state))) {
                    if ((2U & (IData)(vlSelf->__PVT__state))) {
                        if ((1U & (IData)(vlSelf->__PVT__state))) {
                            vlSelf->__PVT__issue = 1U;
                            vlSelf->__PVT__kind = vlSelf->__PVT__norm_kind;
                        }
                    } else if ((1U & (IData)(vlSelf->__PVT__state))) {
                        vlSelf->__PVT__issue = 1U;
                        vlSelf->__PVT__kind = 8U;
                    }
                    if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                  >> 1U)))) {
                        if ((1U & (IData)(vlSelf->__PVT__state))) {
                            vlSelf->__PVT__row = vlSelf->__PVT__source_slot;
                        }
                    }
                }
            } else if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                 >> 2U)))) {
                if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                              >> 1U)))) {
                    if ((1U & (IData)(vlSelf->__PVT__state))) {
                        vlSelf->__PVT__issue = 1U;
                        vlSelf->__PVT__kind = 8U;
                        vlSelf->__PVT__row = vlSelf->__PVT__source_slot;
                    }
                }
            }
            if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                          >> 4U)))) {
                if ((8U & (IData)(vlSelf->__PVT__state))) {
                    if ((4U & (IData)(vlSelf->__PVT__state))) {
                        if ((2U & (IData)(vlSelf->__PVT__state))) {
                            if ((1U & (IData)(vlSelf->__PVT__state))) {
                                vlSelf->__PVT__memory_layer 
                                    = ((7U == (IData)(vlSelf->__PVT__norm_kind))
                                        ? 0U : vlSelf->__PVT__layer);
                            }
                        }
                    }
                }
            }
        }
    } else {
        vlSelf->__PVT__product[0U] = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__product[1U] = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__product[2U] = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__product[3U] = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__product[4U] = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__product[5U] = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__product[6U] = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__product[7U] = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__quotient[0U] = 0U;
        vlSelf->__PVT__quotient[1U] = 0U;
        vlSelf->__PVT__quotient[2U] = 0U;
        vlSelf->__PVT__quotient[3U] = 0U;
        vlSelf->__PVT__root_value = 0ULL;
        vlSelf->mem_req_kind = 0U;
        vlSelf->mem_req_layer = 0U;
        vlSelf->mem_req_proj = 0U;
        vlSelf->mem_req_row = 0U;
        vlSelf->mem_req_col = 0U;
        vlSelf->mem_req_wdata = 0U;
    }
    if (vlSelf->__PVT__complete) {
        vlSelf->__PVT__fault = vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber22;
        vlSelf->__PVT__read_data = vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber21;
    } else {
        vlSelf->__PVT__fault = 0U;
        vlSelf->__PVT__read_data = 0U;
    }
}

VL_INLINE_OPT void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_sequent__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0\n"); );
    // Init
    IData/*31:0*/ __Vfunc_sat32__6__Vfuncout;
    __Vfunc_sat32__6__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__6__x;
    VL_ZERO_W(128, __Vfunc_sat32__6__x);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__7__Vfuncout;
    VL_ZERO_W(128, __Vfunc_round_shift__7__Vfuncout);
    VlWide<4>/*127:0*/ __Vfunc_round_shift__7__x;
    VL_ZERO_W(128, __Vfunc_round_shift__7__x);
    VlWide<5>/*128:0*/ __Vfunc_round_shift__7__magnitude;
    VL_ZERO_W(129, __Vfunc_round_shift__7__magnitude);
    CData/*0:0*/ __Vfunc_f16_invalid__8__Vfuncout;
    __Vfunc_f16_invalid__8__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_invalid__8__h;
    __Vfunc_f16_invalid__8__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__9__Vfuncout;
    __Vfunc_f16_q16__9__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_q16__9__h;
    __Vfunc_f16_q16__9__h = 0;
    IData/*31:0*/ __Vfunc_f16_q16__9__magnitude;
    __Vfunc_f16_q16__9__magnitude = 0;
    QData/*32:0*/ __Vfunc_f16_q16__9__signed_value;
    __Vfunc_f16_q16__9__signed_value = 0;
    IData/*31:0*/ __Vfunc_f16_scale__10__Vfuncout;
    __Vfunc_f16_scale__10__Vfuncout = 0;
    SData/*15:0*/ __Vfunc_f16_scale__10__h;
    __Vfunc_f16_scale__10__h = 0;
    IData/*31:0*/ __Vfunc_f16_scale__10__magnitude;
    __Vfunc_f16_scale__10__magnitude = 0;
    IData/*31:0*/ __Vfunc_f16_scale__10__shift;
    __Vfunc_f16_scale__10__shift = 0;
    IData/*31:0*/ __Vfunc_sat32__11__Vfuncout;
    __Vfunc_sat32__11__Vfuncout = 0;
    VlWide<4>/*127:0*/ __Vfunc_sat32__11__x;
    VL_ZERO_W(128, __Vfunc_sat32__11__x);
    CData/*4:0*/ __Vdly__state;
    __Vdly__state = 0;
    IData/*31:0*/ __Vdly__index;
    __Vdly__index = 0;
    CData/*1:0*/ __Vdly__memory_port__DOT__state;
    __Vdly__memory_port__DOT__state = 0;
    CData/*7:0*/ __Vdly__multiplier__DOT__multiplier__DOT__valid_pipe;
    __Vdly__multiplier__DOT__multiplier__DOT__valid_pipe = 0;
    CData/*1:0*/ __Vdly__divider__DOT__divider__DOT__state;
    __Vdly__divider__DOT__divider__DOT__state = 0;
    VlWide<4>/*127:0*/ __Vdly__divider__DOT__divider__DOT__quotient_work;
    VL_ZERO_W(128, __Vdly__divider__DOT__divider__DOT__quotient_work);
    CData/*1:0*/ __Vdly__root_unit__DOT__state;
    __Vdly__root_unit__DOT__state = 0;
    QData/*63:0*/ __Vdly__root_unit__DOT__root_work;
    __Vdly__root_unit__DOT__root_work = 0;
    VlWide<4>/*127:0*/ __Vtemp_1;
    VlWide<5>/*159:0*/ __Vtemp_3;
    VlWide<4>/*127:0*/ __Vtemp_6;
    VlWide<4>/*127:0*/ __Vtemp_8;
    VlWide<5>/*159:0*/ __Vtemp_10;
    VlWide<5>/*159:0*/ __Vtemp_11;
    VlWide<8>/*255:0*/ __Vtemp_17;
    VlWide<8>/*255:0*/ __Vtemp_18;
    VlWide<8>/*255:0*/ __Vtemp_19;
    VlWide<8>/*255:0*/ __Vtemp_20;
    VlWide<8>/*255:0*/ __Vtemp_21;
    VlWide<8>/*255:0*/ __Vtemp_22;
    VlWide<8>/*255:0*/ __Vtemp_23;
    VlWide<8>/*255:0*/ __Vtemp_24;
    VlWide<8>/*255:0*/ __Vtemp_25;
    VlWide<8>/*255:0*/ __Vtemp_26;
    VlWide<8>/*255:0*/ __Vtemp_27;
    VlWide<8>/*255:0*/ __Vtemp_28;
    VlWide<8>/*255:0*/ __Vtemp_29;
    VlWide<8>/*255:0*/ __Vtemp_30;
    VlWide<8>/*255:0*/ __Vtemp_31;
    VlWide<8>/*255:0*/ __Vtemp_32;
    VlWide<8>/*255:0*/ __Vtemp_33;
    VlWide<8>/*255:0*/ __Vtemp_34;
    VlWide<8>/*255:0*/ __Vtemp_35;
    VlWide<8>/*255:0*/ __Vtemp_36;
    VlWide<8>/*255:0*/ __Vtemp_37;
    VlWide<8>/*255:0*/ __Vtemp_38;
    VlWide<8>/*255:0*/ __Vtemp_39;
    VlWide<8>/*255:0*/ __Vtemp_40;
    VlWide<8>/*255:0*/ __Vtemp_41;
    VlWide<8>/*255:0*/ __Vtemp_42;
    VlWide<8>/*255:0*/ __Vtemp_43;
    VlWide<8>/*255:0*/ __Vtemp_44;
    VlWide<8>/*255:0*/ __Vtemp_45;
    VlWide<8>/*255:0*/ __Vtemp_46;
    VlWide<8>/*255:0*/ __Vtemp_47;
    VlWide<8>/*255:0*/ __Vtemp_48;
    VlWide<8>/*255:0*/ __Vtemp_49;
    VlWide<8>/*255:0*/ __Vtemp_50;
    VlWide<8>/*255:0*/ __Vtemp_51;
    VlWide<8>/*255:0*/ __Vtemp_52;
    VlWide<8>/*255:0*/ __Vtemp_53;
    VlWide<8>/*255:0*/ __Vtemp_54;
    VlWide<8>/*255:0*/ __Vtemp_55;
    VlWide<8>/*255:0*/ __Vtemp_56;
    VlWide<8>/*255:0*/ __Vtemp_57;
    VlWide<8>/*255:0*/ __Vtemp_58;
    VlWide<8>/*255:0*/ __Vtemp_59;
    VlWide<8>/*255:0*/ __Vtemp_60;
    VlWide<8>/*255:0*/ __Vtemp_61;
    VlWide<8>/*255:0*/ __Vtemp_62;
    VlWide<8>/*255:0*/ __Vtemp_63;
    VlWide<8>/*255:0*/ __Vtemp_64;
    VlWide<8>/*255:0*/ __Vtemp_65;
    VlWide<8>/*255:0*/ __Vtemp_66;
    VlWide<8>/*255:0*/ __Vtemp_67;
    VlWide<8>/*255:0*/ __Vtemp_68;
    VlWide<8>/*255:0*/ __Vtemp_69;
    VlWide<8>/*255:0*/ __Vtemp_70;
    VlWide<8>/*255:0*/ __Vtemp_71;
    VlWide<8>/*255:0*/ __Vtemp_72;
    VlWide<8>/*255:0*/ __Vtemp_73;
    VlWide<8>/*255:0*/ __Vtemp_74;
    VlWide<8>/*255:0*/ __Vtemp_75;
    VlWide<8>/*255:0*/ __Vtemp_76;
    VlWide<8>/*255:0*/ __Vtemp_77;
    VlWide<8>/*255:0*/ __Vtemp_78;
    VlWide<8>/*255:0*/ __Vtemp_79;
    VlWide<8>/*255:0*/ __Vtemp_80;
    VlWide<4>/*127:0*/ __Vtemp_82;
    VlWide<5>/*159:0*/ __Vtemp_83;
    VlWide<5>/*159:0*/ __Vtemp_84;
    VlWide<5>/*159:0*/ __Vtemp_91;
    VlWide<5>/*159:0*/ __Vtemp_92;
    VlWide<5>/*159:0*/ __Vtemp_93;
    VlWide<5>/*159:0*/ __Vtemp_94;
    VlWide<4>/*127:0*/ __Vtemp_96;
    VlWide<5>/*159:0*/ __Vtemp_97;
    VlWide<4>/*127:0*/ __Vtemp_101;
    VlWide<4>/*127:0*/ __Vtemp_102;
    VlWide<4>/*127:0*/ __Vtemp_107;
    VlWide<4>/*127:0*/ __Vtemp_108;
    VlWide<4>/*127:0*/ __Vtemp_109;
    VlWide<4>/*127:0*/ __Vtemp_110;
    VlWide<3>/*95:0*/ __Vtemp_111;
    VlWide<3>/*95:0*/ __Vtemp_112;
    VlWide<5>/*159:0*/ __Vtemp_115;
    VlWide<5>/*159:0*/ __Vtemp_119;
    VlWide<4>/*127:0*/ __Vtemp_122;
    VlWide<4>/*127:0*/ __Vtemp_124;
    VlWide<5>/*159:0*/ __Vtemp_130;
    VlWide<5>/*159:0*/ __Vtemp_131;
    // Body
    __Vdly__root_unit__DOT__root_work = vlSelf->__PVT__root_unit__DOT__root_work;
    __Vdly__root_unit__DOT__state = vlSelf->__PVT__root_unit__DOT__state;
    __Vdly__divider__DOT__divider__DOT__quotient_work[0U] 
        = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[0U];
    __Vdly__divider__DOT__divider__DOT__quotient_work[1U] 
        = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[1U];
    __Vdly__divider__DOT__divider__DOT__quotient_work[2U] 
        = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[2U];
    __Vdly__divider__DOT__divider__DOT__quotient_work[3U] 
        = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[3U];
    __Vdly__divider__DOT__divider__DOT__state = vlSelf->__PVT__divider__DOT__divider__DOT__state;
    __Vdly__index = vlSelf->__PVT__index;
    __Vdly__state = vlSelf->__PVT__state;
    __Vdly__memory_port__DOT__state = vlSelf->__PVT__memory_port__DOT__state;
    __Vdly__multiplier__DOT__multiplier__DOT__valid_pipe 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_pipe;
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->__PVT__fault)))) {
            if ((0x10U & (IData)(vlSelf->__PVT__state))) {
                if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                  >> 2U)))) {
                        if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                      >> 1U)))) {
                            if ((1U & (~ (IData)(vlSelf->__PVT__state)))) {
                                if (vlSelf->__PVT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__8__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->__PVT__read_data);
                                                __Vfunc_f16_invalid__8__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__8__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__8__Vfuncout))) {
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
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->__PVT__fault)))) {
            if ((0x10U & (IData)(vlSelf->__PVT__state))) {
                if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                  >> 2U)))) {
                        if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                      >> 1U)))) {
                            if ((1U & (~ (IData)(vlSelf->__PVT__state)))) {
                                if (vlSelf->__PVT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__8__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->__PVT__read_data);
                                                __Vfunc_f16_invalid__8__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__8__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__8__Vfuncout))) {
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
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        if ((1U & (~ (IData)(vlSelf->__PVT__fault)))) {
            if ((0x10U & (IData)(vlSelf->__PVT__state))) {
                if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                              >> 3U)))) {
                    if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                  >> 2U)))) {
                        if ((1U & (~ ((IData)(vlSelf->__PVT__state) 
                                      >> 1U)))) {
                            if ((1U & (~ (IData)(vlSelf->__PVT__state)))) {
                                if (vlSelf->__PVT__complete) {
                                    if (([&]() {
                                                __Vfunc_f16_invalid__8__h 
                                                    = 
                                                    (0xffffU 
                                                     & vlSelf->__PVT__read_data);
                                                __Vfunc_f16_invalid__8__Vfuncout 
                                                    = 
                                                    (0x1fU 
                                                     == 
                                                     (0x1fU 
                                                      & ((IData)(__Vfunc_f16_invalid__8__h) 
                                                         >> 0xaU)));
                                            }(), (IData)(__Vfunc_f16_invalid__8__Vfuncout))) {
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
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        if ((2U & (IData)(vlSelf->__PVT__root_unit__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__root_unit__DOT__state))) {
                if (((IData)(vlSelf->__PVT__root_valid) 
                     & (0xaU == (IData)(vlSelf->__PVT__state)))) {
                    __Vdly__root_unit__DOT__state = 0U;
                }
            } else {
                vlSelf->__PVT__root_unit__DOT__root_result 
                    = vlSelf->__PVT__root_unit__DOT__root_work;
                __Vdly__root_unit__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__root_unit__DOT__state))) {
            VL_SHIFTL_WWI(128,128,32, __Vtemp_1, vlSelf->__PVT__root_unit__DOT__radicand_shift, 2U);
            vlSelf->__PVT__root_unit__DOT__radicand_shift[0U] 
                = __Vtemp_1[0U];
            vlSelf->__PVT__root_unit__DOT__radicand_shift[1U] 
                = __Vtemp_1[1U];
            vlSelf->__PVT__root_unit__DOT__radicand_shift[2U] 
                = __Vtemp_1[2U];
            vlSelf->__PVT__root_unit__DOT__radicand_shift[3U] 
                = __Vtemp_1[3U];
            if (vlSelf->__PVT__root_unit__DOT__subtract) {
                __Vdly__root_unit__DOT__root_work = 
                    (1ULL | VL_SHIFTL_QQI(64,64,32, vlSelf->__PVT__root_unit__DOT__root_work, 1U));
                VL_SUB_W(5, __Vtemp_3, vlSelf->__PVT__root_unit__DOT__shifted_remainder, vlSelf->__PVT__root_unit__DOT__trial);
                vlSelf->__PVT__root_unit__DOT__remainder_work[0U] 
                    = __Vtemp_3[0U];
                vlSelf->__PVT__root_unit__DOT__remainder_work[1U] 
                    = __Vtemp_3[1U];
                vlSelf->__PVT__root_unit__DOT__remainder_work[2U] 
                    = __Vtemp_3[2U];
                vlSelf->__PVT__root_unit__DOT__remainder_work[3U] 
                    = __Vtemp_3[3U];
                vlSelf->__PVT__root_unit__DOT__remainder_work[4U] 
                    = (3U & __Vtemp_3[4U]);
            } else {
                __Vdly__root_unit__DOT__root_work = 
                    VL_SHIFTL_QQI(64,64,32, vlSelf->__PVT__root_unit__DOT__root_work, 1U);
                vlSelf->__PVT__root_unit__DOT__remainder_work[0U] 
                    = vlSelf->__PVT__root_unit__DOT__shifted_remainder[0U];
                vlSelf->__PVT__root_unit__DOT__remainder_work[1U] 
                    = vlSelf->__PVT__root_unit__DOT__shifted_remainder[1U];
                vlSelf->__PVT__root_unit__DOT__remainder_work[2U] 
                    = vlSelf->__PVT__root_unit__DOT__shifted_remainder[2U];
                vlSelf->__PVT__root_unit__DOT__remainder_work[3U] 
                    = vlSelf->__PVT__root_unit__DOT__shifted_remainder[3U];
                vlSelf->__PVT__root_unit__DOT__remainder_work[4U] 
                    = vlSelf->__PVT__root_unit__DOT__shifted_remainder[4U];
            }
            if ((0x3fU == (IData)(vlSelf->__PVT__root_unit__DOT__iteration))) {
                __Vdly__root_unit__DOT__state = 2U;
            } else {
                vlSelf->__PVT__root_unit__DOT__iteration 
                    = (0x3fU & ((IData)(1U) + (IData)(vlSelf->__PVT__root_unit__DOT__iteration)));
            }
        } else if (((9U == (IData)(vlSelf->__PVT__state)) 
                    & (IData)(vlSelf->__PVT__root_ready))) {
            vlSelf->__PVT__root_unit__DOT__radicand_shift[0U] 
                = vlSelf->__PVT__mean[0U];
            vlSelf->__PVT__root_unit__DOT__radicand_shift[1U] 
                = vlSelf->__PVT__mean[1U];
            vlSelf->__PVT__root_unit__DOT__radicand_shift[2U] 
                = vlSelf->__PVT__mean[2U];
            vlSelf->__PVT__root_unit__DOT__radicand_shift[3U] 
                = vlSelf->__PVT__mean[3U];
            __Vdly__root_unit__DOT__root_work = 0ULL;
            vlSelf->__PVT__root_unit__DOT__iteration = 0U;
            vlSelf->__PVT__root_unit__DOT__remainder_work[0U] = 0U;
            vlSelf->__PVT__root_unit__DOT__remainder_work[1U] = 0U;
            vlSelf->__PVT__root_unit__DOT__remainder_work[2U] = 0U;
            vlSelf->__PVT__root_unit__DOT__remainder_work[3U] = 0U;
            vlSelf->__PVT__root_unit__DOT__remainder_work[4U] = 0U;
            __Vdly__root_unit__DOT__state = 1U;
        }
        if ((2U & (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__state))) {
                if (((IData)(vlSelf->__PVT__divide_valid) 
                     & ((7U == (IData)(vlSelf->__PVT__state)) 
                        | (0xcU == (IData)(vlSelf->__PVT__state))))) {
                    __Vdly__divider__DOT__divider__DOT__state = 0U;
                }
            } else {
                if (vlSelf->__PVT__divider__DOT__divider__DOT__zero_divisor) {
                    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[0U] = 0U;
                    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[1U] = 0U;
                    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[2U] = 0U;
                    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[3U] = 0U;
                } else {
                    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[0U] 
                        = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[0U];
                    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[1U] 
                        = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[1U];
                    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[2U] 
                        = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[2U];
                    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[3U] 
                        = vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[3U];
                }
                __Vdly__divider__DOT__divider__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__state))) {
            VL_SHIFTL_WWI(128,128,32, __Vtemp_6, vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift, 1U);
            vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[0U] 
                = __Vtemp_6[0U];
            vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[1U] 
                = __Vtemp_6[1U];
            vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[2U] 
                = __Vtemp_6[2U];
            vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[3U] 
                = __Vtemp_6[3U];
            if (vlSelf->__PVT__divider__DOT__divider__DOT__subtract) {
                VL_SHIFTL_WWI(128,128,32, __Vtemp_8, vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work, 1U);
                __Vdly__divider__DOT__divider__DOT__quotient_work[0U] 
                    = (1U | __Vtemp_8[0U]);
                __Vdly__divider__DOT__divider__DOT__quotient_work[1U] 
                    = __Vtemp_8[1U];
                __Vdly__divider__DOT__divider__DOT__quotient_work[2U] 
                    = __Vtemp_8[2U];
                __Vdly__divider__DOT__divider__DOT__quotient_work[3U] 
                    = __Vtemp_8[3U];
                __Vtemp_10[0U] = vlSelf->__PVT__divider__DOT__divider__DOT__divisor[0U];
                __Vtemp_10[1U] = vlSelf->__PVT__divider__DOT__divider__DOT__divisor[1U];
                __Vtemp_10[2U] = vlSelf->__PVT__divider__DOT__divider__DOT__divisor[2U];
                __Vtemp_10[3U] = vlSelf->__PVT__divider__DOT__divider__DOT__divisor[3U];
                __Vtemp_10[4U] = 0U;
                VL_SUB_W(5, __Vtemp_11, vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_10);
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = __Vtemp_11[0U];
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = __Vtemp_11[1U];
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = __Vtemp_11[2U];
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[3U] 
                    = __Vtemp_11[3U];
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[4U] 
                    = (1U & __Vtemp_11[4U]);
            } else {
                VL_SHIFTL_WWI(128,128,32, __Vdly__divider__DOT__divider__DOT__quotient_work, vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work, 1U);
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[0U] 
                    = vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[0U];
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[1U] 
                    = vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[1U];
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[2U] 
                    = vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[2U];
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[3U] 
                    = vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[3U];
                vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[4U] 
                    = vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[4U];
            }
            if ((0x7fU == (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__iterations))) {
                __Vdly__divider__DOT__divider__DOT__state = 2U;
            } else {
                vlSelf->__PVT__divider__DOT__divider__DOT__iterations 
                    = (0xffU & ((IData)(1U) + (IData)(vlSelf->__PVT__divider__DOT__divider__DOT__iterations)));
            }
        } else if ((((6U == (IData)(vlSelf->__PVT__state)) 
                     | (0xbU == (IData)(vlSelf->__PVT__state))) 
                    & (IData)(vlSelf->__PVT__divide_ready))) {
            vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[0U] = 0U;
            if ((6U == (IData)(vlSelf->__PVT__state))) {
                vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[1U] 
                    = vlSelf->__PVT__sum[0U];
                vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[2U] 
                    = vlSelf->__PVT__sum[1U];
                vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[3U] 
                    = vlSelf->__PVT__sum[2U];
            } else {
                vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[1U] = 0U;
                vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[2U] = 1U;
                vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[3U] = 0U;
            }
            __Vdly__divider__DOT__divider__DOT__quotient_work[0U] = 0U;
            __Vdly__divider__DOT__divider__DOT__quotient_work[1U] = 0U;
            __Vdly__divider__DOT__divider__DOT__quotient_work[2U] = 0U;
            __Vdly__divider__DOT__divider__DOT__quotient_work[3U] = 0U;
            vlSelf->__PVT__divider__DOT__divider__DOT__iterations = 0U;
            vlSelf->__PVT__divider__DOT__divider__DOT__divisor[0U] 
                = vlSelf->__Vcellinp__divider__denominator[0U];
            vlSelf->__PVT__divider__DOT__divider__DOT__divisor[1U] 
                = vlSelf->__Vcellinp__divider__denominator[1U];
            vlSelf->__PVT__divider__DOT__divider__DOT__divisor[2U] 
                = vlSelf->__Vcellinp__divider__denominator[2U];
            vlSelf->__PVT__divider__DOT__divider__DOT__divisor[3U] 
                = vlSelf->__Vcellinp__divider__denominator[3U];
            vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
            vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
            vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
            vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[3U] = 0U;
            vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[4U] = 0U;
            vlSelf->__PVT__divider__DOT__divider__DOT__zero_divisor 
                = (0U == (((vlSelf->__Vcellinp__divider__denominator[0U] 
                            | vlSelf->__Vcellinp__divider__denominator[1U]) 
                           | vlSelf->__Vcellinp__divider__denominator[2U]) 
                          | vlSelf->__Vcellinp__divider__denominator[3U]));
            __Vdly__divider__DOT__divider__DOT__state = 1U;
        }
        if (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__busy) {
            __Vtemp_17[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                                            >> 0x10U));
            __Vtemp_17[1U] = 0U;
            __Vtemp_17[2U] = 0U;
            __Vtemp_17[3U] = 0U;
            __Vtemp_17[4U] = 0U;
            __Vtemp_17[5U] = 0U;
            __Vtemp_17[6U] = 0U;
            __Vtemp_17[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered, __Vtemp_17, 0xe0U);
            __Vtemp_18[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U]));
            __Vtemp_18[1U] = 0U;
            __Vtemp_18[2U] = 0U;
            __Vtemp_18[3U] = 0U;
            __Vtemp_18[4U] = 0U;
            __Vtemp_18[5U] = 0U;
            __Vtemp_18[6U] = 0U;
            __Vtemp_18[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered, __Vtemp_18, 0xd0U);
            __Vtemp_19[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                                            >> 0x10U));
            __Vtemp_19[1U] = 0U;
            __Vtemp_19[2U] = 0U;
            __Vtemp_19[3U] = 0U;
            __Vtemp_19[4U] = 0U;
            __Vtemp_19[5U] = 0U;
            __Vtemp_19[6U] = 0U;
            __Vtemp_19[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered, __Vtemp_19, 0xc0U);
            __Vtemp_20[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U]));
            __Vtemp_20[1U] = 0U;
            __Vtemp_20[2U] = 0U;
            __Vtemp_20[3U] = 0U;
            __Vtemp_20[4U] = 0U;
            __Vtemp_20[5U] = 0U;
            __Vtemp_20[6U] = 0U;
            __Vtemp_20[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered, __Vtemp_20, 0xb0U);
            __Vtemp_21[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                                            >> 0x10U));
            __Vtemp_21[1U] = 0U;
            __Vtemp_21[2U] = 0U;
            __Vtemp_21[3U] = 0U;
            __Vtemp_21[4U] = 0U;
            __Vtemp_21[5U] = 0U;
            __Vtemp_21[6U] = 0U;
            __Vtemp_21[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_21, 0xa0U);
            __Vtemp_22[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U]));
            __Vtemp_22[1U] = 0U;
            __Vtemp_22[2U] = 0U;
            __Vtemp_22[3U] = 0U;
            __Vtemp_22[4U] = 0U;
            __Vtemp_22[5U] = 0U;
            __Vtemp_22[6U] = 0U;
            __Vtemp_22[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_22, 0x90U);
            __Vtemp_23[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                                            >> 0x10U));
            __Vtemp_23[1U] = 0U;
            __Vtemp_23[2U] = 0U;
            __Vtemp_23[3U] = 0U;
            __Vtemp_23[4U] = 0U;
            __Vtemp_23[5U] = 0U;
            __Vtemp_23[6U] = 0U;
            __Vtemp_23[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_23, 0x80U);
            __Vtemp_24[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U]));
            __Vtemp_24[1U] = 0U;
            __Vtemp_24[2U] = 0U;
            __Vtemp_24[3U] = 0U;
            __Vtemp_24[4U] = 0U;
            __Vtemp_24[5U] = 0U;
            __Vtemp_24[6U] = 0U;
            __Vtemp_24[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_24, 0x70U);
            __Vtemp_25[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                                 >> 0x10U));
            __Vtemp_25[1U] = 0U;
            __Vtemp_25[2U] = 0U;
            __Vtemp_25[3U] = 0U;
            __Vtemp_25[4U] = 0U;
            __Vtemp_25[5U] = 0U;
            __Vtemp_25[6U] = 0U;
            __Vtemp_25[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered, __Vtemp_25, 0xd0U);
            __Vtemp_26[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U]));
            __Vtemp_26[1U] = 0U;
            __Vtemp_26[2U] = 0U;
            __Vtemp_26[3U] = 0U;
            __Vtemp_26[4U] = 0U;
            __Vtemp_26[5U] = 0U;
            __Vtemp_26[6U] = 0U;
            __Vtemp_26[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered, __Vtemp_26, 0xc0U);
            __Vtemp_27[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                                 >> 0x10U));
            __Vtemp_27[1U] = 0U;
            __Vtemp_27[2U] = 0U;
            __Vtemp_27[3U] = 0U;
            __Vtemp_27[4U] = 0U;
            __Vtemp_27[5U] = 0U;
            __Vtemp_27[6U] = 0U;
            __Vtemp_27[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered, __Vtemp_27, 0xb0U);
            __Vtemp_28[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U]));
            __Vtemp_28[1U] = 0U;
            __Vtemp_28[2U] = 0U;
            __Vtemp_28[3U] = 0U;
            __Vtemp_28[4U] = 0U;
            __Vtemp_28[5U] = 0U;
            __Vtemp_28[6U] = 0U;
            __Vtemp_28[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered, __Vtemp_28, 0xa0U);
            __Vtemp_29[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                                 >> 0x10U));
            __Vtemp_29[1U] = 0U;
            __Vtemp_29[2U] = 0U;
            __Vtemp_29[3U] = 0U;
            __Vtemp_29[4U] = 0U;
            __Vtemp_29[5U] = 0U;
            __Vtemp_29[6U] = 0U;
            __Vtemp_29[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_29, 0x90U);
            __Vtemp_30[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U]));
            __Vtemp_30[1U] = 0U;
            __Vtemp_30[2U] = 0U;
            __Vtemp_30[3U] = 0U;
            __Vtemp_30[4U] = 0U;
            __Vtemp_30[5U] = 0U;
            __Vtemp_30[6U] = 0U;
            __Vtemp_30[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_30, 0x80U);
            __Vtemp_31[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                                 >> 0x10U));
            __Vtemp_31[1U] = 0U;
            __Vtemp_31[2U] = 0U;
            __Vtemp_31[3U] = 0U;
            __Vtemp_31[4U] = 0U;
            __Vtemp_31[5U] = 0U;
            __Vtemp_31[6U] = 0U;
            __Vtemp_31[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_31, 0x70U);
            __Vtemp_32[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U]));
            __Vtemp_32[1U] = 0U;
            __Vtemp_32[2U] = 0U;
            __Vtemp_32[3U] = 0U;
            __Vtemp_32[4U] = 0U;
            __Vtemp_32[5U] = 0U;
            __Vtemp_32[6U] = 0U;
            __Vtemp_32[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_32, 0x60U);
            __Vtemp_33[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                                            >> 0x10U));
            __Vtemp_33[1U] = 0U;
            __Vtemp_33[2U] = 0U;
            __Vtemp_33[3U] = 0U;
            __Vtemp_33[4U] = 0U;
            __Vtemp_33[5U] = 0U;
            __Vtemp_33[6U] = 0U;
            __Vtemp_33[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered, __Vtemp_33, 0xc0U);
            __Vtemp_34[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U]));
            __Vtemp_34[1U] = 0U;
            __Vtemp_34[2U] = 0U;
            __Vtemp_34[3U] = 0U;
            __Vtemp_34[4U] = 0U;
            __Vtemp_34[5U] = 0U;
            __Vtemp_34[6U] = 0U;
            __Vtemp_34[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered, __Vtemp_34, 0xb0U);
            __Vtemp_35[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                                            >> 0x10U));
            __Vtemp_35[1U] = 0U;
            __Vtemp_35[2U] = 0U;
            __Vtemp_35[3U] = 0U;
            __Vtemp_35[4U] = 0U;
            __Vtemp_35[5U] = 0U;
            __Vtemp_35[6U] = 0U;
            __Vtemp_35[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered, __Vtemp_35, 0xa0U);
            __Vtemp_36[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U]));
            __Vtemp_36[1U] = 0U;
            __Vtemp_36[2U] = 0U;
            __Vtemp_36[3U] = 0U;
            __Vtemp_36[4U] = 0U;
            __Vtemp_36[5U] = 0U;
            __Vtemp_36[6U] = 0U;
            __Vtemp_36[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered, __Vtemp_36, 0x90U);
            __Vtemp_37[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                                            >> 0x10U));
            __Vtemp_37[1U] = 0U;
            __Vtemp_37[2U] = 0U;
            __Vtemp_37[3U] = 0U;
            __Vtemp_37[4U] = 0U;
            __Vtemp_37[5U] = 0U;
            __Vtemp_37[6U] = 0U;
            __Vtemp_37[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_37, 0x80U);
            __Vtemp_38[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U]));
            __Vtemp_38[1U] = 0U;
            __Vtemp_38[2U] = 0U;
            __Vtemp_38[3U] = 0U;
            __Vtemp_38[4U] = 0U;
            __Vtemp_38[5U] = 0U;
            __Vtemp_38[6U] = 0U;
            __Vtemp_38[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_38, 0x70U);
            __Vtemp_39[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                                            >> 0x10U));
            __Vtemp_39[1U] = 0U;
            __Vtemp_39[2U] = 0U;
            __Vtemp_39[3U] = 0U;
            __Vtemp_39[4U] = 0U;
            __Vtemp_39[5U] = 0U;
            __Vtemp_39[6U] = 0U;
            __Vtemp_39[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_39, 0x60U);
            __Vtemp_40[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U]));
            __Vtemp_40[1U] = 0U;
            __Vtemp_40[2U] = 0U;
            __Vtemp_40[3U] = 0U;
            __Vtemp_40[4U] = 0U;
            __Vtemp_40[5U] = 0U;
            __Vtemp_40[6U] = 0U;
            __Vtemp_40[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_40, 0x50U);
            __Vtemp_41[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                                 >> 0x10U));
            __Vtemp_41[1U] = 0U;
            __Vtemp_41[2U] = 0U;
            __Vtemp_41[3U] = 0U;
            __Vtemp_41[4U] = 0U;
            __Vtemp_41[5U] = 0U;
            __Vtemp_41[6U] = 0U;
            __Vtemp_41[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered, __Vtemp_41, 0xb0U);
            __Vtemp_42[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U]));
            __Vtemp_42[1U] = 0U;
            __Vtemp_42[2U] = 0U;
            __Vtemp_42[3U] = 0U;
            __Vtemp_42[4U] = 0U;
            __Vtemp_42[5U] = 0U;
            __Vtemp_42[6U] = 0U;
            __Vtemp_42[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered, __Vtemp_42, 0xa0U);
            __Vtemp_43[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                                 >> 0x10U));
            __Vtemp_43[1U] = 0U;
            __Vtemp_43[2U] = 0U;
            __Vtemp_43[3U] = 0U;
            __Vtemp_43[4U] = 0U;
            __Vtemp_43[5U] = 0U;
            __Vtemp_43[6U] = 0U;
            __Vtemp_43[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered, __Vtemp_43, 0x90U);
            __Vtemp_44[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U]));
            __Vtemp_44[1U] = 0U;
            __Vtemp_44[2U] = 0U;
            __Vtemp_44[3U] = 0U;
            __Vtemp_44[4U] = 0U;
            __Vtemp_44[5U] = 0U;
            __Vtemp_44[6U] = 0U;
            __Vtemp_44[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered, __Vtemp_44, 0x80U);
            __Vtemp_45[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                                 >> 0x10U));
            __Vtemp_45[1U] = 0U;
            __Vtemp_45[2U] = 0U;
            __Vtemp_45[3U] = 0U;
            __Vtemp_45[4U] = 0U;
            __Vtemp_45[5U] = 0U;
            __Vtemp_45[6U] = 0U;
            __Vtemp_45[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_45, 0x70U);
            __Vtemp_46[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U]));
            __Vtemp_46[1U] = 0U;
            __Vtemp_46[2U] = 0U;
            __Vtemp_46[3U] = 0U;
            __Vtemp_46[4U] = 0U;
            __Vtemp_46[5U] = 0U;
            __Vtemp_46[6U] = 0U;
            __Vtemp_46[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_46, 0x60U);
            __Vtemp_47[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                                 >> 0x10U));
            __Vtemp_47[1U] = 0U;
            __Vtemp_47[2U] = 0U;
            __Vtemp_47[3U] = 0U;
            __Vtemp_47[4U] = 0U;
            __Vtemp_47[5U] = 0U;
            __Vtemp_47[6U] = 0U;
            __Vtemp_47[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_47, 0x50U);
            __Vtemp_48[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U]));
            __Vtemp_48[1U] = 0U;
            __Vtemp_48[2U] = 0U;
            __Vtemp_48[3U] = 0U;
            __Vtemp_48[4U] = 0U;
            __Vtemp_48[5U] = 0U;
            __Vtemp_48[6U] = 0U;
            __Vtemp_48[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_48, 0x40U);
            __Vtemp_49[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                                            >> 0x10U));
            __Vtemp_49[1U] = 0U;
            __Vtemp_49[2U] = 0U;
            __Vtemp_49[3U] = 0U;
            __Vtemp_49[4U] = 0U;
            __Vtemp_49[5U] = 0U;
            __Vtemp_49[6U] = 0U;
            __Vtemp_49[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered, __Vtemp_49, 0xa0U);
            __Vtemp_50[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U]));
            __Vtemp_50[1U] = 0U;
            __Vtemp_50[2U] = 0U;
            __Vtemp_50[3U] = 0U;
            __Vtemp_50[4U] = 0U;
            __Vtemp_50[5U] = 0U;
            __Vtemp_50[6U] = 0U;
            __Vtemp_50[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered, __Vtemp_50, 0x90U);
            __Vtemp_51[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                                            >> 0x10U));
            __Vtemp_51[1U] = 0U;
            __Vtemp_51[2U] = 0U;
            __Vtemp_51[3U] = 0U;
            __Vtemp_51[4U] = 0U;
            __Vtemp_51[5U] = 0U;
            __Vtemp_51[6U] = 0U;
            __Vtemp_51[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered, __Vtemp_51, 0x80U);
            __Vtemp_52[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U]));
            __Vtemp_52[1U] = 0U;
            __Vtemp_52[2U] = 0U;
            __Vtemp_52[3U] = 0U;
            __Vtemp_52[4U] = 0U;
            __Vtemp_52[5U] = 0U;
            __Vtemp_52[6U] = 0U;
            __Vtemp_52[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered, __Vtemp_52, 0x70U);
            __Vtemp_53[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                                            >> 0x10U));
            __Vtemp_53[1U] = 0U;
            __Vtemp_53[2U] = 0U;
            __Vtemp_53[3U] = 0U;
            __Vtemp_53[4U] = 0U;
            __Vtemp_53[5U] = 0U;
            __Vtemp_53[6U] = 0U;
            __Vtemp_53[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_53, 0x60U);
            __Vtemp_54[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U]));
            __Vtemp_54[1U] = 0U;
            __Vtemp_54[2U] = 0U;
            __Vtemp_54[3U] = 0U;
            __Vtemp_54[4U] = 0U;
            __Vtemp_54[5U] = 0U;
            __Vtemp_54[6U] = 0U;
            __Vtemp_54[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_54, 0x50U);
            __Vtemp_55[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                                            >> 0x10U));
            __Vtemp_55[1U] = 0U;
            __Vtemp_55[2U] = 0U;
            __Vtemp_55[3U] = 0U;
            __Vtemp_55[4U] = 0U;
            __Vtemp_55[5U] = 0U;
            __Vtemp_55[6U] = 0U;
            __Vtemp_55[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_55, 0x40U);
            __Vtemp_56[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U]));
            __Vtemp_56[1U] = 0U;
            __Vtemp_56[2U] = 0U;
            __Vtemp_56[3U] = 0U;
            __Vtemp_56[4U] = 0U;
            __Vtemp_56[5U] = 0U;
            __Vtemp_56[6U] = 0U;
            __Vtemp_56[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_56, 0x30U);
            __Vtemp_57[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                                 >> 0x10U));
            __Vtemp_57[1U] = 0U;
            __Vtemp_57[2U] = 0U;
            __Vtemp_57[3U] = 0U;
            __Vtemp_57[4U] = 0U;
            __Vtemp_57[5U] = 0U;
            __Vtemp_57[6U] = 0U;
            __Vtemp_57[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered, __Vtemp_57, 0x90U);
            __Vtemp_58[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U]));
            __Vtemp_58[1U] = 0U;
            __Vtemp_58[2U] = 0U;
            __Vtemp_58[3U] = 0U;
            __Vtemp_58[4U] = 0U;
            __Vtemp_58[5U] = 0U;
            __Vtemp_58[6U] = 0U;
            __Vtemp_58[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered, __Vtemp_58, 0x80U);
            __Vtemp_59[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                                 >> 0x10U));
            __Vtemp_59[1U] = 0U;
            __Vtemp_59[2U] = 0U;
            __Vtemp_59[3U] = 0U;
            __Vtemp_59[4U] = 0U;
            __Vtemp_59[5U] = 0U;
            __Vtemp_59[6U] = 0U;
            __Vtemp_59[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered, __Vtemp_59, 0x70U);
            __Vtemp_60[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U]));
            __Vtemp_60[1U] = 0U;
            __Vtemp_60[2U] = 0U;
            __Vtemp_60[3U] = 0U;
            __Vtemp_60[4U] = 0U;
            __Vtemp_60[5U] = 0U;
            __Vtemp_60[6U] = 0U;
            __Vtemp_60[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered, __Vtemp_60, 0x60U);
            __Vtemp_61[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                                 >> 0x10U));
            __Vtemp_61[1U] = 0U;
            __Vtemp_61[2U] = 0U;
            __Vtemp_61[3U] = 0U;
            __Vtemp_61[4U] = 0U;
            __Vtemp_61[5U] = 0U;
            __Vtemp_61[6U] = 0U;
            __Vtemp_61[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_61, 0x50U);
            __Vtemp_62[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U]));
            __Vtemp_62[1U] = 0U;
            __Vtemp_62[2U] = 0U;
            __Vtemp_62[3U] = 0U;
            __Vtemp_62[4U] = 0U;
            __Vtemp_62[5U] = 0U;
            __Vtemp_62[6U] = 0U;
            __Vtemp_62[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_62, 0x40U);
            __Vtemp_63[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                                 >> 0x10U));
            __Vtemp_63[1U] = 0U;
            __Vtemp_63[2U] = 0U;
            __Vtemp_63[3U] = 0U;
            __Vtemp_63[4U] = 0U;
            __Vtemp_63[5U] = 0U;
            __Vtemp_63[6U] = 0U;
            __Vtemp_63[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_63, 0x30U);
            __Vtemp_64[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U]));
            __Vtemp_64[1U] = 0U;
            __Vtemp_64[2U] = 0U;
            __Vtemp_64[3U] = 0U;
            __Vtemp_64[4U] = 0U;
            __Vtemp_64[5U] = 0U;
            __Vtemp_64[6U] = 0U;
            __Vtemp_64[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_64, 0x20U);
            __Vtemp_65[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                                            >> 0x10U));
            __Vtemp_65[1U] = 0U;
            __Vtemp_65[2U] = 0U;
            __Vtemp_65[3U] = 0U;
            __Vtemp_65[4U] = 0U;
            __Vtemp_65[5U] = 0U;
            __Vtemp_65[6U] = 0U;
            __Vtemp_65[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered, __Vtemp_65, 0x80U);
            __Vtemp_66[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U]));
            __Vtemp_66[1U] = 0U;
            __Vtemp_66[2U] = 0U;
            __Vtemp_66[3U] = 0U;
            __Vtemp_66[4U] = 0U;
            __Vtemp_66[5U] = 0U;
            __Vtemp_66[6U] = 0U;
            __Vtemp_66[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered, __Vtemp_66, 0x70U);
            __Vtemp_67[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                                            >> 0x10U));
            __Vtemp_67[1U] = 0U;
            __Vtemp_67[2U] = 0U;
            __Vtemp_67[3U] = 0U;
            __Vtemp_67[4U] = 0U;
            __Vtemp_67[5U] = 0U;
            __Vtemp_67[6U] = 0U;
            __Vtemp_67[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered, __Vtemp_67, 0x60U);
            __Vtemp_68[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U]));
            __Vtemp_68[1U] = 0U;
            __Vtemp_68[2U] = 0U;
            __Vtemp_68[3U] = 0U;
            __Vtemp_68[4U] = 0U;
            __Vtemp_68[5U] = 0U;
            __Vtemp_68[6U] = 0U;
            __Vtemp_68[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered, __Vtemp_68, 0x50U);
            __Vtemp_69[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                                            >> 0x10U));
            __Vtemp_69[1U] = 0U;
            __Vtemp_69[2U] = 0U;
            __Vtemp_69[3U] = 0U;
            __Vtemp_69[4U] = 0U;
            __Vtemp_69[5U] = 0U;
            __Vtemp_69[6U] = 0U;
            __Vtemp_69[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_69, 0x40U);
            __Vtemp_70[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U]));
            __Vtemp_70[1U] = 0U;
            __Vtemp_70[2U] = 0U;
            __Vtemp_70[3U] = 0U;
            __Vtemp_70[4U] = 0U;
            __Vtemp_70[5U] = 0U;
            __Vtemp_70[6U] = 0U;
            __Vtemp_70[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_70, 0x30U);
            __Vtemp_71[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                               >> 0x10U) * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                                            >> 0x10U));
            __Vtemp_71[1U] = 0U;
            __Vtemp_71[2U] = 0U;
            __Vtemp_71[3U] = 0U;
            __Vtemp_71[4U] = 0U;
            __Vtemp_71[5U] = 0U;
            __Vtemp_71[6U] = 0U;
            __Vtemp_71[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_71, 0x20U);
            __Vtemp_72[0U] = ((vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                               >> 0x10U) * (0xffffU 
                                            & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U]));
            __Vtemp_72[1U] = 0U;
            __Vtemp_72[2U] = 0U;
            __Vtemp_72[3U] = 0U;
            __Vtemp_72[4U] = 0U;
            __Vtemp_72[5U] = 0U;
            __Vtemp_72[6U] = 0U;
            __Vtemp_72[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered, __Vtemp_72, 0x10U);
            __Vtemp_73[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                                 >> 0x10U));
            __Vtemp_73[1U] = 0U;
            __Vtemp_73[2U] = 0U;
            __Vtemp_73[3U] = 0U;
            __Vtemp_73[4U] = 0U;
            __Vtemp_73[5U] = 0U;
            __Vtemp_73[6U] = 0U;
            __Vtemp_73[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered, __Vtemp_73, 0x70U);
            __Vtemp_74[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U]));
            __Vtemp_74[1U] = 0U;
            __Vtemp_74[2U] = 0U;
            __Vtemp_74[3U] = 0U;
            __Vtemp_74[4U] = 0U;
            __Vtemp_74[5U] = 0U;
            __Vtemp_74[6U] = 0U;
            __Vtemp_74[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered, __Vtemp_74, 0x60U);
            __Vtemp_75[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                                 >> 0x10U));
            __Vtemp_75[1U] = 0U;
            __Vtemp_75[2U] = 0U;
            __Vtemp_75[3U] = 0U;
            __Vtemp_75[4U] = 0U;
            __Vtemp_75[5U] = 0U;
            __Vtemp_75[6U] = 0U;
            __Vtemp_75[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered, __Vtemp_75, 0x50U);
            __Vtemp_76[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U]));
            __Vtemp_76[1U] = 0U;
            __Vtemp_76[2U] = 0U;
            __Vtemp_76[3U] = 0U;
            __Vtemp_76[4U] = 0U;
            __Vtemp_76[5U] = 0U;
            __Vtemp_76[6U] = 0U;
            __Vtemp_76[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered, __Vtemp_76, 0x40U);
            __Vtemp_77[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                                 >> 0x10U));
            __Vtemp_77[1U] = 0U;
            __Vtemp_77[2U] = 0U;
            __Vtemp_77[3U] = 0U;
            __Vtemp_77[4U] = 0U;
            __Vtemp_77[5U] = 0U;
            __Vtemp_77[6U] = 0U;
            __Vtemp_77[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered, __Vtemp_77, 0x30U);
            __Vtemp_78[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U]) 
                              * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U]));
            __Vtemp_78[1U] = 0U;
            __Vtemp_78[2U] = 0U;
            __Vtemp_78[3U] = 0U;
            __Vtemp_78[4U] = 0U;
            __Vtemp_78[5U] = 0U;
            __Vtemp_78[6U] = 0U;
            __Vtemp_78[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered, __Vtemp_78, 0x20U);
            __Vtemp_79[0U] = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U]) 
                              * (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                                 >> 0x10U));
            __Vtemp_79[1U] = 0U;
            __Vtemp_79[2U] = 0U;
            __Vtemp_79[3U] = 0U;
            __Vtemp_79[4U] = 0U;
            __Vtemp_79[5U] = 0U;
            __Vtemp_79[6U] = 0U;
            __Vtemp_79[7U] = 0U;
            VL_SHIFTL_WWI(256,256,32, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered, __Vtemp_79, 0x10U);
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
                = ((0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U]) 
                   * (0xffffU & vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U]));
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] = 0U;
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] = 0U;
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] = 0U;
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] = 0U;
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] = 0U;
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] = 0U;
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] = 0U;
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [5U][0U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [5U][1U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [4U][2U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [4U][3U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [4U][0U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [4U][1U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [3U][6U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [3U][7U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [3U][4U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [3U][5U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [3U][2U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [3U][3U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [3U][0U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [3U][1U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][0xeU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][0xfU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][0xcU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][0xdU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][0xaU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][0xbU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][8U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][9U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][6U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][7U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][4U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][5U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][2U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][3U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][0U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [2U][1U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x1eU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x1fU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x1cU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x1dU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x1aU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x1bU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x18U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x19U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x16U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x17U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x14U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x15U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x12U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x13U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x10U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0x11U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0xeU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0xfU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0xcU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0xdU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0xaU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0xbU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][8U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][9U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][6U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][7U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][4U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][5U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][2U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][3U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][0U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [1U][1U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x3eU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x3fU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x3cU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x3dU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x3aU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x3bU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x38U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x39U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x36U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x37U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x34U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x35U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x32U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x33U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x30U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x31U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x2eU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x2fU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x2cU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x2dU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x2aU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x2bU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x28U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x29U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x26U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x27U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x24U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x25U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x22U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x23U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x20U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x21U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x1eU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x1fU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x1cU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x1dU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x1aU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x1bU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x18U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x19U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x16U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x17U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x14U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x15U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x12U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x13U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x10U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0x11U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0xeU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0xfU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0xcU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0xdU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0xaU], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0xbU]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][8U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][9U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][6U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][7U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][4U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][5U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][2U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][3U]);
            VL_ADD_W(8, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum, 
                     vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][0U], vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                     [0U][1U]);
        }
        if ((0U == (IData)(vlSelf->__PVT__memory_port__DOT__state))) {
            if (vlSelf->__PVT__issue) {
                vlSelf->__PVT__memory_port__DOT__wr 
                    = vlSelf->__PVT__write_request;
                vlSelf->__PVT__memory_port__DOT__kd 
                    = vlSelf->__PVT__kind;
                vlSelf->__PVT__memory_port__DOT__pj = 0U;
                vlSelf->__PVT__memory_port__DOT__ly 
                    = vlSelf->__PVT__memory_layer;
                vlSelf->__PVT__memory_port__DOT__rw 
                    = vlSelf->__PVT__row;
                vlSelf->__PVT__memory_port__DOT__cl 
                    = vlSelf->__PVT__index;
                vlSelf->__PVT__memory_port__DOT__wd 
                    = vlSelf->__PVT__write_data;
                __Vdly__memory_port__DOT__state = 1U;
            }
        } else if ((1U == (IData)(vlSelf->__PVT__memory_port__DOT__state))) {
            if (((IData)(vlSelf->mem_req_valid) & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber11))) {
                __Vdly__memory_port__DOT__state = 2U;
            }
        } else if ((2U == (IData)(vlSelf->__PVT__memory_port__DOT__state))) {
            if (((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber19) 
                 & (IData)(vlSelf->mem_rsp_ready))) {
                __Vdly__memory_port__DOT__state = 0U;
            }
        } else {
            __Vdly__memory_port__DOT__state = 0U;
        }
        __Vdly__multiplier__DOT__multiplier__DOT__valid_pipe 
            = (0xffU & VL_SHIFTL_III(8,8,32, (IData)(vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_pipe), 1U));
        if (((IData)(vlSelf->__Vcellinp__multiplier__in_valid) 
             & (IData)(vlSelf->__PVT__multiply_ready))) {
            __Vdly__multiplier__DOT__multiplier__DOT__valid_pipe 
                = (1U | (IData)(__Vdly__multiplier__DOT__multiplier__DOT__valid_pipe));
        }
        if ((0x80U & (IData)(vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_pipe))) {
            VL_NEGATE_W(8, __Vtemp_80, vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                        [6U][0U]);
            if (vlSelf->__PVT__multiplier__DOT__multiplier__DOT__negative) {
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[0U] 
                    = __Vtemp_80[0U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[1U] 
                    = __Vtemp_80[1U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[2U] 
                    = __Vtemp_80[2U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[3U] 
                    = __Vtemp_80[3U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[4U] 
                    = __Vtemp_80[4U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[5U] 
                    = __Vtemp_80[5U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[6U] 
                    = __Vtemp_80[6U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[7U] 
                    = __Vtemp_80[7U];
            } else {
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[0U] 
                    = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                    [6U][0U][0U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[1U] 
                    = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                    [6U][0U][1U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[2U] 
                    = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                    [6U][0U][2U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[3U] 
                    = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                    [6U][0U][3U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[4U] 
                    = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                    [6U][0U][4U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[5U] 
                    = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                    [6U][0U][5U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[6U] 
                    = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                    [6U][0U][6U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[7U] 
                    = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree
                    [6U][0U][7U];
            }
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_result = 1U;
        }
        if (((IData)(vlSelf->__PVT__multiply_valid) 
             & (IData)(vlSelf->__Vcellinp__multiplier__out_ready))) {
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_result = 0U;
        }
    } else {
        vlSelf->__PVT__root_unit__DOT__radicand_shift[0U] = 0U;
        vlSelf->__PVT__root_unit__DOT__radicand_shift[1U] = 0U;
        vlSelf->__PVT__root_unit__DOT__radicand_shift[2U] = 0U;
        vlSelf->__PVT__root_unit__DOT__radicand_shift[3U] = 0U;
        __Vdly__root_unit__DOT__root_work = 0ULL;
        vlSelf->__PVT__root_unit__DOT__iteration = 0U;
        __Vdly__root_unit__DOT__state = 0U;
        vlSelf->__PVT__root_unit__DOT__remainder_work[0U] = 0U;
        vlSelf->__PVT__root_unit__DOT__remainder_work[1U] = 0U;
        vlSelf->__PVT__root_unit__DOT__remainder_work[2U] = 0U;
        vlSelf->__PVT__root_unit__DOT__remainder_work[3U] = 0U;
        vlSelf->__PVT__root_unit__DOT__remainder_work[4U] = 0U;
        vlSelf->__PVT__root_unit__DOT__root_result = 0ULL;
        vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[0U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[1U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[2U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[3U] = 0U;
        __Vdly__divider__DOT__divider__DOT__quotient_work[0U] = 0U;
        __Vdly__divider__DOT__divider__DOT__quotient_work[1U] = 0U;
        __Vdly__divider__DOT__divider__DOT__quotient_work[2U] = 0U;
        __Vdly__divider__DOT__divider__DOT__quotient_work[3U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__iterations = 0U;
        __Vdly__divider__DOT__divider__DOT__state = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__divisor[0U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__divisor[1U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__divisor[2U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__divisor[3U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[0U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[1U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[2U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[3U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work[4U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[0U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[1U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[2U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__quotient_result[3U] = 0U;
        vlSelf->__PVT__divider__DOT__divider__DOT__zero_divisor = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        __Vdly__memory_port__DOT__state = 0U;
        vlSelf->__PVT__memory_port__DOT__wr = 0U;
        vlSelf->__PVT__memory_port__DOT__kd = 0U;
        vlSelf->__PVT__memory_port__DOT__pj = 0U;
        vlSelf->__PVT__memory_port__DOT__ly = 0U;
        vlSelf->__PVT__memory_port__DOT__rw = 0U;
        vlSelf->__PVT__memory_port__DOT__cl = 0U;
        vlSelf->__PVT__memory_port__DOT__wd = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_result = 0U;
        __Vdly__multiplier__DOT__multiplier__DOT__valid_pipe = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__result[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[0U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[0U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[1U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[1U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[2U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[2U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[3U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[3U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[4U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[4U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[5U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[5U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[6U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[6U];
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[7U] 
            = Vbench__ConstPool__CONST_h9e67c271_0[7U];
    }
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        if (vlSelf->__PVT__fault) {
            vlSelf->__PVT__failed = 1U;
            __Vdly__state = 0x18U;
        } else if ((0x10U & (IData)(vlSelf->__PVT__state))) {
            if ((8U & (IData)(vlSelf->__PVT__state))) {
                if ((4U & (IData)(vlSelf->__PVT__state))) {
                    vlSelf->__PVT__failed = 1U;
                    __Vdly__state = 0x18U;
                } else if ((2U & (IData)(vlSelf->__PVT__state))) {
                    vlSelf->__PVT__failed = 1U;
                    __Vdly__state = 0x18U;
                } else {
                    __Vdly__state = ((1U & (IData)(vlSelf->__PVT__state))
                                      ? 0x18U : 0U);
                }
            } else if ((4U & (IData)(vlSelf->__PVT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__state))) {
                        if (vlSelf->__PVT__complete) {
                            if ((8U > ((IData)(1U) 
                                       + vlSelf->__PVT__index))) {
                                __Vdly__index = ((IData)(1U) 
                                                 + vlSelf->__PVT__index);
                                __Vdly__state = 0xdU;
                            } else {
                                __Vdly__state = 0x18U;
                            }
                        }
                    } else if (vlSelf->__PVT__issue) {
                        __Vdly__state = 0x17U;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__state))) {
                    __Vfunc_round_shift__7__x[0U] = 
                        vlSelf->__PVT__scale_product[0U];
                    __Vfunc_round_shift__7__x[1U] = 
                        vlSelf->__PVT__scale_product[1U];
                    __Vfunc_round_shift__7__x[2U] = 
                        vlSelf->__PVT__scale_product[2U];
                    __Vfunc_round_shift__7__x[3U] = 
                        vlSelf->__PVT__scale_product[3U];
                    __Vtemp_82[0U] = 0U;
                    __Vtemp_82[1U] = 0U;
                    __Vtemp_82[2U] = 0U;
                    __Vtemp_82[3U] = 0U;
                    __Vtemp_83[0U] = __Vfunc_round_shift__7__x[0U];
                    __Vtemp_83[1U] = __Vfunc_round_shift__7__x[1U];
                    __Vtemp_83[2U] = __Vfunc_round_shift__7__x[2U];
                    __Vtemp_83[3U] = __Vfunc_round_shift__7__x[3U];
                    __Vtemp_83[4U] = (__Vfunc_round_shift__7__x[3U] 
                                      >> 0x1fU);
                    VL_NEGATE_W(5, __Vtemp_84, __Vtemp_83);
                    if (VL_GTS_IWW(128, __Vtemp_82, __Vfunc_round_shift__7__x)) {
                        __Vfunc_round_shift__7__magnitude[0U] 
                            = __Vtemp_84[0U];
                        __Vfunc_round_shift__7__magnitude[1U] 
                            = __Vtemp_84[1U];
                        __Vfunc_round_shift__7__magnitude[2U] 
                            = __Vtemp_84[2U];
                        __Vfunc_round_shift__7__magnitude[3U] 
                            = __Vtemp_84[3U];
                        __Vfunc_round_shift__7__magnitude[4U] 
                            = (1U & __Vtemp_84[4U]);
                    } else {
                        __Vfunc_round_shift__7__magnitude[0U] 
                            = __Vfunc_round_shift__7__x[0U];
                        __Vfunc_round_shift__7__magnitude[1U] 
                            = __Vfunc_round_shift__7__x[1U];
                        __Vfunc_round_shift__7__magnitude[2U] 
                            = __Vfunc_round_shift__7__x[2U];
                        __Vfunc_round_shift__7__magnitude[3U] 
                            = __Vfunc_round_shift__7__x[3U];
                        __Vfunc_round_shift__7__magnitude[4U] = 0U;
                    }
                    __Vdly__state = 0x16U;
                    __Vtemp_91[0U] = 0U;
                    __Vtemp_91[1U] = 0x8000U;
                    __Vtemp_91[2U] = 0U;
                    __Vtemp_91[3U] = 0U;
                    __Vtemp_91[4U] = 0U;
                    VL_ADD_W(5, __Vtemp_92, __Vtemp_91, __Vfunc_round_shift__7__magnitude);
                    __Vtemp_93[0U] = __Vtemp_92[0U];
                    __Vtemp_93[1U] = __Vtemp_92[1U];
                    __Vtemp_93[2U] = __Vtemp_92[2U];
                    __Vtemp_93[3U] = __Vtemp_92[3U];
                    __Vtemp_93[4U] = (1U & __Vtemp_92[4U]);
                    VL_SHIFTR_WWI(129,129,32, __Vtemp_94, __Vtemp_93, 0x30U);
                    __Vfunc_round_shift__7__magnitude[0U] 
                        = __Vtemp_94[0U];
                    __Vfunc_round_shift__7__magnitude[1U] 
                        = __Vtemp_94[1U];
                    __Vfunc_round_shift__7__magnitude[2U] 
                        = __Vtemp_94[2U];
                    __Vfunc_round_shift__7__magnitude[3U] 
                        = __Vtemp_94[3U];
                    __Vfunc_round_shift__7__magnitude[4U] 
                        = (1U & __Vtemp_94[4U]);
                    __Vtemp_96[0U] = 0U;
                    __Vtemp_96[1U] = 0U;
                    __Vtemp_96[2U] = 0U;
                    __Vtemp_96[3U] = 0U;
                    VL_NEGATE_W(5, __Vtemp_97, __Vfunc_round_shift__7__magnitude);
                    if (VL_GTS_IWW(128, __Vtemp_96, __Vfunc_round_shift__7__x)) {
                        __Vfunc_round_shift__7__Vfuncout[0U] 
                            = __Vtemp_97[0U];
                        __Vfunc_round_shift__7__Vfuncout[1U] 
                            = __Vtemp_97[1U];
                        __Vfunc_round_shift__7__Vfuncout[2U] 
                            = __Vtemp_97[2U];
                        __Vfunc_round_shift__7__Vfuncout[3U] 
                            = __Vtemp_97[3U];
                    } else {
                        __Vfunc_round_shift__7__Vfuncout[0U] 
                            = __Vfunc_round_shift__7__magnitude[0U];
                        __Vfunc_round_shift__7__Vfuncout[1U] 
                            = __Vfunc_round_shift__7__magnitude[1U];
                        __Vfunc_round_shift__7__Vfuncout[2U] 
                            = __Vfunc_round_shift__7__magnitude[2U];
                        __Vfunc_round_shift__7__Vfuncout[3U] 
                            = __Vfunc_round_shift__7__magnitude[3U];
                    }
                    __Vfunc_sat32__6__x[0U] = __Vfunc_round_shift__7__Vfuncout[0U];
                    __Vfunc_sat32__6__x[1U] = __Vfunc_round_shift__7__Vfuncout[1U];
                    __Vfunc_sat32__6__x[2U] = __Vfunc_round_shift__7__Vfuncout[2U];
                    __Vfunc_sat32__6__x[3U] = __Vfunc_round_shift__7__Vfuncout[3U];
                    __Vtemp_101[0U] = 0x7fffffffU;
                    __Vtemp_101[1U] = 0U;
                    __Vtemp_101[2U] = 0U;
                    __Vtemp_101[3U] = 0U;
                    __Vtemp_102[0U] = 0x80000000U;
                    __Vtemp_102[1U] = 0xffffffffU;
                    __Vtemp_102[2U] = 0xffffffffU;
                    __Vtemp_102[3U] = 0xffffffffU;
                    __Vfunc_sat32__6__Vfuncout = (VL_LTS_IWW(128, __Vtemp_101, __Vfunc_sat32__6__x)
                                                   ? 0x7fffffffU
                                                   : 
                                                  (VL_GTS_IWW(128, __Vtemp_102, __Vfunc_sat32__6__x)
                                                    ? 0x80000000U
                                                    : 
                                                   __Vfunc_sat32__6__x[0U]));
                    vlSelf->__PVT__output_value = __Vfunc_sat32__6__Vfuncout;
                } else if (vlSelf->__PVT__multiply_valid) {
                    vlSelf->__PVT__scale_product[0U] 
                        = vlSelf->__PVT__product[0U];
                    vlSelf->__PVT__scale_product[1U] 
                        = vlSelf->__PVT__product[1U];
                    vlSelf->__PVT__scale_product[2U] 
                        = vlSelf->__PVT__product[2U];
                    vlSelf->__PVT__scale_product[3U] 
                        = vlSelf->__PVT__product[3U];
                    __Vdly__state = 0x15U;
                }
            } else if ((2U & (IData)(vlSelf->__PVT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__state))) {
                    if (vlSelf->__PVT__multiply_ready) {
                        __Vdly__state = 0x14U;
                    }
                } else if (vlSelf->__PVT__multiply_valid) {
                    vlSelf->__PVT__norm_product = (
                                                   ((QData)((IData)(
                                                                    vlSelf->__PVT__product[1U])) 
                                                    << 0x20U) 
                                                   | (QData)((IData)(
                                                                     vlSelf->__PVT__product[0U])));
                    __Vdly__state = 0x13U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__state))) {
                if (vlSelf->__PVT__multiply_ready) {
                    __Vdly__state = 0x12U;
                }
            } else if (vlSelf->__PVT__complete) {
                if (([&]() {
                            __Vfunc_f16_invalid__8__h 
                                = (0xffffU & vlSelf->__PVT__read_data);
                            __Vfunc_f16_invalid__8__Vfuncout 
                                = (0x1fU == (0x1fU 
                                             & ((IData)(__Vfunc_f16_invalid__8__h) 
                                                >> 0xaU)));
                        }(), (IData)(__Vfunc_f16_invalid__8__Vfuncout))) {
                    vlSelf->__PVT__failed = 1U;
                    __Vdly__state = 0x18U;
                } else {
                    __Vfunc_f16_q16__9__h = (0xffffU 
                                             & vlSelf->__PVT__read_data);
                    __Vfunc_f16_scale__10__h = __Vfunc_f16_q16__9__h;
                    __Vdly__state = 0x11U;
                    if ((0U == (0x1fU & ((IData)(__Vfunc_f16_scale__10__h) 
                                         >> 0xaU)))) {
                        __Vfunc_f16_scale__10__magnitude 
                            = (0x3ffU & (IData)(__Vfunc_f16_scale__10__h));
                        __Vfunc_f16_scale__10__shift = 0xfffffff8U;
                    } else {
                        __Vfunc_f16_scale__10__magnitude 
                            = (0x400U | (0x3ffU & (IData)(__Vfunc_f16_scale__10__h)));
                        __Vfunc_f16_scale__10__shift 
                            = ((0x1fU & ((IData)(__Vfunc_f16_scale__10__h) 
                                         >> 0xaU)) 
                               - (IData)(9U));
                    }
                    __Vfunc_f16_scale__10__magnitude 
                        = (VL_LTES_III(32, 0U, __Vfunc_f16_scale__10__shift)
                            ? VL_SHIFTL_III(32,32,32, __Vfunc_f16_scale__10__magnitude, __Vfunc_f16_scale__10__shift)
                            : VL_SHIFTR_III(32,32,32, 
                                            (__Vfunc_f16_scale__10__magnitude 
                                             + VL_SHIFTL_III(32,32,32, (IData)(1U), 
                                                             ((- __Vfunc_f16_scale__10__shift) 
                                                              - (IData)(1U)))), 
                                            (- __Vfunc_f16_scale__10__shift)));
                    __Vfunc_f16_scale__10__Vfuncout 
                        = __Vfunc_f16_scale__10__magnitude;
                    __Vfunc_f16_q16__9__magnitude = __Vfunc_f16_scale__10__Vfuncout;
                    __Vfunc_f16_q16__9__signed_value 
                        = (0x1ffffffffULL & ((0x8000U 
                                              & (IData)(__Vfunc_f16_q16__9__h))
                                              ? (- (QData)((IData)(__Vfunc_f16_q16__9__magnitude)))
                                              : (QData)((IData)(__Vfunc_f16_q16__9__magnitude))));
                    __Vfunc_sat32__11__x[0U] = (IData)(__Vfunc_f16_q16__9__signed_value);
                    __Vfunc_sat32__11__x[1U] = (((- (IData)(
                                                            (1U 
                                                             & (IData)(
                                                                       (__Vfunc_f16_q16__9__signed_value 
                                                                        >> 0x20U))))) 
                                                 << 1U) 
                                                | (IData)(
                                                          (__Vfunc_f16_q16__9__signed_value 
                                                           >> 0x20U)));
                    __Vfunc_sat32__11__x[2U] = (((- (IData)(
                                                            (1U 
                                                             & (IData)(
                                                                       (__Vfunc_f16_q16__9__signed_value 
                                                                        >> 0x20U))))) 
                                                 >> 0x1fU) 
                                                | ((- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (__Vfunc_f16_q16__9__signed_value 
                                                                          >> 0x20U))))) 
                                                   << 1U));
                    __Vfunc_sat32__11__x[3U] = (((- (IData)(
                                                            (1U 
                                                             & (IData)(
                                                                       (__Vfunc_f16_q16__9__signed_value 
                                                                        >> 0x20U))))) 
                                                 >> 0x1fU) 
                                                | ((- (IData)(
                                                              (1U 
                                                               & (IData)(
                                                                         (__Vfunc_f16_q16__9__signed_value 
                                                                          >> 0x20U))))) 
                                                   << 1U));
                    __Vtemp_107[0U] = 0x7fffffffU;
                    __Vtemp_107[1U] = 0U;
                    __Vtemp_107[2U] = 0U;
                    __Vtemp_107[3U] = 0U;
                    __Vtemp_108[0U] = 0x80000000U;
                    __Vtemp_108[1U] = 0xffffffffU;
                    __Vtemp_108[2U] = 0xffffffffU;
                    __Vtemp_108[3U] = 0xffffffffU;
                    __Vfunc_sat32__11__Vfuncout = (
                                                   VL_LTS_IWW(128, __Vtemp_107, __Vfunc_sat32__11__x)
                                                    ? 0x7fffffffU
                                                    : 
                                                   (VL_GTS_IWW(128, __Vtemp_108, __Vfunc_sat32__11__x)
                                                     ? 0x80000000U
                                                     : 
                                                    __Vfunc_sat32__11__x[0U]));
                    __Vfunc_f16_q16__9__Vfuncout = __Vfunc_sat32__11__Vfuncout;
                    vlSelf->__PVT__gamma = __Vfunc_f16_q16__9__Vfuncout;
                }
            }
        } else if ((8U & (IData)(vlSelf->__PVT__state))) {
            if ((4U & (IData)(vlSelf->__PVT__state))) {
                if ((2U & (IData)(vlSelf->__PVT__state))) {
                    if ((1U & (IData)(vlSelf->__PVT__state))) {
                        if (vlSelf->__PVT__issue) {
                            __Vdly__state = 0x10U;
                        }
                    } else if (vlSelf->__PVT__complete) {
                        vlSelf->__PVT__x = vlSelf->__PVT__read_data;
                        __Vdly__state = 0xfU;
                    }
                } else if ((1U & (IData)(vlSelf->__PVT__state))) {
                    if (vlSelf->__PVT__issue) {
                        __Vdly__state = 0xeU;
                    }
                } else if (vlSelf->__PVT__divide_valid) {
                    if (vlSelf->__PVT__divide_by_zero) {
                        vlSelf->__PVT__failed = 1U;
                        __Vdly__state = 0x18U;
                    } else {
                        __Vdly__index = 0U;
                        vlSelf->__PVT__reciprocal = 
                            (((QData)((IData)(vlSelf->__PVT__quotient[1U])) 
                              << 0x20U) | (QData)((IData)(
                                                          vlSelf->__PVT__quotient[0U])));
                        __Vdly__state = 0xdU;
                    }
                }
            } else if ((2U & (IData)(vlSelf->__PVT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__state))) {
                    if (vlSelf->__PVT__divide_ready) {
                        __Vdly__state = 0xcU;
                    }
                } else if (vlSelf->__PVT__root_valid) {
                    if ((0ULL == vlSelf->__PVT__root_value)) {
                        vlSelf->__PVT__failed = 1U;
                        __Vdly__state = 0x18U;
                    } else {
                        vlSelf->__PVT__denominator 
                            = vlSelf->__PVT__root_value;
                        __Vdly__state = 0xbU;
                    }
                }
            } else if ((1U & (IData)(vlSelf->__PVT__state))) {
                if (vlSelf->__PVT__root_ready) {
                    __Vdly__state = 0xaU;
                }
            } else {
                __Vtemp_110[0U] = 0xf7a0b5eeU;
                __Vtemp_110[1U] = 0x10c6U;
                __Vtemp_110[2U] = 0U;
                __Vtemp_110[3U] = 0U;
                VL_ADD_W(4, __Vtemp_109, __Vtemp_110, vlSelf->__PVT__mean);
                vlSelf->__PVT__mean[0U] = __Vtemp_109[0U];
                vlSelf->__PVT__mean[1U] = __Vtemp_109[1U];
                vlSelf->__PVT__mean[2U] = __Vtemp_109[2U];
                vlSelf->__PVT__mean[3U] = __Vtemp_109[3U];
                __Vdly__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->__PVT__state))) {
            if ((2U & (IData)(vlSelf->__PVT__state))) {
                if ((1U & (IData)(vlSelf->__PVT__state))) {
                    if (vlSelf->__PVT__divide_valid) {
                        if (vlSelf->__PVT__divide_by_zero) {
                            vlSelf->__PVT__failed = 1U;
                            __Vdly__state = 0x18U;
                        } else {
                            vlSelf->__PVT__mean[0U] 
                                = vlSelf->__PVT__quotient[0U];
                            vlSelf->__PVT__mean[1U] 
                                = vlSelf->__PVT__quotient[1U];
                            vlSelf->__PVT__mean[2U] 
                                = vlSelf->__PVT__quotient[2U];
                            vlSelf->__PVT__mean[3U] 
                                = vlSelf->__PVT__quotient[3U];
                            __Vdly__state = 8U;
                        }
                    }
                } else if (vlSelf->__PVT__divide_ready) {
                    __Vdly__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->__PVT__state))) {
                __Vtemp_112[0U] = (IData)(vlSelf->__PVT__square_value);
                __Vtemp_112[1U] = (IData)((vlSelf->__PVT__square_value 
                                           >> 0x20U));
                __Vtemp_112[2U] = 0U;
                VL_ADD_W(3, __Vtemp_111, vlSelf->__PVT__sum, __Vtemp_112);
                vlSelf->__PVT__sum[0U] = __Vtemp_111[0U];
                vlSelf->__PVT__sum[1U] = __Vtemp_111[1U];
                vlSelf->__PVT__sum[2U] = __Vtemp_111[2U];
                if ((8U > ((IData)(1U) + vlSelf->__PVT__index))) {
                    __Vdly__index = ((IData)(1U) + vlSelf->__PVT__index);
                    __Vdly__state = 1U;
                } else {
                    __Vdly__state = 6U;
                }
            } else if (vlSelf->__PVT__multiply_valid) {
                vlSelf->__PVT__square_value = (((QData)((IData)(
                                                                vlSelf->__PVT__product[1U])) 
                                                << 0x20U) 
                                               | (QData)((IData)(
                                                                 vlSelf->__PVT__product[0U])));
                __Vdly__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->__PVT__state))) {
            if ((1U & (IData)(vlSelf->__PVT__state))) {
                if (vlSelf->__PVT__multiply_ready) {
                    __Vdly__state = 4U;
                }
            } else if (vlSelf->__PVT__complete) {
                vlSelf->__PVT__x = vlSelf->__PVT__read_data;
                __Vdly__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->__PVT__state))) {
            if (vlSelf->__PVT__issue) {
                __Vdly__state = 2U;
            }
        } else if ((((IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____VdfgTmp_h25e570cc__0) 
                     & (0U == vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__selected)) 
                    & (IData)(vlSelf->cmd_ready))) {
            __Vdly__index = 0U;
            vlSelf->__PVT__sum[0U] = 0U;
            vlSelf->__PVT__sum[1U] = 0U;
            vlSelf->__PVT__sum[2U] = 0U;
            vlSelf->__PVT__failed = 0U;
            vlSelf->__PVT__layer = vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__layer;
            if ((((2U < (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__norm_mode)) 
                  | (1U <= vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__layer)) 
                 | (4U <= vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__position))) {
                vlSelf->__PVT__failed = 1U;
                __Vdly__state = 0x19U;
            } else {
                vlSelf->__PVT__source_slot = ((1U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__norm_mode))
                                               ? 7U
                                               : 0U);
                if ((0U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__norm_mode))) {
                    vlSelf->__PVT__target_slot = 1U;
                    vlSelf->__PVT__norm_kind = 5U;
                } else if ((1U == (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT__norm_mode))) {
                    vlSelf->__PVT__target_slot = 8U;
                    vlSelf->__PVT__norm_kind = 6U;
                } else {
                    vlSelf->__PVT__target_slot = 0xeU;
                    vlSelf->__PVT__norm_kind = 7U;
                }
                __Vdly__state = 1U;
            }
        }
    } else {
        __Vdly__index = 0U;
        vlSelf->__PVT__sum[0U] = 0U;
        vlSelf->__PVT__sum[1U] = 0U;
        vlSelf->__PVT__sum[2U] = 0U;
        vlSelf->__PVT__mean[0U] = 0U;
        vlSelf->__PVT__mean[1U] = 0U;
        vlSelf->__PVT__mean[2U] = 0U;
        vlSelf->__PVT__mean[3U] = 0U;
        __Vdly__state = 0U;
        vlSelf->__PVT__failed = 0U;
        vlSelf->__PVT__layer = 0U;
        vlSelf->__PVT__source_slot = 0U;
        vlSelf->__PVT__target_slot = 0U;
        vlSelf->__PVT__norm_kind = 0U;
        vlSelf->__PVT__square_value = 0ULL;
        vlSelf->__PVT__reciprocal = 0ULL;
        vlSelf->__PVT__denominator = 0ULL;
        vlSelf->__PVT__x = 0U;
        vlSelf->__PVT__gamma = 0U;
        vlSelf->__PVT__output_value = 0U;
        vlSelf->__PVT__norm_product = 0ULL;
        vlSelf->__PVT__scale_product[0U] = 0U;
        vlSelf->__PVT__scale_product[1U] = 0U;
        vlSelf->__PVT__scale_product[2U] = 0U;
        vlSelf->__PVT__scale_product[3U] = 0U;
    }
    vlSelf->__PVT__root_unit__DOT__root_work = __Vdly__root_unit__DOT__root_work;
    vlSelf->__PVT__root_unit__DOT__state = __Vdly__root_unit__DOT__state;
    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[0U] 
        = __Vdly__divider__DOT__divider__DOT__quotient_work[0U];
    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[1U] 
        = __Vdly__divider__DOT__divider__DOT__quotient_work[1U];
    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[2U] 
        = __Vdly__divider__DOT__divider__DOT__quotient_work[2U];
    vlSelf->__PVT__divider__DOT__divider__DOT__quotient_work[3U] 
        = __Vdly__divider__DOT__divider__DOT__quotient_work[3U];
    vlSelf->__PVT__divider__DOT__divider__DOT__state 
        = __Vdly__divider__DOT__divider__DOT__state;
    vlSelf->__PVT__memory_port__DOT__state = __Vdly__memory_port__DOT__state;
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__valid_pipe 
        = __Vdly__multiplier__DOT__multiplier__DOT__valid_pipe;
    vlSelf->__PVT__index = __Vdly__index;
    vlSelf->__PVT__state = __Vdly__state;
    vlSelf->__PVT__root_unit__DOT__trial[0U] = (1U 
                                                | ((IData)(vlSelf->__PVT__root_unit__DOT__root_work) 
                                                   << 2U));
    vlSelf->__PVT__root_unit__DOT__trial[1U] = (((IData)(vlSelf->__PVT__root_unit__DOT__root_work) 
                                                 >> 0x1eU) 
                                                | ((IData)(
                                                           (vlSelf->__PVT__root_unit__DOT__root_work 
                                                            >> 0x20U)) 
                                                   << 2U));
    vlSelf->__PVT__root_unit__DOT__trial[2U] = ((IData)(
                                                        (vlSelf->__PVT__root_unit__DOT__root_work 
                                                         >> 0x20U)) 
                                                >> 0x1eU);
    vlSelf->__PVT__root_unit__DOT__trial[3U] = 0U;
    vlSelf->__PVT__root_unit__DOT__trial[4U] = 0U;
    VL_SHIFTL_WWI(130,130,32, __Vtemp_115, vlSelf->__PVT__root_unit__DOT__remainder_work, 2U);
    vlSelf->__PVT__root_unit__DOT__shifted_remainder[0U] 
        = (__Vtemp_115[0U] | (vlSelf->__PVT__root_unit__DOT__radicand_shift[3U] 
                              >> 0x1eU));
    vlSelf->__PVT__root_unit__DOT__shifted_remainder[1U] 
        = __Vtemp_115[1U];
    vlSelf->__PVT__root_unit__DOT__shifted_remainder[2U] 
        = __Vtemp_115[2U];
    vlSelf->__PVT__root_unit__DOT__shifted_remainder[3U] 
        = __Vtemp_115[3U];
    vlSelf->__PVT__root_unit__DOT__shifted_remainder[4U] 
        = (3U & __Vtemp_115[4U]);
    VL_SHIFTL_WWI(129,129,32, __Vtemp_119, vlSelf->__PVT__divider__DOT__divider__DOT__remainder_work, 1U);
    vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[0U] 
        = (__Vtemp_119[0U] | (vlSelf->__PVT__divider__DOT__divider__DOT__dividend_shift[3U] 
                              >> 0x1fU));
    vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[1U] 
        = __Vtemp_119[1U];
    vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[2U] 
        = __Vtemp_119[2U];
    vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[3U] 
        = __Vtemp_119[3U];
    vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder[4U] 
        = (1U & __Vtemp_119[4U]);
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3fU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3fU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3fU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3fU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3fU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3fU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3fU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3fU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3eU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3eU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3eU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3eU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3eU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3eU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3eU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3eU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3dU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3dU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3dU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3dU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3dU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3dU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3dU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3dU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3cU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3cU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3cU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3cU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3cU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3cU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3cU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3cU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3bU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3bU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3bU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3bU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3bU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3bU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3bU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3bU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3aU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3aU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3aU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3aU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3aU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3aU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3aU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x3aU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x39U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x39U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x39U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x39U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x39U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x39U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x39U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x39U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x38U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x38U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x38U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x38U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x38U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x38U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x38U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x38U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__7__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x37U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x37U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x37U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x37U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x37U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x37U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x37U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x37U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x36U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x36U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x36U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x36U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x36U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x36U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x36U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x36U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x35U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x35U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x35U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x35U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x35U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x35U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x35U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x35U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x34U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x34U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x34U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x34U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x34U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x34U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x34U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x34U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x33U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x33U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x33U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x33U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x33U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x33U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x33U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x33U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x32U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x32U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x32U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x32U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x32U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x32U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x32U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x32U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x31U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x31U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x31U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x31U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x31U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x31U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x31U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x31U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x30U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x30U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x30U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x30U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x30U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x30U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x30U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x30U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__6__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2fU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2fU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2fU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2fU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2fU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2fU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2fU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2fU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2eU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2eU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2eU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2eU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2eU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2eU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2eU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2eU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2dU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2dU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2dU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2dU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2dU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2dU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2dU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2dU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2cU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2cU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2cU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2cU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2cU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2cU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2cU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2cU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2bU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2bU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2bU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2bU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2bU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2bU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2bU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2bU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2aU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2aU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2aU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2aU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2aU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2aU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2aU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x2aU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x29U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x29U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x29U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x29U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x29U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x29U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x29U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x29U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x28U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x28U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x28U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x28U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x28U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x28U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x28U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x28U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__5__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x27U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x27U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x27U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x27U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x27U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x27U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x27U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x27U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x26U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x26U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x26U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x26U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x26U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x26U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x26U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x26U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x25U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x25U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x25U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x25U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x25U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x25U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x25U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x25U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x24U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x24U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x24U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x24U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x24U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x24U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x24U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x24U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x23U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x23U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x23U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x23U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x23U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x23U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x23U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x23U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x22U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x22U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x22U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x22U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x22U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x22U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x22U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x22U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x21U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x21U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x21U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x21U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x21U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x21U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x21U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x21U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x20U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x20U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x20U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x20U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x20U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x20U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x20U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x20U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__4__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1fU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1fU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1fU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1fU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1fU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1fU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1fU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1fU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1eU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1eU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1eU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1eU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1eU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1eU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1eU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1eU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1dU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1dU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1dU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1dU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1dU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1dU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1dU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1dU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1cU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1cU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1cU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1cU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1cU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1cU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1cU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1cU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1bU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1bU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1bU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1bU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1bU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1bU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1bU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1bU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1aU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1aU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1aU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1aU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1aU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1aU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1aU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x1aU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x19U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x19U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x19U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x19U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x19U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x19U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x19U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x19U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x18U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x18U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x18U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x18U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x18U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x18U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x18U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x18U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__3__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x17U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x17U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x17U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x17U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x17U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x17U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x17U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x17U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x16U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x16U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x16U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x16U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x16U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x16U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x16U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x16U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x15U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x15U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x15U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x15U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x15U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x15U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x15U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x15U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x14U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x14U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x14U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x14U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x14U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x14U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x14U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x14U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x13U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x13U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x13U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x13U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x13U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x13U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x13U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x13U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x12U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x12U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x12U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x12U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x12U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x12U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x12U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x12U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x11U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x11U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x11U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x11U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x11U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x11U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x11U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x11U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x10U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x10U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x10U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x10U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x10U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x10U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x10U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0x10U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__2__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xfU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xfU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xfU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xfU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xfU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xfU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xfU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xfU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xeU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xeU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xeU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xeU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xeU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xeU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xeU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xeU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xdU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xdU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xdU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xdU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xdU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xdU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xdU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xdU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xcU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xcU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xcU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xcU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xcU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xcU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xcU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xcU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xbU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xbU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xbU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xbU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xbU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xbU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xbU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xbU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xaU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xaU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xaU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xaU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xaU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xaU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xaU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0xaU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][9U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][9U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][9U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][9U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][9U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][9U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][9U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][9U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][8U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][8U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][8U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][8U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][8U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][8U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][8U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][8U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__1__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][7U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][7U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][7U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][7U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][7U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][7U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][7U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][7U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__7__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][6U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][6U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][6U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][6U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][6U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][6U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][6U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][6U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__6__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][5U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][5U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][5U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][5U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][5U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][5U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][5U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][5U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__5__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][4U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][4U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][4U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][4U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][4U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][4U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][4U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][4U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__4__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][3U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][3U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][3U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][3U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][3U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][3U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][3U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][3U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__3__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][2U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][2U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][2U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][2U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][2U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][2U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][2U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][2U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__2__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][1U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][1U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][1U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][1U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__1__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[6U];
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        if (((IData)(vlSelf->__Vcellinp__multiplier__in_valid) 
             & (IData)(vlSelf->__PVT__multiply_ready))) {
            VL_NEGATE_W(4, __Vtemp_122, vlSelf->__PVT__operand_a);
            if ((vlSelf->__PVT__operand_a[3U] >> 0x1fU)) {
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                    = __Vtemp_122[0U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                    = __Vtemp_122[1U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                    = __Vtemp_122[2U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                    = __Vtemp_122[3U];
            } else {
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] 
                    = vlSelf->__PVT__operand_a[0U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] 
                    = vlSelf->__PVT__operand_a[1U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] 
                    = vlSelf->__PVT__operand_a[2U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] 
                    = vlSelf->__PVT__operand_a[3U];
            }
            VL_NEGATE_W(4, __Vtemp_124, vlSelf->__PVT__operand_b);
            if ((vlSelf->__PVT__operand_b[3U] >> 0x1fU)) {
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                    = __Vtemp_124[0U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                    = __Vtemp_124[1U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                    = __Vtemp_124[2U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                    = __Vtemp_124[3U];
            } else {
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] 
                    = vlSelf->__PVT__operand_b[0U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] 
                    = vlSelf->__PVT__operand_b[1U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] 
                    = vlSelf->__PVT__operand_b[2U];
                vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] 
                    = vlSelf->__PVT__operand_b[3U];
            }
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__negative 
                = ((vlSelf->__PVT__operand_a[3U] ^ 
                    vlSelf->__PVT__operand_b[3U]) >> 0x1fU);
        }
    } else {
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_a[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[0U] = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[1U] = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[2U] = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__magnitude_b[3U] = 0U;
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__negative = 0U;
    }
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[0U][0U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__a_limb__BRA__0__KET____DOT__b_limb__BRA__0__KET____DOT__partial_registered[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[6U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[6U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[6U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[6U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    if (vlSymsp->TOP.bench__DOT__rst_n) {
        if (((IData)(vlSelf->__Vcellinp__multiplier__in_valid) 
             & (IData)(vlSelf->__PVT__multiply_ready))) {
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__busy = 1U;
        }
        if (((IData)(vlSelf->__PVT__multiply_valid) 
             & (IData)(vlSelf->__Vcellinp__multiplier__out_ready))) {
            vlSelf->__PVT__multiplier__DOT__multiplier__DOT__busy = 0U;
        }
    } else {
        vlSelf->__PVT__multiplier__DOT__multiplier__DOT__busy = 0U;
    }
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[6U][0U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[6U][0U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[6U][0U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[6U][0U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__6__KET____DOT__adder__BRA__0__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][1U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][1U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][1U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][1U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__1__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][0U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][0U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][0U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[5U][0U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__5__KET____DOT__adder__BRA__0__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][3U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][3U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][3U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][3U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][3U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][3U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][3U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][3U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__3__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][2U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][2U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][2U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][2U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][2U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][2U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][2U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][2U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__2__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][1U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][1U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][1U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][1U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__1__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][0U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][0U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][0U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[4U][0U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__4__KET____DOT__adder__BRA__0__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][7U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][7U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][7U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][7U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][7U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][7U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][7U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][7U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__7__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][6U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][6U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][6U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][6U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][6U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][6U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][6U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][6U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__6__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][5U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][5U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][5U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][5U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][5U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][5U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][5U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][5U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__5__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][4U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][4U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][4U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][4U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][4U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][4U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][4U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][4U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__4__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][3U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][3U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][3U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][3U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][3U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][3U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][3U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][3U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__3__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][2U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][2U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][2U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][2U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][2U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][2U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][2U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][2U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__2__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][1U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][1U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][1U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][1U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__1__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][0U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][0U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][0U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[3U][0U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__3__KET____DOT__adder__BRA__0__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xfU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xfU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xfU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xfU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xfU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xfU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xfU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xfU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__15__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xeU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xeU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xeU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xeU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xeU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xeU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xeU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xeU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__14__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xdU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xdU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xdU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xdU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xdU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xdU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xdU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xdU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__13__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xcU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xcU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xcU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xcU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xcU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xcU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xcU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xcU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__12__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xbU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xbU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xbU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xbU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xbU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xbU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xbU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xbU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__11__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xaU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xaU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xaU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xaU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xaU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xaU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xaU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0xaU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__10__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][9U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][9U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][9U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][9U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][9U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][9U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][9U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][9U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__9__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][8U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][8U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][8U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][8U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][8U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][8U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][8U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][8U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__8__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][7U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][7U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][7U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][7U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][7U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][7U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][7U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][7U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__7__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][6U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][6U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][6U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][6U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][6U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][6U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][6U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][6U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__6__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][5U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][5U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][5U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][5U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][5U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][5U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][5U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][5U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__5__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][4U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][4U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][4U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][4U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][4U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][4U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][4U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][4U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__4__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][3U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][3U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][3U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][3U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][3U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][3U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][3U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][3U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__3__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][2U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][2U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][2U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][2U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][2U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][2U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][2U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][2U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__2__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][1U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][1U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][1U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][1U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__1__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[2U][0U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__2__KET____DOT__adder__BRA__0__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1fU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1fU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1fU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1fU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1fU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1fU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1fU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1fU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__31__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1eU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1eU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1eU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1eU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1eU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1eU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1eU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1eU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__30__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1dU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1dU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1dU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1dU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1dU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1dU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1dU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1dU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__29__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1cU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1cU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1cU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1cU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1cU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1cU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1cU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1cU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__28__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1bU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1bU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1bU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1bU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1bU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1bU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1bU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1bU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__27__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1aU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1aU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1aU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1aU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1aU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1aU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1aU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x1aU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__26__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x19U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x19U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x19U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x19U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x19U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x19U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x19U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x19U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__25__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x18U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x18U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x18U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x18U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x18U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x18U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x18U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x18U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__24__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x17U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x17U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x17U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x17U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x17U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x17U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x17U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x17U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__23__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x16U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x16U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x16U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x16U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x16U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x16U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x16U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x16U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__22__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x15U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x15U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x15U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x15U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x15U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x15U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x15U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x15U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__21__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x14U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x14U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x14U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x14U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x14U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x14U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x14U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x14U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__20__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x13U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x13U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x13U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x13U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x13U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x13U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x13U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x13U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__19__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x12U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x12U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x12U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x12U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x12U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x12U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x12U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x12U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__18__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x11U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x11U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x11U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x11U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x11U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x11U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x11U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x11U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__17__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x10U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x10U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x10U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x10U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x10U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x10U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x10U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0x10U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__16__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xfU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xfU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xfU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xfU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xfU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xfU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xfU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xfU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__15__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xeU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xeU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xeU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xeU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xeU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xeU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xeU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xeU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__14__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xdU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xdU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xdU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xdU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xdU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xdU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xdU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xdU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__13__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xcU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xcU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xcU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xcU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xcU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xcU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xcU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xcU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__12__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xbU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xbU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xbU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xbU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xbU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xbU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xbU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xbU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__11__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xaU][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xaU][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xaU][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xaU][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xaU][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xaU][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xaU][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0xaU][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__10__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][9U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][9U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][9U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][9U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][9U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][9U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][9U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][9U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__9__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][8U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][8U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][8U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][8U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][8U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][8U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][8U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][8U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__8__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][7U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][7U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][7U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][7U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][7U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][7U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][7U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][7U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__7__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][6U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][6U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][6U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][6U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][6U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][6U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][6U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][6U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__6__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][5U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][5U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][5U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][5U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][5U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][5U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][5U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][5U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__5__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][4U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][4U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][4U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][4U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][4U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][4U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][4U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][4U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__4__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][3U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][3U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][3U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][3U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][3U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][3U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][3U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][3U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__3__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][2U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][2U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][2U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][2U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][2U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][2U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][2U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][2U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__2__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][1U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][1U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][1U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][1U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][1U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][1U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][1U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][1U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__1__KET____DOT__sum[7U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0U][0U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[0U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0U][1U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[1U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0U][2U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[2U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0U][3U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[3U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0U][4U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[4U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0U][5U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[5U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0U][6U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[6U];
    vlSelf->__PVT__multiplier__DOT__multiplier__DOT__tree[1U][0U][7U] 
        = vlSelf->__PVT__multiplier__DOT__multiplier__DOT__adder_level__BRA__1__KET____DOT__adder__BRA__0__KET____DOT__sum[7U];
    if ((6U == (IData)(vlSelf->__PVT__state))) {
        vlSelf->__Vcellinp__divider__denominator[0U] = 8U;
        vlSelf->__Vcellinp__divider__denominator[1U] = 0U;
    } else {
        vlSelf->__Vcellinp__divider__denominator[0U] 
            = (IData)(vlSelf->__PVT__denominator);
        vlSelf->__Vcellinp__divider__denominator[1U] 
            = (IData)((vlSelf->__PVT__denominator >> 0x20U));
    }
    vlSelf->__Vcellinp__divider__denominator[2U] = 0U;
    vlSelf->__Vcellinp__divider__denominator[3U] = 0U;
    __Vtemp_130[0U] = (1U | ((IData)(vlSelf->__PVT__root_unit__DOT__root_work) 
                             << 2U));
    __Vtemp_130[1U] = (((IData)(vlSelf->__PVT__root_unit__DOT__root_work) 
                        >> 0x1eU) | ((IData)((vlSelf->__PVT__root_unit__DOT__root_work 
                                              >> 0x20U)) 
                                     << 2U));
    __Vtemp_130[2U] = ((IData)((vlSelf->__PVT__root_unit__DOT__root_work 
                                >> 0x20U)) >> 0x1eU);
    __Vtemp_130[3U] = 0U;
    __Vtemp_130[4U] = 0U;
    vlSelf->__PVT__root_unit__DOT__subtract = VL_GTE_W(5, vlSelf->__PVT__root_unit__DOT__shifted_remainder, __Vtemp_130);
    __Vtemp_131[0U] = vlSelf->__PVT__divider__DOT__divider__DOT__divisor[0U];
    __Vtemp_131[1U] = vlSelf->__PVT__divider__DOT__divider__DOT__divisor[1U];
    __Vtemp_131[2U] = vlSelf->__PVT__divider__DOT__divider__DOT__divisor[2U];
    __Vtemp_131[3U] = vlSelf->__PVT__divider__DOT__divider__DOT__divisor[3U];
    __Vtemp_131[4U] = 0U;
    vlSelf->__PVT__divider__DOT__divider__DOT__subtract 
        = VL_GTE_W(5, vlSelf->__PVT__divider__DOT__divider__DOT__shifted_remainder, __Vtemp_131);
    vlSelf->__Vcellinp__multiplier__out_ready = ((4U 
                                                  == (IData)(vlSelf->__PVT__state)) 
                                                 | ((0x12U 
                                                     == (IData)(vlSelf->__PVT__state)) 
                                                    | (0x14U 
                                                       == (IData)(vlSelf->__PVT__state))));
    vlSelf->__Vcellinp__multiplier__in_valid = ((3U 
                                                 == (IData)(vlSelf->__PVT__state)) 
                                                | ((0x11U 
                                                    == (IData)(vlSelf->__PVT__state)) 
                                                   | (0x13U 
                                                      == (IData)(vlSelf->__PVT__state))));
}
