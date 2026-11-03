// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Design implementation internals
// See Vbench.h for the primary calling header

#include "Vbench__pch.h"
#include "Vbench___024root.h"

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__1(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__1\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__multiply_a 
        = (((9U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
            | (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)))
            ? (QData)((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_rows))
            : (QData)((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_row)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_columns 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__region_columns;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____Vcellinp__index_multiplier__out_ready 
        = ((0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
           | (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____Vcellinp__index_multiplier__in_valid 
        = ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
           | (0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__2(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__2\n"); );
    // Init
    IData/*31:0*/ __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter;
    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter = 0;
    CData/*1:0*/ __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state;
    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state = 0;
    CData/*1:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0;
    __Vdlyvdim0__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0 = 0;
    SData/*8:0*/ __Vdlyvval__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0;
    __Vdlyvval__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0;
    __Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0 = 0;
    CData/*1:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0;
    __Vdlyvdim0__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0 = 0;
    SData/*8:0*/ __Vdlyvval__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0;
    __Vdlyvval__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0 = 0;
    CData/*0:0*/ __Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0;
    __Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0 = 0;
    // Body
    __Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0 = 0U;
    vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_shift 
        = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_shift;
    vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_active 
        = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_active;
    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
        = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter;
    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state 
        = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_state;
    __Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0 = 0U;
    if (vlSelf->bench__DOT__dut__DOT__io_rst_n) {
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__pop) {
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr 
                = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr))
                    ? 0U : (3U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr))));
        }
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__pop) {
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr 
                = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr))
                    ? 0U : (3U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr))));
        }
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__push) {
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT____Vlvbound_h27873815__0 
                = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_in_data;
            if ((2U >= (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__write_ptr))) {
                __Vdlyvval__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0 
                    = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT____Vlvbound_h27873815__0;
                __Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0 = 1U;
                __Vdlyvdim0__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0 
                    = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__write_ptr;
            }
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__write_ptr 
                = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__write_ptr))
                    ? 0U : (3U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__write_ptr))));
        }
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count 
            = (3U & ((2U == (((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__push) 
                              << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__pop)))
                      ? ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count))
                      : ((1U == (((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__push) 
                                  << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__pop)))
                          ? ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count) 
                             - (IData)(1U)) : (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count))));
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count 
            = (3U & ((2U == (((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__push) 
                              << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__pop)))
                      ? ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count))
                      : ((1U == (((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__push) 
                                  << 1U) | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__pop)))
                          ? ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count) 
                             - (IData)(1U)) : (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count))));
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_active) {
            if ((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_counter)) {
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_counter 
                    = (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_counter 
                       - (IData)(1U));
            } else if ((9U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_bit))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_active = 0U;
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_counter = 0U;
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_shift 
                    = (0x200U | (0x1ffU & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_shift) 
                                           >> 1U)));
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_bit 
                    = (0xfU & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_bit)));
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_counter 
                    = (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_divisor 
                       - (IData)(1U));
            }
        } else if ((((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass)) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_valid)) 
                    & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_pop))) {
            vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_shift 
                = (0x200U | (((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo_valid)
                               ? (0xffU & (IData)(vlSelf->__VdfgTmp_h1afe3993__0))
                               : 0U) << 1U));
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_bit = 0U;
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_counter 
                = (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_divisor 
                   - (IData)(1U));
            vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_active = 1U;
        }
        if ((((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass)) 
              & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid)) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__healthy))) {
            if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__receive_open) {
                if ((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes)) {
                    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count 
                        = ((vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count 
                            == (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes 
                                - (IData)(1U))) ? 0U
                            : ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count));
                }
                if ((0U == vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes)) {
                    if ((0xaU != (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte))) {
                        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_byte 
                            = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte;
                    }
                    if ((0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte))) {
                        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid)))) {
                            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__empty_frame_fault = 1U;
                        }
                    }
                    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid 
                        = (0xaU != (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte));
                }
            } else {
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count = 0U;
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid = 0U;
            }
            if ((1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__receive_open)) 
                       | ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_emit) 
                          & (~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_ready)))))) {
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__overflow_fault = 1U;
            }
        }
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__push) {
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT____Vlvbound_h27873815__0 
                = ((((IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n) 
                     & (0xdU == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) 
                    << 8U) | ((IData)(vlSelf->bench__DOT__dut__DOT__text_valid)
                               ? (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_byte)
                               : 0U));
            if ((2U >= (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__write_ptr))) {
                __Vdlyvval__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0 
                    = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT____Vlvbound_h27873815__0;
                __Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0 = 1U;
                __Vdlyvdim0__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0 
                    = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__write_ptr;
            }
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__write_ptr 
                = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__write_ptr))
                    ? 0U : (3U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__write_ptr))));
        }
        if (vlSelf->bench__DOT__dut__DOT__done_r) {
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_closed = 0U;
        } else if ((((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_valid) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_ready)) 
                    & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_in_data) 
                       >> 8U))) {
            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_closed = 1U;
        }
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid = 0U;
        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass)))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_state))) {
                    if ((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter)) {
                        __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                            = (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                               - (IData)(1U));
                    } else {
                        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync) {
                            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte 
                                = vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_shift;
                            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid = 1U;
                        } else {
                            vlSelf->bench__DOT__dut__DOT__edge_io__DOT__framing_fault = 1U;
                        }
                        __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state = 0U;
                    }
                } else if ((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter)) {
                    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                        = (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                           - (IData)(1U));
                } else {
                    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_shift 
                        = (((~ ((IData)(1U) << (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_bit))) 
                            & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_shift)) 
                           | (0xffU & ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync) 
                                       << (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_bit))));
                    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                        = (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_divisor 
                           - (IData)(1U));
                    if ((7U == (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_bit))) {
                        __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state = 3U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_bit 
                            = (7U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_bit)));
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_state))) {
                if ((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter)) {
                    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                        = (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                           - (IData)(1U));
                } else if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync) {
                    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__framing_fault = 1U;
                    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state = 0U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_bit = 0U;
                    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                        = (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_divisor 
                           - (IData)(1U));
                    __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state = 2U;
                }
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_previous) 
                        & (~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync)))) {
                __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
                    = (VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_divisor, 1U) 
                       - (IData)(1U));
                __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state = 1U;
            }
        }
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__paths_idle) {
            if ((4U > vlSelf->bench__DOT__dut__DOT__divisor)) {
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_fault = 1U;
            }
            if ((4U <= vlSelf->bench__DOT__dut__DOT__divisor)) {
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes 
                    = ((IData)(vlSelf->bench__DOT__rst_n)
                        ? vlSelf->bench__DOT__dut__DOT__configuration__DOT__frame_r
                        : 0U);
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_divisor 
                    = vlSelf->bench__DOT__dut__DOT__divisor;
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__write_ptr = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__count = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_shift = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_bit = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_active = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_counter = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_count = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__write_ptr = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_fault = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__overflow_fault = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_byte = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__empty_frame_fault = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_closed = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_bit = 0U;
        __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state = 0U;
        __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_shift = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_byte = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__framing_fault = 0U;
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_divisor = 0x364U;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0) {
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data[__Vdlyvdim0__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0] 
            = __Vdlyvval__bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data__v0;
    }
    if (__Vdlyvset__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0) {
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data[__Vdlyvdim0__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0] 
            = __Vdlyvval__bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data__v0;
    }
    vlSelf->__VdfgTmp_h5b2387d0__0 = ((2U >= (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr))
                                       ? vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__data
                                      [vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__read_ptr]
                                       : (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT____Vxrand_h8d954d18__0));
    vlSelf->__VdfgTmp_h1afe3993__0 = ((2U >= (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr))
                                       ? vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__data
                                      [vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__read_ptr]
                                       : (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT____Vxrand_h8d954d18__0));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_h57a93df3__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__empty_frame_fault) 
           | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_fault));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_counter 
        = __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_counter;
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_state 
        = __Vdly__bench__DOT__dut__DOT__edge_io__DOT__rx_state;
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_emit 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__received_valid) 
           & ((0U != vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_frame_bytes) 
              | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__pending_valid)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__healthy 
        = (1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__framing_fault)) 
                 & (~ ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__overflow_fault) 
                       | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_h57a93df3__0)))));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_previous 
        = ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n))) 
           || (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync 
        = ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n))) 
           || (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_meta));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hf663a351__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_previous) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_sync));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_meta 
        = ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n))) 
           || (IData)(vlSelf->bench__DOT__uart_rx));
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__5(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__5\n"); );
    // Body
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
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__8(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__8\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__exponential_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__exp_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__residual__DOT__silu_unit__DOT__exp_unit__DOT__state;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT____Vcellinp__multiplier__operand_a 
        = (((QData)((IData)((- (IData)((vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand 
                                        >> 0x1fU))))) 
            << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__operand)));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__sigmoid;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__silu_product__DOT__silu_unit__DOT__state;
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
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__10(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__10\n"); );
    // Body
    vlSelf->bench__DOT__spi_command_bits = 0U;
    vlSelf->bench__DOT__command_shift = 0U;
    vlSelf->bench__DOT__flash_bit = 0U;
    vlSelf->bench__DOT__spi_miso = 0U;
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__11(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__11\n"); );
    // Body
    if (((~ (IData)(vlSelf->bench__DOT__spi_cs_n)) 
         & (0x20U == vlSelf->bench__DOT__spi_command_bits))) {
        vlSelf->bench__DOT__spi_miso = (1U & (VL_LTES_III(32, 0x4858U, vlSelf->bench__DOT__flash_address) 
                                              | (vlSelf->bench__DOT__flash
                                                 [(0xffffU 
                                                   & vlSelf->bench__DOT__flash_address)] 
                                                 >> 
                                                 (7U 
                                                  & ((IData)(7U) 
                                                     - vlSelf->bench__DOT__flash_bit)))));
    }
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__12(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__12\n"); );
    // Body
    if (vlSelf->bench__DOT__rst_n) {
        vlSelf->bench__DOT__rng = (vlSelf->bench__DOT__rng 
                                   ^ VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__rng, 0xdU));
        vlSelf->bench__DOT__rng = (vlSelf->bench__DOT__rng 
                                   ^ VL_SHIFTR_III(32,32,32, vlSelf->bench__DOT__rng, 0x11U));
        vlSelf->bench__DOT__rng = (vlSelf->bench__DOT__rng 
                                   ^ VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__rng, 5U));
        vlSelf->bench__DOT__ddr_req_ready = (vlSelf->bench__DOT__rng 
                                             & (0U 
                                                != 
                                                VL_MODDIVS_III(32, vlSelf->bench__DOT__cycle, (IData)(7U))));
        vlSelf->bench__DOT__m_axis_tready = ((vlSelf->bench__DOT__rng 
                                              >> 3U) 
                                             & (0U 
                                                != 
                                                VL_MODDIVS_III(32, vlSelf->bench__DOT__cycle, (IData)(7U))));
        if (((IData)(vlSelf->bench__DOT__pending) & 
             (~ (IData)(vlSelf->bench__DOT__ddr_rsp_valid)))) {
            if ((0U == vlSelf->bench__DOT__delay_count)) {
                vlSelf->bench__DOT__ddr_rsp_rdata = 
                    ((vlSelf->bench__DOT__ddr[(0xffffU 
                                               & ((IData)(3U) 
                                                  + (IData)(vlSelf->bench__DOT__pending_address)))] 
                      << 0x18U) | ((vlSelf->bench__DOT__ddr
                                    [(0xffffU & ((IData)(2U) 
                                                 + (IData)(vlSelf->bench__DOT__pending_address)))] 
                                    << 0x10U) | ((vlSelf->bench__DOT__ddr
                                                  [
                                                  (0xffffU 
                                                   & ((IData)(1U) 
                                                      + (IData)(vlSelf->bench__DOT__pending_address)))] 
                                                  << 8U) 
                                                 | vlSelf->bench__DOT__ddr
                                                 [(0xffffU 
                                                   & (IData)(vlSelf->bench__DOT__pending_address))])));
                vlSelf->bench__DOT__ddr_rsp_error = 0U;
                vlSelf->__Vdly__bench__DOT__ddr_rsp_valid = 1U;
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
    IData/*31:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_inputs;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_inputs = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_outputs = 0;
    IData/*31:0*/ bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_groups;
    bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__projection_groups = 0;
    // Body
    vlSelf->bench__DOT__dut__DOT__publish_error = ((IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__publish_failed) 
                                                   & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (6U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__core_mem_rsp_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__response_error) 
           & (IData)(vlSelf->bench__DOT__rst_n));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__writable_key = 0U;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__expected_format = 0U;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__legal_key = 0U;
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
        vlSelf->bench__DOT__dut__DOT__core_mem_rsp_rdata 
            = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__response_data;
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
        vlSelf->bench__DOT__ddr_req_addr = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_address;
        vlSelf->bench__DOT__ddr_req_wdata = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_data;
        vlSelf->bench__DOT__ddr_req_wstrb = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_strobes;
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_hee8b2130__0 
            = (0x13U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state));
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_ready 
            = ((5U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
               | (0x14U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_valid 
            = ((4U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)) 
               | (0x13U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state)));
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_idle 
            = (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state));
        vlSelf->bench__DOT__dut__DOT__core_mem_rsp_valid 
            = (0x15U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state));
        vlSelf->bench__DOT__cfg_rsp_valid = vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_valid;
        vlSelf->bench__DOT__ddr_req_write = vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__request_write;
        vlSelf->bench__DOT__ddr_req_valid = (4U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state));
        vlSelf->bench__DOT__ddr_rsp_ready = (5U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state));
    } else {
        vlSelf->bench__DOT__dut__DOT__core_mem_rsp_rdata = 0U;
        vlSelf->bench__DOT__ddr_req_addr = 0ULL;
        vlSelf->bench__DOT__ddr_req_wdata = 0U;
        vlSelf->bench__DOT__ddr_req_wstrb = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_hee8b2130__0 = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_ready = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_idle = 0U;
        vlSelf->bench__DOT__dut__DOT__core_mem_rsp_valid = 0U;
        vlSelf->bench__DOT__cfg_rsp_valid = 0U;
        vlSelf->bench__DOT__ddr_req_write = 0U;
        vlSelf->bench__DOT__ddr_req_valid = 0U;
        vlSelf->bench__DOT__ddr_rsp_ready = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__boot_rsp_valid = 
        ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0) 
         & (3U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0) 
           & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)));
    vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0) 
           & (1U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_req_write 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT____VdfgTmp_hee8b2130__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__request_write));
    vlSelf->bench__DOT__dut__DOT__memory_idle = ((IData)(vlSelf->bench__DOT__rst_n) 
                                                 & ((0U 
                                                     == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__state)) 
                                                    & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_idle)));
}

