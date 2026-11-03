// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench__Syms.h"
#include "Vbench_anvil_q1_rmsnorm__N1_H8_M4.h"

extern const VlWide<8>/*255:0*/ Vbench__ConstPool__CONST_h9e67c271_0;

VL_INLINE_OPT void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__0\n"); );
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

VL_INLINE_OPT void Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__2(Vbench_anvil_q1_rmsnorm__N1_H8_M4* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+                Vbench_anvil_q1_rmsnorm__N1_H8_M4___nba_comb__TOP__bench__DOT__dut__DOT__decoder__DOT__norm__2\n"); );
    // Body
    vlSelf->__PVT__complete = ((IData)(vlSelf->mem_rsp_ready) 
                               & (IData)(vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber19));
    if (vlSelf->__PVT__complete) {
        vlSelf->__PVT__fault = vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber22;
        vlSelf->__PVT__read_data = vlSymsp->TOP.bench__DOT__dut__DOT__decoder__DOT____Vcellinp__norm____pinNumber21;
    } else {
        vlSelf->__PVT__fault = 0U;
        vlSelf->__PVT__read_data = 0U;
    }
}