extern const VlWide<40>/*1279:0*/ Vbench__ConstPool__CONST_had224c38_0;
extern const VlWide<32>/*1023:0*/ Vbench__ConstPool__CONST_hd6b7ba52_0;
extern const VlWide<16>/*511:0*/ Vbench__ConstPool__CONST_h93e1b771_0;
extern const VlUnpacked<CData/*2:0*/, 16> Vbench__ConstPool__TABLE_h554b41bf_0;

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__14(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__14\n"); );
    // Init
    CData/*3:0*/ __Vtableidx5;
    __Vtableidx5 = 0;
    IData/*31:0*/ __Vilp;
    // Body
    if (vlSelf->bench__DOT__rst_n) {
        if (vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__publish) {
            if ((1U & (~ ((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_match)) 
                          | (~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__bundle_legal)))))) {
                vlSelf->bench__DOT__dut__DOT__configuration__DOT__frame_r 
                    = vlSelf->bench__DOT__dut__DOT__committed_config[6U];
            }
        } else if (((IData)(vlSelf->bench__DOT__cfg_valid) 
                    & (IData)(vlSelf->bench__DOT__cfg_ready))) {
            if ((1U & (~ ((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__address_known)) 
                          | ((IData)(vlSelf->bench__DOT__cfg_write) 
                             & (((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable)) 
                                 | (~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal))) 
                                | ((0x1cU == vlSelf->bench__DOT__cfg_addr)
                                    ? (~ (IData)(vlSelf->bench__DOT__dut__DOT__reload_allowed))
                                    : (~ (IData)(vlSelf->bench__DOT__dut__DOT__write_allowed))))))))) {
                if (vlSelf->bench__DOT__cfg_write) {
                    if (((((((((4U == vlSelf->bench__DOT__cfg_addr) 
                               | (8U == vlSelf->bench__DOT__cfg_addr)) 
                              | (0xcU == vlSelf->bench__DOT__cfg_addr)) 
                             | (0x10U == vlSelf->bench__DOT__cfg_addr)) 
                            | (0x14U == vlSelf->bench__DOT__cfg_addr)) 
                           | (0x18U == vlSelf->bench__DOT__cfg_addr)) 
                          | (0x1cU == vlSelf->bench__DOT__cfg_addr)) 
                         | (0x24U == vlSelf->bench__DOT__cfg_addr))) {
                        if ((4U != vlSelf->bench__DOT__cfg_addr)) {
                            if ((8U != vlSelf->bench__DOT__cfg_addr)) {
                                if ((0xcU != vlSelf->bench__DOT__cfg_addr)) {
                                    if ((0x10U != vlSelf->bench__DOT__cfg_addr)) {
                                        if ((0x14U 
                                             != vlSelf->bench__DOT__cfg_addr)) {
                                            if ((0x18U 
                                                 != vlSelf->bench__DOT__cfg_addr)) {
                                                if (
                                                    (0x1cU 
                                                     != vlSelf->bench__DOT__cfg_addr)) {
                                                    vlSelf->bench__DOT__dut__DOT__configuration__DOT__frame_r 
                                                        = vlSelf->bench__DOT__cfg_wdata;
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        if ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__publish)))) {
            if (((IData)(vlSelf->bench__DOT__cfg_valid) 
                 & (IData)(vlSelf->bench__DOT__cfg_ready))) {
                vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_error = 0U;
                if ((1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__address_known)) 
                           | ((IData)(vlSelf->bench__DOT__cfg_write) 
                              & (((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable)) 
                                  | (~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal))) 
                                 | ((0x1cU == vlSelf->bench__DOT__cfg_addr)
                                     ? (~ (IData)(vlSelf->bench__DOT__dut__DOT__reload_allowed))
                                     : (~ (IData)(vlSelf->bench__DOT__dut__DOT__write_allowed)))))))) {
                    vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_error = 1U;
                }
                vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_data = 0U;
                if ((1U & (~ ((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__address_known)) 
                              | ((IData)(vlSelf->bench__DOT__cfg_write) 
                                 & (((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable)) 
                                     | (~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal))) 
                                    | ((0x1cU == vlSelf->bench__DOT__cfg_addr)
                                        ? (~ (IData)(vlSelf->bench__DOT__dut__DOT__reload_allowed))
                                        : (~ (IData)(vlSelf->bench__DOT__dut__DOT__write_allowed))))))))) {
                    if ((1U & (~ (IData)(vlSelf->bench__DOT__cfg_write)))) {
                        vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_data 
                            = vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value;
                    }
                }
            }
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage) 
             & ((5U >= (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected))
                 ? ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__stage_error) 
                    >> (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected))
                 : (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d96565c__2)))) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__code 
                = (0xffU & ((0x2fU >= (0x3fU & VL_SHIFTL_III(6,32,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected), 3U)))
                             ? (IData)((vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__stage_codes 
                                        >> (0x3fU & 
                                            VL_SHIFTL_III(6,32,32, (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected), 3U))))
                             : (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vxrand_h8d94df49__0)));
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_enabled = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0xfU;
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__reload_request) {
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[0U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[1U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[2U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[3U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[4U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[5U] = 0U;
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[6U] = 0U;
                        __Vilp = 0U;
                        while ((__Vilp <= 0x27U)) {
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[__Vilp] 
                                = Vbench__ConstPool__CONST_had224c38_0[__Vilp];
                            __Vilp = ((IData)(1U) + __Vilp);
                        }
                        __Vilp = 0U;
                        while ((__Vilp <= 0x27U)) {
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_lengths[__Vilp] 
                                = Vbench__ConstPool__CONST_had224c38_0[__Vilp];
                            __Vilp = ((IData)(1U) + __Vilp);
                        }
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[1U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[1U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[2U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[2U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[3U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[4U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[4U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[5U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[5U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[6U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[6U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[7U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[7U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[8U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[8U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[9U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[9U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xaU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xaU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xbU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xbU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xcU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xcU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xdU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xdU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xeU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xeU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xfU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xfU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x10U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x10U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x11U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x11U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x12U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x12U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x13U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x13U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x14U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x14U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x15U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x15U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x16U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x16U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x17U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x17U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x18U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x18U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x19U] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x19U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1aU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1aU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1bU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1bU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1cU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1cU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1dU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1dU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1eU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1eU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1fU] 
                            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1fU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[0U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[1U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[1U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[2U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[2U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[3U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[3U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[4U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[4U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[5U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[5U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[6U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[6U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[7U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[7U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[8U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[8U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[9U] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[9U];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xaU] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[0xaU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xbU] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[0xbU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xcU] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[0xcU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xdU] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[0xdU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xeU] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[0xeU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xfU] 
                            = Vbench__ConstPool__CONST_h93e1b771_0[0xfU];
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__code = 0U;
                        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_enabled = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0U;
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                    if (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n) 
                         & (0x1bU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__state)))) {
                        if ((1U & (((((~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded)) 
                                      | (~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest_valid))) 
                                     | (~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory_valid))) 
                                    | (~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens_valid))) 
                                   | (~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile_valid))))) {
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__code = 6U;
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_enabled = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0xfU;
                        } else {
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[0U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[0U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[1U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[1U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[2U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[2U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[3U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[3U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[4U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[4U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[5U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[5U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[6U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_config[6U];
                            __Vilp = 0U;
                            while ((__Vilp <= 0x27U)) {
                                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[__Vilp] 
                                    = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_bases[__Vilp];
                                __Vilp = ((IData)(1U) 
                                          + __Vilp);
                            }
                            __Vilp = 0U;
                            while ((__Vilp <= 0x27U)) {
                                vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_lengths[__Vilp] 
                                    = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_lengths[__Vilp];
                                __Vilp = ((IData)(1U) 
                                          + __Vilp);
                            }
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[1U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[1U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[2U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[2U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[3U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[4U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[4U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[5U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[5U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[6U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[6U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[7U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[7U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[8U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[8U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[9U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[9U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xaU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xaU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xbU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xbU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xcU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xcU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xdU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xdU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xeU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xeU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xfU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0xfU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x10U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x10U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x11U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x11U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x12U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x12U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x13U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x13U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x14U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x14U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x15U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x15U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x16U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x16U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x17U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x17U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x18U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x18U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x19U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x19U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1aU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1aU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1bU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1bU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1cU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1cU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1dU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1dU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1eU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1eU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1fU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_metadata[0x1fU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[1U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[1U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[2U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[2U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[3U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[3U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[4U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[4U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[5U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[5U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[6U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[6U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[7U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[7U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[8U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[8U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[9U] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[9U];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xaU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xaU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xbU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xbU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xcU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xcU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xdU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xdU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xeU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xeU];
                            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xfU] 
                                = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__staged_counts[0xfU];
                            vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0xeU;
                        }
                    }
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0xdU;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__profile_valid) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0xcU;
                    }
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0xbU;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__tokens_valid) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0xaU;
                }
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 9U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__directory_valid) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 8U;
                    }
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__manifest_valid) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 6U;
                }
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
                if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__loaded) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 4U;
                }
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state))) {
            if (vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__calibration_sync) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 2U;
            }
        } else {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_enabled = 1U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 1U;
        }
        vlSelf->bench__DOT__dut__DOT__done_r = 0U;
        if (((IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__done_r) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n))) {
            vlSelf->__Vdly__bench__DOT__dut__DOT__controller_finished = 1U;
        }
        if (((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__done_r) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n))) {
            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer_finished = 1U;
        }
        if (vlSelf->bench__DOT__dut__DOT__reload_request) {
            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0U;
            vlSelf->bench__DOT__dut__DOT__clients_enabled = 0U;
            vlSelf->bench__DOT__dut__DOT__io_enabled = 0U;
            vlSelf->bench__DOT__dut__DOT__admitted = 0U;
            vlSelf->bench__DOT__dut__DOT__abort_r = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__controller_finished = 0U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer_finished = 0U;
            vlSelf->bench__DOT__dut__DOT__code = 0U;
        } else if (vlSelf->bench__DOT__dut__DOT__fault) {
            vlSelf->bench__DOT__dut__DOT__code = vlSelf->bench__DOT__dut__DOT__fault_code;
            vlSelf->bench__DOT__dut__DOT__abort_r = 1U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 9U;
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__code = 0x32U;
                vlSelf->bench__DOT__dut__DOT__abort_r = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 9U;
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    vlSelf->bench__DOT__dut__DOT__code = 0x32U;
                    vlSelf->bench__DOT__dut__DOT__abort_r = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 9U;
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 4U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__clients_enabled = 0U;
            } else if ((((IData)(vlSelf->bench__DOT__dut__DOT__controller_finished) 
                         & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_finished)) 
                        & (IData)(vlSelf->bench__DOT__dut__DOT__io_tx_idle))) {
                vlSelf->bench__DOT__dut__DOT__done_r = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 4U;
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                    if (vlSelf->bench__DOT__dut__DOT__controller_finished) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 8U;
                    }
                } else if ((((IData)(vlSelf->bench__DOT__dut__DOT__io_rx_valid) 
                             & (IData)(vlSelf->bench__DOT__dut__DOT__io_rx_ready)) 
                            & (IData)(vlSelf->bench__DOT__dut__DOT__io_rx_last))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__state = 7U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller_finished = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer_finished = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 6U;
            } else if (vlSelf->bench__DOT__dut__DOT__serial_update) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0xaU;
            } else if (vlSelf->bench__DOT__dut__DOT__io_rx_valid) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 5U;
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
                vlSelf->bench__DOT__dut__DOT__clients_enabled = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 4U;
            } else {
                vlSelf->bench__DOT__dut__DOT__admitted = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__state))) {
            vlSelf->__Vdly__bench__DOT__dut__DOT__state = 2U;
        } else {
            vlSelf->bench__DOT__dut__DOT__io_enabled = 1U;
            if (vlSelf->bench__DOT__dut__DOT__loader_done) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__state = 1U;
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__configuration__DOT__frame_r = 0U;
        vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_error = 0U;
        vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_data = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_enabled = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__code = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_config[6U] = 0U;
        __Vilp = 0U;
        while ((__Vilp <= 0x27U)) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[__Vilp] 
                = Vbench__ConstPool__CONST_had224c38_0[__Vilp];
            __Vilp = ((IData)(1U) + __Vilp);
        }
        __Vilp = 0U;
        while ((__Vilp <= 0x27U)) {
            vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_lengths[__Vilp] 
                = Vbench__ConstPool__CONST_had224c38_0[__Vilp];
            __Vilp = ((IData)(1U) + __Vilp);
        }
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[1U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[2U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[3U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[4U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[5U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[6U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[7U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[8U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[9U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xaU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xbU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xcU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xdU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xeU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xfU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0xfU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x10U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x10U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x11U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x11U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x12U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x12U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x13U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x13U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x14U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x14U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x15U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x15U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x16U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x16U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x17U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x17U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x18U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x18U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x19U] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x19U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1aU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1aU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1bU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1bU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1cU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1cU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1dU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1dU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1eU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1eU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0x1fU] 
            = Vbench__ConstPool__CONST_hd6b7ba52_0[0x1fU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[1U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[1U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[2U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[2U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[3U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[3U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[4U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[4U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[5U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[5U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[6U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[6U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[7U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[7U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[8U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[8U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[9U] 
            = Vbench__ConstPool__CONST_h93e1b771_0[9U];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xaU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xaU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xbU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xbU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xcU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xcU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xdU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xdU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xeU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xeU];
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[0xfU] 
            = Vbench__ConstPool__CONST_h93e1b771_0[0xfU];
        vlSelf->__Vdly__bench__DOT__dut__DOT__controller_finished = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer_finished = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__state = 0U;
        vlSelf->bench__DOT__dut__DOT__clients_enabled = 0U;
        vlSelf->bench__DOT__dut__DOT__io_enabled = 1U;
        vlSelf->bench__DOT__dut__DOT__admitted = 0U;
        vlSelf->bench__DOT__dut__DOT__abort_r = 0U;
        vlSelf->bench__DOT__dut__DOT__done_r = 0U;
        vlSelf->bench__DOT__dut__DOT__code = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__state;
    vlSelf->bench__DOT__dut__DOT__controller_finished 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__controller_finished;
    vlSelf->bench__DOT__dut__DOT__detokenizer_finished 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer_finished;
    vlSelf->bench__DOT__dut__DOT__state = vlSelf->__Vdly__bench__DOT__dut__DOT__state;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__calibration_sync 
        = ((IData)(vlSelf->bench__DOT__rst_n) && (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__calibration_meta));
    __Vtableidx5 = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__selected 
        = Vbench__ConstPool__TABLE_h554b41bf_0[__Vtableidx5];
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h065bd496__0 
        = ((0xeU != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)) 
           & (0xfU != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__calibration_meta 
        = ((IData)(vlSelf->bench__DOT__rst_n) && (IData)(vlSelf->bench__DOT__ddr_cal_done));
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__15(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__15\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_shift 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_shift;
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_active 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__edge_io__DOT__tx_active;
    if (vlSelf->bench__DOT__dut__DOT__io_rst_n) {
        if (vlSelf->bench__DOT__dut__DOT__edge_io__DOT__paths_idle) {
            if ((4U <= vlSelf->bench__DOT__dut__DOT__divisor)) {
                vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass 
                    = ((IData)(vlSelf->bench__DOT__rst_n) 
                       & vlSelf->bench__DOT__dut__DOT__configuration__DOT__transport_r);
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass = 0U;
    }
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
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__16(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__16\n"); );
    // Init
    CData/*0:0*/ __VdfgTmp_h77ceb880__0;
    __VdfgTmp_h77ceb880__0 = 0;
    CData/*0:0*/ __VdfgTmp_had546d50__0;
    __VdfgTmp_had546d50__0 = 0;
    CData/*7:0*/ __Vdlyvval__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v0;
    __Vdlyvval__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v0 = 0;
    CData/*1:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1;
    __Vdlyvdim0__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1 = 0;
    CData/*7:0*/ __Vdlyvval__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1;
    __Vdlyvval__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1 = 0;
    CData/*3:0*/ __Vdlyvdim0__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0;
    __Vdlyvdim0__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0 = 0;
    IData/*31:0*/ __Vdlyvval__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0;
    __Vdlyvval__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0 = 0;
    VlWide<3>/*95:0*/ __Vtemp_2;
    VlWide<3>/*95:0*/ __Vtemp_4;
    VlWide<3>/*95:0*/ __Vtemp_5;
    VlWide<3>/*95:0*/ __Vtemp_6;
    VlWide<3>/*95:0*/ __Vtemp_7;
    VlWide<3>/*95:0*/ __Vtemp_8;
    VlWide<3>/*95:0*/ __Vtemp_9;
    VlWide<3>/*95:0*/ __Vtemp_10;
    VlWide<3>/*95:0*/ __Vtemp_11;
    VlWide<3>/*95:0*/ __Vtemp_13;
    VlWide<3>/*95:0*/ __Vtemp_14;
    VlWide<3>/*95:0*/ __Vtemp_15;
    VlWide<3>/*95:0*/ __Vtemp_16;
    VlWide<3>/*95:0*/ __Vtemp_17;
    VlWide<3>/*95:0*/ __Vtemp_18;
    VlWide<3>/*95:0*/ __Vtemp_22;
    VlWide<3>/*95:0*/ __Vtemp_24;
    VlWide<3>/*95:0*/ __Vtemp_26;
    VlWide<3>/*95:0*/ __Vtemp_27;
    VlWide<3>/*95:0*/ __Vtemp_28;
    VlWide<3>/*95:0*/ __Vtemp_29;
    VlWide<3>/*95:0*/ __Vtemp_30;
    VlWide<3>/*95:0*/ __Vtemp_31;
    VlWide<3>/*95:0*/ __Vtemp_32;
    VlWide<3>/*95:0*/ __Vtemp_33;
    VlWide<3>/*95:0*/ __Vtemp_35;
    VlWide<3>/*95:0*/ __Vtemp_36;
    VlWide<3>/*95:0*/ __Vtemp_37;
    VlWide<3>/*95:0*/ __Vtemp_38;
    VlWide<3>/*95:0*/ __Vtemp_39;
    VlWide<3>/*95:0*/ __Vtemp_40;
    VlWide<3>/*95:0*/ __Vtemp_42;
    VlWide<3>/*95:0*/ __Vtemp_43;
    VlWide<3>/*95:0*/ __Vtemp_44;
    VlWide<3>/*95:0*/ __Vtemp_45;
    VlWide<3>/*95:0*/ __Vtemp_46;
    VlWide<3>/*95:0*/ __Vtemp_48;
    VlWide<3>/*95:0*/ __Vtemp_49;
    VlWide<3>/*95:0*/ __Vtemp_50;
    VlWide<3>/*95:0*/ __Vtemp_52;
    VlWide<3>/*95:0*/ __Vtemp_53;
    VlWide<3>/*95:0*/ __Vtemp_54;
    VlWide<3>/*95:0*/ __Vtemp_55;
    VlWide<3>/*95:0*/ __Vtemp_56;
    VlWide<3>/*95:0*/ __Vtemp_57;
    VlWide<3>/*95:0*/ __Vtemp_58;
    VlWide<3>/*95:0*/ __Vtemp_59;
    // Body
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__component;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__activation_reuse_valid 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__activation_reuse_valid;
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state;
    __VdfgTmp_h77ceb880__0 = ((6U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)) 
                              | (7U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)));
    __VdfgTmp_had546d50__0 = ((8U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)) 
                              | (9U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__state)));
    if (vlSelf->bench__DOT__dut__DOT__client_rst_n) {
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__done_r = 0U;
        if ((((0U != (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state)) 
              & (7U != (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) 
             & (IData)(vlSelf->bench__DOT__dut__DOT__core_error))) {
            vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x20U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
        } else if (((((0U != (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state)) 
                      & (7U != (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) 
                     & (3U != (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) 
                    & ((IData)(vlSelf->bench__DOT__dut__DOT__core_logit_valid) 
                       | (IData)(vlSelf->bench__DOT__dut__DOT__core_done)))) {
            vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x21U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x21U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                } else if (((IData)(vlSelf->bench__DOT__dut__DOT__finish_valid) 
                            & (IData)(vlSelf->bench__DOT__dut__DOT__finish_ready))) {
                    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__done_r = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 0U;
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__generated_valid) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__generated_ready))) {
                    if (vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 6U;
                    } else if ((((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__position) 
                                >= vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__sequence_limit)) {
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x31U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                    } else {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__position 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__position);
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__issue_id 
                            = vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_id;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 2U;
                    }
                }
            } else if ((1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_valid)) 
                              | (vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count 
                                 != vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary)))) {
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x21U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prefill) 
                        & (((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index) 
                           < vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index 
                    = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index);
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__position 
                    = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__position);
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__issue_id 
                    = vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt
                    [(0xfU & ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index))];
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 2U;
            } else {
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prefill = 0U;
                if ((0U == vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__max_tokens)) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 6U;
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections 
                        = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections);
                    if ((vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_id 
                         == vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__eos)) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 6U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_id 
                            = vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_id;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last 
                            = (((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections) 
                               >= vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__max_tokens);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 5U;
                    }
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__core_logit_valid) 
                     & ((vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count 
                         >= vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary) 
                        | (vlSelf->bench__DOT__dut__DOT__core_logit_index 
                           != vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count)))) {
                    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x21U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                } else if (((IData)(vlSelf->bench__DOT__dut__DOT__core_done) 
                            & (~ (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__frame_complete)))) {
                    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x21U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                } else {
                    if (vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__accept_logit) {
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count 
                            = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count);
                        if ((1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_valid)) 
                                   | VL_GTS_III(32, vlSelf->bench__DOT__dut__DOT__core_logit_data, vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_value)))) {
                            vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_value 
                                = vlSelf->bench__DOT__dut__DOT__core_logit_data;
                            vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_id 
                                = vlSelf->bench__DOT__dut__DOT__core_logit_index;
                            vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_valid = 1U;
                        }
                    }
                    if (vlSelf->bench__DOT__dut__DOT__core_done) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 4U;
                    }
                }
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__core_token_valid) 
                        & (IData)(vlSelf->bench__DOT__dut__DOT__core_token_ready))) {
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count = 0U;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_valid = 0U;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_id = 0U;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_value = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__token_valid) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__token_ready))) {
                if ((vlSelf->bench__DOT__dut__DOT__token_id 
                     >= vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary)) {
                    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x11U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                } else if ((vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count 
                            >= vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__sequence_limit)) {
                    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x31U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                } else if ((0x10U <= vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count)) {
                    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x30U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                } else {
                    __Vdlyvval__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0 
                        = vlSelf->bench__DOT__dut__DOT__token_id;
                    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0 = 1U;
                    __Vdlyvdim0__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0 
                        = (0xfU & vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count 
                        = ((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count);
                    if (vlSelf->bench__DOT__dut__DOT__token_last) {
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count = 0U;
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__issue_id 
                            = ((0U == vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count)
                                ? vlSelf->bench__DOT__dut__DOT__token_id
                                : vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt
                               [0U]);
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_valid = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 2U;
                    } else if ((((IData)(1U) + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count) 
                                >= vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__sequence_limit)) {
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x31U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                    } else if ((0x10U <= ((IData)(1U) 
                                          + vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count))) {
                        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x30U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
                    }
                }
            }
        } else if (vlSelf->bench__DOT__dut__DOT__engine_start) {
            if (((((0U == vlSelf->bench__DOT__dut__DOT__vocabulary) 
                   | (0x40000U < vlSelf->bench__DOT__dut__DOT__vocabulary)) 
                  | (vlSelf->bench__DOT__dut__DOT__eos_id 
                     >= vlSelf->bench__DOT__dut__DOT__vocabulary)) 
                 | (4U < vlSelf->bench__DOT__dut__DOT__maximum_tokens))) {
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0x32U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 7U;
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__position = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections = 0U;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__eos 
                    = vlSelf->bench__DOT__dut__DOT__eos_id;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__max_tokens 
                    = vlSelf->bench__DOT__dut__DOT__maximum_tokens;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary 
                    = vlSelf->bench__DOT__dut__DOT__vocabulary;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__sequence_limit = 4U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index = 0U;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_id = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last = 0U;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prefill = 1U;
                vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 1U;
            }
        }
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__done_r = 0U;
        if ((0x10U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x12U;
            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
        } else if ((8U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
            if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                    if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                    } else if (vlSelf->bench__DOT__dut__DOT__engine_start) {
                        __Vtemp_2[0U] = 0xffffffffU;
                        __Vtemp_2[1U] = 0xffffffffU;
                        __Vtemp_2[2U] = 0U;
                        __Vtemp_4[0U] = 0x20U;
                        __Vtemp_4[1U] = 0U;
                        __Vtemp_4[2U] = 0U;
                        __Vtemp_5[0U] = (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base);
                        __Vtemp_5[1U] = (IData)((vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base 
                                                 >> 0x20U));
                        __Vtemp_5[2U] = 0U;
                        __Vtemp_6[0U] = vlSelf->bench__DOT__dut__DOT__vocabulary;
                        __Vtemp_6[1U] = 0U;
                        __Vtemp_6[2U] = 0U;
                        VL_SHIFTL_WWI(66,66,32, __Vtemp_7, __Vtemp_6, 4U);
                        VL_ADD_W(3, __Vtemp_8, __Vtemp_5, __Vtemp_7);
                        VL_ADD_W(3, __Vtemp_9, __Vtemp_4, __Vtemp_8);
                        __Vtemp_10[0U] = __Vtemp_9[0U];
                        __Vtemp_10[1U] = __Vtemp_9[1U];
                        __Vtemp_10[2U] = (3U & __Vtemp_9[2U]);
                        __Vtemp_11[0U] = 0xffffffffU;
                        __Vtemp_11[1U] = 0xffffffffU;
                        __Vtemp_11[2U] = 0U;
                        __Vtemp_13[0U] = 0x20U;
                        __Vtemp_13[1U] = 0U;
                        __Vtemp_13[2U] = 0U;
                        __Vtemp_14[0U] = (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base);
                        __Vtemp_14[1U] = (IData)((vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base 
                                                  >> 0x20U));
                        __Vtemp_14[2U] = 0U;
                        __Vtemp_15[0U] = (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count);
                        __Vtemp_15[1U] = (IData)((vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count 
                                                  >> 0x20U));
                        __Vtemp_15[2U] = 0U;
                        VL_ADD_W(3, __Vtemp_16, __Vtemp_14, __Vtemp_15);
                        VL_ADD_W(3, __Vtemp_17, __Vtemp_13, __Vtemp_16);
                        __Vtemp_18[0U] = __Vtemp_17[0U];
                        __Vtemp_18[1U] = __Vtemp_17[1U];
                        __Vtemp_18[2U] = (3U & __Vtemp_17[2U]);
                        if ((1U & ((((((((~ (IData)(vlSelf->bench__DOT__boot_done)) 
                                         | (0x100U 
                                            > vlSelf->bench__DOT__dut__DOT__vocabulary)) 
                                        | (0x40000U 
                                           < vlSelf->bench__DOT__dut__DOT__vocabulary)) 
                                       | (0U == vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length)) 
                                      | (0U != (3U 
                                                & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base)))) 
                                     | (0U != (3U & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base)))) 
                                    | VL_LT_W(3, __Vtemp_2, __Vtemp_10)) 
                                   | VL_LT_W(3, __Vtemp_11, __Vtemp_18)))) {
                            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 6U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                        } else {
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__vocabulary 
                                = vlSelf->bench__DOT__dut__DOT__vocabulary;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__maximum_length 
                                = vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length;
                            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__records_base 
                                = vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base;
                            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_base 
                                = vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__bytes_count 
                                = vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__scalar_length = 0U;
                            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__tail_valid = 0U;
                            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_byte = 0U;
                            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 1U;
                        }
                    }
                } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                    if (((IData)(vlSelf->bench__DOT__dut__DOT__text_valid) 
                         & (IData)(vlSelf->bench__DOT__dut__DOT__text_ready))) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__tail_valid = 0U;
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__done_r = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xeU;
                    }
                } else if ((0U != (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x10U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                } else if (vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_valid) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xdU;
                } else {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__done_r = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xeU;
                }
            } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_last)
                            ? 0xcU : 1U);
                } else if ((1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_valid)) 
                                  | ((IData)(vlSelf->bench__DOT__dut__DOT__text_valid) 
                                     & (IData)(vlSelf->bench__DOT__dut__DOT__text_ready))))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_byte 
                        = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes
                        [(3U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__emit_index))];
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__tail_valid = 1U;
                    if ((((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__emit_index)) 
                         == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_length))) {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 9U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__emit_index 
                            = (7U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__emit_index)));
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state 
                    = ((0U == vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__remaining_bytes)
                        ? 0xbU : 7U);
            } else {
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor 
                    = (1ULL + vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor);
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__remaining_bytes 
                    = (vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__remaining_bytes 
                       - (IData)(1U));
                if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__emit_index = 0U;
                    __Vdlyvval__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v0 
                        = (0xffU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0);
                    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v0 = 1U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__scalar_length = 1U;
                    if ((0x80U > (0xffU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0))) {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value 
                            = (0xffU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xaU;
                    } else if (((0xc2U <= (0xffU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0)) 
                                & (0xdfU >= (0xffU 
                                             & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0)))) {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value 
                            = (0x1fU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar = 0x80U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining = 1U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 9U;
                    } else if (((0xe0U <= (0xffU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0)) 
                                & (0xefU >= (0xffU 
                                             & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0)))) {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value 
                            = (0xfU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar = 0x800U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining = 2U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 9U;
                    } else if (((0xf0U <= (0xffU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0)) 
                                & (0xf4U >= (0xffU 
                                             & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0)))) {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value 
                            = (7U & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar = 0x10000U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining = 3U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 9U;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x10U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                    }
                } else if ((2U != (3U & (vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0 
                                         >> 6U)))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x10U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                } else {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining 
                        = (7U & ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining) 
                                 - (IData)(1U)));
                    __Vdlyvval__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1 
                        = (0xffU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0);
                    vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1 = 1U;
                    __Vdlyvdim0__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1 
                        = (3U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_length));
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value 
                        = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__continued_scalar;
                    if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining))) {
                        if ((((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__continued_scalar 
                               < vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar) 
                              | (0x10ffffU < vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__continued_scalar)) 
                             | ((0xd800U <= vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__continued_scalar) 
                                & (0xdfffU >= vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__continued_scalar)))) {
                            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x10U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                        } else {
                            vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__emit_index = 0U;
                            vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xaU;
                        }
                    } else {
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 9U;
                    }
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__scalar_length 
                        = (7U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_length)));
                }
            }
        } else if ((4U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
            if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                    if ((1U & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[2U])) {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x11U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__request_address 
                            = (0xfffffffffffffffcULL 
                               & (((QData)((IData)(
                                                   vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[1U])) 
                                   << 0x20U) | (0xfffffffffffffffcULL 
                                                & (QData)((IData)(
                                                                  vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[0U])))));
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_lane 
                            = (3U & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[0U]);
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__reading_record = 0U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 3U;
                    }
                } else {
                    __Vtemp_22[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_count);
                    __Vtemp_22[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_count 
                                              >> 0x20U));
                    __Vtemp_22[2U] = 0U;
                    if ((1U & ((((((0U != (vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_flags 
                                           >> 2U)) 
                                   | (0U == (3U & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_flags))) 
                                  | (vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_flags 
                                     & (0U == vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length))) 
                                 | (vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length 
                                    > vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__maximum_length)) 
                                | vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end[2U]) 
                               | VL_GT_W(3, vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end, __Vtemp_22)))) {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x11U;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                    } else {
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor 
                            = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset;
                        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__remaining_bytes 
                            = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length;
                        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state 
                            = ((0U == vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length)
                                ? 0xbU : 7U);
                    }
                }
            } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                if ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset 
                        = ((0xffffffff00000000ULL & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset) 
                           | (IData)((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data)));
                } else if ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset 
                        = ((0xffffffffULL & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset) 
                           | ((QData)((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data)) 
                              << 0x20U));
                } else if ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length 
                        = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data;
                } else if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_flags 
                        = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data;
                }
                if ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 6U;
                } else {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word 
                        = (3U & ((IData)(1U) + (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word)));
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 2U;
                }
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_valid) 
                        & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_ready))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_valid) 
                     & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error))) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 4U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                } else {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_valid)
                            ? vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data
                            : 0U);
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__reading_record)
                            ? 5U : 8U);
                }
            }
        } else if ((2U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
            if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
                if (((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer_req_valid) 
                     & ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_valid) 
                        & (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__selected_owner))))) {
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 4U;
                }
            } else if ((1U & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[2U])) {
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x11U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
            } else {
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__request_address 
                    = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[1U])) 
                        << 0x20U) | (QData)((IData)(
                                                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[0U])));
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__reading_record = 1U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 3U;
            }
        } else if ((1U & (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state))) {
            if (((IData)(vlSelf->bench__DOT__dut__DOT__generated_valid) 
                 & (IData)(vlSelf->bench__DOT__dut__DOT__generated_ready))) {
                if ((vlSelf->bench__DOT__dut__DOT__generated_id 
                     >= vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__vocabulary)) {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0x11U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
                } else {
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word = 0U;
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_id 
                        = vlSelf->bench__DOT__dut__DOT__generated_id;
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_last 
                        = ((IData)(vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last) 
                           & (IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n));
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset = 0ULL;
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length = 0U;
                    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_flags = 0U;
                    vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 2U;
                }
            } else if (((IData)(vlSelf->bench__DOT__dut__DOT__finish_valid) 
                        & (IData)(vlSelf->bench__DOT__dut__DOT__finish_ready))) {
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xcU;
            }
        } else if (vlSelf->bench__DOT__dut__DOT__engine_start) {
            __Vtemp_24[0U] = 0xffffffffU;
            __Vtemp_24[1U] = 0xffffffffU;
            __Vtemp_24[2U] = 0U;
            __Vtemp_26[0U] = 0x20U;
            __Vtemp_26[1U] = 0U;
            __Vtemp_26[2U] = 0U;
            __Vtemp_27[0U] = (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base);
            __Vtemp_27[1U] = (IData)((vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base 
                                      >> 0x20U));
            __Vtemp_27[2U] = 0U;
            __Vtemp_28[0U] = vlSelf->bench__DOT__dut__DOT__vocabulary;
            __Vtemp_28[1U] = 0U;
            __Vtemp_28[2U] = 0U;
            VL_SHIFTL_WWI(66,66,32, __Vtemp_29, __Vtemp_28, 4U);
            VL_ADD_W(3, __Vtemp_30, __Vtemp_27, __Vtemp_29);
            VL_ADD_W(3, __Vtemp_31, __Vtemp_26, __Vtemp_30);
            __Vtemp_32[0U] = __Vtemp_31[0U];
            __Vtemp_32[1U] = __Vtemp_31[1U];
            __Vtemp_32[2U] = (3U & __Vtemp_31[2U]);
            __Vtemp_33[0U] = 0xffffffffU;
            __Vtemp_33[1U] = 0xffffffffU;
            __Vtemp_33[2U] = 0U;
            __Vtemp_35[0U] = 0x20U;
            __Vtemp_35[1U] = 0U;
            __Vtemp_35[2U] = 0U;
            __Vtemp_36[0U] = (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base);
            __Vtemp_36[1U] = (IData)((vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base 
                                      >> 0x20U));
            __Vtemp_36[2U] = 0U;
            __Vtemp_37[0U] = (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count);
            __Vtemp_37[1U] = (IData)((vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count 
                                      >> 0x20U));
            __Vtemp_37[2U] = 0U;
            VL_ADD_W(3, __Vtemp_38, __Vtemp_36, __Vtemp_37);
            VL_ADD_W(3, __Vtemp_39, __Vtemp_35, __Vtemp_38);
            __Vtemp_40[0U] = __Vtemp_39[0U];
            __Vtemp_40[1U] = __Vtemp_39[1U];
            __Vtemp_40[2U] = (3U & __Vtemp_39[2U]);
            if ((1U & ((((((((~ (IData)(vlSelf->bench__DOT__boot_done)) 
                             | (0x100U > vlSelf->bench__DOT__dut__DOT__vocabulary)) 
                            | (0x40000U < vlSelf->bench__DOT__dut__DOT__vocabulary)) 
                           | (0U == vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length)) 
                          | (0U != (3U & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base)))) 
                         | (0U != (3U & (IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base)))) 
                        | VL_LT_W(3, __Vtemp_24, __Vtemp_32)) 
                       | VL_LT_W(3, __Vtemp_33, __Vtemp_40)))) {
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 6U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0xfU;
            } else {
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__vocabulary 
                    = vlSelf->bench__DOT__dut__DOT__vocabulary;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__maximum_length 
                    = vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length;
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__records_base 
                    = vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base;
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_base 
                    = vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__bytes_count 
                    = vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__scalar_length = 0U;
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__tail_valid = 0U;
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_byte = 0U;
                vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0U;
                vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 1U;
            }
        }
    } else {
        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__position = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__logit_count = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__eos = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__max_tokens = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__vocabulary = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__sequence_limit = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__issue_id = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_id = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_value = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__winner_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_id = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prefill = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__done_r = 0U;
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__code = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor = 0ULL;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__remaining_bytes = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__emit_index = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__vocabulary = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__maximum_length = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_id = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__records_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_base = 0ULL;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__bytes_count = 0ULL;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_last = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset = 0ULL;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_flags = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__request_address = 0ULL;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__reading_record = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_lane = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__scalar_length = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value = 0U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar = 0U;
        vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v2 = 1U;
        vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__tail_valid = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_byte = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__done_r = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__code = 0U;
        vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v3 = 1U;
    }
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
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__position 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__position;
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_index;
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selections;
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt_count;
    if (vlSelf->__Vdlyvset__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0) {
        vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt[__Vdlyvdim0__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0] 
            = __Vdlyvval__bench__DOT__dut__DOT__controller__DOT__controller__DOT__prompt__v0;
    }
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__state;
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__vocabulary 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__vocabulary;
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__maximum_length 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__maximum_length;
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_count 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__bytes_count;
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__utf_remaining;
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_length 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__scalar_length;
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__minimum_scalar;
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__reading_record 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__reading_record;
    vlSelf->bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__controller__DOT__controller__DOT__selected_last;
    if (vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v0) {
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes[0U] 
            = __Vdlyvval__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v0;
    }
    if (vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1) {
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes[__Vdlyvdim0__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1] 
            = __Vdlyvval__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v1;
    }
    if (vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v2) {
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes[0U] = 0U;
    }
    if (vlSelf->__Vdlyvset__bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes__v3) {
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_bytes[3U] = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__tail_valid 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__tail_valid;
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__detokenizer__DOT__state;
    __Vtemp_42[0U] = 0x20U;
    __Vtemp_42[1U] = 0U;
    __Vtemp_42[2U] = 0U;
    __Vtemp_43[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_base);
    __Vtemp_43[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__bytes_base 
                              >> 0x20U));
    __Vtemp_43[2U] = 0U;
    __Vtemp_44[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor);
    __Vtemp_44[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__cursor 
                              >> 0x20U));
    __Vtemp_44[2U] = 0U;
    VL_ADD_W(3, __Vtemp_45, __Vtemp_43, __Vtemp_44);
    VL_ADD_W(3, __Vtemp_46, __Vtemp_42, __Vtemp_45);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[0U] 
        = __Vtemp_46[0U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[1U] 
        = __Vtemp_46[1U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_address_wide[2U] 
        = (1U & __Vtemp_46[2U]);
    __Vtemp_48[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset);
    __Vtemp_48[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_offset 
                              >> 0x20U));
    __Vtemp_48[2U] = 0U;
    __Vtemp_49[0U] = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_length;
    __Vtemp_49[1U] = 0U;
    __Vtemp_49[2U] = 0U;
    VL_ADD_W(3, __Vtemp_50, __Vtemp_48, __Vtemp_49);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end[0U] 
        = __Vtemp_50[0U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end[1U] 
        = __Vtemp_50[1U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_end[2U] 
        = (1U & __Vtemp_50[2U]);
    __Vtemp_52[0U] = 0x20U;
    __Vtemp_52[1U] = 0U;
    __Vtemp_52[2U] = 0U;
    __Vtemp_53[0U] = (IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__records_base);
    __Vtemp_53[1U] = (IData)((vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__records_base 
                              >> 0x20U));
    __Vtemp_53[2U] = 0U;
    __Vtemp_54[0U] = vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__token_id;
    __Vtemp_54[1U] = 0U;
    __Vtemp_54[2U] = 0U;
    VL_SHIFTL_WWI(65,65,32, __Vtemp_55, __Vtemp_54, 4U);
    __Vtemp_56[0U] = ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_word) 
                      << 2U);
    __Vtemp_56[1U] = 0U;
    __Vtemp_56[2U] = 0U;
    VL_ADD_W(3, __Vtemp_57, __Vtemp_55, __Vtemp_56);
    VL_ADD_W(3, __Vtemp_58, __Vtemp_53, __Vtemp_57);
    VL_ADD_W(3, __Vtemp_59, __Vtemp_52, __Vtemp_58);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[0U] 
        = __Vtemp_59[0U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[1U] 
        = __Vtemp_59[1U];
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__record_address_wide[2U] 
        = (1U & __Vtemp_59[2U]);
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0 
        = (vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__response_data 
           >> ((IData)(vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__byte_lane) 
               << 3U));
    vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__continued_scalar 
        = (0x1fffffU & (VL_SHIFTL_III(21,21,32, vlSelf->bench__DOT__dut__DOT__detokenizer__DOT__scalar_value, 6U) 
                        | (0x3fU & vlSelf->bench__DOT__dut__DOT__detokenizer__DOT____VdfgTmp_h152219a1__0)));
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__17(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__17\n"); );
    // Body
    vlSelf->bench__DOT__ddr_rsp_valid = vlSelf->__Vdly__bench__DOT__ddr_rsp_valid;
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__18(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__18\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__command_shift 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__command_shift;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state;
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__state 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__boot_loader__DOT__special_trie__DOT__validator__DOT__state;
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__1(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__1\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__raw_specials__tbl_rsp_valid 
        = ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalization__tbl_rsp_valid 
        = ((1U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__normalized_specials__tbl_rsp_valid 
        = ((2U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_rsp_valid 
        = ((3U == (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__selected)) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__normalization__tbl_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__normalize_selected) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_rsp_valid));
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT____Vcellinp__span__DOT__pretokenization__tbl_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__ordinary_text__DOT__span__DOT__dfa_selected) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__tokenizer__DOT____Vcellinp__tokenizer__DOT__ordinary_text__tbl_rsp_valid));
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__2(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__2\n"); );
    // Body
    if (vlSelf->bench__DOT__rst_n) {
        vlSelf->bench__DOT__dut__DOT__serial_update 
            = vlSelf->bench__DOT__dut__DOT__configuration__DOT__serial_update_r;
        vlSelf->bench__DOT__dut__DOT__reload_request 
            = vlSelf->bench__DOT__dut__DOT__configuration__DOT__reload_r;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_enabled;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__image_loader__start 
            = (2U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__manifest__start 
            = (4U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__directory__start 
            = (6U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__tokens__start 
            = (8U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__profile__start 
            = (0xaU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__special_trie__start 
            = (0xcU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__loader_error 
            = (0xfU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state));
        vlSelf->bench__DOT__dut__DOT__loader_done = 
            (0xeU == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state));
        vlSelf->bench__DOT__error_code = vlSelf->bench__DOT__dut__DOT__code;
        vlSelf->bench__DOT__dut__DOT__divisor = vlSelf->bench__DOT__dut__DOT__configuration__DOT__divisor_r;
        vlSelf->bench__DOT__dut__DOT__eos_id = vlSelf->bench__DOT__dut__DOT__configuration__DOT__eos_r;
        vlSelf->bench__DOT__dut__DOT__maximum_tokens 
            = vlSelf->bench__DOT__dut__DOT__configuration__DOT__max_r;
        vlSelf->bench__DOT__dut__DOT__vocabulary = vlSelf->bench__DOT__dut__DOT__configuration__DOT__vocab_r;
        vlSelf->bench__DOT__busy = ((4U != (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                                    & (9U != (IData)(vlSelf->bench__DOT__dut__DOT__state)));
        vlSelf->bench__DOT__error = (9U == (IData)(vlSelf->bench__DOT__dut__DOT__state));
        vlSelf->bench__DOT__done = ((IData)(vlSelf->bench__DOT__dut__DOT__done_r) 
                                    & (9U != (IData)(vlSelf->bench__DOT__dut__DOT__state)));
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage 
            = ((0U != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)) 
               & ((1U != (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__state)) 
                  & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____VdfgTmp_h065bd496__0)));
        vlSelf->bench__DOT__dut__DOT__io_rst_n = vlSelf->bench__DOT__dut__DOT__io_enabled;
    } else {
        vlSelf->bench__DOT__dut__DOT__serial_update = 0U;
        vlSelf->bench__DOT__dut__DOT__reload_request = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__image_loader__start = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__manifest__start = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__directory__start = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__tokens__start = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__profile__start = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT____Vcellinp__special_trie__start = 0U;
        vlSelf->bench__DOT__dut__DOT__loader_error = 0U;
        vlSelf->bench__DOT__dut__DOT__loader_done = 0U;
        vlSelf->bench__DOT__error_code = 0U;
        vlSelf->bench__DOT__dut__DOT__divisor = 0U;
        vlSelf->bench__DOT__dut__DOT__eos_id = 0U;
        vlSelf->bench__DOT__dut__DOT__maximum_tokens = 0U;
        vlSelf->bench__DOT__dut__DOT__vocabulary = 0U;
        vlSelf->bench__DOT__busy = 0U;
        vlSelf->bench__DOT__error = 0U;
        vlSelf->bench__DOT__done = 0U;
        vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_stage = 0U;
        vlSelf->bench__DOT__dut__DOT__io_rst_n = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__detokenizer_rsp_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT____VdfgTmp_heea46ac4__0) 
           & (2U == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__owner)));
    vlSelf->bench__DOT__dut__DOT__engine_start = ((IData)(vlSelf->bench__DOT__rst_n) 
                                                  & (5U 
                                                     == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__client_rst_n = ((IData)(vlSelf->bench__DOT__dut__DOT__clients_enabled) 
                                                  & (IData)(vlSelf->bench__DOT__rst_n));
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
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xbU])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xaU])));
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base 
            = (((QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xdU])) 
                << 0x20U) | (QData)((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_bases[0xcU])));
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length 
            = vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_metadata[0xeU];
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
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_records_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_base = 0ULL;
        vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_max_token_byte_length = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_core_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & ((IData)(vlSelf->bench__DOT__dut__DOT__loader_done) 
                                                 & (0U 
                                                    == (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__tensor_mapper__DOT__state))));
    vlSelf->bench__DOT__dut__DOT____Vcellinp__detokenizer__cfg_token_bytes_count 
        = (QData)((IData)(((IData)(vlSelf->bench__DOT__dut__DOT__loader_done)
                            ? vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__active_counts[2U]
                            : 0U)));
    vlSelf->bench__DOT__boot_done = ((IData)(vlSelf->bench__DOT__rst_n) 
                                     & ((IData)(vlSelf->bench__DOT__dut__DOT__admitted) 
                                        & (IData)(vlSelf->bench__DOT__dut__DOT__loader_done)));
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
    vlSelf->bench__DOT__dut__DOT____VdfgTmp_he886f039__0 
        = ((~ (IData)(vlSelf->bench__DOT__dut__DOT__abort_r)) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__client_rst_n));
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
    vlSelf->bench__DOT__dut__DOT__core_mem_req_ready 
        = ((IData)(vlSelf->bench__DOT__rst_n) & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__abort_r)) 
                                                 & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_core_ready)));
    vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__status 
        = (((IData)(vlSelf->bench__DOT__error) << 3U) 
           | (((IData)(vlSelf->bench__DOT__done) << 2U) 
              | ((((IData)(vlSelf->bench__DOT__rst_n) 
                   & ((4U != (IData)(vlSelf->bench__DOT__dut__DOT__state)) 
                      & (9U != (IData)(vlSelf->bench__DOT__dut__DOT__state)))) 
                  << 1U) | (IData)(vlSelf->bench__DOT__boot_done))));
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
}

VL_INLINE_OPT void Vbench___024root___nba_sequent__TOP__19(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_sequent__TOP__19\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__memory_subsystem__DOT__response_error;
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data 
        = vlSelf->__Vdly__bench__DOT__dut__DOT__memory_subsystem__DOT__response_data;
    if (vlSelf->bench__DOT__rst_n) {
        if (vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__publish) {
            if ((1U & (~ ((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__staged_match)) 
                          | (~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__bundle_legal)))))) {
                vlSelf->bench__DOT__dut__DOT__configuration__DOT__transport_r 
                    = vlSelf->bench__DOT__dut__DOT__committed_config[3U];
            }
        } else if (((IData)(vlSelf->bench__DOT__cfg_valid) 
                    & (IData)(vlSelf->bench__DOT__cfg_ready))) {
            if ((1U & (~ ((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__address_known)) 
                          | ((IData)(vlSelf->bench__DOT__cfg_write) 
                             & (((~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable)) 
                                 | (~ (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal))) 
                                | ((0x1cU == vlSelf->bench__DOT__cfg_addr)
                                    ? (~ (IData)(vlSelf->bench__DOT__dut__DOT__reload_allowed))
                                    : (~ (IData)(vlSelf->bench__DOT__dut__DOT__write_allowed))))))))) {
                if (vlSelf->bench__DOT__cfg_write) {
                    if (((((((((4U == vlSelf->bench__DOT__cfg_addr) 
                               | (8U == vlSelf->bench__DOT__cfg_addr)) 
                              | (0xcU == vlSelf->bench__DOT__cfg_addr)) 
                             | (0x10U == vlSelf->bench__DOT__cfg_addr)) 
                            | (0x14U == vlSelf->bench__DOT__cfg_addr)) 
                           | (0x18U == vlSelf->bench__DOT__cfg_addr)) 
                          | (0x1cU == vlSelf->bench__DOT__cfg_addr)) 
                         | (0x24U == vlSelf->bench__DOT__cfg_addr))) {
                        if ((4U != vlSelf->bench__DOT__cfg_addr)) {
                            if ((8U != vlSelf->bench__DOT__cfg_addr)) {
                                if ((0xcU != vlSelf->bench__DOT__cfg_addr)) {
                                    if ((0x10U == vlSelf->bench__DOT__cfg_addr)) {
                                        vlSelf->bench__DOT__dut__DOT__configuration__DOT__transport_r 
                                            = vlSelf->bench__DOT__cfg_wdata;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    } else {
        vlSelf->bench__DOT__dut__DOT__configuration__DOT__transport_r = 0U;
    }
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__3(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__3\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__live_ddr_error = 
        ((IData)(vlSelf->bench__DOT__ddr_rsp_valid) 
         & ((IData)(vlSelf->bench__DOT__ddr_rsp_error) 
            & (IData)(vlSelf->bench__DOT__ddr_rsp_ready)));
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__4(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__4\n"); );
    // Body
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
    vlSelf->bench__DOT__spi_cs_n = (1U & ((~ (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n)) 
                                          | ((0U == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state)) 
                                             | (5U 
                                                == (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__state)))));
    vlSelf->bench__DOT__spi_sck = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_reader__DOT__reader__DOT__clock_level) 
                                   & (IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__epoch_rst_n));
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
    vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__assembled_word 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__flash_data) 
            << 0x18U) | (0xffffffU & vlSelf->bench__DOT__dut__DOT__boot_loader__DOT__image_loader__DOT__loader__DOT__word_buffer));
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__5(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__5\n"); );
    // Init
    CData/*0:0*/ bench__DOT__dut__DOT__io_rx_idle;
    bench__DOT__dut__DOT__io_rx_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_he9711bd6__0;
    bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_he9711bd6__0 = 0;
    // Body
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
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hb418d625__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__healthy));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & (0U != (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__receive_open 
        = ((~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__frame_closed)) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__receiving));
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
    vlSelf->bench__DOT__dut__DOT__io_rx_valid = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hb418d625__0) 
                                                 & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_valid 
        = (((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT____VdfgTmp_hb418d625__0) 
            & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__receive_open)) 
           & ((1U & (~ (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__active_bypass))) 
              && (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__serial_emit)));
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
    vlSelf->bench__DOT__dut__DOT__text_ready = ((IData)(vlSelf->bench__DOT__dut__DOT____VdfgTmp_he886f039__0) 
                                                & (IData)(vlSelf->bench__DOT__dut__DOT__io_tx_ready));
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__6(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__6\n"); );
    // Init
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
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__gemv__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__rope__DOT__port_idle = 0;
    CData/*0:0*/ bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__port_idle;
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__port_idle = 0;
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
    VlWide<5>/*159:0*/ __Vtemp_4;
    VlWide<9>/*287:0*/ __Vtemp_21;
    // Body
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
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active 
            = (3U > vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected);
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
        vlSelf->bench__DOT__dut__DOT__core_token_ready 
            = ((IData)(vlSelf->bench__DOT__boot_done) 
               & (0U == (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__state)));
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
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active = 0U;
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
        vlSelf->bench__DOT__dut__DOT__core_token_ready = 0U;
    }
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_done) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__failed));
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__divider__DOT__divider__DOT__zero_divisor));
    VL_NEGATE_W(5, __Vtemp_4, bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__quotient);
    if (vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__negative) {
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[0U] 
            = __Vtemp_4[0U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[1U] 
            = __Vtemp_4[1U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[2U] 
            = __Vtemp_4[2U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[3U] 
            = __Vtemp_4[3U];
        vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__attention__DOT__rounded_divider__DOT__signed_quotient[4U] 
            = (1U & __Vtemp_4[4U]);
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
    vlSelf->bench__DOT__dut__DOT____Vcellinp__edge_io__tx_valid 
        = ((IData)(vlSelf->bench__DOT__dut__DOT____VdfgTmp_he886f039__0) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__text_valid));
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
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h6323ea89__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active) 
           & (2U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h632b4bf4__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active) 
           & (0U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected));
    bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT____VdfgTmp_h62f58b69__0 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__bus__DOT__mux__DOT__active) 
           & (1U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__selected));
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
    __Vtemp_21[0U] = bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber18;
    __Vtemp_21[1U] = (IData)((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                               << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))));
    __Vtemp_21[2U] = (IData)(((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber16)) 
                                << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber17))) 
                              >> 0x20U));
    __Vtemp_21[3U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                       << 3U) | (IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber15));
    __Vtemp_21[4U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                       << 9U) | (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber10) 
                                  << 8U) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber12) 
                                             << 7U) 
                                            | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber13) 
                                                << 3U) 
                                               | (bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__gemv____pinNumber14 
                                                  >> 0x1dU)))));
    __Vtemp_21[5U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber18 
                       >> 0x17U) | ((IData)((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                              << 0x20U) 
                                             | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                                    << 9U));
    __Vtemp_21[6U] = (((IData)((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                 << 0x20U) | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17)))) 
                       >> 0x17U) | ((IData)(((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                               << 0x20U) 
                                              | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                             >> 0x20U)) 
                                    << 9U));
    __Vtemp_21[7U] = ((bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber14 
                       << 0xcU) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber15) 
                                    << 9U) | ((IData)(
                                                      ((((QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber16)) 
                                                         << 0x20U) 
                                                        | (QData)((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber17))) 
                                                       >> 0x20U)) 
                                              >> 0x17U)));
    __Vtemp_21[8U] = (((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber10) 
                       << 0x11U) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber12) 
                                     << 0x10U) | (((IData)(bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT____Vcellout__silu_product____pinNumber13) 
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
                 ? 0U : (__Vtemp_21[((IData)(1U) + 
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
               | (__Vtemp_21[(0xfU & (((IData)(0x89U) 
                                       * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                           ? 1U : 0U)) 
                                      >> 5U))] >> (0x1fU 
                                                   & ((IData)(0x89U) 
                                                      * 
                                                      ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                        ? 1U
                                                        : 0U)))));
        bench__DOT__dut__DOT__core_adapter__DOT__core__DOT__decoder__DOT__mlp__DOT__bus__DOT____VdfgTmp_h1d40ca1e__0[1U] 
            = (((0U == (0x1fU & ((IData)(0x89U) * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
                                                    ? 1U
                                                    : 0U))))
                 ? 0U : (__Vtemp_21[((IData)(2U) + 
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
               | (__Vtemp_21[((IData)(1U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
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
                 ? 0U : (__Vtemp_21[((IData)(3U) + 
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
               | (__Vtemp_21[((IData)(2U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
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
                 ? 0U : (__Vtemp_21[((IData)(4U) + 
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
               | (__Vtemp_21[((IData)(3U) + (0xfU & 
                                             (((IData)(0x89U) 
                                               * ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
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
                           ? 0U : (__Vtemp_21[((IData)(5U) 
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
                         | (__Vtemp_21[((IData)(4U) 
                                        + (0xfU & (
                                                   ((IData)(0x89U) 
                                                    * 
                                                    ((IData)(vlSelf->__VdfgTmp_h26c9701b__0)
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
    vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__frame_complete 
        = ((0x101U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_count) 
           | ((IData)(vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_transfer) 
              & (0x100U == vlSelf->bench__DOT__dut__DOT__core_adapter__DOT__physical_count)));
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

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__8(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__8\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error));
    vlSelf->bench__DOT__dut__DOT__boot_rsp_error = 
        ((IData)(vlSelf->bench__DOT__dut__DOT__boot_rsp_valid) 
         & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error));
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_error 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_error));
    vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_data 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__tokenizer_rsp_valid)
            ? vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data
            : 0U);
    vlSelf->bench__DOT__dut__DOT__boot_rsp_data = ((IData)(vlSelf->bench__DOT__dut__DOT__boot_rsp_valid)
                                                    ? vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data
                                                    : 0U);
    vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_rdata 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__mapper_rsp_valid)
            ? vlSelf->bench__DOT__dut__DOT__memory_subsystem__DOT__response_data
            : 0U);
    if (vlSelf->bench__DOT__dut__DOT__loader_done) {
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
    } else {
        vlSelf->bench__DOT__dut__DOT__committed_config[0U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[1U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[2U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[3U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[4U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[5U] = 0U;
        vlSelf->bench__DOT__dut__DOT__committed_config[6U] = 0U;
    }
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
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal = 1U;
    vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__publish 
        = ((IData)(vlSelf->bench__DOT__rst_n) & (1U 
                                                 == (IData)(vlSelf->bench__DOT__dut__DOT__state)));
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value = 0U;
    if (((((((((0U == vlSelf->bench__DOT__cfg_addr) 
               | (4U == vlSelf->bench__DOT__cfg_addr)) 
              | (8U == vlSelf->bench__DOT__cfg_addr)) 
             | (0xcU == vlSelf->bench__DOT__cfg_addr)) 
            | (0x10U == vlSelf->bench__DOT__cfg_addr)) 
           | (0x14U == vlSelf->bench__DOT__cfg_addr)) 
          | (0x18U == vlSelf->bench__DOT__cfg_addr)) 
         | (0x1cU == vlSelf->bench__DOT__cfg_addr))) {
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
    } else {
        if ((0x20U != vlSelf->bench__DOT__cfg_addr)) {
            if ((0x24U != vlSelf->bench__DOT__cfg_addr)) {
                vlSelf->bench__DOT__dut__DOT__configuration__DOT__value_legal = 0U;
            }
        }
        if ((0x20U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT__code;
        } else if ((0x24U == vlSelf->bench__DOT__cfg_addr)) {
            vlSelf->bench__DOT__dut__DOT__configuration__DOT__read_value 
                = vlSelf->bench__DOT__dut__DOT__configuration__DOT__frame_r;
        }
    }
    vlSelf->bench__DOT__cfg_ready = ((~ ((IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__configuration__publish) 
                                         | (IData)(vlSelf->bench__DOT__dut__DOT__configuration__DOT__response_valid))) 
                                     & (IData)(vlSelf->bench__DOT__rst_n));
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__9(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__9\n"); );
    // Body
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
    vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable = 1U;
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
    } else if ((0x20U == vlSelf->bench__DOT__cfg_addr)) {
        vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable = 0U;
    } else if ((0x24U != vlSelf->bench__DOT__cfg_addr)) {
        vlSelf->bench__DOT__dut__DOT__configuration__DOT__writable = 0U;
    }
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__10(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__10\n"); );
    // Body
    vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__continued_scalar 
        = (VL_SHIFTL_III(32,32,32, vlSelf->bench__DOT__dut__DOT__tokenizer__DOT__tokenizer__DOT__utf8__DOT__decoder__DOT__scalar, 6U) 
           | ((IData)(vlSelf->bench__DOT__dut__DOT__io_rx_valid)
               ? ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_out_valid)
                   ? (0x3fU & (IData)(vlSelf->__VdfgTmp_h5b2387d0__0))
                   : 0U) : 0U));
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
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__tx_fifo__DOT__storage__DOT__push 
        = ((IData)(vlSelf->bench__DOT__dut__DOT____Vcellinp__edge_io__tx_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__io_tx_ready));
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
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_ready 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__io_rst_n) 
           & ((3U > (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__count)) 
              | (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__pop)));
    vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo__DOT__storage__DOT__push 
        = ((IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_valid) 
           & (IData)(vlSelf->bench__DOT__dut__DOT__edge_io__DOT__rx_fifo_ready));
}

VL_INLINE_OPT void Vbench___024root___nba_comb__TOP__11(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___nba_comb__TOP__11\n"); );
    // Body
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
}

void Vbench___024root___timing_resume(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___timing_resume\n"); );
    // Body
    if ((2ULL & vlSelf->__VactTriggered.word(0U))) {
        vlSelf->__VtrigSched_h0016f595__0.resume("@(posedge bench.clk)");
    }
    if ((1ULL & vlSelf->__VactTriggered.word(0U))) {
        vlSelf->__VtrigSched_h0016f654__0.resume("@(negedge bench.clk)");
    }
    if ((0x400ULL & vlSelf->__VactTriggered.word(0U))) {
        vlSelf->__VdlySched.resume();
    }
}

void Vbench___024root___timing_commit(Vbench___024root* vlSelf) {
    if (false && vlSelf) {}  // Prevent unused
    Vbench__Syms* const __restrict vlSymsp VL_ATTR_UNUSED = vlSelf->vlSymsp;
    VL_DEBUG_IF(VL_DBG_MSGF("+    Vbench___024root___timing_commit\n"); );
    // Body
    if ((! (2ULL & vlSelf->__VactTriggered.word(0U)))) {
        vlSelf->__VtrigSched_h0016f595__0.commit("@(posedge bench.clk)");
    }
    if ((! (1ULL & vlSelf->__VactTriggered.word(0U)))) {
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
    VlTriggerVec<11> __VpreTriggered;
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
            VL_FATAL_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 2, "", "NBA region did not converge.");
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
                VL_FATAL_MT("evidence/verification/l1-2d1c41c6c5c449ac871be765f08c06d7/case-0089-suite-16-run_top/top-synthetic-q1-uart-s17-reload/compiled-bench.sv", 2, "", "Active region did not converge.");
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
